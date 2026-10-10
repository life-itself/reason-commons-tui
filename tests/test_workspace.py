"""Presentation guarantees exercised through application capabilities and real adapters."""

from copy import deepcopy
import json

import pytest

from reason_commons.adapters.invocation import run_contribution
from reason_commons.adapters.mcp_server import CaseToolBridge
from reason_commons.adapters.rendering import render_mermaid, render_workspace
from reason_commons.application.presentation import VIEWS
from reason_commons.bootstrap import create_case, open_case
from reason_commons.domain.model import InvalidCase
from examples.p0_slice import AuthoredConsultant
from tests.support import ScriptedConsultant, bounded_case, cli, proposal, submit


# These tests are about what the views show of the model, so the commons accepts proposals as they arrive.
AUTOMATIC = {"acceptance": "automatic", "actor": "Sam"}


@pytest.mark.parametrize("view", VIEWS)
def test_open_and_local_views_do_not_consult_or_change_state(tmp_path, view):
    consultant = ScriptedConsultant([bounded_case])
    path = tmp_path / "case"
    with create_case(path, "Payments", consultant=consultant) as app:
        assert app.workspace()["question"] is None and consultant.calls == []
        submit(app, "The pilot has an original forecast.")
        before = app.inspect()
    files_before = {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}
    with open_case(path, writable=False) as app:
        workspace = app.workspace(view=view)
        assert workspace["revision"] == 1 and workspace["target"] == {
            "base_revision": 1, "response_target": "I1@1"}
        assert workspace["question"]["data"]["primary_prompt"] == "What should we observe next?"
        assert app.inspect() == before
        assert len(consultant.calls) == 1
        assert "95% acknowledged within four hours" in render_workspace(workspace)
        if view == "explain":
            assert "Keep the next move bounded." in render_workspace(workspace)
        if view == "sources":
            assert workspace["sources"]["in000001"]["text"] == "The pilot has an original forecast."
    assert files_before == {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}


def test_frozen_read_is_independent_of_later_updates_and_caller_edits(tmp_path):
    consultant = ScriptedConsultant([bounded_case])
    with create_case(tmp_path / "case", consultant=consultant, **AUTOMATIC) as app:
        submit(app)
        original_current = app._store.current
        reads = []
        def current():
            reads.append(True)
            return original_current()
        app._store.current = current
        first = app.workspace(view="history")
        assert len(reads) == 1
        frozen = deepcopy(first)
        first["goals"][0]["data"]["statement"] = "Caller changed this"
        first["diagram"]["links"].clear()
        assert app.workspace()["goals"] == frozen["goals"]
        submit(app, "A later contribution")
        assert frozen["revision"] == 1 and frozen["question"]["ref"] == "I1@1"
        old = app.workspace(revision=1, view="sources")
        assert old["historical"] and set(old["sources"]) == {"in000001"}
        assert all(a["route"] == "local" for a in old["available_actions"])
        assert next(a for a in old["available_actions"] if a["id"] == "return_live")["arguments"] == {"view": "next"}
        with pytest.raises(InvalidCase):
            app.workspace(revision=1, selection="in000002")
        with pytest.raises(InvalidCase):
            app.workspace(revision=99)
        with pytest.raises(InvalidCase):
            app.workspace(revision=True)
        with pytest.raises(InvalidCase):
            app.workspace(view="invented_graph")


def test_original_forecast_actual_safeguard_and_execution_remain_distinct(tmp_path):
    consultant = AuthoredConsultant()
    with create_case(tmp_path / "case", "Payments", consultant=consultant, **AUTOMATIC) as app:
        for text, declarations in [("Bounded pilot", None), ("I own and completed the work", {"ownership": ["Sam"]}),
                                   ("Actual measured results", None), ("Pause for the safeguard breach", None)]:
            assert submit(app, text, declarations=declarations)["status"] == "saved"
        workspace = app.workspace(view="tests")
        comparison = workspace["comparisons"][0]
        assert [f["expected"] for f in comparison["test"]["data"]["forecast"]] == ["80%", "95%"]
        assert [r["data"]["value"] for r in comparison["observations"]] == ["80%", "90%"]
        assert comparison["reviews"][0]["data"]["assessment"] == "Acknowledgement below original 95% bound"
        text = render_workspace(workspace, markdown=True)
        assert "| Measure | Original forecast | Reported result |" in text
        assert all(value in text for value in ["95%", "90%", "20 deliveries due", "10 urgent requests", "two weeks"])
        actions = app.workspace(view="actions")
        action = next(r for r in actions["records"] if r["kind"] == "action")
        assert action["data"]["execution"] == "completed" and action["data"]["expected_state_attainment"] == "unknown"
        assert {r["kind"] for r in actions["records"]} >= {"goal", "test", "action"}
        assert "Work execution: completed" in render_workspace(actions)
        assert "Expected state attainment: unknown" in render_workspace(actions)
        old = app.workspace(view="tests", revision=1)
        assert old["comparisons"][0]["observations"] == []
        assert old["comparisons"][0]["reviews"] == []


def test_diagram_uses_only_explicit_resolved_references_and_escapes_labels(tmp_path):
    malicious = 'A "quote"] --> injected["node"\n<script>evil</script> #35; Café'
    def output(request):
        value = bounded_case(request)
        value["proposed_updates"][1]["data"]["statement"] = malicious
        value["intervention"]["options"] = [
            {"id": "test", "label": "Inspect pilot", "action": {"type": "view", "target": "test:test"}},
            {"id": "advice", "label": "Get advice", "action": {"type": "consult", "intent": "direct_advice"}}]
        return value
    consultant = ScriptedConsultant([output])
    with create_case(tmp_path / "case", consultant=consultant, **AUTOMATIC) as app:
        assert submit(app)["status"] == "saved"
        workspace = app.workspace(view="reasoning")
        assert workspace["diagram"]["links"] == [{"from": "P1@1", "to": "G1@1", "field": "goal_ref", "label": "tests progress toward"}]
        assert {r["ref"] for r in workspace["diagram"]["nodes"]} == {"P1@1", "G1@1"}
        graph = render_mermaid(workspace)
        assert 'injected["' not in graph and "<script>" not in graph and "#233;" in graph
        assert graph.count("-->") == 1
        assert malicious == workspace["goals"][0]["data"]["statement"]
        routes = {a["id"]: a for a in workspace["available_actions"]}
        assert routes["option_test"]["arguments"] == {"view": "tests", "revision": 1, "selection": "P1@1"}
        assert routes["option_advice"]["arguments"] == {"intent": "direct_advice", "base_revision": 1, "response_target": "I1@1"}
        assert routes["option_test"]["route"] == "local" and routes["option_advice"]["route"] == "asks_consultant"


def test_unlinked_notes_do_not_become_diagrams_and_missing_data_stays_unknown(tmp_path):
    with create_case(tmp_path / "case", consultant=ScriptedConsultant()) as app:
        submit(app, "A causes B (participant hypothesis)")
        workspace = app.workspace()
        assert render_mermaid(workspace) == "" and workspace["diagram"]["links"] == []
        assert any(u["field"] == "goal" for u in workspace["uncertainty"])
        assert workspace["attribution"]["N1@1"] == [{"source_ref": "in000001", "speaker": "Sam"}]


def test_reply_uses_displayed_anchor_and_explicit_consultant_intent(tmp_path):
    consultant = ScriptedConsultant()
    with create_case(tmp_path / "case", consultant=consultant) as app:
        displayed = app.workspace()
        submit(app, "Someone else advances the commons")
        stale = run_contribution(app, consultant, text="My reply to the old question", speaker="David", target=displayed["target"])
        assert stale["result"]["status"] == "stale" and len(consultant.calls) == 1
        current = app.workspace()
        text = 'Please advise\n5\n:options\n'
        report = run_contribution(app, consultant, text=text, speaker="David", target=current["target"], intent="direct_advice")
        assert report["result"]["status"] == "saved" and report["procedure_completed"]
        assert consultant.calls[-1]["input"]["intent"] == "direct_advice"
        assert consultant.calls[-1]["input"]["text"] == text
        assert report["workspace"]["revision"] == 2 and report["workspace"]["question"]["ref"] == "I2@1"
        assert "What should we observe next?" in report["rendered"]["markdown"]


def test_failure_resume_and_explicit_retry_preserve_input_and_do_not_leak_proposals(tmp_path):
    path = tmp_path / "case"
    consultant = ScriptedConsultant([RuntimeError("private error")])
    with create_case(path, consultant=consultant) as app:
        report = run_contribution(app, consultant, text="My exact contribution", speaker="David")
        assert report["result"]["status"] == "unavailable"
        assert report["workspace"]["revision"] == 0
    with open_case(path, writable=False) as app:
        workspace = app.workspace()
        assert workspace["pending_requests"][0]["status"] == "unavailable"
        assert workspace["pending_requests"][0]["input"]["text"] == "My exact contribution"
        assert "private error" not in render_workspace(workspace)
        assert len(consultant.calls) == 1
    with open_case(path, consultant=consultant) as app:
        saved = run_contribution(app, consultant, retry_request=report["result"]["request_id"])
        assert saved["result"]["status"] == "saved" and saved["workspace"]["pending_requests"] == []
        assert len(consultant.calls) == 2 and len(app.sources()["sources"]) == 1
        again = run_contribution(app, consultant, retry_request=report["result"]["request_id"])
        assert again["result"]["already_applied"] and len(consultant.calls) == 2


def test_cli_and_mcp_present_the_same_frozen_workspace_offline(tmp_path):
    consultant = ScriptedConsultant([bounded_case])
    bridge = CaseToolBridge(tmp_path, consultant)
    bridge.invoke("new_case", {"case": "payments", "name": "Payments"})
    saved = bridge.invoke("submit", {"case": "payments", "text": "Original contribution", "speaker": "David",
                                  "base_revision": 0, "response_target": None})
    assert saved["status"] == "saved" and saved["workspace"]["revision"] == 1
    assert "Current question" in saved["rendered"]["text"]
    workspace = bridge.invoke("workspace", {"case": "payments", "view": "tests"})
    output = cli("show", tmp_path / "payments", "--view", "tests", "--format", "json")
    assert output.returncode == 0 and json.loads(output.stdout) == workspace
    assert cli("show", tmp_path / "payments", "--view", "tests").stdout == workspace["rendered"]["text"]
    assert cli("show", tmp_path / "payments", "--view", "tests", "--format", "markdown").stdout == workspace["rendered"]["markdown"]
    assert len(consultant.calls) == 1


def test_pending_status_uses_attempt_and_receipt_sequence_not_filename_order(tmp_path):
    consultant = ScriptedConsultant([RuntimeError("failure")])
    with create_case(tmp_path / "case", consultant=consultant) as app:
        result = submit(app)
        request_id = result["request_id"]
        # Adapter-level setup models several confirmations within the same attempt.
        for index in range(10):
            app._store.receipt(request_id, 1, {"status": "rejected" if index == 9 else "not_saved"})
        assert app.workspace()["pending_requests"][0]["status"] == "rejected"
        assert app.receipts(request_id)["attempts"][-1]["status"] == "rejected"
