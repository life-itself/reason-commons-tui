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


def test_consultations_count_first_attempts_reasons_and_tokens(tmp_path):
    report = Report(tmp_path / "evidence", {"model": "fixture"})
    turn = lambda result, usage=None, seconds=1.0: {"number": 1, "speaker": "Sam", "text": "literal",
                                                     "result": result, "usage": usage, "elapsed_seconds": seconds}
    report.append({"id": "one", "turns": [
        turn({"status": "saved"}, {"input_tokens": 100, "output_tokens": 20}),
        turn({"status": "rejected", "reason": "Anthropic stopped at max_tokens (4096) before finishing the proposal"},
             {"input_tokens": 100, "output_tokens": 4096})]})
    report.append({"id": "two", "turns": [turn({"status": "unavailable", "failure_category": "timeout"}, None, 120.0)]})
    report.finish()
    summary = json.loads((report.directory / "report.json").read_text())["consultations"]
    assert summary["turns"] == 3 and summary["by_status"] == {"saved": 1, "rejected": 1, "unavailable": 1}
    assert summary["not_saved_reasons"] == {
        "Anthropic stopped at max_tokens (4096) before finishing the proposal": 1, "timeout": 1}
    assert summary["tokens"] == {"input_tokens": 200, "output_tokens": 4116} and summary["turns_with_usage"] == 2
    assert summary["seconds"] == 122.0
    assert "Consultations:" in (report.directory / "report.md").read_text()
