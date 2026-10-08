#!/usr/bin/env python3
"""Opt-in live replay of the live procedure's consultant steps (evaluations/procedure.py), in review mode.

Each contribution is attempted once, in the procedure's order, accepting what waits between steps as the
procedure does. The evidence (report.json, report.md and an exported .reasoncase per run) goes to a new
directory: how each reply ended, why any was not saved, tokens and time. It judges no consulting quality.
All data is synthetic, and no credential, request body or provider message is written.
"""

import argparse
import platform
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from reason_commons.bootstrap import configured_consultant
from evaluations.procedure import STEPS, run_procedure
from evaluations.report import Report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", required=True, help="New evidence directory; existing paths refused")
    parser.add_argument("--provider", required=True, choices=["anthropic", "lm-studio"])
    parser.add_argument("--model", help="Provider model ID; otherwise the provider's default")
    parser.add_argument("--base-url")
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 10:
        parser.error("--repeat must be between 1 and 10")
    consultant = configured_consultant(provider=args.provider, model=args.model, base_url=args.base_url)
    report = Report(args.output, {"provider": args.provider, "model": args.model or "provider default",
                                  "provider_version": consultant.version, "repeat": args.repeat,
                                  "synthetic_data": True, "steps": [step for step, *_ in STEPS],
                                  "acceptance": "review; the operator accepts what waits between steps",
                                  "python": platform.python_version(), "platform": platform.platform()})
    try:
        for repeat in range(1, args.repeat + 1):
            print(f"RUN procedure repetition {repeat}", flush=True)
            run_procedure(report, consultant, repeat)
    except KeyboardInterrupt:
        report.finish("interrupted")
        return 130
    except Exception as exc:
        report.value["error_category"] = type(exc).__name__
        report.finish("aborted")
        raise
    report.finish()
    print(str(report.directory / "report.md"), flush=True)
    print(report.value["consultations"], flush=True)
    return 1 if report.value["machine_checks"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
