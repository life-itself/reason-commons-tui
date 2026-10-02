"""Offline p0 utilities. The persistent human workspace is the p1 increment."""

import argparse
import json
import sys

from reason_commons import __version__
from reason_commons.application.ports import StoreError
from reason_commons.bootstrap import create_case, import_case, open_case
from reason_commons.domain.model import InvalidCase


def main(argv=None):
    parser = argparse.ArgumentParser(prog="reason-commons", description="Reason Commons p0 durable case utilities")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")
    new = commands.add_parser("new", help="Create a durable minimal case (p0)")
    new.add_argument("--store", required=True)
    new.add_argument("--name", default="Untitled case")
    for name in ("inspect", "history"):
        item = commands.add_parser(name, help="Read stored records offline")
        item.add_argument("store")
        item.add_argument("--json", action="store_true")
    export = commands.add_parser("export", help="Export a portable .reasoncase archive")
    export.add_argument("store")
    export.add_argument("bundle")
    imported = commands.add_parser("import", help="Validate and import into a new editable store")
    imported.add_argument("bundle")
    imported.add_argument("--store", required=True)
    commands.add_parser("storage-help", help="Explain storage integrity guarantees")
    args = parser.parse_args(argv)
    try:
        if args.command == "new":
            with create_case(args.store, args.name) as app:
                print(json.dumps(app.inspect(), ensure_ascii=False))
        elif args.command in {"inspect", "history"}:
            # Archives are inspected through a temporary read-only import below.
            from pathlib import Path
            if Path(args.store).suffix == ".reasoncase":
                import tempfile
                with tempfile.TemporaryDirectory() as temporary:
                    with import_case(args.store, Path(temporary) / "case") as app:
                        result = app.inspect() if args.command == "inspect" else app.history()
            else:
                with open_case(args.store, writable=False) as app:
                    result = app.inspect() if args.command == "inspect" else app.history()
            print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2))
        elif args.command == "export":
            with open_case(args.store) as app:
                app.export(args.bundle)
        elif args.command == "import":
            with import_case(args.bundle, args.store) as app:
                print(json.dumps(app.inspect(), ensure_ascii=False))
        elif args.command == "storage-help":
            from reason_commons.application.service import STORAGE_HELP
            print(STORAGE_HELP)
        else:
            parser.print_help()
        return 0
    except (StoreError, InvalidCase, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

