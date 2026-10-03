"""Negative real-model proposals remain invalid independently of any skill."""

from copy import deepcopy
import json
from pathlib import Path

from reason_commons.bootstrap import create_case
from tests.support import ScriptedConsultant, bounded_case, submit


def test_captured_orphan_observations_reject_entire_application_update(tmp_path):
    captured = json.loads((Path(__file__).parent / "fixtures/null-test-reference.json").read_text())

    def replay(request):
        proposal = deepcopy(captured)
        old_identity = proposal["request_id"]
        proposal["request_id"] = request["input"]["request_id"]
        proposal["base_revision"] = request["input"]["base_revision"]
        for update in proposal["proposed_updates"]:
            update["source_refs"] = [proposal["request_id"] if s == old_identity else s
                                     for s in update["source_refs"]]
        return proposal

    with create_case(tmp_path / "case", consultant=ScriptedConsultant([bounded_case, replay])) as app:
        assert submit(app, "A sourced prospective pilot")["status"] == "saved"
        before = app.inspect()["case"]
        result = submit(app, "40 of 50 orders on time; 18 of 20 urgent acknowledgements.")
        assert result["status"] == "rejected"
        assert app.inspect()["case"] == before
        assert len(app.history()["revisions"]) == 2
        assert app.sources()["sources"][result["request_id"]]["text"] == (
            "40 of 50 orders on time; 18 of 20 urgent acknowledgements.")
