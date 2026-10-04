"""Seed a throwaway goals folder for the demo video.

Adds one goal a few weeks in: Mira's example loop, answered with the built-in guide
on the days its answers mention, then the six trees of the analysis its test comes
from. The people and numbers are fictional (see reason_commons.adapters.sample).

    python3 scripts/video/seed_demo.py FOLDER
"""

from functools import partial
from importlib.resources import as_file, files
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from reason_commons.adapters.guided import GuidedConsultant  # noqa: E402
from reason_commons.adapters.ltp_trees import import_trees  # noqa: E402
from reason_commons.adapters.sample import ANSWERS, SPEAKER  # noqa: E402
from reason_commons.bootstrap import create_case, open_case  # noqa: E402

NAME = "From open evening to first practice"
CREATED = "2025-10-08T19:00:00+01:00"
# When each of the example's answers was given; "Thursday 16 October" and "Sunday,
# 9 November" in the answers are 2025 dates.
ANSWERED = ["2025-10-08T19:05:00+01:00", "2025-10-08T19:12:00+01:00", "2025-10-08T19:20:00+01:00",
            "2025-10-12T10:00:00+01:00", "2025-10-12T10:06:00+01:00", "2025-10-12T10:08:00+01:00",
            "2025-10-12T10:10:00+01:00", "2025-10-14T18:30:00+01:00", "2025-11-06T20:00:00+00:00",
            "2025-11-09T09:00:00+00:00"]
TREES = "2025-11-09T09:40:00+00:00"


class Clock:
    def __init__(self, value):
        self.value = value

    def now(self):
        return self.value


def seed(path):
    clock = Clock(CREATED)
    create_case(path, NAME, clock=clock).close()
    with open_case(path, consultant=GuidedConsultant(), clock=clock) as app:
        for answer, when in zip(ANSWERS, ANSWERED):
            clock.value = when
            target = app.workspace()["target"]
            result = app.retain_input(answer, SPEAKER, target["base_revision"], target["response_target"])
            result = app.consult(result["request_id"])
            if result["status"] != "saved":
                raise RuntimeError(f"Demo goal could not be built: {result['status']}")
    clock.value = TREES
    with as_file(files("reason_commons.adapters").joinpath("sample-trees.ltp.yaml")) as source:
        import_trees(path, source, SPEAKER, open_case=partial(open_case, clock=clock))
    with open_case(path, clock=clock) as app:
        # Open on Tests, where the original forecast sits next to the reported result.
        target = app.workspace()["target"]
        app.checkpoint({"view": "tests", "focus": "browse", "draft": "", "caret": 0, "speaker": SPEAKER,
                        "response_target": target["response_target"], "base_revision": target["base_revision"]})


def main():
    goals = Path(sys.argv[1])
    goals.mkdir(parents=True, exist_ok=True)
    seed(goals / "first-practice")


if __name__ == "__main__":
    main()
