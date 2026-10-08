"""A new goal's first-use note and How this works: they explain the screen and gate nothing."""

import asyncio

import pytest

pytest.importorskip("textual")

from reason_commons.adapters.accessible import AccessibleWorkspace  # noqa: E402
from reason_commons.adapters.guided import GuidedConsultant  # noqa: E402
from reason_commons.adapters.settings import Settings  # noqa: E402
from reason_commons.adapters.tui import ReasonCommonsApp, caret_index  # noqa: E402
from reason_commons.adapters.welcome import sketch, welcome_lines  # noqa: E402
from reason_commons.bootstrap import create_case, open_case  # noqa: E402
from rich.cells import cell_len  # noqa: E402
from tests.test_tui import send, settled, screen_text  # noqa: E402


def new_goal(tmp_path, name="Read for pleasure again"):
    path = tmp_path / "case"
    create_case(path, name).close()
    return path


def launch(path, settings=None, **options):
    return ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                            lambda provider: GuidedConsultant(), settings=settings, **options)


def test_the_note_sits_under_the_answer_box_and_the_box_keeps_focus(tmp_path):
    path = new_goal(tmp_path)

    async def run():
        app = launch(path)
        async with app.run_test(size=(120, 40)) as pilot:
            await settled(app, pilot, "#welcome", "#response")
            assert app._welcome_form == "full"
            text = screen_text(app)
            assert "NEW HERE" in text
            for line in welcome_lines("guided"):
                assert line in text, line
            # Under the box, so the answer still sits at the question; and the box has the keyboard.
            assert app.query_one("#welcome").region.y > app.query_one("#response").region.bottom - 1
            assert app.focused.id == "editor"
            # Typing goes into the answer, and Send sends at once: nothing has to be dismissed first.
            await pilot.press(*"I read again")
            assert app.query_one("#editor").text == "I read again"
            await send(app, pilot, "I read for pleasure again")
            await settled(app, pilot, "#welcome", "#response")
            # The goal's first answer is sent, so the note has done its work.
            assert app._welcome_form == "hidden" and "NEW HERE" not in screen_text(app)
    asyncio.run(run())


def test_on_a_short_screen_the_note_never_pushes_the_answer_box_away(tmp_path):
    path = new_goal(tmp_path)

    async def run():
        app = launch(path)
        async with app.run_test(size=(80, 24)) as pilot:
            await settled(app, pilot, "#welcome", "#response")
            # At 80 by 24 each line fits one row, so the note fits whole.
            assert app._welcome_form == "full"
            assert app.query_one("#response").region.bottom <= 23
            # A long draft grows the box (to five rows on a short screen); the note gives way to one line.
            app.query_one("#editor").load_text("\n".join(["a line"] * 6))
            await settled(app, pilot, "#welcome", "#response")
            assert app._welcome_form in ("line", "hidden")
            assert app.query_one("#response").region.bottom <= 23
            if app._welcome_form == "line":
                assert "New here?" in screen_text(app)
        async with launch(path).run_test(size=(80, 16)) as pilot:
            app = pilot.app
            await settled(app, pilot, "#welcome", "#response")
            assert app._welcome_form in ("line", "hidden")
            assert app.query_one("#response").region.bottom <= 15
    asyncio.run(run())


def test_hide_this_is_kept_in_the_settings_file_once_there_is_one(tmp_path):
    path = new_goal(tmp_path)
    file = tmp_path / "settings.yaml"
    Settings(file, {"version": 1, "name": "David"}).save()

    async def run(settings):
        app = launch(path, settings=settings)
        async with app.run_test(size=(120, 40)) as pilot:
            await settled(app, pilot, "#welcome", "#response")
            shown = app._welcome_form
            if shown != "hidden":
                app.query_one("#hide-welcome").press()
                await settled(app, pilot, "#welcome", "#response")
                assert app._welcome_form == "hidden" and app.focused.id == "editor"
            return shown

    assert asyncio.run(run(Settings.load(file))) == "full"
    assert Settings.load(file).get("welcome") == "hidden"
    # The next goal, or the next run, opens without it.
    assert asyncio.run(run(Settings.load(file))) == "hidden"


def test_hide_this_never_creates_the_settings_file_before_first_start_finishes(tmp_path):
    path = new_goal(tmp_path)
    file = tmp_path / "settings.yaml"

    async def run():
        app = launch(path, settings=Settings.load(file))
        async with app.run_test(size=(120, 40)) as pilot:
            await settled(app, pilot, "#welcome", "#response")
            app.query_one("#hide-welcome").press()
            await settled(app, pilot, "#welcome", "#response")
            return app._welcome_form
    assert asyncio.run(run()) == "hidden"
    # First start is over only when setup saves the settings; hiding a note does not end it.
    assert not file.exists()


def test_how_this_works_opens_from_the_note_and_commands_and_keeps_the_draft(tmp_path):
    path = new_goal(tmp_path)

    async def run():
        app = launch(path)
        async with app.run_test(size=(120, 40)) as pilot:
            await settled(app, pilot, "#welcome", "#response")
            editor = app.query_one("#editor")
            editor.load_text("Half a thought")
            editor.cursor_location = (0, 4)
            app.query_one("#how-it-works").press()
            await pilot.pause()
            assert type(app.screen).__name__ == "HowItWorksScreen"
            text = screen_text(app)
            assert "How this works" in text and "(5)" in text and "Answer as you" in text
            await pilot.press("escape")
            await pilot.pause()
            assert editor.text == "Half a thought" and caret_index(editor.text, editor.cursor_location) == 4
            # Commands lists it after Help, so typing "help" still finds Help first.
            names = [name for _, name, _, _ in app.action_list()]
            assert names.index("How this works") == names.index("Help") + 1
            assert not [detail for _, name, detail, _ in app.action_list()
                        if name == "How this works" and "help" in detail.lower()]
    asyncio.run(run())


def test_how_this_works_draws_the_screen_only_where_it_fits(tmp_path):
    from reason_commons.adapters.welcome import HowItWorksScreen
    path = new_goal(tmp_path)
    for width in (76, 52):
        assert {cell_len(line) for line, _ in sketch(width)} == {width}

    async def drawn(size):
        app = launch(path)
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            app.push_screen(HowItWorksScreen("guided"))
            await pilot.pause()
            await pilot.pause()
            holder = app.screen.query_one("#how-sketch")
            return holder.display, screen_text(app)
    shown, text = asyncio.run(drawn((120, 40)))
    assert shown and "Test + forecast" in text
    shown, text = asyncio.run(drawn((80, 24)))
    assert shown and "Answer as you" in text
    shown, text = asyncio.run(drawn((60, 24)))
    # Too narrow for a drawing: the numbered parts still say everything.
    assert not shown and "(1)" in text


def test_the_note_stays_away_from_goals_that_have_begun_and_from_other_views(tmp_path):
    path = new_goal(tmp_path)

    async def run():
        app = launch(path)
        async with app.run_test(size=(120, 40)) as pilot:
            await settled(app, pilot, "#welcome", "#response")
            app.show_view("goal")
            await settled(app, pilot, "#welcome", "#response")
            assert app._welcome_form == "hidden"
            app.show_view("next")
            await settled(app, pilot, "#welcome", "#response")
            assert app._welcome_form == "full"
            await send(app, pilot, "Sleep better")
        async with launch(path).run_test(size=(120, 40)) as pilot:
            await settled(pilot.app, pilot, "#welcome", "#response")
            # This goal has a question now: the note does not come back.
            return pilot.app._welcome_form
    assert asyncio.run(run()) == "hidden"


def test_the_accessible_presentation_says_the_same_on_a_new_goal(tmp_path):
    path = new_goal(tmp_path)
    written = []
    with open_case(path, consultant=GuidedConsultant()) as case:
        workspace = AccessibleWorkspace(case, "David", width=100, height=60, write=written.append,
                                        consultant="the offline guide")
        workspace.start()
        text = "".join(written)
        for line in welcome_lines("guided"):
            assert line in text, line
        assert any(control.label == "How this works" for control in workspace.controls())
        workspace.open("how")
        assert "Views" in "".join(written[-3:]) or "Views" in "".join(written)
