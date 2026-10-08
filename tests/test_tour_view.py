"""The guided tour in the terminal: its story pages, the strip that narrates the workspace, the two decisions, the
loop run on Ruth's answers, leaving and the contents, and how the start screen and run_home reach it."""

import asyncio
from importlib.resources import files

import pytest

pytest.importorskip("textual")

from reason_commons.adapters.guided import GuidedConsultant  # noqa: E402
from reason_commons.adapters.settings import Settings  # noqa: E402
from reason_commons.adapters.tour import Progress, Tour, TourClock, guided_step, load_tour  # noqa: E402
from reason_commons.adapters.tour_view import ContentsPage, StoryPage  # noqa: E402
from reason_commons.adapters.tui import (STORY_HOME, TOUR, TOUR_COMMONS, TOUR_HOME, TOUR_OWN_GOAL,  # noqa: E402
                                         TOUR_PART, ChoiceScreen, ReasonCommonsApp)
from reason_commons.bootstrap import import_case, open_case  # noqa: E402
from tests.test_tui import screen_text  # noqa: E402

ARCHIVE = "stories/harrowfield.reasoncase"
RUTH = "Ruth Okonjo"


def tour_app(tmp_path, part=None, progress=None):
    """The workspace on a fresh copy of the tour's goal, as run_tour opens it."""
    path = tmp_path / "harrowfield"
    path.parent.mkdir(parents=True, exist_ok=True)
    import_case(str(files("reason_commons.adapters").joinpath(ARCHIVE)), str(path)).close()
    script = load_tour()
    clock = TourClock(script)
    tour = Tour(script, part, progress=progress or Progress(tmp_path / "tour.yaml"), clock=clock)
    app = ReasonCommonsApp(path, RUTH, "guided", lambda consultant: open_case(path, consultant=consultant, clock=clock),
                           lambda provider, model=None: GuidedConsultant(), tour=tour, settings=Settings(data={}))
    return app, tour


async def calm(pilot, rounds=6):
    for _ in range(rounds):
        await pilot.pause()


async def done(app, pilot):
    """Until the guide has answered (or a part is ready) and the screen has caught up."""
    await app.workers.wait_for_complete()
    await calm(pilot)


def strip_text(app):
    return str(app.query_one("#tour-text").render())


def footer(app):
    return next(line for line in screen_text(app).splitlines() if "f1 Help" in line)


async def answer_with_the_example(app, pilot):
    app.query_one("#fill").press()
    await pilot.pause()
    await pilot.press("ctrl+s")
    await done(app, pilot)


def test_the_tour_opens_on_its_story_and_the_workspace_answers_as_ruth(tmp_path):
    async def run():
        app, tour = tour_app(tmp_path)
        async with app.run_test(size=(120, 40)) as pilot:
            await calm(pilot)
            assert isinstance(app.screen, StoryPage)
            text = screen_text(app)
            for wanted in ("Reason Commons · guided tour", "A winter at Harrowfield", "you'll be Ruth Okonjo", "Begin",
                           "Contents",
                           "Not now", "⏎ Open", "^q Leave tour"):
                assert wanted in text, wanted
            await pilot.press("escape")  # nothing before the first page
            assert tour.first()
            await pilot.press("enter")
            await calm(pilot)
            assert "Harrowfield General" in screen_text(app) and "You are Ruth Okonjo." in screen_text(app)
            for _ in range(2):
                await pilot.press("enter")
                await calm(pilot)
            text = screen_text(app)
            assert "Three months later" in text and "Part 1 of 9" in text
            await pilot.press("enter")
            await calm(pilot)
            text = screen_text(app)
            assert "How this works" in text and "Answer as you" in text and "(5)" in text
            await pilot.press("enter")
            await calm(pilot)
            # The workspace, as Ruth: the story's goal under her name, and the strip narrating it.
            assert not isinstance(app.screen, StoryPage)
            text = screen_text(app)
            assert "Ruth Okonjo · Tour" in text and "Answer as Ruth Okonjo" in text and "Saved" not in text
            assert "Tour · Part 1 of 9 · Where things stand" in text
            assert "Open Goal to read it whole" in strip_text(app)
            assert "f3 Next ▶" in footer(app) and "^q Leave tour" in footer(app)
            # Nothing moved on its own: the question is on screen and the answer box has the keys.
            assert app.view_name == "next" and app.focused is app.query_one("#editor")
            app.query_one("#tour-do").press()
            await calm(pilot)
            assert app.view_name == "goal" and "open History" in strip_text(app)
            await pilot.press("f3")
            await calm(pilot)
            assert "Two proposals, Graham's and Joy's" in strip_text(app)
            assert str(app.query_one("#tour-next").label) == "Continue ▶"
            await pilot.press("f3")
            await calm(pilot)
            assert isinstance(app.screen, StoryPage) and "An infirmary on the pass" in screen_text(app)
            await pilot.press("escape")
            await calm(pilot)
            assert not isinstance(app.screen, StoryPage) and "Two proposals" in strip_text(app)
    asyncio.run(run())


def test_a_waiting_decision_is_asked_for_and_the_strip_says_how_it_turned_out(tmp_path):
    async def run():
        app, tour = tour_app(tmp_path, "goal-tree")
        async with app.run_test(size=(80, 24)) as pilot:
            await calm(pilot)
            assert "Your first week · the Goal Tree" in screen_text(app)
            await pilot.press("enter")
            await calm(pilot)
            assert app.view_name == "next" and "Open the Goal Tree" in strip_text(app)
            app.query_one("#tour-do").press()  # Open it
            await calm(pilot)
            assert (app.view_name, app.shown_tree()) == ("trees", "goal")
            assert app.focused is app.query_one("#canvas") and "Read down" in strip_text(app)
            app.query_one("#tour-do").press()  # Show me
            await calm(pilot)
            chosen = next(c["statement"] for t in app.workspace_value["trees"] for c in t["claims"]
                          if c["ref"] == app.selected_claim)
            assert chosen == "No one occupies a bed they no longer need"
            assert "No one occupies a bed" in screen_text(app)  # scrolled to, not just chosen
            assert "Graham Teller has sent one more condition" in strip_text(app)
            app.query_one("#tour-do").press()  # Open Backlog
            await calm(pilot)
            assert app.view_name == "backlog" and app.focused is app.query_one("#backlog-list")
            assert app.query_one("#tour-do").has_class("hidden")
            listing = app.query_one("#backlog-list")
            listing.highlighted = next(i for i, entry in enumerate(app.backlog())
                                       if entry["summary"] == "Keep occupancy at 95% or more")
            await pilot.press("r")
            await calm(pilot)
            # The application says what goes with it; the tour adds nothing to the decision.
            assert isinstance(app.screen, ChoiceScreen) and "Reject 2 together?" in screen_text(app)
            await pilot.press("enter")
            await calm(pilot)
            assert strip_text(app).startswith("Rejected. Graham's words stay in History")
            assert tour.step["kind"] == "beat" and app.focused is not None
            await pilot.press("f3")
            await calm(pilot)
            text = screen_text(app)
            assert isinstance(app.screen, StoryPage) and "At the pass" in text and "Must" in text
            assert "Next: Why are we not there yet?" in text and "Part 3 of 9" in text
    asyncio.run(run())


def test_joys_correction_enters_with_its_link_and_the_keys_stay_on_the_page(tmp_path):
    async def run():
        app, tour = tour_app(tmp_path, "current-reality")
        async with app.run_test(size=(80, 24)) as pilot:
            await calm(pilot)
            await pilot.press("enter")
            await calm(pilot)
            # Graham's condition was rejected in Part 2: here, Joy's correction is all that waits.
            occupancy = next(e["ref"] for e in app.backlog() if e["summary"] == "Keep occupancy at 95% or more")
            app.perform("reject", [occupancy], confirmed=True)
            await calm(pilot)
            await pilot.press("f3")
            await calm(pilot)
            assert "You've missed pharmacy" in strip_text(app)
            app.query_one("#tour-do").press()  # Open Backlog
            await calm(pilot)
            listing = app.query_one("#backlog-list")
            listing.highlighted = next(i for i, entry in enumerate(app.backlog()) if entry["entry"] == "proposal"
                                       and entry["kind"] == "link")
            await pilot.press("a")
            await calm(pilot)
            assert isinstance(app.screen, ChoiceScreen) and "Accept 2 together?" in screen_text(app)
            await pilot.press("enter")
            await calm(pilot)
            assert not app.backlog() and strip_text(app).startswith("Accepted, in Joy's words")
            # The emptied list went away; the keyboard did not go with it.
            assert app.focused is app.query_one("#main")
            assert "Nothing waits" in screen_text(app)
    asyncio.run(run())


def test_the_loop_runs_on_ruths_answers_dated_monday(tmp_path):
    async def run():
        app, tour = tour_app(tmp_path, "monday")
        loop = tour.part["loop"]
        async with app.run_test(size=(120, 40)) as pilot:
            await calm(pilot)
            await pilot.press("enter")
            await calm(pilot)
            assert strip_text(app) == " ".join(loop["test_change"].split())
            asked = []
            while not tour.met():
                if app.reply_waiting():
                    assert strip_text(app) == " ".join(loop["waiting"].split())
                    app.query_one("#accept-all").press()
                    await done(app, pilot)
                    continue
                step = guided_step(app.workspace_value["question"])
                asked.append(step)
                app.query_one("#fill").press()
                await pilot.pause()
                assert app.query_one("#editor").text == " ".join(tour.script["examples"][step].split())
                await pilot.press("ctrl+s")
                await done(app, pilot)
            assert asked == ["test_change", "test_forecast", "test_review", "test_stop", "action"]
            assert strip_text(app) == " ".join(loop["done"].split())
            assert "✓ Action" in screen_text(app)
            last = app.case.history()["revisions"][-1]
            assert last["timestamp"].startswith("2026-01-12")  # the story's Monday
    asyncio.run(run())


def test_day_three_gets_monday_ready_then_sets_the_forecast_beside_the_result(tmp_path):
    progress = Progress(tmp_path / "tour.yaml")

    async def run():
        app, tour = tour_app(tmp_path, "day-three", progress)
        async with app.run_test(size=(120, 40)) as pilot:
            await calm(pilot)
            assert isinstance(app.screen, StoryPage) and "Pharmacy is slow" in screen_text(app)
            # Monday's answers go in while the page is read; the workspace waits for them.
            assert app._preparing
            await pilot.press("enter")
            await calm(pilot, 2)
            assert isinstance(app.screen, StoryPage)
            await done(app, pilot)
            assert not app._preparing and guided_step(app.workspace_value["question"]) == "observe"
            monday = [r for r in app.case.history()["revisions"] if r["timestamp"].startswith("2026-01-12")]
            assert len(monday) >= 5
            await pilot.press("enter")
            await calm(pilot)
            await answer_with_the_example(app, pilot)
            app.query_one("#accept-all").press()
            await done(app, pilot)
            assert guided_step(app.workspace_value["question"]) == "review"
            text = screen_text(app)
            # The original forecast, word for word, beside what was reported.
            assert "ORIGINAL FORECAST" in text and "8 in 10" in text and "4 of 11" in text
            await answer_with_the_example(app, pilot)
            app.query_one("#accept-all").press()
            await done(app, pilot)
            assert tour.met() and strip_text(app).startswith("Recorded")
            assert app.case.history()["revisions"][-1]["timestamp"].startswith("2026-01-15")
            await pilot.press("f3")
            await calm(pilot)
            app.query_one("#tour-do").press()  # Open Tests
            await calm(pilot)
            assert app.view_name == "tests" and "ORIGINAL FORECAST" in screen_text(app)
            await pilot.press("f3")
            await calm(pilot)
            assert "The Herbalist" in screen_text(app)
            for _ in range(2):
                await pilot.press("enter")
                await calm(pilot)
            text = screen_text(app)
            assert "Down the Mountain" in text and "Start my own goal" in text and "Explore a real commons" in text
            await pilot.press("enter")  # Start my own goal
            await calm(pilot)
        return app.return_value
    assert asyncio.run(run()) == TOUR_OWN_GOAL
    assert progress.reached("harrowfield") == ("epilogue", True)


def test_leaving_goes_to_the_start_screen_and_the_contents_start_a_part(tmp_path):
    progress = Progress(tmp_path / "tour.yaml")

    async def leave(keys):
        app, tour = tour_app(tmp_path / str(len(keys)), progress=progress)
        async with app.run_test(size=(80, 24)) as pilot:
            await calm(pilot)
            for key in keys:
                await pilot.press(key)
                await calm(pilot)
        return app.return_value

    # From a page, and from the workspace: Ctrl+Q leaves the tour; it never quits the program.
    assert asyncio.run(leave(["ctrl+q"])) == TOUR_HOME
    assert asyncio.run(leave(["enter"] * 5 + ["ctrl+q"])) == TOUR_HOME
    assert progress.reached("harrowfield") == ("workspace", False)

    async def contents():
        app, tour = tour_app(tmp_path / "contents", progress=progress)
        async with app.run_test(size=(80, 24)) as pilot:
            await calm(pilot)
            app.screen.choose("contents")
            await calm(pilot)
            assert isinstance(app.screen, ContentsPage)
            text = screen_text(app)
            assert "From the beginning" in text and "you are here" in text
            assert "8  Your first loop" in text and "9  Day three" in text
            # Nothing has changed yet and Monday needs nothing before it: it simply opens.
            app.screen.choose("part:monday")
            await calm(pilot)
            assert isinstance(app.screen, StoryPage) and tour.part["id"] == "monday"
            assert progress.reached("harrowfield") == ("monday", False)
            # Thursday needs Monday's loop: the tour starts it on a fresh copy.
            app.screen.choose("contents")
            await calm(pilot)
            app.screen.choose("part:day-three")
            await calm(pilot)
        return app.return_value
    assert asyncio.run(contents()) == (TOUR_PART, "day-three")


def test_the_tour_keeps_its_guide_and_its_trees(tmp_path):
    async def run():
        app, tour = tour_app(tmp_path, "workspace")
        async with app.run_test(size=(120, 40)) as pilot:
            await calm(pilot)
            names = [name for _, name, _, _ in app.action_list()]
        return names
    names = asyncio.run(run())
    assert not [name for name in names if name.startswith("Consultant:")]
    assert "Import trees" not in names and "Save and quit" not in names
    assert {"Tour: next", "Tour: contents", "Leave the tour", "How this works"} <= set(names)


def test_every_story_page_fits_an_80_by_24_screen(tmp_path):
    async def run():
        app, tour = tour_app(tmp_path)
        seen = 0
        async with app.run_test(size=(80, 24)) as pilot:
            await calm(pilot)
            for index, part in enumerate(tour.parts):
                for at, step in enumerate(tour.steps(index)):
                    if step["kind"] not in ("page", "closing"):
                        continue
                    tour.index, tour.at = index, at
                    app.screen.show()
                    await calm(pilot, 3)
                    body = app.screen.query_one("#page-body")
                    assert body.max_scroll_y == 0, (part["id"], at)
                    seen += 1
        return seen
    assert asyncio.run(run()) > 20


def test_run_tour_opens_a_fresh_copy_and_starts_a_chosen_part_on_another(tmp_path, monkeypatch):
    from reason_commons.adapters import tui
    progress = Progress(tmp_path / "tour.yaml")
    outcomes, seen = iter([(TOUR_PART, "cloud"), TOUR_HOME]), []

    def fake_run(store, **options):
        seen.append({"store": store, "exists": store.exists(), "part": options["tour"].part["id"], **options})
        return next(outcomes)
    monkeypatch.setattr(tui, "run", fake_run)
    assert tui.run_tour(progress=progress) == TOUR_HOME
    assert [entry["part"] for entry in seen] == ["prologue", "cloud"]
    assert all(entry["exists"] and not entry["store"].exists() for entry in seen)  # thrown away after
    assert seen[0]["speaker"] == RUTH and seen[0]["provider"] == "guided" and seen[0]["clock"] is not None
    assert seen[0]["store"] != seen[1]["store"]

    # It resumes where the person left, and starts again once it was finished.
    seen.clear()
    progress.save("harrowfield", "transition")
    outcomes = iter([TOUR_HOME])
    tui.run_tour(progress=progress)
    progress.save("harrowfield", "epilogue", finished=True)
    outcomes = iter([TOUR_HOME])
    tui.run_tour(progress=progress)
    assert [entry["part"] for entry in seen] == ["transition", "prologue"]


def test_run_home_goes_where_the_tour_leaves_to(tmp_path, monkeypatch):
    from reason_commons.adapters import tui
    shown, left, calls = iter([TOUR, TOUR, TOUR, None]), iter([TOUR_HOME, TOUR_COMMONS, TOUR_OWN_GOAL]), []
    monkeypatch.setattr(tui.GoalsApp, "run", lambda self: (calls.append(("home", self.start_new)), next(shown))[1])
    monkeypatch.setattr(tui, "run_tour", lambda: (calls.append("tour"), next(left))[1])
    monkeypatch.setattr(tui, "run_story", lambda: (calls.append("commons"), STORY_HOME)[1])
    monkeypatch.setenv("REASON_COMMONS_HOME", str(tmp_path / "goals"))
    tui.run_home(settings=Settings.load(tmp_path / "settings.yaml"))
    assert calls == [("home", False), "tour", ("home", False), "tour", "commons", ("home", False), "tour",
                     ("home", True)]
