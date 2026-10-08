"""Terminal workspace adapter: layout state and routing over the application boundary."""

import asyncio
import os
import html
import re

import pytest

pytest.importorskip("textual")

from reason_commons.adapters.guided import GuidedConsultant  # noqa: E402
from reason_commons.adapters.tui import TREE_NAV, ReasonCommonsApp, caret_index, caret_location  # noqa: E402
from reason_commons.bootstrap import create_case, open_case  # noqa: E402
from tests.support import ScriptedConsultant, timezone  # noqa: E402


@pytest.fixture
def utc():
    """The computer's own time zone is UTC for the test, and is put back after it."""
    with timezone("UTC"):
        yield


@pytest.fixture
def berlin():
    with timezone("Europe/Berlin"):
        yield


def launch(path, consultants):
    return ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                            lambda provider: consultants[provider])


def screen_text(app):
    """What is visible on screen right now, as plain text (scrolled-away content is not included)."""
    return html.unescape(re.sub(r"<[^>]+>", "", app.export_screenshot())).replace("\xa0", " ")


def as_read(renderable, width=200):
    """A drawing's words as read: rendered to plain text, with wrapped lines joined."""
    import io
    from rich.console import Console
    console = Console(width=width, file=io.StringIO(), record=True, color_system=None)
    console.print(renderable)
    return " ".join(console.export_text().split())


async def settled(app, pilot, *selectors):
    """Pause until these widgets stop moving: the reading pane is fitted over a few frames, and a check made
    after a single pause can catch it a row out."""
    last = None
    for _ in range(40):
        await pilot.pause()
        now = [app.query_one(selector).region for selector in selectors]
        if now == last:
            return
        last = now


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


def test_a_save_timer_that_fires_after_the_workspace_closes_does_nothing(tmp_path):
    # The delayed draft save (0.8 s) can fire while the app is being taken down, when the editor is gone.
    path = tmp_path / "case"
    create_case(path, "Running").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            app.query_one("#editor").load_text("kept draft")
            await pilot.press("ctrl+q")
        assert not app.query("#editor")
        app.checkpoint()  # as the late timer would; it must not raise

    asyncio.run(run())
    with open_case(path, writable=False) as case:
        assert case.workspace()["draft"]["draft"] == "kept draft"


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
            goals = app.query_one("#goals")
            goals.highlighted = goals.get_option_index("new")
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
    status = next(line for line in asyncio.run(run()) if "Plain" in line)
    # The goal's name on the left, who you are and whether it is saved on the right.
    assert re.search(r"Plain\s+David · Saved", status) and not re.search(r"\br\d{4}\b", status)
    # The view is named by the list and the page, and the keyboard by the frame: neither is repeated here.
    assert "Next step" not in status and "Focus" not in status


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
    # Every answer, then the trees brought in; the organiser accepted each reply's proposals as they came,
    # and kept her own goal when the trees' file proposed another.
    assert workspace["backlog"] == [] and workspace["goals"][0]["data"]["statement"] == ANSWERS[0]
    assert len(workspace["history"]) == 0 and app.history()["revisions"][-1]["decisions"]
    assert {"goal", "test", "action", "observation", "claim", "link"} <= kinds
    assert workspace["question"]["data"]["purpose"] == "guided:test_change"


def test_goals_home_offers_the_example(tmp_path):
    from reason_commons.adapters.tui import SAMPLE, GoalsApp

    async def run():
        app = GoalsApp(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            goals = app.query_one("#goals")
            goals.highlighted = goals.get_option_index("sample")
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
            # What the file brings waits for the operator; Accept all takes it.
            assert app.view_name == "backlog" and "Decide it first" in app.query_one("#content").source
            assert all(not t["claims"] for t in app.workspace_value["trees"])
            app.accept_reply()
            await pilot.pause()
            app.show_view("trees")
            await pilot.pause()
            assert app.view_name == "trees"
            titles = ["Goal Tree", "Current Reality Tree", "Evaporating Cloud", "Future Reality Tree",
                      "Prerequisite Tree", "Transition Tree"]
            # The first visit shows all six, each folded at what its tree is for, named under Trees in Views.
            drawing = str(app.query_one("#canvas").render())
            assert all(title in drawing for title in titles) and "▸ 9 below" in drawing
            assert "## All six trees" in app.query_one("#content").source
            prompts = [str(o.prompt) for o in app.query_one("#views").options]
            assert prompts[3:6] == ["▸ Trees", "  ▸ All six", "    Goal Tree"]
            # Ctrl+N steps through the six, one at a time, then back to all six.
            for index, title in enumerate(titles):
                await pilot.press("ctrl+n")
                await pilot.pause()
                assert f"## {title}" in app.query_one("#content").source
                drawing = str(app.query_one("#canvas").render())
                assert not any(other in drawing for other in titles)  # the page heading names the tree
                assert "  ▸ " + TREE_NAV[app.shown_tree()] in [str(o.prompt) for o in app.query_one("#views").options]
                if title == "Evaporating Cloud":  # a complete cloud is drawn as its five boxes
                    assert "SHARED OBJECTIVE" in drawing and "◀─⚡─▶" in drawing and "(1) ┆ assuming" in drawing
            await pilot.press("ctrl+n", "ctrl+n")
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
        assert case.inspect()["cursor"]["display"] == {"tree": "goal", "density": "compact"}


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
            assert goal in " ".join(screen_text(app).split())
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


def test_focus_is_a_strong_frame_and_the_footer_says_what_the_keys_do(tmp_path):
    """S114: the focused control stays visible. A heavy accent frame shows where the keyboard is; the old
    "Focus: Answer" label read like debug output, and a person cannot miss a frame."""
    path = tmp_path / "case"
    create_case(path, "Frames").close()

    def heavy(selector, app, side="top"):
        return getattr(app.query_one(selector).styles, f"border_{side}")[0] == "heavy"

    async def run(size):
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            assert app.focused.id == "editor" and heavy("#response", app) and not heavy("#views-pane", app)
            assert "Focus:" not in screen_text(app)
            assert "Save & quit" in screen_text(app) and "Next control" in screen_text(app)
            await pilot.press("escape")
            await pilot.pause()
            assert app.focused.id == "main" and heavy("#main", app, "left") and not heavy("#response", app)
            # Next tree is offered only where it means something.
            assert not app.check_action("next_tree", ()) and "Next tree" not in screen_text(app)
            app.show_view("trees")
            await pilot.pause()
            assert app.check_action("next_tree", ())
            # The Views button appears only when the destinations list does not fit.
            return app.query_one("#views").has_class("hidden"), app.query_one("#views-button").has_class("hidden")
    assert asyncio.run(run((120, 40))) == (False, True)
    assert asyncio.run(run((80, 24))) == (True, False)


def test_the_views_list_has_its_own_frame_and_tab_goes_back_to_the_answer(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Views").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.query_one("#views").focus()
            await pilot.pause()
            frame = app.query_one("#views-pane").styles
            assert frame.border_top[0] == "heavy" and frame.border_left[0] == "heavy"
            text = screen_text(app)
            assert "Choose view" in text and "Open" in text and "Back to answer" in text
            assert "Save & quit" not in text  # the footer speaks about this pane, not every pane
            # The open view is marked, and the one the cursor is on is highlighted.
            prompts = [str(option.prompt) for option in app.query_one("#views").options]
            assert prompts[0] == "▸ Next step" and all(not prompt.startswith("▸") for prompt in prompts[1:])
            await pilot.press("down", "down", "down", "enter")
            await pilot.pause()
            assert app.view_name == "trees"
            assert [str(o.prompt) for o in app.query_one("#views").options][3] == "▸ Trees"
            await pilot.press("tab")
            await pilot.pause()
            assert app.focused.id == "editor"
    asyncio.run(run())


def test_commands_and_help_are_footer_controls_that_tab_reaches(tmp_path):
    """The Actions and Help buttons are gone; Commands and Help are in the footer, where Tab still reaches them."""
    path = tmp_path / "case"
    create_case(path, "Footer").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert not app.query("#actions") and "Actions" not in screen_text(app)
            order = []
            for _ in range(8):
                await pilot.press("tab")
                order.append(app.focused.id)
            assert order.index("send") < order.index("commands") < order.index("help"), order
            app.query_one("#commands").focus()
            await pilot.press("enter")
            await pilot.pause()
            assert type(app.screen).__name__ == "MenuScreen" and "Commands" in screen_text(app)
            await pilot.press("escape")
            await pilot.pause()
            app.query_one("#help").focus()
            await pilot.press("enter")
            await pilot.pause()
            assert type(app.screen).__name__ == "HelpScreen"
    asyncio.run(run())


def test_every_footer_hint_that_names_a_key_is_a_real_binding(tmp_path):
    """The footer may not promise a key that does nothing: each hint with a key to press must be bound."""
    path = tmp_path / "case"
    create_case(path, "Hints").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            for focus in ("editor", "views", "main", "send", "commands", "help"):
                app.query_one("#" + focus).focus()
                await pilot.pause()
                before, after = app.footer_hints()
                bound = set(app.screen.active_bindings)
                for key, label, press, *short in before + after:
                    assert press is None or press in bound, (focus, key, label, press)
    asyncio.run(run())


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


def test_a_reply_that_grows_the_trees_is_named_and_marked_without_moving_the_view(tmp_path):
    from tests.test_trees import claim, link, with_updates
    path = tmp_path / "case"
    create_case(path, "Open evenings").close()
    consultant = ScriptedConsultant([
        with_updates(claim("temp_ude", "Newcomers do not know the next step"),
                     claim("temp_cause", "We never offer one", role="intermediate_cause", basis="participant_report"),
                     link("temp_link", "temp_cause", "temp_ude")),
        with_updates(claim("temp_new", "We never offer a next step after open evenings",
                           role="intermediate_cause", replaces="C2@1")),
    ])

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            await send(app, pilot, "Newcomers do not know the next step, because we never offer one")
            assert app.view_name == "next"
            # Under the next question: what the answer led the consultant to propose, drawn as the trees draw it,
            # beside the words it came from, while the person who said them still knows what they meant.
            under = as_read(app.render_context())
            assert "PROPOSED FROM YOUR ANSWER · NOT YET IN YOUR MODEL Current Reality Tree" in under
            assert "Newcomers do not know the next step · undesirable effect NEW" in under
            assert "because: We never offer one · cause · reported NEW" in under
            assert "You wrote" in under and "“Newcomers do not know the next step, because we never offer one”" in under
            assert "Accept all admits these to your model; it does not make them true" in under
            # Drawn, so not summed up in a line as well, nor listed again as context rows.
            assert "In the trees" not in app.query_one("#content").source
            assert under.count("We never offer one") == 1 and under.count("Newcomers do not know the next step ·") == 1
            # Nothing is in the trees until it is accepted; Accept all is beside Send.
            assert all(not t["claims"] for t in app.workspace_value["trees"])
            assert not app.query_one("#accept-all").has_class("hidden") and "Backlog · 3" in screen_text(app)
            await pilot.click("#accept-all")
            await pilot.pause()
            assert app.query_one("#accept-all").has_class("hidden") and "PROPOSED" not in as_read(app.render_context())
            await pilot.press("ctrl+t")
            await pilot.pause()
            # What the acceptance added opens in the overview, marked; nothing new is folded away.
            drawing = str(app.query_one("#canvas").render())
            assert drawing.count("NEW") == 2 and "because: We never offer one" in drawing
            # A reply that arrives while the trees are open leaves them open; what it proposes waits.
            await send(app, pilot, "Say the cause more precisely")
            assert app.view_name == "trees" and "We never offer one" in str(app.query_one("#canvas").render())
            assert "1 proposal for the trees waits in Backlog" in app.query_one("#content").source.replace(
                "proposal for the trees wait in", "proposal for the trees waits in")
            app.accept_reply()
            await pilot.pause()
            drawing = " ".join(str(app.query_one("#canvas").render()).split())  # as read, across wrapped lines
            assert "REWORDED" in drawing and "We never offer a next step after open evenings" in drawing
            assert "NEW" not in drawing and "We never offer one" not in drawing
            assert "Current Reality Tree: 1 statement reworded" in app.query_one("#content").source
            # The link was stated for the earlier wording, so it waits in Backlog to be reviewed.
            assert [e["entry"] for e in app.backlog()] == ["review"]

    async def later():
        # Opened again later, the goal is not marked; History still shows what each step changed.
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            app.show_view("next")
            await pilot.pause()
            assert "In the trees" not in app.query_one("#content").source
            assert "PROPOSED FROM" not in as_read(app.render_context())
            app.show_view("trees")
            await pilot.pause()
            assert "REWORDED" not in str(app.query_one("#canvas").render())
            assert "changed)" not in app.query_one("#content").source
    asyncio.run(run())
    asyncio.run(later())


def test_choose_a_tree_statement_and_see_where_it_came_from(tmp_path):
    from tests.test_trees import claim, link, with_updates
    from reason_commons.adapters.tui import StatementScreen
    path = tmp_path / "case"
    create_case(path, "Open evenings", acceptance="automatic", actor="David").close()
    consultant = ScriptedConsultant([
        with_updates(claim("temp_ude", "Newcomers do not know the next step"),
                     claim("temp_cause", "We never offer one", role="intermediate_cause", basis="participant_report"),
                     link("temp_link", "temp_cause", "temp_ude", assumption="Nobody else tells them")),
        with_updates(claim("temp_new", "We never offer a next step after open evenings",
                           role="intermediate_cause", replaces="C2@1")),
    ])

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            await send(app, pilot, "Newcomers do not know the next step, because we never offer one")
            await send(app, pilot, "Say the cause more precisely")
            editor = app.query_one("#editor")
            editor.load_text("half an answer")
            editor.cursor_location = (0, 4)
            await pilot.press("ctrl+t")
            await pilot.pause()
            # Opening the trees puts the keys on them, with the first statement chosen and shown beside them.
            assert app.focused.id == "canvas" and app.query_one("#canvas").styles.border_left[0] == "heavy"
            assert "Choose statement" in screen_text(app) and "Next tree" in screen_text(app)
            assert not app.query_one("#inspector").has_class("hidden")
            assert "Newcomers do not know the next step" in " ".join(
                str(app.query_one("#inspector-text").render()).split())
            await pilot.press("down")
            await pilot.pause()
            # As read: across wrapped lines, and past the dotted rule that marks an assumption.
            panel = " ".join(str(app.query_one("#inspector-text").render()).replace("┆", "").split())
            assert "We never offer a next step after open evenings" in panel
            assert "We never offer one" in panel  # its earlier wording
            assert "David" in panel and "Say the cause more precisely" in panel  # who, in their own words
            assert "Causes" in panel and "Nobody else tells them" in panel  # its link, read from its side
            # In all six, Enter opens the statement's own tree, still chosen; there Enter opens its details.
            await pilot.press("enter")
            await pilot.pause()
            assert app.shown_tree() == "current_reality" and app.selected_claim == "C2@2"
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, StatementScreen)
            await pilot.press("escape")
            await pilot.pause()
            assert app.focused.id == "canvas" and app.selected_claim == "C2@2"
            # Ctrl+T goes back to the question with the draft and caret as they were.
            await pilot.press("ctrl+t")
            await pilot.pause()
            assert app.view_name == "next" and app.focused.id == "editor"
            assert editor.text == "half an answer" and editor.cursor_location == (0, 4)
    asyncio.run(run())
    assert len(consultant.calls) == 2  # choosing and inspecting asked the consultant nothing
    with open_case(path, writable=False) as case:
        assert case.inspect()["case"]["revision"] == 2


def test_statement_details_open_full_screen_at_80_columns_and_the_choice_survives_a_restart(tmp_path):
    from importlib.resources import files
    from reason_commons.adapters.ltp_trees import import_trees
    from reason_commons.adapters.tui import StatementScreen
    path = tmp_path / "case"
    create_case(path, "Imported", acceptance="automatic", actor="David").close()
    import_trees(path, str(files("reason_commons.adapters").joinpath("sample-trees.ltp.yaml")), "David")
    chosen = {}

    async def first():
        app = launch(path, {"guided": ScriptedConsultant()})
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("ctrl+t")
            await pilot.pause()
            assert app.focused.id == "canvas" and app.query_one("#inspector").has_class("hidden")
            await pilot.press("ctrl+n")  # from all six to the Goal Tree, where Enter opens the details
            await pilot.press("down", "down")
            await pilot.pause()
            chosen["ref"] = app.selected_claim
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, StatementScreen)
            details = " ".join(str(app.screen.query_one("#statement-text").render()).split())
            assert "sample-trees.ltp.yaml" in details and "Goal Tree" in details
            await pilot.press("escape")
            await pilot.pause()
            await pilot.press("ctrl+q")

    async def second():
        app = launch(path, {"guided": ScriptedConsultant()})
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert app.view_name == "trees" and app.selected_claim == chosen["ref"]
    asyncio.run(first())
    asyncio.run(second())


def test_a_live_resize_lays_the_workspace_out_for_the_new_size(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Resize").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            assert not app.query_one("#views").has_class("hidden")
            await pilot.resize_terminal(80, 24)
            await pilot.pause()
            assert app.query_one("#views").has_class("hidden") and not app.query_one("#views-button").has_class("hidden")
            assert app.query_one("#editor").styles.max_height.value == 5
            await pilot.resize_terminal(120, 40)
            await pilot.pause()
            assert not app.query_one("#views").has_class("hidden") and app.query_one("#views-button").has_class("hidden")
    asyncio.run(run())


def test_loop_line_is_a_spine_joined_by_rules():
    from reason_commons.adapters.tui import loop_line
    line = loop_line("test")
    assert line.count("─") == 4  # five steps, four joins
    assert "✓ Goal" in line and "● Test + forecast" in line and "○ Action" in line
    assert "then a new loop begins" in loop_line("review") and "then a new loop begins" not in loop_line("review", wide=False)


def test_a_missing_measure_is_named_not_hidden_behind_no_goal_yet(tmp_path):
    """A goal with a name but nothing recorded yet used to read "No goal yet" under the goal's own title."""
    path = tmp_path / "case"
    create_case(path, "become the person i want to become").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            text = screen_text(app)
            assert "No goal yet" not in text and not app.query_one("#pinned").display
            assert str(app.query_one("#measure").render()) == "Measure: not set"
            # At 80 columns it still fits next to the five steps.
            await pilot.resize_terminal(80, 24)
            await pilot.pause()
            assert str(app.query_one("#measure").render()) == "Measure: not set"
    asyncio.run(run())


def test_the_measure_replaces_the_aside_after_review_and_gives_way_on_a_narrow_screen(tmp_path):
    app = sample_at(tmp_path, 9)

    async def run():
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            measure = str(app.query_one("#measure").render())
            assert measure.startswith("Measure: Newcomers at a first practice") and measure.endswith("…")
            assert "then a new loop begins" not in str(app.query_one("#loop").render())
            await pilot.resize_terminal(80, 24)
            await pilot.pause()
            assert str(app.query_one("#measure").render()) == ""  # no room for a measure worth reading
    asyncio.run(run())


def test_the_heading_is_strongest_the_question_plain_and_the_optional_hint_quiet(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Hierarchy").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert app.render_next().splitlines()[0] == "## Clarify the goal"
            await send(app, pilot, "Sleep better")
            lines = [line for line in app.render_next().splitlines() if line]
            assert lines[0] == "## Clarify the goal"
            assert lines[1].startswith("How will you know it got better?") and "**" not in lines[1]
            assert lines[2] == "###### Leave empty if you don't know yet\\."  # stored text is escaped for Markdown
    asyncio.run(run())


def test_the_answer_box_sits_under_a_short_question_and_stays_in_view_under_a_long_page(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Placement").close()
    long_page = sample_at(tmp_path, 9)

    async def short():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await settled(app, pilot, "#content", "#response")
            content, box = app.query_one("#content"), app.query_one("#response")
            # Right under the question and its hint, not a screenful below it.
            assert 0 <= box.region.y - content.region.bottom <= 2, (content.region, box.region)
            # The hint about Enter and Send is beside the buttons when there is room, and under them when there is not.
            assert not app.query_one("#hint").has_class("hidden") and app.query_one("#hint-below").has_class("hidden")
            await pilot.resize_terminal(80, 24)
            await settled(app, pilot, "#content", "#response")
            assert app.query_one("#hint").has_class("hidden") and not app.query_one("#hint-below").has_class("hidden")

    async def long():
        async with long_page.run_test(size=(80, 24)) as pilot:
            await settled(long_page, pilot, "#main", "#response")
            box, main = long_page.query_one("#response"), long_page.query_one("#main")
            assert box.region.bottom <= 23 and main.region.bottom <= box.region.y  # the page scrolls above it
            assert main.max_scroll_y > 0
    asyncio.run(short())
    asyncio.run(long())


def test_your_words_say_when_in_your_own_clock_and_hide_internal_ids(tmp_path, monkeypatch, utc):
    from datetime import date
    from reason_commons.adapters import timeline
    monkeypatch.setattr(timeline, "today", lambda: date(2026, 10, 5))
    path = tmp_path / "case"
    create_case(path, "Words").close()

    class Fixed:
        def __init__(self, value):
            self.value = value

        def now(self):
            return self.value
    with open_case(path, consultant=GuidedConsultant(), clock=Fixed("2026-10-03T18:02:05.379311+00:00")) as case:
        target = case.workspace()["target"]
        case.submit("i want to consistently progress", "davidjoseph", target["base_revision"],
                    target["response_target"])

    async def run(speakers):
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            if speakers == 2:
                await send(app, pilot, "and enjoy it")
            app.show_view("sources")
            await pilot.pause()
            return app.query_one("#content").source
    one = asyncio.run(run(1))
    assert "###### Oct 3, 18:02" in one and "> i want to consistently progress" in one
    assert "in000001" not in one and "davidjoseph" not in one and "+00:00" not in one
    two = asyncio.run(run(2))
    # With two voices, who said what matters, so each says who.
    assert "davidjoseph · Oct 3, 18:02" in two and "David · " in two


def test_the_time_helpers_use_the_persons_clock_and_drop_this_years_year(monkeypatch, berlin):
    from datetime import date
    from reason_commons.adapters import timeline
    monkeypatch.setattr(timeline, "today", lambda: date(2026, 10, 5))
    assert timeline.moment("2026-10-03T18:02:05.379311+00:00") == "Oct 3, 20:02"
    assert timeline.short_day("2026-10-03T18:02:05+00:00") == "Oct 3"
    assert timeline.short_day("2026-10-03T23:30:00+00:00") == "Oct 4"  # their clock has passed midnight
    assert timeline.short_day("2025-12-31T09:00:00+00:00") == "Dec 31, 2025"
    assert timeline.moment("2026-10-03T18:02:05Z") == "Oct 3, 20:02"  # a Z for UTC, as other tools write it
    assert timeline.moment("not a time") == "not a time" and timeline.moment(None) == "None"


def test_the_answer_box_shows_an_example_only_when_the_guide_asked(tmp_path):
    from reason_commons.adapters.guided import PLACEHOLDERS
    path = tmp_path / "case"
    create_case(path, "Example").close()

    async def run(provider):
        app = ReasonCommonsApp(path, "David", provider, lambda c: open_case(path, consultant=c),
                               lambda chosen: GuidedConsultant())
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            first = app.query_one("#editor").placeholder
            if provider == "guided":
                await send(app, pilot, "Sleep better")
            return first, app.query_one("#editor").placeholder
    first, second = asyncio.run(run("guided"))
    assert first == PLACEHOLDERS["goal"] and second == PLACEHOLDERS["goal_measure"]
    assert asyncio.run(run("anthropic")) == ("", "")  # another consultant asks its own questions


def test_footer_hints_can_be_clicked(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Clicks").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trees = next(h for h in app.query("Hint") if "Trees" in str(h.render()))
            await pilot.click(trees)
            await pilot.pause()
            assert app.view_name == "trees"
    asyncio.run(run())


async def footer_settled(app, pilot):
    """Wait until the footer's hints have stopped moving (they are laid out a frame after they change)."""
    await settled(app, pilot, "#hint-0", "#commands", "#help")


def footer_fits(app):
    """Every shown hint lies inside the bar, none overlaps another, and Commands and Help are among them."""
    width = app.size.width
    shown = sorted((h for h in app.query("Hint") if not h.has_class("hidden")), key=lambda h: h.region.x)
    assert {"commands", "help"} <= {h.id for h in shown}, [h.id for h in shown]
    assert all(h.region.right <= width for h in shown), [(h.id, h.region.right) for h in shown]
    assert all(a.region.right <= b.region.x for a, b in zip(shown, shown[1:]))
    return [str(h.render()) for h in shown]


def test_the_footer_fits_the_smallest_terminals_and_keeps_commands_and_help(tmp_path):
    """At 80 columns (S117) and at the 40 the specification allows, no hint is cut off and Help stays visible."""
    from importlib.resources import files
    from reason_commons.adapters.ltp_trees import import_trees
    path = tmp_path / "case"
    create_case(path, "Narrow", acceptance="automatic", actor="David").close()
    import_trees(path, str(files("reason_commons.adapters").joinpath("sample-trees.ltp.yaml")), "David")

    async def run(size):
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            seen = {}
            for focus in ("editor", "send", "explain", "moves", "views-button", "main", "commands", "help"):
                app.query_one("#" + focus).focus()
                await footer_settled(app, pilot)
                seen[focus] = footer_fits(app)
            await pilot.press("ctrl+t")  # the trees: the longest hints of all
            await footer_settled(app, pilot)
            assert app.focused.id == "canvas"
            seen["canvas"] = footer_fits(app)
            app.show_view("history")
            app.query_one("#timeline").focus()
            await footer_settled(app, pilot)
            seen["timeline"] = footer_fits(app)
            return seen
    wide = asyncio.run(run((120, 40)))
    assert "tab Next control" in wide["editor"] and "^t Back to question" in wide["canvas"]
    narrow = asyncio.run(run((80, 24)))
    assert "tab Next control" in narrow["editor"]  # it still fits, so it is not shortened
    assert "tab Next" in narrow["send"] and "tab Next control" not in narrow["send"]  # shortened to fit
    # The trees open on all six, where Enter opens the chosen statement's tree and Space unfolds it.
    assert "↑↓ Choose" in narrow["canvas"] and "space Unfold" in narrow["canvas"] and "⏎ Open" in narrow["canvas"]
    assert "^n Next tree" in narrow["canvas"]
    smallest = asyncio.run(run((40, 24)))
    assert all(hints[-1] == "f1 Help" and "^p Commands" in hints for hints in smallest.values())


def test_a_wider_terminal_brings_back_the_hints_a_narrow_one_dropped(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Resize").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await footer_settled(app, pilot)
            assert "tab Next control" in footer_fits(app) and "^q Save & quit" in footer_fits(app)
            await pilot.resize_terminal(40, 24)
            await footer_settled(app, pilot)
            narrow = footer_fits(app)
            assert "tab Next control" not in narrow and narrow[-1] == "f1 Help"
            await pilot.resize_terminal(120, 40)
            await footer_settled(app, pilot)
            assert "tab Next control" in footer_fits(app) and "^q Save & quit" in footer_fits(app)
    asyncio.run(run())


def test_the_story_footer_fits_at_80_columns(tmp_path):
    """The story opens with the keyboard on a button, whose hints are the longest in the workspace."""
    from importlib.resources import files
    from reason_commons.adapters.story import load_story
    from reason_commons.adapters.tui import STORY_ARCHIVE
    from reason_commons.bootstrap import import_case
    path = tmp_path / "story"
    import_case(str(files("reason_commons.adapters").joinpath(STORY_ARCHIVE)), str(path)).close()

    async def run():
        app = ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                               lambda provider: GuidedConsultant(), story=load_story())
        async with app.run_test(size=(80, 24)) as pilot:
            await footer_settled(app, pilot)
            assert app.focused.id == "earlier"
            assert any("Press" in hint for hint in footer_fits(app))
    asyncio.run(run())


def test_the_loop_line_always_shows_where_you_are(tmp_path):
    from reason_commons.adapters.tui import loop_line
    for width in (40, 50, 56, 58, 60, 62, 80, 120):
        text = lambda line: __import__("textual.content", fromlist=["Content"]).Content.from_markup(line)
        line = loop_line("review", wide=False, width=width)
        assert text(line).cell_length <= width and "● Review" in text(line).plain, (width, text(line).plain)
    assert loop_line("review", wide=False, width=120).count("─") == 4  # the joins, when there is room
    assert "─" not in loop_line("review", wide=False, width=58)  # none when there is not
    assert loop_line("observe", wide=False, width=40).endswith("· step 4 of 5[/]")  # only where you are
    app = sample_at(tmp_path, 9)

    async def run():
        async with app.run_test(size=(60, 24)) as pilot:
            await pilot.pause()
            assert "● Review" in str(app.query_one("#loop").render())
    asyncio.run(run())


def test_text_a_person_wrote_is_never_read_as_markup(tmp_path):
    """Names, measures and goal titles can hold brackets and backslashes; they show exactly as written."""
    path = tmp_path / "case"
    create_case(path, "Hostile").close()

    async def run():
        app = ReasonCommonsApp(path, "Dana [QA]", "guided", lambda c: open_case(path, consultant=c),
                               lambda provider: GuidedConsultant())
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert str(app.query_one("#response").border_title) == "Answer as Dana [QA]"
            app.pinned_goal = lambda: {"ref": "G1@1", "data": {"measure": "20 pages [x] a day, now [~5]\\"}}
            app.render_stepper()
            assert str(app.query_one("#measure").render()) == "Measure: 20 pages [x] a day, now [~5]\\"
    asyncio.run(run())


def test_commands_and_help_can_be_clicked_in_the_footer(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Clicks").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            for control, screen in (("#commands", "MenuScreen"), ("#help", "HelpScreen")):
                before = app.query_one(control).region
                await pilot.click(control)
                # Clicking gives the control focus, and the footer must not move under the pointer as it does.
                assert app.query_one(control).region == before
                for _ in range(40):  # a menu takes a few frames to appear
                    await pilot.pause()
                    if type(app.screen).__name__ == screen:
                        break
                assert type(app.screen).__name__ == screen
                await pilot.press("escape")
                await pilot.pause()
    asyncio.run(run())


def test_same_person_is_a_generous_match_of_names():
    from reason_commons.adapters.tui import same_person
    assert same_person("David", "david") and same_person("davidjoseph", "David") and same_person("David", "davidjoseph")
    assert not same_person("Rufus", "David") and not same_person("", "David") and not same_person("David", " ")


def test_words_someone_else_wrote_say_who_even_when_they_are_the_only_voice(tmp_path, utc):
    """Your words hides names when it is all one person; it must not mislabel a shared goal's words as yours."""
    path = tmp_path / "case"
    create_case(path, "Shared").close()
    with open_case(path, consultant=GuidedConsultant()) as case:
        target = case.workspace()["target"]
        case.submit("The pull to act is real", "Rufus", target["base_revision"], target["response_target"])

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})  # opened as David
        async with app.run_test(size=(120, 40)) as pilot:
            app.show_view("sources")
            await pilot.pause()
            return app.query_one("#content").source
    assert "Rufus · " in asyncio.run(run())


def imported_trees(tmp_path):
    from importlib.resources import files
    from reason_commons.adapters.ltp_trees import import_trees
    path = tmp_path / "case"
    # These tests are about reading the trees, so the case accepts what it brings in as it arrives.
    create_case(path, "Imported", acceptance="automatic", actor="David").close()
    import_trees(path, str(files("reason_commons.adapters").joinpath("sample-trees.ltp.yaml")), "David")
    return path


def ref_of(app, statement):
    return next(c["ref"] for t in app.workspace_value["trees"] for c in t["claims"] if c["statement"] == statement)


def styles_at(text, words):
    """The styles a drawing gives the first character of these words (their first four, which a drawing
    wrapped to its width keeps on one line)."""
    start = text.plain.index(" ".join(words.split()[:4]))
    return " ".join(str(span.style) for span in text.spans if span.start <= start < span.end)


def test_working_in_a_tree_quiets_all_but_the_chosen_statements_chunk(tmp_path):
    """Dim, not hide: while the keyboard is on a tree, the chosen statement, what it hangs under and what hangs
    under it keep their colours, and every other line takes one quiet tone in the same place. Leaving the
    drawing brings the whole tree back evenly; all six, which is for seeing the whole, never dims."""
    from textual.color import Color
    from reason_commons.adapters.tui import QUIET
    path = imported_trees(tmp_path)
    consultant = ScriptedConsultant()
    chosen, above, below = ("Others may admire the work without reproducing it",
                            "The group is busy while durable-adoption throughput remains low",
                            "Pockets are difficult to form and remain fragile or isolated")
    elsewhere = "Throughput is not yet operationally defined and accepted"

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("ctrl+t")
            await pilot.pause()
            variables = app.theme_variables
            tone = Color.parse(variables["foreground"]).blend(Color.parse(variables["background"]), QUIET).hex
            assert tone not in " ".join(str(span.style) for span in app.render_trees().spans)  # all six: whole
            app.show_tree("current_reality")
            app.query_one("#canvas").focus()
            await pilot.pause()
            while app.selected_claim != ref_of(app, chosen):
                await pilot.press("down")
            await pilot.pause()
            drawing = app.render_trees()
            for words in (chosen, above, below):
                assert tone not in styles_at(drawing, words), words
            assert tone in styles_at(drawing, elsewhere)
            # Nothing moved or went: every statement is still drawn, in the same order.
            assert all(words in " ".join(drawing.plain.replace("│", "").split()) for words in (chosen, above, below, elsewhere))
            # The page says what the tree does not state yet.
            assert "10 statements · 9 links · 10 statements state no basis" in app.query_one("#content").source
            # The keyboard leaves the drawing: the whole tree is even again, with the choice still marked.
            app.query_one("#editor").focus()
            await pilot.pause()
            assert not app._dimmed and tone not in " ".join(str(span.style) for span in app.render_trees().spans)
            assert app.selected_claim == ref_of(app, chosen)
    asyncio.run(run())
    assert consultant.calls == []


def test_answer_about_this_puts_the_statements_words_in_the_answer_and_sends_nothing(tmp_path):
    """Pointing, kept in the words: "that one is not a root cause" says which one. The quote is ordinary text
    to change before sending; the answer still answers the current question and nothing is sent."""
    path = imported_trees(tmp_path)
    consultant = ScriptedConsultant()
    statement = "Throughput is not yet operationally defined and accepted"

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            target = dict(app.workspace_value["target"])
            editor = app.query_one("#editor")
            editor.load_text("half an answer")
            app.show_tree("current_reality")
            app.query_one("#canvas").focus()
            await pilot.pause()
            while app.selected_claim != ref_of(app, statement):
                await pilot.press("down")
            await pilot.pause()
            assert "a About" in screen_text(app)
            await pilot.press("a")
            await pilot.pause()
            assert editor.text == ("half an answer\n\nAbout “Throughput is not yet operationally defined and accepted” "
                                   "(root cause, Current Reality Tree): ")
            assert app.focused is editor and app.view_name == "trees"
            decision = app.workspace_value["question"]["data"]["decision"]
            assert str(app.query_one("#response").border_title) == f"Answer as David · {decision}"  # same question
            # In the answer box every key is literal again, "a" included.
            await pilot.press("a")
            assert editor.text.endswith("Tree): a")
            assert "answer-about-the-chosen-statement" in [key for key, *_ in app.action_list()]
            assert app.workspace_value["target"] == target
    asyncio.run(run())
    assert consultant.calls == []
    with open_case(path, writable=False) as case:
        assert case.inspect()["case"]["revision"] == 1


def test_a_change_too_big_to_read_at_a_glance_is_summed_up_under_the_question(tmp_path):
    from importlib.resources import files
    path = tmp_path / "case"
    create_case(path, "Trees").close()

    async def run():
        app = launch(path, {"guided": ScriptedConsultant()})
        async with app.run_test(size=(120, 40)) as pilot:
            app.action_import_trees()
            await pilot.pause()
            app.screen.query_one("#destination").value = str(files("reason_commons.adapters").joinpath(
                "sample-trees.ltp.yaml"))
            await pilot.press("enter")
            await pilot.pause()
            app.show_view("next")
            await pilot.pause()
            assert "proposals from the last reply wait for you" in as_read(app.render_context())
            app.accept_reply()
            await pilot.pause()
            assert "68 statements added · 61 links, in 6 trees. Ctrl+T shows them." in app.query_one("#content").source
            assert "PROPOSED FROM" not in as_read(app.render_context())
    asyncio.run(run())


def backlog_case(tmp_path):
    """A goal in the model, then replies proposing a Transition Tree action, a cause with its link to an
    accepted symptom, and a new version of the goal (S138's backlog)."""
    from tests.test_trees import claim, link, with_updates
    path = tmp_path / "case"
    create_case(path, "Open evenings").close()
    goal = {"operation": "record_goal", "temporary_id": "goal", "source_refs": ["x"],
            "data": {"statement": "A clear next step after open evenings", "protections": []}}
    consultant = ScriptedConsultant([
        with_updates(goal, claim("temp_ude", "Newcomers do not know the next step")),
        with_updates(claim("temp_act", "Offer one clear invitation", tree="transition", role="transition_action")),
        with_updates(claim("temp_cause", "We never offer a next step", role="root_cause"),
                     link("temp_link", "temp_cause", "C1@1")),
        with_updates({**goal, "data": {**goal["data"], "statement": "Most newcomers reach a first practice",
                                       "replaces": "G1@1"}}),
    ])
    return path, consultant


def test_the_backlog_lists_proposals_in_decision_order_and_decides_them(tmp_path):
    from reason_commons.adapters.tui import ChoiceScreen
    path, consultant = backlog_case(tmp_path)

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(140, 40)) as pilot:
            await send(app, pilot, "The goal is a clear next step; newcomers do not know it")
            # Before anything is accepted the band says the goal is only proposed.
            assert "proposed, not yet accepted: A clear next step" in as_read(app.band())
            app.accept_reply()
            await pilot.pause()
            for words in ("Offer an invitation", "Because we never offer one", "Aim higher"):
                await send(app, pilot, words)
            app.show_view("backlog")
            await pilot.pause()
            listing = app.query_one("#backlog-list")
            rows = [str(o.prompt) for o in listing.options]
            assert [r.split(".")[0].strip() for r in rows] == ["1", "2", "3", "4"]
            assert "Decide first" in rows[0] and "Most newcomers reach a first practice" in rows[0]
            assert "We never offer a next step" in rows[1] and "waits for 2" in rows[2]
            assert "Offer one clear invitation" in rows[3]
            assert "Decide it first" in app.query_one("#content").source and "Backlog · 4" in screen_text(app)
            listing.focus()
            await pilot.pause()
            assert "a Accept" in screen_text(app) and "r Reject" in screen_text(app)
            # Beside the list on a wide terminal: the chosen entry in full.
            assert "Most newcomers reach a first practice" in str(app.query_one("#inspector-text").render())
            # Accepting the link takes the cause it needs; that is shown first, and nothing changes until confirmed.
            listing.highlighted = 2
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, ChoiceScreen) and "Accept 2 together?" in screen_text(app)
            assert "We never offer a next step" in screen_text(app)
            await pilot.press("enter")  # Confirm
            await pilot.pause()
            crt = next(t for t in app.workspace_value["trees"] if t["tree"] == "current_reality")
            assert [l["ref"] for l in crt["links"]] == ["L1@1"]
            # A single ready proposal needs no confirmation; a rejection is final.
            listing.highlighted = [str(o.prompt) for o in listing.options].index(
                next(str(o.prompt) for o in listing.options if "Offer one clear invitation" in str(o.prompt)))
            await pilot.press("r")
            await pilot.pause()
            assert not isinstance(app.screen, ChoiceScreen)
            assert [e["ref"] for e in app.backlog()] == ["G1@2"]
            # Enter offers the choices for the chosen entry.
            listing.highlighted = 0
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, ChoiceScreen) and "Accept · admits it to your model" in screen_text(app)
            await pilot.press("escape")
            await pilot.pause()
            assert [e["ref"] for e in app.backlog()] == ["G1@2"]
    asyncio.run(run())
    assert len(consultant.calls) == 4  # deciding asked the consultant nothing


def test_undo_from_history_shows_what_goes_and_is_final(tmp_path):
    from reason_commons.adapters.tui import ChoiceScreen
    path, consultant = backlog_case(tmp_path)

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            await send(app, pilot, "The goal is a clear next step; newcomers do not know it")
            app.accept_reply()
            await pilot.pause()
            app.show_view("history")
            await pilot.pause()
            timeline = app.query_one("#timeline")
            rows = [str(o.prompt) for o in timeline.options]
            assert "Accepted 2 proposals" in rows[-1] and "goal set" in rows[-1] and "1 statement added" in rows[-1]
            assert "2 proposed" in rows[-2]
            timeline.focus()
            timeline.highlighted = len(rows) - 1
            await pilot.pause()
            assert "u Undo this change" in screen_text(app)
            await pilot.press("u")
            await pilot.pause()
            assert isinstance(app.screen, ChoiceScreen) and "Undo? This is final." in screen_text(app)
            assert "Leaves your model" in screen_text(app)
            await pilot.press("enter")
            await pilot.pause()
            assert app.workspace_value["goals"] == [] and app.backlog() == []
            # The undo is a step too; there is nothing left in the model for u to undo.
            rows = [str(o.prompt) for o in app.query_one("#timeline").options]
            assert "Undid 2 changes" in rows[-1]
            timeline.highlighted = len(rows) - 2
            await pilot.press("u")
            await pilot.pause()
            assert not isinstance(app.screen, ChoiceScreen)
    asyncio.run(run())


def test_accepting_a_withdrawal_shows_the_links_that_leave_with_it(tmp_path):
    from reason_commons.adapters.tui import ChoiceScreen
    from tests.test_trees import claim, link, with_updates
    path = tmp_path / "case"
    create_case(path, "Open evenings").close()
    consultant = ScriptedConsultant([
        with_updates(claim("temp_ude", "Newcomers do not know the next step"),
                     claim("temp_cause", "We never offer a next step", role="root_cause"),
                     link("temp_link", "temp_cause", "temp_ude")),
        with_updates({"operation": "record_retraction", "temporary_id": "temp_x", "source_refs": ["x"],
                      "data": {"target_ref": "C2@1", "reason": "Not what we think now"}}),
    ])

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(140, 40)) as pilot:
            await send(app, pilot, "Newcomers do not know the next step, because we never offer one")
            app.accept_reply()
            await pilot.pause()
            await send(app, pilot, "Drop that cause")
            app.accept_reply()
            await pilot.pause()
            # The withdrawal takes the link with it: that is shown first, and nothing changes until confirmed.
            assert isinstance(app.screen, ChoiceScreen) and "Leaves your trees with it" in screen_text(app)
            assert "We never offer a next step" in screen_text(app)
            crt = next(t for t in app.workspace_value["trees"] if t["tree"] == "current_reality")
            assert [l["ref"] for l in crt["links"]] == ["L1@1"]
            await pilot.press("enter")  # Confirm
            await pilot.pause()
            crt = next(t for t in app.workspace_value["trees"] if t["tree"] == "current_reality")
            assert [c["ref"] for c in crt["claims"]] == ["C1@1"] and crt["links"] == []
    asyncio.run(run())


def test_expanded_display_repeats_the_complete_context_and_is_saved_with_the_draft(tmp_path):
    from tests.acceptance.steps.display_steps import PILOT
    from tests.acceptance.steps.question_steps import GOAL
    from tests.test_trees import with_updates
    path = tmp_path / "case"
    create_case(path, "Forge", acceptance="automatic", actor="Sam").close()
    consultant = ScriptedConsultant([with_updates(GOAL), with_updates(PILOT)])

    async def run(expand):
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            if expand:
                await send(app, pilot, "90% on time by October 30")
                await send(app, pilot, "Keep two urgent slots open")
                assert app.density == "compact" and "Horizon" not in as_read(app.band())
                calls = len(consultant.calls)
                app.set_density("expanded")
                await pilot.pause()
                app.checkpoint()
                assert len(consultant.calls) == calls
            shown = as_read(app.band())
            assert app.density == "expanded"
            assert "Horizon October 30" in shown and "Baseline 71% in September" in shown
            assert "Overtime at most 20 hours per week" in shown and "Keep two urgent slots open each day" in shown
    asyncio.run(run(True))
    asyncio.run(run(False))  # reopened: the preference came back with the draft


def test_commands_switch_how_proposals_are_accepted(tmp_path):
    path, consultant = backlog_case(tmp_path)

    async def run():
        app = launch(path, {"guided": consultant})
        async with app.run_test(size=(120, 40)) as pilot:
            commands = {key: run for key, _, _, run in app.action_list()}
            assert "accept-proposals-automatically" in commands and "hold-proposals-for-review" not in commands
            commands["accept-proposals-automatically"]()
            await pilot.pause()
            assert app.workspace_value["acceptance"] == "automatic"
            await send(app, pilot, "The goal is a clear next step; newcomers do not know it")
            # The reply's proposals entered the model with it, and Next step says so.
            assert app.backlog() == [] and app.workspace_value["goals"]
            assert "UNDER YOUR AUTOMATIC ACCEPTANCE" in as_read(app.render_context())
            commands = {key: run for key, _, _, run in app.action_list()}
            commands["hold-proposals-for-review"]()
            await pilot.pause()
            assert app.workspace_value["acceptance"] == "review"
    asyncio.run(run())
    with open_case(path, writable=False) as case:
        decisions = case.inspect()["case"]["decisions"]
    assert [(d["action"], d.get("value"), d["actor"]) for d in decisions if d["action"] == "acceptance"] == [
        ("acceptance", "automatic", "David"), ("acceptance", "review", "David")]


# ----- what paid replies cost: the footer meter, the reply's notice, the cost screen and the soft budget ------
@pytest.fixture
def claude():
    from tests.servers import anthropic_server_instance
    yield from anthropic_server_instance()


def counted(tmp_path, now=None):
    from reason_commons.adapters.usage import UsageLog, UsageSession
    return UsageSession(UsageLog(tmp_path / "usage.jsonl", now), "workspace")


def earlier_reply(tmp_path, model="claude-haiku-5-5", times=1):
    """A reply some other run already paid for this month, in the same log."""
    from reason_commons.adapters.usage import UsageLog, UsageSession
    other = UsageSession(UsageLog(tmp_path / "usage.jsonl"), "cli")
    for _ in range(times):
        other.record({"model": model, "outcome": "proposal", "tokens": {"input": 12_000, "output": 900}})


def paid_workspace(path, server, usage, settings=None):
    from reason_commons.adapters.anthropic import AnthropicConsultant
    consultant = AnthropicConsultant(base_url=server.url, api_key="fixture-secret", usage=usage.record)
    return ReasonCommonsApp(path, "David", "anthropic", lambda c: open_case(path, consultant=c),
                            lambda provider: consultant if provider == "anthropic" else GuidedConsultant(),
                            usage=usage, settings=settings)


def noted(app):
    """Every notice the workspace shows, as text."""
    notes, original = [], app.notify

    def notify(message, *args, **options):
        notes.append(str(message))
        return original(message, *args, **options)
    app.notify = notify
    return notes


def meter(app):
    return str(app.query_one("#summary").render())


def posts(server):
    return [path for method, path, _, _ in server.requests if method == "POST" and path == "/v1/messages"]


def test_the_footer_says_what_claude_costs_where_there_is_room(tmp_path, claude):
    path = tmp_path / "case"
    create_case(path, "Paid").close()
    usage = counted(tmp_path)

    async def run(size):
        app = paid_workspace(path, claude, usage)
        async with app.run_test(size=size) as pilot:
            await footer_settled(app, pilot)
            before = meter(app)
            await send(app, pilot, "Fewer missed deliveries")
            await footer_settled(app, pilot)
            hints = footer_fits(app)
            return before, meter(app), hints
    before, after, hints = asyncio.run(run((120, 40)))
    assert before == "Haiku 5.5 · month ≈ $0"
    assert after == "Haiku 5.5 · session ≈ $0.0017 · month ≈ $0.0017"
    assert "^p Commands" in hints and hints[-1] == "f1 Help"
    for size in ((80, 24), (40, 24)):  # the meter goes before any hint does
        _, narrow, hints = asyncio.run(run(size))
        assert narrow == "" and "^p Commands" in hints and hints[-1] == "f1 Help"


def test_the_guide_shows_no_meter_until_something_was_spent_and_then_says_it_is_free(tmp_path, monkeypatch):
    path = tmp_path / "case"
    create_case(path, "Free").close()
    monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", "5")

    async def run():
        app = ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                               lambda provider: GuidedConsultant(), usage=counted(tmp_path))
        async with app.run_test(size=(140, 40)) as pilot:
            await footer_settled(app, pilot)
            quiet = meter(app)
            earlier_reply(tmp_path)
            app.refresh_meter()
            await footer_settled(app, pilot)
            return quiet, meter(app)
    assert asyncio.run(run()) == ("", "offline guide · no charge · month ≈ $0.0017 of $5")


def test_a_replys_notice_says_what_it_cost_and_the_budget_is_told_at_80_and_100_percent(tmp_path, claude,
                                                                                        monkeypatch):
    path = tmp_path / "case"
    create_case(path, "Paid").close()
    earlier_reply(tmp_path)  # $0.00165 of a $0.004 budget
    monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", "0.004")

    async def run():
        app = paid_workspace(path, claude, counted(tmp_path))
        notes = noted(app)
        async with app.run_test(size=(120, 40)) as pilot:
            await send(app, pilot, "Fewer missed deliveries")
            first = list(notes)
            await send(app, pilot, "Measured weekly")
            return first, notes[len(first):]
    first, second = asyncio.run(run())
    assert any(note.endswith("Reply ≈ $0.0017 (Haiku 5.5).") for note in first)
    assert any("80% of your $0.004 budget (estimate)" in note and "Nothing is blocked" in note for note in first)
    assert any("past your $0.004 budget" in note and "Each send will ask first; nothing is blocked." in note
               for note in second)


def test_past_the_budget_a_send_asks_once_and_not_now_changes_nothing(tmp_path, claude, monkeypatch):
    path = tmp_path / "case"
    create_case(path, "Paid").close()
    earlier_reply(tmp_path)
    monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", "0.001")

    async def run():
        app = paid_workspace(path, claude, counted(tmp_path))
        notes = noted(app)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert any("past your $0.001 budget" in note for note in notes)  # said once on opening
            app.query_one("#editor").load_text("Keep these words")
            await pilot.press("ctrl+s")
            await pilot.pause()
            assert type(app.screen).__name__ == "ChoiceScreen"
            body = screen_text(app)
            assert "This month ≈ $0.0017 of your $0.001 budget (estimate)." in body
            assert "This reply ≈ $0.0042." in body  # a typical Haiku reply, until the log has three of its own
            await pilot.press("down", "enter")  # Not now
            await pilot.pause()
            assert type(app.screen).__name__ == "Screen"
            assert app.query_one("#editor").text == "Keep these words" and not app.busy
            assert app.workspace_value["revision"] == 0 and app.workspace_value["pending_requests"] == []
            assert posts(claude) == []
            await pilot.press("ctrl+s")
            await pilot.pause()
            await pilot.press("enter")  # Send this one
            await app.workers.wait_for_complete()
            await pilot.pause()
            return app.workspace_value["revision"], notes
    revision, notes = asyncio.run(run())
    assert revision == 1 and len(posts(claude)) == 1
    assert any("Nothing was sent. Your answer is still in the box." in note for note in notes)
    with open_case(path, writable=False) as case:
        assert case.workspace()["draft"] is None or case.workspace()["draft"]["draft"] == ""


def test_the_guide_never_asks_about_the_budget_and_retry_does(tmp_path, claude, monkeypatch):
    path = tmp_path / "case"
    create_case(path, "Mixed").close()
    earlier_reply(tmp_path)
    monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", "0.001")

    async def run():
        app = paid_workspace(path, claude, counted(tmp_path))
        async with app.run_test(size=(120, 40)) as pilot:
            claude.get_status = 500  # the model check fails: the answer is kept for Retry
            app.query_one("#editor").load_text("Kept for retry")
            await pilot.press("ctrl+s")
            await pilot.pause()
            await pilot.press("enter")  # Send this one
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.retryable()
            claude.get_status = 200
            app.action_retry()
            await pilot.pause()
            asked = type(app.screen).__name__
            await pilot.press("escape")  # Esc is Not now too
            await pilot.pause()
            assert app.retryable() and posts(claude) == []
            app.switch_provider("guided")
            app.action_retry()
            await app.workers.wait_for_complete()
            await pilot.pause()
            return asked, type(app.screen).__name__, app.workspace_value["revision"]
    assert asyncio.run(run()) == ("ChoiceScreen", "Screen", 1)


def test_retry_asks_again_only_when_no_received_reply_waits_to_be_applied():
    from types import SimpleNamespace
    def asks(*attempts):
        case = SimpleNamespace(receipts=lambda request_id: {"attempts": list(attempts)})
        return ReasonCommonsApp.retry_asks_again(SimpleNamespace(case=case), "in000001")
    started = {"attempt": 1, "status": "started"}
    received = {"attempt": 1, "proposal": {}, "version": "v"}
    assert asks(started, {"attempt": 1, "status": "unavailable"})
    assert not asks(started, received, {"attempt": 1, "status": "not_saved"})  # applied again, no new call
    assert asks(started, received, {"attempt": 1, "status": "rejected"})
    assert asks()


def test_consultant_calls_and_cost_says_it_in_words_from_the_log(tmp_path, claude, monkeypatch):
    path = tmp_path / "case"
    create_case(path, "Paid").close()
    earlier_reply(tmp_path, "claude-sonnet-5-5")
    monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", "5")

    async def run():
        app = paid_workspace(path, claude, counted(tmp_path))
        async with app.run_test(size=(120, 50)) as pilot:
            await send(app, pilot, "Fewer missed deliveries")
            app.open_menu("actions")
            await pilot.pause()
            await pilot.press(*"Consultant calls", "enter")
            await pilot.pause()
            return type(app.screen).__name__, screen_text(app)
    name, text = asyncio.run(run())
    assert name == "CallsScreen" and "Consultant calls and cost" in text
    assert "Consultant calls in this goal: 1" in text
    words = " ".join(text.split())
    for wanted in ("This goal Claude: 1 reply, ≈ $0.0017", "Last reply Haiku 5.5 · 12,000 tokens in, 900 out · ≈ $0.0017",
                   "This session 1 reply, ≈ $0.0017", "This month 2 replies, ≈ $0.03",
                   "of your $5 budget (0%)", "Sonnet 5.5: 1 reply, ≈ $0.03", "Haiku 5.5: 1 reply",
                   "Claude now Haiku 5.5, the default", "LM Studio and the built-in guide",
                   "Estimates at Anthropic's list prices of 8 Oct 2026", "Anthropic Console",
                   "readable only by you"):
        assert wanted in words, wanted
    assert "claude-haiku" not in words and not re.search(r"\d{4}-\d\d-\d\dT", words)


def test_the_cost_screen_names_a_saved_sonnet_choice_and_the_new_default(tmp_path, claude, monkeypatch):
    from reason_commons.adapters.anthropic import AnthropicConsultant
    from reason_commons.adapters.settings import Settings
    path = tmp_path / "case"
    create_case(path, "Saved").close()
    claude.metadata = {"id": "claude-sonnet-5-5"}
    monkeypatch.setenv("REASON_COMMONS_ANTHROPIC_MODEL", "claude-sonnet-5-5")
    settings = Settings(tmp_path / "settings.yaml", {"anthropic": {"model": "claude-sonnet-5-5"}}, exists=True)
    usage = counted(tmp_path)
    consultant = AnthropicConsultant.from_env(base_url=claude.url, usage=usage.record)

    async def run():
        app = ReasonCommonsApp(path, "David", "anthropic", lambda c: open_case(path, consultant=c),
                               lambda provider: consultant, usage=usage, settings=settings)
        async with app.run_test(size=(120, 50)) as pilot:
            app.action_consultant_calls()
            await pilot.pause()
            return " ".join(screen_text(app).split())
    words = asyncio.run(run())
    assert "Claude now Sonnet 5.5, your saved choice" in words
    assert "Haiku 5.5 is now the default and costs least. Your saved choice, Sonnet 5.5, stays" in words


def test_without_a_usage_log_the_screen_is_the_count_alone_and_the_guide_says_no_charge(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Plain").close()

    async def run(usage):
        app = ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                               lambda provider: GuidedConsultant(), usage=usage)
        async with app.run_test(size=(120, 50)) as pilot:
            app.action_consultant_calls()
            await pilot.pause()
            return " ".join(screen_text(app).split())
    plain = asyncio.run(run(None))
    assert "Consultant calls in this goal: 0" in plain and "CLAUDE REPLIES" not in plain
    words = asyncio.run(run(counted(tmp_path)))
    assert "Consultant now the built-in guide: no charge" in words and "Consultant calls in this goal: 0" in words


def test_the_budget_row_sets_and_clears_the_monthly_budget_and_keeps_it(tmp_path, monkeypatch):
    from reason_commons.adapters.settings import Settings
    monkeypatch.setenv("REASON_COMMONS_MONTHLY_BUDGET_USD", "")  # set first, so teardown puts back what is written
    monkeypatch.delenv("REASON_COMMONS_MONTHLY_BUDGET_USD")
    path = tmp_path / "case"
    create_case(path, "Budget").close()
    settings = Settings(tmp_path / "settings.yaml", {"name": "David"}, exists=True)
    settings.save()
    earlier_reply(tmp_path)

    async def run():
        app = ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                               lambda provider: GuidedConsultant(), usage=counted(tmp_path), settings=settings)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("f2")
            await pilot.pause()
            rows = app.screen.query_one("#settings-rows")
            ids = [option.id for option in rows.options]
            assert "none set" in str(rows.get_option("budget").prompt)
            await pilot.press("down", "down", "enter")
            await pilot.pause()
            await type_into(app, pilot, "$5.50")
            row = str(app.screen.query_one("#settings-rows").get_option("budget").prompt)
            saved = os.environ["REASON_COMMONS_MONTHLY_BUDGET_USD"], Settings.load(settings.path).get(
                "usage", "monthly_budget_usd")
            await pilot.press("enter")
            await pilot.pause()
            await type_into(app, pilot, "lots")  # not an amount: nothing changes
            unreadable = os.environ["REASON_COMMONS_MONTHLY_BUDGET_USD"]
            await pilot.press("enter")
            await pilot.pause()
            await type_into(app, pilot, "none")
            cleared = str(app.screen.query_one("#settings-rows").get_option("budget").prompt)
            return ids, row, saved, unreadable, cleared, Settings.load(settings.path).get("usage", "monthly_budget_usd")
    ids, row, saved, unreadable, cleared, after = asyncio.run(run())
    assert ids == ["voice", "mode", "budget"]
    assert "$5.50 a month · ≈ $0.0017 so far" in row and saved == ("5.5", "5.5") and unreadable == "5.5"
    assert "none set" in cleared and after is None


async def type_into(app, pilot, text):
    await pilot.pause()
    app.screen.query_one("Input").value = text
    await pilot.press("enter")
    await pilot.pause()


def test_every_command_with_claude_still_says_local_or_asks_the_consultant(tmp_path, claude):
    """S119 with a paid consultant: the cost screen is local, and every other command names its consequence."""
    path = tmp_path / "case"
    create_case(path, "Paid").close()

    async def run():
        app = paid_workspace(path, claude, counted(tmp_path))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            return [(name, detail) for _, name, detail, _ in app.action_list()]
    commands = asyncio.run(run())
    assert ("Consultant calls and cost", "Local: how often the consultant was asked, and what Claude's replies "
            "cost, as estimated") in commands
    for name, detail in commands:
        assert detail.startswith("Local") or "asks the consultant" in detail.lower(), (name, detail)
