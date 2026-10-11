#!/usr/bin/env python3
"""Run every automated v1 case selected by authoritative scenario metadata.

Scope, runnable coverage, live consulting quality and participant evidence are
separate. The historical check_p0.py entry point delegates to this gate.
"""
from collections import Counter
import argparse
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


def verify_cases(expected, report):
    """Check each stable identity AND every expanded row, including passed steps."""
    wanted = Counter()
    names = Counter()
    for scenario in expected:
        identity = next(t for t in scenario.tags if t.startswith("S") and t[1:].isdigit())
        for case in scenario.scenarios if hasattr(scenario, "examples") else [scenario]:
            wanted[identity] += 1
            names[case.name] += 1
    ran = [s for f in report for s in f.get("elements", [])
           if s.get("type") == "scenario" and {"v1", "automated"} <= set(s.get("tags", []))]
    actual = Counter(t for s in ran for t in s["tags"] if t.startswith("S") and t[1:].isdigit())
    if (actual != wanted or Counter(s["name"] for s in ran) != names or
            any(s["status"] != "passed" or
                any(step.get("result", {}).get("status") != "passed" for step in s.get("steps", []))
                for s in ran)):
        raise SystemExit(f"FAIL: incomplete v1 acceptance coverage; expected {dict(wanted)}, got {dict(actual)}")
    return len(wanted), len(ran)


def gate():
    from behave.parser import parse_file
    manifest = json.loads((ROOT / "reason-commons-spec/delivery-phases.json").read_text())
    run("reason-commons-spec/check_bundle.py", "--select", "v1", "--list")
    run("-m", "unittest", "discover", "-s", "reason-commons-spec", "-p", "test_*.py")
    run("-m", "pytest", "-q")
    total_ids = total_cases = 0
    with tempfile.TemporaryDirectory(prefix="reason-commons-acceptance-") as directory:
        for index, source in enumerate(manifest["scenario_roots"]):
            folder = ROOT / "reason-commons-spec" / source["path"]
            expected = [s for path in sorted(folder.glob("*.feature"))
                        for s in parse_file(str(path)).scenarios
                        if {"v1", "automated"} <= set(s.tags)]
            report = Path(directory) / f"acceptance-{index}.json"
            run("-m", "behave", "--runner", source["runner"], str(folder),
                "--tags", "@v1 and @automated", "--format", "json", "--outfile", str(report))
            identities, cases = verify_cases(expected, json.loads(report.read_text()))
            total_ids += identities
            total_cases += cases
            print(f"PASS: {source['path']}: {identities} v1 identities, {cases} expanded cases executed and passed")
    print(f"PASS: complete automated v1 scope: {total_ids} identities, {total_cases} expanded cases")
    print("Live consulting quality, participant usability and assistive-technology evidence remain separate; "
          "see docs/v1-delivery.md and docs/validation.md.")


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    with tempfile.TemporaryDirectory(prefix="reason-commons-gate-") as usage:
        os.environ["REASON_COMMONS_CONFIG"] = str(Path(usage) / "settings.yaml")
        os.environ["REASON_COMMONS_USAGE_LOG"] = str(Path(usage) / "usage.jsonl")
        gate()


if __name__ == "__main__":
    main()
