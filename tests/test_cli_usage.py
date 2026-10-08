"""`reason-commons usage` reads the local log and sends nothing; contribute, retry and MCP say when the month
reaches 80% of the budget, without changing their results."""

from datetime import datetime, timedelta, timezone
import json

from reason_commons.adapters.mcp_server import CaseToolBridge
from reason_commons.adapters.usage import UsageLog, UsageSession, log_path
from reason_commons.bootstrap import create_case
from tests.servers import anthropic_server_instance
from tests.support import cli

HAIKU = {"model": "claude-haiku-5-5", "outcome": "proposal", "tokens": {"input": 12_000, "output": 900}}


def logged(entry_point, *events, at=None):
    """Record events in the test's own usage log (REASON_COMMONS_USAGE_LOG, set for every test)."""
    session = UsageSession(UsageLog(log_path(), (lambda: at) if at else None), entry_point)
    for event in events:
        session.record(event)


def test_usage_sums_this_month_by_model_against_the_budget_and_says_where_it_comes_from(monkeypatch):
    monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", "1")
    logged("workspace", HAIKU, HAIKU)
    logged("cli", {**HAIKU, "model": "claude-sonnet-5-5"})
    logged("mcp", {**HAIKU, "outcome": "no_reply", "tokens": {}})
    logged("cli", HAIKU, at=datetime.now(timezone.utc) - timedelta(days=40))
    with log_path().open("a") as file:
        file.write("not json\n")
    result = cli("usage")
    assert result.returncode == 0 and result.stderr == ""
    text = result.stdout
    assert f"Claude usage, {datetime.now().astimezone():%B %Y} (estimates)" in text
    assert "Sonnet 5.5  1 reply, ≈ $0.03 · 12,000 tokens in, 900 out" in text
    assert "Haiku 5.5   2 replies, ≈ $0.0033 · 24,000 tokens in, 1,800 out" in text
    assert "Total       3 replies, ≈ $0.04, 3% of your $1 monthly budget" in text
    assert "Today: 3 replies, ≈ $0.04" in text
    assert ("Where: command line 1 reply, ≈ $0.03 · MCP server 0 replies, ≈ $0 · workspace 2 replies, ≈ $0.0033"
            in text)
    assert "No reply: 1 request was sent and got no reply; they may still have been billed." in text
    assert "1 line of the log could not be read and is not counted." in text
    assert "your bill is in the Anthropic Console." in text and "Log: " in text


def test_usage_takes_another_month_everything_or_one_goal_and_gives_json(tmp_path):
    earlier = datetime(2026, 9, 15, 12, tzinfo=timezone.utc)
    logged("cli", HAIKU, at=earlier)
    store = tmp_path / "goal"
    with create_case(store, "Goal") as app:
        case_id = app.inspect()["case"]["case_id"]
    logged("workspace", {**HAIKU, "case_id": case_id}, {**HAIKU, "case_id": "another-case"})
    september = json.loads(cli("usage", "--month", "2026-09", "--json").stdout)
    assert september["period"] == "2026-09" and september["total"]["replies"] == 1
    assert september["budget_usd"] is None and september["models"][0]["label"] == "Haiku 5.5"
    everything = json.loads(cli("usage", "--all", "--json").stdout)
    assert everything["period"] == "all" and everything["total"] == {
        "replies": 3, "no_reply": 0, "unpriced": 0, "estimated_usd": "0.00495"}
    goal = json.loads(cli("usage", "--all", "--goal", store, "--json").stdout)
    assert goal["goal"] == case_id and goal["total"]["replies"] == 1
    assert set(goal) >= {"models", "total", "today", "entry_points", "skipped_lines", "log", "prices_as_of"}
    assert "Claude usage, September 2026 (estimates)" in cli("usage", "--month", "2026-09").stdout
    bad = cli("usage", "--month", "September")
    assert bad.returncode == 1 and "YYYY-MM" in bad.stderr


def test_usage_with_the_log_off_says_nothing_is_counted(monkeypatch):
    monkeypatch.setenv("REASON_COMMONS_USAGE_LOG", "off")
    result = cli("usage")
    assert result.returncode == 0 and "The usage log is off" in result.stdout


def contribute(tmp_path, server, monkeypatch, budget):
    monkeypatch.setenv("REASON_COMMONS_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-secret")
    monkeypatch.setenv("REASON_COMMONS_ANTHROPIC_URL", server.url)
    if budget:
        monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", budget)
    store = tmp_path / ("case-" + (budget or "none"))
    cli("new", "--store", store)
    return cli("contribute", store, "--speaker", "Sam", "--text", "literal", "--json")


def test_contribute_says_on_stderr_when_the_month_reaches_80_percent_and_changes_nothing_else(tmp_path, monkeypatch):
    generator = anthropic_server_instance()
    server = next(generator)
    try:
        quiet = contribute(tmp_path, server, monkeypatch, None)
        assert quiet.returncode == 0 and quiet.stderr == "" and json.loads(quiet.stdout)["result"]["status"] == "saved"
        near = contribute(tmp_path, server, monkeypatch, "0.004")  # two Haiku replies: $0.0033, 82%
        assert near.returncode == 0 and json.loads(near.stdout)["result"]["status"] == "saved"
        assert near.stderr == ("Claude this month ≈ $0.0033, 82% of your $0.004 monthly budget (estimate); "
                               "nothing was blocked.\n")
        over = contribute(tmp_path, server, monkeypatch, "0.003")
        assert over.returncode == 0 and "has reached your $0.003 monthly budget" in over.stderr
        assert over.stderr.count("\n") == 1
    finally:
        next(generator, None)


def test_mcp_results_carry_a_usage_notice_from_80_percent_of_the_budget(tmp_path, monkeypatch):
    from reason_commons.adapters.anthropic import AnthropicConsultant
    generator = anthropic_server_instance()
    server = next(generator)
    try:
        usage = UsageSession(UsageLog(log_path()), "mcp")
        consultant = AnthropicConsultant(base_url=server.url, api_key="fixture-secret", usage=usage.record)
        bridge = CaseToolBridge(tmp_path, consultant, usage=usage)
        results = []
        for name, budget in (("first", "1"), ("second", "0.002")):
            monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", budget)
            bridge.invoke("new_case", {"case": name, "name": name})
            results.append(bridge.invoke("submit", {"case": name, "text": "literal", "speaker": "Sam",
                                                    "base_revision": 0, "response_target": None}))
        assert results[0]["status"] == "saved" and "usage_notice" not in results[0]
        assert results[1]["status"] == "saved"
        assert results[1]["usage_notice"] == ("Claude this month ≈ $0.0033 has reached your $0.002 monthly budget "
                                              "(estimate); nothing was blocked.")
    finally:
        next(generator, None)
