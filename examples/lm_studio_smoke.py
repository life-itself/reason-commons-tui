#!/usr/bin/env python3
"""One-shot developer integration check; does not replace the future TUI."""

import argparse
import json
import sys

from reason_commons.adapters.lm_studio import LMStudioConsultant
from reason_commons.bootstrap import create_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True, help="New disposable commons directory")
    parser.add_argument("--model", help="Served chat model ID (overrides environment)")
    parser.add_argument("--base-url", help="Server URL (overrides environment)")
    args = parser.parse_args()
    consultant = LMStudioConsultant.from_env(model=args.model, base_url=args.base_url)
    with create_case(args.store, "LM Studio integration check", consultant=consultant) as app:
        result = app.submit("Late deliveries, changing priorities, overtime, and falling morale.",
                            "Sam", base_revision=0, response_target=None)
        print(json.dumps({"provider": consultant.version, "result": result, "case": app.inspect()["case"]},
                         ensure_ascii=False, indent=2))
        return 0 if result["status"] == "saved" else 1


if __name__ == "__main__":
    sys.exit(main())
