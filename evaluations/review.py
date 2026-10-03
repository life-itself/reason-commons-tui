"""Consume attributed external reviews without conflating them with machine checks."""

from hashlib import sha256
import json
from pathlib import Path

from evaluations.report import write_json


def review_template(report_path):
    path = Path(report_path)
    report = json.loads(path.read_text())
    return {"format": "reason-commons-review/1", "report_sha256": sha256(path.read_bytes()).hexdigest(),
            "reviewer": "", "reviewed_at": "", "reviewer_role": "", "decisions": [
                {"run_id": run["id"], "criterion": index, "rubric": rubric,
                 "status": "pending", "evidence": ""}
                for run in report["runs"] for index, rubric in enumerate(run.get("rubric", []), 1)]}


def apply_review(report_path, review_path, output_path):
    report_path = Path(report_path)
    expected = review_template(report_path)
    review = json.loads(Path(review_path).read_text())
    if review.get("format") != expected["format"] or review.get("report_sha256") != expected["report_sha256"]:
        raise ValueError("Review must identify the unchanged completed evidence report")
    report = json.loads(report_path.read_text())
    if report["status"] != "completed":
        raise ValueError("Cannot approve an unfinished evaluation")
    if any(not isinstance(review.get(k), str) or not review[k].strip()
           for k in ("reviewer", "reviewed_at", "reviewer_role")):
        raise ValueError("An attributed reviewer, role and date are required")
    decisions = review.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("Review decisions must be a list")
    if not expected["decisions"]:
        raise ValueError("This report contains no semantic criteria to review")
    identities = [(d["run_id"], d["criterion"]) for d in expected["decisions"]]
    if [(d.get("run_id"), d.get("criterion")) for d in decisions] != identities:
        raise ValueError("Review must cover every criterion in report order without omissions or duplicates")
    for actual, original in zip(decisions, expected["decisions"]):
        if actual.get("rubric") != original["rubric"] or actual.get("status") not in {"pass", "fail", "pending"}:
            raise ValueError("Review criteria cannot be rewritten")
        if actual["status"] != "pending" and (not isinstance(actual.get("evidence"), str) or not actual["evidence"].strip()):
            raise ValueError("Every decided criterion needs cited case/turn evidence")
    statuses = [d["status"] for d in decisions]
    result = {"format": "reason-commons-reviewed-evaluation/1", "report_sha256": expected["report_sha256"],
              "machine_checks": report["machine_checks"], "review": review,
              "semantic_status": "fail" if "fail" in statuses else "pending" if "pending" in statuses else "pass",
              "release_gate": "incomplete: this review does not satisfy p1/p2 acceptance or participant gates"}
    output = Path(output_path)
    if output.exists():
        raise FileExistsError("Use a new reviewed evidence path")
    write_json(output, result)
    return result
