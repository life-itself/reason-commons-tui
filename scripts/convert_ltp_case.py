#!/usr/bin/env python3
"""Convert an LTP 1.0 source to a new native continuation commons, offline."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reason_commons.adapters.ltp_conversion import convert_ltp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--speaker", required=True)
    parser.add_argument("--request-text", required=True, help="Exact participant authorization, retained as input")
    args = parser.parse_args()
    try:
        report = convert_ltp(args.source, args.store, args.bundle, speaker=args.speaker, request_text=args.request_text)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
