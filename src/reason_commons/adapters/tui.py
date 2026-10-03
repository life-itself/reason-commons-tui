"""Persistent terminal workspace (first usable slice of p1) built with Textual.

The TUI is a projection over ``CaseApplication``: it reads ``workspace`` and
``inspect``, and changes the case only through ``retain_input``, ``consult``,
``retry``, ``export`` and ``checkpoint``. It owns layout, focus, the editor and
which view is shown; it defines no reasoning or persistence rules.
"""

from datetime import date
import os
import re
from pathlib import Path

from rich.markup import escape
from textual import on
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, Markdown, OptionList, Static, TextArea
from textual.widgets.option_list import Option

from reason_commons.adapters.guided import STEPS
from reason_commons.adapters.rendering import _literal


PROVIDERS = {"guided": "Built-in guide (offline)", "anthropic": "Anthropic Claude", "lm-studio": "LM Studio (local)"}
VIEW_LABELS = [("next", "Next step"), ("goal", "Goal"), ("tests", "Tests"), ("actions", "Actions"),
               ("reasoning", "Everything"), ("sources", "Your words"), ("history", "History")]
STATUS_TEXT = {"unavailable": "the consultant could not be reached", "rejected": "the consultant's reply was invalid",
               "started": "the request was interrupted", "input_retained": "the consultant was not asked yet"}

HELP = """\
## How Reason Commons works

You work through one small loop, as often as you like:

1. **Goal**: what would count as better, how you will measure it, and what must not get worse.
2. **Test**: one small change you can make yourself, with a forecast written *before* any result.
3. **Action**: the concrete next thing you will do.
4. **Observation**: what actually happened. Doing the work is not the same as it working.
5. **Review**: compare the result with the original forecast, then keep, adjust or drop the change.

Everything is saved in the case folder as you go. Closing the app keeps your draft.

## Keys

| Key | What it does |
| --- | --- |
| Enter | New line in your answer (typing is always literal) |
| Ctrl+S, or Tab to **Send** then Enter | Send your answer |
| Tab / Shift+Tab | Move between controls |
| Esc | Leave the editor to browse; your text stays |
| Ctrl+P | Actions: export, retry, change consultant, quit |
| F1 | This help |
| Ctrl+Q | Save and quit |

## Consultants

The **built-in guide** works offline and asks the loop's questions in order.
**Anthropic** (needs `ANTHROPIC_API_KEY`) or **LM Studio** (a local model) give
adaptive questions and advice. Change it any time with Ctrl+P.
"""


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


class ExportScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    def __init__(self, default):
        super().__init__()
        self.default = default

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Export a portable copy of this case (.reasoncase)", classes="dialog-title")
            yield Input(self.default, id="destination")
            yield Label("Enter exports. Use a new file name. Esc cancels.", classes="hint")

    @on(Input.Submitted)
    def submitted(self, event):
        self.dismiss(event.value.strip() or None)


class ReasonCommonsApp(App):
    TITLE = "Reason Commons"
    COMMAND_PALETTE_DISPLAY = "Actions"
    CSS = """
    Screen { layout: vertical; }
    #status { height: 1; background: $primary; color: $text; padding: 0 1; }
    #pinned { height: auto; max-height: 3; background: $boost; padding: 0 1; }
    #body { height: 1fr; }
    #views { width: 18; border: round $panel; }
    #views.hidden { display: none; }
    #main { border: round $panel; padding: 0 1; }
    #content { margin: 0; }
    #content MarkdownH2 { margin: 0 0 1 0; }
    #content MarkdownH3 { margin: 1 0 1 0; }
    #main:focus-within, #main:focus { border: round $accent; }
    #response { height: auto; border: round $accent; padding: 0 1; }
    #response-label { color: $text-muted; }
    #editor { height: 6; border: none; }
    #controls { height: 1; margin-top: 1; }
    #controls Button { min-width: 8; height: 1; border: none; margin-right: 1; }
    #retry.hidden { display: none; }
    ChoiceScreen, ExportScreen, HelpScreen { align: center middle; }
    #dialog { width: 80%; max-width: 90; height: auto; max-height: 90%; border: thick $accent;
              background: $surface; padding: 1 2; }
    HelpScreen #dialog { height: 90%; }
    .dialog-title { text-style: bold; margin-bottom: 1; }
    .hint { color: $text-muted; margin-top: 1; }
    """
    BINDINGS = [
        Binding("ctrl+s", "send", "Send", priority=True),
        Binding("escape", "browse", "Browse", show=False),
        Binding("f1", "help", "Help"),
        Binding("ctrl+q", "quit", "Save & quit", priority=True),
    ]

    def __init__(self, store, speaker, provider, open_application, consultant_factory):
        super().__init__()
        self.store, self.speaker, self.provider = str(store), speaker, provider
        self._open, self._consultant_factory = open_application, consultant_factory
        self.case = open_application(consultant_factory(provider))
        self.view_name, self.explain, self.busy = "next", False, False
        self.workspace_value, self._restoring, self._save_timer = None, False, None

    # ----- layout -------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Static(id="status")
        yield Static(id="pinned")
        with Horizontal(id="body"):
            yield OptionList(*[Option(label, id=key) for key, label in VIEW_LABELS], id="views")
            with VerticalScroll(id="main"):
                yield Markdown(id="content")
        with Vertical(id="response"):
            yield Label(id="response-label")
            yield TextArea("", id="editor", soft_wrap=True, show_line_numbers=False, tab_behavior="focus")
            with Horizontal(id="controls"):
                yield Button("Send", id="send", variant="primary")
                yield Button("Retry", id="retry", variant="warning", classes="hidden")
                yield Button("Explain this", id="explain")
                yield Button("Other moves", id="moves")
                yield Button("Views", id="views-button")
                yield Button("Actions", id="actions")
        yield Footer()

    def on_mount(self):
        self.title = "Reason Commons"
        cursor = self.case.inspect()["cursor"] or {}
        self.refresh_workspace()
        if cursor.get("draft"):
            self._restoring = True
            editor = self.query_one("#editor", TextArea)
            editor.load_text(cursor["draft"])
            editor.cursor_location = caret_location(cursor["draft"], cursor.get("caret", len(cursor["draft"])))
            self._restoring = False
        if cursor.get("view") in dict(VIEW_LABELS) and cursor["view"] != "next":
            self.show_view(cursor["view"])
        self.query_one("#editor").focus()
        self.on_resize()

    def on_resize(self, event=None):
        self.query_one("#views").set_class(self.size.width < 100, "hidden")
        self.query_one("#editor").styles.height = 3 if self.size.height < 30 else 6

    # ----- reading ------------------------------------------------------
    def refresh_workspace(self):
        self.workspace_value = self.case.workspace(view=self.view_name)
        self.render_all()

    def render_all(self):
        w = self.workspace_value
        question = (w["question"] or {}).get("data", {})
        step = question.get("decision") or ("Start" if not w["question"] else "Next question")
        consultant = PROVIDERS.get(self.provider, self.provider)
        state = "asking the consultant..." if self.busy else "Saved"
        self.query_one("#status", Static).update(
            f"[b]{escape(w['case_name'])}[/b]  |  {escape(self.speaker)}  |  {state}  |  "
            f"{escape(step)}  |  {escape(consultant)}")
        self.query_one("#pinned", Static).update(self.pinned_text())
        content = self.render_next() if self.view_name == "next" else self.render_view()
        self.query_one("#content", Markdown).update(content)
        retryable = self.retryable()
        self.query_one("#retry").set_class(not retryable, "hidden")
        self.query_one("#response-label", Label).update(
            f"Answer as {escape(self.speaker)}  ·  Enter: new line  ·  Ctrl+S or Send: send to the "
            f"{'guide' if self.provider == 'guided' else 'consultant'}")

    def pinned_text(self):
        case = self.case.inspect()["case"]
        records = [r for r in case["records"]]
        latest = lambda kind: max((r for r in records if r["kind"] == kind),
                                  key=lambda r: int(r["ref"][1:].split("@")[0]), default=None)
        goal, test = latest("goal"), latest("test")
        if goal is None:
            return "Goal: not set yet  |  Safeguards: not set yet  |  No test yet"
        protections = "; ".join(goal["data"].get("protections") or []) or "none recorded"
        parts = [f"[b]Goal[/b] {escape(goal['data']['statement'])}", f"[b]Protect[/b] {escape(protections)}"]
        if test:
            forecast = "; ".join(f.get("expected") or "" for f in test["data"].get("forecast") or [])
            parts.append(f"[b]Test[/b] {escape(test['data']['statement'])} (forecast: {escape(forecast)})")
        else:
            parts.append("No test yet")
        return "  |  ".join(parts)

    def retryable(self):
        return [a for a in self.workspace_value["available_actions"] if a["capability"] == "retry"]

    def render_next(self):
        w = self.workspace_value
        lines = []
        if w["question"]:
            data = w["question"]["data"]
            lines += [f"## {md(data.get('decision') or 'Next question')}", "", f"**{md(data['primary_prompt'])}**", ""]
            rationale = data["rationale"]
        else:
            lines += ["## Welcome to Reason Commons", "",
                      "Work through one goal at a time: set a goal, try a small test with a forecast, "
                      "act, observe what happened, and review.", ""]
            if self.provider == "guided":
                lines += [f"**{md(STEPS['goal'][1])}**", ""]
                rationale = STEPS["goal"][2]
            else:
                lines += ["**What is happening, and what would count as better?** "
                          "You can begin in ordinary words. Unknown measures can stay open.", ""]
                rationale = "A clear picture of success comes before choosing what to change."
        if self.explain:
            lines += ["> **Why this question** (saved explanation, no consultant call)", ">",
                      "> " + md(rationale), ""]
        for pending in w["pending_requests"]:
            value = pending["input"]
            if value["base_revision"] == w["revision"] and value["response_target"] == w["target"]["response_target"]:
                lines += [f"> **Saved, but not answered yet:** {STATUS_TEXT.get(pending['status'], pending['status'])}. "
                          "Your words are kept. Use **Retry** to ask again.", ">", "> " + md(value["text"]), ""]
        records = [r for r in w["records"] if r["kind"] != "intervention"]
        if records:
            lines += ["---", "", "### What this step builds on", ""]
            for record in records:
                lines += self.record_lines(record)
        return "\n".join(lines)

    def record_lines(self, record):
        d, ref = record["data"], record["ref"]
        kind = record["kind"]
        if kind == "goal":
            out = [f"**Goal {ref}:** {md(d['statement'])}  "]
            out.append(f"Measure: {md(d.get('measure') or 'not set')}  ")
            out.append("Protect: " + md("; ".join(d.get("protections") or []) or "none recorded"))
        elif kind == "test":
            out = [f"**Test {ref}:** {md(d['statement'])}  "]
            for f in d.get("forecast") or []:
                out.append(f"Original forecast (saved before results): {md(f.get('expected'))}  ")
            out.append(f"Review: {md(d.get('review_date') or 'not set')} | "
                       f"Stop if: {md(d.get('stop_condition') or 'not set')}")
        elif kind == "action":
            out = [f"**Action {ref}:** {md(d['statement'])}  ",
                   f"Execution: {md(d.get('execution') or 'unknown')} | "
                   f"Expected state: {md(d.get('expected_state_attainment') or 'unknown')}"]
        elif kind == "observation":
            out = [f"**Observation {ref}** ({md(d.get('basis') or 'basis unknown')}): {md(d['value'])}"]
        elif kind == "review":
            out = [f"**Review {ref}** of {d['test_ref']}: {md(d['assessment'])}"]
            if d.get("next_decision"):
                out.append(f"  \nNext: {md(d['next_decision'])}")
        else:
            out = [f"**Note {ref}:** {md(d.get('text'))}"]
        return out + [""]

    def render_view(self):
        w, view = self.workspace_value, self.view_name
        title = dict(VIEW_LABELS)[view]
        lines = [f"## {title}", "", "_Browsing is local and never asks the consultant._", ""]
        if view == "history":
            for item in reversed(w["history"]):
                lines.append(f"- Revision {item['revision']} | {md(item['timestamp'])}")
            return "\n".join(lines)
        if view == "sources":
            sources = [s for s in w["sources"].values() if "request_id" in s]
            for source in sorted(sources, key=lambda s: s["request_id"], reverse=True):
                lines += [f"**{md(source['speaker'])}** | {md(source['timestamp'])} | {source['request_id']}", "",
                          "> " + md(source["text"] or "(empty)").replace("\n", "  \n> "), ""]
            return "\n".join(lines) if sources else "\n".join(lines + ["Nothing written yet."])
        if view == "tests":
            if not w["comparisons"]:
                lines.append("No test yet.")
            for comparison in reversed(w["comparisons"]):
                test = comparison["test"]
                lines += [f"### Test {test['ref']}: {md(test['data']['statement'])}", "",
                          "| | Original forecast | Reported result |", "| --- | --- | --- |"]
                results = "<br>".join(md(o["data"]["value"]).replace("\n", "<br>") for o in comparison["observations"])
                for forecast in test["data"].get("forecast") or []:
                    lines.append(f"| {md(forecast.get('measure'))} | {md(forecast.get('expected'))} | "
                                 f"{results or 'not observed yet'} |")
                lines += ["", f"Review date: {md(test['data'].get('review_date') or 'not set')} | "
                          f"Stop if: {md(test['data'].get('stop_condition') or 'not set')}", ""]
                for review in comparison["reviews"]:
                    lines += [f"**Review {review['ref']}:** {md(review['data']['assessment'])}", ""]
            return "\n".join(lines)
        records = [r for r in w["records"] if r["kind"] != "intervention"]
        if not records:
            lines.append("Nothing recorded here yet.")
        for record in records:
            lines += self.record_lines(record)
        if view == "reasoning" and w["uncertainty"]:
            lines += ["### Still open", ""] + [f"- {md(u['message'])}" for u in w["uncertainty"]]
        return "\n".join(lines)

    def show_view(self, name):
        self.view_name = name
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

    def action_explain(self):
        if self.view_name != "next":
            self.view_name = "next"
        self.explain = not self.explain
        self.refresh_workspace()

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
        editor = self.query_one("#editor", TextArea)
        status = result["status"]
        sent = text is not None and editor.text == text
        if status == "saved":
            if sent:
                editor.clear()
            self.explain = False
            self.view_name = "next" if text is not None or self.view_name == "next" else self.view_name
            self.notify("Saved.")
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
        if self.busy or self.workspace_value is None:
            return
        editor = self.query_one("#editor", TextArea)
        draft = editor.text
        target = self.workspace_value["target"]
        try:
            result = self.case.checkpoint({
                "view": self.view_name, "focus": "response" if editor.has_focus else "browse",
                "draft": draft, "caret": caret_index(draft, editor.cursor_location), "speaker": self.speaker,
                "response_target": target["response_target"], "base_revision": target["base_revision"]})
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
        yield SystemCommand("Export case", "Write a portable .reasoncase copy", self.action_export)
        for key, label in PROVIDERS.items():
            if key != self.provider:
                yield SystemCommand(f"Consultant: {label}", "Use this consultant from now on",
                                    lambda key=key: self.switch_provider(key))
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
            self.notify("ANTHROPIC_API_KEY is not set, so requests will fail. See the README.",
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
            yield Label("What would you like to call this goal?", classes="dialog-title")
            yield Input(placeholder="for example: Sleep better, Ship the payments change", id="goal-name")
            yield Label("A short name is enough; you describe the goal inside. Enter starts, Esc goes back.",
                        classes="hint")

    @on(Input.Submitted)
    def submitted(self, event):
        self.dismiss(event.value.strip() or None)


class GoalsApp(App):
    """Home screen: pick one of your goals or start a new one. Returns the chosen folder."""

    TITLE = "Reason Commons"
    ENABLE_COMMAND_PALETTE = False
    CSS = ReasonCommonsApp.CSS + """
    #home { padding: 1 2; }
    #home-title { text-style: bold; color: $accent; }
    #home-intro { margin: 1 0; }
    #goals { height: auto; max-height: 1fr; border: round $accent; }
    """
    BINDINGS = [Binding("ctrl+q", "quit", "Quit", priority=True), Binding("f1", "help", "Help")]

    def __init__(self, root, list_goals=find_goals, create=None):
        super().__init__()
        self.root, self._list = Path(root), list_goals
        self._create = create or self._create_case
        self.goals = []

    def compose(self) -> ComposeResult:
        with Vertical(id="home"):
            yield Static("Reason Commons", id="home-title")
            yield Static(id="home-intro")
            yield OptionList(id="goals")
            yield Label("Arrows choose, Enter opens. F1 explains the loop. Ctrl+Q quits.", classes="hint")
        yield Footer()

    def on_mount(self):
        self.goals = self._list(self.root)
        intro = ("Make progress on a goal that matters, one small loop at a time: "
                 "goal → test with a forecast → action → observation → review.")
        if not self.goals:
            intro += "\n\nYou have no goals yet. Start one below; it is saved as you go."
        self.query_one("#home-intro", Static).update(intro)
        options = [Option("+ Start a new goal", id="new")]
        for index, goal in enumerate(self.goals):
            label = f"{goal['name']}   ·   {goal['step']}   ·   {str(goal['changed'])[:10]}"
            options.append(Option(escape(label), id=str(index)))
        goals = self.query_one("#goals", OptionList)
        goals.add_options(options)
        goals.highlighted = 1 if self.goals else 0
        goals.focus()

    @on(OptionList.OptionSelected, "#goals")
    def chosen(self, event):
        if event.option.id != "new":
            self.exit(self.goals[int(event.option.id)]["path"])
            return

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


def run_home(speaker=None, provider=None, model=None, base_url=None):
    """Show your goals, then open the chosen one in the workspace."""
    store = GoalsApp(goals_home()).run()
    if store is not None:
        run(store, speaker=speaker, provider=provider, model=model, base_url=base_url)


def run(store, name=None, speaker=None, provider=None, model=None, base_url=None):
    """Create the case if the folder does not exist yet, then open the workspace."""
    from reason_commons.bootstrap import configured_consultant, create_case, open_case
    store = Path(os.path.expanduser(store)).resolve()
    provider = provider or os.environ.get("REASON_COMMONS_PROVIDER") or "guided"
    speaker = speaker or os.environ.get("REASON_COMMONS_SPEAKER") or os.environ.get("USER") or "Me"
    factory = lambda chosen: configured_consultant(provider=chosen, model=model if chosen == provider else None,
                                                   base_url=base_url if chosen == provider else None)
    if not store.exists():
        store.parent.mkdir(parents=True, exist_ok=True)
        create_case(store, name or store.name).close()
    app = ReasonCommonsApp(store, speaker, provider, lambda consultant: open_case(store, consultant=consultant), factory)
    app.run()
