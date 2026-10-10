"""Build the source-backed dogfood handoff through ordinary application use cases."""
import argparse
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from reason_commons.adapters.commons import build_commons  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/restoration/reason-commons.reasoncase')
    parser.add_argument('--acceptance', choices=['automatic', 'review'], default='automatic')
    parser.add_argument('--pending', action='store_true', help='Import for review without adopting the reasoning')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        with build_commons(Path(folder) / 'case', acceptance='review' if args.pending else args.acceptance,
                           adopted=not args.pending) as app:
            app.export(str(args.output))
    print(args.output)


if __name__ == '__main__':
    main()
