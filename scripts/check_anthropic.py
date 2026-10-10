#!/usr/bin/env python3
"""Explicit provider check; never retries or changes a participant's commons.

A billed smoke consultation is counted in the usage log (entry "check"), like any other reply."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reason_commons.adapters.anthropic import AnthropicConsultant
from reason_commons.bootstrap import create_case, open_case, usage_session


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="Count the complete pending prompt, without inference or writes")
    parser.add_argument("--smoke", action="store_true", help="One billed synthetic consultation in a temporary commons")
    parser.add_argument("--model", help="Claude model ID; otherwise REASON_COMMONS_ANTHROPIC_MODEL or the default")
    parser.add_argument("--output", help="New JSON verification file; contains no key, commons text or model output")
    args = parser.parse_args()
    if args.output and Path(args.output).exists():
        parser.error("Choose a new output file")
    usage = usage_session("check")
    consultant = AnthropicConsultant.from_env(model=args.model, usage=usage.record)
    metadata = consultant.model_metadata()
    report = {"model": metadata["id"], "max_input_tokens": metadata.get("max_input_tokens"),
              "max_tokens": metadata.get("max_tokens"), "participant_consultations": 0}
    if args.case:
        with open_case(args.case, writable=False) as app:
            workspace = app.workspace()
            pending = workspace["pending_requests"]
            if not pending:
                raise ValueError("No pending contribution to count")
            request = {"input": pending[-1]["input"], "case": app.inspect()["case"],
                       "sources": app.sources()["sources"]}
            baseline = sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
            report["case_revision"] = workspace["revision"]
            report["pending_request_id"] = request["input"]["request_id"]
        report["complete_prompt_input_tokens"] = consultant.count_tokens(request)
        if type(report["max_input_tokens"]) is int:
            report["context_fits"] = report["complete_prompt_input_tokens"] + consultant.max_tokens <= report["max_input_tokens"]
        with open_case(args.case, writable=False) as app:
            after = {"input": app.workspace()["pending_requests"][-1]["input"],
                     "case": app.inspect()["case"], "sources": app.sources()["sources"]}
            report["case_unchanged"] = baseline == sha256(json.dumps(after, sort_keys=True).encode()).hexdigest()
    if args.smoke:
        with tempfile.TemporaryDirectory(prefix="reason-commons-anthropic-") as directory:
            with create_case(Path(directory) / "synthetic", "Synthetic provider verification", consultant=consultant) as app:
                result = app.submit("This is a synthetic integration check. We want to reduce missed deliveries. "
                                    "We have not agreed a numerical target or safeguards yet.",
                                    "Synthetic test participant", base_revision=0, response_target=None)
                spent = [entry["usd"] for entry in usage.since(0)]
                report["synthetic_smoke"] = {"status": result["status"], "revision": app.inspect()["case"]["revision"],
                                             "provider_version": consultant.version,
                                             "usage": consultant.last_usage,
                                             # An estimate at list prices; the Anthropic Console has the bill.
                                             "estimated_cost_usd": None if None in spent or not spent
                                             else str(sum(spent))}
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if (report.get("case_unchanged", True) and report.get("context_fits", True)
                 and report.get("synthetic_smoke", {"status": "saved"})["status"] == "saved") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
