#!/usr/bin/env python3
"""Build packaged stories from their story files.

Reads src/reason_commons/adapters/stories/NAME.yaml, saves each chapter as one
revision through the application, and exports the result as
stories/NAME.reasoncase. The second-renaissance story is the real commons the
home screen opens read-only; harrowfield is the goal the guided tour opens. Run
it after editing a story file, naming the stories to build:

    python3 scripts/build_story.py harrowfield
    python3 scripts/build_story.py second-renaissance
"""

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reason_commons.adapters.story import build_story, load_story  # noqa: E402
from reason_commons.bootstrap import open_case  # noqa: E402

STORIES = ROOT / "src" / "reason_commons" / "adapters" / "stories"


def build(name):
    story = load_story(name)
    destination = STORIES / f"{name}.reasoncase"
    with tempfile.TemporaryDirectory() as folder:
        path = build_story(Path(folder) / "story", story)
        if destination.exists():
            destination.unlink()
        with open_case(path) as app:
            app.export(str(destination))
    print(f"wrote {destination.relative_to(ROOT)}: {len(story['chapters'])} chapters")


def main(names):
    if not names:
        sys.exit("Name the stories to build, for example: python3 scripts/build_story.py harrowfield")
    for name in names:
        if not (STORIES / f"{name}.yaml").exists():
            sys.exit(f"No story called {name!r} in {STORIES.relative_to(ROOT)}")
        build(name)


if __name__ == "__main__":
    main(sys.argv[1:])
