#!/usr/bin/env python3
"""Opt-in live semantic evaluation with any configured consultant (Anthropic, LM Studio).

Every fixture in evaluations/fixtures.py (or one, with --case) runs against the chosen provider through the
application use cases, sequentially, each generation attempted once. The evidence (report.json, report.md and
an exported .reasoncase per run) goes to a new directory. Nothing here judges consulting quality: the rubric
waits for an attributed human review (scripts/review_evaluation.py). All data is synthetic, and no credential,
request body or provider message is written.
"""

import argparse
import platform
import signal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from reason_commons.bootstrap import configured_consultant
from evaluations.fixtures import SCENARIOS
from evaluations.report import Report
from evaluations.semantic import run_scenario


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", required=True, help="New evidence directory; existing paths refused")
    parser.add_argument("--provider", required=True, choices=["anthropic", "lm-studio"])
    parser.add_argument("--model", help="Provider model ID; otherwise the provider's default")
    parser.add_argument("--base-url")
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--case", action="append", choices=[s.name for s in SCENARIOS],
                        help="Run only this fixture (repeatable)")
    args = parser.parse_args()
    if not 1 <= args.repeat <= 20:
        parser.error("--repeat must be between 1 and 20")
    consultant = configured_consultant(provider=args.provider, model=args.model, base_url=args.base_url)
    selected = [s for s in SCENARIOS if not args.case or s.name in args.case]
    report = Report(args.output, {"provider": args.provider, "model": args.model or "provider default",
                                  "provider_version": consultant.version, "repeat": args.repeat,
                                  "synthetic_data": True, "selected_semantic_cases": [s.name for s in selected],
                                  "acceptance": "automatic, recorded as Sam's setting in each commons",
                                  "python": platform.python_version(), "platform": platform.platform()})
    for name, attribute in (("consulting-procedure.md", "_procedure"), ("domain-context.md", "_context")):
        if hasattr(consultant, attribute):
            (report.directory / name).write_text(getattr(consultant, attribute))

    def interrupted(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    try:
        for repeat in range(1, args.repeat + 1):
            for scenario in selected:
                print(f"RUN {scenario.name} repetition {repeat}", flush=True)
                run_scenario(report, scenario, consultant, repeat)
    except KeyboardInterrupt:
        report.finish("interrupted")
        return 130
    except Exception as exc:
        # Error categories only; provider exception text can contain credentials.
        report.value["error_category"] = type(exc).__name__
        report.finish("aborted")
        raise
    report.finish()
    print(str(report.directory / "report.md"), flush=True)
    print(report.value["machine_checks"], flush=True)
    print(report.value["consultations"], flush=True)
    print("The semantic rubric waits for an attributed review; the v1 participant gate is separate.", flush=True)
    return 1 if report.value["machine_checks"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
