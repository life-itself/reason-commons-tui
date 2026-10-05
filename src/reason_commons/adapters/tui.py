"""Persistent terminal workspace (first usable slice of p1) built with Textual.

The TUI is a projection over ``CaseApplication``: it reads ``workspace`` and
``inspect``, and changes the case only through ``retain_input``, ``consult``,
``retry``, ``export`` and ``checkpoint``. It owns layout, focus, the editor and
which view is shown; it defines no reasoning or persistence rules.
"""

from datetime import date
import os
import re
import tempfile
import textwrap
from pathlib import Path

from rich.console import Group
from rich.markup import escape
from rich.table import Table
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, Markdown, OptionList, Static, TextArea
from textual.widgets.option_list import Option

from reason_commons.adapters import themes
from reason_commons.adapters.guided import STEPS
from reason_commons.adapters.onboarding import EXAMPLE_ANSWERS, coach_text, login_name, run_setup, tour_state
from reason_commons.adapters.settings import Settings, describe
from reason_commons.adapters.rendering import _literal
from reason_commons.adapters.timeline import change_summary, day, next_action, revision_changes
from reason_commons.adapters.trees import ROLE_LABELS, TREE_TITLES, trees_lines


TOUR_FINISHED = "tour-finished"
STORY_OWN_GOAL, STORY_HOME = "story-own-goal", "story-home"
PROVIDERS = {"guided": "Built-in guide (offline)", "anthropic": "Anthropic Claude", "lm-studio": "LM Studio (local)"}
# Who receives what you send, named where you send it.
SEND_TO = {"guided": "the offline guide", "anthropic": "Claude", "lm-studio": "your local model"}
TREE_ORDER = list(TREE_TITLES)
VIEW_LABELS = [("next", "Next step"), ("goal", "Goal"), ("trees", "Trees"), ("tests", "Tests"), ("actions", "Actions"),
               ("reasoning", "Reasoning"), ("sources", "Your words"), ("history", "History")]
# The control that has keyboard focus, named in the header.
FOCUS_NAMES = {"editor": "Answer", "send": "Send", "fill": "Example answer", "retry": "Retry",
               "explain": "Explain this", "moves": "Other moves", "views-button": "Views", "actions": "Actions",
               "finish": "Finish tour", "views": "Views list", "main": "Reading", "timeline": "History list",
               "earlier": "Earlier", "later": "Later", "now": "Back to now", "first": "From the beginning",
               "own": "Start my own goal", "home": "Back to start"}
LOOP = [("goal", "Goal"), ("test", "Test + forecast"), ("action", "Action"), ("observe", "Observe"),
        ("review", "Review")]
GUIDED_STAGE = {"goal": "goal", "goal_measure": "goal", "goal_protect": "goal", "test_change": "test",
                "test_forecast": "test", "test_review": "test", "test_stop": "test", "action": "action",
                "observe": "observe", "review": "review"}
STAGE_WORDS = [("review", ("review",)), ("observe", ("observ", "result", "happened")), ("action", ("action",)),
               ("test", ("test", "forecast", "trial", "change")), ("goal", ("goal", "success", "start"))]
WELCOME_WIDE = """\
```
 +--------------------+     +--------------------+     +--------------------+
 | What matters       |     | One small test     |     | What you learn     |
 | your goal and what | --> | with a forecast    | --> | the result next to |
 | must not get worse |     | written first      |     | your forecast      |
 +--------------------+     +--------------------+     +--------------------+
```"""
WELCOME_NARROW = """\
```
 [What matters] --> [One small test] --> [What you learn]
```"""
STATUS_TEXT = {"unavailable": "the consultant could not be reached", "rejected": "the consultant's reply was invalid",
               "started": "the request was interrupted", "input_retained": "the consultant was not asked yet"}
# Stored values in everyday words.
BASIS_WORDS = {"participant_report": "reported", "observed": "observed", "hypothesis": "hypothesis"}
EXECUTION_WORDS = {"unknown": "not known yet", "planned": "planned", "completed": "done", "blocked": "blocked"}
ATTAINMENT_WORDS = {"unknown": "not known yet", "pending": "pending", "met": "met", "not_met": "not met"}
# Pane width from which a forecast and its results sit side by side rather than one after the other.
WIDE = 90

HELP = """\
## How Reason Commons works

You work through one small loop, as often as you like:

1. **Goal**: what would count as better, how you will measure it, and what must not get worse.
2. **Test**: one small change you can make yourself, with a forecast written *before* any result.
3. **Action**: the concrete next thing you will do.
4. **Observation**: what actually happened. Doing the work is not the same as it working.
5. **Review**: compare the result with the original forecast, then keep, adjust or drop the change.

Everything is saved in the case folder as you go. Closing the app keeps your draft.

## The trees

The **Trees** view (Ctrl+T) draws the six thinking-process trees, one at a
time: Goal, Current Reality, Evaporating Cloud, Future Reality, Prerequisite and
Transition. Ctrl+N moves to the next tree, and after the sixth shows all six together. They grow as you
talk: tell the consultant what causes a problem, what conflict keeps you stuck,
what stands in the way or what you plan to do, and it records each statement in
its tree, linked to the others. Ask it to reword or drop something and the tree
changes; earlier wording stays in History. A test can carry out an action from
the Transition Tree, and its forecast and result then show under that action.

The built-in guide does not add to the trees; Anthropic or LM Studio do. Any
consultant can work with trees you bring in: Ctrl+P, **Import trees** reads an
`.ltp.yaml` file, and **Export trees** writes one.

## Keys

| Key | What it does |
| --- | --- |
| Enter | New line in your answer (typing is always literal) |
| Ctrl+S, or Tab to **Send** then Enter | Send your answer |
| Tab / Shift+Tab | Move between controls |
| Esc | Leave the editor to browse; your text stays |
| Ctrl+T | Open the trees; press again to go back to the current question |
| Ctrl+N | In the Trees view: the next tree, then all six together |
| Ctrl+P | Actions: export, retry, change consultant, theme, quit |
| F1 | This help |
| Ctrl+Q | Save and quit |

## Consultants

The **built-in guide** works offline and asks the loop's questions in order.
**Anthropic** (needs `ANTHROPIC_API_KEY`) or **LM Studio** (a local model) give
adaptive questions and advice. Ctrl+P switches for this session; **Settings** on
the home screen saves your name, consultant and model for next time.

## Themes

Twelve voices from the Reason Commons web app, each light or dark. Ctrl+P,
**Theme** (or **Theme** on the home screen) previews them as you move: arrows
up and down choose a voice, left and right choose light or dark, Enter keeps it.
The choice is saved as `theme:` in your settings file; `--theme` or
`REASON_COMMONS_THEME` overrides it for one run.

New to it? **Take the guided tour** from the home screen: a practice goal with
coaching at each step and example answers. **Explore a real commons** shows how a
movement's shared reasoning grew, step by step. Nothing from either is kept.

## Looking back

**History** lists every saved step: when, who, and what changed. Enter opens that
moment exactly as it was; ← and → step through, **Back to now** returns. Nothing
can be changed while looking back.
"""


def loop_stage(question):
    """Which part of the loop the current question belongs to, or None when it cannot be told."""
    if not question:
        return "goal"
    data = question.get("data", {})
    purpose = data.get("purpose") or ""
    if purpose.startswith("guided:"):
        return GUIDED_STAGE.get(purpose[len("guided:"):])
    decision = (data.get("decision") or "").lower()
    return next((stage for stage, words in STAGE_WORDS if any(word in decision for word in words)), None)


def loop_line(stage, wide=True):
    """The loop drawn as one line: ✓ done, ● current, ○ still to come; symbols carry the meaning.

    When the step cannot be told (another consultant's own question), no step is marked.
    """
    keys = [key for key, _ in LOOP]
    if stage not in keys:
        return "[dim]" + "  ·  ".join(name for _, name in LOOP) + "[/]"
    now = keys.index(stage)
    parts = [f"[b]● {name}[/b]" if index == now else f"[dim]{'✓' if index < now else '○'} {name}[/]"
             for index, (_, name) in enumerate(LOOP)]
    return "  ".join(parts) + ("   [dim]then a new loop begins[/]" if stage == "review" and wide else "")


def md(value):
    """Escape stored, untrusted text for Markdown display."""
    return _literal(value, True)


def caret_index(text, location):
    row, column = location
    lines = text.split("\n")
    return min(len(text), sum(len(line) + 1 for line in lines[:row]) + column)


def caret_location(text, index):
    before = text[:max(0, min(index, len(text)))].split("\n")
    return len(before) - 1, len(before[-1])


def clip(text, width, lines):
    """Wrap text to at most ``lines`` lines; a cut is always marked with an ellipsis, never silent."""
    width = max(10, width)
    wrapped = textwrap.wrap(" ".join(str(text).split()), width) or [""]
    if len(wrapped) <= lines:
        return "\n".join(wrapped)
    kept = wrapped[:lines]
    kept[-1] = kept[-1][:width - 1].rstrip() + "…"
    return "\n".join(kept)


def latest(records, kind):
    return max((r for r in records if r["kind"] == kind), key=lambda r: int(r["ref"][1:].split("@")[0]),
               default=None)


def speakers(workspace, ref):
    names = [a["speaker"] for a in workspace["attribution"].get(ref, []) if a.get("speaker")]
    return ", ".join(dict.fromkeys(names))


def qualifiers(data):
    """Scope, denominator and period of a forecast or result, when recorded."""
    parts = [f"{field}: {data[field]}" for field in ("scope", "denominator", "period") if data.get(field)]
    return Text(" · ".join(parts), style="dim") if parts else None


def label(text):
    return Text(text, style="bold dim")


def side_by_side(rows):
    table = Table.grid(expand=True, padding=(0, 3))
    table.add_column(ratio=4)
    table.add_column(ratio=5)
    for left, right in rows:
        table.add_row(left, right)
    return table


def comparison_block(workspace, comparison, wide):
    """A test's original forecast next to what was reported, then the goal's safeguards.

    Results are matched to a forecast or safeguard only by the measure name someone
    recorded, as the chat renderer does. Nothing is judged: no tick, cross or breach
    appears unless someone recorded it.
    """
    test = comparison["test"]["data"]
    observations = comparison["observations"]
    goal = next((g for g in workspace["goals"] if g["ref"] == test.get("goal_ref")), None)
    protections = (goal or {}).get("data", {}).get("protections") or []
    forecasts = test.get("forecast") or []

    def results(measure):
        return [o for o in observations if o["data"]["measure"] == measure]

    def reported(found):
        if not found:
            return Text("not observed yet", style="dim")
        body = Text("\n\n".join(str(o["data"]["value"]) for o in found))
        extra = [qualifiers(o["data"]) for o in found if qualifiers(o["data"])]
        return Group(body, *extra)

    def heading(title, note):
        """One line when stacked; when side by side, the note goes underneath so both columns align."""
        if not wide:
            return label(title + (f" · {note}" if note else ""))
        return Group(label(title), Text(note, style="dim"))

    def result_heading(found):
        basis = {o["data"].get("basis") for o in found}
        word = "OBSERVED RESULT" if basis == {"observed"} else "REPORTED RESULT" if found else "RESULT"
        return heading(word, ", ".join(dict.fromkeys(n for o in found for n in [speakers(workspace, o["ref"])] if n)))

    parts = [Text.assemble(("TEST  ", "bold dim"), str(test["statement"]))]
    for forecast in forecasts:
        found = results(forecast.get("measure"))
        parts += [Text("")] * wide + [Text("Measure: " + str(forecast.get("measure") or "not stated"), style="dim")]
        expected = Group(Text(str(forecast.get("expected") or "not stated")),
                         *[q for q in [qualifiers(forecast)] if q])
        before, after = heading("ORIGINAL FORECAST", "saved before any result"), result_heading(found)
        if wide:
            parts.append(side_by_side([(before, after), (expected, reported(found))]))
        else:
            parts += [before, expected, after, reported(found)]
    named = {f.get("measure") for f in forecasts} | set(protections)
    for observation in (o for o in observations if o["data"]["measure"] not in named):
        parts.append(Group(label(f"ADDITIONAL RESULT · {observation['data']['measure']}"),
                           reported([observation])))
    if protections:
        checked = {p: results(p) for p in protections}
        if not any(checked.values()):
            parts.append(Text(""))
            parts.append(label("SAFEGUARDS · no separate result recorded: check each against the report"))
            parts += [Text("· " + p) for p in protections]
        else:
            parts += [Text(""), label("SAFEGUARDS")]
            rows = [(Text("· " + p), reported(found) if found else Text("no separate result recorded", style="dim"))
                    for p, found in checked.items()]
            parts.append(side_by_side(rows) if wide else Group(*[part for row in rows for part in row]))
    details = Table.grid(padding=(0, 2))
    details.add_column(style="bold dim", no_wrap=True)
    details.add_column()
    for name, value in (("Stop condition", test.get("stop_condition")), ("Review date", test.get("review_date"))):
        if value:
            details.add_row(name, Text(str(value)))
    for review in comparison["reviews"]:
        who = speakers(workspace, review["ref"])
        details.add_row("Review" + (f" · {who}" if who else ""), Text(str(review["data"]["assessment"])))
        if review["data"].get("next_decision"):
            details.add_row("Next", Text(str(review["data"]["next_decision"])))
    if details.row_count:
        parts += [Text(""), details]
    return Group(*parts)


def context_rows(workspace, record, pinned_goal):
    """One context record as (label, value) rows; what the band already shows is left out."""
    d, kind = record["data"], record["kind"]
    if kind == "goal":
        rows = [] if record["ref"] == pinned_goal else [("Goal", d["statement"])]
        rows += [(name.capitalize(), d[name]) for name in ("measure", "baseline", "horizon", "scope") if d.get(name)]
        if record["ref"] != pinned_goal:
            rows.append(("Protect", " · ".join(d.get("protections") or []) or "none recorded"))
        return rows
    if kind == "test":
        rows = [("Test", d["statement"])]
        rows += [("Original forecast", f.get("expected") or "not stated") for f in d.get("forecast") or []]
        rows += [(name, d[field]) for name, field in (("Review date", "review_date"), ("Stop condition", "stop_condition"))
                 if d.get(field)]
        return rows
    if kind == "action":
        return [("Action", d["statement"]),
                ("Status", f"{EXECUTION_WORDS.get(d.get('execution'), 'not known yet')} · whether it has the "
                           f"expected effect: {ATTAINMENT_WORDS.get(d.get('expected_state_attainment'), 'not known yet')}")]
    who = speakers(workspace, record["ref"])
    if kind == "observation":
        return [(" · ".join(filter(None, [BASIS_WORDS.get(d.get("basis"), "result").capitalize(), who])), d["value"])]
    if kind == "review":
        rows = [("Review" + (f" · {who}" if who else ""), d["assessment"])]
        return rows + ([("Next", d["next_decision"])] if d.get("next_decision") else [])
    if kind == "claim":
        return [(f"{TREE_TITLES[d['tree']][0]}, {ROLE_LABELS[d['role']].lower()}", d["statement"])]
    if kind == "link":
        return [(f"{TREE_TITLES[d['tree']][0]} link", d["relation"].replace("_", " "))]
    if kind == "retraction":
        return [("Withdrawn", d["reason"])]
    return [("Note", d.get("text"))]


class HelpScreen(ModalScreen):
    BINDINGS = [Binding("escape,f1", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            with VerticalScroll():
                yield Markdown(HELP)
            yield Button("Close", id="close", variant="primary")

    @on(Button.Pressed, "#close")
    def close(self):
        self.dismiss()


class ChoiceScreen(ModalScreen):
    """A labeled menu; nothing happens until an item is activated."""

    BINDINGS = [Binding("escape", "dismiss", "Back")]

    def __init__(self, title, options):
        super().__init__()
        self.title_text, self.options = title, options

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.title_text, classes="dialog-title")
            yield OptionList(*[Option(label, id=key) for key, label in self.options])
            yield Label("Arrows select, Enter activates, Esc returns. Your draft stays.", classes="hint")

    @on(OptionList.OptionSelected)
    def chosen(self, event):
        self.dismiss(event.option.id)


class PathScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    def __init__(self, title, default, hint):
        super().__init__()
        self.title_text, self.default, self.hint = title, default, hint

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.title_text, classes="dialog-title")
            yield Input(self.default, id="destination")
            yield Label(self.hint, classes="hint")

    @on(Input.Submitted)
    def submitted(self, event):
        self.dismiss(event.value.strip() or None)


class ExportScreen(PathScreen):
    def __init__(self, default):
        super().__init__("Export a portable copy of this case (.reasoncase)", default,
                         "Enter exports. Use a new file name. Esc cancels.")


class ThemeScreen(ModalScreen):
    """Every voice, previewed as you move. Enter keeps it; Esc puts back the one you had."""

    BINDINGS = [Binding("escape", "cancel", "Back"), Binding("left", "mode('light')", "Light"),
                Binding("right", "mode('dark')", "Dark")]

    def __init__(self, current):
        super().__init__()
        self.original = current
        self.voice, self.mode = themes.split_name(current)

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Theme", classes="dialog-title")
            yield Static(id="theme-mode")
            yield OptionList(*[Option(option_label(themes.title(voice), description), id=voice)
                               for voice, (_, _, description) in themes.VOICES.items()], id="themes")
            yield Label("↑↓ choose a voice, ←→ light or dark. Enter keeps it, Esc puts back the one you had.",
                        classes="hint")

    def on_mount(self):
        self.query_one("#themes", OptionList).highlighted = list(themes.VOICES).index(self.voice)
        self.preview()

    @on(OptionList.OptionHighlighted)
    def highlighted(self, event):
        self.voice = event.option.id
        self.preview()

    @on(OptionList.OptionSelected)
    def chosen(self, event):
        self.voice = event.option.id
        self.dismiss(themes.theme_name(self.voice, self.mode))

    def action_mode(self, mode):
        self.mode = mode
        self.preview()

    def action_cancel(self):
        self.app.theme = self.original
        self.dismiss(None)

    def preview(self):
        self.app.theme = themes.theme_name(self.voice, self.mode)
        marks = [f"[b]● {mode.capitalize()}[/b]" if mode == self.mode else f"[dim]○ {mode.capitalize()}[/]"
                 for mode in themes.MODES]
        self.query_one("#theme-mode", Static).update("   ".join(marks))


class ThemedApp(App):
    """Opens in the chosen voice (``$REASON_COMMONS_THEME``, filled from settings) and remembers a new one.

    Only the Reason Commons voices are offered; Textual's own themes are not.
    """

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings
        for theme in themes.THEMES.values():
            self.register_theme(theme)
        requested = os.environ.get(themes.ENVIRONMENT)
        self._unknown_theme = requested if requested and not themes.resolve(requested) else None
        self.theme = themes.resolve(requested) or themes.DEFAULT_THEME
        for name in set(self.available_themes) - set(themes.THEMES):
            self.unregister_theme(name)

    def on_mount(self):
        if self._unknown_theme:
            self.notify(f"No theme called {self._unknown_theme!r}; using {themes.title(self.theme)}. "
                        "Ctrl+P, Theme lists them.", severity="warning", timeout=8)

    def action_change_theme(self):
        self.push_screen(ThemeScreen(self.theme), self.keep_theme)

    def keep_theme(self, name):
        """Use this theme from now on: for this run, and in the settings file once there is one."""
        if not name:
            return
        self.theme = name
        os.environ[themes.ENVIRONMENT] = name
        if self.settings is None:
            return
        self.settings.set(name, "theme")
        if self.settings.exists:  # before first start finishes, setup saves it with the rest
            try:
                saved = Settings.load(self.settings.path)
                saved.set(name, "theme")
                saved.save()
            except OSError as exc:
                self.notify(f"Theme in use, but not saved ({exc}).", severity="error", timeout=8)


class ReasonCommonsApp(ThemedApp):
    TITLE = "Reason Commons"
    COMMAND_PALETTE_DISPLAY = "Actions"
    CSS = """
    Screen { layout: vertical; }
    #status { height: 1; padding: 0 1; color: $text-muted; }
    #pinned { height: auto; background: $boost; padding: 0 1; }
    #loop { height: 1; padding: 0 1; }
    #body { height: 1fr; }
    #views { width: 16; border: none; background: transparent; color: $text-muted; padding: 0 0 0 1; }
    #views > .option-list--option-highlighted { background: $boost; color: $text; text-style: bold; }
    #views:focus > .option-list--option-highlighted { background: $hand-tint; color: $foreground; }
    #views.hidden, #views-button.hidden { display: none; }
    #main { border: none; border-left: blank; padding: 0 1; }
    #main:focus { border-left: heavy $accent; }
    #content { margin: 0; }
    #canvas { margin: 0 0 1 0; padding: 0 2; }
    #canvas.hidden { display: none; }
    #content MarkdownH2 { margin: 0; color: $text-muted; background: transparent; text-style: bold; }
    #content MarkdownH3 { margin: 1 0 0 0; color: $text-muted; background: transparent; text-style: bold; }
    #response { height: auto; border: $frame $border-blurred; padding: 0 1;
                border-title-color: $text-muted; border-subtitle-color: $text-muted; }
    #response:focus-within { border: $frame $accent; }
    #editor { height: auto; min-height: 3; max-height: 10; border: none; }
    #controls { height: 1; }
    #controls Button { min-width: 8; height: 1; border: none; margin-right: 1; background: transparent;
                       color: $text-muted; text-style: none; }
    #controls Button:hover { color: $text; }
    #controls #send { background: $primary; color: $background; text-style: bold; }
    #controls #retry { color: $warning; }
    #controls #finish { color: $success; }
    #controls Button:focus, #controls #send:focus { background: $hand-tint; color: $foreground; text-style: bold; }
    #retry.hidden, #fill.hidden, #finish.hidden { display: none; }
    #coach { height: auto; max-height: 5; border: $frame $border-blurred; padding: 0 1; }
    #coach.hidden { display: none; }
    #moment { height: auto; border: $frame $border-blurred; padding: 0 1; }
    #moment:focus-within { border: $frame $accent; }
    #moment-text { height: auto; color: $text-muted; }
    #moment-controls { height: 1; }
    #moment-controls Button { min-width: 8; height: 1; border: none; margin-right: 1; background: transparent;
                              color: $text-muted; text-style: none; }
    #moment-controls Button:hover { color: $text; }
    #moment-controls #own { color: $success; }
    #moment-controls Button:focus { background: $hand-tint; color: $foreground; text-style: bold; }
    #timeline > .option-list--option-highlighted { background: $boost; }
    #timeline:focus > .option-list--option-highlighted { background: $hand-tint; color: $foreground; }
    #moment.hidden, #response.hidden, #timeline.hidden, .story-only.hidden { display: none; }
    #timeline { height: auto; max-height: 100%; border: none; margin-top: 1; background: transparent; }
    .step-count { color: $text-muted; }
    Step #dialog, Checking #dialog { padding: 0 2; }
    .explanation { margin-bottom: 1; }
    #choices { height: auto; max-height: 16; }
    ChoiceScreen, PathScreen, HelpScreen, ThemeScreen, Step, Checking { align: center middle; }
    #dialog { width: 80%; max-width: 90; height: auto; max-height: 90%; border: thick $accent;
              background: $surface; padding: 1 2; }
    HelpScreen #dialog, ThemeScreen #dialog { height: 90%; }
    #themes { height: 1fr; margin-top: 1; }
    .dialog-title { text-style: bold; margin-bottom: 1; }
    .hint { color: $text-muted; margin-top: 1; }
    """
    BINDINGS = [
        Binding("ctrl+s", "send", "Send", priority=True),
        Binding("escape", "browse", "Browse", show=False),
        Binding("ctrl+t", "trees", "Trees", priority=True),
        Binding("ctrl+n", "next_tree", "Next tree", priority=True),  # shown and active in Trees only
        Binding("f1", "help", "Help"),
        Binding("ctrl+q", "quit", "Save & quit", priority=True),
        Binding("left", "earlier", "Earlier"),  # shown and active only when stepping through history
        Binding("right", "later", "Later"),
    ]

    def __init__(self, store, speaker, provider, open_application, consultant_factory, tour=False, story=None,
                 settings=None):
        super().__init__(settings)
        self.store, self.speaker, self.provider, self.tour = str(store), speaker, provider, tour
        # A story is read, not answered: its goal opens read-only with its chapters for narration.
        self.story = story
        self.chapters = {n: c for n, c in enumerate(story["chapters"], start=1)} if story else {}
        # None while looking at the live goal; otherwise the past revision on screen.
        self.revision, self._history = None, None
        self._open, self._consultant_factory = open_application, consultant_factory
        self.case = open_application(consultant_factory(provider))
        self.view_name, self.explain, self.busy, self.answer_ready = "next", False, False, False
        self.workspace_value, self._restoring, self._save_timer = None, False, None
        # Which tree the Trees view shows: one of TREE_ORDER, "all", or None until first chosen.
        self.tree_choice = None

    # ----- layout -------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Static(id="status")
        yield Static(id="pinned")
        yield Static(id="loop")
        with Horizontal(id="body"):
            yield OptionList(*[Option(label, id=key) for key, label in VIEW_LABELS], id="views")
            with VerticalScroll(id="main"):
                yield Markdown(id="content")
                yield Static(id="canvas")
                yield OptionList(id="timeline", classes="hidden")
        yield Static(id="coach", classes="" if self.tour else "hidden")
        story_only = "story-only" + ("" if self.story else " hidden")
        with Vertical(id="moment", classes="" if self.story else "hidden"):
            yield Static(id="moment-text")
            with Horizontal(id="moment-controls"):
                yield Button("◀ Earlier", id="earlier")
                yield Button("Later ▶", id="later")
                yield Button("Back to now", id="now")
                yield Button("From the beginning", id="first", classes=story_only)
                yield Button("Start my own goal", id="own", classes=story_only)
                yield Button("Back to start", id="home", classes=story_only)
        with Vertical(id="response", classes="hidden" if self.story else ""):
            yield TextArea("", id="editor", soft_wrap=True, show_line_numbers=False, tab_behavior="focus")
            with Horizontal(id="controls"):
                yield Button("Send", id="send", variant="primary")
                yield Button("Example answer", id="fill", classes="" if self.tour else "hidden")
                yield Button("Retry", id="retry", variant="warning", classes="hidden")
                yield Button("Explain this", id="explain")
                yield Button("Other moves", id="moves")
                yield Button("Views", id="views-button")
                yield Button("Actions", id="actions")
                yield Button("Finish tour", id="finish", variant="success", classes="" if self.tour else "hidden")
        yield Footer()

    def on_mount(self):
        super().on_mount()
        self.title = "Reason Commons"
        # The trees are drawn in the theme's colours, so they are redrawn with it.
        self.theme_changed_signal.subscribe(self, lambda _: self.workspace_value and self.render_all())
        cursor = self.case.inspect()["cursor"] or {}
        self.refresh_workspace()
        if cursor.get("draft"):
            self._restoring = True
            editor = self.query_one("#editor", TextArea)
            editor.load_text(cursor["draft"])
            editor.cursor_location = caret_location(cursor["draft"], cursor.get("caret", len(cursor["draft"])))
            self._restoring = False
        if (cursor.get("display") or {}).get("tree") in TREE_ORDER + ["all"]:
            self.tree_choice = cursor["display"]["tree"]
        if cursor.get("view") in dict(VIEW_LABELS) and cursor["view"] != "next":
            self.show_view(cursor["view"])
        self.query_one("#earlier" if self.story else "#editor").focus()
        self.watch(self.screen, "focused", lambda _: self.render_status())
        self.on_resize()

    MOMENT_LABELS = {"earlier": ("◀ Earlier", "◀ Earlier"), "later": ("Later ▶", "Later ▶"),
                     "now": ("Back to now", "Now"), "first": ("From the beginning", "First"),
                     "own": ("Start my own goal", "My own goal"), "home": ("Back to start", "Start screen")}

    def on_resize(self, event=None):
        # The destinations list needs room; without it, the Views button reaches the same views.
        wide = self.size.width >= 100
        for key, labels in self.MOMENT_LABELS.items():
            self.query_one("#" + key, Button).label = labels[not wide]
        self.query_one("#views").set_class(not wide, "hidden")
        self.query_one("#views-button").set_class(wide, "hidden")
        self.query_one("#editor").styles.max_height = 5 if self.size.height < 30 else 10
        if self.workspace_value is not None:  # the band, comparisons and welcome depend on the width
            self.render_all()

    def check_action(self, action, parameters):
        if action == "next_tree":
            return self.view_name == "trees"
        looking_back = getattr(self, "revision", None) is not None
        if action == "send" and (self.story or looking_back):
            return False
        if action == "earlier":
            return bool(self.story or looking_back) and getattr(self, "revision", None) != 0
        if action == "later":
            return looking_back
        return True

    # ----- reading ------------------------------------------------------
    def refresh_workspace(self):
        self.workspace_value = self.case.workspace(view=self.view_name, revision=self.revision)
        self.render_all()

    # ----- history ------------------------------------------------------
    def history(self):
        """Every saved revision with what it changed (cached until the next save)."""
        if self._history is None:
            snapshots = self.case.history()["revisions"]
            sources = self.case.sources()["sources"]
            self._history = {"snapshots": snapshots, "entries": revision_changes(snapshots, sources)}
        return self._history

    def live_revision(self):
        return self.history()["snapshots"][-1]["revision"]

    def viewed_records(self):
        if self.revision is None:
            return self.case.inspect()["case"]["records"]
        return self.history()["snapshots"][self.revision]["records"]

    def when(self, entry):
        chapter = self.chapters.get(entry["revision"], {})
        mark = "≈ " if chapter.get("dated") == "approximate" else ""
        return mark + day(entry["timestamp"])

    def render_status(self):
        """One quiet line: goal, speaker, save state and view, and the control that has focus."""
        w = self.workspace_value
        if w is None:
            return
        state = (f"Asking {self.send_to()}…" if self.busy else "Answer ready" if self.answer_ready else "Saved")
        who = None if self.story else self.speaker  # a story is read, not answered as anyone
        where = dict(VIEW_LABELS)[self.view_name]
        if self.story or self.revision is not None:
            state = "Read-only"
        line = Table.grid(expand=True)
        line.add_column(no_wrap=True, overflow="ellipsis")
        line.add_column(justify="right", no_wrap=True)
        focused = FOCUS_NAMES.get(getattr(self.screen.focused, "id", None), "")
        line.add_row(Text.assemble((w["case_name"], "bold"), f" · {who} · " if who else " · ",
                                   (state, "bold" if self.answer_ready else ""), f" · {where}"),
                     f"Focus: {focused}" if focused else "")
        self.query_one("#status", Static).update(line)

    def send_to(self):
        return SEND_TO.get(self.provider, self.provider)

    def render_all(self):
        w = self.workspace_value
        self.render_status()
        self.refresh_bindings()
        self.query_one("#loop", Static).update(
            "" if w["historical"] or self.story else loop_line(loop_stage(w["question"]), wide=self.size.width >= 100))
        self.query_one("#loop").display = not self.story
        content = self.render_next() if self.view_name == "next" else self.render_view()
        self.query_one("#content", Markdown).update(content)
        drawing = {"trees": self.render_trees, "next": self.render_context,
                   "tests": self.render_tests}.get(self.view_name, lambda: None)()
        canvas = self.query_one("#canvas", Static)
        canvas.set_class(drawing is None, "hidden")
        if drawing is not None:
            canvas.update(drawing)
        # The band never repeats what the view is showing: safeguards move into a comparison.
        self.query_one("#pinned", Static).update(self.band(protect=not self.shows_safeguards()))
        timeline = self.query_one("#timeline", OptionList)
        timeline.set_class(self.view_name != "history", "hidden")
        if self.view_name == "history":
            self.fill_timeline(timeline)
        looking_back = self.revision is not None
        self.query_one("#moment").set_class(not (self.story or looking_back), "hidden")
        self.query_one("#response").set_class(bool(self.story) or looking_back, "hidden")
        if self.story or looking_back:
            self.query_one("#moment-text", Static).update(self.moment_text())
            self.query_one("#later").disabled = not looking_back
            self.query_one("#now").disabled = not looking_back
            self.query_one("#earlier").disabled = self.revision == 0
            self.query_one("#first").disabled = self.revision == 1
        retryable = self.retryable()
        self.query_one("#retry").set_class(not retryable, "hidden")
        if self.tour:
            state = self.tour_state()
            self.query_one("#coach", Static).update(coach_text(state))
            self.query_one("#fill").set_class(state not in EXAMPLE_ANSWERS, "hidden")
        response = self.query_one("#response")
        response.border_title = f"Answer as {escape(self.speaker)}"
        response.border_subtitle = f"Enter adds a line · Send asks {escape(self.send_to())}"

    def tour_state(self):
        return tour_state(self.workspace_value["question"], self.case.inspect()["case"]["records"])

    def pinned_goal(self):
        return latest(self.workspace_value["goals"], "goal")

    def band(self, protect=True):
        """The goal and its safeguards, at most two labelled lines; a cut is marked, and Goal shows it all."""
        goal = self.pinned_goal()
        if goal is None:
            return Text("No goal yet", style="dim")
        width = self.size.width - 11
        grid = Table.grid(padding=(0, 1))
        grid.add_column(style="bold", width=7, no_wrap=True)
        grid.add_column()
        grid.add_row("Goal", Text(clip(goal["data"]["statement"], width, 2 if self.size.height >= 30 else 1)))
        if protect and not self.story:
            protections = " · ".join(goal["data"].get("protections") or []) or "none recorded"
            grid.add_row("Protect", Text(clip(protections, width, 1)))
        upcoming = next_action(self.viewed_records())
        if upcoming and not self.shows_action(upcoming["action"]["ref"]):
            data = upcoming["action"]["data"]
            owner = f" ({data['owner']})" if data.get("owner") else ""
            grid.add_row("Action", Text(clip(data["statement"] + owner, width, 1)))
        return grid

    def shows_action(self, ref):
        """Whether the view on screen already shows this action, so the band need not repeat it."""
        if self.view_name != "next" or self.revision is not None:
            return False
        return bool(self.story) or any(r["ref"] == ref for r in self.workspace_value["records"])

    def pane_width(self):
        main = self.query_one("#main")
        return main.content_size.width or self.size.width - (22 if self.size.width >= 100 else 4)

    def compared(self):
        """The comparisons the current view draws: every test in Tests, tests with results in Next."""
        comparisons = self.workspace_value["comparisons"]
        if self.view_name == "tests":
            return comparisons
        return [c for c in comparisons if c["observations"]] if self.view_name == "next" else []

    def shows_safeguards(self):
        goal = self.pinned_goal()
        return bool(goal and goal["data"].get("protections")) and any(
            c["test"]["data"].get("goal_ref") == goal["ref"] for c in self.compared())

    def retryable(self):
        return [a for a in self.workspace_value["available_actions"] if a["capability"] == "retry"]

    def render_next(self):
        if self.revision is not None:
            return self.render_moment()
        if self.story:
            return self.render_story_now()
        w = self.workspace_value
        lines = []
        if w["question"]:
            data = w["question"]["data"]
            lines += [f"## {md(data.get('decision') or 'Next question')}", "", f"**{md(data['primary_prompt'])}**", ""]
            rationale = data["rationale"]
        else:
            # A new goal: its name is in the header, so the first question builds on it.
            lines += [f"## {md(STEPS['goal'][0])}", "",
                      "**What would count as better? Describe it in your own words.**" if self.provider == "guided"
                      else "**What is happening, and what would count as better?**", "",
                      "Your words are kept as written. Unknowns can stay open. Nothing is sent until you press "
                      "Send.", ""]
            rationale = (STEPS["goal"][2] if self.provider == "guided"
                         else "A clear picture of success comes before choosing what to change.")
        if self.explain:
            lines += ["> **Why this question** (saved explanation, no consultant call)", ">",
                      "> " + md(rationale), ""]
            if not w["question"]:
                lines += ["How one loop works, one small change at a time:", "",
                          WELCOME_WIDE if self.size.width >= 100 else WELCOME_NARROW,
                          "*This shows how one loop works, not what causes what.*", ""]
        for pending in w["pending_requests"]:
            value = pending["input"]
            if value["base_revision"] == w["revision"] and value["response_target"] == w["target"]["response_target"]:
                lines += [f"> **Saved, but not answered yet:** {STATUS_TEXT.get(pending['status'], pending['status'])}. "
                          "Your words are kept. Use **Retry** to ask again.", ">", "> " + md(value["text"]), ""]
        return "\n".join(lines)

    def render_context(self):
        """What the current question builds on, below it: each forecast beside its results first,
        then the other records the consultant attached, leaving out what the band shows."""
        if self.revision is not None:
            return None
        if self.story:
            return self.story_rows()
        w = self.workspace_value
        compared = self.compared()
        drawn = {r["ref"] for c in compared for r in [c["test"], *c["observations"], *c["reviews"]]}
        parts = [comparison_block(w, c, self.pane_width() >= WIDE) for c in compared]
        rows = Table.grid(padding=(0, 2))
        rows.add_column(style="bold dim", max_width=24)
        rows.add_column()
        pinned = (self.pinned_goal() or {}).get("ref")
        measures = {f.get("measure") for c in compared for f in c["test"]["data"].get("forecast") or []}
        for record in w["records"]:
            if record["kind"] != "intervention" and record["ref"] not in drawn:
                for name, value in context_rows(w, record, pinned):
                    if not (name == "Measure" and value in measures):  # already above, with its forecast
                        rows.add_row(name, Text(str(value)))
        if rows.row_count:
            parts += [Text("")] * bool(parts) + [rows]
        return Group(*parts) if parts else None

    def render_tests(self):
        comparisons = list(reversed(self.compared()))
        wide = self.pane_width() >= WIDE
        return Group(*[part for index, c in enumerate(comparisons)
                       for part in [Text("")] * bool(index) + [comparison_block(self.workspace_value, c, wide)]]
                     ) if comparisons else None

    def record_lines(self, record):
        rows = context_rows(self.workspace_value, record, None)
        return [f"**{md(name)}:** {md(value)}  " for name, value in rows] + [""]

    def render_view(self):
        w, view = self.workspace_value, self.view_name
        title = dict(VIEW_LABELS)[view]
        lines = [f"## {title}", ""]
        if view == "history":
            lines.append("Every saved step, oldest first: when, who, and what changed. "
                         "Tab to the list, arrows choose, Enter opens that moment; nothing there can be changed.")
            return "\n".join(lines)
        if view == "sources":
            sources = [s for s in w["sources"].values() if "request_id" in s]
            for source in sorted(sources, key=lambda s: s["request_id"], reverse=True):
                lines += [f"**{md(source['speaker'])}** | {md(source['timestamp'])} | {source['request_id']}", "",
                          "> " + md(source["text"] or "(empty)").replace("\n", "  \n> "), ""]
            return "\n".join(lines) if sources else "\n".join(lines + ["Nothing written yet."])
        if view == "trees":
            if not any(t["claims"] for t in w["trees"]):
                if self.provider == "guided":
                    lines.append("No trees yet. The built-in guide asks the loop's questions in order; it does "
                                 "not add to the trees. To grow them as you talk, switch to Claude or a local "
                                 "model: Ctrl+P, **Consultant**. Or bring in trees you already have: Ctrl+P, "
                                 "**Import trees**.")
                else:
                    lines.append("No trees yet. They grow as you talk: tell the consultant what causes the problem, "
                                 "what conflict keeps you stuck, what stands in the way, or what you plan to do. "
                                 "Or bring in trees you already have: Ctrl+P, **Import trees**.")
            else:
                shown = self.shown_tree()
                tabs = []
                for tree in w["trees"]:
                    name = f"{TREE_TITLES[tree['tree']][0]} ({len(tree['claims'])})"
                    tabs.append(f"**▸ {name}**" if tree["tree"] == shown else name)
                tabs.append("**▸ All six**" if shown == "all" else "All six")
                lines += [" · ".join(tabs)]
            return "\n".join(lines)
        if view == "tests":
            if not w["comparisons"]:
                lines.append("No test yet.")
            return "\n".join(lines)
        records = [r for r in w["records"] if r["kind"] != "intervention"]
        if not records:
            lines.append("Nothing recorded here yet.")
        for record in records:
            lines += self.record_lines(record)
        if view == "reasoning" and w["uncertainty"]:
            lines += ["### Still open", ""] + [f"- {md(u['message'])}" for u in w["uncertainty"]]
        return "\n".join(lines)

    def render_trees(self):
        """The six trees, drawn from the recorded claims and links, coloured by role."""
        width = max(40, self.query_one("#main").size.width - 6)
        text = Text()
        shown = self.shown_tree()
        fresh = self.history()["entries"][self.revision]["fresh"] if self.revision is not None else ()
        for line in trees_lines(self.workspace_value["trees"], width, only=None if shown == "all" else shown,
                                fresh=fresh):
            for part, style in line:
                text.append(part, style=themed(style, self.theme_variables) or None)
            text.append("\n")
        return text

    # ----- looking back -------------------------------------------------
    def fill_timeline(self, timeline):
        entries = self.history()["entries"]
        options = []
        for entry in entries:
            if entry["revision"] == 0:
                label = Text(f"{self.when(entry)}  ·  The goal was created", style="dim")
            else:
                label = Text()
                label.append(f"{self.when(entry)}  ·  {entry['speaker'] or 'unknown'}  ·  ", style="dim")
                label.append(self.step_title(entry))
                label.append("\n   " + change_summary(entry["counts"]), style="dim")
            if entry["revision"] == len(entries) - 1:
                label.append("   ● now", style="dim")
            options.append(Option(label, id=str(entry["revision"])))
        current = timeline.highlighted
        timeline.clear_options()
        timeline.add_options(options)
        timeline.highlighted = current if current is not None and current < len(options) else (
            self.revision if self.revision is not None else len(options) - 1)

    def step_title(self, entry):
        """A story chapter's title, else the question this step answered."""
        chapter = self.chapters.get(entry["revision"], {})
        return chapter.get("title") or entry.get("answered") or entry["decision"] or "Saved"

    def moment_text(self):
        """Where in the history the screen is: one muted line; the step itself is in the reading pane."""
        entries = self.history()["entries"]
        live = len(entries) - 1
        if self.revision is None:
            first = entries[1] if live else entries[0]
            return Text.assemble(("Now", "bold"), f"  ·  {live} steps since {day(first['timestamp'])}  ·  "
                                 "← steps back through how it got here")
        entry = entries[self.revision]
        return Text.assemble((f"Step {self.revision} of {live}", "bold"),
                             f"  ·  {self.when(entry)}" + (f"  ·  {entry['speaker']}" if entry["speaker"] else ""))

    def render_moment(self):
        """One past step: what it was called, the editor's narration, the words, and what changed."""
        history = self.history()
        entry = history["entries"][self.revision]
        chapter = self.chapters.get(self.revision, {})
        if self.revision == 0:
            return "## The goal was created\n\nNothing had been recorded yet."
        lines = [f"## {md(self.step_title(entry))}", ""]
        if chapter.get("summary"):
            lines += [f"*{md(' '.join(chapter['summary'].split()))}*", ""]
        elif entry.get("asked"):
            lines += [md(entry["asked"]), ""]  # the question these words answered
        paragraphs = [md(part).replace("\n", "  \n> ") for part in (entry["text"] or "").split("\n\n")]
        lines += ["> " + "\n>\n> ".join(paragraphs), ""]
        notes = [chapter[key] for key in ("words_note",) if chapter.get(key)]
        if chapter.get("source"):
            notes.append(f"Source: {chapter['source']}")
        if notes:
            lines += [f"*{md(' · '.join(notes))}*", ""]
        lines += ["### What changed", "", change_summary(entry["counts"]), ""]
        before = {r["ref"]: r for r in history["snapshots"][self.revision - 1]["records"]}
        now = history["snapshots"][self.revision]["records"]
        everything = {**before, **{r["ref"]: r for r in now}}
        for record in (r for r in now if r["ref"] not in before):
            data = record["data"]
            if record["kind"] == "claim":
                where = f"{TREE_TITLES[data['tree']][0]}, {ROLE_LABELS[data['role']].lower()}"
                if data.get("replaces"):
                    old = everything[data["replaces"]]["data"]["statement"]
                    lines.append(f"- *Reworded, {md(where)}:* {md(data['statement'])}  \n  *was:* {md(old)}")
                else:
                    lines.append(f"- *{md(where)}:* {md(data['statement'])}")
            elif record["kind"] == "retraction":
                target = everything.get(data["target_ref"], {}).get("data", {})
                lines.append(f"- *Withdrawn:* {md(target.get('statement') or data['target_ref'])}  \n"
                             f"  *why:* {md(data['reason'])}")
            elif record["kind"] == "goal":
                lines.append(f"- *Goal:* {md(data['statement'])}" +
                             (f"  \n  *measure:* {md(data['measure'])}" if data.get("measure") else ""))
            elif record["kind"] == "test":
                forecast = "; ".join(f.get("expected") or "" for f in data.get("forecast") or [])
                lines.append(f"- *Test:* {md(data['statement'])}  \n  *forecast, written first:* {md(forecast)}")
            elif record["kind"] == "action":
                lines.append(f"- *Action planned:* {md(data['statement'])}")
            elif record["kind"] == "note":
                lines.append(f"- *Note:* {md(data['text'])}")
        question = (self.workspace_value["question"] or {}).get("data", {})
        if question.get("primary_prompt"):
            lines += ["", "### Asked next", "", md(question["primary_prompt"])]
        return "\n".join(lines)

    def render_story_now(self):
        """The decision the story is waiting on leads; the action's details follow as rows."""
        question = (self.workspace_value["question"] or {}).get("data", {})
        lines = ["## The next action", ""]
        if question.get("primary_prompt"):
            lines += [f"**{md(question['primary_prompt'])}**", ""]
        return "\n".join(lines)

    def story_rows(self):
        """The open action as label/value rows, then how the story got here, in muted text."""
        upcoming = next_action(self.viewed_records())
        rows = Table.grid(padding=(0, 2))
        rows.add_column(style="bold dim", max_width=24)
        rows.add_column()
        if upcoming:
            action, test, claim = upcoming["action"]["data"], (upcoming["test"] or {}).get("data", {}), upcoming["claim"]
            rows.add_row("Action", Text(action["statement"]))
            if action.get("owner"):
                rows.add_row("Owner", Text(action["owner"]))
            if claim:
                rows.add_row("Carries out", Text(f"{claim['data']['statement']} "
                                                 f"({TREE_TITLES[claim['data']['tree']][0]})"))
            for forecast in test.get("forecast") or []:
                rows.add_row("Expect to see", Text(forecast.get("expected") or "not stated"))
            if test.get("stop_condition"):
                rows.add_row("Stop if", Text(test["stop_condition"]))
        question = (self.workspace_value["question"] or {}).get("data", {})
        if question.get("rationale"):
            rows.add_row("Why now", Text(question["rationale"]))
        entries = self.history()["entries"]
        speakers = len({e["speaker"] for e in entries if e["speaker"]})
        how = (f"How it got here: {len(entries) - 1} steps by {speakers} people, from "
               f"{day(entries[1]['timestamp']) if len(entries) > 1 else ''} to {day(entries[-1]['timestamp'])}. "
               f"{' '.join(self.story['intro'].split())} {' '.join(self.story['fidelity'].split())} "
               "Italic narration is the editor's. ◀ Earlier steps back; History lists every step; Ctrl+T shows the "
               "trees as they stand now.")
        return Group(rows, Text(""), Text(how, style="dim"))

    def go_to(self, revision):
        """Show a past revision, or the live goal with None."""
        live = self.live_revision()
        if revision is not None and (revision >= live or revision < 0):
            revision = None if revision >= live else 0
        self.revision = revision
        self.refresh_workspace()
        self.query_one("#main").scroll_home(animate=False)

    def action_earlier(self):
        if self.story or self.revision is not None:
            current = self.live_revision() if self.revision is None else self.revision
            if current > 0:
                self.go_to(current - 1)

    def action_later(self):
        if self.revision is not None:
            self.go_to(self.revision + 1)

    @on(Button.Pressed, "#earlier")
    def earlier_pressed(self):
        self.action_earlier()

    @on(Button.Pressed, "#later")
    def later_pressed(self):
        self.action_later()

    @on(Button.Pressed, "#now")
    def now_pressed(self):
        self.go_to(None)

    @on(Button.Pressed, "#first")
    def first_pressed(self):
        self.go_to(1)

    @on(Button.Pressed, "#own")
    def own_pressed(self):
        self.exit(STORY_OWN_GOAL)

    @on(Button.Pressed, "#home")
    def home_pressed(self):
        self.exit(STORY_HOME)

    @on(OptionList.OptionSelected, "#timeline")
    def moment_selected(self, event):
        self.revision = int(event.option.id)  # set first, so the step page opens directly
        self.show_view("next")

    def shown_tree(self):
        """The tree on screen: the last one chosen, else the first that has statements."""
        if self.tree_choice:
            return self.tree_choice
        trees = (self.workspace_value or {}).get("trees") or []
        return next((t["tree"] for t in trees if t["claims"]), TREE_ORDER[0])

    def show_view(self, name):
        self.view_name = name
        self.answer_ready = self.answer_ready and name != "next"
        views = self.query_one("#views", OptionList)
        views.highlighted = [key for key, _ in VIEW_LABELS].index(name)
        self.refresh_workspace()
        self.query_one("#main").scroll_home(animate=False)
        self.schedule_checkpoint()

    # ----- events -------------------------------------------------------
    @on(OptionList.OptionSelected, "#views")
    def view_selected(self, event):
        self.show_view(event.option.id)

    @on(Button.Pressed, "#send")
    def send_pressed(self):
        self.action_send()

    @on(Button.Pressed, "#fill")
    def fill_pressed(self):
        """Tour only: put the tutorial's example answer for this question into the editor."""
        answer = EXAMPLE_ANSWERS.get(self.tour_state())
        if answer is not None:
            editor = self.query_one("#editor", TextArea)
            editor.load_text(answer)
            editor.cursor_location = caret_location(answer, len(answer))
            editor.focus()

    @on(Button.Pressed, "#finish")
    def finish_pressed(self):
        self.exit(TOUR_FINISHED)

    @on(Button.Pressed, "#retry")
    def retry_pressed(self):
        self.action_retry()

    @on(Button.Pressed, "#explain")
    def explain_pressed(self):
        self.action_explain()

    @on(Button.Pressed, "#moves")
    def moves_pressed(self):
        self.action_other_moves()

    @on(Button.Pressed, "#views-button")
    def views_pressed(self):
        self.push_screen(ChoiceScreen("Views (local, no consultant call)", VIEW_LABELS),
                         lambda choice: choice and self.show_view(choice))

    @on(Button.Pressed, "#actions")
    def actions_pressed(self):
        self.action_command_palette()

    @on(TextArea.Changed, "#editor")
    def draft_changed(self):
        if not self._restoring:
            self.schedule_checkpoint()

    # ----- actions ------------------------------------------------------
    def action_browse(self):
        self.query_one("#main").focus()

    def action_help(self):
        self.push_screen(HelpScreen())

    def show_tree(self, key):
        self.tree_choice = key
        self.show_view("trees")

    def action_trees(self):
        """Ctrl+T: open the Trees view, or go back to the current question from it."""
        self.show_view("next" if self.view_name == "trees" else "trees")

    def action_next_tree(self):
        """Ctrl+N: show the next tree (the six in turn, then all six together)."""
        if self.view_name == "trees":
            order = TREE_ORDER + ["all"]
            self.tree_choice = order[(order.index(self.shown_tree()) + 1) % len(order)]
        self.show_view("trees")

    def action_explain(self):
        self.explain = not self.explain
        self.show_view("next")

    def action_other_moves(self):
        options = [("explain", "Understand why this question     LOCAL"),
                   ("goal", "Inspect goal and safeguards      LOCAL"),
                   ("direct_advice", "Give me direct advice            ASKS CONSULTANT"),
                   ("another_question", "Ask me a different question      ASKS CONSULTANT"),
                   ("explain_observation", "Help me plan an observation      ASKS CONSULTANT")]

        def chosen(choice):
            if choice == "explain":
                self.explain = True
                self.show_view("next")
            elif choice == "goal":
                self.show_view("goal")
            elif choice:
                self.action_send(intent=choice)
        self.push_screen(ChoiceScreen("Other moves. Nothing is sent until you choose an item.", options), chosen)

    def action_send(self, intent="answer"):
        if self.story or self.revision is not None:
            self.notify("This is a record of what happened; nothing here can be changed. "
                        + ("Start your own goal to write." if self.story else "Back to now to answer."))
            return
        if self.busy:
            self.notify("Still waiting for the consultant. You can keep browsing.")
            return
        w = self.workspace_value
        if w["historical"]:
            return
        text = self.query_one("#editor", TextArea).text
        if not text.strip() and self.provider != "guided" and intent == "answer":
            self.notify("Write an answer first.", severity="warning")
            return
        self.set_busy(True)
        target = w["target"]
        self.run_worker(lambda: self._submit(text, intent, target), thread=True, exclusive=True)

    def _submit(self, text, intent, target):
        try:
            result = self.case.retain_input(text, self.speaker, target["base_revision"],
                                            target["response_target"], intent=intent)
            if result["status"] == "input_retained":
                result = self.case.consult(result["request_id"])
        except Exception as exc:  # keep the draft; report the category only
            result = {"status": "not_saved", "message": f"Not saved ({type(exc).__name__})."}
        self.call_from_thread(self._submitted, result, text)

    def action_retry(self):
        actions = self.retryable()
        if self.busy or not actions:
            return
        self.set_busy(True)
        request_id = actions[-1]["arguments"]["request_id"]

        def work():
            try:
                result = self.case.retry(request_id)
            except Exception as exc:
                result = {"status": "not_saved", "message": f"Not saved ({type(exc).__name__})."}
            self.call_from_thread(self._submitted, result, None)
        self.run_worker(work, thread=True, exclusive=True)

    def _submitted(self, result, text):
        self.set_busy(False, refresh=False)
        self._history = None
        editor = self.query_one("#editor", TextArea)
        status = result["status"]
        sent = text is not None and editor.text == text
        if status == "saved":
            if sent:
                editor.clear()
            self.explain = False
            # Never move the person: a reply that arrives while they browse waits on Next step.
            self.answer_ready = self.view_name != "next"
            self.notify("Answer ready: Next step shows the new question." if self.answer_ready else "Saved.")
        elif result.get("input_retained"):
            if sent:
                editor.clear()  # the words are retained in the case; Retry reuses them
            self.notify(result.get("message", status) + ". Use Retry when the consultant is reachable.",
                        severity="warning", timeout=8)
        else:
            self.notify(result.get("message", status) + " Your text is still in the editor.",
                        severity="error", timeout=8)
        self.refresh_workspace()
        self.checkpoint()

    def set_busy(self, busy, refresh=True):
        self.busy = busy
        for name in ("#send", "#retry", "#moves"):
            self.query_one(name).disabled = busy
        if refresh:
            self.render_all()

    # ----- persistence of view and draft ---------------------------------
    def schedule_checkpoint(self):
        if self._save_timer is not None:
            self._save_timer.stop()
        self._save_timer = self.set_timer(0.8, self.checkpoint)

    def checkpoint(self):
        if self.busy or self.workspace_value is None or self.story or self.revision is not None:
            return
        editor = self.query_one("#editor", TextArea)
        draft = editor.text
        target = self.workspace_value["target"]
        try:
            result = self.case.checkpoint({
                "view": self.view_name, "focus": "response" if editor.has_focus else "browse",
                "draft": draft, "caret": caret_index(draft, editor.cursor_location), "speaker": self.speaker,
                "response_target": target["response_target"], "base_revision": target["base_revision"],
                "display": {"tree": self.shown_tree()}})
        except Exception:
            return
        if result["status"] != "saved":
            self.notify("Draft not saved to disk. Copy your text somewhere safe.", severity="error")

    async def action_quit(self):
        if not self.busy:
            self.checkpoint()
        self.exit()

    # ----- Actions palette (Ctrl+P) ---------------------------------------
    def get_system_commands(self, screen):
        yield SystemCommand("Send answer", "Send your answer to the consultant (Ctrl+S)", self.action_send)
        if self.retryable():
            yield SystemCommand("Retry", "Ask the consultant again with your saved answer", self.action_retry)
        yield SystemCommand("Explain this question", "Show the saved explanation (local)", self.action_explain)
        yield SystemCommand("Other moves", "Advice, a different question, or local explanations",
                            self.action_other_moves)
        for key, label in VIEW_LABELS:
            yield SystemCommand(f"View: {label}", "Local view, no consultant call",
                                lambda key=key: self.show_view(key))
        for key in TREE_ORDER + ["all"]:
            label = TREE_TITLES[key][0] if key in TREE_TITLES else "All six trees"
            yield SystemCommand(f"Tree: {label}", "Show this tree in the Trees view (Ctrl+N cycles)",
                                lambda key=key: self.show_tree(key))
        yield SystemCommand("History: step back", "Show the goal as it was one step earlier (←)", self.action_earlier)
        if self.revision is not None:
            yield SystemCommand("History: step forward", "One step later (→)", self.action_later)
            yield SystemCommand("History: back to now", "Return to the goal as it is now", lambda: self.go_to(None))
        yield SystemCommand("Export case", "Write a portable .reasoncase copy", self.action_export)
        yield SystemCommand("Import trees", "Bring in trees from an .ltp.yaml file", self.action_import_trees)
        yield SystemCommand("Export trees", "Write the trees to an .ltp.yaml file", self.action_export_trees)
        for key, label in PROVIDERS.items():
            if key != self.provider:
                yield SystemCommand(f"Consultant: {label}", "Use this consultant from now on",
                                    lambda key=key: self.switch_provider(key))
        yield SystemCommand("Theme", f"How Reason Commons looks; now {themes.title(self.theme)}",
                            self.action_change_theme)
        yield SystemCommand("Help", "Keys and how the loop works (F1)", self.action_help)
        yield SystemCommand("Save and quit", "Keep your draft and close (Ctrl+Q)", self.action_quit)

    def action_export(self):
        default = str(Path(self.store).with_name(f"{Path(self.store).name}-{date.today().isoformat()}.reasoncase"))

        def chosen(destination):
            if not destination:
                return
            try:
                self.case.export(os.path.expanduser(destination))
                self.notify(f"Exported to {destination}")
            except Exception as exc:
                self.notify(f"Export failed: {exc}", severity="error", timeout=8)
        self.push_screen(ExportScreen(default), chosen)

    def action_import_trees(self):
        if self.busy:
            self.notify("Wait for the current request to finish.")
            return

        def chosen(path):
            if not path:
                return
            from reason_commons.adapters.ltp_trees import import_trees
            self.checkpoint()
            self.case.close()
            try:
                summary = import_trees(self.store, os.path.expanduser(path), self.speaker)
                self.notify(f"Brought in {summary['claims']} statements and {summary['links']} links." +
                            (f" {summary['notes']} items the trees cannot draw are kept as notes."
                             if summary["notes"] else ""), timeout=8)
            except Exception as exc:
                self.notify(f"Import failed: {exc}", severity="error", timeout=10)
            finally:
                self.case = self._open(self._consultant_factory(self.provider))
            self.show_view("trees")
        self.push_screen(PathScreen("Bring in trees from an LTP file (.ltp.yaml)", "",
                                    "Enter imports. They join the trees already here. Esc cancels."), chosen)

    def action_export_trees(self):
        default = str(Path(self.store).with_name(f"{Path(self.store).name}-trees-{date.today().isoformat()}.ltp.yaml"))

        def chosen(destination):
            if not destination:
                return
            from reason_commons.adapters.ltp_trees import export_trees
            try:
                summary = export_trees(self.case.workspace(view="trees"), os.path.expanduser(destination))
                self.notify(f"Wrote {summary['claims']} statements and {summary['links']} links to {destination}")
            except Exception as exc:
                self.notify(f"Export failed: {exc}", severity="error", timeout=8)
        self.push_screen(PathScreen("Write the trees to an LTP file (.ltp.yaml)", default,
                                    "Enter writes. Use a new file name. Esc cancels."), chosen)

    def switch_provider(self, provider):
        if self.busy:
            self.notify("Wait for the current request to finish.")
            return
        try:
            consultant = self._consultant_factory(provider)
        except Exception as exc:
            self.notify(f"Could not set up {PROVIDERS[provider]}: {exc}", severity="error", timeout=8)
            return
        if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
            self.notify("No Anthropic key yet, so requests will fail. Add one under Settings on the home "
                        "screen, or set ANTHROPIC_API_KEY.",
                        severity="warning", timeout=10)
        self.checkpoint()
        self.case.close()
        self.case = self._open(consultant)
        self.provider = provider
        self.refresh_workspace()
        self.notify(f"Consultant: {PROVIDERS[provider]}")

    def on_unmount(self):
        self.case.close()


def goals_home():
    """The folder that holds your goals: REASON_COMMONS_HOME, otherwise ~/ReasonCommons."""
    return Path(os.path.expanduser(os.environ.get("REASON_COMMONS_HOME") or "~/ReasonCommons")).resolve()


def find_goals(root):
    """Case folders directly under root, most recently changed first. Unreadable folders are skipped."""
    from reason_commons.bootstrap import open_case
    goals = []
    for path in sorted(Path(root).iterdir()) if Path(root).is_dir() else []:
        if not path.is_dir() or path.name.startswith(".") or path.name == "exports":
            continue
        try:
            with open_case(path, writable=False) as app:
                case = app.inspect()["case"]
                question = (app.workspace()["question"] or {}).get("data", {})
        except Exception:
            continue
        goals.append({"path": path, "name": case["name"], "changed": case["timestamp"],
                      "step": question.get("decision") or "Start"})
    return sorted(goals, key=lambda goal: goal["changed"], reverse=True)


def goal_folder(root, name):
    """A new folder name for a goal: letters, digits and hyphens, unique under root."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60].strip("-") or "goal"
    if slug == "exports":
        slug = "exports-goal"
    candidate, number = Path(root) / slug, 2
    while candidate.exists():
        candidate, number = Path(root) / f"{slug}-{number}", number + 1
    return candidate


class NewGoalScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Back")]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Name this goal", classes="dialog-title")
            yield Input(placeholder="for example: A clear next step after open evenings", id="goal-name")
            yield Label("A few words is enough. Next you describe what would count as better. "
                        "Enter starts, Esc goes back.", classes="hint")

    @on(Input.Submitted)
    def submitted(self, event):
        self.dismiss(event.value.strip() or None)


class GoalsApp(ThemedApp):
    """Home screen: how to begin on first start, then your goals. Returns what to open next.

    With ``settings`` that were never saved, it first offers the ways to start: set up and
    start a goal, the guided tour, the real commons, or skipping setup.
    """

    TITLE = "Reason Commons"
    ENABLE_COMMAND_PALETTE = False
    CSS = ReasonCommonsApp.CSS + """
    #home { padding: 1 2; }
    #home-title { text-style: bold; color: $accent; }
    #home-intro { margin: 1 0; }
    #goals { height: auto; max-height: 1fr; border: $frame $accent; }
    """
    BINDINGS = [Binding("ctrl+q", "quit", "Quit", priority=True), Binding("f1", "help", "Help")]

    def __init__(self, root, list_goals=find_goals, create=None, settings=None, checks=None, start_new=False):
        super().__init__(settings)
        self.root, self._list, self.start_new = Path(root), list_goals, start_new
        self._create = create or self._create_case
        self._checks = checks
        self.goals = []

    @property
    def first_run(self):
        return self.settings is not None and not self.settings.exists

    def compose(self) -> ComposeResult:
        with Vertical(id="home"):
            yield Static("Reason Commons", id="home-title")
            yield Static(id="home-intro")
            yield OptionList(id="goals")
            yield Label("Arrows choose, Enter opens. F1 explains the loop. Ctrl+Q quits.", classes="hint")
        yield Footer()

    def on_mount(self):
        super().on_mount()
        self.goals = self._list(self.root)
        self.show_options()
        if self.start_new:
            self.new_goal()

    def show_options(self):
        loop = "goal → test with a forecast → action → observation → review"
        goals = self.query_one("#goals", OptionList)
        goals.clear_options()
        if self.first_run:
            intro = ("[b]Welcome.[/b] Reason Commons helps you make progress on something that matters, one small "
                     f"loop at a time: {loop}.\n\nHow would you like to start? Everything stays on this computer.")
            options = [Option(option_label("Start my first goal",
                                           f"The offline guide asks the questions; your answers are saved as "
                                           f"{login_name() or 'Me'}. Change either later in Settings."), id="start"),
                       Option(option_label("Choose who asks the questions first",
                                           "Your name, and the offline guide, Claude or a local model. About a "
                                           "minute."), id="setup"),
                       Option(option_label("Take the guided tour",
                                           "Practise one whole loop with example answers. About 5 minutes; "
                                           "nothing is kept."), id="tour"),
                       Option(option_label("Explore a real commons",
                                           "How the Second Renaissance's shared reasoning grew, step by step, "
                                           "and the one action it says comes next."), id="sample")]
            highlighted = 0
        else:
            intro = f"Make progress on a goal that matters, one small loop at a time: {loop}."
            if not self.goals:
                intro += "\n\nYou have no goals yet. Start one below; it is saved as you go."
            options = [Option("+ Start a new goal", id="new"),
                       Option("  Explore a real commons: the Second Renaissance, step by step", id="sample"),
                       Option("  Take the guided tour (practice goal, about 5 minutes)", id="tour")]
            if self.settings is not None:
                options.append(Option(f"  Settings: {escape(describe(self.settings))}", id="settings"))
            options.append(Option(f"  Theme: {escape(themes.title(self.theme))}", id="theme"))
            highlighted = len(options) if self.goals else 0
            for index, goal in enumerate(self.goals):
                label = f"{goal['name']}   ·   {goal['step']}   ·   {str(goal['changed'])[:10]}"
                options.append(Option(escape(label), id=str(index)))
        self.query_one("#home-intro", Static).update(intro)
        goals.add_options(options)
        goals.highlighted = highlighted
        goals.focus()

    @on(OptionList.OptionSelected, "#goals")
    def chosen(self, event):
        choice = event.option.id
        if choice in (SAMPLE, TOUR):
            self.exit(choice)
        elif choice in ("setup", "settings"):
            self.setup(first_run=choice == "setup")
        elif choice == "theme":
            self.action_change_theme()
        elif choice == "start":
            # The defaults setup would offer; the next screen names the goal.
            self.settings.set(self.settings.get("name") or login_name() or "Me", "name")
            self.settings.set("guided", "consultant")
            try:
                self.settings.save()
            except OSError as exc:
                self.notify(f"Could not save your settings ({exc}).", severity="error", timeout=8)
            self.settings.apply()
            self.show_options()
            self.new_goal()
        elif choice == "new":
            self.new_goal()
        else:
            self.exit(self.goals[int(choice)]["path"])

    @work
    async def setup(self, first_run):
        then = await run_setup(self, self.settings, first_run, checks=self._checks)
        if then in (SAMPLE, TOUR):
            self.exit(then)
        elif then == "goal":
            self.show_options()
            self.new_goal()
        else:
            self.show_options()

    def new_goal(self):
        def named(name):
            if name:
                try:
                    self.exit(self._create(name))
                except Exception as exc:
                    self.notify(f"Could not start the goal: {exc}", severity="error", timeout=8)
        self.push_screen(NewGoalScreen(), named)

    def _create_case(self, name):
        from reason_commons.bootstrap import create_case
        self.root.mkdir(parents=True, exist_ok=True)
        path = goal_folder(self.root, name)
        create_case(path, name).close()
        return path

    def action_help(self):
        self.push_screen(HelpScreen())

    def keep_theme(self, name):
        super().keep_theme(name)
        if name and not self.first_run:  # the first-start menu has no Theme row
            self.show_options()
            goals = self.query_one("#goals", OptionList)
            goals.highlighted = goals.get_option_index("theme")


def themed(style, variables):
    """A drawing style with its colour families (``$hand``, ``$disagreed`` …) in the current theme's colours.

    A family colour replaces ``dim``: each is chosen to stay readable on the ground, and dimming would undo that.
    """
    words = style.split()
    if any(word.startswith("$") for word in words):
        words = [variables.get(word[1:], "") if word.startswith("$") else word for word in words if word != "dim"]
    return " ".join(words)


def option_label(title, detail):
    text = Text(title, style="bold")
    text.append("\n" + detail, style="dim")
    return text


SAMPLE = "sample"
TOUR = "tour"


def run_home(speaker=None, provider=None, model=None, base_url=None, settings=None):
    """First start or your goals, then the chosen goal (or the tour or example) in the workspace.

    The tour returns here when finished; quitting any workspace ends the program.
    """
    options = {"speaker": speaker, "provider": provider, "model": model, "base_url": base_url}
    settings = settings or Settings.load()
    settings.apply()
    start_new = False
    while True:
        store = GoalsApp(goals_home(), settings=settings, start_new=start_new).run()
        start_new = False
        if store == TOUR:
            if run_tour(speaker) != TOUR_FINISHED:
                return
        elif store == SAMPLE:
            outcome = run_story()
            if outcome == STORY_OWN_GOAL:
                start_new = True
                continue
            if outcome != STORY_HOME:
                return
        elif store is not None:
            run(store, **options)
            return
        else:
            return


STORY_ARCHIVE = "stories/second-renaissance.reasoncase"


def run_story():
    """The example: a real commons opened read-only from its packaged history."""
    from importlib.resources import as_file, files
    from reason_commons.adapters.story import load_story
    from reason_commons.bootstrap import import_case
    with tempfile.TemporaryDirectory(prefix="reason-commons-story-") as folder:
        with as_file(files("reason_commons.adapters").joinpath(STORY_ARCHIVE)) as archive:
            import_case(str(archive), str(Path(folder) / "story")).close()
        return run(Path(folder) / "story", provider="guided", story=load_story())


def run_tour(speaker=None):
    """The guided tour: a practice goal in a throwaway folder, always with the offline guide."""
    with tempfile.TemporaryDirectory(prefix="reason-commons-tour-") as folder:
        return run(Path(folder) / "practice", name="Practice: your first loop", speaker=speaker,
                   provider="guided", tour=True)


def run(store, name=None, speaker=None, provider=None, model=None, base_url=None, tour=False, story=None):
    """Create the case if the folder does not exist yet, then open the workspace."""
    from reason_commons.bootstrap import configured_consultant, create_case, open_case
    settings = Settings.load()
    settings.apply()  # fills in only what flags and the environment leave unset
    store = Path(os.path.expanduser(store)).resolve()
    provider = provider or os.environ.get("REASON_COMMONS_PROVIDER") or "guided"
    speaker = speaker or os.environ.get("REASON_COMMONS_SPEAKER") or os.environ.get("USER") or "Me"
    factory = lambda chosen: configured_consultant(provider=chosen, model=model if chosen == provider else None,
                                                   base_url=base_url if chosen == provider else None)
    if not store.exists():
        store.parent.mkdir(parents=True, exist_ok=True)
        create_case(store, name or store.name).close()
    app = ReasonCommonsApp(store, speaker, provider, lambda consultant: open_case(store, consultant=consultant),
                           factory, tour=tour, story=story, settings=settings)
    return app.run()
