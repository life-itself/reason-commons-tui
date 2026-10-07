#!/usr/bin/env python3
"""Run the complete p0 gate, the delivered p1 workspace scenarios, every scenario of the two delivered p2
features (trees in conversation; deciding what enters the model) and the other delivered p2 scenarios,
without changing the specification."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
# The p2 features delivered ahead of the rest of p2: every scenario in each must run and pass.
DELIVERED_P2_FEATURES = ["12_trees_in_conversation.feature", "13_proposals_and_review.feature"]
# The p1 workspace scenarios delivered so far. Each runs through the real workspace and must pass;
# the rest of p1 is listed as outstanding on every run, never filtered out silently.
DELIVERED_P1 = ["S07", "S08", "S09", "S10", "S11", "S12", "S13", "S47", "S51", "S54", "S55", "S56", "S57",
                "S58", "S63", "S67", "S68", "S69", "S70", "S72", "S107", "S110", "S113", "S114", "S115", "S116",
                "S117", "S118", "S119", "S120"]
# The p2 scenarios delivered outside the two whole features above; the rest of p2 is listed as outstanding.
DELIVERED_P2 = ["S03", "S04", "S17", "S32", "S37", "S93", "S94", "S95", "S101", "S121"]


def run(*args):
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT))
    result = subprocess.run([sys.executable, *args], cwd=ROOT, env=environment)
    if result.returncode:
        raise SystemExit(result.returncode)


def delivered_phase(phase, delivered, where, directory, parse_file):
    """Run the delivered scenarios of one phase; each must pass, and the rest is named as outstanding."""
    whole = {name for name in DELIVERED_P2_FEATURES} if phase == "p2" else set()
    scenarios = {tag: scenario for path in (ROOT / "reason-commons-spec/features").glob("*.feature")
                 for scenario in parse_file(str(path)).scenarios if phase in scenario.tags
                 for tag in scenario.tags if tag.startswith("S") and tag[1:].isdigit()}
    in_whole = {tag for path in (ROOT / "reason-commons-spec/features").glob("*.feature") if path.name in whole
                for scenario in parse_file(str(path)).scenarios for tag in scenario.tags if tag in scenarios}
    if not set(delivered) <= set(scenarios):
        raise SystemExit(f"FAIL: not {phase} scenarios: {sorted(set(delivered) - set(scenarios))}")
    output = Path(directory) / f"delivered-{phase}.json"
    run("-m", "behave", "--tags", ",".join("@" + tag for tag in delivered), "--format", "json",
        "--outfile", str(output))
    # The report lists every scenario, the skipped ones too; keep the delivered ones.
    ran = [s for feature in json.loads(output.read_text()) for s in feature.get("elements", [])
           if s.get("type") == "scenario" and set(s.get("tags", [])) & set(delivered)]
    cases = sum(sum(len(e.table.rows) for e in scenarios[tag].examples) if hasattr(scenarios[tag], "examples") else 1
                for tag in delivered)
    ids = {t for s in ran for t in s["tags"] if t.startswith("S") and t[1:].isdigit()}
    if len(ran) != cases or ids != set(delivered) or any(s["status"] != "passed" for s in ran):
        raise SystemExit(f"FAIL: incomplete {phase} acceptance coverage")
    outstanding = sorted(set(scenarios) - set(delivered) - in_whole, key=lambda tag: int(tag[1:]))
    total = len(set(scenarios) - in_whole)
    print(f"PASS: {len(delivered)} of {total} {phase} scenarios {where} ({len(ran)} cases) executed and passed; "
          f"not yet delivered: {', '.join(outstanding) or 'none'}")


def main():
    run("reason-commons-spec/check_bundle.py", "--select", "p0", "--list")
    run("-m", "unittest", "discover", "-s", "reason-commons-spec", "-p", "test_*.py")
    run("-m", "pytest", "-q")
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "acceptance.json"
        run("-m", "behave", "--tags", "@p0 and @automated", "--format", "json", "--outfile", str(output))
        features = json.loads(output.read_text())
        selected = [scenario for feature in features for scenario in feature.get("elements", [])
                    if "p0" in scenario.get("tags", [])]
        # Determine membership from the authoritative features, independent of results.
        from behave.parser import parse_file
        expected = {tag for path in (ROOT / "reason-commons-spec/features").glob("*.feature")
                    for scenario in parse_file(str(path)).scenarios if "p0" in scenario.tags
                    for tag in scenario.tags if tag.startswith("S") and tag[1:].isdigit()}
        actual = {tag for scenario in selected for tag in scenario["tags"]
                  if tag.startswith("S") and tag[1:].isdigit()}
        if len(selected) != len(expected) or actual != expected or any(s["status"] != "passed" for s in selected):
            raise SystemExit("FAIL: incomplete p0 acceptance coverage")
        print(f"PASS: all {len(expected)} authoritative p0 scenarios executed and passed: {', '.join(sorted(actual))}")
        for name in DELIVERED_P2_FEATURES:
            feature = ROOT / "reason-commons-spec/features" / name
            output_file = Path(directory) / (feature.stem + ".json")
            run("-m", "behave", "--include", feature.name, "--format", "json", "--outfile", str(output_file))
            ran = [s for item in json.loads(output_file.read_text()) for s in item.get("elements", [])
                   if s.get("type") == "scenario"]
            cases = sum(sum(len(e.table.rows) for e in s.examples) if hasattr(s, "examples") else 1
                        for s in parse_file(str(feature)).scenarios)
            if len(ran) != cases or any(s["status"] != "passed" for s in ran):
                raise SystemExit(f"FAIL: incomplete acceptance coverage for {name}")
            ids = sorted({t for s in ran for t in s["tags"] if t.startswith("S") and t[1:].isdigit()},
                         key=lambda tag: int(tag[1:]))
            print(f"PASS: all {len(ran)} cases of {name} executed and passed: {', '.join(ids)}")
        for phase, delivered, where in (("p1", DELIVERED_P1, "through the workspace"),
                                        ("p2", DELIVERED_P2, "outside the two whole p2 features")):
            delivered_phase(phase, delivered, where, directory, parse_file)
        conversation = Path(directory) / "conversation.json"
        run("-m", "behave", "--runner", "tests.conversation.runner:ConversationRunner",
            "tests/conversation/features", "--format", "json", "--outfile", str(conversation))
        scenarios = [s for feature in json.loads(conversation.read_text()) for s in feature.get("elements", [])]
        expected_names = {s.name for path in (ROOT / "tests/conversation/features").glob("*.feature")
                          for s in parse_file(str(path)).walk_scenarios()}
        if len(scenarios) != len(expected_names) or {s["name"] for s in scenarios} != expected_names or any(
                s["status"] != "passed" for s in scenarios):
            raise SystemExit("FAIL: incomplete conversational acceptance coverage")
        print(f"PASS: all {len(scenarios)} conversational scenarios executed and passed")


if __name__ == "__main__":
    main()
