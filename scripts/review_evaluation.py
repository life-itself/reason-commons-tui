#!/usr/bin/env python3
"""Create a rubric template or validate an attributed review of frozen evidence."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluations.report import write_json
from evaluations.review import apply_review, review_template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    parser.add_argument("--review")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if Path(args.output).exists():
        parser.error("Use a new output path")
    try:
        if args.review:
            result = apply_review(args.report, args.review, args.output)
            print(result["semantic_status"])
            return 0 if result["semantic_status"] == "pass" and not result["machine_checks"]["failed"] else 1
        write_json(args.output, review_template(args.report))
        print(args.output)
        return 0
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
