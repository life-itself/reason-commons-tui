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
    assert all({"Next step", "Case context"} <= {s["view"] for s in t["screens"]} for t in turns)
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
    from evaluations.review_page import build_review_package
    report = screens_report(tmp_path, ("attributed_correction", RejectedSecondReply()))
    page = build_review_package(report.directory / "report.json", tmp_path / "package")
    data = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>',
                                page.read_text(), re.S).group(1))
    assert data["template"] == review_template(report.directory / "report.json")
    case = data["cases"][0]
    # The rejected reply is shown as the operator saw it, and the run is marked as stopped.
    assert [t["saved"] for t in case["turns"]] == [True, False] and case["stopped"]
    assert all((tmp_path / "package" / s["file"]).exists() for t in case["turns"] for s in t["screens"])
    # Blind: no machine check, check name or prior review reaches the page.
    assert "checks" not in json.dumps(data) and "machine" not in page.read_text()
    with pytest.raises(FileExistsError):
        build_review_package(report.directory / "report.json", tmp_path / "package")
    # What the page saves is the template with decisions filled in, which the unchanged checker validates.
    review = data["template"]
    review.update(reviewer="Test reviewer", reviewed_at="2026-10-07", reviewer_role="test fixture")
    for decision in review["decisions"]:
        decision.update(status="unjudgeable", evidence="Turn 2, Next step: the reply was not saved")
    write_json(tmp_path / "review.json", review)
    outcome = apply_review(report.directory / "report.json", tmp_path / "review.json", tmp_path / "reviewed.json")
    assert outcome["semantic_status"] == "incomplete"


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
