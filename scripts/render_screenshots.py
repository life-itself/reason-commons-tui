"""Render the README and docs screenshots from the real workspace.

Runs the Textual app headlessly with the built-in guide and fixed dates, so the
pictures show exactly what a user sees. Writes SVG files to docs/images/ and, when
Chromium (CHROMIUM, or the usual install paths) and Pillow are available, PNG
copies that render the same everywhere; the README uses the PNGs. Run it after changing what the workspace shows:

    python3 scripts/render_screenshots.py
"""

import asyncio
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reason_commons.adapters.sample import ANSWERS, build_sample  # noqa: E402
from reason_commons.adapters.tui import GoalsApp, ReasonCommonsApp  # noqa: E402
from reason_commons.bootstrap import configured_consultant, create_case, open_case  # noqa: E402

OUT = ROOT / "docs" / "images"
SPEAKER = "Mira"
GOAL = "From open evening to first practice"


class FixedClock:
    def __init__(self, value):
        self.value = value

    def now(self):
        return self.value


def workspace(path):
    return ReasonCommonsApp(path, SPEAKER, "guided", lambda consultant: open_case(path, consultant=consultant),
                            lambda provider: configured_consultant(provider=provider))


async def shoot(app, name, size, before=None):
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        if before:
            before(app)
            await pilot.pause()
        app.save_screenshot(filename=f"{name}.svg", path=str(OUT))


async def render(folder):
    goals = folder / "ReasonCommons"
    goals.mkdir()
    build_sample(goals / "first-practice", answers=ANSWERS[:8], view="next", name=GOAL,
                 clock=FixedClock("2026-11-06T19:30:00+00:00"))
    create_case(goals / "map-review", "Agree how our strategy map gets reviewed",
                clock=FixedClock("2026-10-02T07:00:00+00:00")).close()
    await shoot(GoalsApp(goals), "home", (100, 22))
    create_case(folder / "new", "my-first-goal").close()
    await shoot(workspace(folder / "new"), "welcome", (120, 36))
    await shoot(workspace(goals / "first-practice"), "in-progress", (120, 36))
    for name, count in (("tutorial-measure", 1), ("tutorial-forecast", 4), ("tutorial-review", 9)):
        step = build_sample(folder / name, answers=ANSWERS[:count], view="next", name=GOAL,
                            clock=FixedClock("2026-10-14T20:00:00+00:00"))
        await shoot(workspace(step), name, (120, 36))
    finished = build_sample(folder / "finished", name=GOAL, clock=FixedClock("2026-11-09T09:00:00+00:00"))
    await shoot(workspace(finished), "forecast-vs-result", (120, 36))


def can_make_png():
    try:
        import PIL  # noqa: F401
    except ImportError:
        return False
    return True


def chromium():
    candidates = [os.environ.get("CHROMIUM"), shutil.which("chromium"), shutil.which("google-chrome"),
                  *sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))]
    return next((str(c) for c in candidates if c and Path(c).exists()), None)


def to_png(browser, svg):
    # The window matches the SVG's own size, so the PNG has no margins.
    view_box = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg.read_text(encoding="utf-8"))
    width, height = (math.ceil(float(value)) for value in view_box.groups())
    page = svg.with_suffix(".html")
    page.write_text(f'<html><body style="margin:0;background:transparent"><img src="{svg.name}" '
                    f'style="display:block;width:{width}px;height:{height}px"></body></html>', encoding="utf-8")
    subprocess.run([browser, "--headless=new", "--no-sandbox", "--hide-scrollbars", "--disable-gpu",
                    "--force-device-scale-factor=1",
                    f"--screenshot={svg.with_suffix('.png')}", f"--window-size={width},{height + 200}",
                    "--default-background-color=00000000", page.as_uri()],
                   check=True, capture_output=True, timeout=60)
    # Chromium's window includes space it does not draw into; trim to the picture itself.
    from PIL import Image
    with Image.open(svg.with_suffix(".png")) as image:
        image.crop((0, 0, width, height)).save(svg.with_suffix(".png"), optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        asyncio.run(render(Path(folder)))
    browser = chromium() if can_make_png() else None
    for svg in sorted(OUT.glob("*.svg")):
        if svg.name == "loop.svg":
            continue
        if browser:
            try:
                to_png(browser, svg)
            finally:
                svg.with_suffix(".html").unlink(missing_ok=True)
        print(f"wrote {svg.relative_to(ROOT)}" + (" and .png" if browser else ""))


if __name__ == "__main__":
    main()
