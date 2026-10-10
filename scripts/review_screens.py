#!/usr/bin/env python3
"""Build a review package: each commons' workspace screens as its operator saw them, beside the rubric.

Every run of a completed semantic evaluation is replayed through the real workspace with its recorded replies (no
model is called) and refused unless the replay reproduces the recorded commons. The package goes beside the report:

    python3 scripts/review_screens.py .evaluation-runs/RUN/report.json

Then ask Claude Code to "publish the review package in .evaluation-runs/RUN/review-package" and share the link
with your reviewers as Contributors. Reviewers need no background: the page explains the task, shows each turn as
what was written and what the assistant replied, and asks plain yes/no questions. Their answers save as they go; as
the page's owner you save each reviewer's review.json from the page, or collect them all at once:

    python3 scripts/review_screens.py .evaluation-runs/RUN/report.json --collect ROWS --output REVIEWS

where ROWS holds the page's stored rows (ask Claude to save the review page's "reviews" collection there). Check each
with scripts/review_evaluation.py --review. --case limits the package to some fixtures, for a shorter review.
"""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from evaluations.review_page import build_review_package, collect_reviews
from evaluations.screens import ReplayMismatch


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report", help="A completed report.json, with its runs' cases beside it")
    parser.add_argument("--output", help="New folder for the package (default: review-package beside the report)")
    parser.add_argument("--provider", choices=["anthropic", "lm-studio"],
                        help="The consultant the workspace names (default: the report's provider)")
    parser.add_argument("--case", action="append", help="Only this fixture or run id (repeatable)")
    parser.add_argument("--collect", metavar="ROWS",
                        help="Write each reviewer's review.json from the page's stored rows into --output")
    args = parser.parse_args()
    if args.collect:
        if not args.output:
            parser.error("--collect needs --output, a folder for the review files")
        package = Path(args.report).parent / "review-package"
        for path in collect_reviews(package, args.collect, args.output):
            print(path)
        return 0
    try:
        page = build_review_package(args.report, args.output, args.provider, args.case)
    except (ReplayMismatch, ValueError, FileExistsError, OSError) as exc:
        parser.error(str(exc))
    print(f"Built {page.parent}")
    print(f'Next: ask Claude Code to "publish the review package in {page.parent}", then share the link with your '
          "reviewers as Contributors. Opened as a file, index.html also works offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
