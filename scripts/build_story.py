#!/usr/bin/env python3
"""Build the packaged example story from its story file.

Reads src/reason_commons/adapters/stories/second-renaissance.yaml, saves each
chapter as one revision through the application, and exports the result as
stories/second-renaissance.reasoncase, which the home screen opens read-only.
Run it after editing the story file:

    python3 scripts/build_story.py
"""

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reason_commons.adapters.story import build_story, load_story  # noqa: E402
from reason_commons.bootstrap import open_case  # noqa: E402

DESTINATION = ROOT / "src" / "reason_commons" / "adapters" / "stories" / "second-renaissance.reasoncase"


def main():
    story = load_story()
    with tempfile.TemporaryDirectory() as folder:
        path = build_story(Path(folder) / "story", story)
        if DESTINATION.exists():
            DESTINATION.unlink()
        with open_case(path) as app:
            app.export(str(DESTINATION))
    print(f"wrote {DESTINATION.relative_to(ROOT)}: {len(story['chapters'])} chapters")


if __name__ == "__main__":
    main()
