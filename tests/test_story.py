"""The example story: built through the application, packaged, and read in the workspace."""

import asyncio
from importlib.resources import files

import pytest
from rich.console import Console

pytest.importorskip("textual")

from reason_commons.adapters.guided import GuidedConsultant  # noqa: E402
from reason_commons.adapters.story import build_story, load_story  # noqa: E402
from reason_commons.adapters.timeline import change_summary, next_action, revision_changes  # noqa: E402
from reason_commons.adapters.tui import (STORY_ARCHIVE, STORY_HOME, STORY_OWN_GOAL,  # noqa: E402
                                         ReasonCommonsApp)
from reason_commons.bootstrap import create_case, import_case, open_case  # noqa: E402
from tests.support import ScriptedConsultant  # noqa: E402


@pytest.fixture(scope="module")
def story_case(tmp_path_factory):
    path = tmp_path_factory.mktemp("story") / "case"
    import_case(str(files("reason_commons.adapters").joinpath(STORY_ARCHIVE)), str(path)).close()
    return path


def comparable(case):
    """What a reader sees, without identifiers that differ between builds."""
    history = case.history()["revisions"]
    sources = case.sources()["sources"]
    return [(snapshot["timestamp"], [(r["kind"], r["data"]) for r in snapshot["records"]],
             [(sources[q]["speaker"], sources[q]["text"]) for q in snapshot["applied_requests"]])
            for snapshot in history]


def test_story_file_builds_one_revision_per_chapter_and_matches_the_package(tmp_path, story_case):
    story = load_story()
    built = build_story(tmp_path / "fresh", story)
    with open_case(built, writable=False) as fresh, open_case(story_case, writable=False) as packaged:
        assert fresh.workspace()["revision"] == len(story["chapters"])
        # The packaged archive is the story file, built: rerun scripts/build_story.py after editing it.
        assert comparable(fresh) == comparable(packaged)


def test_each_revision_carries_its_date_speaker_and_literal_words(story_case):
    story = load_story()
    with open_case(story_case, writable=False) as case:
        entries = revision_changes(case.history()["revisions"], case.sources()["sources"])
    assert len(entries) == len(story["chapters"]) + 1
    for entry, chapter in zip(entries[1:], story["chapters"]):
        assert entry["timestamp"] == chapter["date"]
        assert entry["speaker"] == chapter["speaker"]
        assert entry["text"] == chapter["words"]
        assert entry["decision"] == chapter["title"]
    speakers = {e["speaker"] for e in entries[1:]}
    assert {"David Joseph", "Robert Bunge", "Rufus Pollock", "curious_reader"} <= speakers


def test_the_story_rewords_withdraws_and_ends_with_one_open_action(story_case):
    with open_case(story_case, writable=False) as case:
        records = case.inspect()["case"]["records"]
        trees = {t["tree"]: t for t in case.workspace(view="trees")["trees"]}
    kinds = [r["kind"] for r in records]
    assert kinds.count("retraction") >= 7
    assert any(r["kind"] == "claim" and r["data"].get("replaces") for r in records)
    upcoming = next_action(records)
    assert upcoming and "stewarded review" in upcoming["action"]["data"]["statement"]
    assert upcoming["claim"]["data"]["role"] == "transition_action"
    # The founding move survives the July reconstruction under its new wording.
    first = next(c for c in trees["prerequisite"]["claims"] if c["statement"].startswith("A stewarded, versioned"))
    assert "Decide how the trees get updated" in first["earlier_wording"]
    # Robert's objection is still on record even though its condition was condensed away.
    assert any("create the pull but to align with it" in c["statement"] for c in trees["goal"]["claims"])


def test_change_summary_counts_in_plain_words():
    assert change_summary({"claim": 2, "link": 1, "withdrawn": 1}) == "2 statements added · 1 withdrawn · 1 link"
    assert change_summary({}) == "no recorded change"


def story_app(path):
    return ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                            lambda provider: GuidedConsultant(), story=load_story())


def test_story_opens_read_only_on_the_next_action_and_steps_through_history(story_case):
    async def run():
        app = story_app(story_case)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert app.query_one("#response").has_class("hidden")
            assert "The next action" in app.query_one("#content").source
            band = Console(width=120, record=True)
            band.print(app.band())
            assert "stewarded review" in band.export_text()
            await pilot.press("ctrl+s")  # nothing to send in a story
            await pilot.pause()
            await pilot.press("left")
            await pilot.pause()
            assert app.revision == len(load_story()["chapters"]) - 1
            app.go_to(6)
            await pilot.pause()
            content = app.query_one("#content").source
            assert "First, decide how the trees get updated" in content and "What changed" in content
            assert "Step 6 of" in str(app.query_one("#moment-text").render())
            app.show_tree("prerequisite")
            await pilot.pause()
            assert "NEW" in str(app.query_one("#canvas").render())
            app.show_view("history")
            await pilot.pause()
            timeline = app.query_one("#timeline")
            assert len(timeline.options) == len(load_story()["chapters"]) + 1
            timeline.focus()
            timeline.highlighted = 1
            await pilot.press("enter")
            await pilot.pause()
            assert app.revision == 1 and app.view_name == "next"
            app.query_one("#now").press()
            await pilot.pause()
            assert app.revision is None
            app.query_one("#own").press()
            await pilot.pause()
        return app.return_value
    assert asyncio.run(run()) == STORY_OWN_GOAL
    with open_case(story_case, writable=False) as case:
        assert case.workspace()["revision"] == len(load_story()["chapters"])  # nothing was added


def test_back_to_start_leaves_the_story(story_case):
    async def run():
        app = story_app(story_case)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            app.query_one("#home").press()
            await pilot.pause()
        return app.return_value
    assert asyncio.run(run()) == STORY_HOME


def test_any_goal_can_be_looked_back_on_without_changing_it(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Running").close()
    consultant = ScriptedConsultant()

    async def run():
        app = ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                               lambda provider: {"guided": GuidedConsultant()}.get(provider, consultant))
        async with app.run_test(size=(120, 40)) as pilot:
            for answer in ("Run 5k", "Weekly km"):
                app.query_one("#editor").load_text(answer)
                await pilot.press("ctrl+s")
                await app.workers.wait_for_complete()
                await pilot.pause()
            app.query_one("#editor").load_text("draft stays")
            app.show_view("history")
            await pilot.pause()
            assert len(app.query_one("#timeline").options) == 3
            app.view_name = "next"
            app.go_to(1)
            await pilot.pause()
            assert app.query_one("#response").has_class("hidden")
            assert "Run 5k" in app.query_one("#content").source
            assert app.query_one("#own").has_class("hidden")
            await pilot.press("ctrl+s")
            await pilot.pause()
            app.query_one("#now").press()
            await pilot.pause()
            assert app.revision is None and not app.query_one("#response").has_class("hidden")
            assert app.query_one("#editor").text == "draft stays"
            return app.workspace_value["revision"]
    assert asyncio.run(run()) == 2
