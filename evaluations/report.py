"""Durable per-run evidence, with explicit machine/human review boundaries."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path


# What a failed check is evidence of: the consultant's reply, the application, or only the consequence of a
# reply that was never committed. A harness error is found later, by a reviewer, and is never a category here.
CATEGORIES = ("consultant", "application", "consequence")


def check(name, passed, evidence="", category="consultant"):
    return {"name": name, "status": "pass" if passed else "fail", "evidence": evidence, "category": category}


def consultation_summary(runs):
    """How the evaluated turns ended, why the others were not saved, and what they cost in tokens and time.

    Each turn is attempted once, so the share saved is the first-attempt validity of the replies."""
    turns = [turn for run in runs for turn in run.get("turns", [])]
    by_status, reasons, tokens = {}, {}, {}
    for turn in turns:
        status = turn["result"].get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        if status != "saved":
            reason = str(turn["result"].get("reason") or turn["result"].get("failure_category")
                         or "no reason given")[:160]
            reasons[reason] = reasons.get(reason, 0) + 1
        for key, count in (turn.get("usage") or {}).items():
            if type(count) is int:
                tokens[key] = tokens.get(key, 0) + count
    return {"turns": len(turns), "by_status": by_status, "not_saved_reasons": reasons,
            "turns_with_usage": sum(bool(turn.get("usage")) for turn in turns), "tokens": tokens,
            "seconds": round(sum(turn.get("elapsed_seconds", 0) for turn in turns), 1)}


def write_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


class Report:
    def __init__(self, directory, configuration):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=False)
        self.value = {"format": "reason-commons-evaluation/1", "started": datetime.now(timezone.utc).isoformat(),
                      "configuration": configuration, "status": "running", "runs": [],
                      "release_gate": "incomplete: semantic review, p1/p2 acceptance and participants required"}
        self.save()

    def append(self, run):
        if any(r["id"] == run["id"] for r in self.value["runs"]):
            raise ValueError("Duplicate evaluation run identity")
        self.value["runs"].append(run)
        self.save()

    def record(self, run):
        for index, previous in enumerate(self.value["runs"]):
            if previous["id"] == run["id"]:
                self.value["runs"][index] = run
                self.save()
                return
        self.append(run)

    def finish(self, status="completed"):
        self.value["status"] = status
        self.value["finished"] = datetime.now(timezone.utc).isoformat()
        checks = [item for run in self.value["runs"] for item in run.get("checks", [])]
        self.value["machine_checks"] = {"passed": sum(c["status"] == "pass" for c in checks),
                                        "failed": sum(c["status"] == "fail" for c in checks),
                                        "failed_by_category": {
                                            category: sum(c["status"] == "fail" and c.get("category", "consultant")
                                                          == category for c in checks)
                                            for category in CATEGORIES},
                                        "uncommitted_turns": sum(len(run.get("unjudgeable_turns", []))
                                                                 for run in self.value["runs"])}
        self.value["consultations"] = consultation_summary(self.value["runs"])
        self.save()

    def save(self):
        write_json(self.directory / "report.json", self.value)
        lines = ["# Consultant evaluation", "", "This report is developer evidence, not a v1 release approval.", "",
                 "Configuration: `" + json.dumps(self.value["configuration"], ensure_ascii=False) + "`", ""]
        if "consultations" in self.value:
            lines += ["Consultations: `" + json.dumps(self.value["consultations"], ensure_ascii=False) + "`", ""]
        for run in self.value["runs"]:
            lines += ["## " + run["id"], "", "Case: " + str(run.get("case", "none")), ""]
            for item in run.get("checks", []):
                lines += ["- " + item["status"].upper() + ": " + item["name"] + " — " + str(item["evidence"])]
            lines += [""]
            for turn in run.get("turns", []):
                lines += ["### Turn " + str(turn["number"]), "", "Participant (" + turn["speaker"] + "): " + turn["text"],
                          "", "Result: `" + json.dumps(turn["result"]) + "`", "",
                          "```json", json.dumps(turn.get("new_records", []), ensure_ascii=False, indent=2), "```", ""]
            if run.get("agent"):
                lines += ["Agent capability trace:", "", "```json",
                          json.dumps(run["agent"], ensure_ascii=False, indent=2), "```", ""]
            if "result" in run:
                lines += ["Result: `" + json.dumps(run["result"]) + "`", ""]
            if "recovered" in run:
                lines += ["Recovery: `" + json.dumps(run["recovered"]) + "`", ""]
            if run.get("rubric"):
                lines += ["Semantic review required:", ""] + ["- [ ] " + item for item in run["rubric"]] + [""]
        (self.directory / "report.md").write_text("\n".join(lines), encoding="utf-8")
