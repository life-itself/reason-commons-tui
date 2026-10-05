"""Themes: the web app's twelve voices as Textual themes, chosen by flag, environment, settings or picker."""

import argparse
import asyncio

import pytest

pytest.importorskip("textual")

from reason_commons.adapters import themes  # noqa: E402
from reason_commons.adapters.cli import theme_choice  # noqa: E402
from reason_commons.adapters.guided import GuidedConsultant  # noqa: E402
from reason_commons.adapters.settings import Settings  # noqa: E402
from reason_commons.adapters.tui import GoalsApp, ThemeScreen, themed  # noqa: E402
from reason_commons.bootstrap import create_case  # noqa: E402
from tests.test_tui import launch  # noqa: E402


def contrast(one, other):
    def luminance(colour):
        channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    low, high = sorted((luminance(one), luminance(other)))
    return (high + 0.05) / (low + 0.05)


def test_every_voice_comes_light_and_dark_with_readable_distinct_families():
    assert len(themes.VOICES) == 12 and len(themes.THEMES) == 24
    for voice, (frame, *palettes) in themes.PALETTES.items():
        assert frame in ("round", "solid")
        for mode, palette in zip(themes.MODES, palettes):
            theme = themes.THEMES[themes.theme_name(voice, mode)]
            assert theme.dark == (mode == "dark")
            for text in (palette.ink, palette.muted, palette.hand, palette.proposed, palette.stood_behind,
                         palette.disagreed):
                assert contrast(text, palette.ground) >= 4.5, (voice, mode, text)
            # The hand may alias a proposal (a proposal is a person's offer), but nothing else may share a colour.
            assert len({palette.hand, palette.stood_behind, palette.disagreed}) == 3, (voice, mode)
            assert len({palette.proposed, palette.stood_behind, palette.disagreed}) == 3, (voice, mode)
            assert theme.variables["frame"] == frame and theme.error == palette.disagreed


def test_a_theme_can_be_named_the_way_a_person_would_type_it():
    assert themes.resolve("tanizaki") == "tanizaki"
    assert themes.resolve("Shadows") == "tanizaki"
    assert themes.resolve("shadows dark") == themes.resolve("Tanizaki-Dark") == "tanizaki-dark"
    assert themes.resolve("Five Phases") == "wuxing"
    assert themes.resolve("optics_dark") == "al-haytham-dark"
    assert themes.resolve("commons-light") == "commons"
    assert themes.resolve("critical-edition") == "schopenhauer"
    for nothing in (None, "", "dark", "textual-dark", "solarized"):
        assert themes.resolve(nothing) is None
    assert theme_choice("Grammar dark") == "wittgenstein-dark"
    with pytest.raises(argparse.ArgumentTypeError):
        theme_choice("solarized")
    assert themes.title("tanizaki-dark") == "Shadows · Jun'ichirō Tanizaki, dark"


def test_settings_fill_in_the_theme_unless_the_environment_already_chose(tmp_path, monkeypatch):
    settings = Settings(tmp_path / "settings.yaml", {"theme": "goethe"}, exists=True)
    environ = {}
    settings.apply(environ)
    assert environ[themes.ENVIRONMENT] == "goethe"
    environ = {themes.ENVIRONMENT: "khipu-dark"}
    settings.apply(environ)
    assert environ[themes.ENVIRONMENT] == "khipu-dark"


def test_workspace_opens_in_the_chosen_theme_and_offers_only_ours(tmp_path, monkeypatch):
    path = tmp_path / "case"
    create_case(path, "Colours").close()
    monkeypatch.setenv(themes.ENVIRONMENT, "Illumination")

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            assert app.theme == "suhrawardi"
            assert set(app.available_themes) == set(themes.THEMES)
            assert app.theme_variables["disagreed"] == themes.PALETTES["suhrawardi"][1].disagreed
    asyncio.run(run())


def test_an_unknown_theme_falls_back_with_a_warning(tmp_path, monkeypatch):
    path = tmp_path / "case"
    create_case(path, "Colours").close()
    monkeypatch.setenv(themes.ENVIRONMENT, "solarized")

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            assert app.theme == themes.DEFAULT_THEME
            assert any("solarized" in n.message for n in app._notifications)
    asyncio.run(run())


def test_picker_previews_as_you_move_and_escape_puts_the_old_theme_back(tmp_path, monkeypatch):
    path = tmp_path / "case"
    create_case(path, "Colours").close()
    monkeypatch.setenv(themes.ENVIRONMENT, "commons-dark")

    async def run():
        app = launch(path, {"guided": GuidedConsultant()})
        async with app.run_test(size=(100, 30)) as pilot:
            app.action_change_theme()
            await pilot.pause()
            assert isinstance(app.screen, ThemeScreen)
            await pilot.press("down")
            assert app.theme == "organic-dark"
            await pilot.press("left")
            assert app.theme == "organic"
            await pilot.press("escape")
            await pilot.pause()
            assert app.theme == "commons-dark" and not isinstance(app.screen, ThemeScreen)
    asyncio.run(run())


def test_choosing_a_theme_on_the_home_screen_saves_it(tmp_path, monkeypatch):
    monkeypatch.delenv(themes.ENVIRONMENT, raising=False)
    settings = Settings(tmp_path / "settings.yaml", {"name": "Dana", "consultant": "guided"})
    settings.save()

    async def run():
        app = GoalsApp(tmp_path / "goals", list_goals=lambda root: [], settings=settings)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            options = app.query_one("#goals")
            options.highlighted = options.get_option_index("theme")
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, ThemeScreen)
            for key in ("end", "right", "enter"):
                await pilot.press(key)
            await pilot.pause()
            assert app.theme == "khipu-dark"
            assert "Channels" in str(options.get_option("theme").prompt)
    asyncio.run(run())
    saved = Settings.load(tmp_path / "settings.yaml")
    assert saved.get("theme") == "khipu-dark" and saved.get("name") == "Dana"


def test_before_first_start_finishes_a_chosen_theme_waits_for_setup_to_save_it(tmp_path, monkeypatch):
    monkeypatch.delenv(themes.ENVIRONMENT, raising=False)
    settings = Settings.load(tmp_path / "settings.yaml")

    async def run():
        app = GoalsApp(tmp_path / "goals", list_goals=lambda root: [], settings=settings)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.keep_theme("goethe")
    asyncio.run(run())
    assert settings.get("theme") == "goethe" and not settings.exists
    assert not (tmp_path / "settings.yaml").exists()


def test_trees_are_drawn_in_the_theme_colours():
    variables = {"disagreed": "#9c3f28", "hand": "#1c5238"}
    assert themed("dim bold $disagreed", variables) == "bold #9c3f28"
    assert themed("bold $hand", variables) == "bold #1c5238"
    assert themed("italic dim", variables) == "italic dim"
    assert themed("", variables) == ""


def test_theme_flag_reaches_the_workspace(monkeypatch):
    from reason_commons.adapters import cli, tui
    monkeypatch.delenv(themes.ENVIRONMENT, raising=False)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    opened = []
    monkeypatch.setattr(tui, "run_home", lambda **options: opened.append(cli.os.environ[themes.ENVIRONMENT]))
    cli.main(["--theme", "Shadows"])
    assert opened == ["tanizaki"]
