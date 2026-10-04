#!/usr/bin/env python3
"""Run the complete p0 gate, plus every delivered p2 tree scenario, without changing the specification."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT))
    result = subprocess.run([sys.executable, *args], cwd=ROOT, env=environment)
    if result.returncode:
        raise SystemExit(result.returncode)


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
        # The trees feature is delivered ahead of the rest of p2: every scenario in it must run and pass.
        trees_feature = ROOT / "reason-commons-spec/features/12_trees_in_conversation.feature"
        trees_output = Path(directory) / "trees.json"
        run("-m", "behave", "--include", trees_feature.name, "--format", "json", "--outfile", str(trees_output))
        ran = [s for feature in json.loads(trees_output.read_text()) for s in feature.get("elements", [])
               if s.get("type") == "scenario"]
        cases = sum(sum(len(e.table.rows) for e in s.examples) if hasattr(s, "examples") else 1
                    for s in parse_file(str(trees_feature)).scenarios)
        if len(ran) != cases or any(s["status"] != "passed" for s in ran):
            raise SystemExit("FAIL: incomplete trees acceptance coverage")
        ids = sorted({t for s in ran for t in s["tags"] if t.startswith("S") and t[1:].isdigit()})
        print(f"PASS: all {len(ran)} trees cases executed and passed: {', '.join(ids)}")
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
