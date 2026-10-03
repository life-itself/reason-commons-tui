"""The MCP adapter preserves application results and explicit case boundaries."""

import base64

import pytest

from reason_commons.adapters.mcp_server import CaseToolBridge, TOOLS
from reason_commons.application.ports import CaseCapabilities
from reason_commons.bootstrap import open_case
from tests.support import ScriptedConsultant


def test_bridge_covers_semantic_capabilities_and_opens_no_idle_writer(tmp_path):
    import inspect
    assert {name for name, member in vars(CaseCapabilities).items()
            if not name.startswith("_") and inspect.isfunction(member)} <= {t["name"] for t in TOOLS}
    provider = ScriptedConsultant()
    bridge = CaseToolBridge(tmp_path, provider)
    bridge.invoke("new_case", {"case": "payments", "name": "Payments"})
    current = bridge.invoke("inspect", {"case": "payments"})["case"]
    retained = bridge.invoke("retain_input", {"case": "payments", "text": "5\n:options", "speaker": "Sam",
        "base_revision": current["revision"], "response_target": current["current_intervention"]})
    request_id = retained["request_id"]
    assert bridge.invoke("consult", {"case": "payments", "request_id": request_id})["status"] == "saved"
    assert bridge.invoke("retry", {"case": "payments", "request_id": request_id})["already_applied"]
    assert len(provider.calls) == 1
    with open_case(tmp_path / "payments") as app:
        assert app.sources()["sources"][request_id]["text"] == "5\n:options"
        assert app.inspect()["case"]["revision"] == 1
    assert "Reasoning Case" in bridge.invoke("context", {})["domain"]


@pytest.mark.parametrize("case", ["../outside", "/tmp/outside", ".", "nested/case", "exports/../case", "exports"])
def test_case_paths_cannot_escape_configured_root(tmp_path, case):
    bridge = CaseToolBridge(tmp_path, ScriptedConsultant())
    with pytest.raises(ValueError):
        bridge.invoke("new_case", {"case": case, "name": "Invalid"})
    assert list(tmp_path.iterdir()) == []


def test_mcp_submission_preserves_explicit_consulting_intents(tmp_path):
    from reason_commons.domain.model import CONSULT_INTENTS
    provider = ScriptedConsultant()
    bridge = CaseToolBridge(tmp_path, provider)
    bridge.invoke("new_case", {"case": "payments", "name": "Payments"})
    grammar = next(t for t in TOOLS if t["name"] == "submit")["inputSchema"]
    assert set(grammar["properties"]["intent"]["enum"]) == {"answer"} | CONSULT_INTENTS
    for intent in sorted(CONSULT_INTENTS):
        case = bridge.invoke("inspect", {"case": "payments"})["case"]
        result = bridge.invoke("submit", {"case": "payments", "text": "Literal participant request", "speaker": "Sam",
            "base_revision": case["revision"], "response_target": case["current_intervention"], "intent": intent})
        assert result["status"] == "saved" and provider.calls[-1]["input"]["intent"] == intent


def test_symlink_case_and_export_escape_are_rejected(tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    bridge = CaseToolBridge(root, ScriptedConsultant())
    (root / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        bridge.invoke("new_case", {"case": "linked", "name": "Invalid"})
    bridge.invoke("new_case", {"case": "payments", "name": "Payments"})
    (root / "exports").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        bridge.invoke("export", {"case": "payments", "bundle": "handoff.reasoncase"})
    assert list(outside.iterdir()) == []


def test_supplied_source_export_and_stale_work_use_application_rules(tmp_path):
    bridge = CaseToolBridge(tmp_path, ScriptedConsultant())
    bridge.invoke("new_case", {"case": "payments", "name": "Payments"})
    source = bridge.invoke("add_source", {"case": "payments", "name": "report.csv", "speaker": "Sam",
        "content_base64": base64.b64encode(b"measure,value\ndelivery,80%\n").decode()})
    assert source["source_ref"] in bridge.invoke("sources", {"case": "payments"})["sources"]
    bridge.invoke("submit", {"case": "payments", "text": "literal", "speaker": "Sam", "base_revision": 0,
                            "response_target": None})
    assert bridge.invoke("retain_input", {"case": "payments", "text": "stale", "speaker": "Sam",
        "base_revision": 0, "response_target": None})["status"] == "stale"
    bundle = bridge.invoke("export", {"case": "payments", "bundle": "handoff.reasoncase"})["bundle"]
    with open_case(bundle, writable=False) as app:
        assert app.inspect() == bridge.invoke("inspect", {"case": "payments"})
    with pytest.raises(ValueError):
        bridge.invoke("export", {"case": "payments", "bundle": "../escape.reasoncase"})
