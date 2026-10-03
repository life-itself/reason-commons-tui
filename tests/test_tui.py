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
