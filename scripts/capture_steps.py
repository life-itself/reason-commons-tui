#!/usr/bin/env python3
"""Capture one screenshot per step of every feature, named by feature, scenario and step.

Runs the specification features and the conversation features through behave, with the same step definitions and
environments as the gate, and after each step that executes saves what the participant would see at that point:

- a step that drives the live workspace (the workspace and question steps) is captured from that running workspace,
  so focus, typed text and open panes are as the step left them;
- an accessible-presentation step is captured as the text the presentation has written so far, in a terminal of the
  size the scenario gives;
- any other step is captured from a fresh workspace opened on a copy of the case as it stands after the step, so
  the case itself is never locked or changed by the capture.

Steps without a step definition are not run by behave, so they have no picture; they are listed in the manifest.

Pictures go to docs/screenshots/<feature>/<scenario>/<NN>-<keyword>-<step>.png. The folder is generated: each run
replaces the previous run's pictures, so nothing stale is left behind. MANIFEST.json beside them lists every step,
its outcome, and where its picture came from.

    python3 scripts/capture_steps.py                     # every feature, four at a time
    python3 scripts/capture_steps.py --feature PATH      # one feature file (what the run above starts for each)

PNG pictures use the same Chromium path as scripts/render_screenshots.py, so Pillow and Chromium must be available.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "scripts")]

OUT = ROOT / "docs" / "screenshots"
SPEC = ROOT / "reason-commons-spec" / "features"
CONVERSATION = ROOT / "tests" / "conversation" / "features"
# Step definitions that drive the live workspace: their picture is the running workspace, not a fresh one.
LIVE_MODULES = {"workspace_steps.py", "question_steps.py"}
ACCESSIBLE_MODULES = {"accessible_steps.py"}
EXECUTED = {"passed", "failed", "error"}
SIZE = (120, 40)
MARKER = "MANIFEST.json"


class Refusing:
    """The consultant a capture opens with: showing a case must never ask Claude a question."""
    version = "capture/refusing"

    def propose(self, request):
        raise RuntimeError("a screenshot never asks the consultant")


def slug(text, limit):
    words = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return words[:limit].rstrip("-") or "untitled"


def feature_title(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Feature:"):
            return line[len("Feature:"):].strip()
    raise ValueError(f"no Feature: line in {path}")


def feature_folder(path):
    """The feature's title, prefixed by its file number so the folders read in specification order."""
    number = re.match(r"(\d+)_", path.stem)
    name = slug(feature_title(path), 90)
    return f"{number.group(1)}-{name}" if number else name


class Capture:
    """Behave's after_step hook: counts the steps of each scenario and saves one picture for each executed step."""

    def __init__(self, directory):
        self.directory = directory
        self.scenario, self.number, self.entries = None, 0, []
        self.folders = {}  # scenario identity -> its folder name, unique within the feature

    def folder_for(self, scenario):
        if id(scenario) not in self.folders:
            tag = next((t for t in scenario.tags if re.fullmatch(r"S\d+", t)), None)
            base = f"{tag}-{slug(scenario.name, 110)}" if tag else slug(scenario.name, 120)
            taken = set(self.folders.values())
            name, copies = base, 1
            while name in taken:
                copies += 1
                name = f"{base}-{copies}"
            self.folders[id(scenario)] = name
        return self.folders[id(scenario)]

    def __call__(self, context, step, registry):
        if context.scenario is not self.scenario:
            self.scenario, self.number = context.scenario, 0
        self.number += 1
        entry = {"feature": context.feature.name, "scenario": context.scenario.name,
                 "step": f"{step.keyword} {step.name}", "number": self.number, "status": step.status.name,
                 "source": None, "image": None}
        if step.status.name in EXECUTED:
            try:
                svg, source = self.screen(context, step, registry)
            except Exception as error:  # a picture never changes the outcome of the step it follows
                svg, source = None, None
                entry["error"] = f"{type(error).__name__}: {error}"
            if svg is not None:
                folder = OUT / self.directory / self.folder_for(context.scenario)
                folder.mkdir(parents=True, exist_ok=True)
                name = f"{self.number:02d}-{step.keyword.lower()}-{slug(step.name, 100)}"
                (folder / f"{name}.svg").write_text(svg, encoding="utf-8")
                entry.update(source=source, image=str((folder / f"{name}.png").relative_to(OUT)))
        self.entries.append(entry)

    @staticmethod
    def screen(context, step, registry):
        """The screen after this step, as SVG, and where it came from."""
        live = [w for w in getattr(context, "workspaces", []) if not w.task.done()]
        module = definition_module(step, registry)
        if live and module in LIVE_MODULES:
            return live[-1].read(lambda app: app.export_screenshot()), "live"
        if module in ACCESSIBLE_MODULES and hasattr(context, "output"):
            return presentation(context), "text"
        path = getattr(context, "path", None)
        if path is None or not Path(path).exists():
            # Before any case exists the participant sees the start screen, with no saved settings.
            return home(), "home"
        return fresh(Path(path)), "fresh"


def definition_module(step, registry):
    """The file of the step definition that runs this step, found the way behave finds it."""
    match = registry.find_match(step)
    return Path(match.func.__code__.co_filename).name if match is not None else None


def fresh(path):
    """The workspace as a participant would open it now, on a copy of the case so nothing is locked or changed."""
    from tests.acceptance.workspace import Workspace
    with tempfile.TemporaryDirectory() as folder:
        copy = Path(folder) / "case"
        shutil.copytree(path, copy)
        workspace = Workspace(copy, Refusing(), size=SIZE)
        try:
            return workspace.read(lambda app: app.export_screenshot())
        finally:
            workspace.close()


def home():
    """The start screen a participant sees before any case exists: no goals and no saved settings."""
    from reason_commons.adapters.settings import Settings
    from reason_commons.adapters.tui import GoalsApp
    app = GoalsApp(Path(tempfile.mkdtemp(prefix="capture-home-")) / "goals", settings=Settings.load())

    async def show():
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            return app.export_screenshot()
    return asyncio.run(show())


def presentation(context):
    """The accessible presentation's output so far, shown as a terminal would show it: the newest lines at the
    bottom, wrapped to the scenario's own width and height."""
    from textual.widgets import RichLog
    from reason_commons.adapters.tui import ThemedApp
    text = "".join(context.output)
    size = (context.width, context.height)

    class Terminal(ThemedApp):
        TITLE = "Reason Commons"

        def compose(self):
            log = RichLog(wrap=True, markup=False, max_lines=1000, auto_scroll=True)
            yield log

        def on_mount(self):
            self.query_one(RichLog).write(text)

    async def show():
        app = Terminal()
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            return app.export_screenshot()
    return asyncio.run(show())


def capturing_runner(suite, capture):
    """The suite's own runner, unchanged except that every step is followed by a capture."""
    if suite == "conversation":
        from tests.conversation.runner import ConversationRunner as base
    else:
        from tests.acceptance.runner import AcceptanceRunner as base

    class CaptureRunner(base):
        def load_hooks(self, filename=None):
            super().load_hooks(filename)
            inner = self.hooks.get("after_step")

            def after_step(context, step):
                if inner:
                    inner(context, step)
                capture(context, step, self.step_registry)
            self.hooks["after_step"] = after_step
    return CaptureRunner


def capture_feature(path, suite, manifest):
    """Run one feature file through behave, capture each executed step, then turn the pictures into PNG."""
    import render_screenshots
    from behave.__main__ import run_behave
    from behave.configuration import Configuration
    from reason_commons.adapters import themes

    os.environ["REASON_COMMONS_USAGE_LOG"] = "off"
    os.environ[themes.ENVIRONMENT] = themes.DEFAULT_THEME  # the pictures show the default, not your own theme
    os.environ["TZ"] = "UTC"  # times read the same wherever the pictures are made
    time.tzset()
    directory = Path(feature_folder(path))
    capture = Capture(directory)
    report = manifest.with_suffix(".behave.json")
    config = Configuration(command_args=[str(path), "--format", "json", "--outfile", str(report), "--no-summary"])
    # behave reports failure for undefined steps; the manifest records those instead of failing the capture.
    run_behave(config, runner_class=capturing_runner(suite, capture))
    # Every step behave saw, by its outcome: a step with no definition is undefined, and a step after one is not run.
    outcomes = {}
    for feature in json.loads(report.read_text(encoding="utf-8")):
        for scenario in feature.get("elements", []):
            for step in scenario.get("steps", []):
                status = step.get("result", {}).get("status", "not run")
                outcomes.setdefault(status, []).append(f"{step['location']} {step['keyword']} {step['name']}")

    browser = render_screenshots.chromium()
    if browser is None:
        raise SystemExit("FAIL: no Chromium found to render PNG pictures (set CHROMIUM)")
    for svg in sorted((OUT / directory).rglob("*.svg")):
        try:
            render_screenshots.to_png(browser, svg)
        finally:
            svg.with_suffix(".html").unlink(missing_ok=True)
        svg.unlink()
    manifest.write_text(json.dumps({"feature": feature_title(path), "file": str(path.relative_to(ROOT)),
                                    "suite": suite, "steps_by_outcome": {k: len(v) for k, v in outcomes.items()},
                                    "undefined_steps": outcomes.get("undefined", []),
                                    "not_run_steps": outcomes.get("not run", []), "steps": capture.entries},
                                   indent=2), encoding="utf-8")
    report.unlink()


def run_all(jobs):
    if OUT.exists():
        # Only a folder this script generated is replaced; anything else is refused rather than deleted.
        if any(OUT.iterdir()) and not (OUT / MARKER).exists():
            raise SystemExit(f"FAIL: {OUT} exists and was not made by this script; move it aside first")
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    work = Path(tempfile.mkdtemp(prefix="capture-steps-"))
    plan = [(path, "spec") for path in sorted(SPEC.glob("*.feature"))]
    plan += [(path, "conversation") for path in sorted(CONVERSATION.glob("*.feature"))]

    def child(item):
        path, suite = item
        manifest, log = work / f"{suite}-{path.stem}.json", work / f"{suite}-{path.stem}.log"
        with log.open("w") as output:
            code = subprocess.run([sys.executable, __file__, "--feature", str(path), "--suite", suite,
                                   "--manifest", str(manifest)], stdout=output, stderr=subprocess.STDOUT,
                                  cwd=ROOT).returncode
        return path, code, manifest, log

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(child, plan))
    features, broken = [], []
    for path, code, manifest, log in results:
        if code or not manifest.exists():
            broken.append((path, code, log))
        else:
            features.append(json.loads(manifest.read_text(encoding="utf-8")))
    steps = [entry for feature in features for entry in feature["steps"]]
    summary = {"features": len(features), "steps_executed": len(steps),
               "with_picture": sum(1 for e in steps if e["image"]),
               "picture_errors": [f"{e['feature']} / {e['scenario']} / {e['step']}: {e['error']}" for e in steps
                                  if "error" in e],
               "from_live_workspace": sum(1 for e in steps if e["source"] == "live"),
               "from_fresh_workspace": sum(1 for e in steps if e["source"] == "fresh"),
               "from_accessible_text": sum(1 for e in steps if e["source"] == "text"),
               "executed_without_picture": [f"{e['feature']} / {e['scenario']} / {e['step']}" for e in steps
                                            if not e["image"]],
               "undefined_steps": sum(len(feature["undefined_steps"]) for feature in features),
               "not_run_steps": sum(len(feature["not_run_steps"]) for feature in features),
               "by_status": {status: sum(1 for e in steps if e["status"] == status)
                             for status in sorted({e["status"] for e in steps})}}
    (OUT / MARKER).write_text(json.dumps({"summary": summary, "features": features}, indent=2), encoding="utf-8")
    for path, code, log in broken:
        print(f"FAIL: {path.relative_to(ROOT)} exited {code}; the end of its log:")
        print("".join(log.read_text(encoding="utf-8").splitlines(keepends=True)[-15:]))
    print(json.dumps(summary, indent=2))
    if broken:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--feature", type=Path, help="capture one feature file (the per-feature run)")
    parser.add_argument("--suite", choices=("spec", "conversation"), default="spec")
    parser.add_argument("--manifest", type=Path, help="where a per-feature run writes its manifest")
    parser.add_argument("--jobs", type=int, default=4, help="features captured at the same time")
    args = parser.parse_args()
    if args.feature:
        capture_feature(args.feature.resolve(), args.suite, args.manifest)
        return
    run_all(args.jobs)


if __name__ == "__main__":
    main()
