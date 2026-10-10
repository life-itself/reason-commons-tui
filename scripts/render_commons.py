"""Render the actual imported working state, without model calls or participant data."""
import asyncio
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from render_screenshots import shoot, to_png, OUT  # noqa: E402
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    os.environ['REASON_COMMONS_USAGE_LOG'] = 'off'
    with tempfile.TemporaryDirectory() as folder:
        asyncio.run(render(Path(folder)))
    browser = os.environ.get('CHROMIUM')
    if browser:
        for name in ['first-start', 'home', 'home-help', 'commons-next', 'commons-next-80x24',
                     'commons-transition', 'commons-conflict', 'commons-history', 'commons-built',
                     'commons-current-reality', 'commons-settings', 'commons-review-import']:
            svg = OUT / (name + '.svg')
            try:
                to_png(browser, svg)
            finally:
                svg.with_suffix('.html').unlink(missing_ok=True)
    print('Rendered imported working case in docs/images')


if __name__ == '__main__':
    main()
