"""The accessible ordered presentation as an interface: literal input, explicit submission, local navigation,
decisions through the same use cases, plain text that wraps, and a draft kept across sessions."""

from reason_commons.adapters.accessible import KEYS, AccessibleWorkspace
from reason_commons.bootstrap import create_case, open_case
from tests.support import ScriptedConsultant, proposal
from tests.test_trees import claim, link, with_updates


def session(path, consultant, width=60, height=20):
    case = open_case(path, consultant=consultant)
    out = []
    workspace = AccessibleWorkspace(case, "Sam", width, height, write=out.append)
    workspace.start()
    return case, workspace, out


def text(out, since=0):
    return " ".join("".join(out[since:]).split())


def focus_on(workspace, label):
    labels = [c.label for c in workspace.controls()]
    for _ in range((labels.index(label) - workspace.focus) % len(labels)):
        workspace.handle("tab")


def test_typing_is_literal_and_only_send_submits(tmp_path):
    create_case(tmp_path / "case", "Forge").close()
    consultant = ScriptedConsultant()
    case, workspace, out = session(tmp_path / "case", consultant)
    for key in ["q", "?", "5", "enter", "x", "space", "y", "backspace"]:
        workspace.handle(key)
    assert workspace.draft == "q?5\nx " and consultant.calls == []
    focus_on(workspace, "Send")
    mark = len(out)
    workspace.handle("enter")
    assert len(consultant.calls) == 1 and consultant.calls[0]["input"]["text"] == "q?5\nx "
    assert workspace.draft == "" and "== Next step (replaces the view above) ==" in text(out, mark)
    case.close()


def test_navigation_is_local_and_esc_returns_with_the_draft(tmp_path):
    create_case(tmp_path / "case", "Forge").close()
    consultant = ScriptedConsultant()
    case, workspace, out = session(tmp_path / "case", consultant)
    for key in "five":
        workspace.handle(key)
    revision = case.inspect()["case"]["revision"]
    for label in ("Explain this", "Case context", "Views", "Help"):
        focus_on(workspace, label)
        workspace.handle("enter")
        assert workspace.view != "next"
        workspace.handle("escape")
        assert workspace.view == "next" and workspace.draft == "five"
    assert consultant.calls == [] and case.inspect()["case"]["revision"] == revision
    assert "Returned to Next step; your draft is kept." in text(out)
    case.close()


def test_backlog_decisions_go_through_the_use_case_and_confirm_what_they_take(tmp_path):
    create_case(tmp_path / "case", "Forge").close()
    consultant = ScriptedConsultant([with_updates(claim("temp_e", "Orders ship late"),
                                                  claim("temp_c", "Priorities change daily", role="root_cause"),
                                                  link("temp_l", "temp_c", "temp_e"))])
    case, workspace, out = session(tmp_path / "case", consultant)
    for key in "Late, because priorities change":
        workspace.handle("space" if key == " " else key)
    focus_on(workspace, "Send")
    workspace.handle("enter")
    focus_on(workspace, "Views")
    workspace.handle("enter")
    focus_on(workspace, "Backlog")
    workspace.handle("enter")
    assert workspace.view == "backlog"
    entries = [e["ref"] for e in case.workspace(view="backlog")["backlog"]]
    for _ in range(entries.index("L1@1")):
        workspace.handle("down")
    focus_on(workspace, "Accept")
    mark = len(out)
    workspace.handle("enter")
    assert "This takes more than you chose" in text(out, mark)
    assert case.workspace()["membership"]["L1@1"] == "proposed"  # nothing changed yet
    workspace.handle("enter")
    assert case.workspace()["membership"]["L1@1"] == "accepted"
    assert case.workspace()["membership"]["C2@1"] == "accepted" and len(consultant.calls) == 1
    case.close()


def test_output_is_plain_text_that_wraps_to_the_terminal(tmp_path):
    create_case(tmp_path / "case", "A goal with a rather long name to wrap").close()
    case, workspace, out = session(tmp_path / "case", ScriptedConsultant(), width=30, height=12)
    workspace.handle("tab")
    focus_on(workspace, "Help")
    workspace.handle("enter")
    lines = "".join(out).splitlines()
    assert max(len(line) for line in lines) <= 30 and "\x1b" not in "".join(out)
    assert "Focus: Send, asks the consultant" in text(out)
    case.close()


def test_the_draft_is_kept_when_the_session_ends(tmp_path):
    create_case(tmp_path / "case", "Forge").close()
    case, workspace, out = session(tmp_path / "case", ScriptedConsultant())
    for key in "half":
        workspace.handle(key)
    workspace.handle("quit")
    assert workspace.running is False
    case.close()
    case, again, _ = session(tmp_path / "case", ScriptedConsultant())
    assert again.draft == "half"
    case.close()


def test_terminal_keys_map_to_the_names_the_presentation_takes():
    assert KEYS["\t"] == "tab" and KEYS["\x1b[Z"] == "shift+tab" and KEYS["\r"] == "enter"
    assert KEYS["\x1b[6~"] == "pagedown" and KEYS["\x1b[5~"] == "pageup" and KEYS["\x1b"] == "escape"


def paid_session(tmp_path, monkeypatch, budget=None):
    """The ordered presentation consulting Claude (a loopback fake), its replies counted in a usage log."""
    from reason_commons.adapters.anthropic import AnthropicConsultant
    from reason_commons.adapters.usage import UsageLog, UsageSession
    from tests.servers import anthropic_server_instance
    if budget is not None:
        monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", budget)
    generator = anthropic_server_instance()
    server = next(generator)
    usage = UsageSession(UsageLog(tmp_path / "usage.jsonl"), "accessible")
    consultant = AnthropicConsultant(base_url=server.url, api_key="fixture-secret", usage=usage.record)
    create_case(tmp_path / "case", "Paid").close()
    case = open_case(tmp_path / "case", consultant=consultant)
    out = []
    workspace = AccessibleWorkspace(case, "Sam", 80, 24, write=out.append, usage=usage, model=consultant.model)
    return case, workspace, out, server, lambda: next(generator, None)


def test_a_replys_cost_and_a_budget_crossing_are_said_once(tmp_path, monkeypatch):
    case, workspace, out, server, stop = paid_session(tmp_path, monkeypatch, budget="0.002")
    try:
        workspace.start()
        for key in "Fewer missed deliveries":
            workspace.handle("space" if key == " " else key)
        focus_on(workspace, "Send")
        mark = len(out)
        workspace.handle("enter")
        said = text(out, mark)
        assert said.count("Cost: about $0.0017, Haiku 5.5, estimated.") == 1
        assert said.count("80% of your $0.002 budget, estimated. Nothing is blocked.") == 1
        assert "≈" not in said  # spoken as "about"
    finally:
        case.close()
        stop()


def test_past_the_budget_send_asks_to_be_activated_again_and_tab_keeps_the_response(tmp_path, monkeypatch):
    case, workspace, out, server, stop = paid_session(tmp_path, monkeypatch, budget="0.001")
    workspace.usage.record({"model": "claude-haiku-5-5", "outcome": "proposal", "tokens": {"input": 12_000,
                                                                                           "output": 900}})
    try:
        workspace.start()
        assert "past your $0.001 budget, estimated. Each send will ask first; nothing is blocked." in text(out)
        for key in "five":
            workspace.handle(key)
        focus_on(workspace, "Send")
        mark = len(out)
        workspace.handle("enter")
        said = text(out, mark)
        assert "Activate the same control again to send it" in said and "This reply about $0.0042" in said
        assert workspace.draft == "five" and case.inspect()["case"]["revision"] == 0
        workspace.handle("tab")  # moving on forgets the question; nothing was sent
        workspace.handle("shift+tab")
        workspace.handle("enter")
        assert case.inspect()["case"]["revision"] == 0 and workspace.draft == "five"
        workspace.handle("enter")  # the same control, activated again
        assert case.inspect()["case"]["revision"] == 1 and workspace.draft == ""
    finally:
        case.close()
        stop()
