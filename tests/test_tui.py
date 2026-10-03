"""Terminal workspace adapter: layout state and routing over the application boundary."""

import asyncio

import pytest

pytest.importorskip("textual")

from reason_commons.adapters.guided import GuidedConsultant  # noqa: E402
from reason_commons.adapters.tui import ReasonCommonsApp, caret_index, caret_location  # noqa: E402
from reason_commons.bootstrap import create_case, open_case  # noqa: E402
from tests.support import ScriptedConsultant  # noqa: E402


def launch(path, consultants):
    return ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                            lambda provider: consultants[provider])


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
            return str(app.query_one("#status").render())
    status = asyncio.run(run())
    assert "Saved" in status and "r0" not in status


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
    assert "✓ Goal" in line and "✓ Test + forecast" in line and "> Action" in line and "✓ Observe" not in line
    assert ">" not in loop_line(None).replace("→", "")


def test_welcome_draws_the_loop_and_the_strip_follows_progress(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Welcome").close()

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert "One small test" in app.render_next()
            assert "> Goal" in str(app.query_one("#loop").render())
            for answer in ("Sleep better", "", "", "Phone in the kitchen"):
                await send(app, pilot, answer)
            assert "> Test + forecast" in str(app.query_one("#loop").render())
            assert "One small test" not in app.render_next()
    asyncio.run(run())


def test_example_goal_is_a_finished_loop(tmp_path):
    from reason_commons.adapters.sample import ANSWERS, build_sample
    path = build_sample(tmp_path / "example")
    with open_case(path, writable=False) as app:
        workspace = app.workspace()
        kinds = {record["kind"] for record in app.inspect()["case"]["records"]}
        assert app.inspect()["cursor"]["view"] == "tests"
    assert workspace["revision"] == len(ANSWERS)
    assert {"goal", "test", "action", "observation"} <= kinds
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
