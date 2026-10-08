"""First start, personal settings and the guided tour, driven headlessly."""

import asyncio
import os
import stat

import pytest

pytest.importorskip("textual")

from reason_commons.adapters.guided import GuidedConsultant  # noqa: E402
from reason_commons.adapters.onboarding import EXAMPLE_ANSWERS, tour_state  # noqa: E402
from reason_commons.adapters.settings import Settings, model_hint  # noqa: E402
from reason_commons.adapters.tui import TOUR, TOUR_FINISHED, GoalsApp, ReasonCommonsApp  # noqa: E402
from reason_commons.bootstrap import create_case, open_case  # noqa: E402

VARIABLES = ["REASON_COMMONS_SPEAKER", "REASON_COMMONS_PROVIDER", "REASON_COMMONS_ANTHROPIC_MODEL",
             "ANTHROPIC_API_KEY", "REASON_COMMONS_LM_STUDIO_URL", "REASON_COMMONS_LM_STUDIO_MODEL"]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for variable in VARIABLES:  # set first so teardown restores the original state
        monkeypatch.setenv(variable, "")
        monkeypatch.delenv(variable)
    monkeypatch.setenv("USER", "david")


def test_settings_round_trip_privately_and_never_override_the_environment(tmp_path, monkeypatch):
    path = tmp_path / "config" / "settings.yaml"
    settings = Settings.load(path)
    assert not settings.exists and settings.get("name") is None
    settings.set("Dana", "name")
    settings.set("anthropic", "consultant")
    settings.set("sk-ant-secret", "anthropic", "api_key")
    settings.save()
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    loaded = Settings.load(path)
    assert loaded.exists and loaded.get("anthropic", "api_key") == "sk-ant-secret"
    environment = {"REASON_COMMONS_PROVIDER": "lm-studio"}
    loaded.apply(environment)
    assert environment == {"REASON_COMMONS_PROVIDER": "lm-studio", "REASON_COMMONS_SPEAKER": "Dana",
                           "ANTHROPIC_API_KEY": "sk-ant-secret"}
    assert loaded.overridden(environment) == ["REASON_COMMONS_PROVIDER"]
    loaded.apply(environment, override=True)
    assert environment["REASON_COMMONS_PROVIDER"] == "anthropic"


def test_default_name_is_the_accounts_first_name(monkeypatch):
    import pwd
    from types import SimpleNamespace
    from reason_commons.adapters.onboarding import login_name
    monkeypatch.setenv("USER", "djoseph")
    monkeypatch.setattr(pwd, "getpwuid", lambda uid: SimpleNamespace(pw_name="djoseph", pw_gecos="David Joseph,,,"))
    assert login_name() == "David"
    monkeypatch.setattr(pwd, "getpwuid", lambda uid: SimpleNamespace(pw_name="djoseph", pw_gecos=""))
    assert login_name() == "Djoseph"


def test_unreadable_settings_count_as_first_start(tmp_path):
    path = tmp_path / "settings.yaml"
    path.write_text("name: [unclosed")
    assert not Settings.load(path).exists


def test_model_hints_name_the_trade_off():
    assert model_hint("claude-haiku-5-5") == "lowest cost; quick, lighter reasoning"
    assert model_hint("claude-sonnet-5-5") == "deeper reasoning; costs more per reply"
    assert "capable" in model_hint("claude-opus-5-5")
    # An older Haiku costs more than Haiku 5.5 and was never validated, so it is not called the cheapest.
    hint = model_hint("claude-haiku-4-5-20251001")
    assert "lowest" not in hint and "not validated" in hint


def test_setup_recommends_haiku_5_5_and_otherwise_sonnet_never_another_haiku():
    from reason_commons.adapters.onboarding import recommended_model
    assert recommended_model(["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5",
                              "claude-haiku-4-5-20251001"]) == "claude-haiku-5-5"
    assert recommended_model(["claude-opus-5-5", "claude-haiku-4-5-20251001", "claude-sonnet-5-5"]) == \
        "claude-sonnet-5-5"
    assert recommended_model(["claude-opus-5-5", "claude-haiku-4-5-20251001"]) == "claude-opus-5-5"


def test_a_saved_claude_model_stays_after_the_default_changes():
    """Someone who chose Sonnet keeps it: the saved choice fills the model the adapter reads."""
    from reason_commons.adapters.anthropic import AnthropicConsultant
    settings = Settings(data={"consultant": "anthropic", "anthropic": {"model": "claude-sonnet-5-5"}}, exists=True)
    environment = {}
    settings.apply(environment)
    assert environment["REASON_COMMONS_ANTHROPIC_MODEL"] == "claude-sonnet-5-5"
    assert AnthropicConsultant.describe_settings(environ=environment)["model"] == "claude-sonnet-5-5"
    assert AnthropicConsultant.describe_settings(environ={})["model"] == "claude-haiku-5-5"


async def pick(app, pilot, key):
    """Activate the option with this id in the current dialog."""
    await pilot.pause()
    choices = (app.screen.query("#choices") or app.screen.query("#goals")).first()
    choices.highlighted = next(i for i, option in enumerate(choices.options) if option.id == key)
    await pilot.press("enter")
    await pilot.pause()


async def type_in(app, pilot, text):
    await pilot.pause()
    app.screen.query_one("Input").value = text
    await pilot.press("enter")
    await pilot.pause()


def test_first_start_offers_the_ways_to_begin(tmp_path):
    settings = Settings.load(tmp_path / "settings.yaml")

    async def run():
        app = GoalsApp(tmp_path / "goals", settings=settings)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            ids = [option.id for option in app.query_one("#goals").options]
            assert ids == ["start", "setup", "tour", "sample"]
            assert app.query_one("#goals").highlighted == 0
            app.query_one("#goals").highlighted = 2
            await pilot.press("enter")
            await pilot.pause()
        return app.return_value
    assert asyncio.run(run()) == TOUR


def test_start_saves_defaults_and_goes_straight_to_naming_the_goal(tmp_path):
    settings = Settings.load(tmp_path / "settings.yaml")

    async def run():
        app = GoalsApp(tmp_path / "goals", settings=settings)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            await pilot.press("enter")  # the first option, highlighted
            await pilot.pause()
            await type_in(app, pilot, "Sleep better")
        return app.return_value
    assert asyncio.run(run()) == tmp_path / "goals" / "sleep-better"
    saved = Settings.load(tmp_path / "settings.yaml")
    assert saved.get("name") == "David" and saved.get("consultant") == "guided"


def test_setup_with_claude_checks_the_key_offers_models_and_starts_a_goal(tmp_path):
    settings = Settings.load(tmp_path / "settings.yaml")
    seen = []

    def fake_anthropic(key):
        seen.append(key)
        if key == "wrong":
            return None, "Anthropic did not accept this key."
        return [("claude-opus-5-5", "Claude Opus 5.5"), ("claude-sonnet-5-5", "Claude Sonnet 5.5"),
                ("claude-haiku-4-5-20251001", "Claude Haiku 4.5")], None

    async def run():
        app = GoalsApp(tmp_path / "goals", settings=settings, checks={"anthropic": fake_anthropic})
        async with app.run_test(size=(100, 30)) as pilot:
            await pick(app, pilot, "setup")
            await type_in(app, pilot, "Dana")
            await pick(app, pilot, "anthropic")
            await type_in(app, pilot, "wrong")
            await pilot.pause(0.2)
            await pick(app, pilot, "back")          # back to the key
            await type_in(app, pilot, "sk-ant-good")
            await pilot.pause(0.2)
            choices = app.screen.query_one("#choices")
            # Haiku 5.5 is not listed, and an older Haiku is never recommended: Sonnet is.
            assert choices.options[choices.highlighted].id == "claude-sonnet-5-5"
            await pick(app, pilot, "claude-opus-5-5")
            await pick(app, pilot, "goal")
            await type_in(app, pilot, "Sleep better")
        return app.return_value

    created = asyncio.run(run())
    assert seen == ["wrong", "sk-ant-good"]
    assert created == tmp_path / "goals" / "sleep-better"
    saved = Settings.load(tmp_path / "settings.yaml")
    assert saved.get("name") == "Dana" and saved.get("consultant") == "anthropic"
    assert saved.get("anthropic", "model") == "claude-opus-5-5"
    assert saved.get("anthropic", "api_key") == "sk-ant-good"
    assert os.environ["REASON_COMMONS_PROVIDER"] == "anthropic"
    with open_case(created, writable=False) as case:
        assert "sk-ant" not in str(case.inspect())


def test_setup_highlights_haiku_5_5_when_the_key_can_use_it(tmp_path):
    settings = Settings.load(tmp_path / "settings.yaml")
    models = [("claude-opus-5-5", "Claude Opus 5.5"), ("claude-sonnet-5-5", "Claude Sonnet 5.5"),
              ("claude-haiku-5-5", "Claude Haiku 5.5"), ("claude-haiku-4-5-20251001", "Claude Haiku 4.5")]

    async def run():
        app = GoalsApp(tmp_path / "goals", settings=settings, checks={"anthropic": lambda key: (models, None)})
        async with app.run_test(size=(100, 30)) as pilot:
            await pick(app, pilot, "setup")
            await type_in(app, pilot, "Dana")
            await pick(app, pilot, "anthropic")
            await type_in(app, pilot, "sk-ant-good")
            await pilot.pause(0.2)
            choices = app.screen.query_one("#choices")
            labels = {option.id: str(option.prompt) for option in choices.options}
            assert choices.options[choices.highlighted].id == "claude-haiku-5-5"
            assert [key for key, label in labels.items() if "(recommended)" in label] == ["claude-haiku-5-5"]
            assert "Haiku 5.5 costs least" in str(app.screen.query_one(".explanation").render())
            await pilot.press("enter")
            await pick(app, pilot, "sample")
        return app.return_value
    assert asyncio.run(run()) == "sample"
    assert Settings.load(tmp_path / "settings.yaml").get("anthropic", "model") == "claude-haiku-5-5"


def test_setup_falls_back_to_the_guide_when_lm_studio_is_missing(tmp_path):
    settings = Settings.load(tmp_path / "settings.yaml")

    async def run():
        app = GoalsApp(tmp_path / "goals", settings=settings,
                       checks={"lm-studio": lambda url: (None, f"Nothing answered at {url}.")})
        async with app.run_test(size=(100, 30)) as pilot:
            await pick(app, pilot, "setup")
            await type_in(app, pilot, "Dana")
            await pick(app, pilot, "lm-studio")
            await type_in(app, pilot, "")           # keep the usual address
            await pilot.pause(0.2)
            await pick(app, pilot, "guided")
            await pick(app, pilot, "sample")
        return app.return_value
    assert asyncio.run(run()) == "sample"
    assert Settings.load(tmp_path / "settings.yaml").get("consultant") == "guided"


def test_escape_leaves_setup_without_saving(tmp_path):
    settings = Settings.load(tmp_path / "settings.yaml")

    async def run():
        app = GoalsApp(tmp_path / "goals", settings=settings)
        async with app.run_test(size=(80, 24)) as pilot:
            await pick(app, pilot, "setup")
            await pilot.press("escape")
            await pilot.pause()
            return [option.id for option in app.query_one("#goals").options]
    assert asyncio.run(run())[0] == "start"  # still the first-start choices
    assert not (tmp_path / "settings.yaml").exists()


def test_tour_coaches_each_step_fills_examples_and_finishes(tmp_path):
    path = tmp_path / "practice"
    create_case(path, "Practice").close()

    async def run():
        app = ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                               lambda provider: GuidedConsultant(), tour=True)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            states = []
            while app.tour_state() != "done":
                states.append(app.tour_state())
                assert "Tour · step" in str(app.query_one("#coach").render())
                app.query_one("#fill").press()
                await pilot.pause()
                assert app.query_one("#editor").text == EXAMPLE_ANSWERS[states[-1]]
                await pilot.press("ctrl+s")
                await app.workers.wait_for_complete()
                await pilot.pause()
            assert states == list(EXAMPLE_ANSWERS)
            assert "Loop complete" in str(app.query_one("#coach").render())
            assert app.query_one("#fill").has_class("hidden")
            app.query_one("#finish").press()
            await pilot.pause()
        return app.return_value
    assert asyncio.run(run()) == TOUR_FINISHED


def test_ordinary_workspace_shows_no_tour_controls(tmp_path):
    path = tmp_path / "case"
    create_case(path, "Plain").close()

    async def run():
        app = ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                               lambda provider: GuidedConsultant())
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            return [app.query_one(name).has_class("hidden") for name in ("#coach", "#fill", "#finish")]
    assert asyncio.run(run()) == [True, True, True]


def test_tour_state_reads_the_guided_purpose():
    assert tour_state(None, []) == "goal"
    assert tour_state({"data": {"purpose": "guided:test_forecast"}}, []) == "test_forecast"
    assert tour_state({"data": {"purpose": "guided:test_change"}}, [{"kind": "review"}]) == "done"


def test_finishing_the_tour_returns_to_the_home_screen(tmp_path, monkeypatch):
    from reason_commons.adapters import tui
    shown = iter([TOUR, None])
    calls = []
    monkeypatch.setattr(tui.GoalsApp, "run", lambda self: (calls.append("home"), next(shown))[1])
    monkeypatch.setattr(tui, "run_tour", lambda speaker=None: (calls.append("tour"), TOUR_FINISHED)[1])
    monkeypatch.setenv("REASON_COMMONS_HOME", str(tmp_path / "goals"))
    tui.run_home(settings=Settings.load(tmp_path / "settings.yaml"))
    assert calls == ["home", "tour", "home"]


def test_run_tour_opens_a_throwaway_practice_goal(monkeypatch):
    from reason_commons.adapters import tui
    seen = {}

    def fake_run(self):
        seen.update(store=self.store, tour=self.tour, provider=self.provider)
        return TOUR_FINISHED
    monkeypatch.setattr(tui.ReasonCommonsApp, "run", fake_run)
    monkeypatch.setenv("REASON_COMMONS_CONFIG", "/nonexistent/settings.yaml")
    assert tui.run_tour("David") == TOUR_FINISHED
    assert seen["tour"] and seen["provider"] == "guided"
    assert not os.path.exists(seen["store"])


def test_settings_offers_you_on_the_home_screen_and_it_runs_the_setup_questions(tmp_path, monkeypatch):
    """The home list no longer has a Settings row, so F2 Settings carries it: Enter on You asks name, then consultant."""
    monkeypatch.setenv("REASON_COMMONS_THEME", "")  # set first, so teardown puts back what a theme change wrote
    monkeypatch.delenv("REASON_COMMONS_THEME")
    settings = Settings(tmp_path / "settings.yaml", {"name": "Dana", "consultant": "guided"}, exists=True)

    async def run():
        app = GoalsApp(tmp_path / "goals", list_goals=lambda root: [], settings=settings)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("f2")
            await pilot.pause()
            rows = app.screen.query_one("#settings-rows")
            assert [option.id for option in rows.options] == ["voice", "mode", "setup"]
            assert "Dana · offline guide" in str(rows.get_option("setup").prompt)
            # Left and Right do nothing on You (they change the voice and mode rows), and Enter opens the questions.
            await pilot.press("down", "down", "right", "left")
            assert app.theme == "yoruba-dark"
            await pilot.press("enter")
            await pilot.pause()
            assert type(app.screen).__name__ == "TextStep"
            assert app.screen.query_one("Input").value == "Dana"
            await pilot.press("escape")  # leaving setup changes nothing
            await pilot.pause()
    asyncio.run(run())
    assert Settings.load(tmp_path / "settings.yaml").get("name") is None  # nothing was saved (the file never existed)


def test_the_workspace_settings_has_no_you_row(tmp_path):
    """Name and consultant are asked on the home screen; inside a goal F2 is only the appearance."""
    path = tmp_path / "case"
    create_case(path, "Plain").close()

    async def run():
        app = ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                               lambda provider: GuidedConsultant())
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("f2")
            await pilot.pause()
            return [option.id for option in app.screen.query_one("#settings-rows").options]
    assert asyncio.run(run()) == ["voice", "mode"]


def test_you_in_settings_is_also_there_on_first_start_and_a_click_on_theme_changes_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("REASON_COMMONS_THEME", "")  # set first, so teardown puts back what a theme change wrote
    monkeypatch.delenv("REASON_COMMONS_THEME")
    settings = Settings.load(tmp_path / "settings.yaml")  # never saved: first start

    async def run():
        app = GoalsApp(tmp_path / "goals", settings=settings)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("f2")
            await pilot.pause()
            rows = app.screen.query_one("#settings-rows")
            assert [option.id for option in rows.options] == ["voice", "mode", "setup"]
            # Choosing a row with Enter or a click does not change it; Left and Right do.
            await pilot.click("#settings-rows", offset=(5, 0))
            await pilot.press("enter")
            assert app.theme == "yoruba-dark"
            await pilot.press("right")
            assert app.theme == "wuxing-dark"
            await pilot.press("down", "down", "enter")
            await pilot.pause()
            assert type(app.screen).__name__ == "TextStep"
            await pilot.press("escape")
            await pilot.pause()
    asyncio.run(run())
    assert not (tmp_path / "settings.yaml").exists()  # first start is unfinished: nothing was saved
