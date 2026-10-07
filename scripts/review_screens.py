#!/usr/bin/env python3
"""Build a review package: each case's workspace screens as its operator saw them, beside the rubric.

Every run of a completed semantic evaluation is replayed through the real workspace with its recorded replies (no
model is called) and refused unless the replay reproduces the recorded case. The page in the new folder shows the
screens and writes a review.json for scripts/review_evaluation.py:

    python3 scripts/review_screens.py .evaluation-runs/RUN/report.json --output .evaluation-runs/RUN/review-package
    # Open review-package/index.html, judge each criterion, then Save review.json.
    python3 scripts/review_evaluation.py .evaluation-runs/RUN/report.json --review review.json \\
      --output .evaluation-runs/RUN/reviewed.json
"""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from evaluations.review_page import build_review_package
from evaluations.screens import ReplayMismatch


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report", help="A completed report.json, with its runs' cases beside it")
    parser.add_argument("--output", required=True, help="New folder for the page and its screens")
    parser.add_argument("--provider", choices=["anthropic", "lm-studio"],
                        help="The consultant the workspace names (default: the report's provider)")
    args = parser.parse_args()
    try:
        page = build_review_package(args.report, args.output, args.provider)
    except (ReplayMismatch, ValueError, FileExistsError, OSError) as exc:
        parser.error(str(exc))
    print(page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
