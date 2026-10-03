"""Case utilities, one-shot skill invocations and the launcher for the terminal workspace."""

import argparse
import json
import sys
from pathlib import Path

from reason_commons import __version__
from reason_commons.application.ports import StoreError
from reason_commons.bootstrap import configured_consultant, create_case, import_case, open_case
from reason_commons.domain.model import InvalidCase
from reason_commons.domain.model import CONSULT_INTENTS
from reason_commons.application.presentation import VIEWS


def main(argv=None):
    parser = argparse.ArgumentParser(prog="reason-commons", description="Reason Commons durable cases and contribution skill")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")
    for name in ("tui", "resume"):
        workspace = commands.add_parser(name, help="Open the terminal workspace; tui also creates a missing case")
        workspace.add_argument("store", help="Case folder, for example ~/ReasonCommons/running")
        workspace.add_argument("--name", help="Case name when creating a new case (default: folder name)")
        workspace.add_argument("--speaker", help="Your name as recorded with each answer (default: $USER)")
        workspace.add_argument("--provider", choices=["guided", "lm-studio", "anthropic"],
                               help="Consultant; otherwise REASON_COMMONS_PROVIDER or guided (offline)")
        workspace.add_argument("--model", help="Selected provider's model ID")
        workspace.add_argument("--base-url", help="Selected provider's URL")
    new = commands.add_parser("new", help="Create a durable minimal case (p0)")
    new.add_argument("--store", required=True)
    new.add_argument("--name", default="Untitled case")
    for name in ("inspect", "history"):
        item = commands.add_parser(name, help="Read stored records offline")
        item.add_argument("store")
        item.add_argument("--json", action="store_true")
    show = commands.add_parser("show", help="Open or inspect the case workspace offline")
    show.add_argument("store")
    show.add_argument("--view", choices=VIEWS, default="next")
    show.add_argument("--revision", type=int)
    show.add_argument("--select", help="Exact saved record or source reference, for detailed inspection")
    show.add_argument("--format", choices=["text", "markdown", "json", "mermaid"], default="text")
    export = commands.add_parser("export", help="Export a portable .reasoncase archive")
    export.add_argument("store")
    export.add_argument("bundle")
    imported = commands.add_parser("import", help="Validate and import into a new editable store")
    imported.add_argument("bundle")
    imported.add_argument("--store", required=True)
    commands.add_parser("storage-help", help="Explain storage integrity guarantees")
    contribution = commands.add_parser("contribute", help="Run the contribution skill once against an existing case")
    contribution.add_argument("store")
    contribution.add_argument("--speaker", required=True, help="Declared participant attribution")
    text = contribution.add_mutually_exclusive_group(required=True)
    text.add_argument("--text", help="Exact literal contribution")
    text.add_argument("--text-file", help="UTF-8 contribution file; - reads standard input, preserving newlines")
    contribution.add_argument("--ownership", action="append", default=[], help="Explicitly declare an owner; repeatable")
    contribution.add_argument("--observed", action="store_true", help="Explicitly declare supplied evidence as observed")
    contribution.add_argument("--intent", choices=sorted({"answer"} | CONSULT_INTENTS), default="answer")
    contribution.add_argument("--base-revision", type=int, help="Revision of the question being answered")
    contribution.add_argument("--response-target", help="Exact displayed question reference, or none for an empty case")
    retry = commands.add_parser("retry", help="Explicitly retry an original retained request, once")
    retry.add_argument("store")
    retry.add_argument("request_id")
    for command in (contribution, retry):
        command.add_argument("--json", action="store_true", help="Include structured state and diagnostic trace")
        command.add_argument("--format", choices=["text", "markdown"], default="text")
        command.add_argument("--provider", choices=["lm-studio", "anthropic"], help="Consultant provider; otherwise REASON_COMMONS_PROVIDER or lm-studio")
        command.add_argument("--model", help="Selected provider's model ID; otherwise use environment/default")
        command.add_argument("--base-url", help="Selected provider's URL; otherwise use environment/default")
        command.add_argument("--runner", choices=["agent", "procedure"], default="procedure",
                             help="procedure follows the fixed sequence (default); agent executes the Markdown skill with a model")
    receipts = commands.add_parser("receipts", help="Inspect attempts for a retained request offline")
    receipts.add_argument("store")
    receipts.add_argument("request_id")
    mcp = commands.add_parser("mcp", help="Serve case capabilities to a local MCP client over standard input/output")
    mcp.add_argument("--case-root", required=True, help="Existing directory containing editable case folders")
    mcp.add_argument("--provider", choices=["lm-studio", "anthropic"], help="Consultant provider; otherwise REASON_COMMONS_PROVIDER or lm-studio")
    mcp.add_argument("--model", help="Selected provider's model ID")
    mcp.add_argument("--base-url", help="Selected provider's URL")
    args = parser.parse_args(argv)
    try:
        if args.command in {"tui", "resume"}:
            if not (sys.stdin.isatty() and sys.stdout.isatty()):
                raise ValueError("The workspace needs an interactive terminal; use show/inspect for offline reads")
            if args.command == "resume" and not Path(args.store).expanduser().exists():
                raise ValueError(f"No case at {args.store}; use 'reason-commons tui {args.store}' to create one")
            try:
                from reason_commons.adapters.tui import run
            except ImportError:
                raise ValueError("The workspace needs Textual: python3 -m pip install -e '.[tui]'") from None
            run(args.store, name=args.name, speaker=args.speaker, provider=args.provider,
                model=args.model, base_url=args.base_url)
        elif args.command == "new":
            with create_case(args.store, args.name) as app:
                print(json.dumps(app.inspect(), ensure_ascii=False))
        elif args.command in {"inspect", "history"}:
            with open_case(args.store, writable=False) as app:
                result = app.inspect() if args.command == "inspect" else app.history()
            print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2))
        elif args.command == "show":
            from reason_commons.adapters.rendering import workspace_output
            with open_case(args.store, writable=False) as app:
                output = workspace_output(app.workspace(view=args.view, revision=args.revision, selection=args.select))
            print(json.dumps(output, ensure_ascii=False, indent=2) if args.format == "json" else
                  output["rendered"][args.format], end="\n" if args.format == "json" else "")
        elif args.command == "export":
            with open_case(args.store) as app:
                app.export(args.bundle)
        elif args.command == "import":
            with import_case(args.bundle, args.store) as app:
                print(json.dumps(app.inspect(), ensure_ascii=False))
        elif args.command == "storage-help":
            from reason_commons.application.service import STORAGE_HELP
            print(STORAGE_HELP)
        elif args.command == "receipts":
            with open_case(args.store, writable=False) as app:
                print(json.dumps(app.receipts(args.request_id), ensure_ascii=False, indent=2))
        elif args.command in {"contribute", "retry"}:
            from reason_commons.adapters.invocation import run_contribution
            consultant = configured_consultant(provider=args.provider, model=args.model, base_url=args.base_url)
            if args.runner == "agent":
                from reason_commons.adapters.lm_studio import LMStudioConsultant
                if not isinstance(consultant, LMStudioConsultant):
                    raise ValueError("The experimental agent runner currently requires lm-studio; use --runner procedure or the Codex skill with Anthropic")
            if args.command == "contribute" and (args.base_revision is None) != (args.response_target is None):
                raise ValueError("Supply both --base-revision and --response-target (none when absent)")
            options = {"retry_request": args.request_id} if args.command == "retry" else {
                "text": args.text if args.text is not None else
                sys.stdin.read() if args.text_file == "-" else Path(args.text_file).read_text(encoding="utf-8"),
                "speaker": args.speaker, "intent": args.intent,
                "target": None if args.base_revision is None else {"base_revision": args.base_revision,
                    "response_target": None if args.response_target == "none" else args.response_target},
                "declarations": {
                    **({"ownership": args.ownership} if args.ownership else {}),
                    **({"evidence": ["observed"]} if args.observed else {})}}
            with open_case(args.store, consultant=consultant) as app:
                result = run_contribution(app, consultant, runner=args.runner, **options)
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["rendered"][args.format],
                  end="\n" if args.json else "")
            return 0 if result["procedure_completed"] and result["result"]["status"] == "saved" else 1
        elif args.command == "mcp":
            from reason_commons.adapters.mcp_server import serve
            serve(args.case_root, args.model, args.base_url, provider=args.provider)
        else:
            parser.print_help()
        return 0
    except (StoreError, InvalidCase, OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
