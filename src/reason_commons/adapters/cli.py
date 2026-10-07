"""Case utilities, one-shot skill invocations and the launcher for the terminal workspace."""

import argparse
import json
import os
import sys
from pathlib import Path

from reason_commons import __version__
from reason_commons.application.ports import StoreError
from reason_commons.bootstrap import PROVIDERS, configured_consultant, create_case, import_case, open_case, provider_settings
from reason_commons.domain.model import InvalidCase
from reason_commons.domain.model import CONSULT_INTENTS
from reason_commons.application.presentation import VIEWS


EVERYDAY = """\
Make progress on a goal that matters, one small loop at a time.

everyday use:
  reason-commons                      Show your goals and open one (kept in ~/ReasonCommons)
  reason-commons tui FOLDER           Open a goal in a folder of your choice, creating it if needed
  reason-commons resume FOLDER        Open an existing goal; never creates one
  reason-commons export FOLDER FILE   Save a portable copy (.reasoncase)
  reason-commons trees FOLDER         Draw the goal's six trees; --import or --export an .ltp.yaml
  reason-commons decide FOLDER ...    Accept, reject or undo proposals, or choose automatic acceptance
  reason-commons --version            Show the version

The workspace works offline with a built-in guide. Inside it, F1 shows help and
Ctrl+P switches to Claude or a local model, or changes the theme."""

ADVANCED = """\
advanced (scripts, AI agents and diagnostics):
  new, show, inspect, history, import, contribute, decide, retry, receipts, mcp, storage-help
  Run 'reason-commons COMMAND --help' for details. REASON_COMMONS_HOME changes where
  your goals are kept."""


def theme_choice(value):
    """A theme name for --theme, from an id or label in any case, light or dark (``"Shadows dark"``)."""
    from reason_commons.adapters import themes
    name = themes.resolve(value)
    if not name:
        raise argparse.ArgumentTypeError(f"no theme called {value!r}; choose from {', '.join(themes.THEME_NAMES)}")
    return name


THEME_HELP = ("Colour theme for this run: one of the twelve voices of the web app, light or dark, for example "
              "commons-dark or tanizaki; otherwise REASON_COMMONS_THEME, your settings, then yoruba-dark (Chromatics)")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="reason-commons", usage="reason-commons [COMMAND] ...",
                                     description=EVERYDAY, epilog=ADVANCED,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--theme", type=theme_choice, help=THEME_HELP)
    commands = parser.add_subparsers(dest="command", metavar="COMMAND", help=argparse.SUPPRESS, prog="reason-commons")
    for name, summary in (("tui", "Open a goal in the terminal workspace, creating the folder if needed"),
                          ("resume", "Open an existing goal in the terminal workspace")):
        workspace = commands.add_parser(name, help=summary, description=summary)
        workspace.add_argument("store", metavar="FOLDER", nargs="?" if name == "tui" else None,
                               help="Goal folder, for example ~/ReasonCommons/running"
                                    + ("; omit it to choose from your goals" if name == "tui" else ""))
        if name == "tui":
            workspace.add_argument("--name", help="Goal name when creating a new folder (default: folder name)")
        workspace.add_argument("--speaker", help="Your name as recorded with each answer (default: $USER)")
        workspace.add_argument("--provider", choices=["guided", "lm-studio", "anthropic"],
                               help="Consultant; otherwise REASON_COMMONS_PROVIDER or guided (offline)")
        workspace.add_argument("--model", help="Selected provider's model ID")
        workspace.add_argument("--base-url", help="Selected provider's URL")
        workspace.add_argument("--theme", type=theme_choice, default=argparse.SUPPRESS, help=THEME_HELP)
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
    trees = commands.add_parser("trees", help="Draw the six trees, or bring them in or out as an .ltp.yaml file")
    trees.add_argument("store", metavar="FOLDER")
    trees_file = trees.add_mutually_exclusive_group()
    trees_file.add_argument("--import", dest="import_file", metavar="FILE", help="Bring in the trees from an LTP file")
    trees_file.add_argument("--export", dest="export_file", metavar="FILE", help="Write the trees to a new LTP file")
    trees.add_argument("--speaker", help="Your name as recorded with an import (default: $USER)")
    trees.add_argument("--width", type=int, default=100, help="Drawing width in columns")
    trees.add_argument("--tree", choices=["goal", "current_reality", "conflict", "future_reality", "prerequisite",
                                          "transition"], help="Draw only this tree")
    imported = commands.add_parser("import", help="Validate and import into a new editable store")
    imported.add_argument("bundle")
    imported.add_argument("--store", required=True)
    commands.add_parser("storage-help", help="Explain storage integrity guarantees")
    providers = commands.add_parser("providers", help="Check which consultant would be used and whether it is configured; sends no request")
    providers.add_argument("--provider", choices=list(PROVIDERS), help="Check this provider instead of REASON_COMMONS_PROVIDER")
    providers.add_argument("--model", help="Model ID to check")
    providers.add_argument("--base-url", help="Server URL to check")
    providers.add_argument("--json", action="store_true")
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
        command.add_argument("--provider", choices=list(PROVIDERS), help="Consultant provider; otherwise REASON_COMMONS_PROVIDER or lm-studio")
        command.add_argument("--model", help="Selected provider's model ID; otherwise use environment/default")
        command.add_argument("--base-url", help="Selected provider's URL; otherwise use environment/default")
        command.add_argument("--runner", choices=["agent", "procedure"], default="procedure",
                             help="procedure follows the fixed sequence (default); agent executes the Markdown skill with a model")
    decide = commands.add_parser("decide", help="Decide what enters the model, offline; no consultant call",
                                 description="Accept, reject or undo proposals by their refs (see 'show --view "
                                             "backlog'), say a flagged record still holds, or set how later "
                                             "proposals are accepted. A decision that takes more than you named "
                                             "lists it and changes nothing unless you add --confirm.")
    decide.add_argument("store", metavar="FOLDER")
    decide.add_argument("action", choices=["accept", "reject", "undo", "still-holds", "acceptance"])
    decide.add_argument("refs", nargs="+", metavar="REF",
                        help="Record refs such as C3@1; for acceptance, review or automatic")
    decide.add_argument("--speaker", help="Your name as recorded with the decision (default: $USER)")
    decide.add_argument("--confirm", action="store_true", help="Confirm a decision that takes more, or an undo")
    receipts = commands.add_parser("receipts", help="Inspect attempts for a retained request offline")
    receipts.add_argument("store")
    receipts.add_argument("request_id")
    mcp = commands.add_parser("mcp", help="Serve case capabilities to a local MCP client over standard input/output")
    mcp.add_argument("--case-root", required=True, help="Existing directory containing editable case folders")
    mcp.add_argument("--provider", choices=list(PROVIDERS), help="Consultant provider; otherwise REASON_COMMONS_PROVIDER or lm-studio")
    mcp.add_argument("--model", help="Selected provider's model ID")
    mcp.add_argument("--base-url", help="Selected provider's URL")
    mcp.add_argument("--allow-acceptance-setting", action="store_true",
                     help="Let the client switch cases to automatic acceptance; off unless you grant it")
    args = parser.parse_args(argv)
    try:
        if args.command is None and not (sys.stdin.isatty() and sys.stdout.isatty()):
            parser.print_help()
        elif args.command in {None, "tui", "resume"}:
            if not (sys.stdin.isatty() and sys.stdout.isatty()):
                raise ValueError("The workspace needs an interactive terminal; use show/inspect for offline reads")
            if args.command == "resume" and not Path(args.store).expanduser().exists():
                raise ValueError(f"No goal at {args.store}; use 'reason-commons tui {args.store}' to start one")
            if args.theme:  # a flag wins over the environment and settings, which only fill what is unset
                os.environ["REASON_COMMONS_THEME"] = args.theme
            try:
                from reason_commons.adapters.tui import run, run_home
            except ImportError:
                raise ValueError("The workspace needs Textual; reinstall Reason Commons (see the README)") from None
            options = {} if args.command is None else {
                "speaker": args.speaker, "provider": args.provider, "model": args.model, "base_url": args.base_url}
            if getattr(args, "store", None) is None:
                run_home(**options)
            else:
                run(args.store, name=getattr(args, "name", None), **options)
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
        elif args.command == "trees":
            from reason_commons.adapters.ltp_trees import export_trees, import_trees
            from reason_commons.adapters.trees import plain, trees_lines
            if args.import_file:
                speaker = args.speaker or os.environ.get("REASON_COMMONS_SPEAKER") or os.environ.get("USER") or "Me"
                summary = import_trees(args.store, args.import_file, speaker)
                print(f"Brought in {summary['claims']} statements and {summary['links']} links"
                      + (f"; {summary['notes']} items kept as notes." if summary["notes"] else "."))
                waiting = len(summary["proposed"]) - len(summary["accepted"])
                if waiting:
                    print(f"{waiting} proposals wait in the backlog: see 'reason-commons show {args.store} --view "
                          f"backlog', then accept them there or in the workspace.")
            else:
                with open_case(args.store, writable=False) as app:
                    workspace = app.workspace(view="trees")
                if args.export_file:
                    summary = export_trees(workspace, args.export_file)
                    print(f"Wrote {summary['claims']} statements and {summary['links']} links to {args.export_file}")
                else:
                    print(plain(trees_lines(workspace["trees"], args.width, only=args.tree)), end="")
        elif args.command == "import":
            with import_case(args.bundle, args.store) as app:
                print(json.dumps(app.inspect(), ensure_ascii=False))
        elif args.command == "storage-help":
            from reason_commons.application.service import STORAGE_HELP
            print(STORAGE_HELP)
        elif args.command == "providers":
            from reason_commons.adapters.rendering import render_provider_settings
            settings = provider_settings(provider=args.provider, model=args.model, base_url=args.base_url)
            print(json.dumps(settings, ensure_ascii=False, indent=2) if args.json else render_provider_settings(settings), end="\n" if args.json else "")
            return 0 if settings["ready"] else 1
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
            serve(args.case_root, args.model, args.base_url, provider=args.provider,
                  allow_acceptance_setting=args.allow_acceptance_setting)
        elif args.command == "decide":
            speaker = args.speaker or os.environ.get("REASON_COMMONS_SPEAKER") or os.environ.get("USER") or "Me"
            with open_case(args.store) as app:
                revision = app.inspect()["case"]["revision"]
                if args.action == "acceptance":
                    if len(args.refs) != 1:
                        raise ValueError("Name one setting: review or automatic")
                    result = app.set_acceptance(args.refs[0], speaker, revision)
                elif args.action == "still-holds":
                    if len(args.refs) != 1:
                        raise ValueError("Name one flagged record")
                    result = app.still_holds(args.refs[0], speaker, revision)
                else:
                    result = getattr(app, args.action)(args.refs, speaker, revision, confirmed=args.confirm)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "saved" else 1
        else:
            parser.print_help()
        return 0
    except (StoreError, InvalidCase, OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
