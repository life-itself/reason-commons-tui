"""Evaluation evidence must remain separate from claims of semantic release."""

import json

import pytest

from evaluations.fixtures import SCENARIOS, SeedConsultant, NoteConsultant
from evaluations.report import Report, check
from evaluations.semantic import run_scenario
from evaluations.review import review_template, apply_review
from evaluations.report import write_json
from reason_commons.bootstrap import create_case


def test_report_refuses_overwrite_and_records_failures(tmp_path):
    report = Report(tmp_path / "evidence", {"model": "fixture"})
    report.append({"id": "failed", "checks": [check("not repaired", False)]})
    report.finish()
    loaded = json.loads((report.directory / "report.json").read_text())
    assert (loaded["machine_checks"]["passed"], loaded["machine_checks"]["failed"]) == (0, 1)
    assert loaded["machine_checks"]["failed_by_category"]["consultant"] == 1
    assert "incomplete" in loaded["release_gate"]
    with pytest.raises(FileExistsError):
        Report(report.directory, {})


def test_semantic_harness_records_real_effects_and_pending_rubric(tmp_path):
    report = Report(tmp_path / "evidence", {"model": "authored-fixture"})
    run_scenario(report, SCENARIOS[1], NoteConsultant(), 1)
    report.finish()
    run = report.value["runs"][0]
    assert len(run["turns"]) == 3 and all(c["status"] == "pass" for c in run["checks"])
    assert run["semantic_review"].startswith("pending")
    assert "Priya" in (report.directory / "report.md").read_text()
    assert (report.directory / (run["id"] + ".reasoncase")).exists()


def test_authored_pilot_setup_is_valid_and_original_denominators_preserved(tmp_path):
    with create_case(tmp_path / "case", consultant=SeedConsultant()) as app:
        assert app.submit("A prospective pilot", "Sam", 0, None)["status"] == "saved"
        pilot = next(r for r in app.inspect()["case"]["records"] if r["kind"] == "test")
        assert [f["expected"] for f in pilot["data"]["forecast"]] == ["80%", "95%"]
        assert [f["denominator"] for f in pilot["data"]["forecast"]] == ["orders due", "urgent requests"]


def test_external_review_is_attributed_complete_and_bound_to_frozen_report(tmp_path):
    report = Report(tmp_path / "evidence", {"model": "fixture"})
    report.append({"id": "sample", "checks": [check("valid schema", True)], "rubric": ["No unsupported claim"]})
    report.finish()
    path = report.directory / "report.json"
    review = review_template(path)
    review.update(reviewer="Test reviewer", reviewed_at="2026-10-02", reviewer_role="test fixture")
    review["decisions"][0].update(status="fail", evidence="Turn 1 asserts an unsupported causal relation")
    write_json(tmp_path / "review.json", review)
    outcome = apply_review(path, tmp_path / "review.json", tmp_path / "reviewed.json")
    assert outcome["semantic_status"] == "fail" and "incomplete" in outcome["release_gate"]
    report.value["configuration"]["model"] = "different"
    report.save()
    with pytest.raises(ValueError, match="unchanged"):
        apply_review(path, tmp_path / "review.json", tmp_path / "stale-review.json")


def test_review_cannot_omit_required_criteria_or_decide_without_evidence(tmp_path):
    report = Report(tmp_path / "evidence", {})
    report.append({"id": "sample", "rubric": ["First", "Second"]})
    report.finish()
    path = report.directory / "report.json"
    review = review_template(path)
    review.update(reviewer="Test reviewer", reviewed_at="2026-10-02", reviewer_role="test fixture")
    review["decisions"] = review["decisions"][:1]
    write_json(tmp_path / "review.json", review)
    with pytest.raises(ValueError, match="every criterion"):
        apply_review(path, tmp_path / "review.json", tmp_path / "reviewed.json")


def test_every_fixture_sets_up_through_the_application_and_runs(tmp_path):
    from evaluations.fixtures import SEEDS
    report = Report(tmp_path / "evidence", {"model": "authored-fixture"})
    for scenario in SCENARIOS:
        run_scenario(report, scenario, NoteConsultant(), 1)
    report.finish()
    runs = {run["id"]: run for run in report.value["runs"]}
    assert len(runs) == len(SCENARIOS) and all(run["status"] == "completed" for run in runs.values())
    # Every authored setup is valid, and every evaluated turn was published and retained exactly.
    assert {s.seed_kind for s in SCENARIOS if s.seed} >= set(SEEDS) | {"pilot"}
    assert all(t["result"]["status"] == "saved" for run in runs.values() for t in run["turns"])
    covered = {sid for s in SCENARIOS for sid in s.scenarios}
    assert {"S01", "S02", "S06", "S30", "S34", "S35", "S36", "S52", "S102", "S104", "S105", "S122"} <= covered


def test_a_criterion_that_cannot_be_judged_never_counts_as_passed(tmp_path):
    report = Report(tmp_path / "evidence", {})
    report.append({"id": "sample", "rubric": ["First", "Second"]})
    report.finish()
    path = report.directory / "report.json"
    review = review_template(path)
    review.update(reviewer="Test reviewer", reviewed_at="2026-10-07", reviewer_role="test fixture")
    review["decisions"][0].update(status="pass", evidence="Turn 1 keeps the forecast")
    review["decisions"][1].update(status="unjudgeable", evidence="")
    write_json(tmp_path / "review.json", review)
    with pytest.raises(ValueError, match="evidence"):
        apply_review(path, tmp_path / "review.json", tmp_path / "reviewed.json")
    review["decisions"][1]["evidence"] = "Turn 3's reply was rejected before commit; nothing to judge"
    write_json(tmp_path / "review.json", review)
    assert apply_review(path, tmp_path / "review.json", tmp_path / "reviewed.json")["semantic_status"] == "incomplete"


def test_runs_keep_their_setup_and_failures_by_kind(tmp_path):
    report = Report(tmp_path / "evidence", {"model": "authored-fixture"})
    run_scenario(report, next(s for s in SCENARIOS if s.seed is True), NoteConsultant(), 1)
    report.finish()
    run = report.value["runs"][0]
    assert run["setup_text"] and any(r["kind"] == "test" for r in run["setup_records"])
    assert run["unjudgeable_turns"] == []
    assert set(report.value["machine_checks"]["failed_by_category"]) == {"consultant", "application", "consequence"}
    assert {c["category"] for c in run["checks"]} <= {"consultant", "application", "consequence"}


class RejectedSecondReply(NoteConsultant):
    """The second reply carries a field the next move does not have, as one live reply did."""

    def propose(self, request):
        value = super().propose(request)
        if self.calls == 2:
            value["intervention"]["purpose_note"] = "not a field"
        return value


def screens_report(tmp_path, *runs):
    report = Report(tmp_path / "evidence", {"provider": "anthropic", "model": "authored-fixture"})
    for name, consultant in runs:
        run_scenario(report, next(s for s in SCENARIOS if s.name == name), consultant, 1)
    report.finish()
    return report


def test_the_replay_sends_each_turn_through_the_workspace_and_reproduces_the_run(tmp_path):
    from evaluations.screens import replay_run
    report = screens_report(tmp_path, ("goal_action_review", NoteConsultant()), ("attributed_correction", NoteConsultant()))
    review, correction = report.value["runs"]
    turns = replay_run(report.directory, review, "anthropic", tmp_path / "work", tmp_path / "review")
    # Advice and observation turns go through Other moves; the ownership turn says the workspace cannot declare it.
    assert [t["sent_with"] for t in turns] == ["Send", "Send", "Ask for direct advice", "Send",
                                               "Ask for help planning an observation"]
    assert [bool(t["notes"]) for t in turns] == [False, False, False, True, False]
    assert all({"Next step", "Commons context"} <= {s["view"] for s in t["screens"]} for t in turns)
    first = (tmp_path / "review" / turns[0]["before"]["file"]).read_text()
    assert "Late" in first and "deliveries," in first  # the answer as typed, before Send
    after = (tmp_path / "review" / turns[0]["screens"][0]["file"]).read_text()
    assert "Answer" in after and "Claude" in after  # the workspace's own screen, naming the consultant
    # A turn by another participant is answered in a workspace opened as them.
    turns = replay_run(report.directory, correction, "anthropic", tmp_path / "work", tmp_path / "correction")
    assert [t["speaker"] for t in turns] == ["Sam", "Priya", "Sam"]
    assert "Answer as Priya" in (tmp_path / "correction" / turns[1]["screens"][0]["file"]).read_text().replace(
        "&#160;", " ")


def test_the_replay_refuses_a_report_its_case_does_not_match(tmp_path):
    from evaluations.screens import ReplayMismatch, replay_run
    run = screens_report(tmp_path, ("attributed_correction", NoteConsultant())).value["runs"][0]
    reply = next(a for a in run["turns"][1]["receipts"]["attempts"] if "proposal" in a)
    reply["proposal"]["intervention"]["primary_prompt"] = "A question the consultant never asked"
    with pytest.raises(ReplayMismatch, match="replies"):
        replay_run(tmp_path / "evidence", run, "anthropic", tmp_path / "work", tmp_path / "screens")


def test_the_review_package_is_blind_and_writes_the_review_the_checker_accepts(tmp_path):
    import re
    from evaluations.review_page import CAPABILITIES, build_review_package, collect_reviews
    report = screens_report(tmp_path, ("attributed_correction", RejectedSecondReply()))
    page = build_review_package(report.directory / "report.json")
    package = report.directory / "review-package"  # beside the report unless told otherwise
    assert page == package / "index.html"
    html = page.read_text()
    # Recorded history and the accepted current model are different; older reply wording remains readable.
    assert "<b>commons</b>" in html and "<b>conversation</b>" in html
    assert "currently accepted reasoning" in html and "two names for the same thing" not in html
    assert "Recording a proposal preserves it in the commons; accepting it admits it to the model" in html
    from evaluations.plain_reply import words_in
    glossary = dict(words_in([{"headline": "The case keeps earlier reasoning outside the model.", "lines": []}]))
    assert "complete history across conversations" in glossary["commons"]
    assert "called a case in older replies" in glossary["commons"]
    assert "currently accepted reasoning" in glossary["the model"]
    assert "without belonging to its current model" in glossary["the model"]
    data = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S).group(1))
    assert data["template"] == review_template(report.directory / "report.json")
    case = data["cases"][0]
    # Each turn is what was written and what the assistant replied, in plain words, without record IDs.
    assert [t["speaker"] for t in case["turns"]] == ["Sam", "Priya"] and case["unsent"] == [3]
    first = case["turns"][0]
    assert first["reply"][0]["headline"] == "The system asks: What should we observe next?"
    assert first["reply"][1]["source"] == "Based on Sam's message in Turn 1"
    assert not re.search(r"\b[A-Z]\d+@\d+\b", json.dumps([t["reply"] for t in case["turns"]]))
    # A code in the assistant's own words stays, with what it names beside it.
    from evaluations.plain_reply import Names
    names = Names([{"ref": "P1@1", "kind": "test", "data": {"statement": "Daily queue"}}])
    assert names.explain("matches the forecast in P1@1") == "matches the forecast in P1@1 [the trial “Daily queue”]"
    assert names.explain("Z9@1 is unknown") == "Z9@1 is unknown"
    # A question about the rejected reply, or the turn never sent, is answered for the reviewer.
    given = {q["id"]: q.get("given", {}).get("answer") for q in case["questions"]}
    assert given == {"1.1": "cant", "1.2": "cant", "2.1": "cant", "2.2": "cant", "3.1": "cant", "3.2": "cant",
                     "3.3": "cant"}
    # Every screen the page names is in its commons' file, as the workspace's own SVG.
    screens = json.loads((package / case["file"]).read_text().split("] = ", 1)[1].rstrip(";\n"))
    keys = {s["key"] for t in case["turns"] for s in t["screens"]}
    assert keys == set(screens) and all(svg.lstrip().startswith("<svg") for svg in screens.values())
    # The publish call: the commons files, and each reviewer's record readable only by them and the owner.
    publish = json.loads((package / "publish.json").read_text())
    assert publish["files"] == {case["file"]: case["file"]} and publish["capabilities"] == CAPABILITIES
    assert {"path": "reviews/{self}", "read": "interact", "write": "interact"} in CAPABILITIES["db"]["rules"]
    assert {"path": "reviews", "read": "owner", "write": "owner"} in CAPABILITIES["db"]["rules"]
    # Blind: no machine check, check name or prior review reaches the page; the method's labels stay out.
    assert "checks" not in json.dumps(data) and "machine" not in html and "S06" not in html
    # The assistant is "the system" throughout; the model is named once, beside the person's screens.
    assert "{consultant}" not in html and html.count("Claude") == 1 and "the system" in html
    with pytest.raises(FileExistsError):
        build_review_package(report.directory / "report.json")
    # The reviewer's stored answers become a review.json the unchanged checker validates.
    rows = tmp_path / "rows" / "reviews"
    rows.mkdir(parents=True)
    stored = {"reviewer": "Test reviewer", "reviewer_role": "No background in this kind of work",
              "reviewed_at": "2026-10-08", "report_sha256": data["template"]["report_sha256"], "answers": {}}
    (rows / "u_reviewer.json").write_text(json.dumps({"id": "u_reviewer", "data": stored}))
    written = collect_reviews(package, tmp_path / "rows", tmp_path / "reviews")
    assert [p.name for p in written] == ["review-Test-reviewer.json"]
    outcome = apply_review(report.directory / "report.json", written[0], tmp_path / "reviewed.json")
    assert outcome["semantic_status"] == "incomplete"  # nothing could be judged: every reply was rejected or unsent


def test_every_rubric_criterion_has_plain_questions_about_real_turns():
    import re
    from evaluations.review_questions import REVIEW
    for scenario in SCENARIOS:
        case = REVIEW[scenario.name]
        assert [rubric for rubric, _ in case.criteria] == list(scenario.rubric), scenario.name
        for _, asks in case.criteria:
            assert asks
            for ask in asks:
                assert ask.turn is None or 1 <= ask.turn <= len(scenario.turns), (scenario.name, ask.text)
                text = ask.text.format(consultant="the system")
                assert "?" in text and "{" not in text, text
                # Asked plainly: what the reply did, never a double negative ("does it avoid...?").
                assert "avoid" not in text.lower() and ask.passes in {"yes", "no"}, text
                # Plain words: no method labels, scenario IDs or pronouns nobody gave.
                assert not re.search(r"\b(he|she|his|her|him|denominator|proxy|CRT|FRT|S\d+)\b", text), text
        # Nothing is used before it is introduced: a fact belongs to a turn that happens, and a question about a turn
        # names no fact that only becomes known in a later turn.
        assert "Claude" not in case.situation + str(case.facts) + str(case.criteria)
        for turn, label, value in case.facts:
            assert 0 <= turn <= len(scenario.turns) and label and value, (scenario.name, label)
        for _, asks in case.criteria:
            for ask in asks:
                later = [label for turn, label, _ in case.facts
                         if label.lower() in ask.text.lower() and ask.turn is not None and turn > ask.turn]
                assert not later, (scenario.name, ask.text, later)


def test_a_criterion_is_decided_from_its_questions():
    from evaluations.review_questions import combine, verdict
    # A question about a mistake is met by No; any other by Yes.
    assert verdict("yes") == "good" and verdict("no") == "bad"
    assert verdict("no", passes="no") == "good" and verdict("yes", passes="no") == "bad"
    assert verdict("cant", passes="no") == "cant" and verdict("unclear") == "unclear"
    assert combine(["good", "good"]) == "pass"
    assert combine(["good", "bad"]) == "fail" and combine(["bad", "unclear"]) == "fail"
    assert combine(["good", "cant"]) == "unjudgeable"
    assert combine(["good", "unclear"]) == "pending" and combine(["good", None]) == "pending" and combine([]) == "pending"


def test_answers_combine_into_the_review_the_checker_accepts(tmp_path):
    from evaluations.review_page import build_review_package, review_from_answers
    report = screens_report(tmp_path, ("blaming_question", NoteConsultant()))
    build_review_package(report.directory / "report.json")
    questions = json.loads((report.directory / "review-package" / "questions.json").read_text())
    run = questions["cases"][0]
    # Each question answered the way that meets its criterion (No for a question about a mistake), but one.
    answers = {f"{run['id']}__{q['id']}": {"answer": q["passes"], "why": ""} for q in run["questions"]}
    assert {q["passes"] for q in run["questions"]} == {"yes", "no"}
    answers[f"{run['id']}__2.2"] = {"answer": "no", "why": "It asks who is to blame"}
    review = review_from_answers(questions, {"reviewer": "Test reviewer", "reviewer_role": "fixture",
                                             "reviewed_at": "2026-10-08", "answers": answers})
    assert [d["status"] for d in review["decisions"]] == ["pass", "fail", "pass"]
    assert "Turn 1:" in review["decisions"][1]["evidence"] and "It asks who is to blame" in review["decisions"][1]["evidence"]
    write_json(tmp_path / "review.json", review)
    outcome = apply_review(report.directory / "report.json", tmp_path / "review.json", tmp_path / "reviewed.json")
    assert outcome["semantic_status"] == "fail"


def test_the_replay_refuses_screens_of_a_case_that_came_out_differently(tmp_path, monkeypatch):
    from evaluations import screens
    run = screens_report(tmp_path, ("attributed_correction", NoteConsultant())).value["runs"][0]
    recorded = screens.ReplayConsultant.propose

    def drifted(self, request):
        value = recorded(self, request)
        value["intervention"]["primary_prompt"] = "A question the run never showed"
        return value
    monkeypatch.setattr(screens.ReplayConsultant, "propose", drifted)
    with pytest.raises(screens.ReplayMismatch, match="did not reproduce"):
        screens.replay_run(tmp_path / "evidence", run, "anthropic", tmp_path / "work", tmp_path / "screens")


def test_consultations_count_first_attempts_reasons_and_tokens(tmp_path):
    report = Report(tmp_path / "evidence", {"model": "fixture"})
    turn = lambda result, usage=None, seconds=1.0: {"number": 1, "speaker": "Sam", "text": "literal",
                                                     "result": result, "usage": usage, "elapsed_seconds": seconds}
    report.append({"id": "one", "turns": [
        dict(turn({"status": "saved"}, {"input_tokens": 100, "output_tokens": 20}),
             repairs=["unwrapped the proposal from input"]),
        turn({"status": "rejected", "reason": "Anthropic stopped at max_tokens (4096) before finishing the proposal"},
             {"input_tokens": 100, "output_tokens": 4096})]})
    report.append({"id": "two", "turns": [turn({"status": "unavailable", "failure_category": "timeout"}, None, 120.0)]})
    report.finish()
    summary = json.loads((report.directory / "report.json").read_text())["consultations"]
    assert summary["turns"] == 3 and summary["by_status"] == {"saved": 1, "rejected": 1, "unavailable": 1}
    assert summary["not_saved_reasons"] == {
        "Anthropic stopped at max_tokens (4096) before finishing the proposal": 1, "timeout": 1}
    assert summary["tokens"] == {"input_tokens": 200, "output_tokens": 4116} and summary["turns_with_usage"] == 2
    assert summary["transport_repairs"] == {"unwrapped the proposal from input": 1}
    assert summary["seconds"] == 122.0
    assert "Consultations:" in (report.directory / "report.md").read_text()


def test_procedure_replay_runs_every_step_through_the_application(tmp_path):
    from evaluations.procedure import STEPS, run_procedure
    report = Report(tmp_path / "evidence", {"model": "authored-fixture"})
    run_procedure(report, NoteConsultant(), 1)
    report.finish()
    run = report.value["runs"][0]
    assert run["status"] == "completed" and len(run["turns"]) == len(STEPS)
    assert all(t["result"]["status"] == "saved" for t in run["turns"])
    assert all(c["status"] == "pass" for c in run["checks"])
    # Between steps the operator accepted what waited; the injection step left the setting alone.
    assert any(d["status"] == "saved" for t in run["turns"] for d in t["decisions"])
    assert report.value["consultations"]["by_status"] == {"saved": len(STEPS)}
