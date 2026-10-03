#!/usr/bin/env python3
"""Offline executable p0 demonstration with authored consultant proposals."""

import argparse
import json
from pathlib import Path

from reason_commons.bootstrap import create_case, import_case, open_case
from reason_commons.adapters.skills import RetainedContributionWorkflow


class AuthoredConsultant:
    """A fixture, not a language model. All output is explicit and inspectable."""

    version = "authored-p0-demo/1"

    def propose(self, request):
        source = request["input"]["request_id"]
        turn = len(request["case"]["applied_requests"])
        updates = [{"operation": "record_note", "data": {
            "text": request["input"]["text"], "basis": "participant_report"}, "source_refs": [source]}]
        if turn == 0:
            updates += [
                {"operation": "record_goal", "temporary_id": "goal", "data": {
                    "statement": "90% of Payments deliveries on time", "scope": "Payments",
                    "horizon": "October 30", "baseline": None,
                    "protections": ["Urgent acknowledgement at least 95%"]}, "source_refs": [source]},
                {"operation": "record_test", "temporary_id": "pilot", "data": {
                    "statement": "A two-week bounded release pilot", "goal_ref": "goal", "scope": "Payments pilot",
                    "forecast": [{"measure": "delivery", "expected": "80%", "scope": "pilot",
                                  "denominator": "deliveries due"},
                                 {"measure": "acknowledgement", "expected": "95%", "scope": "pilot",
                                  "denominator": "urgent requests"}]}, "source_refs": [source]}]
            prompt = "Who will carry out the bounded pilot?"
        elif turn == 1:
            updates.append({"operation": "record_action", "data": {"statement": "Run the pilot",
                            "test_ref": "P1@1", "owner": "Sam", "execution": "completed",
                            "expected_state_attainment": "unknown"}, "source_refs": [source]})
            prompt = "What did the pilot measure?"
        elif turn == 2:
            for measure, value, denominator in [("delivery", "80%", "20 deliveries due"),
                                                 ("acknowledgement", "90%", "10 urgent requests")]:
                updates.append({"operation": "record_observation", "data": {"test_ref": "P1@1",
                                "measure": measure, "value": value, "scope": "Payments pilot",
                                "denominator": denominator, "period": "two weeks", "basis": "participant_report"},
                                "source_refs": [source]})
            prompt = "What should happen after the breached safeguard?"
        else:
            updates.append({"operation": "record_review", "data": {"test_ref": "P1@1",
                            "observation_refs": ["B1@1", "B2@1"], "assessment": "Acknowledgement below original 95% bound",
                            "next_decision": "Pause and revise urgent handling"}, "source_refs": [source]})
            prompt = "What revised condition would justify another test?"
        return {"schema_version": "1", "delivery_profile": "p2", "request_id": source,
                "base_revision": request["input"]["base_revision"], "intervention": {
                    "kind": "question", "purpose": "bounded_demo", "primary_prompt": prompt,
                    "rationale": "Preserve the original forecast and separate action from effects."},
                "proposed_updates": updates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path, help="New directory for demo artifacts")
    directory = parser.parse_args().directory
    directory.mkdir(mode=0o700)  # never replace an existing demonstration
    with create_case(directory / "case", "Payments", consultant=AuthoredConsultant()) as app:
        workflow = RetainedContributionWorkflow(app)
        for text, declarations in [
            ("Goal 90% on time; pilot delivery forecast 80%, urgent acknowledgement bound 95%.", None),
            ("I own the pilot and completed the planned work.", {"ownership": ["Sam"]}),
            ("16 of 20 deliveries on time; 9 of 10 urgent requests acknowledged within four hours.", None),
            ("Pause the pilot and revise urgent handling before another test.", None),
        ]:
            result = workflow.contribute(text, "Sam", declarations)
            if result["status"] != "saved":
                raise RuntimeError(result)
        case = app.inspect()["case"]
        app.checkpoint({"view": "next", "focus": "response", "speaker": "Sam",
                        "draft": "Retained draft\n5", "caret": 16, "base_revision": case["revision"],
                        "response_target": case["current_intervention"]})
        before = app.inspect()
        app.export(directory / "handoff.reasoncase")
    with open_case(directory / "case") as resumed:
        assert resumed.inspect() == before
    with import_case(directory / "handoff.reasoncase", directory / "handoff") as imported:
        assert imported.inspect() == before
    print(json.dumps({"status": "saved", "revision": case["revision"], "provider": "authored fixture",
                      "record_kinds": sorted({r["kind"] for r in case["records"]}),
                      "restart_and_handoff": "identical", "directory": str(directory.resolve())}))


if __name__ == "__main__":
    main()
