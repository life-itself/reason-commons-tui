"""The home screen: ways to start, then your goals as a table; settings live behind F2 and the footer."""

import asyncio
from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("textual")

from reason_commons.adapters import themes, timeline  # noqa: E402
from reason_commons.adapters.settings import Settings, summary  # noqa: E402
from reason_commons.adapters.tui import GoalsApp  # noqa: E402
from tests.support import timezone  # noqa: E402
from tests.test_tui import screen_text, settled  # noqa: E402

GOALS = [
    {"path": Path("a"), "name": "kol", "changed": "2026-10-05T10:00:00+00:00", "step": "Start"},
    {"path": Path("b"), "name": "become the person i want to become", "changed": "2026-10-03T18:02:05+00:00",
     "step": "Clarify the goal"},
    {"path": Path("c"), "name": "my-first-goal", "changed": "2026-10-03T09:00:00+00:00", "step": "Start"},
]


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    """Dates are shown on the person's clock, without this year's year: pin both. The theme is the default one."""
    monkeypatch.setenv(themes.ENVIRONMENT, "")  # set first, so teardown puts back what a theme change wrote
    monkeypatch.delenv(themes.ENVIRONMENT)
    monkeypatch.setattr(timeline, "today", lambda: date(2026, 10, 5))
    with timezone("UTC"):
        yield


def home(tmp_path, goals=GOALS, name="David"):
    settings = Settings(tmp_path / "settings.yaml", {"name": name, "consultant": "guided"}, exists=True)
    return GoalsApp(tmp_path / "goals", list_goals=lambda root: list(goals), settings=settings)


def test_the_list_has_a_start_section_and_a_table_of_goals(tmp_path):
    async def run():
        app = home(tmp_path)
        async with app.run_test(size=(120, 30)) as pilot:
            await pilot.pause()
            options = app.query_one("#goals").options
            # Headings are not choices: the cursor skips them, so the first choice is the first goal.
            assert [option.id for option in options if not option.disabled] == ["commons", "new", "0", "1", "2"]
            assert app.query_one("#goals").highlighted_option.id == "0"
            text = screen_text(app)
            for wanted in ("START", "+ New goal", "Continue Reason Commons", "YOUR GOALS", "STAGE", "UPDATED"):
                assert wanted in text, wanted
            # Settings and Theme are not rows any more, and the old "·"-separated, ISO-dated rows are gone.
            assert "Settings:" not in text and "Theme:" not in text and "2026-10-05" not in text
            assert "No goal yet" not in text
    asyncio.run(run())


def test_goal_rows_are_aligned_columns_of_name_stage_and_day(tmp_path):
    async def run():
        app = home(tmp_path)
        async with app.run_test(size=(120, 30)) as pilot:
            await pilot.pause()
            lines = screen_text(app).splitlines()
            find = lambda needle: next(line for line in lines if needle in line)
            head, kol, long, first = find("YOUR GOALS"), find("kol"), find("become the person"), find("my-first-goal")
            # Each column starts in the same place in every row, so the eye can run down it.
            stage = head.index("STAGE")
            assert kol.index("Start") == stage and long.index("Clarify the goal") == stage
            assert first.index("Start") == stage
            updated = head.index("UPDATED")
            assert kol.index("Oct 5") == updated and long.index("Oct 3") == updated and first.index("Oct 3") == updated
    asyncio.run(run())


def test_the_arrow_marks_only_the_highlighted_row_and_follows_the_cursor(tmp_path):
    async def run():
        app = home(tmp_path)
        async with app.run_test(size=(120, 30)) as pilot:
            await pilot.pause()
            goals = app.query_one("#goals")
            marked = lambda: [str(o.prompt) for o in goals.options if str(o.prompt).startswith("▸")]
            assert len(marked()) == 1 and "kol" in marked()[0]
            await pilot.press("down")
            await pilot.pause()
            assert len(marked()) == 1 and "become the person" in marked()[0]
            goals.highlighted = goals.get_option_index("new")
            await pilot.pause()
            assert len(marked()) == 1 and "New goal" in marked()[0]
    asyncio.run(run())


def test_the_footer_says_what_enter_does_and_what_is_set_now(tmp_path):
    async def run():
        app = home(tmp_path)
        async with app.run_test(size=(120, 30)) as pilot:
            await pilot.pause()
            footer = screen_text(app).splitlines()
            footer = next(line for line in footer if "f2 Settings" in line)
            assert "Open" in footer and "f1 Help" in footer and "^q Quit" in footer
            assert "David · offline guide · Chromatics, dark" in footer
            goals = app.query_one("#goals")
            goals.highlighted = goals.get_option_index("commons")
            await pilot.pause()
            assert "Choose" in next(line for line in screen_text(app).splitlines() if "f2 Settings" in line)
    asyncio.run(run())


def test_a_narrow_screen_drops_the_stage_column_and_marks_a_cut_name(tmp_path):
    async def run():
        app = home(tmp_path)
        async with app.run_test(size=(40, 24)) as pilot:  # the smallest the specification supports
            await pilot.pause()
            text = screen_text(app)
            assert "STAGE" not in text and "UPDATED" in text
            row = next(line for line in text.splitlines() if "become the person" in line)
            assert "…" in row and "Oct 3" in row
            await pilot.resize_terminal(120, 30)
            await pilot.pause()
            assert "STAGE" in screen_text(app)  # the columns come back with the room
    asyncio.run(run())


def test_with_no_goals_the_list_is_only_the_ways_to_start(tmp_path):
    async def run():
        app = home(tmp_path, goals=[])
        async with app.run_test(size=(120, 30)) as pilot:
            await pilot.pause()
            text = screen_text(app)
            assert "You have no goals yet" in text and "YOUR GOALS" not in text
            assert app.query_one("#goals").highlighted_option.id == "commons"
    asyncio.run(run())


def test_the_settings_summary_names_who_you_are_and_who_asks():
    assert summary(Settings(Path("x"), {"name": "David", "consultant": "guided"})) == "David · offline guide"
    assert summary(Settings(Path("x"), {"name": "Dana", "consultant": "anthropic"})) == "Dana · Claude"
    assert summary(Settings(Path("x"), {"consultant": "lm-studio"})) == "local model"
    assert summary(Settings(Path("x"), {})) == "offline guide"


def test_goal_names_with_brackets_and_backslashes_show_as_written(tmp_path):
    names = ["a [ b", "[Draft] Q3 plan", "[WIP]", "x [$accent] y", "k\\", "Dad's [birthday", "C:\\temp\\[x]"]
    goals = [{"path": Path(str(n)), "name": name, "changed": "2026-10-03T09:00:00+00:00", "step": "Start"}
             for n, name in enumerate(names)]

    async def run():
        app = home(tmp_path, goals=goals)
        async with app.run_test(size=(120, 30)) as pilot:
            await pilot.pause()
            return screen_text(app)
    text = asyncio.run(run())
    for name in names:
        assert name in text, name
    assert "$text-muted" not in text  # no markup leaked into the Stage column


def test_the_summary_shortens_before_it_is_cut_and_never_pushes_a_hint_off(tmp_path):
    async def run(width):
        app = home(tmp_path)
        async with app.run_test(size=(width, 24)) as pilot:
            await pilot.pause()
            await settled(app, pilot, "#hint-0", "#hint-1", "#hint-2", "#summary")
            footer = next(line for line in screen_text(app).splitlines() if "f2 Settings" in line)
            hints = [h for h in app.query("Hint") if not h.has_class("hidden")]
            assert all(h.region.right <= width for h in hints)
            return footer
    assert "David · offline guide · Chromatics, dark" in asyncio.run(run(120))
    eighty = asyncio.run(run(80))
    assert "David · offline guide · Chromatics" in eighty and "dark" not in eighty  # the mode went first
    forty = asyncio.run(run(40))
    assert "f2 Settings" in forty and "David" not in forty  # no room for it: the keys stay, the summary goes
