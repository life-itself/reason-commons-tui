"""Source-backed dogfood import, through the public application boundary."""
import base64

from reason_commons.adapters.commons import build_commons, continue_commons
from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.bootstrap import open_case


def test_reconstruction_preserves_sources_and_leaves_history_honest(tmp_path):
    with build_commons(tmp_path / "case") as app:
        case = app.inspect()["case"]
        records = case["records"]
        assert case["name"] == "Reason Commons · development"
        assert not any(r["kind"] in {"test", "action", "observation", "review"} for r in records)
        assert {r["data"]["tree"] for r in records if r["kind"] == "claim"} == {
            "goal", "current_reality", "conflict", "future_reality", "prerequisite", "transition"}
        assert any("already built" in r["data"].get("statement", "") for r in records)
        sources = app.sources()["sources"].values()
        human = next(s for s in sources if s.get('name') == 'Original conversation T2')
        assert base64.b64decode(human['content_base64']).decode('utf-8').startswith('my intention is to develop')
        assert {s['speaker'] for s in sources} >= {'Human expert (name not supplied)', 'AI questioner'}
        assert app.workspace()["question"]["data"]["purpose"] == "continuation"
        assert app.workspace()["backlog"] == []


def test_continuing_does_not_turn_an_issue_into_a_trial(tmp_path):
    with build_commons(tmp_path / "case") as app:
        pass
    with open_case(tmp_path / "case", consultant=GuidedConsultant()) as app:
        app.set_acceptance('review', 'David', app.inspect()['case']['revision'])
        target = app.workspace()["target"]
        result = app.submit("We need clearer attribution before making the next decision.", "David",
                            target["base_revision"], target["response_target"])
        assert result["status"] == "saved", result
        workspace = app.workspace()
        assert workspace["question"]["data"]["purpose"] == "continuation"
        assert not any(r["kind"] == "test" for r in app.inspect()["case"]["records"])
        assert any(r["kind"] == "note" and r["data"]["text"].startswith("We need clearer attribution")
                   for r in app.inspect()["case"]["records"])


def test_home_imports_once_and_resumes_without_overwriting(tmp_path):
    path = continue_commons(tmp_path)
    with open_case(path) as app:
        revision = app.inspect()["case"]["revision"]
    assert continue_commons(tmp_path) == path
    with open_case(path) as app:
        assert app.inspect()["case"]["revision"] == revision


def test_name_collision_is_preserved_and_import_round_trips(tmp_path):
    from reason_commons.bootstrap import create_case, import_case
    collision = tmp_path / 'goals' / 'reason-commons'
    collision.parent.mkdir()
    with create_case(collision, 'My unrelated case') as app:
        original = app.inspect()['case']
    path = continue_commons(collision.parent)
    assert path != collision
    with open_case(collision) as app:
        assert app.inspect()['case'] == original
    with open_case(path) as app:
        expected = app.inspect()['case']
        sources = app.sources()
        app.export(str(tmp_path / 'commons.reasoncase'))
    with import_case(tmp_path / 'commons.reasoncase', tmp_path / 'roundtrip') as app:
        assert app.inspect()['case'] == expected
        assert app.sources() == sources


def test_imported_workspace_keeps_the_question_primary_and_sources_readable(tmp_path):
    import asyncio
    from reason_commons.adapters.tui import GoalsApp, ReasonCommonsApp
    from tests.test_tui import screen_text
    from reason_commons.adapters.settings import Settings
    from reason_commons.bootstrap import configured_consultant

    async def walkthrough():
        home = GoalsApp(tmp_path / 'goals', settings=Settings.load(tmp_path / 'settings.yaml'))
        async with home.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert [o.id for o in home.query_one('#goals').options] == ['commons', 'start']
            await pilot.press('enter')
            await pilot.pause()
        path = home.return_value
        assert path == tmp_path / 'goals' / 'reason-commons-development'
        app = ReasonCommonsApp(path, 'David', 'guided', lambda c: open_case(path, consultant=c),
                               lambda p: configured_consultant(provider=p))
        async with app.run_test(size=(120, 36)) as pilot:
            await pilot.pause()
            assert not app.query_one('#loop-row').display
            assert [o.id for o in app.query_one('#views').options] == [
                'next', 'backlog', 'goal', 'trees', 'sources', 'history']
            assert 'Next: trace why manual RC led to this interface' in screen_text(app)
            assert {'tests', 'actions', 'reasoning', 'context'} <= {key for key, _ in app.menu_items('views')}
            app.show_view('history')
            await pilot.pause()
            entries = app.history()['entries']
            assert app.step_title(entries[7]) == 'Build the minimal interface'
            assert app.step_title(entries[10]) == 'Choose the first dogfood move'
            app.go_to(7)
            await pilot.pause()
            assert app.render_moment().startswith('## Build the minimal interface')
            app.go_to(None)
            app.show_view('sources')
            await pilot.pause()
            content = app.render_view()
            assert 'Original conversation T2' in content
            assert 'my intention is to develop a system' in content
            assert 'Human expert' in content and 'name not supplied' in content
            app.show_view('next')
            await pilot.resize_terminal(80, 24)
            await pilot.pause()
            assert 'Next: trace why manual RC led to this interface' in screen_text(app)
    asyncio.run(walkthrough())


def test_development_history_reconstructs_the_argument_before_the_import(tmp_path):
    with build_commons(tmp_path / 'case') as app:
        history = app.history()['revisions']
        stages = [next(r for r in reversed(s['records']) if r['kind'] == 'intervention')['data']['decision']
                  for s in history if s['applied_requests'] and len(s['applied_requests']) == s['revision']]
        assert len(stages) >= 9
        assert stages.index('Why TOC needs assistance') < stages.index('Build the minimal interface')
        assert stages.index('Build the minimal interface') < stages.index('Import and adopt prior reasoning')
        model = app.workspace()
        assert sum(len(t['claims']) for t in model['trees']) >= 55
        assert model['acceptance'] == 'automatic'
        assert not model['backlog']
        assert not any(status == 'rejected' for status in model['membership'].values())
        assert model['question']['data']['kind'] == 'recommendation'
        assert 'Which decision' not in model['question']['data']['primary_prompt']


def test_review_import_has_visible_proposals_until_adopted(tmp_path):
    with build_commons(tmp_path / 'case', acceptance='review', adopted=False) as app:
        workspace = app.workspace()
        assert not any(tree['claims'] for tree in workspace['trees'])
        refs = [e['ref'] for e in workspace['backlog'] if e['entry'] == 'proposal']
        assert len(refs) > 100
        result = app.accept(refs, 'David', app.inspect()['case']['revision'], confirmed=True)
        assert result['status'] == 'saved', result
        assert not app.workspace()['backlog']
        assert sum(len(t['claims']) for t in app.workspace()['trees']) >= 55


def test_acceptance_mode_is_available_in_workspace_settings(tmp_path):
    import asyncio
    from reason_commons.adapters.tui import ReasonCommonsApp
    from reason_commons.bootstrap import configured_consultant
    with build_commons(tmp_path / 'case'):
        pass
    async def run():
        app = ReasonCommonsApp(tmp_path / 'case', 'David', 'guided', lambda c: open_case(tmp_path / 'case', consultant=c),
                               lambda p: configured_consultant(provider=p))
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press('f2')
            await pilot.pause()
            rows = app.screen.query_one('#settings-rows')
            assert 'acceptance' in [o.id for o in rows.options]
            rows.highlighted = rows.get_option_index('acceptance')
            await pilot.press('right')
            await pilot.pause()
            assert app.case.workspace()['acceptance'] == 'review'
            await pilot.press('right')
            await pilot.pause()
            assert app.case.workspace()['acceptance'] == 'automatic'
    asyncio.run(run())


def test_review_import_can_be_adopted_from_the_workspace(tmp_path):
    import asyncio
    from reason_commons.adapters.tui import ReasonCommonsApp
    from reason_commons.bootstrap import configured_consultant
    with build_commons(tmp_path / 'case', acceptance='review', adopted=False):
        pass
    async def run():
        app = ReasonCommonsApp(tmp_path / 'case', 'David', 'guided',
                               lambda c: open_case(tmp_path / 'case', consultant=c),
                               lambda p: configured_consultant(provider=p))
        async with app.run_test(size=(120, 36)) as pilot:
            await pilot.pause()
            button = app.query_one('#accept-all')
            assert str(button.label) == 'Adopt import' and button.display
            assert len(app.import_waiting()) == 119
            await pilot.click('#accept-all')
            await pilot.pause()
            assert not app.case.workspace()['backlog']
            assert app.case.workspace()['question']['data']['primary_prompt'].startswith('Next: trace')
            assert not app.import_waiting()
            assert not button.display
            # A later proposal cites imported context, but is not part of the import.
            app.case.submit('The causal chain is hard to follow.', 'David', **app.case.workspace()['target'])
            app._history = None
            app.refresh_workspace()
            assert not app.import_waiting()
            assert len(app.case.workspace()['backlog']) == 1
    asyncio.run(run())
