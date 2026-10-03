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
    assert loaded["machine_checks"] == {"passed": 0, "failed": 1}
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
