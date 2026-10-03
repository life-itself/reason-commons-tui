#!/usr/bin/env python3
"""Opt-in live checks. All data is synthetic; output is retained for review."""

import argparse
import math
import platform
import signal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from reason_commons.adapters.lm_studio import LMStudioConsultant
from evaluations.fixtures import SCENARIOS
from evaluations.report import Report
from evaluations.semantic import run_scenario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New evidence directory; existing paths refused")
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--suite", choices=["semantic", "agent", "recovery", "all"], default="all")
    parser.add_argument("--case", choices=[s.name for s in SCENARIOS], help="Select one semantic fixture")
    args = parser.parse_args()
    if not 1 <= args.repeat <= 20:
        parser.error("--repeat must be between 1 and 20")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be positive and finite")
    consultant = LMStudioConsultant.from_env(model=args.model, base_url=args.base_url)
    consultant.timeout = args.timeout
    report = Report(args.output, {"model": args.model, "provider_version": consultant.version,
                                 "repeat": args.repeat, "suite": args.suite, "synthetic_data": True,
                                 "selected_semantic_cases": [s.name for s in SCENARIOS if not args.case or s.name == args.case],
                                 "python": platform.python_version(), "platform": platform.platform()})
    (report.directory / "consulting-procedure.md").write_text(consultant._procedure)
    (report.directory / "domain-context.md").write_text(consultant._context)
    try:
        report.value["configuration"]["model_metadata"] = consultant.model_metadata()
    except Exception:
        report.value["configuration"]["model_metadata"] = "unavailable; no inference about loaded context"
    report.save()
    def interrupted(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    try:
        execute(report, consultant, args)
    except KeyboardInterrupt:
        report.finish("interrupted")
        return 130
    except Exception as exc:
        # Error categories only; arbitrary provider exception text can contain credentials.
        report.value["error_category"] = type(exc).__name__
        report.finish("aborted")
        raise
    report.finish()
    print(str(report.directory / "report.md"), flush=True)
    print(report.value["machine_checks"], flush=True)
    print("Semantic review and the v1 release gates remain incomplete.", flush=True)
    return 1 if report.value["machine_checks"]["failed"] else 0


def execute(report, consultant, args):
    # Sequential generation avoids competition for the local model and records every attempt.
    if args.suite in {"semantic", "all"}:
        for repeat in range(1, args.repeat + 1):
            for scenario in SCENARIOS:
                if args.case and args.case != scenario.name:
                    continue
                print(f"RUN semantic {scenario.name} repetition {repeat}", flush=True)
                run_scenario(report, scenario, consultant, repeat)
    if args.suite in {"agent", "all"}:
        from evaluations.agent import run_agent_suite
        run_agent_suite(report, consultant, args.repeat)
    if args.suite in {"recovery", "all"}:
        from evaluations.recovery import run_recovery_suite
        run_recovery_suite(report, consultant)


if __name__ == "__main__":
    raise SystemExit(main())
