"""Live semantic cases: actual application outcomes plus authored review rubric."""

from copy import deepcopy
import time

from reason_commons.bootstrap import create_case, open_case
from evaluations.fixtures import SEED_TEXT, SEEDS, SeedConsultant
from evaluations.report import check


def run_scenario(report, scenario, consultant, repeat):
    identity = f"semantic-{scenario.name}-{repeat}"
    path = report.directory / identity
    checks, turns = [], []
    def evidence(status):
        report.record({"id": identity, "status": status, "scenarios": list(scenario.scenarios), "case": str(path),
                       "setup": (f"authored setup '{scenario.seed_kind}' via application, accepted under Sam's "
                                 "automatic-acceptance setting") if scenario.seed else
                                "empty case set to accept proposals automatically (Sam's recorded setting)",
                       "checks": deepcopy(checks), "turns": deepcopy(turns), "rubric": list(scenario.rubric),
                       "semantic_review": "pending; no keyword score or self-grading model"})
    evidence("running")
    # Proposals enter the model under Sam's recorded automatic-acceptance setting, so each turn builds on the
    # last as a participant accepting what they agree with would; every proposal stays in the evidence.
    if scenario.seed:
        with create_case(str(path), scenario.name, consultant=SeedConsultant(scenario.seed_kind),
                         acceptance="automatic", actor="Sam") as app:
            text = SEED_TEXT if scenario.seed_kind == "pilot" else SEEDS[scenario.seed_kind]["text"]
            result = app.submit(text, "Sam", app.inspect()["case"]["revision"], None)
            if result["status"] != "saved":
                raise RuntimeError("Authored evaluation setup failed")
    with (open_case(str(path), consultant=consultant) if scenario.seed else
          create_case(str(path), scenario.name, consultant=consultant, acceptance="automatic", actor="Sam")) as app:
        for number, turn in enumerate(scenario.turns, 1):
            before = app.inspect()["case"]
            start = time.monotonic()
            result = app.submit(turn.text, turn.speaker, before["revision"], before["current_intervention"],
                                intent=turn.intent, declarations=turn.declarations)
            after = app.inspect()["case"]
            new = after["records"][len(before["records"]):]
            retained = app.sources()["sources"].get(result.get("request_id"), {})
            checks += [
                check(f"turn {number}: live proposal published", result["status"] == "saved", result["status"]),
                check(f"turn {number}: exact input/attribution/target retained",
                      retained.get("text") == turn.text and retained.get("speaker") == turn.speaker
                      and retained.get("base_revision") == before["revision"]
                      and retained.get("response_target") == before["current_intervention"]),
                check(f"turn {number}: history unchanged", after["records"][:len(before["records"])] == before["records"]),
                check(f"turn {number}: contribution represented by sourced non-intervention record",
                      any(r["kind"] != "intervention" and result.get("request_id") in r["source_refs"] for r in new)),
                check(f"turn {number}: one prominent next intervention",
                      sum(r["kind"] == "intervention" for r in new) == 1),
            ]
            if scenario.name == "goal_action_review":
                kinds = {r["kind"] for r in new}
                expected = {1: {"goal", "note"}, 2: {"goal"}, 3: {"test"},
                            4: {"action"}, 5: {"observation", "review"}}[number]
                checks.append(check(f"turn {number}: task is represented as the required record kinds",
                                    expected <= kinds, sorted(kinds)))
                if number == 2:
                    checks.append(check("unknown baseline remains unknown", all(
                        r["data"].get("baseline") in {None, "unknown", "Unknown", "unknown baseline"}
                        for r in new if r["kind"] == "goal")))
                if number == 4:
                    actions = [r for r in new if r["kind"] == "action"]
                    checks.append(check("completion does not establish attained result", bool(actions) and all(
                        r["data"].get("execution") == "completed" and
                        r["data"].get("expected_state_attainment", "unknown") in {"unknown", "pending"}
                        for r in actions)))
            if scenario.expects_review and number == 1:  # the turn that reports results; later turns ask about them
                tests = [r for r in before["records"] if r["kind"] == "test"]
                checks.append(check("review references the exact original prospective pilot", any(
                    r["kind"] == "review" and r["data"]["test_ref"] == tests[0]["ref"] for r in new)))
            turns.append({"number": number, "text": turn.text, "speaker": turn.speaker,
                          "elapsed_seconds": round(time.monotonic() - start, 2), "result": result,
                          "new_records": deepcopy(new), "provider_version": consultant.version,
                          "membership": {r["ref"]: app.workspace()["membership"].get(r["ref"]) for r in new
                                         if r["kind"] != "intervention"},
                          "receipts": app.receipts(result["request_id"]) if "request_id" in result else {}})
            evidence("running")
            # Model failures remain evidence. Do not silently retry or replace them with authored responses.
            if result["status"] != "saved":
                break
        final = app.inspect()["case"]
        app.export(str(report.directory / (identity + ".reasoncase")))
    with open_case(str(path), writable=False) as app:
        checks.append(check("restart reproduces published state offline", app.inspect()["case"] == final))
    evidence("completed")
