"""Render the actual imported working state, without model calls or participant data."""
import asyncio
import os
from pathlib import Path
import sys
import tempfile
import time
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from render_screenshots import shoot, to_png, OUT, SHOTS, chromium, write_manifest  # noqa: E402
from reason_commons.adapters import themes, timeline
from reason_commons.adapters.commons import build_commons  # noqa: E402
from reason_commons.adapters.settings import Settings  # noqa: E402
from reason_commons.adapters.tui import GoalsApp, ReasonCommonsApp  # noqa: E402
from reason_commons.bootstrap import open_case, configured_consultant  # noqa: E402


async def render(folder):
    path = folder / 'reason-commons-development'
    with build_commons(path):
        pass
    def app():
        return ReasonCommonsApp(path, 'David', 'guided',
            lambda consultant: open_case(path, consultant=consultant),
            lambda provider: configured_consultant(provider=provider))
    await shoot(GoalsApp(folder, settings=Settings.load(folder / 'settings.yaml')), 'first-start', (100, 30))
    await shoot(GoalsApp(folder, settings=Settings(folder / 'saved.yaml', {'name': 'David', 'consultant': 'guided'}, exists=True)), 'home', (120, 30))
    await shoot(GoalsApp(folder, settings=Settings.load(folder / 'settings.yaml')), 'home-help', (100, 30), before=lambda app: app.action_help())
    await shoot(app(), 'commons-next', (120, 36))
    await shoot(app(), 'commons-next-80x24', (80, 24))
    await shoot(app(), 'commons-transition', (120, 36), before=lambda app: app.show_tree('transition'))
    await shoot(app(), 'commons-conflict', (120, 36), before=lambda app: app.show_tree('conflict'))
    await shoot(app(), 'commons-history', (120, 36), before=lambda app: app.show_view('history'))
    await shoot(app(), 'commons-built', (120, 36), before=lambda app: app.go_to(7))
    await shoot(app(), 'commons-commands-views', (100, 30), before=lambda app: app.action_command_palette())
    await shoot(app(), 'commons-current-reality', (120, 36), before=lambda app: app.show_tree('current_reality'))
    async def acceptance(app, pilot):
        rows = app.screen.query_one('#settings-rows')
        rows.highlighted = rows.get_option_index('acceptance')
    await shoot(app(), 'commons-settings', (100, 30), before=lambda app: app.action_settings(), steps=acceptance)
    review = folder / 'review-import'
    with build_commons(review, acceptance='review', adopted=False):
        pass
    pending = ReasonCommonsApp(review, 'David', 'guided',
        lambda consultant: open_case(review, consultant=consultant),
        lambda provider: configured_consultant(provider=provider))
    await shoot(pending, 'commons-review-import', (120, 36), before=lambda app: app.show_view('backlog'))

    async def adopt(app, pilot):
        app.adopt_import()
        await pilot.pause()
        from textual.widgets import OptionList
        if app.screen.query(OptionList):
            options = app.screen.query_one(OptionList)
            index = next((i for i, o in enumerate(options.options) if o.id == 'confirm'), None)
            if index is not None:
                options.highlighted = index
                await pilot.press('enter')
        await pilot.pause()
    adopted = ReasonCommonsApp(review, 'David', 'guided',
        lambda consultant: open_case(review, consultant=consultant),
        lambda provider: configured_consultant(provider=provider))
    await shoot(adopted, 'commons-adopted-review', (120, 36), steps=adopt)

    feedback_path = folder / 'feedback'
    with build_commons(feedback_path):
        pass
    def feedback_app():
        return ReasonCommonsApp(feedback_path, 'David', 'guided',
            lambda consultant: open_case(feedback_path, consultant=consultant),
            lambda provider: configured_consultant(provider=provider))
    async def contribute(app, pilot):
        app.query_one('#editor').load_text('Explore importing prior conversations without re-entering them by hand.')
        await pilot.press('ctrl+s')
        await app.workers.wait_for_complete()
    await shoot(feedback_app(), 'commons-contribution-receipt', (120, 36), steps=contribute)
    await shoot(feedback_app(), 'commons-contribution-receipt-80x24', (80, 24))

    # An explicitly authored offline fixture, not evidence of a live model's reasoning.
    from copy import deepcopy
    class FeedbackFixture:
        version = 'fixture/feedback'
        def propose(self, request):
            case, value = request['case'], request['input']
            intervention = deepcopy(next(r['data'] for r in case['records']
                                         if r['ref'] == case['current_intervention']))
            updates = []
            for identity, tree, role, statement in (
                ('burden', 'current_reality', 'undesirable_effect', 'Re-entering prior reasoning takes attention'),
                ('import', 'transition', 'transition_action', 'Try importing one plain-text conversation')):
                updates.append({'operation': 'record_claim', 'temporary_id': identity,
                                'data': {'tree': tree, 'role': role, 'statement': statement, 'basis': 'hypothesis'},
                                'source_refs': [value['request_id']]})
            return {'schema_version': '1', 'delivery_profile': 'p2', 'request_id': value['request_id'],
                    'base_revision': value['base_revision'], 'proposed_updates': updates,
                    'intervention': intervention}
    scripted = FeedbackFixture()
    changed = ReasonCommonsApp(feedback_path, 'David', 'fixture',
        lambda consultant: open_case(feedback_path, consultant=consultant), lambda _: scripted)
    await shoot(changed, 'commons-tree-update-markers', (120, 36), steps=contribute)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    os.environ['REASON_COMMONS_USAGE_LOG'] = 'off'
    os.environ[themes.ENVIRONMENT] = themes.DEFAULT_THEME
    os.environ['TZ'] = 'UTC'
    time.tzset()
    timeline.today = lambda: date(2026, 11, 10)
    with tempfile.TemporaryDirectory() as folder:
        os.environ["REASON_COMMONS_CONFIG"] = str(Path(folder) / "settings.yaml")
        asyncio.run(render(Path(folder)))
    browser = chromium()
    if browser:
        for name in sorted(SHOTS):
            svg = OUT / (name + '.svg')
            try:
                to_png(browser, svg)
            finally:
                svg.with_suffix('.html').unlink(missing_ok=True)
    write_manifest('scripts/render_commons.py', 'disposable RC-on-RC adopted and pending imports')
    print('Rendered imported working commons in docs/images')


if __name__ == '__main__':
    main()
