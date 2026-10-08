"""Render the README and docs screenshots from the real workspace.

Runs the Textual app headlessly with the built-in guide and fixed dates, so the
pictures show exactly what a user sees. Writes SVG files to docs/images/ and, when
Chromium (CHROMIUM, or the usual install paths) and Pillow are available, PNG
copies that render the same everywhere; the README uses the PNGs. Run it after changing what the workspace shows:

    python3 scripts/render_screenshots.py
"""

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reason_commons.adapters import themes, timeline  # noqa: E402
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


async def shoot(app, name, size, before=None, steps=None):
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        if before:
            before(app)
            await pilot.pause()
        if steps:
            await steps(app, pilot)
            await pilot.pause(0.3)
        app.save_screenshot(filename=f"{name}.svg", path=str(OUT))
        if getattr(app, "_save_timer", None):
            app._save_timer.stop()  # a pending draft save must not fire while the app shuts down


async def render(folder):
    goals = folder / "ReasonCommons"
    goals.mkdir()
    build_sample(goals / "first-practice", answers=ANSWERS[:8], view="next", name=GOAL,
                 clock=FixedClock("2026-11-06T19:30:00+00:00"))
    create_case(goals / "map-review", "Agree how our strategy map gets reviewed",
                clock=FixedClock("2026-10-02T07:00:00+00:00")).close()
    from reason_commons.adapters.settings import Settings
    settings = Settings.load(folder / "settings.yaml")
    settings.set(SPEAKER, "name")
    settings.set("guided", "consultant")
    settings.save()
    await shoot(GoalsApp(goals, settings=settings), "home", (100, 22))
    await first_start(folder)
    create_case(folder / "new", "my-first-goal").close()
    await shoot(workspace(folder / "new"), "welcome", (120, 36))
    await shoot(workspace(goals / "first-practice"), "in-progress", (120, 36))
    for name, count in (("tutorial-measure", 1), ("tutorial-forecast", 4), ("tutorial-review", 9)):
        step = build_sample(folder / name, answers=ANSWERS[:count], view="next", name=GOAL,
                            clock=FixedClock("2026-10-14T20:00:00+00:00"))
        await shoot(workspace(step), name, (120, 36))
        if name == "tutorial-review":  # the smallest supported terminal, where the comparison stacks
            await shoot(workspace(step), "review-80x24", (80, 24))
    finished = build_sample(folder / "finished", name=GOAL, clock=FixedClock("2026-11-09T09:00:00+00:00"))
    await shoot(workspace(finished), "forecast-vs-result", (120, 36))
    await shoot(workspace(finished), "trees-view", (120, 36), before=lambda app: app.show_view("trees"))
    await real_commons(folder)
    await shoot(workspace(finished), "trees-current-reality", (120, 56),
                before=lambda app: app.show_tree("current_reality"))

    def reality(app):
        app.tree_choice = "current_reality"

    async def choose(app, pilot, *more):
        for key in ("ctrl+t", "down", "down", *more):
            await pilot.press(key)
            await pilot.pause()
    await shoot(workspace(finished), "trees-statement", (120, 40), before=reality, steps=choose)
    await shoot(workspace(finished), "trees-statement-80x24", (80, 24), before=reality,
                steps=lambda app, pilot: choose(app, pilot, "enter"))
    await heard(folder)
    await backlog(folder)
    await more_workspace(folder, goals, finished)
    await cost(folder)
    await more_home(folder, goals)


class Recorder:
    """Stands in for Claude in one picture: its reply proposes a symptom, a cause and the link between them for
    the Current Reality Tree, from the answer's own words, and asks the next question. The built-in guide
    never proposes tree statements, so without it the picture could not be taken offline."""
    version = "screenshot/recorder"

    def propose(self, request):
        source = [request["input"]["request_id"]]

        def claim(alias, role, statement):
            return {"operation": "record_claim", "temporary_id": alias, "source_refs": source,
                    "data": {"tree": "current_reality", "role": role, "statement": statement,
                             "basis": "participant_report"}}
        return {"schema_version": "1", "delivery_profile": "p2", "request_id": source[0],
                "base_revision": request["input"]["base_revision"],
                "intervention": {"kind": "question", "purpose": "choose_test", "decision": "Choose a test",
                                 "primary_prompt": "What one small change could you try at the next open evening, "
                                                   "and what do you expect it to do?",
                                 "rationale": "A small change with a forecast tests the cause you named."},
                "proposed_updates": [
                    claim("ude", "undesirable_effect", "Newcomers do not come back after their first open evening"),
                    claim("cause", "root_cause", "We never offer a next step at the end of an open evening"),
                    {"operation": "record_link", "temporary_id": "because", "source_refs": source,
                     "data": {"tree": "current_reality", "relation": "causes", "from_ref": "cause", "to_ref": "ude",
                              "assumption": "Without an invitation, newcomers do not know a first practice exists"}}]}


class Drafter:
    """Stands in for Claude in the Backlog picture: each reply proposes what the next item of ``replies`` holds."""
    version = "screenshot/drafter"

    def __init__(self, replies):
        self.replies = list(replies)

    def propose(self, request):
        source = [request["input"]["request_id"]]
        updates = [dict(update, source_refs=source) for update in self.replies.pop(0)]
        return {"schema_version": "1", "delivery_profile": "p2", "request_id": source[0],
                "base_revision": request["input"]["base_revision"],
                "intervention": {"kind": "question", "purpose": "choose_test", "decision": "Choose a test",
                                 "primary_prompt": "What one small change could you try at the next open evening, "
                                                   "and what do you expect it to do?",
                                 "rationale": "A small change with a forecast tests the cause you named."},
                "proposed_updates": updates}


class PaidRecorder(Recorder):
    """The Recorder as Claude Haiku 5.5, telling the usage log what a typical reply costs, offline."""
    model = "claude-haiku-5-5"

    def __init__(self, usage):
        self.usage = usage

    def propose(self, request):
        self.usage({"provider": "anthropic", "model": self.model, "outcome": "proposal",
                    "case_id": request["case"]["case_id"], "request_id": request["input"]["request_id"],
                    "tokens": {"input": 17_000, "output": 5_000}})
        return super().propose(request)


async def cost(folder):
    """What Claude's replies cost: the footer and a reply's notice, then Consultant calls and cost. A usage log
    of its own (under a stand-in home folder, so the path reads as it would for you), a fixed clock and a $5
    budget; nothing is sent anywhere."""
    from reason_commons.adapters.usage import UsageLog, UsageSession
    home, saved = folder / "home", {name: os.environ.get(name) for name in ("HOME", "REASON_COMMONS_USAGE_LOG",
                                                                           "REASON_COMMONS_MONTHLY_BUDGET_USD",
                                                                           "REASON_COMMONS_ANTHROPIC_MODEL")}
    log = home / ".local/state/reason-commons/usage.jsonl"
    os.environ.update(HOME=str(home), REASON_COMMONS_USAGE_LOG=str(log), REASON_COMMONS_MONTHLY_BUDGET_USD="5")
    os.environ.pop("REASON_COMMONS_ANTHROPIC_MODEL", None)
    try:
        now = lambda: datetime(2026, 11, 9, 9, 0, tzinfo=timezone.utc)
        earlier = UsageSession(UsageLog(log, lambda: datetime(2026, 11, 4, 18, 0, tzinfo=timezone.utc)), "cli")
        for _ in range(38):
            earlier.record({"model": "claude-haiku-5-5", "outcome": "proposal", "tokens": {"input": 17_000,
                                                                                           "output": 5_000}})
        for _ in range(3):
            earlier.record({"model": "claude-sonnet-5-5", "outcome": "proposal", "tokens": {"input": 17_000,
                                                                                            "output": 1_600}})
        def app(name):
            path = folder / name
            build_sample(path, answers=ANSWERS[:3], view="next", name=GOAL,
                         clock=FixedClock("2026-11-09T08:00:00+00:00"))
            usage = UsageSession(UsageLog(log, now), "workspace")
            paid = PaidRecorder(usage.record)
            return ReasonCommonsApp(path, SPEAKER, "anthropic", lambda consultant: open_case(path, consultant=consultant),
                                    lambda provider, model=None: paid, usage=usage)

        async def answer(app, pilot):
            app.query_one("#editor").text = ("People come to one open evening and we never see them again. Nobody "
                                             "tells them what to do next: we never offer a next step.")
            app.action_send()
            await app.workers.wait_for_complete()
            await pilot.pause(0.3)

        async def answer_then_cost(app, pilot):
            await answer(app, pilot)
            app.action_consultant_calls()
            await pilot.pause(0.3)
        await shoot(app("paid"), "footer-meter", (120, 36), steps=answer)
        await shoot(app("paid-cost"), "usage-and-cost", (120, 40), steps=answer_then_cost)
    finally:
        for name, value in saved.items():
            os.environ.pop(name, None)
            if value is not None:
                os.environ[name] = value


async def backlog(folder):
    """The Backlog: a new version of the goal to decide first, a cause and the link that waits for it, an
    action, and the chosen entry in full beside the list."""
    path = folder / "backlog"
    build_sample(path, answers=ANSWERS[:3], view="next", name=GOAL, clock=FixedClock("2026-10-14T20:00:00+00:00"))
    with open_case(path) as case:
        goal = next(g for g in case.workspace(view="goal")["goals"])

    def claim(alias, tree, role, statement):
        return {"operation": "record_claim", "temporary_id": alias,
                "data": {"tree": tree, "role": role, "statement": statement, "basis": "participant_report"}}
    drafter = Drafter([
        [claim("ude", "current_reality", "undesirable_effect", "Newcomers do not come back after their first open evening"),
         claim("cause", "current_reality", "root_cause", "We never offer a next step at the end of an open evening"),
         {"operation": "record_link", "temporary_id": "because",
          "data": {"tree": "current_reality", "relation": "causes", "from_ref": "cause", "to_ref": "ude",
                   "assumption": "Without an invitation, newcomers do not know a first practice exists"}}],
        [claim("act", "transition", "transition_action", "End each open evening with one clear invitation")],
        [{"operation": "record_goal", "temporary_id": "goal",
          "data": {"statement": "Newcomers at our open evenings find a clear, no-pressure next step, and most "
                                "come back for a second practice", "replaces": goal["ref"],
                   "measure": goal["data"].get("measure"), "protections": goal["data"].get("protections") or []}}]])
    with open_case(path, consultant=drafter, clock=FixedClock("2026-10-15T19:00:00+00:00")) as case:
        for words in ("People come once and we never see them again: we never offer a next step.",
                      "I could end each evening with one clear invitation.",
                      "Really, the goal is that they come back for a second practice."):
            target = case.workspace()["target"]
            assert case.submit(words, SPEAKER, target["base_revision"], target["response_target"])["status"] == "saved"
    app = ReasonCommonsApp(path, SPEAKER, "anthropic", lambda consultant: open_case(path, consultant=drafter),
                           lambda provider: drafter)

    async def open_backlog(app, pilot):
        app.show_view("backlog")
        await pilot.pause()
        app.query_one("#backlog-list").focus()
        await pilot.pause(0.3)
    await shoot(app, "backlog", (130, 36), steps=open_backlog)


async def heard(folder):
    """Under the next question: what a reply proposes, beside the words it came from."""
    path = folder / "heard"
    build_sample(path, answers=ANSWERS[:3], view="next", name=GOAL, clock=FixedClock("2026-10-14T20:00:00+00:00"))
    app = ReasonCommonsApp(path, SPEAKER, "anthropic", lambda consultant: open_case(path, consultant=Recorder()),
                           lambda provider: Recorder())

    async def answer(app, pilot):
        app.query_one("#editor").text = ("People come to one open evening and we never see them again. Nobody tells "
                                         "them what to do next: we never offer a next step.")
        app.action_send()
        await app.workers.wait_for_complete()
        await pilot.pause(0.3)
    await shoot(app, "trees-heard", (120, 36), steps=answer)


async def more_workspace(folder, goals, finished):
    """Every other view, the trees not shown above, the dialogs, the palette and the narrow layout."""
    for view, name in (("goal", "view-goal"), ("actions", "view-actions"), ("reasoning", "view-reasoning"),
                       ("sources", "view-sources"), ("history", "view-history")):
        await shoot(workspace(finished), name, (120, 36), before=lambda app, view=view: app.show_view(view))
    for tree, name, height in (("goal", "tree-goal", 36), ("conflict", "tree-evaporating-cloud", 44),
                               ("future_reality", "tree-future-reality", 56), ("prerequisite", "tree-prerequisite", 44),
                               ("all", "tree-all-six", 60)):
        await shoot(workspace(finished), name, (120, height), before=lambda app, tree=tree: app.show_tree(tree))
    # Looking back: an ordinary goal at an earlier step, read-only.
    def step_back(app):
        app.go_to(8)
        app.show_view("next")  # the example opens on Tests; a step reads best on its own page
    await shoot(workspace(finished), "history-moment", (120, 36), before=step_back)
    create_case(folder / "bare", "Agree how our strategy map gets reviewed").close()
    await shoot(workspace(folder / "bare"), "trees-empty", (120, 30), before=lambda app: app.show_view("trees"))
    await shoot(workspace(finished), "explain-this", (120, 36), steps=press("explain"))
    await shoot(workspace(goals / "first-practice"), "explain-question", (120, 36), steps=press("explain"))
    await shoot(workspace(goals / "first-practice"), "other-moves", (120, 36), steps=press("moves"))
    await shoot(workspace(goals / "first-practice"), "views-menu", (80, 30), steps=press("views-button"))
    await shoot(workspace(goals / "first-practice"), "workspace-narrow", (80, 30))
    await shoot(workspace(goals / "first-practice"), "help", (120, 36), steps=keys("f1"))
    await shoot(workspace(finished), "actions-palette", (120, 36), steps=keys("ctrl+p"))
    await shoot(workspace(finished), "actions-palette-search", (120, 36), steps=keys("ctrl+p", text="trees"))
    await shoot(workspace(finished), "export-case", (120, 36), steps=call("action_export"))
    await shoot(workspace(finished), "export-trees", (120, 36), steps=call("action_export_trees"))
    await shoot(workspace(finished), "import-trees", (120, 36), steps=call("action_import_trees"))

    async def draft(app, pilot):
        app.query_one("#editor").text = "Newcomers book a first practice before they leave the open evening."
        await pilot.pause()
    await shoot(workspace(goals / "first-practice"), "answer-draft", (120, 36), steps=draft)

    class Offline:
        """Claude Haiku 5.5 out of reach: Retry, and Retry with Sonnet beside it."""
        model, version = "claude-haiku-5-5", "screenshot/offline"

        def propose(self, request):
            raise ConnectionError("offline")
    offline = folder / "offline"
    build_sample(offline, answers=ANSWERS[:2], view="next", name=GOAL, clock=FixedClock("2026-10-14T20:00:00+00:00"))
    app = ReasonCommonsApp(offline, SPEAKER, "anthropic", lambda consultant: open_case(offline, consultant=Offline()),
                           lambda provider, model=None: Offline())

    async def fail(app, pilot):
        app.query_one("#editor").text = "Mira's group, six of us, runs the sign-up sheet."
        app.action_send()
        await pilot.pause(0.5)
    await shoot(app, "consultant-unavailable", (120, 36), steps=fail)


def press(button):
    async def steps(app, pilot):
        app.query_one(f"#{button}").press()
        await pilot.pause(0.3)
    return steps


def keys(*names, text=None):
    async def steps(app, pilot):
        await pilot.press(*names)
        await pilot.pause(0.3)
        if text:
            await pilot.press(*text)
            await pilot.pause(0.3)
    return steps


def call(method):
    async def steps(app, pilot):
        getattr(app, method)()
        await pilot.pause(0.3)
    return steps


async def more_home(folder, goals):
    """The goals list's dialogs and its help."""
    from reason_commons.adapters.settings import Settings
    settings = Settings.load(folder / "settings.yaml")

    settings.set(5, "usage", "monthly_budget_usd")  # the Budget row with a budget set

    def home():
        app = GoalsApp(goals, settings=settings)
        app.month_spent = lambda: Decimal("0.32")  # the pictures read no usage log
        return app

    async def new_goal(app, pilot):
        goals = app.query_one("#goals")
        goals.highlighted = goals.get_option_index("new")
        await pilot.press("enter")
        await pilot.pause(0.3)
        app.screen.query_one("Input").value = "A clear next step after open evenings"
        await pilot.pause(0.2)
    await shoot(home(), "new-goal", (100, 22), steps=new_goal)
    await shoot(home(), "home-help", (100, 30), steps=keys("f1"))
    await shoot(home(), "home-settings", (100, 26), steps=keys("f2"))


async def real_commons(folder):
    """The packaged Second Renaissance story: now, one step back in time, and its Transition Tree."""
    from importlib.resources import files
    from reason_commons.adapters.story import load_story
    from reason_commons.adapters.tui import STORY_ARCHIVE
    from reason_commons.bootstrap import import_case
    path = folder / "real-commons"
    import_case(str(files("reason_commons.adapters").joinpath(STORY_ARCHIVE)), str(path)).close()

    def story():
        return ReasonCommonsApp(path, SPEAKER, "guided", lambda consultant: open_case(path, consultant=consultant),
                                lambda provider: configured_consultant(provider=provider), story=load_story())
    await shoot(story(), "story-now", (120, 36))
    await shoot(story(), "story-moment", (120, 36), before=lambda app: app.go_to(6))
    await shoot(story(), "tutorial-trees", (120, 36), before=lambda app: app.show_tree("transition"))


async def first_start(folder):
    """The first-start choices, two setup steps and the tour's coaching."""
    from reason_commons.adapters.settings import Settings
    models = [("claude-opus-5-5", "Claude Opus 5.5"), ("claude-sonnet-5-5", "Claude Sonnet 5.5"),
              ("claude-haiku-5-5", "Claude Haiku 5.5"), ("claude-haiku-4-5-20251001", "Claude Haiku 4.5")]
    os.environ["USER"] = "mira"

    def fresh():
        return GoalsApp(folder / "empty", settings=Settings.load(folder / "no-settings.yaml"),
                        checks={"anthropic": lambda key: (models, None)})

    async def answer(app, pilot, value=None, key=None):
        await pilot.pause()
        if key is None:
            app.screen.query_one("Input").value = value
        else:
            choices = (app.screen.query("#choices") or app.screen.query("#goals")).first()
            choices.highlighted = [option.id for option in choices.options].index(key)
        await pilot.press("enter")
        await pilot.pause(0.2)

    async def to_consultant(app, pilot):
        await answer(app, pilot, key="setup")
        await answer(app, pilot, "Mira")

    async def to_model(app, pilot):
        await to_consultant(app, pilot)
        await answer(app, pilot, key="anthropic")
        await answer(app, pilot, "sk-ant-example")
        await pilot.pause(0.3)

    await shoot(fresh(), "first-start", (100, 30))
    await shoot(fresh(), "setup-consultant", (100, 30), steps=to_consultant)
    await shoot(fresh(), "setup-model", (100, 30), steps=to_model)
    create_case(folder / "tour", "Practice: your first loop").close()
    tour = ReasonCommonsApp(folder / "tour", SPEAKER, "guided",
                            lambda consultant: open_case(folder / "tour", consultant=consultant),
                            lambda provider: configured_consultant(provider=provider), tour=True)

    async def fill(app, pilot):
        app.query_one("#fill").press()
    await shoot(tour, "tour", (120, 36), steps=fill)


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
    # The pictures never read or write the real usage log.
    os.environ["REASON_COMMONS_USAGE_LOG"] = "off"
    os.environ[themes.ENVIRONMENT] = themes.DEFAULT_THEME  # the docs show the default, not your own theme
    # Times are shown on the person's own clock and a date omits the year when it is this year, so the pictures
    # fix both: UTC, and a day shortly after the dates the pictures use.
    os.environ["TZ"] = "UTC"
    time.tzset()
    timeline.today = lambda: date(2026, 11, 10)
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
