"""First start: choosing how to begin, personal setup and the guided tour's coaching.

Setup records only personal settings (name, consultant, model) outside every goal.
The tour runs the ordinary workspace on a throwaway practice goal with the built-in
guide; its coaching text lives here and changes nothing in the case.
"""

import asyncio
import os

from rich.markup import escape
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from reason_commons.adapters.sample import ANSWERS
from reason_commons.adapters.settings import describe, model_hint

CONSULTANT_CHOICES = [
    ("guided", "Built-in guide  ·  offline, free, nothing to set up",
     "Asks the loop's questions in order and keeps your exact words. No advice, no trees. "
     "The best way to do a first loop."),
    ("anthropic", "Claude (Anthropic)  ·  needs an API key, paid per use",
     "Adapts its questions, gives advice and grows the six trees. What you send goes to Anthropic."),
    ("lm-studio", "Local model with LM Studio  ·  private, on your computer",
     "Like Claude, but nothing leaves your computer. Needs LM Studio and a capable model."),
]
CONSULTANT_NAMES = {"guided": "Built-in guide (offline)", "anthropic": "Claude (Anthropic)",
                    "lm-studio": "LM Studio (local)"}
DEFAULT_LM_STUDIO_URL = "http://127.0.0.1:1234/v1"


def login_name():
    """A friendly default for the name field: the login name, capitalised."""
    name = os.environ.get("USER") or os.environ.get("USERNAME") or ""
    return name[:1].upper() + name[1:]


# ----- steps -------------------------------------------------------------------------
class Step(ModalScreen):
    """One setup question in a dialog. Esc goes back one step (or leaves setup at the first)."""

    BINDINGS = [Binding("escape", "back", "Back")]
    BACK = object()

    def __init__(self, number, title, explanation, hint):
        super().__init__()
        self.number, self.title_text, self.explanation, self.hint = number, title, explanation, hint

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            if self.number:
                yield Label(f"Setup · step {self.number} of 3", classes="step-count")
            yield Label(self.title_text, classes="dialog-title")
            if self.explanation:
                yield Static(self.explanation, classes="explanation")
            yield from self.body()
            yield Static(self.hint, classes="hint")

    def body(self):
        return []

    def action_back(self):
        self.dismiss(self.BACK)


class TextStep(Step):
    def __init__(self, number, title, explanation, hint, value="", placeholder="", password=False):
        super().__init__(number, title, explanation, hint)
        self.value, self.placeholder, self.password = value, placeholder, password

    def body(self):
        yield Input(self.value, placeholder=self.placeholder, password=self.password, id="answer")

    @on(Input.Submitted)
    def submitted(self, event):
        self.dismiss(event.value.strip())


class ChoiceStep(Step):
    def __init__(self, number, title, explanation, hint, options, highlighted=0):
        super().__init__(number, title, explanation, hint)
        self.options, self.highlighted = options, highlighted

    def body(self):
        yield OptionList(*[Option(prompt, id=key) for key, prompt in self.options], id="choices")

    def on_mount(self):
        choices = self.query_one("#choices", OptionList)
        choices.highlighted = self.highlighted
        choices.focus()

    @on(OptionList.OptionSelected)
    def chosen(self, event):
        self.dismiss(event.option.id)


class Checking(ModalScreen):
    def __init__(self, message):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.message, classes="dialog-title")
            yield Label("This takes a few seconds. Nothing from your goals is sent.", classes="hint")


def option_text(title, detail):
    text = Text(title, style="bold")
    text.append("\n" + detail, style="dim")
    return text


# ----- connection checks (run in a thread) ---------------------------------------------
def check_anthropic(key):
    """Return (models, None) or (None, plain explanation)."""
    from reason_commons.adapters.anthropic import AnthropicConsultant, AnthropicError
    try:
        consultant = AnthropicConsultant(
            base_url=os.environ.get("REASON_COMMONS_ANTHROPIC_URL", "https://api.anthropic.com/v1"),
            api_key=key, timeout=20.0)
        models = consultant.list_models()
    except AnthropicError as exc:
        if exc.http_status in (401, 403):
            return None, "Anthropic did not accept this key. Check that you copied all of it."
        if exc.category in ("connection", "timeout"):
            return None, "Could not reach Anthropic. Check your internet connection."
        return None, f"Anthropic answered with an error ({exc})."
    except ValueError as exc:
        return None, f"That key cannot be used: {exc}."
    except Exception as exc:  # report the category only, never the key
        return None, f"The check failed ({type(exc).__name__})."
    if not models:
        return None, "Anthropic accepted the key but listed no models for this account."
    return models, None


def check_lm_studio(url):
    from reason_commons.adapters.lm_studio import LMStudioConsultant, LMStudioError
    try:
        consultant = LMStudioConsultant(base_url=url, api_key=os.environ.get("LM_STUDIO_API_TOKEN") or None,
                                        timeout=10.0)
        models = consultant.list_models()
    except ValueError as exc:
        return None, f"That address cannot be used: {exc}."
    except LMStudioError as exc:
        if exc.category in ("connection", "timeout"):
            return None, (f"Nothing answered at {url}. Open LM Studio, go to the Developer tab and "
                          "start the server, then try again.")
        if exc.http_status == 401:
            return None, "LM Studio wants a token. Set LM_STUDIO_API_TOKEN in your shell, then try again."
        return None, f"LM Studio answered with an error ({exc})."
    except Exception as exc:
        return None, f"The check failed ({type(exc).__name__})."
    if not models:
        return None, "LM Studio is running but no model is loaded. Load a chat model, then try again."
    return [(model, model) for model in models], None


# ----- the setup flow --------------------------------------------------------------------
async def run_setup(app, settings, first_run, checks=None):
    """Ask for name and consultant (and its key and model), save, and return the next choice.

    Returns "goal", "tour", "sample" or "home" after saving, or None when setup was left
    (nothing is saved then). ``checks`` replaces the network checks in tests.
    """
    checks = checks or {"anthropic": check_anthropic, "lm-studio": check_lm_studio}
    name = settings.get("name") or login_name()
    consultant = settings.get("consultant") or "guided"
    key, models, model = settings.get("anthropic", "api_key"), [], None
    url = settings.get("lm_studio", "url") or os.environ.get("REASON_COMMONS_LM_STUDIO_URL") or DEFAULT_LM_STUDIO_URL
    environment_key = os.environ.get("ANTHROPIC_API_KEY") if not key else None
    history, state = [], "name"

    def go(next_state):
        history.append(state)
        return next_state

    while True:
        if state == "name":
            answer = await app.push_screen_wait(TextStep(
                1, "What should we call you?",
                "Your name is saved with every answer you write, so it is clear who said what when a "
                "goal is shared. It stays on this computer.",
                "Enter continues. Esc leaves setup without changing anything.", value=name,
                placeholder="your name"))
            if answer is Step.BACK:
                return None
            if not answer:
                app.notify("A name is needed; a first name is enough.", severity="warning")
                continue
            name, state = answer, go("consultant")
        elif state == "consultant":
            options = [(key_, option_text(title, detail)) for key_, title, detail in CONSULTANT_CHOICES]
            answer = await app.push_screen_wait(ChoiceStep(
                2, "Who should ask you the questions?",
                "You can change this any time: Settings on the home screen, or Ctrl+P inside a goal. "
                "Your goals keep going from where they are when you switch.",
                "Arrows choose, Enter continues, Esc goes back. New here? The built-in guide is a good start.",
                options, highlighted=[c[0] for c in CONSULTANT_CHOICES].index(consultant)))
            if answer is Step.BACK:
                state = history.pop()
                continue
            consultant = answer
            state = go({"guided": "done", "anthropic": "anthropic_key", "lm-studio": "lm_url"}[answer])
        elif state == "anthropic_key":
            reuse = "Leave it empty to use the key already set in ANTHROPIC_API_KEY. " if environment_key else ""
            answer = await app.push_screen_wait(TextStep(
                3, "Paste your Anthropic API key",
                "Create one at console.anthropic.com, under API keys. It starts with sk-ant-. "
                + reuse + "It is saved only in your personal settings file, readable by you alone, and "
                "never in a goal or an export.",
                "Enter checks the key. Esc goes back.", password=True,
                placeholder="key already set in your environment" if environment_key else "sk-ant-...",
                value=key or ""))
            if answer is Step.BACK:
                state = history.pop()
                continue
            if not answer and not environment_key:
                app.notify("Paste a key, or press Esc and choose another consultant.", severity="warning")
                continue
            key = answer or None
            state = go("anthropic_check")
        elif state in ("anthropic_check", "lm_check"):
            provider = "anthropic" if state == "anthropic_check" else "lm-studio"
            waiting = Checking("Checking your key with Anthropic..." if provider == "anthropic"
                               else f"Looking for LM Studio at {url}...")
            app.push_screen(waiting)
            argument = (key or environment_key) if provider == "anthropic" else url
            models, problem = await asyncio.to_thread(checks[provider], argument)
            waiting.dismiss()
            if problem is None:
                state = go("anthropic_model" if provider == "anthropic" else "lm_model")
                continue
            answer = await app.push_screen_wait(ChoiceStep(
                3, "That did not work yet", problem, "Arrows choose, Enter continues.",
                [("again", "Try again"), ("back", "Go back and change it"),
                 ("guided", "Use the built-in guide for now (switch later from Settings)")]))
            if answer == "guided":
                consultant, state = "guided", go("done")
            elif answer in ("back", Step.BACK):
                state = history.pop()
        elif state in ("anthropic_model", "lm_model"):
            provider = "anthropic" if state == "anthropic_model" else "lm-studio"
            current = settings.get("anthropic" if provider == "anthropic" else "lm_studio", "model")
            ids = [model_id for model_id, _ in models]
            if provider == "anthropic":
                recommended = next((m for m in ids if "sonnet" in m.lower()), ids[0])
                options = []
                for model_id, display in models:
                    hint = model_hint(model_id) or "Claude model"
                    title = display + ("  (recommended)" if model_id == recommended else "")
                    options.append((model_id, option_text(title, f"{hint}  ·  {model_id}")))
                explanation = ("These are the models your key can use. Sonnet suits most people; "
                               "you can change it later.")
            else:
                recommended = ids[0]
                options = [(model_id, model_id) for model_id in ids]
                explanation = "These models are loaded in LM Studio. Larger models usually ask better questions."
            highlighted = ids.index(current) if current in ids else ids.index(recommended)
            answer = await app.push_screen_wait(ChoiceStep(
                3, "Choose a model", explanation, "Arrows choose, Enter continues, Esc goes back.",
                options, highlighted=highlighted))
            if answer is Step.BACK:
                history.pop()  # skip the check when going back
                state = history.pop()
                continue
            model, state = answer, go("done")
        elif state == "lm_url":
            answer = await app.push_screen_wait(TextStep(
                3, "Where is LM Studio's server?",
                "In LM Studio, load a chat model, open the Developer tab and start the server. The usual "
                "address is already filled in.", "Enter checks the server. Esc goes back.", value=url))
            if answer is Step.BACK:
                state = history.pop()
                continue
            url, state = answer or DEFAULT_LM_STUDIO_URL, go("lm_check")
        elif state == "done":
            settings.set(name, "name")
            settings.set(consultant, "consultant")
            if consultant == "anthropic":
                settings.set(key, "anthropic", "api_key")
                settings.set(model, "anthropic", "model")
            elif consultant == "lm-studio":
                settings.set(url, "lm_studio", "url")
                settings.set(model, "lm_studio", "model")
            overridden = settings.overridden()
            try:
                settings.save()
            except OSError as exc:
                app.notify(f"Could not save your settings ({exc}). They apply until you quit.",
                           severity="error", timeout=10)
            settings.apply(override=True)
            lines = [f"Name: {escape(name)}", f"Consultant: {escape(describe(settings).split(' · ', 1)[1])}", "",
                     f"Saved in {escape(str(settings.path))}, readable only by you."]
            if overridden:
                lines += ["", "[b]Note:[/b] your shell also sets " + ", ".join(overridden) +
                          ". Those win the next time you start; remove them from your shell profile "
                          "to use these settings."]
            if first_run:
                options = [("goal", "Start my first goal"),
                           ("tour", "Take the guided tour first (about 5 minutes, nothing is kept)"),
                           ("sample", "Look around a finished example first")]
            else:
                options = [("home", "Back to my goals")]
            answer = await app.push_screen_wait(ChoiceStep(
                None, "You are set up", "\n".join(lines), "Arrows choose, Enter continues.", options))
            return "home" if answer is Step.BACK else answer


# ----- the guided tour ----------------------------------------------------------------
TOUR_PURPOSES = ["goal", "goal_measure", "goal_protect", "test_change", "test_forecast", "test_review",
                 "test_stop", "action", "observe", "review"]
EXAMPLE_ANSWERS = dict(zip(TOUR_PURPOSES, ANSWERS))
TOUR_STAGE = {"goal": 1, "goal_measure": 1, "goal_protect": 1, "test_change": 2, "test_forecast": 2,
              "test_review": 2, "test_stop": 2, "action": 3, "observe": 4, "review": 5, "done": 6}
COACH = {
    "goal": "Welcome! The question is in the middle; you answer in the box below. Write a goal of your own, "
            "or press [b]Example answer[/b] to borrow Mira's from the tutorial. Then press [b]Ctrl+S[/b] "
            "(or Tab to Send, then Enter) to send it.",
    "goal_measure": "The guide saved your exact words and asked the next question. Press [b]Explain this[/b] "
                    "to see why a question matters; it never sends anything. Optional questions are "
                    "skipped by sending an empty answer.",
    "goal_protect": "Safeguards are what must not get worse. Write one per line: [b]Enter starts a new line "
                    "and never sends.[/b]",
    "test_change": "Goal is ticked on the loop line above. Now pick one small change you could make "
                   "yourself, soon.",
    "test_forecast": "The key step: [b]write down what you expect before any result exists.[/b] This original "
                     "forecast is saved now and cannot be quietly rewritten later.",
    "test_review": "When will you look at the result? Optional: send an empty answer to skip.",
    "test_stop": "What would make you stop early? Also optional.",
    "action": "Name the very next action and when. For real, you would now press [b]Ctrl+Q[/b] and go do "
              "it; everything, even a half-written answer, is saved. In the tour, time skips ahead.",
    "observe": "Some weeks later... Report what actually happened, separately from what you hoped.",
    "review": "The guide quotes your original forecast word for word. Check the safeguards first, then "
              "decide: keep, adjust or drop the change.",
    "done": "[b]Loop complete.[/b] Look around before you go: [b]Views[/b] then [i]Tests[/i] puts your forecast "
            "next to the result; [b]Ctrl+T[/b] opens the six trees (Claude or a local model grows them as "
            "you talk); [b]Ctrl+P[/b] lists every action, including changing consultant. Press "
            "[b]Finish tour[/b] to start a goal of your own.",
}


def tour_state(question, records):
    """Which coaching step applies: a guided purpose, or "done" once a review is recorded."""
    if any(record["kind"] == "review" for record in records):
        return "done"
    if not question:
        return "goal"
    purpose = question.get("data", {}).get("purpose") or ""
    return purpose[len("guided:"):] if purpose.startswith("guided:") else "goal"


def coach_text(state):
    return (f"[b]Tour · step {TOUR_STAGE.get(state, 1)} of 6[/b]   [dim]practice goal with the offline "
            f"guide · nothing here is kept[/dim]\n{COACH.get(state, COACH['goal'])}")
