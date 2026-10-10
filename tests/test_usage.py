"""The local usage log: where it is, how it is written and read, and what its summaries say."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

import pytest

from reason_commons.adapters.anthropic import AnthropicConsultant
from reason_commons.adapters.usage import KEYS, UsageLog, UsageSession, budget, crossed, log_path, parse_budget
from reason_commons.bootstrap import create_case, usage_session
from tests.servers import anthropic_server_instance
from tests.support import submit

ROOT = Path(__file__).resolve().parents[1]
REPLY = {"provider": "anthropic", "model": "claude-haiku-5-5", "outcome": "proposal", "case_id": "case-1",
         "request_id": "in000001", "tokens": {"input": 12_000, "output": 900}}


def clock(value):
    return lambda: value


def session(tmp_path, now=None, entry="workspace", **options):
    return UsageSession(UsageLog(tmp_path / "state" / "usage.jsonl", now), entry, **options)


@pytest.fixture
def local_time():
    """Run in a time zone far from UTC, so a day and a month are the person's own."""
    saved = os.environ.get("TZ")
    os.environ["TZ"] = "America/Los_Angeles"
    time.tzset()
    yield
    if saved is None:
        os.environ.pop("TZ")
    else:
        os.environ["TZ"] = saved
    time.tzset()


def test_the_log_is_where_the_environment_says_or_in_the_state_folder(tmp_path):
    assert log_path({"REASON_COMMONS_USAGE_LOG": str(tmp_path / "mine.jsonl")}) == tmp_path / "mine.jsonl"
    assert log_path({"REASON_COMMONS_USAGE_LOG": " OFF "}) is None
    assert log_path({"XDG_STATE_HOME": str(tmp_path)}) == tmp_path / "reason-commons" / "usage.jsonl"
    assert log_path({"XDG_STATE_HOME": "relative"}) == Path("~/.local/state/reason-commons/usage.jsonl").expanduser()
    assert log_path({}) == Path("~/.local/state/reason-commons/usage.jsonl").expanduser()


def test_the_log_is_private_and_holds_only_its_own_keys(tmp_path):
    usage = session(tmp_path)
    usage.record(REPLY)
    path = tmp_path / "state" / "usage.jsonl"
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    line = json.loads(path.read_text())
    assert tuple(line) == KEYS
    assert line["usd"] == "0.00165" and line["model"] == "claude-haiku-5-5" and line["entry"] == "workspace"
    assert line["prices"] == {"source": "list", "as_of": "2026-10-08", "input": "0.10", "output": "0.50",
                              "cache_write": "0.125", "cache_write_1h": "0.20", "cache_read": "0.01"}
    assert line["tokens"] == {"input": 12000, "output": 900, "cache_write": 0, "cache_write_1h": 0, "cache_read": 0}


def test_unreadable_and_torn_lines_are_skipped_and_counted_and_the_next_line_starts_fresh(tmp_path):
    usage = session(tmp_path)
    usage.record(REPLY)
    path = usage.log.path
    with path.open("ab") as file:
        file.write(b"not json\n{\"v\": 99}\n" + json.dumps({"v": 1, "at": "yesterday", "tokens": {}}).encode() + b"\n")
        file.write(b'{"v": 1, "at": "2026-10-08T10:0')  # a write cut short
    entries, skipped = usage.log.read()
    assert len(entries) == 1 and skipped == 4
    usage.record(REPLY)
    entries, skipped = usage.log.read()
    assert len(entries) == 2 and skipped == 4  # the torn line is now a whole bad line, and the new one reads


def test_four_processes_writing_at_once_never_interleave(tmp_path):
    path = tmp_path / "usage.jsonl"
    program = ("import sys\nfrom reason_commons.adapters.usage import UsageLog, UsageSession\n"
               "usage = UsageSession(UsageLog(sys.argv[1]), 'cli')\n"
               "for n in range(200):\n"
               "    usage.record({'model': 'claude-haiku-5-5', 'outcome': 'proposal', 'request_id': f'in{n:06d}',\n"
               "                  'tokens': {'input': 12000 + n, 'output': 900}})\n")
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    workers = [subprocess.Popen([sys.executable, "-c", program, str(path)], env=environment) for _ in range(4)]
    assert [worker.wait(timeout=60) for worker in workers] == [0] * 4
    entries, skipped = UsageLog(path).read()
    assert (len(entries), skipped) == (800, 0)
    assert len({entry["session"] for entry in entries}) == 4


def test_today_and_this_month_are_the_persons_own_days(tmp_path, local_time):
    # 23:30 on 31 October in Los Angeles is already 1 November in UTC.
    late = datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc)
    usage = session(tmp_path, now=clock(late))
    usage.record(REPLY)
    summary = usage.summary(case_id="case-1")
    assert summary["today"]["replies"] == summary["month"]["replies"] == 1
    # Forty minutes later it is 1 November there too: a new day and a new month.
    usage.log.now = clock(late + timedelta(minutes=40))
    summary = usage.summary(case_id="case-1")
    assert summary["today"]["replies"] == summary["month"]["replies"] == 0
    assert summary["goal"]["replies"] == summary["session"]["replies"] == 1
    assert usage.summary(case_id="another")["goal"]["replies"] == 0


def test_a_summary_sums_by_model_and_keeps_requests_without_a_reply_apart(tmp_path):
    now = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)
    earlier = session(tmp_path, now=clock(now - timedelta(days=1)), entry="cli")
    earlier.record(REPLY)
    usage = session(tmp_path, now=clock(now))
    mark = usage.mark()
    usage.record({**REPLY, "model": "claude-sonnet-5-5", "request_id": "in000002"})
    usage.record({**REPLY, "outcome": "no_reply", "tokens": {}, "request_id": "in000003"})
    usage.record({**REPLY, "model": "local-model", "request_id": "in000004"})
    assert [entry["request_id"] for entry in usage.since(mark)] == ["in000002", "in000003", "in000004"]
    assert usage.last_for("in000002")["usd"] == Decimal("0.033") and usage.last_for("in000009") is None
    summary = usage.summary(case_id="case-1")
    assert summary["reply"]["model"] == "local-model"
    assert summary["session"]["replies"] == 2 and summary["session"]["no_reply"] == 1
    assert summary["session"]["unpriced"] == 1 and summary["session"]["usd"] == Decimal("0.033")
    month = summary["month"]
    assert month["replies"] == 3 and month["usd"] == Decimal("0.03465")
    assert month["by_model"]["claude-haiku-5-5"] == {"replies": 1, "usd": Decimal("0.00165"), "unpriced": 0,
                                                    "no_reply": 1, "input": 12000, "output": 900}
    assert summary["today"]["replies"] == 2  # yesterday's command-line reply is in the month only


def test_crossing_a_budget_line_is_said_once(tmp_path):
    five = Decimal(5)
    assert crossed(Decimal(3), Decimal("4.5"), five) == 80
    assert crossed(Decimal("4.5"), Decimal("4.9"), five) is None
    assert crossed(Decimal("4.9"), Decimal("5.1"), five) == 100
    assert crossed(Decimal(3), Decimal(6), five) == 100
    assert crossed(Decimal("5.1"), Decimal(7), five) is None
    assert crossed(Decimal(0), Decimal(9), None) is None


def test_the_budget_comes_from_the_environment_then_the_settings(tmp_path):
    assert [parse_budget(v) for v in ("5", "$5", " 5.50 ", 5, "none", "0", "", None, "lots", -1)] == [
        Decimal(5), Decimal(5), Decimal("5.50"), Decimal(5), None, None, None, None, None, None]
    assert budget({"REASON_COMMONS_MONTHLY_BUDGET_USD": "$3"}, 5) == (Decimal(3), "environment")
    assert budget({"REASON_COMMONS_MONTHLY_BUDGET_USD": "none"}, 5) == (None, "environment")
    assert budget({"REASON_COMMONS_MONTHLY_BUDGET_USD": " "}, "5") == (Decimal(5), "settings")
    assert budget({}, None) == (None, None)
    settings = type("Saved", (), {"data": {"usage": {"monthly_budget_usd": 7, "prices": {
        "claude-haiku-5-5": {"input": "1", "output": "1"}}}}})()
    usage = usage_session("cli", environ={"REASON_COMMONS_USAGE_LOG": "off"}, settings=settings)
    assert usage.budget() == (Decimal(7), "settings") and usage.log.path is None
    usage.record(REPLY)
    assert usage.last_for("in000001")["usd"] == Decimal("0.0129")  # the saved prices, not the list


def test_a_log_that_cannot_be_written_never_raises_and_the_reply_still_counts(tmp_path):
    blocked = tmp_path / "a-file"
    blocked.write_text("not a folder")
    usage = UsageSession(UsageLog(blocked / "usage.jsonl"), "workspace")
    usage.record(REPLY)
    assert usage.error in ("NotADirectoryError", "FileExistsError")
    summary = usage.summary()
    assert summary["session"]["replies"] == summary["month"]["replies"] == 1 and summary["error"] == usage.error
    usage.record({"tokens": "nonsense", "model": object()})  # an event it cannot read is dropped quietly
    assert usage.summary()["session"]["replies"] == 1


def test_typical_cost_needs_three_recent_replies(tmp_path):
    now = datetime(2026, 10, 8, tzinfo=timezone.utc)
    usage = session(tmp_path, now=clock(now))
    for _ in range(2):
        usage.record(REPLY)
    assert usage.typical("claude-haiku-5-5") is None
    usage.record({**REPLY, "tokens": {"input": 24_000, "output": 1_800}})
    assert usage.typical("claude-haiku-5-5") == Decimal("0.0022")
    usage.log.now = clock(now + timedelta(days=91))
    assert usage.typical("claude-haiku-5-5") is None


def test_a_real_consultation_is_logged_without_words_names_paths_or_key(tmp_path):
    generator = anthropic_server_instance()
    server = next(generator)
    try:
        usage = session(tmp_path)
        consultant = AnthropicConsultant(base_url=server.url, api_key="fixture-secret", usage=usage.record)
        store = tmp_path / "Secret Project Name"
        with create_case(store, "Secret Project Name", consultant=consultant) as app:
            assert submit(app, "Words only the commons may hold")["status"] == "saved"
            case_id = app.inspect()["case"]["case_id"]
    finally:
        next(generator, None)
    raw = usage.log.path.read_text()
    for private in ("Words only the commons", "Secret Project", str(tmp_path), "fixture-secret"):
        assert private not in raw
    line = json.loads(raw)
    assert tuple(line) == KEYS and (line["case_id"], line["request_id"]) == (case_id, "in000001")
