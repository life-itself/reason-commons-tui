"""Terminal workspace adapter: layout state and routing over the application boundary."""

import asyncio
import html
import re

import pytest

pytest.importorskip("textual")

from reason_commons.adapters.guided import GuidedConsultant  # noqa: E402
from reason_commons.adapters.tui import ReasonCommonsApp, caret_index, caret_location  # noqa: E402
from reason_commons.bootstrap import create_case, open_case  # noqa: E402
from tests.support import ScriptedConsultant  # noqa: E402


def launch(path, consultants):
    return ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                            lambda provider: consultants[provider])


def screen_text(app):
    """What is visible on screen right now, as plain text (scrolled-away content is not included)."""
    return html.unescape(re.sub(r"<[^>]+>", "", app.export_screenshot())).replace("\xa0", " ")


async def send(app, pilot, text):
    app.query_one("#editor").load_text(text)
    await pilot.press("ctrl+s")
    await app.workers.wait_for_complete()
    await pilot.pause()


def test_caret_conversion_round_trips():
    text = "one\ntwo lines\n"
    for index in range(len(text) + 1):
        assert caret_index(text, caret_location(text, index)) == index


def test_send_saves_a_revision_and_quit_keeps_the_draft(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Running").close()

    async def first():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(80, 24)) as pilot:
            await send(app, pilot, "Run 5k under 30 minutes")
            assert app.workspace_value["revision"] == 1
            assert app.query_one("#editor").text == ""
            app.query_one("#editor").load_text("5 ? q literal draft")
            await pilot.press("ctrl+q")

    async def second():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert app.query_one("#editor").text == "5 ? q literal draft"
            assert app.workspace_value["question"]["data"]["purpose"] == "guided:goal_measure"

    asyncio.run(first())
    asyncio.run(second())


def test_browsing_never_calls_the_consultant(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Local").close()
    consultant = ScriptedConsultant()

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            for view in ("goal", "tests", "actions", "reasoning", "sources", "history", "next"):
                app.show_view(view)
                await pilot.pause()
            app.action_explain()
            await pilot.pause()
    asyncio.run(run())
    assert consultant.calls == []


def test_unavailable_consultant_retains_input_and_offers_retry(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Retry").close()

    async def run():
        app = launch(path, {"guided": ScriptedConsultant([RuntimeError("offline")]),
                            "anthropic": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await send(app, pilot, "Calmer mornings")
            assert app.workspace_value["revision"] == 0
            assert app.retryable() and not app.query_one("#retry").has_class("hidden")
            app.switch_provider("anthropic")
            app.action_retry()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.workspace_value["revision"] == 1 and not app.retryable()
    asyncio.run(run())


def test_goals_home_lists_goals_newest_first_and_skips_other_folders(tmp_path):
    from reason_commons.adapters.tui import find_goals
    class Fixed:
        def __init__(self, value):
            self.value = value

        def now(self):
            return self.value
    create_case(tmp_path / "a-older", "Older goal", clock=Fixed("2026-10-01T08:00:00+00:00")).close()
    create_case(tmp_path / "b-newer", "Newer goal", clock=Fixed("2026-10-02T08:00:00+00:00")).close()
    (tmp_path / "notes").mkdir()
    (tmp_path / "exports").mkdir()
    goals = find_goals(tmp_path)
    assert [goal["name"] for goal in goals] == ["Newer goal", "Older goal"]
    assert find_goals(tmp_path / "missing") == []


def test_goal_folders_are_readable_and_unique(tmp_path):
    from reason_commons.adapters.tui import goal_folder
    assert goal_folder(tmp_path, "Sleep better, 4 nights!").name == "sleep-better-4-nights"
    (tmp_path / "sleep-better").mkdir()
    assert goal_folder(tmp_path, "Sleep better").name == "sleep-better-2"
    assert goal_folder(tmp_path, "???").name == "goal"
    assert goal_folder(tmp_path, "Exports").name == "exports-goal"


def test_goals_home_starts_a_new_goal_or_opens_an_existing_one(tmp_path):
    from reason_commons.adapters.tui import GoalsApp
    create_case(tmp_path / "running", "Running").close()

    async def start_new():
        app = GoalsApp(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            app.query_one("#goals").highlighted = 0
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press(*"Sleep better")
            await pilot.press("enter")
            await pilot.pause()
        return app.return_value

    async def open_existing():
        app = GoalsApp(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
        return app.return_value

    created = asyncio.run(start_new())
    assert created == tmp_path / "sleep-better"
    with open_case(created, writable=False) as app:
        assert app.inspect()["case"]["name"] == "Sleep better"
    assert asyncio.run(open_existing()) in {tmp_path / "running", tmp_path / "sleep-better"}


def test_header_says_saved_without_engine_revision(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Plain").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            return screen_text(app).splitlines()
    status = next(line for line in asyncio.run(run()) if "Plain · David" in line)
    assert "Saved" in status and not re.search(r"\br\d{4}\b", status)


def test_bare_command_without_a_terminal_prints_everyday_help():
    from tests.support import cli
    result = cli()
    assert result.returncode == 0 and result.stderr == ""
    assert "everyday use" in result.stdout and "advanced" in result.stdout
    assert "receipts" not in result.stdout.split("advanced")[0]


def test_loop_line_marks_done_and_current_steps():
    from reason_commons.adapters.tui import loop_line, loop_stage
    assert loop_stage(None) == "goal"
    assert loop_stage({"data": {"purpose": "guided:test_forecast"}}) == "test"
    assert loop_stage({"data": {"decision": "Review against the forecast"}}) == "review"
    assert loop_stage({"data": {"decision": "Something else entirely"}}) is None
    line = loop_line("action")
    assert "✓ Goal" in line and "✓ Test + forecast" in line and "● Action" in line and "○ Observe" in line
    assert not any(mark in loop_line(None) for mark in "✓●○")


def test_welcome_draws_the_loop_and_the_strip_follows_progress(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Welcome").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            # The welcome asks one question; the loop diagram is one press away, behind Explain this.
            assert "One small test" not in app.render_next() and "Nothing is sent until" in app.render_next()
            app.action_explain()
            assert "One small test" in app.render_next()
            app.action_explain()
            assert "● Goal" in str(app.query_one("#loop").render())
            for answer in ("Sleep better", "", "", "Phone in the kitchen"):
                await send(app, pilot, answer)
            assert "● Test + forecast" in str(app.query_one("#loop").render())
            assert "One small test" not in app.render_next()
    asyncio.run(run())


def test_example_goal_is_a_finished_loop(tmp_path):
    from reason_commons.adapters.sample import ANSWERS, build_sample
    path = build_sample(tmp_path / "example")
    with open_case(path, writable=False) as app:
        workspace = app.workspace()
        kinds = {record["kind"] for record in app.inspect()["case"]["records"]}
        assert app.inspect()["cursor"]["view"] == "tests"
    # One revision per answer, then one that brings in the trees.
    assert workspace["revision"] == len(ANSWERS) + 1
    assert {"goal", "test", "action", "observation", "claim", "link"} <= kinds
    assert workspace["question"]["data"]["purpose"] == "guided:test_change"


def test_goals_home_offers_the_example(tmp_path):
    from reason_commons.adapters.tui import SAMPLE, GoalsApp

    async def run():
        app = GoalsApp(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            app.query_one("#goals").highlighted = 1
            await pilot.press("enter")
            await pilot.pause()
        return app.return_value
    assert asyncio.run(run()) == SAMPLE


def test_trees_view_draws_imported_trees_and_exports_them(tmp_path):
    from importlib.resources import files
    path = tmp_path / "case"
    create_case(path, "Trees").close()
    source = files("reason_commons.adapters").joinpath("sample-trees.ltp.yaml")
    exported = tmp_path / "out.ltp.yaml"
    consultant = ScriptedConsultant()

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            app.show_view("trees")
            await pilot.pause()
            assert "No trees yet" in app.query_one("#content").source
            app.action_import_trees()
            await pilot.pause()
            app.screen.query_one("#destination").value = str(source)
            await pilot.press("enter")
            await pilot.pause()
            assert app.view_name == "trees"
            titles = ["Goal Tree", "Current Reality Tree", "Evaporating Cloud", "Future Reality Tree",
                      "Prerequisite Tree", "Transition Tree"]
            # One tree at a time; Ctrl+N steps through the six, then shows them all together.
            for index, title in enumerate(titles):
                drawing = str(app.query_one("#canvas").render())
                assert title in drawing and not any(other in drawing for other in titles if other != title)
                assert f"**▸ {title} (" in app.query_one("#content").source
                await pilot.press("ctrl+n")
                await pilot.pause()
            drawing = str(app.query_one("#canvas").render())
            assert all(title in drawing for title in titles) and "conflicts with" in drawing
            assert "**▸ All six**" in app.query_one("#content").source
            await pilot.press("ctrl+n")
            await pilot.pause()
            assert app.shown_tree() == "goal"
            # Ctrl+T goes back to the question and returns to the same tree.
            await pilot.press("ctrl+t")
            await pilot.pause()
            assert app.view_name == "next"
            await pilot.press("ctrl+t")
            await pilot.pause()
            assert app.view_name == "trees" and app.shown_tree() == "goal"
            app.checkpoint()
            app.action_export_trees()
            await pilot.pause()
            app.screen.query_one("#destination").value = str(exported)
            await pilot.press("enter")
            await pilot.pause()
    asyncio.run(run())
    assert consultant.calls == []
    assert exported.read_text().count("tree: ") >= 69
    with open_case(path, writable=False) as case:
        assert case.inspect()["cursor"]["display"] == {"tree": "goal"}


def sample_at(tmp_path, answers):
    from reason_commons.adapters.sample import ANSWERS, build_sample
    path = build_sample(tmp_path / "sample", answers=ANSWERS[:answers], view="next")
    return launch(path, {"guided": GuidedConsultant()})


def test_review_shows_the_original_forecast_beside_the_result_without_judging(tmp_path):
    app = sample_at(tmp_path, 9)

    async def run():
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            visible = screen_text(app)
            assert "6 of 30 newcomers come" in visible and "9 of 31 newcomers came" in visible
            assert "Nobody feels recruited or pressured" in visible and "no separate result recorded" in visible
            assert not any(verdict in visible for verdict in ("BREACH", "✓ Review", "✗"))
            # The safeguards are in the comparison now, so the band does not repeat them.
            assert "Protect" not in str(app.query_one("#pinned").render())
    asyncio.run(run())


def test_forecast_question_shows_the_change_and_does_not_repeat_the_goal(tmp_path):
    app = sample_at(tmp_path, 4)

    async def run():
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            visible = screen_text(app)
            assert 'Your change: "End each open evening with one clear invitation' in visible
            assert "(sign-up sheet): now 2 of 30" in visible  # the measure, beside the forecast question
            assert visible.count("Newcomers at our open evenings find a clear") == 1  # only in the band
    asyncio.run(run())


def test_band_marks_a_cut_and_the_goal_view_shows_it_all(tmp_path):
    app = sample_at(tmp_path, 3)
    goal = ("Newcomers at our open evenings find a clear, no-pressure next step into a first practice session, "
            "so interest turns into sustained practice.")

    async def run():
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            band = screen_text(app)
            assert "…" in band and goal not in band
            app.show_view("goal")
            await pilot.pause()
            assert goal.replace("-", "\\-").replace(".", "\\.") in app.query_one("#content").source
    asyncio.run(run())


def test_a_reply_never_moves_the_person_out_of_what_they_are_reading(tmp_path):
    """S118: an answer arriving while History is open leaves the view and focus alone."""
    import threading
    path = tmp_path / "case"
    create_case(path, "Waiting").close()
    release = threading.Event()

    class Slow(GuidedConsultant):
        def propose(self, request):
            release.wait(5)
            return super().propose(request)

    async def run():
        app = launch(path, {"guided": Slow()})
        async with app.run_test(size=(120, 40)) as pilot:
            app.query_one("#editor").load_text("Calmer mornings")
            await pilot.press("ctrl+s")
            await pilot.pause()
            assert "Asking the offline guide…" in screen_text(app)
            app.show_view("history")
            await pilot.pause()
            release.set()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.view_name == "history" and app.focused.id == "editor"
            assert "Answer ready" in screen_text(app)
            app.show_view("next")
            await pilot.pause()
            assert "Answer ready" not in screen_text(app)
            assert app.workspace_value["question"]["data"]["purpose"] == "guided:goal_measure"
    asyncio.run(run())


def test_header_names_the_focused_control_and_routes_are_not_duplicated(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Focus").close()

    async def run(size):
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            assert "Focus: Answer" in screen_text(app)
            await pilot.press("escape")
            await pilot.pause()
            assert "Focus: Reading" in screen_text(app)
            # Next tree is offered only where it means something.
            assert not app.check_action("next_tree", ()) and "Next tree" not in screen_text(app)
            app.show_view("trees")
            await pilot.pause()
            assert app.check_action("next_tree", ())
            # The Views button appears only when the destinations list does not fit.
            return app.query_one("#views").has_class("hidden"), app.query_one("#views-button").has_class("hidden")
    assert asyncio.run(run((120, 40))) == (False, True)
    assert asyncio.run(run((80, 24))) == (True, False)


def test_empty_trees_say_which_consultants_grow_them(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Empty").close()

    async def run():
        app = launch(path, {"guided": ScriptedConsultant(), "anthropic": ScriptedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            app.show_view("trees")
            await pilot.pause()
            guided = app.query_one("#content").source
            assert "No trees yet" in guided and "built-in guide" in guided and "does not add to the trees" in guided
            assert "**Consultant**" in guided and "**Import trees**" in guided
            app.switch_provider("anthropic")
            await pilot.pause()
            model = app.query_one("#content").source
            assert "They grow as you talk" in model and "built-in guide" not in model
    asyncio.run(run())
