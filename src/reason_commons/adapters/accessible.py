"""The accessible ordered presentation: the same workspace as ordered text, for a reader that cannot use
alternate-screen redrawing (``reason-commons tui FOLDER --accessible``, or ``TERM=dumb``).

It is a presentation of the same application, with the same records, explicit submission, attribution and
recovery (``reason-commons-spec/accessibility.md``). Nothing here decides what is valid: every change goes
through the application's use cases. There is no command prompt or phrase parser: Tab and Shift+Tab move
between labelled controls, Enter or Space activates one, arrows choose within a list, Page Down and Page Up
page, and Esc returns with the draft kept. Printable keys edit Response only while it has focus; Enter there
adds a line, and only Send submits.

Output is appended, never redrawn. A meaningful view change appends a section that says it replaces the one
above, so scrollback is not mistaken for current state. Lines wrap to the terminal's width, and a section
longer than the terminal is paged explicitly. Nothing depends on colour: every status is a word.
"""

import os
import sys
import textwrap

from reason_commons.adapters.pricing import label, money, typical
from reason_commons.adapters.usage import crossed

TITLES = {"next": "Next step", "context": "Commons context", "explain": "Explain this", "moves": "Other moves",
          "views": "Views", "backlog": "Backlog", "goal": "Goal", "tests": "Tests", "sources": "Your words",
          "history": "History", "help": "Help"}
LISTED_VIEWS = ("next", "backlog", "goal", "tests", "sources", "history", "context")
EXECUTION = {"unknown": "not known yet", "planned": "planned", "completed": "done, as reported", "blocked": "blocked"}
ATTAINMENT = {"unknown": "not known yet", "pending": "pending", "met": "met", "not_met": "not met"}
KEYS = {"\t": "tab", "\x1b[Z": "shift+tab", "\r": "enter", "\n": "enter", " ": "space", "\x1b": "escape",
        "\x7f": "backspace", "\x08": "backspace", "\x1b[6~": "pagedown", "\x1b[5~": "pageup", "\x1b[A": "up",
        "\x1b[B": "down", "\x03": "quit", "\x11": "quit"}


class Control:
    def __init__(self, label, role, consequence, run=None):
        self.label, self.role, self.consequence, self.run = label, role, consequence, run

    def describe(self):
        return f"{self.label}, {self.role}: {self.consequence}"


class AccessibleWorkspace:
    """One commons in the ordered presentation. ``write`` receives text to append; ``handle`` takes one key."""

    def __init__(self, case, speaker, width=80, height=24, write=None, consultant="the consultant", usage=None,
                 model=None):
        self.case, self.speaker, self.consultant = case, speaker, consultant
        # The usage log session and the paid consultant's model (None when it costs nothing): each reply's cost
        # is said once, and past the monthly budget Send asks to be activated again. Nothing is blocked.
        self.usage, self.model = usage, model
        self.width, self.height = max(20, width), max(8, height)
        self.write = write or (lambda text: (sys.stdout.write(text), sys.stdout.flush()))
        self.view, self.origin, self.focus, self.pages, self.page = "next", None, 0, [], 0
        self.draft, self.state, self.chosen, self.pending = "", "saved", 0, None
        cursor = case.inspect()["cursor"] or {}
        if cursor.get("draft") and cursor.get("response_target") == case.workspace()["target"]["response_target"]:
            self.draft = cursor["draft"]

    # ----- output ----------------------------------------------------------
    def wrap(self, line):
        """A logical line as display lines no wider than the terminal; continuation lines are indented."""
        if not line:
            return [""]
        indent = len(line) - len(line.lstrip(" "))
        return textwrap.wrap(line, self.width, subsequent_indent=" " * min(indent + 2, self.width // 4),
                             break_long_words=True, break_on_hyphens=False) or [""]

    def emit(self, lines):
        for line in lines:
            for part in self.wrap(line):
                self.write(part + "\n")

    def announce(self, text):
        """One short status line, said once."""
        self.emit([text])

    def show(self, replaces=True):
        """Append the current view as a new section, its first page, with the status lines first."""
        lines = self.view_lines()
        body = [part for line in lines for part in self.wrap(line)]
        room = self.height - 3 - (self.width < 50)  # the heading and paging lines (two when narrow) are outside
        self.pages = [body[i:i + room] for i in range(0, len(body), room)] or [[]]
        self.page = 0
        heading = f"== {TITLES[self.view]}" + (" (replaces the view above)" if replaces else "") + " =="
        self.emit([heading])
        self.print_page()

    def print_page(self):
        for line in self.pages[self.page]:
            self.write(line + "\n")
        if len(self.pages) > 1:
            more = "Page Down: more" if self.page + 1 < len(self.pages) else "the last page"
            back = "; Page Up: back" if self.page else ""
            self.emit([f"Page {self.page + 1} of {len(self.pages)}. {more}{back}."])

    # ----- what is shown ---------------------------------------------------
    def workspace(self, view="next"):
        return self.case.workspace(view=view)

    def status_lines(self):
        w = self.workspace()
        controls = self.controls()
        focus = controls[self.focus % len(controls)]
        return [f"Reason Commons | {w['case_name']} | {self.speaker} (declared) | {self.state}",
                f"View: {TITLES[self.view]} | Focus: {focus.label} ({focus.role})"]

    def view_lines(self):
        lines = self.status_lines()
        lines += getattr(self, "lines_" + self.view)()
        lines += ["", "Controls (Tab moves, Enter activates):"]
        controls = self.controls()
        lines += [f"{'> ' if i == self.focus % len(controls) else '- '}{c.describe()}" for i, c in enumerate(controls)]
        return lines

    def attention(self, w):
        lines = [f"Attention: BREACH. {b['measure']}: reported {b['value']}, outside the bound {b['bound']}."
                 for b in w.get("breaches") or []]
        lines += [f"Attention: {n['message']}" for n in w.get("notices") or []]
        lines += [f"Attention: review needed. Test {r['ref']} was planned for an earlier version of what it "
                  "cites." for r in w.get("test_reviews") or []]
        return lines

    def goal_lines(self, w):
        goal = next(iter(w["goals"][-1:]), None)
        if goal is None:
            waiting = [e for e in w["backlog"] if e["entry"] == "proposal" and e["kind"] == "goal"]
            return ["Goal: proposed, not yet accepted: " + waiting[0]["summary"]] if waiting else ["Goal: unknown."]
        data = goal["data"]
        label = "Goal (provisional, no measure yet)" if not data.get("measure") else "Goal"
        return [f"{label}: {data['statement']}"] + [f"Protect: {p}" for p in data.get("protections") or []] + (
            [] if data.get("protections") else ["Protect: none recorded."])

    def comparison_lines(self, comparison):
        test = comparison["test"]["data"]
        lines = [f"Test {comparison['test']['ref']}: {test['statement']}"]
        for forecast in test.get("forecast") or []:
            qualifiers = ", ".join(f"{k} {forecast[k]}" for k in ("scope", "denominator", "period") if forecast.get(k))
            lines.append(f"  Measure: {forecast.get('measure') or 'not stated yet'}.")
            lines.append(f"  Original forecast, saved before any result: {forecast.get('expected') or 'not stated'}"
                         + (f" ({qualifiers})." if qualifiers else "."))
            found = [o for o in comparison["observations"] if o["data"]["measure"] == forecast.get("measure")]
            for o in found:
                details = ", ".join(f"{k} {o['data'][k]}" for k in ("scope", "denominator", "period")
                                    if o["data"].get(k))
                basis = "Observed" if o["data"].get("basis") == "observed" else "Reported"
                lines.append(f"  {basis} result: {o['data']['value']}" + (f" ({details})." if details else "."))
            if not found:
                lines.append("  Result: not observed yet.")
        for action in comparison.get("actions") or []:
            data = action["data"]
            lines.append(f"  Action: {data['statement']}. Execution: {EXECUTION.get(data.get('execution'), 'not known yet')}."
                         f" Expected effect: {ATTAINMENT.get(data.get('expected_state_attainment'), 'not known yet')}.")
        if test.get("review_date"):
            lines.append(f"  Review {test['review_date']}; no reminder scheduled.")
        unknown = [f["field"] for f in comparison.get("review_fields") or [] if not f["value"]]
        if unknown:
            lines.append("  Not known yet: " + ", ".join(unknown) + ".")
        return lines

    def lines_next(self):
        w = self.workspace()
        lines = self.attention(w)
        question = (w["question"] or {}).get("data") or {}
        if question:
            lines += [f"NEXT: {question.get('decision') or 'Next question'}", f"Question: {question['primary_prompt']}"]
            purpose = str(question.get("purpose") or "")
            if " " in purpose.strip():
                lines.append(f"Purpose: {purpose}")
        else:
            lines += ["NEXT: Clarify the goal", "Question: What is happening, and what would count as better?"]
        lines += self.goal_lines(w)
        unknown = {}
        for item in w.get("uncertainty") or []:
            field = item["field"].replace("_", " ")
            if field.startswith("forecast."):
                _, index, name = field.split(".")
                field = f"forecast {int(index) + 1} {name}"
            unknown.setdefault(item["ref"] or "the commons", []).append(field)
        if unknown:
            lines.append("Uncertain: " + "; ".join(f"{ref}: {', '.join(fields)}" for ref, fields in unknown.items()) + ".")
        for comparison in (c for c in w["comparisons"] if c["observations"]):
            lines += [""] + self.comparison_lines(comparison)
            goal = next((g for g in w["goals"] if g["ref"] == comparison["test"]["data"].get("goal_ref")), None)
            if goal:
                lines.append(f"  System goal: {goal['data']['statement']}; judged by its own measure, not by this pilot.")
        reply = w.get("reply") or {}
        waiting = [r for r in reply.get("records") or [] if r["status"] == "proposed"]
        if waiting:
            lines += ["", "Proposed, not yet in the model (from your last answer):"]
            lines += [f"- {r['kind']} {r['ref']}: {r['summary']}" for r in waiting]
        lines += ["", "Response: " + ("(empty)" if not self.draft else "draft kept, " + str(len(self.draft)) + " characters:")]
        lines += ["  " + line for line in self.draft.split("\n")] if self.draft else []
        return lines

    def lines_context(self):
        w = self.workspace()
        lines = [f"Commons context, complete. Local: nothing is sent.",
                 f"Saved at revision {w['revision']}. Proposals are "
                 + ("accepted automatically." if w.get("acceptance") == "automatic" else "held for you.")]
        lines += self.attention(w)
        goal = next(iter(w["goals"][-1:]), None)
        if goal:
            data = goal["data"]
            lines += [f"Goal {goal['ref']}: {data['statement']}"] + [
                f"{name.capitalize()}: {data.get(name) or 'not known yet'}" for name in ("measure", "baseline", "horizon", "scope")]
            lines += [f"Protect: {p}" for p in data.get("protections") or []] or ["Protect: none recorded."]
        else:
            lines.append("Goal: none in the model yet.")
        tests = self.workspace("tests")["comparisons"]
        for comparison in tests:
            data = comparison["test"]["data"]
            periods = ", ".join(dict.fromkeys(f["period"] for f in data.get("forecast") or [] if f.get("period")))
            lines.append(f"Test {comparison['test']['ref']}: {data['statement']}; scope {data.get('scope') or 'not known yet'};"
                         f" period {periods or 'not known yet'}; stop if {data.get('stop_condition') or 'not known yet'};"
                         f" review {data['review_date'] + ', no reminder scheduled' if data.get('review_date') else 'no date'}.")
        if not tests:
            lines.append("Tests: none in the model yet.")
        question = (w["question"] or {}).get("data") or {}
        lines.append(f"Answering: {question.get('primary_prompt') or 'the first question'}"
                     + (f" ({w['target']['response_target']})." if w["target"]["response_target"] else "."))
        waiting = [e for e in w["backlog"] if e["entry"] == "proposal"]
        flagged = [e for e in w["backlog"] if e["entry"] == "review"]
        lines += [f"Waiting: {len(waiting)} proposals in Backlog; {len(flagged)} records flagged for review; "
                  f"{len(w.get('pending_requests') or [])} answers saved but not answered yet.",
                  f"In the model: {sum(1 for s in w['membership'].values() if s == 'accepted')} records accepted."]
        return lines

    def lines_explain(self):
        question = (self.workspace()["question"] or {}).get("data") or {}
        return ["Why this question (saved explanation, no consultant call):",
                question.get("rationale") or "A clear picture of success comes before choosing what to change."]

    def lines_moves(self):
        return ["Other moves. Each says whether it stays local or asks the consultant."]

    def lines_views(self):
        return ["Views. Each is local and makes no consultant call."]

    def lines_help(self):
        return ["Tab and Shift+Tab move between controls; each is announced with what it does.",
                "Enter or Space activates the control with focus. In Response, keys are typed literally and Enter "
                "adds a line; only Send submits.", "Page Down and Page Up page a long view. Esc returns to where you "
                "were, keeping your draft.", "Nothing is sent to the consultant unless a control says it asks."]

    def lines_backlog(self):
        w = self.workspace("backlog")
        entries = w["backlog"]
        if not entries:
            return ["Backlog: nothing waits for you."]
        lines = ["Backlog, in the order it is best decided. Arrows choose an entry."]
        for i, e in enumerate(entries):
            mark = "> " if i == self.chosen % len(entries) else "- "
            if e["entry"] == "review":
                lines.append(f"{mark}Review {e['ref']}: {e['summary']} (something it cites has changed)")
            else:
                lines.append(f"{mark}Proposed {e['kind']} {e['ref']}: {e['summary']}"
                             + (" (decide first)" if e["decide_first"] else "")
                             + (f" (waits for {', '.join(e['waits_for'])})" if e["waits_for"] else ""))
        return lines

    def lines_goal(self):
        return self.goal_lines(self.workspace())

    def lines_tests(self):
        lines = []
        for comparison in self.workspace("tests")["comparisons"]:
            lines += self.comparison_lines(comparison) + [""]
        return lines or ["No test yet."]

    def lines_sources(self):
        sources = [s for s in self.case.sources()["sources"].values() if "request_id" in s]
        return [f"{s['speaker']}, {s['timestamp'][:16].replace('T', ' ')}: {s['text']}" for s in sources] or [
            "Nothing written yet."]

    def lines_history(self):
        revisions = self.case.history()["revisions"]
        return [f"Revision {r['revision']}, {r['timestamp'][:16].replace('T', ' ')}: {len(r['records'])} records, "
                f"{len(r.get('decisions') or [])} decisions" for r in revisions]

    # ----- controls --------------------------------------------------------
    def controls(self):
        w = self.workspace()
        if self.view == "moves":
            options = [Control(o["label"], "local" if o["action"]["type"] == "view" else "asks the consultant",
                               "stored option of this question", lambda o=o: self.option(o))
                       for o in ((w["question"] or {}).get("data") or {}).get("options", [])]
            options += [Control("Ask for direct advice", "asks the consultant", "your Response goes with it",
                                lambda: self.send("direct_advice")),
                        Control("Ask a different question", "asks the consultant", "your Response goes with it",
                                lambda: self.send("another_question"))]
            return options + [Control("Back", "local", "return to the question; your draft is kept", self.back)]
        if self.view == "views":
            return [Control(TITLES[v], "local view", "no consultant call", lambda v=v: self.open(v))
                    for v in LISTED_VIEWS] + [Control("Back", "local", "return; your draft is kept", self.back)]
        if self.view == "backlog" and w["backlog"]:
            entry = w["backlog"][self.chosen % len(w["backlog"])]
            chosen = [Control("Still holds", "local decision", f"say {entry['ref']} still holds; no consultant call",
                              lambda: self.decide("still_holds", entry["ref"]))] if entry["entry"] == "review" else [
                Control("Accept", "local decision", f"admit {entry['ref']} to the model; no consultant call",
                        lambda: self.decide("accept", entry["ref"])),
                Control("Reject", "local decision", f"reject {entry['ref']}, finally; no consultant call",
                        lambda: self.decide("reject", entry["ref"]))]
            return chosen + [Control("Back", "local", "return; your draft is kept", self.back)]
        if self.view != "next":
            return [Control("Back", "local", "return to where you were; your draft is kept", self.back)]
        controls = [Control("Response", "editor", "type your answer literally; Enter adds a line"),
                    Control("Send", "asks the consultant", f"sends your Response to {self.consultant}",
                            lambda: self.send("answer")),
                    Control("Explain this", "local", "the saved explanation; no consultant call",
                            lambda: self.open("explain")),
                    Control("Other moves", "local list", "other moves, each saying whether it asks the consultant",
                            lambda: self.open("moves")),
                    Control("Commons context", "local", "the complete current context; no consultant call",
                            lambda: self.open("context"))]
        reply = w.get("reply") or {}
        if any(r["status"] == "proposed" for r in reply.get("records") or []):
            controls.append(Control("Accept all", "local decision", "admit what your last answer proposed; no "
                                    "consultant call", self.accept_reply))
        controls += [Control("Views", "local list", "every view; no consultant call", lambda: self.open("views")),
                     Control("Help", "local", "keys and controls", lambda: self.open("help")),
                     Control("Save and quit", "local", "keep your draft and close", self.quit)]
        return controls

    # ----- actions ---------------------------------------------------------
    def open(self, view):
        if self.origin is None:
            self.origin = {"view": self.view, "focus": self.focus}
        self.view, self.focus, self.chosen = view, 0, 0
        self.show()

    def back(self):
        origin, self.origin = self.origin or {"view": "next", "focus": 0}, None
        self.view, self.focus = origin["view"], origin["focus"]
        self.show()
        self.announce("Returned to " + TITLES[self.view] + "; your draft is kept.")

    def option(self, option):
        action = option["action"]
        if action["type"] == "consult":
            return self.send(action["intent"])
        target = {"current_question": "next", "trees": "tests"}.get(action["target"], action["target"])
        self.open(target if target in TITLES else "next")

    def month(self):
        """(this month's estimated spending, the monthly budget or None), from the usage log."""
        summary = self.usage.summary()
        return summary["month"]["usd"], summary["budget"]

    def over_budget_words(self, spent, limit):
        reply = self.usage.typical(self.model) or typical(self.model)
        return (f"This month about {money(spent)} of your {money(limit)} budget, estimated."
                + (f" This reply about {money(reply)}." if reply else ""))

    def send(self, intent):
        if not self.draft.strip() and intent == "answer":
            self.announce("Response is empty; nothing was sent.")
            return
        spent = limit = None
        if self.model and self.usage is not None:
            spent, limit = self.month()
            if limit and spent >= limit and self.pending != ("send", intent):
                self.pending = ("send", intent)
                self.announce(self.over_budget_words(spent, limit) + " Activate the same control again to send it; "
                              "nothing is blocked, and Tab keeps your Response.")
                return
        self.pending = None
        mark = self.usage.mark() if self.usage is not None else None
        target = self.workspace()["target"]
        self.announce(f"Asking {self.consultant}. Your Response is saved first.")
        result = self.case.submit(self.draft, self.speaker, target["base_revision"], target["response_target"],
                                  intent=intent)
        cost = self.cost_lines(mark, spent)
        if result["status"] == "saved":
            self.draft, self.state, self.view, self.origin, self.focus = "", "saved", "next", None, 0
            self.checkpoint()
            self.show()
            waiting = len(result.get("proposed") or []) - len(result.get("accepted_automatically") or [])
            self.announce("Reply saved." + (f" {waiting} proposals wait for you; Accept all admits them."
                                             if waiting > 0 else ""))
        else:
            self.state = {"unavailable": "consultant unavailable", "rejected": "reply rejected",
                          "stale": "commons changed", "not_saved": "not saved"}.get(result["status"], result["status"])
            self.announce(f"Not answered: {result.get('message') or result['status']}. Your Response is kept.")
        for line in cost:
            self.announce(line)

    def cost_lines(self, mark, before):
        """What a send just cost, and whether the month reached 80% or 100% of the budget: each said once, after
        the reply's own announcement."""
        if self.usage is None or mark is None:
            return []
        lines, paid = [], self.usage.since(mark)
        if paid:
            models = ", ".join(dict.fromkeys(label(e["model"]) for e in paid))
            priced = [e["usd"] for e in paid if e["usd"] is not None]
            if all(e["outcome"] == "no_reply" for e in paid):
                lines.append(f"No reply came from {models}; the request may still be billed.")
            elif len(priced) == len(paid):
                lines.append(f"Cost: about {money(sum(priced))}, {models}, estimated.")
            else:
                lines.append(f"Cost: not known for {models}.")
        if before is not None:
            after, limit = self.month()
            share = crossed(before, after, limit)
            if share == 80:
                lines.append(f"This month about {money(after)}: 80% of your {money(limit)} budget, estimated. "
                             "Nothing is blocked.")
            elif share == 100:
                lines.append(f"This month about {money(after)}, past your {money(limit)} budget, estimated. "
                             "Each send will ask first; nothing is blocked.")
        return lines

    def decide(self, action, ref, confirmed=False):
        revision = self.case.inspect()["case"]["revision"]
        result = (self.case.still_holds(ref, self.speaker, revision) if action == "still_holds" else
                  getattr(self.case, action)([ref], self.speaker, revision, confirmed=confirmed))
        if result["status"] == "confirm":
            more = result["refs"] + result.get("leaves", []) + result.get("closes", [])
            self.announce(f"This takes more than you chose: {', '.join(more)}. Activate the same control again "
                          "to confirm.")
            self.pending = (action, ref)
            return
        self.pending = None
        self.announce(f"{action.replace('_', ' ').capitalize()}: {result['status']}.")
        self.show()

    def accept_reply(self):
        refs = [r["ref"] for r in (self.workspace().get("reply") or {}).get("records") or [] if r["status"] == "proposed"]
        result = self.case.accept(refs, self.speaker, self.case.inspect()["case"]["revision"], confirmed=True)
        self.announce(f"Accepted {len(result.get('refs') or [])}: in your model now." if result["status"] == "saved"
                      else f"Not accepted: {result.get('message') or result['status']}.")
        self.show()

    def quit(self):
        self.checkpoint()
        self.running = False

    def checkpoint(self):
        target = self.workspace()["target"]
        try:
            self.case.checkpoint({"view": "next", "focus": "response", "draft": self.draft, "caret": len(self.draft),
                                  "speaker": self.speaker, "response_target": target["response_target"],
                                  "base_revision": target["base_revision"]})
        except Exception:
            self.announce("Draft not saved to disk. Copy your text somewhere safe.")

    # ----- keys ------------------------------------------------------------
    def start(self):
        self.running = True
        self.show(replaces=False)
        if self.model and self.usage is not None:
            spent, limit = self.month()
            if limit and spent >= limit:
                self.announce(f"This month about {money(spent)}, past your {money(limit)} budget, estimated. "
                              "Each send will ask first; nothing is blocked.")

    def handle(self, key):
        """One key, named ("tab", "enter", "pagedown"...) or a printable character."""
        controls = self.controls()
        focused = controls[self.focus % len(controls)]
        if key in ("tab", "shift+tab"):
            self.focus = (self.focus + (1 if key == "tab" else -1)) % len(controls)
            self.pending = None
            self.announce("Focus: " + controls[self.focus].describe())
        elif key in ("pagedown", "pageup"):
            step = 1 if key == "pagedown" else -1
            if 0 <= self.page + step < len(self.pages):
                self.page += step
                self.print_page()
            else:
                self.announce("No more pages that way.")
        elif key in ("up", "down") and self.view == "backlog":
            self.chosen += 1 if key == "down" else -1
            self.show(replaces=True)
        elif key == "escape":
            if self.view != "next" or self.origin:
                self.back()
            else:
                self.focus = 0
                self.announce("Focus: " + self.controls()[0].describe())
        elif key == "quit":
            self.quit()
        elif focused.label == "Response" and self.view == "next":
            if key in ("enter",):
                self.draft += "\n"
                self.announce("New line.")
            elif key == "backspace":
                if self.draft:
                    removed, self.draft = self.draft[-1], self.draft[:-1]
                    self.announce("Deleted " + ("a line break" if removed == "\n" else repr(removed)) + ".")
            elif key == "space":
                self.draft += " "
            elif len(key) == 1 and key.isprintable():
                self.draft += key
                self.write(key)
        elif key in ("enter", "space") and focused.run:
            if self.pending and focused.label in ("Accept", "Reject"):
                action, ref = self.pending
                return self.decide(action, ref, confirmed=True)
            focused.run()
        return self.running


def read_keys(stream):
    """Keys from a terminal in raw mode, as the names ``handle`` takes."""
    import termios
    import tty
    descriptor = stream.fileno()
    saved = termios.tcgetattr(descriptor)
    tty.setcbreak(descriptor)
    try:
        while True:
            key = os.read(descriptor, 1).decode(errors="ignore")
            if key == "\x1b":
                more = os.read(descriptor, 5).decode(errors="ignore") if _ready(descriptor) else ""
                key += more
            yield KEYS.get(key, key)
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, saved)


def _ready(descriptor):
    import select
    return bool(select.select([descriptor], [], [], 0.05)[0])


def run(store, name=None, speaker=None, provider=None, model=None, base_url=None):
    """Open (creating if needed) a commons in the ordered presentation, in this terminal, without redrawing it."""
    from pathlib import Path
    from reason_commons.bootstrap import configured_consultant, create_case, open_case, usage_session
    store = Path(os.path.expanduser(store)).resolve()
    provider = provider or os.environ.get("REASON_COMMONS_PROVIDER") or "guided"
    speaker = speaker or os.environ.get("REASON_COMMONS_SPEAKER") or os.environ.get("USER") or "Me"
    if not store.exists():
        store.parent.mkdir(parents=True, exist_ok=True)
        create_case(store, name or store.name).close()
    size = os.get_terminal_size(sys.stdout.fileno()) if sys.stdout.isatty() else os.terminal_size((80, 24))
    usage = usage_session("accessible")
    consultant = configured_consultant(provider=provider, model=model, base_url=base_url, usage=usage.record)
    with open_case(store, consultant=consultant) as case:
        workspace = AccessibleWorkspace(case, speaker, size.columns, size.lines,
                                        consultant={"guided": "the built-in guide"}.get(provider, provider),
                                        usage=usage,
                                        model=getattr(consultant, "model", None) if provider == "anthropic" else None)
        workspace.start()
        for key in read_keys(sys.stdin):
            if not workspace.handle(key):
                break
