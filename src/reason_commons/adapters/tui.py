"""Persistent terminal workspace (first usable slice of p1) built with Textual.

The TUI is a projection over ``CaseApplication``: it reads ``workspace`` and
``inspect``, and changes the case only through ``retain_input``, ``consult``,
``retry``, the operator's decisions (``accept``, ``reject``, ``undo``,
``still_holds``, ``set_acceptance``), ``export`` and ``checkpoint``. It owns
layout, focus, the editor and which view is shown; it defines no reasoning or
persistence rules, and the application decides what a decision takes with it.
"""

from datetime import date
import os
import base64
import re
import tempfile
import textwrap
from pathlib import Path

from rich.cells import cell_len, set_cell_size
from rich.console import Group
from rich.markup import escape
from rich.table import Table
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.color import Color
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.content import Content
from textual.css.query import NoMatches
from textual.markup import escape as escape_markup
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Markdown, OptionList, Static, TextArea
from textual.widgets.option_list import Option

from reason_commons.adapters import pricing, themes
from reason_commons.adapters.guided import STEPS, placeholder, split_hint
from reason_commons.adapters.onboarding import EXAMPLE_ANSWERS, coach_text, login_name, run_setup, tour_state
from reason_commons.adapters.settings import Settings, summary
from reason_commons.adapters.usage import BUDGET_VARIABLE, crossed, parse_budget, skipped_words
from reason_commons.adapters.rendering import _literal
from reason_commons.adapters.timeline import (change_summary, day, decision_words, moment, next_action,
                                              revision_changes, short_day, tree_summary)
from reason_commons.application.presentation import describe
from reason_commons.adapters.trees import (READING, ROLE_LABELS, TREE_TITLES, bright_lines, branches, neighbours,
                                           roots, statement_details, tally_line, tree_lines, trees_lines)


TOUR_FINISHED = "tour-finished"
STORY_OWN_GOAL, STORY_HOME = "story-own-goal", "story-home"
PROVIDERS = {"guided": "Built-in guide (offline)", "anthropic": "Anthropic Claude", "lm-studio": "LM Studio (local)"}
# Who receives what you send, named where you send it.
SEND_TO = {"guided": "the offline guide", "anthropic": "Claude", "lm-studio": "your local model"}
TREE_ORDER = list(TREE_TITLES)
# In the overview, a branch with at most this many statements below its start is shown whole.
OVERVIEW_OPEN = 3
# The trees as the Views list names them under Trees, the overview first. Short enough for the list.
TREE_NAV = {"all": "All six", "goal": "Goal Tree", "current_reality": "Current Reality", "conflict": "Cloud",
            "future_reality": "Future Reality", "prerequisite": "Prerequisite", "transition": "Transition"}
VIEW_LABELS = [("next", "Next step"), ("backlog", "Backlog"), ("goal", "Goal"), ("trees", "Trees"), ("tests", "Tests"),
               ("actions", "Loop actions"), ("reasoning", "Reasoning"), ("sources", "Your words"),
               ("history", "History"), ("context", "Case context")]
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
# The records the Goal and Loop actions views show; a goal in Loop actions is left to the band and Goal.
RECORD_KINDS = {"goal": {"goal"}, "actions": {"test", "action"}}
# How much context the band repeats; a presentation preference saved with the cursor.
DENSITIES = ("compact", "expanded")
# What each kind of record is called where Reasoning lists what is still open about it.
OPEN_KINDS = {"goal": "Goal", "test": "Test", "action": "Action", "observation": "Result", "review": "Review"}
# Pane width from which a forecast and its results sit side by side rather than one after the other.
WIDE = 90
# Controls a person passes through on the way to something else. Esc does not return focus to them:
# it returns to the answer they were writing.
NAVIGATION_CONTROLS = {"send", "fill", "retry", "retry-deeper", "accept-all", "explain", "moves", "views-button", "commands", "help",
                       "finish", "views"}
# What each kind of proposal is called in the Backlog and in decisions.
KIND_NAMES = {"goal": "Goal", "note": "Note", "test": "Test", "action": "Action", "observation": "Result",
              "review": "Review", "claim": "Statement", "link": "Link", "retraction": "Withdrawal"}
# The alternatives to answering the current question. Each says whether it stays local or asks the consultant.
OTHER_MOVES = [("explain", "Inspect rationale · local; opens saved explanation"),
               ("evidence", "Inspect evidence · local; opens this question's saved sources"),
               ("goal", "Inspect goal and safeguards · local; opens the Goal view"),
               ("direct_advice", "Ask for direct advice · asks consultant"),
               ("another_question", "Ask another question · asks consultant"),
               ("explain_observation", "Ask for help planning an observation · asks consultant")]
# The menu named "actions" is the Commands list; the name is kept because a saved cursor may hold it.
MENU_TITLES = {"other_moves": "Other moves. Nothing is sent until you choose an item.",
               "actions": "Commands", "views": "Views (local, no consultant call)"}
# What Send brings back, said where Send is: "Send: get the guide's reply".
REPLY_FROM = {"guided": "the guide's reply", "anthropic": "Claude's reply", "lm-studio": "your local model's reply"}
# Actions of later delivery profiles. A restored cursor may still name one; it is refused locally.
LATER_PROFILE_ACTIONS = {"explore-causal-model": "Explore causal model", "record-position": "Record position",
                         "record-test-reliance": "Record test reliance", "restore-reasoning": "Restore reasoning"}
# Proposal adapters that bring material in offline; their attempts are not consultant calls.
OFFLINE_ADAPTERS = ("ltp-tree-import/", "story/", "commons-import/")
# Terminal width from which a chosen statement's details sit beside the trees; below it, Enter opens them.
INSPECTOR_FROM, INSPECTOR_WIDTH = 120, 36
# The most statements a reply may add to the trees and still be drawn under the next question; more (an import,
# say) is summed up in a line, and Ctrl+T shows them.
HEARD_AT_MOST = 8
# How far a line outside the chosen statement's chunk moves from the text colour toward the ground: about a
# third of full contrast, faint enough not to compete and still readable when the eye goes there.
QUIET = 0.62

HELP = """\
## The screen

The current question and its answer box are the main task. A guided trial or a recorded test also shows
the loop: ✓ done, ● now, ○ still to come. **Views** on the left offers the core destinations;
Enter opens one. Other supporting views are available under **Commands**. The footer shows the keys that
work where the keyboard is now; Tab reaches **Commands** and **Help** there like any other control.

## Keys and controls

Help covers the controls; **Explain this** covers the reasoning behind a question.

| Key | What it does |
| --- | --- |
| Enter | New line in your answer (typing is always literal) |
| Ctrl+S, or Tab to **Send** then Enter | Send your answer |
| F2 | Settings, including automatic reasoning acceptance or requiring acceptance |
| Tab / Shift+Tab | Move between controls |
| Esc | Leave the editor to browse, your text kept; elsewhere, back to where you were before looking around |
| Ctrl+T | Open the trees; press again to go back to the question and your draft |
| ↑ / ↓ | In the Trees view: choose a statement |
| Space | In the Trees view: fold the chosen statement's branches away, or unfold them |
| Enter | In the Trees view: the chosen statement's details in full; in all six, its tree |
| a | In the Trees view: begin an answer about the chosen statement (nothing is sent) |
| Enter, a, r, h | In Backlog: choices for the chosen entry; accept; reject; a flagged record still holds |
| u | In History: undo the chosen step's acceptance (you see what goes first) |
| Ctrl+N | In the Trees view: the next tree, then all six again |
| Ctrl+P, or **Commands** | Every command, each marked local or asking the consultant |
| In a menu | Type to filter, arrows choose, Enter activates; **Back** or Esc returns |
| F1, or **Help** | This help |
| Ctrl+Q | Save and quit |

## How Reason Commons works

You work through one small loop, as often as you like:

1. **Goal**: what would count as better, how you will measure it, and what must not get worse.
2. **Test**: one small change you can make yourself, with a forecast written *before* any result.
3. **Action**: the concrete next thing you will do.
4. **Observation**: what actually happened. Doing the work is not the same as it working.
5. **Review**: compare the result with the original forecast, then keep, adjust or drop the change.

Everything is saved in the case folder as you go. Closing the app keeps your draft.

## The trees

The **Trees** view (Ctrl+T) draws the six thinking-process trees: Goal, Current
Reality, Evaporating Cloud, Future Reality, Prerequisite and Transition. It opens on
all six, each folded at what it is for; Space unfolds a branch and Enter opens its
tree. The six are listed under Trees in Views, and Ctrl+N steps through them. Each
line reads as a sentence ("because: …"), with the statement's role after it and the
assumption behind the link under it; a complete Evaporating Cloud is drawn as its
five boxes. They grow as you
talk: tell the consultant what causes a problem, what conflict keeps you stuck,
what stands in the way or what you plan to do, and it proposes each statement for
its tree, linked to the others. Ask it to reword or drop something and it proposes
that too; once you accept, the tree changes and earlier wording stays in History. A test can carry out an action from
the Transition Tree, and its forecast and result then show under that action.
The Trees view marks what the last reply changed NEW or REWORDED. Where paths meet, a statement
says how many of its tree's ends it leads to ("leads to 5 of 6 undesirable
effects"), and each tree's page counts what it does not state yet.

After a reply, Next step draws what it proposes under the new question, beside
the words it came from, while you still know what you meant. Nothing a reply
proposes is in your model until you accept it: **Accept all** takes everything that
reply proposed, and **Backlog** decides one at a time. Accepting admits it to your
model; it does not make it true or record that you agree.

In the Trees view, ↑ and ↓ choose a statement. In a single tree the rest goes
quiet around it, in place, until the keyboard leaves the drawing. Its details (the
question worth asking of it; every link read from its side, with the assumption
behind it or none stated; the tests that carry it out, each forecast saved before
any result; earlier wordings; and who said it, when, in their own words) sit
beside the trees on a wide terminal. Enter shows them full screen; Esc returns.
**a** puts the statement's words at the end of your answer, so what you write says
which statement you mean; change them as you like, and nothing is sent until Send.

The built-in guide does not add to the trees; Anthropic or LM Studio do. Any
consultant can work with trees you bring in: Ctrl+P, **Import trees** reads an
`.ltp.yaml` file, and **Export trees** writes one.

## Consultants

The **built-in guide** works offline and asks the loop's questions in order.
**Anthropic** (needs `ANTHROPIC_API_KEY`) or **LM Studio** (a local model) give
adaptive questions and advice. Ctrl+P switches for this session; F2 **Settings** on
the home screen saves your name, consultant and model for next time.

With Claude, **Send with deeper reasoning** in Commands sends one answer to Claude
Sonnet, which reasons more deeply and costs more; the next Send goes to your usual
model again. When Retry would ask again, **Retry with Sonnet** does the same.

Claude is paid per reply; LM Studio and the guide cost nothing. With Claude, the
footer's right end estimates what this session and this month cost, each reply's
notice says what it cost, and **Consultant calls and cost** in Commands has the
details. They are estimates at Anthropic's list prices; your bill is in the
Anthropic Console. A **monthly budget** (F2 Settings) is a soft limit: past it,
each send asks once first, and nothing is blocked.

## Themes

Twelve voices from the Reason Commons web app, each light or dark. F2 **Settings**
changes the voice and light or dark as you press ← and →, and keeps the choice. Ctrl+P,
**Theme** previews every voice with its description as you move: arrows up and down
choose a voice, left and right choose light or dark, Enter keeps it. The choice is
saved as `theme:` in your settings file; `--theme` or `REASON_COMMONS_THEME`
overrides it for one run.

New to it? **Take the guided tour** from the home screen: a practice goal with
coaching at each step and example answers. **Explore a real commons** shows how a
movement's shared reasoning grew, step by step. Nothing from either is kept.

## Deciding what enters your model

The consultant drafts; you decide. What a reply proposes waits in **Backlog** with
the words it came from, in the order it is best decided: a new goal first, because
everything else is judged against it, then the trees in their usual order, then
tests and results. A proposal that needs another waits for it, and says so.

In Backlog, Enter offers the choices for the chosen entry; **a** accepts it and
**r** rejects it. Accepting also takes the proposals it needs, and rejecting the
proposals that need it; you see the whole list before anything changes. A
rejection is final, though the consultant may propose the idea again.

When an accepted change rewords or withdraws something, whatever cites it is
flagged for review in Backlog, with the change that raised the flag. It changes
nothing: **h** says it still holds, or ask the consultant about the open reviews
(Commands), and accept or reject what it proposes. A change reaches one step
further each time you accept one.

Every acceptance can be undone: in **History**, choose the step and press **u**.
The list of what leaves the model with it comes first. An undo is final.

**Commands** has **Accept proposals automatically**: from then on, a reply's
proposals enter the model with the reply, marked as accepted under your setting,
and each can still be undone. **Hold proposals for review** turns it back.
Proposals already waiting keep waiting either way.

## Looking back

**History** lists every saved step, one row each: when, the question it answered
or the decision taken, and what entered the model. Enter opens that moment exactly
as it was; ← and → step through, **Back to now** returns. Nothing can be changed
while looking back, but **u** undoes the chosen step's acceptance.
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


def loop_line(stage, wide=True, width=None):
    """The loop drawn as one line, its steps joined by ─: ✓ done, ● current, ○ still to come. The symbols
    carry the meaning; colour only adds to it.

    With a ``width`` it always fits: first without the joins, then as just where you are ("● Review · step
    5 of 5"), because a line cut off at the right would lose the one step that matters.
    When the step cannot be told (another consultant's own question), no step is marked.
    """
    keys = [key for key, _ in LOOP]
    if stage not in keys:
        return "[dim]" + "  ·  ".join(name for _, name in LOOP) + "[/]"
    now = keys.index(stage)
    parts = [f"[b $accent]● {name}[/]" if index == now else f"[$text-muted]{'✓' if index < now else '○'} {name}[/]"
             for index, (_, name) in enumerate(LOOP)]
    aside = "   [$text-muted]then a new loop begins[/]" if stage == "review" and wide else ""
    fits = lambda line: width is None or Content.from_markup(line).cell_length <= width
    line = " [$text-muted]─[/] ".join(parts) + aside
    if not fits(line):
        line = "  ".join(parts)
    if not fits(line):
        line = f"[b $accent]● {LOOP[now][1]}[/] [$text-muted]· step {now + 1} of {len(LOOP)}[/]"
    return line


def md(value):
    """Escape stored, untrusted text for Markdown display."""
    return _literal(value, True)


def same_person(one, other):
    """Whether two names plausibly name one person: alike ignoring case, or one the start of the other, as
    "David" is of the login name "davidjoseph" that an earlier answer may have been saved under."""
    one, other = str(one).strip().lower(), str(other).strip().lower()
    return bool(one and other) and (one.startswith(other) or other.startswith(one))


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
    return max((r for r in records if r["kind"] == kind),
               key=lambda r: tuple(int(n) for n in r["ref"][1:].split("@")), default=None)


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
        for breach in (b for b in workspace.get("breaches") or [] if b["test_ref"] == comparison["test"]["ref"]
                       and b["measure"] == forecast.get("measure")):
            parts.append(Text(f"BREACH · reported {breach['value']}, outside the bound {breach['bound']}",
                              style="bold red"))
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
    if test.get("stop_condition"):
        details.add_row("Stop condition", Text(str(test["stop_condition"])))
    if test.get("review_date"):
        details.add_row("Review", Text(f"{test['review_date']}; no reminder scheduled"))
    unknown = [f["field"] for f in comparison.get("review_fields") or [] if not f["value"]]
    if unknown:
        details.add_row("Not recorded yet", Text(", ".join(unknown), style="italic"))
    for action in comparison.get("actions") or []:
        data = action["data"]
        done = EXECUTION_WORDS.get(data.get("execution"), "not known yet")
        details.add_row("Action", Text(f"{data['statement']} · {done}{' as reported' * (done == 'done')} · "
                                       f"expected effect: {ATTAINMENT_WORDS.get(data.get('expected_state_attainment'), 'not known yet')}"))
    if goal and observations:  # at review, a pilot's result is kept apart from the goal; before it, the band has it
        details.add_row("System goal", Text(f"{goal['data']['statement']} · judged by its own measure, "
                                            "not by this pilot"))
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
        if d.get("baseline"):
            rows.append(("Baseline", d["baseline"]))
        for forecast in d.get("forecast") or []:
            rows += [("Original forecast", forecast.get("expected") or "not stated"),
                     ("Measure", forecast.get("measure") or "not stated yet")]
            if forecast.get("period"):
                rows.append(("Period", forecast["period"]))
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


def styled(lines, variables, marked=None, width=None, columns=None, bright=None):
    """Drawing lines as one Text, in the theme's colours. Lines in ``marked`` (a range) are the chosen
    statement: a band in the hand's tint, across ``width`` cells, or only across ``columns`` (first, end)
    when the statement is one of several boxes side by side. Focus is the frame's business, not this.

    When ``bright`` is a set of line indexes, every other line is quiet: still there, in the same place and
    shape, but in one low-contrast tone, so the chosen statement's chunk stands out without the rest of the
    tree moving or going. Terminal dimming is too faint for that on most themes, so the tone is mixed here."""
    text = Text()
    tint = themed("on $hand-tint", variables)
    tone = Color.parse(variables["foreground"]).blend(Color.parse(variables["background"]), QUIET).hex
    for index, line in enumerate(lines):
        start = len(text)
        quiet = bright is not None and index not in bright
        for part, style in line:
            style = themed(style, variables)
            if quiet:  # keep the shape (bold, italic) and lose the colour
                style = " ".join([word for word in style.split() if word in ("bold", "italic", "strike")] + [tone])
            text.append(part, style=style or None)
        if marked is not None and index in marked:
            if columns is None:
                text.append(" " * max(0, (width or 0) - text[start:].cell_len))
                text.stylize(tint, start, len(text))
            else:
                text.stylize(tint, *(start + offset for offset in char_offsets(text.plain[start:], columns)))
        text.append("\n")
    return text


def char_offsets(line, columns):
    """The character positions in ``line`` of the cells from ``columns[0]`` up to ``columns[1]``."""
    cells, first, last = 0, None, len(line)
    for position, character in enumerate(line):
        if first is None and cells >= columns[0]:
            first = position
        if cells >= columns[1]:
            last = position
            break
        cells += cell_len(character)
    return (len(line) if first is None else first), last


class TreeCanvas(Static):
    """The drawing area. In the Trees view it takes focus: ↑↓ choose a statement, Enter opens its details,
    and ``a`` starts an answer about it. Nothing here takes text, so a letter cannot swallow typing."""

    BINDINGS = [Binding("down", "choose(1)", "Choose", key_display="↑↓"),
                Binding("up", "choose(-1)", "Choose", show=False),
                Binding("enter", "details", "Details"),
                Binding("space", "fold", "Fold"),
                Binding("a", "about", "About this")]

    def on_mount(self):
        self.can_focus = False
        self.drawn_width = None

    def on_resize(self, event):
        # Drawings are wrapped to the width they get; after the terminal resizes, draw them again.
        if self.drawn_width is not None and event.size.width != self.drawn_width:
            self.app.call_after_refresh(self.app.render_all)
        self.drawn_width = event.size.width

    def on_focus(self):
        self.app.statement_focused()

    def action_choose(self, step):
        self.app.choose_statement(step)

    def action_details(self):
        self.app.open_statement()

    def action_fold(self):
        self.app.toggle_fold()

    def action_about(self):
        self.app.answer_about()


class StatementScreen(ModalScreen):
    """One statement in full; Esc returns to the trees with the same statement chosen, and ``a`` returns
    with an answer about it begun.

    ``build(width)`` draws the details; they are drawn for the room the dialog actually has."""

    BINDINGS = [Binding("escape,enter", "dismiss", "Back to the trees"),
                Binding("a", "about", "Answer about this")]

    def action_about(self):
        self.dismiss()
        self.app.answer_about()

    def __init__(self, build):
        super().__init__()
        self.build = build

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            with VerticalScroll():
                yield Static("", id="statement-text")
            yield Label("Esc returns to the trees; a starts an answer about this statement. Nothing is sent.",
                        classes="hint")

    def on_mount(self):
        self.call_after_refresh(self.fill)

    def on_resize(self, event):
        self.call_after_refresh(self.fill)

    def fill(self):
        text = self.query_one("#statement-text", Static)
        # Leave room for the scroll bar that long details bring with them.
        text.update(self.build(max(30, text.content_size.width - 3)))


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


class MenuScreen(ModalScreen):
    """A labelled menu, filtered by typing and bound to the question it was opened for.

    The filter has focus: printable keys narrow the items, arrows choose, Enter activates the
    chosen item. With nothing matching, Enter activates nothing and the menu says so, offering
    Clear filter and Back. It returns (item, binding), or None for Back or Esc; the workspace
    checks the binding before acting, so a menu left open while the case moved on cannot act
    on a question it was not opened for."""

    BINDINGS = [Binding("escape", "dismiss", "Back"), Binding("down", "move(1)", show=False),
                Binding("up", "move(-1)", show=False)]

    def __init__(self, title, items, binding=None, context=None, notice=None, text="", highlighted=None):
        super().__init__()
        self.title_text, self.items, self.binding = title, items, binding
        self.context, self.notice, self.text, self.wanted = context, notice, text, highlighted

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.title_text, classes="dialog-title")
            if self.context:
                yield Static(self.context, id="menu-context")
            if self.notice:
                yield Static(self.notice, id="menu-notice")
            yield Input(self.text, placeholder="Type to filter", id="filter")
            yield OptionList(id="items")
            yield Static("No matches. Nothing is activated.", id="no-matches", classes="hidden")
            with Horizontal(id="menu-controls"):
                yield Button("Clear filter", id="clear")
                yield Button("Back", id="back")
            yield Static("Type to filter · arrows choose · Enter activates · Back or Esc returns; your draft stays.",
                         classes="hint")

    def on_mount(self):
        self.show_items()
        self.query_one("#filter").focus()

    def matching(self):
        words = self.query_one("#filter", Input).value.strip().lower()
        return [(key, label) for key, label in self.items if words in str(label).lower()]

    def show_items(self):
        shown = self.matching()
        items = self.query_one("#items", OptionList)
        items.clear_options()
        items.add_options([Option(label, id=key) for key, label in shown])
        keys = [key for key, _ in shown]
        if keys:
            items.highlighted = keys.index(self.wanted) if self.wanted in keys else 0
        self.query_one("#no-matches").set_class(bool(shown), "hidden")
        self.query_one("#clear").set_class(not self.query_one("#filter", Input).value, "hidden")
        self.app.menu_changed(self)

    def chosen_key(self):
        items = self.query_one("#items", OptionList)
        if items.highlighted is None or not items.option_count:
            return None
        return items.get_option_at_index(items.highlighted).id

    def action_move(self, step):
        items = self.query_one("#items", OptionList)
        if items.option_count:
            items.highlighted = max(0, min(items.option_count - 1, (items.highlighted or 0) + step))

    @on(Input.Changed, "#filter")
    def filtered(self):
        self.show_items()

    @on(OptionList.OptionHighlighted, "#items")
    def highlighted(self, event):
        self.wanted = event.option.id
        self.app.menu_changed(self)

    @on(Input.Submitted, "#filter")
    def submitted(self):
        key = self.chosen_key()
        if key is not None:
            self.dismiss((key, self.binding))

    @on(OptionList.OptionSelected, "#items")
    def selected(self, event):
        self.dismiss((event.option.id, self.binding))

    @on(Button.Pressed, "#clear")
    def clear(self):
        self.query_one("#filter", Input).value = ""
        self.query_one("#filter").focus()

    @on(Button.Pressed, "#back")
    def back(self):
        self.dismiss(None)


class ChoiceScreen(ModalScreen):
    """A decision about what enters the model: what it concerns, then labelled choices.

    Returns the chosen key, or None for Esc. Nothing changes until a choice is made, and the
    application, not this screen, decides what a choice takes with it."""

    BINDINGS = [Binding("escape", "dismiss", "Back")]

    def __init__(self, title, body, choices):
        super().__init__()
        self.title_text, self.body, self.choices = title, body, choices

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.title_text, classes="dialog-title")
            with VerticalScroll(id="choice-body"):
                yield Markdown(self.body)
            yield OptionList(*[Option(label, id=key) for key, label in self.choices], id="choices")
            yield Label("Arrows choose · Enter decides · Esc returns; nothing changes until you choose.",
                        classes="hint")

    def on_mount(self):
        self.query_one("#choices").focus()

    @on(OptionList.OptionSelected, "#choices")
    def chosen(self, event):
        self.dismiss(event.option.id)


class Timeline(OptionList):
    """The History list. u undoes the chosen step's acceptance; the workspace asks first."""
    BINDINGS = [Binding("u", "app.undo_step", "Undo", show=False)]


class BacklogList(OptionList):
    """The Backlog list. Keys act on the chosen entry; the workspace shows what a decision takes first."""
    BINDINGS = [Binding("a", "app.decide('accept')", "Accept", show=False),
                Binding("r", "app.decide('reject')", "Reject", show=False),
                Binding("h", "app.decide('still_holds')", "Still holds", show=False)]


class TextScreen(ModalScreen):
    """Saved material to read; Esc returns. Nothing here asks the consultant."""

    BINDINGS = [Binding("escape,enter", "dismiss", "Back")]

    def __init__(self, text):
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            with VerticalScroll():
                yield Markdown(self.text, id="text")
            yield Label("Esc returns; nothing is sent.", classes="hint")


class CallsScreen(ModalScreen):
    """How often the consultant was asked, counted from the saved attempt receipts, and with a usage log, what
    paid replies cost: estimates from the log kept outside every goal, never from the case."""

    BINDINGS = [Binding("escape,enter", "dismiss", "Back")]

    def __init__(self, calls, offline, report=None):
        super().__init__()
        self.calls, self.offline, self.report = calls, offline, report

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Consultant calls and cost", classes="dialog-title")
            with VerticalScroll(id="calls-body"):
                yield Static(f"Consultant calls in this goal: {self.calls}\n"
                             f"Offline imports, which ask no consultant: {self.offline}", id="calls-text")
                if self.report is not None:
                    yield Static(self.report, id="cost-text")
            yield Static("Counted from the attempt receipts saved with your inputs"
                         + (", and costs from the usage log kept outside every goal" if self.report is not None else "")
                         + ". Reading them asks the consultant nothing. Esc returns.", classes="hint")


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


class BudgetScreen(ModalScreen):
    """The monthly budget, typed: "5", "$5" or "5.50". Returns the text (blank clears it), or None for Esc."""

    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    def __init__(self, current):
        super().__init__()
        self.current = current

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Monthly budget for Claude replies, in dollars", classes="dialog-title")
            yield Input(self.current, placeholder="for example 5", id="budget")
            yield Static("A soft limit: at 80% and 100% you are told, and past it each send asks first. Nothing is "
                         "blocked. Enter keeps it; blank, none or 0 clears it. Esc cancels.", classes="hint")

    @on(Input.Submitted)
    def submitted(self, event):
        self.dismiss(event.value.strip())


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


class SettingsScreen(ModalScreen):
    """Settings at a glance: Left and Right change the highlighted row and apply (and save) at once.

    Where the home screen can ask, a third row, You, opens the questions for your name and consultant
    (the dialog closes and returns "setup"). The last row, Budget, opens a box for the monthly budget."""

    BINDINGS = [Binding("escape,f2", "close", "Done"), Binding("left", "step(-1)", "Previous"),
                Binding("right", "step(1)", "Next")]

    def __init__(self, setup=False):
        super().__init__()
        self.offer_setup = setup

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Settings", classes="dialog-title")
            yield OptionList(id="settings-rows")
            yield Static(id="settings-about")
            yield Static("↑↓ choose a setting, ←→ change it. Changes apply and are kept at once. "
                         + ("Enter on You changes your name and consultant. " if self.offer_setup else "")
                         + "Enter on Budget changes it. Esc closes.", classes="hint")

    def on_mount(self):
        self.rows = self.query_one("#settings-rows", OptionList)
        self.show(0)

    def show(self, index):
        voice, mode = themes.split_name(self.app.theme)
        options = [Option(f"Theme    ◀ {themes.title(voice)} ▶", id="voice"),
                   Option(f"Mode     ◀ {mode.capitalize()} ▶", id="mode")]
        if self.offer_setup:
            options.append(Option(Content.assemble("You      ", summary(self.app.settings),
                                                   ("   Enter changes", "$text-muted")), id="setup"))
        acceptance = self.app.acceptance_mode()
        if acceptance is not None:
            label = 'Automatic' if acceptance == 'automatic' else 'Require acceptance'
            options.append(Option(f'Reasoning    ◀ {label} ▶', id='acceptance'))
        options.append(Option(Content.assemble("Budget   ", self.app.budget_words(),
                                               ("   Enter changes", "$text-muted")), id="budget"))
        self.rows.clear_options()
        self.rows.add_options(options)
        self.rows.highlighted = index
        self.query_one("#settings-about", Static).update(f"\n{themes.VOICES[voice].description}")
        self.rows.focus()

    def current(self):
        return self.rows.get_option_at_index(self.rows.highlighted or 0).id

    @on(OptionList.OptionHighlighted, '#settings-rows')
    def describe_setting(self, event):
        voice, _ = themes.split_name(self.app.theme)
        description = ('Automatic: later proposals enter the model. Require acceptance: later proposals '
                       'wait in Backlog. Changing this does not decide existing proposals. Each change '
                       'is recorded in History.' if event.option.id == 'acceptance'
                       else themes.VOICES[voice].description)
        self.query_one('#settings-about', Static).update('\n' + description)

    def action_step(self, direction):
        row = self.current()
        if row in ("setup", "budget"):
            return
        if row == 'acceptance':
            mode = 'review' if self.app.acceptance_mode() == 'automatic' else 'automatic'
            self.app.set_acceptance(mode)
            self.show(self.rows.highlighted or 0)
            self.query_one('#settings-about', Static).update(
                'Automatic: later proposals enter the model. Require acceptance: later proposals wait in Backlog. '
                'Changing this does not decide existing proposals. Each change is recorded in History.')
            return
        voice, mode = themes.split_name(self.app.theme)
        if row == "voice":
            keys = list(themes.VOICES)
            voice = keys[(keys.index(voice) + direction) % len(keys)]
        else:
            mode = "dark" if mode == "light" else "light"
        self.app.keep_theme(themes.theme_name(voice, mode))
        self.show(self.rows.highlighted or 0)

    @on(OptionList.OptionSelected, "#settings-rows")
    def chosen(self, event):
        """Enter (or a click) on You opens the questions and on Budget its box; on the other rows it changes
        nothing: Left and Right do."""
        if event.option.id == "setup":
            self.dismiss("setup")
        elif event.option.id == "budget":
            amount, _ = self.app.budget_state()
            self.app.push_screen(BudgetScreen(f"{amount}" if amount is not None else ""), self.budget_typed)

    def budget_typed(self, text):
        if text is None:
            return
        if not self.app.keep_budget(text):
            self.app.notify("Type an amount such as 5 or 5.50, or none to have no budget. Nothing changed.")
        self.show(self.rows.highlighted or 0)

    def action_close(self):
        self.dismiss(None)


def hint_cost(key, label):
    """The columns a footer hint takes: its padding, the key, a space, the label and the gap after it."""
    return cell_len(key) + 1 + cell_len(label) + 3


class Hint(Static):
    """One key hint in the footer: the key in the accent colour, then what it does.

    Clicking it presses the key. Commands and Help are also controls: they take focus, and Enter or Space
    presses them, so Tab reaches them like any other control."""

    BINDINGS = [Binding("enter,space", "press", "Press", show=False)]
    DEFAULT_CSS = """
    Hint { width: auto; height: 1; padding: 0 1; margin-right: 1; }
    Hint.hidden { display: none; }
    Hint:hover { background: $boost; }
    Hint:focus { background: $hand-tint; color: $foreground; text-style: bold; }
    """

    def __init__(self, id, focusable=False):
        super().__init__(id=id, classes="hidden")
        self.press, self.can_focus = None, focusable

    def show(self, key, label, press=None):
        self.press = press
        self.update(Content.assemble((key, "b $accent"), " ", label))
        self.remove_class("hidden")

    def hide(self):
        self.press = None
        self.add_class("hidden")

    def on_click(self):
        self.action_press()

    def action_press(self):
        if self.press:
            self.app.simulate_key(self.press)


class HintBar(Horizontal):
    """The footer command bar: the keys that work for the control that has the keyboard, then Commands and
    Help, which Tab reaches, and on the right whatever the screen wants to say about itself.

    The hints are a fixed set of widgets that are shown, changed or hidden, never rebuilt, so a hint that
    has focus keeps it while the others change around it. They are fitted to the bar's width: a hint with a
    short label says less before it is dropped, the last hints go first, and Commands and Help always stay."""

    BEFORE, AFTER = 6, 2
    CONTROLS = {"commands": ("^p", "Commands", "ctrl+p"), "help": ("f1", "Help", "f1")}
    DEFAULT_CSS = """
    HintBar { dock: bottom; height: 1; background: $footer-background; color: $footer-foreground; }
    HintBar #summary { width: 1fr; height: 1; padding: 0 1; text-align: right; color: $text-muted; }
    """

    def compose(self) -> ComposeResult:
        for number in range(self.BEFORE):
            yield Hint(f"hint-{number}")
        yield Hint("commands", focusable=True)
        for number in range(self.AFTER):
            yield Hint(f"after-{number}")
        yield Static(id="summary")
        yield Hint("help", focusable=True)

    def update_hints(self, before, after=(), summary=(), controls=True):
        """Show these hints: ``before`` Commands and ``after`` it. A hint is (key as drawn, what it does, key
        to press or None), plus a shorter label to use when there is no room. ``summary`` is what the screen
        says about itself, or its alternatives from longest to shortest; the first that fits is shown.
        Commands and Help are shown only with ``controls`` (the workspace has them)."""
        self._wanted = (list(before), list(after), [summary] if isinstance(summary, str) else list(summary),
                        controls)
        self.refit()

    def on_resize(self, event):
        # Not now: changing the hints asks for a layout, which is lost if it is asked for during one.
        self.call_after_refresh(self.refit)

    def refit(self):
        wanted = getattr(self, "_wanted", None)
        if wanted is None:
            return
        before, after, summaries, controls = wanted
        width = self.size.width or 10_000  # not laid out yet: say everything, and fit again once it is
        fixed = sum(hint_cost(key, label) for key, label, _ in self.CONTROLS.values()) if controls else 0
        groups = [list(before), list(after)]  # copies: a wider terminal later brings the dropped hints back
        used = lambda: fixed + sum(hint_cost(hint[0], hint[1]) for group in groups for hint in group)
        for group in reversed(groups):  # say less, the last hints first
            for index in reversed(range(len(group))):
                if used() > width and len(group[index]) > 3:
                    key, _, press, short = group[index]
                    group[index] = (key, short, press)
        for group in reversed(groups):  # then drop the last hints
            while used() > width and group:
                group.pop()
        for prefix, hints, size in (("hint-", groups[0], self.BEFORE), ("after-", groups[1], self.AFTER)):
            for number in range(size):
                slot = self.query_one(f"#{prefix}{number}", Hint)
                if number < len(hints):
                    slot.show(*hints[number][:3])
                else:
                    slot.hide()
        for name, hint in self.CONTROLS.items():
            slot = self.query_one("#" + name, Hint)
            if controls:
                slot.show(*hint)
            else:
                slot.hide()
        room = width - used() - 2  # the summary's own padding
        text = next((text for text in summaries if text and cell_len(text) <= room), "")
        summary = self.query_one("#summary", Static)
        summary.styles.padding = (0, 1) if text else (0, 0)  # empty, it takes nothing but keeps Help at the right
        summary.update(Content(text))


class Views(OptionList):
    """The list of views. Tab goes to the open page's own list, or back to the answer (``tab_target``)."""

    BINDINGS = [Binding("tab", "app.answer", "Back to answer", show=False)]


class Refits:
    """Mixin: tells the workspace when this widget's size changes, so the reading pane is fitted above the
    answer box again. The column and the box change with the terminal and the box with what is typed; the
    page's height settles only after it is drawn, and the History list under it takes what is left."""

    def on_resize(self, event):
        fit = getattr(self.app, "fit_reading", None)
        if fit:
            self.app.call_after_refresh(fit)


class Pane(Refits, Vertical):
    pass


class Page(Refits, Markdown):
    pass


class ThemedApp(App):
    """Opens in the chosen voice (``$REASON_COMMONS_THEME``, filled from settings) and remembers a new one.

    Only the Reason Commons voices are offered; Textual's own themes are not.
    """

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings
        # The terminal size from the latest resize event (see ``terminal``).
        self._terminal = None
        for theme in themes.THEMES.values():
            self.register_theme(theme)
        requested = os.environ.get(themes.ENVIRONMENT)
        self._unknown_theme = requested if requested and not themes.resolve(requested) else None
        self.theme = themes.resolve(requested) or themes.DEFAULT_THEME
        for name in set(self.available_themes) - set(themes.THEMES):
            self.unregister_theme(name)

    @property
    def terminal(self):
        """The terminal's size. Textual calls ``on_resize`` before it updates ``size``, so during a
        resize this is the new size from the event."""
        return self._terminal or self.size

    def on_mount(self):
        if self._unknown_theme:
            self.notify(f"No theme called {self._unknown_theme!r}; using {themes.title(self.theme)}. "
                        "Ctrl+P, Theme lists them.", severity="warning", timeout=8)

    def action_settings(self):
        self.push_screen(SettingsScreen(self.can_set_up()), self.settings_closed)

    def acceptance_mode(self):
        """A case setting is available only in a writable case workspace."""
        return None

    def can_set_up(self):
        """Whether Settings can also change your name and consultant: only where the home screen can ask."""
        return False

    def settings_closed(self, result):
        """What to do after Settings closes, given what it returned (None, or "setup")."""

    def action_change_theme(self):
        self.push_screen(ThemeScreen(self.theme), self.keep_theme)

    def budget_state(self):
        """The monthly budget (dollars or None), and whether your shell sets it, so this app cannot keep it."""
        saved = parse_budget(self.settings.get("usage", "monthly_budget_usd")) if self.settings is not None else None
        raw = os.environ.get(BUDGET_VARIABLE)
        if raw is None or not raw.strip():
            return saved, False
        amount = parse_budget(raw)
        return amount, amount != saved and not getattr(self, "_budget_kept", False)

    def month_spent(self):
        """This month's estimated spending, from the usage log."""
        from reason_commons.adapters.usage import UsageLog, UsageSession
        usage = getattr(self, "usage", None) or UsageSession(UsageLog.from_env(), "workspace")
        return usage.summary()["month"]["usd"]

    def budget_words(self):
        """The Budget row: '$5 a month · ≈ $1.40 so far', or 'none set'."""
        amount, shell = self.budget_state()
        words = "none set" if amount is None else f"{money(amount)} a month · ≈ {money(self.month_spent())} so far"
        return words + (" · set in your shell" if shell else "")

    def keep_budget(self, text):
        """Use this monthly budget from now on: for this run, and in the settings file once there is one. Blank,
        none or 0 clears it. False, changing nothing, when the amount cannot be read."""
        cleared = text.strip().lower() in ("", "none", "off")
        amount = None if cleared else pricing.parse_amount(text)
        if not cleared and amount is None:
            return False
        value = None if not amount else int(amount) if amount == amount.to_integral_value() else float(amount)
        _, shell = self.budget_state()
        os.environ[BUDGET_VARIABLE] = "none" if value is None else str(value)
        self._budget_kept = True
        if getattr(self, "usage", None) is not None:
            self.usage.saved_budget = value
        if self.settings is not None:
            self.settings.set(value, "usage", "monthly_budget_usd")
            if self.settings.exists:
                try:
                    saved = Settings.load(self.settings.path)
                    saved.set(value, "usage", "monthly_budget_usd")
                    saved.save()
                except OSError as exc:
                    self.notify(f"Budget in use, but not saved ({exc}).", severity="error", timeout=8)
        if shell:
            self.notify(f"Your shell also sets {BUDGET_VARIABLE}, which wins the next time you start.", timeout=8)
        self.budget_changed()
        return True

    def budget_changed(self):
        """What to redraw after the budget changes."""

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


class ChosenConsultant:
    """The workspace's consultant, with an optional stand-in for exactly one consultation (a reply with deeper
    reasoning). The application reads ``version`` after ``propose`` returns, so the stand-in stays until
    consult() has returned; the workspace then puts it away, whether the consultation worked or not."""

    def __init__(self, consultant):
        self.default, self.once = consultant, None

    @property
    def current(self):
        return self.once or self.default

    @property
    def version(self):
        return self.current.version

    def propose(self, request):
        return self.current.propose(request)


class ReasonCommonsApp(ThemedApp):
    TITLE = "Reason Commons"
    CSS = """
    Screen { layout: vertical; }
    #status { height: 1; padding: 0 1; }
    #pinned { height: auto; padding: 0 1; }
    #loop-row { height: 2; padding: 0 1; border-bottom: solid $border-blurred; }
    #loop { width: auto; }
    #measure { width: 1fr; text-align: right; }
    #body { height: 1fr; }
    #views-pane { width: 23; padding: 0 1; border: blank; border-right: solid $border-blurred; }
    #views-pane:focus-within { border: heavy $accent; }
    #views-title { color: $text-muted; text-style: bold; }
    #views-pane:focus-within #views-title { color: $accent; }
    #views { height: auto; border: none; background: transparent; color: $text-muted; padding: 0; }
    #views > .option-list--option-highlighted { background: transparent; color: $accent; text-style: bold; }
    #views:focus > .option-list--option-highlighted { background: $hand-tint; color: $foreground; text-style: bold; }
    #views-pane.hidden, #views.hidden, #views-button.hidden { display: none; }
    #column { width: 1fr; height: 1fr; }
    #column.beside-views { padding-top: 1; }
    #main { height: auto; border: none; border-left: blank; padding: 0 1 0 0; }
    #main.fills { height: 1fr; }
    #main:focus { border-left: heavy $accent; }
    #content { margin: 0 0 1 0; }
    #canvas { margin: 0 0 1 0; padding: 0 2 0 1; border-left: blank; }
    #canvas:focus { border-left: heavy $accent; }
    #inspector { width: 36; border-left: solid $border-blurred; padding: 0 1; }
    #inspector:focus { border-left: heavy $accent; }
    #inspector.hidden { display: none; }
    #canvas.hidden { display: none; }
    #content MarkdownH2 { margin: 0; color: $accent; background: transparent; text-style: bold; }
    #content MarkdownH3 { margin: 1 0 0 0; color: $text-muted; background: transparent; text-style: bold; }
    #content MarkdownH6 { margin: 0; color: $text-muted; background: transparent; text-style: none; }
    #content MarkdownParagraph { margin: 0 0 0 0; }
    #response { height: auto; margin: 0 1 0 1; border: $frame $border-blurred; padding: 0 1;
                border-title-color: $text-muted; border-title-background: transparent; }
    #response:focus-within { border: heavy $accent; border-title-color: $background;
                             border-title-background: $accent; border-title-style: bold; }
    #response.collapsed #controls, #response.collapsed #hint-below { display: none; }
    #response.collapsed #editor { min-height: 1; }
    #editor { height: auto; min-height: 3; max-height: 10; border: none; }
    #controls { height: 1; }
    #controls Button { min-width: 8; height: 1; border: none; margin-right: 1; background: transparent;
                       color: $text-muted; text-style: none; }
    #controls Button:hover { color: $text; }
    #controls #send { background: $primary; color: $background; text-style: bold; }
    #controls #retry { color: $warning; }
    #controls #finish { color: $success; }
    #controls Button:focus, #controls #send:focus { background: $hand-tint; color: $foreground; text-style: bold; }
    #retry.hidden, #retry-deeper.hidden, #fill.hidden, #finish.hidden { display: none; }
    #hint { width: 1fr; height: 1; text-align: right; color: $text-muted; }
    #hint-below { height: 1; color: $text-muted; }
    #hint.hidden, #hint-below.hidden { display: none; }
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
    #timeline > .option-list--option-highlighted, #backlog-list > .option-list--option-highlighted {
        background: $boost; }
    #timeline:focus > .option-list--option-highlighted, #backlog-list:focus > .option-list--option-highlighted {
        background: $hand-tint; color: $foreground; }
    #moment.hidden, #response.hidden, #timeline.hidden, #backlog-list.hidden, .story-only.hidden { display: none; }
    #timeline, #backlog-list { height: auto; max-height: 100%; border: none; margin-top: 1; background: transparent; }
    #controls #accept-all { color: $success; }
    #accept-all.hidden { display: none; }
    #choice-body { height: auto; max-height: 60%; }
    #calls-body { height: auto; max-height: 30; }
    #cost-text { margin-top: 1; }
    .step-count { color: $text-muted; }
    Step #dialog, Checking #dialog { padding: 0 2; }
    .explanation { margin-bottom: 1; }
    #choices { height: auto; max-height: 16; }
    MenuScreen #items { height: auto; max-height: 16; margin-top: 1; }
    MenuScreen #menu-context { color: $text-muted; margin-bottom: 1; }
    MenuScreen #menu-notice { color: $warning; margin-bottom: 1; }
    MenuScreen #no-matches { margin-top: 1; color: $warning; }
    MenuScreen #no-matches.hidden, MenuScreen #clear.hidden { display: none; }
    MenuScreen #menu-controls { height: 1; margin-top: 1; }
    MenuScreen #menu-controls Button { min-width: 8; height: 1; border: none; margin-right: 2;
                                       background: transparent; color: $text-muted; text-style: none; }
    MenuScreen #menu-controls Button:focus { background: $hand-tint; color: $foreground; text-style: bold; }
    MenuScreen, PathScreen, HelpScreen, ThemeScreen, SettingsScreen, StatementScreen, CallsScreen, TextScreen, Step, Checking,
    ChoiceScreen, BudgetScreen {
        align: center middle; }
    #dialog { width: 80%; max-width: 90; height: auto; max-height: 90%; border: thick $accent;
              background: $surface; padding: 1 2; }
    HelpScreen #dialog, ThemeScreen #dialog { height: 90%; }
    StatementScreen #dialog { max-width: 100; }
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
        Binding("f2", "settings", "Settings"),
        Binding("ctrl+q", "quit", "Save & quit", priority=True),
        Binding("left", "earlier", "Earlier"),  # shown and active only when stepping through history
        Binding("right", "later", "Later"),
    ]

    def __init__(self, store, speaker, provider, open_application, consultant_factory, tour=False, story=None,
                 settings=None, usage=None):
        super().__init__(settings)
        # The usage log session this workspace's paid replies are counted in, or None (tests, the story and the
        # tour), which hides the meter. What it says is cached in _meter: read on mount, after each reply and
        # when the cost screen opens, never while the footer is drawn.
        self.usage, self._meter, self._usage_mark = usage, None, None
        self.store, self.speaker, self.provider, self.tour = str(store), speaker, provider, tour
        # A story is read, not answered: its goal opens read-only with its chapters for narration.
        self.story = story
        self.chapters = {n: c for n, c in enumerate(story["chapters"], start=1)} if story else {}
        # None while looking at the live goal; otherwise the past revision on screen.
        self.revision, self._history = None, None
        self._open, self._consultant_factory = open_application, consultant_factory
        # The consultant in use, and what the case consults: the same, or for one reply a stand-in with deeper
        # reasoning, built once per model (``stand_in``). ``_asking`` names that model while it answers.
        self.consultant = consultant_factory(provider)
        self.chosen = ChosenConsultant(self.consultant)
        self._stand_ins, self._asking = {}, None
        self.case = open_application(self.chosen)
        self.view_name, self.explain, self.busy, self.answer_ready = "next", False, False, False
        self.workspace_value, self._restoring, self._save_timer = None, False, None
        # Which tree the Trees view shows: one of TREE_ORDER, "all", or None until first chosen.
        self.tree_choice = None
        # The statement chosen in the Trees view (a claim reference), where each drawn statement sits,
        # and the control to give focus back to when Ctrl+T leaves the trees.
        self.selected_claim, self._tree_spans, self._focus_before_trees = None, [], None
        # Whether the drawing on screen dims all but the chosen statement's chunk (see ``dims``).
        self._dimmed = False
        # What is folded away (interface state, kept for this session): per tree, and opened in the overview.
        self._folds, self._overview_open = {}, set()
        # Where a local inspection began (view, explanation, past moment, scroll, focus), for Esc.
        self.density = "compact"  # Compact is the default; Expanded repeats the complete context
        self._origin = None
        # The open menu's name, and its state as kept in the cursor (filter, choice, binding).
        self._menu_name, self._menu_state = None, None

    # ----- layout -------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Static(id="status")
        yield Static(id="pinned")
        with Horizontal(id="loop-row"):
            yield Static(id="loop")
            yield Static(id="measure")
        with Horizontal(id="body"):
            with Vertical(id="views-pane"):
                yield Static("VIEWS", id="views-title")
                yield Views(*self.view_options(), id="views")
            with Pane(id="column"):
                with VerticalScroll(id="main"):
                    yield Page(id="content", open_links=False)
                    yield TreeCanvas(id="canvas")
                    yield Timeline(id="timeline", classes="hidden")
                    yield BacklogList(id="backlog-list", classes="hidden")
                with Pane(id="response", classes="hidden" if self.story else ""):
                    yield TextArea("", id="editor", soft_wrap=True, show_line_numbers=False, tab_behavior="focus")
                    with Horizontal(id="controls"):
                        yield Button("Send ^s", id="send", variant="primary")
                        yield Button("Example answer", id="fill", classes="" if self.tour else "hidden")
                        yield Button("Retry", id="retry", variant="warning", classes="hidden")
                        yield Button("Retry with Sonnet", id="retry-deeper", classes="hidden")
                        yield Button("Accept all", id="accept-all", classes="hidden")
                        yield Button("Explain this", id="explain")
                        yield Button("Other moves", id="moves")
                        yield Button("Views", id="views-button")
                        yield Button("Finish tour", id="finish", variant="success",
                                     classes="" if self.tour else "hidden")
                        yield Static(id="hint")
                    yield Static(id="hint-below", classes="hidden")
            with VerticalScroll(id="inspector", classes="hidden"):
                yield Static(id="inspector-text")
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
        yield HintBar()

    def view_prompt(self, key):
        """A view's name in the list, with ▸ beside the one that is open; Backlog says how much waits."""
        waiting = len(self.backlog()) if key == "backlog" else 0
        return ("▸ " if key == self.view_name else "  ") + dict(VIEW_LABELS)[key] + (f" · {waiting}" if waiting else "")

    def view_options(self):
        """The Views list: every view, and under an open Trees view with something in it, the overview
        and the six trees in the method's order, with ▸ beside the one on screen."""
        options = []
        for key, _ in VIEW_LABELS:
            # Supporting views stay in Commands/Views; the sidebar follows actual case work.
            records = (self.workspace_value or {}).get('records', [])
            has_test = any(r['kind'] == 'test' for r in records)
            if key in ('reasoning', 'context') and key != self.view_name and not has_test:
                continue
            kinds = {'tests': {'test'}, 'actions': {'test', 'action'}}.get(key)
            if kinds and key != self.view_name and not any(r['kind'] in kinds for r in records):
                continue
            options.append(Option(self.view_prompt(key), id=key))
            if key == "trees" and self.view_name == "trees" and self.has_trees():
                shown = self.shown_tree()
                options += [Option(("  ▸ " if tree == shown else "    ") + name, id="tree:" + tree)
                            for tree, name in TREE_NAV.items()]
        return options

    def has_trees(self):
        return any(t["claims"] for t in ((self.workspace_value or {}).get("trees") or []))

    def refresh_views(self):
        """Rebuild the Views list for the open view (and tree), keeping the cursor on what is open."""
        views = self.query_one("#views", OptionList)
        options = self.view_options()
        views.clear_options()
        views.add_options(options)
        ids = [option.id for option in options]
        wanted = "tree:" + self.shown_tree() if "tree:" + self.shown_tree() in ids else self.view_name
        views.highlighted = ids.index(wanted)

    def on_mount(self):
        super().on_mount()
        self.title = "Reason Commons"
        # The trees are drawn in the theme's colours, so they are redrawn with it.
        self.theme_changed_signal.subscribe(self, lambda _: self.workspace_value and self.render_all())
        cursor = self.case.inspect()["cursor"] or {}
        # Steps saved after this point are this session's; their tree changes are marked.
        self._opened_revision = self.case.inspect()["case"]["revision"]
        self.refresh_workspace()
        if cursor.get("draft"):
            self._restoring = True
            editor = self.query_one("#editor", TextArea)
            editor.load_text(cursor["draft"])
            editor.cursor_location = caret_location(cursor["draft"], cursor.get("caret", len(cursor["draft"])))
            self._restoring = False
        if (cursor.get("display") or {}).get("tree") in TREE_ORDER + ["all"]:
            self.tree_choice = cursor["display"]["tree"]
        if (cursor.get("display") or {}).get("density") in DENSITIES:
            self.density = cursor["display"]["density"]
            self.render_all()
        if any(c["ref"] == cursor.get("selection") for t in self.workspace_value["trees"] for c in t["claims"]):
            self.selected_claim = cursor["selection"]
        if cursor.get("view") in dict(VIEW_LABELS) and cursor["view"] != "next":
            self.show_view(cursor["view"])
        if isinstance(cursor.get("menu"), dict):
            self.call_after_refresh(self.restore_menu, cursor["menu"])
        self.query_one("#earlier" if self.story else "#editor").focus()
        self.watch(self.screen, "focused", lambda _: (self.refresh_hints(), self.fit_answer_box(), self.refit_dimming()))
        self.on_resize()
        self.refresh_meter()
        if self._meter and self.provider == "anthropic" and self._meter["budget"] and \
                self._meter["month"]["usd"] >= self._meter["budget"]:
            self.notify(budget_notice(100, self._meter["month"]["usd"], self._meter["budget"]), timeout=10)

    MOMENT_LABELS = {"earlier": ("◀ Earlier", "◀ Earlier"), "later": ("Later ▶", "Later ▶"),
                     "now": ("Back to now", "Now"), "first": ("From the beginning", "First"),
                     "own": ("Start my own goal", "My own goal"), "home": ("Back to start", "Start screen")}

    def on_resize(self, event=None):
        if event is not None:
            self._terminal = event.size
        # The destinations list needs room; without it, the Views button reaches the same views.
        wide = self.terminal.width >= 100
        for key, labels in self.MOMENT_LABELS.items():
            self.query_one("#" + key, Button).label = labels[not wide]
        for name in ("#views-pane", "#views"):
            self.query_one(name).set_class(not wide, "hidden")
        self.query_one("#column").set_class(wide, "beside-views")
        self.query_one("#views-button").set_class(wide, "hidden")
        self.query_one("#editor").styles.max_height = 5 if self.terminal.height < 30 else 10
        if self.workspace_value is not None:  # the band, comparisons and welcome depend on the width
            self.render_all()

    def fit_reading(self):
        """Fit the reading pane above the answer box: as tall as what it holds, up to the room the box leaves.

        The box then sits right under a short question and stays on screen under a long page, which
        scrolls in the room it has. The hint about Enter and Send goes beside the buttons when they leave
        room for it, and under them otherwise."""
        try:
            column, main, response = (self.query_one(name) for name in ("#column", "#main", "#response"))
            controls, below = self.query_one("#controls"), self.query_one("#hint-below")
        except NoMatches:  # a refit that was queued as the workspace closed
            return
        used = sum(button.outer_size.width + button.styles.margin.right for button in controls.query(Button)
                   if button.display)
        beside = controls.size.width - used >= len(self.hint_text()) + 2
        # Moving the hint changes the box's height by its row; count that now, not a frame later.
        grows = (0 if beside else 1) - (0 if below.has_class("hidden") else 1)
        self.query_one("#hint").set_class(not beside, "hidden")
        below.set_class(beside, "hidden")
        margin = response.styles.margin
        taken = 0 if response.has_class("hidden") else (response.outer_size.height + grows
                                                         + margin.top + margin.bottom)
        room = max(3, column.size.height - taken)
        main.styles.max_height = room
        # The History list scrolls on its own, so it gets exactly what the heading above it leaves.
        timeline, page = self.query_one("#timeline"), self.query_one("#content")
        above = page.outer_size.height + max(page.styles.margin.bottom, timeline.styles.margin.top)
        timeline.styles.max_height = max(3, room - above)

    def fit_answer_box(self):
        """The answer box at the question it answers. On Next step it is the full box under the question;
        on any other view it names that question in its title and, while empty and not being written in,
        folds to one line, so the view gets the room. Tab or a click opens it again; a draft keeps it open."""
        if self.workspace_value is None:
            return
        try:
            response, editor = self.query_one("#response"), self.query_one("#editor", TextArea)
        except NoMatches:
            return
        elsewhere = self.view_name != "next" and self.revision is None and not self.story
        folded = elsewhere and not editor.text and not response.has_focus_within
        question = (self.workspace_value["question"] or {}).get("data", {})
        decision = question.get("decision") or STEPS["goal"][0]
        response.border_title = Content(f"Answer as {self.speaker}" + (f" · {decision}" if elsewhere else ""))
        # An example of the answer asked for, faint in an empty box. The tour has its own example button.
        example = None if self.tour or self.story or self.provider != "guided" else placeholder(self.workspace_value["question"])
        editor.placeholder = ("Tab here to write; the question is on Next step." if folded else example or "")
        if response.has_class("collapsed") != folded:
            response.set_class(folded, "collapsed")
            self.call_after_refresh(self.fit_reading)

    def hint_text(self):
        question = (self.workspace_value or {}).get('question') or {}
        if self.provider == 'guided' and question.get('data', {}).get('purpose') == 'continuation':
            return 'Enter: new line · Send: save contribution · AI consultant in Commands'
        model = self.model_name()
        return (f"Enter: new line · Send: get {REPLY_FROM.get(self.provider, f'the reply of {self.provider}')}"
                + (f" ({model})" if model else ""))

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
        """Every saved revision with what it changed, and every source (cached until the next save)."""
        if self._history is None:
            snapshots = self.case.history()["revisions"]
            sources = self.case.sources()["sources"]
            self._history = {"snapshots": snapshots, "entries": revision_changes(snapshots, sources),
                             "sources": sources}
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
        """One quiet line: the goal's name on the left, who you are and whether it is saved on the right.

        The view is named by the list and the page itself, and the keyboard by the focused pane's frame,
        so neither is repeated here."""
        w = self.workspace_value
        if w is None:
            return
        asking = self.send_to() + (f" ({self._asking})" if self._asking else "")
        state = (f"Asking {asking}…" if self.busy else "Answer ready" if self.answer_ready else "Saved")
        who = None if self.story else self.speaker  # a story is read, not answered as anyone
        if self.story or self.revision is not None:
            state = "Read-only"
        muted = themed("$text-muted", self.theme_variables)
        line = Table.grid(expand=True)
        line.add_column(no_wrap=True, overflow="ellipsis")
        line.add_column(justify="right", no_wrap=True)
        status = Text.assemble((f"{who} · " if who else "", muted),
                               (state, "bold" if self.answer_ready else muted))
        if self.terminal.width >= 100 and self.acceptance_mode() is not None:
            mode = 'automatic' if self.acceptance_mode() == 'automatic' else 'require acceptance'
            status.append(f' · Reasoning: {mode}', style=muted)
        line.add_row(Text(w["case_name"], style="bold"), status)
        self.query_one("#status", Static).update(line)

    def send_to(self):
        return SEND_TO.get(self.provider, self.provider)

    def render_all(self):
        w = self.workspace_value
        self.render_status()
        self.refresh_bindings()
        self.render_stepper()
        content = self.render_next() if self.view_name == "next" else self.render_view()
        self.query_one("#content", Markdown).update(content)
        drawing = {"trees": self.render_trees, "next": self.render_context, "tests": self.render_tests,
                   "goal": self.render_records, "actions": self.render_records,
                   "reasoning": self.render_reasoning}.get(self.view_name, lambda: None)()
        canvas = self.query_one("#canvas", Static)
        canvas.set_class(drawing is None, "hidden")
        if drawing is not None:
            canvas.update(drawing)
        canvas.can_focus = self.view_name == "trees" and bool(self._tree_spans)
        if self.focused is canvas and not canvas.can_focus:
            self.query_one("#main").focus()
        self.render_inspector()
        # The band never repeats what the view is showing: safeguards move into a comparison.
        band = self.band(protect=not self.shows_safeguards())
        self.query_one("#pinned", Static).display = band is not None
        if band is not None:
            self.query_one("#pinned", Static).update(band)
        timeline = self.query_one("#timeline", OptionList)
        timeline.set_class(self.view_name != "history", "hidden")
        backlog = self.query_one("#backlog-list", OptionList)
        backlog.set_class(self.view_name != "backlog" or not self.backlog(), "hidden")
        # The lists scroll, not the page.
        self.query_one("#main").set_class(self.view_name in ("history", "backlog"), "fills")
        if self.view_name == "history":
            self.fill_timeline(timeline)
        if self.view_name == "backlog":
            self.fill_backlog(backlog)
        imported = self.import_waiting()
        self.query_one('#accept-all', Button).label = 'Adopt import' if imported else 'Accept all'
        self.query_one("#accept-all").set_class(not self.reply_waiting() and not imported, "hidden")
        # The Views list names what waits in Backlog, so it changes with the case.
        views = self.query_one("#views", OptionList)
        if [str(o.prompt) for o in views.options] != [str(o.prompt) for o in self.view_options()]:
            self.refresh_views()
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
        # Beside Retry where there is room, and only when Retry would ask again; narrower, it is in Commands.
        deeper = self.boost() if retryable and self.terminal.width >= 100 else None
        offered = bool(deeper) and self.retry_asks_again(retryable[-1]["arguments"]["request_id"])
        self.query_one("#retry-deeper").set_class(not offered, "hidden")
        if offered:
            self.query_one("#retry-deeper", Button).label = f"Retry with {pricing.label(deeper).split()[0]}"
        if self.tour:
            state = self.tour_state()
            self.query_one("#coach", Static).update(coach_text(state))
            self.query_one("#fill").set_class(state not in EXAMPLE_ANSWERS, "hidden")
        for name in ("#hint", "#hint-below"):
            self.query_one(name, Static).update(escape_markup(self.hint_text()))
        self.fit_answer_box()
        self.refresh_hints()
        self.call_after_refresh(self.fit_reading)

    def render_stepper(self):
        """The loop line, which is the spine of the screen, and the goal's measure on its right.

        The measure is what makes progress visible, so while it is missing the line says so rather than
        leaving the person to wonder: "not set" in the warning colour."""
        w = self.workspace_value
        row = self.query_one("#loop-row")
        row.display = not self.story and (
            (w['question'] or {}).get('data', {}).get('purpose', '').startswith('guided:')
            or bool(w['comparisons']))
        looking_back = bool(w["historical"] or self.story)
        value = (((self.pinned_goal() or {}).get("data") or {}).get("measure") or "").strip()
        # The aside after Review gives way to a measure, which is worth more than it.
        wide = self.terminal.width >= 100 and not value
        steps = "" if looking_back else loop_line(loop_stage(w["question"]), wide, self.terminal.width - 2)
        self.query_one("#loop", Static).update(steps)
        label = "Measure: "
        room = self.terminal.width - 2 - Content.from_markup(steps).cell_length - 2  # the row's padding, a gap
        shown = Content("")
        if not looking_back and not value and room >= len(label) + len("not set"):
            shown = Content.assemble((label, "$text-muted"), ("not set", "$warning"))
        elif not looking_back and value and room >= len(label) + 20:
            shown = Content.assemble((label, "$text-muted"), clip(value, room - len(label), 1))
        self.query_one("#measure", Static).update(shown)

    def tour_state(self):
        return tour_state(self.workspace_value["question"], self.case.inspect()["case"]["records"])

    def pinned_goal(self):
        return latest(self.workspace_value["goals"], "goal")

    def band(self, protect=True):
        """The goal and its safeguards, at most two labelled lines; a cut is marked, and Goal shows it all.
        A goal that only waits in the Backlog is shown as proposed. None until a goal has been proposed."""
        goal = self.pinned_goal()
        if goal is None:
            proposed = next((e for e in self.backlog() if e["entry"] == "proposal" and e["kind"] == "goal"), None)
            if proposed is None or self.story:
                return None  # nothing recorded yet: the stepper's "Measure: not set" says so
            grid = Table.grid(padding=(0, 1))
            grid.add_column(style="bold", width=7, no_wrap=True)
            grid.add_column()
            grid.add_row("Goal", Text.assemble(("proposed, not yet accepted: ", "italic dim"),
                                               clip(proposed["summary"], self.terminal.width - 40, 1)))
            return grid
        expanded = self.density == "expanded" and not self.story
        width = self.terminal.width - 11 - expanded
        grid = Table.grid(padding=(0, 1))
        grid.add_column(style="bold", width=8 if expanded else 7, no_wrap=True)  # Expanded's "Baseline" fits
        grid.add_column()
        statement = goal["data"]["statement"]
        provisional = not goal["data"].get("measure") and "provisional" not in statement.lower()
        grid.add_row("Goal", Text.assemble(("provisional · ", "italic dim") if provisional else "",
                                           clip(statement, width - 14 * provisional,
                                                2 if self.terminal.height >= 30 else 1)))
        if expanded:
            for name in ("measure", "baseline", "horizon", "scope"):
                grid.add_row(name.capitalize(), Text(clip(goal["data"].get(name) or "not known yet", width, 1)))
            for index, protection in enumerate(goal["data"].get("protections") or ["none recorded"]):
                grid.add_row("Protect" if index == 0 else "", Text(clip(protection, width, 1)))
            for comparison in self.workspace_value["comparisons"]:
                data = comparison["test"]["data"]
                periods = ", ".join(dict.fromkeys(f["period"] for f in data.get("forecast") or [] if f.get("period")))
                grid.add_row("Test", Text(clip(" · ".join(filter(None, [data["statement"], data.get("scope"), periods,
                                                                       data.get("stop_condition")])), width, 1)))
        elif protect and not self.story:
            protections = " · ".join(goal["data"].get("protections") or []) or "none recorded"
            grid.add_row("Protect", Text(clip(protections, width, 1)))
        for breach in self.workspace_value.get("breaches") or []:
            grid.add_row(Text("Breach", style="bold red"),
                         Text(clip(f"{breach['measure']}: {breach['value']}, outside {breach['bound']}", width, 1),
                              style="bold"))
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
        return main.content_size.width or self.terminal.width - (22 if self.terminal.width >= 100 else 4)

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
            # The heading is the strongest line, the question plain, and an "optional answer" hint the quietest.
            question, hint = split_hint(data["primary_prompt"])
            lines += [f"## {md(data.get('decision') or 'Next question')}", ""]
            purpose = str(data.get("purpose") or "")
            if " " in purpose.strip():  # a coded purpose (guided steps, fixtures) is not for people
                lines += [f"*{md(purpose)}*", ""]
            lines += [md(question), ""]
            lines += [f"###### {md(hint)}", ""] * bool(hint)
            rationale = data["rationale"]
            # What changes the next decision: work done whose effect is not known yet, and tests whose goal moved.
            for notice in w.get("notices") or []:
                lines += [f"**{md(notice['message'])}** It says the work happened, not that it had its effect.", ""]
            for review in w.get("test_reviews") or []:
                changed = ("an earlier version of the goal" if any(f["field"] == "goal_ref" for f in review["flags"])
                           else "something that has since changed")
                lines += [f"> **Review needed:** the test *{md(review['statement'])}* was planned for {changed}. "
                          "Check it still serves the current goal; **h** in Backlog says it still holds.", ""]
            news = self.tree_news()
            if news and not self.heard_in_full():  # a small change is drawn below the question instead
                lines += [f"*In the trees, the last step: {md(tree_summary(news))}. Ctrl+T shows them.*", ""]
        else:
            # A new goal: its name is in the header, so the first question builds on it.
            lines += [f"## {md(STEPS['goal'][0])}", "",
                      "What would count as better? Describe it in your own words." if self.provider == "guided"
                      else "What is happening, and what would count as better?", "",
                      "###### Your words are kept as written. Unknowns can stay open. Nothing is sent until you "
                      "press Send.", ""]
            rationale = (STEPS["goal"][2] if self.provider == "guided"
                         else "A clear picture of success comes before choosing what to change.")
        if self.explain:
            lines += ["> **Why this question** (saved explanation, no consultant call)", ">",
                      "> " + md(rationale), ""]
            served = (w["question"] or {}).get("data", {}).get("goal_ref")
            goal = {r["ref"]: r for r in self.viewed_records()}.get(served)
            if goal:
                current = (self.pinned_goal() or {}).get("ref")
                note = "" if served == current else " (worded so then; the goal has a newer version)"
                lines += [f"> **Serves the goal:** {md(goal['data']['statement'])}{note}", ""]
            if not w["question"]:
                lines += ["How one loop works, one small change at a time:", "",
                          WELCOME_WIDE if self.terminal.width >= 100 else WELCOME_NARROW,
                          "*This shows how one loop works, not what causes what.*", ""]
        for pending in w["pending_requests"]:
            value = pending["input"]
            if value["base_revision"] == w["revision"] and value["response_target"] == w["target"]["response_target"]:
                lines += [f"> **Saved, but not answered yet:** {STATUS_TEXT.get(pending['status'], pending['status'])}. "
                          "Your words are kept. Use **Retry** to ask again.", ">", "> " + md(value["text"]), ""]
        return "\n".join(lines)

    def backlog(self):
        """What waits for a decision, live; nothing while looking back or reading a story."""
        if self.workspace_value is None or self.revision is not None or self.story:
            return []
        return self.workspace_value.get("backlog") or []

    def reply_waiting(self):
        """The last reply's proposals that still wait, when the live question is on screen."""
        reply = (self.workspace_value or {}).get("reply")
        if not reply or self.revision is not None or self.story:
            return []
        return [r for r in reply["records"] if r["status"] == "proposed"]

    def heard_in_full(self):
        """Whether what the last reply proposed, or added under automatic acceptance, is small enough to be
        drawn under the question."""
        shown = self.reply_shown()
        return bool(shown) and len(shown) <= HEARD_AT_MOST

    def reply_shown(self):
        """The records the reply block is about: the last reply's waiting proposals, or, right after a reply
        accepted under the automatic setting, what it added."""
        waiting = self.reply_waiting()
        if waiting:
            return waiting
        reply, step = (self.workspace_value or {}).get("reply"), self.marked_step()
        if reply and reply["automatic"] and step and step["request_id"] == reply["request_id"]:
            return [r for r in reply["records"] if r["status"] == "accepted"]
        return []

    def heard(self):
        """What the last reply proposes, drawn as the trees draw it and set beside the words it came from,
        under the question that followed.

        This is the moment the person who said it still knows what they meant, so a wrong reading is
        cheapest to catch here. Nothing a reply proposes is in the model until it is accepted; Accept all
        takes all of it, Backlog one at a time. Under automatic acceptance it says what entered the model.
        Returns the drawing and the records it draws; (None, no records) when there is nothing to show, or
        more than can be read at a glance (an import, say), which a line sums up instead."""
        shown = self.reply_shown()
        w = self.workspace_value
        if not shown:
            return None, set()
        waiting = bool(self.reply_waiting())
        if len(shown) > HEARD_AT_MOST:
            what = (f"{len(shown)} proposals from the last reply wait for you. Accept all takes them; Backlog "
                    "decides them one by one." if waiting else
                    f"{len(shown)} records from the last reply entered your model under your automatic acceptance.")
            return [Text(what, style="italic")], set()
        request = w["reply"]["request_id"]
        source = self.history()["sources"].get(request, {})
        width = max(40, self.query_one("#main").size.width - 7)
        mine = not source.get("speaker") or same_person(source["speaker"], self.speaker)
        whose = "YOUR ANSWER" if mine else "THE LAST ANSWER"
        parts = [label(f"PROPOSED FROM {whose} · NOT YET IN YOUR MODEL" if waiting else
                       f"ADDED TO YOUR MODEL FROM {whose}, UNDER YOUR AUTOMATIC ACCEPTANCE")]
        records = {r["ref"]: r["record"] for r in shown}
        nodes = {c["ref"]: c for tree in w["trees"] for c in tree["claims"]}
        everything = {**{r["ref"]: r for r in w["records"]}, **w["proposals"]}
        drawn = set(records)
        for name in TREE_ORDER:
            claims = [r for r in records.values() if r["kind"] == "claim" and r["data"]["tree"] == name]
            links = [r for r in records.values() if r["kind"] == "link" and r["data"]["tree"] == name]
            if not claims and not links:
                continue
            part = {"tree": name, "claims": [], "links": []}
            for record in claims:
                old = everything.get(record["data"].get("replaces"))
                part["claims"].append({"ref": record["ref"], "role": record["data"]["role"],
                                       "statement": record["data"]["statement"], "basis": record["data"].get("basis"),
                                       "earlier_wording": [old["data"]["statement"]] if old else [], "tests": []})
            present = {c["ref"] for c in part["claims"]}
            for record in links:
                ends = record["data"]["from_ref"], record["data"]["to_ref"]
                for end in ends:
                    if end not in present and (end in nodes or end in everything):
                        found = nodes.get(end) or {"ref": end, "statement": everything[end]["data"]["statement"],
                                                   "role": everything[end]["data"].get("role", "goal"),
                                                   "basis": None, "earlier_wording": [], "tests": []}
                        part["claims"].append(found)
                        present.add(end)
                if set(ends) <= present:
                    part["links"].append({"ref": record["ref"], "relation": record["data"]["relation"],
                                          "from": ends[0], "to": ends[1], "assumption": record["data"].get("assumption")})
            parts += [Text(TREE_TITLES[name][0], style="bold"),
                      styled(tree_lines(part, width, fresh=set(records), title=False, whole=False),
                             self.theme_variables)]
        rows = Table.grid(padding=(0, 2))
        rows.add_column(style="bold dim", max_width=24)
        rows.add_column()
        for record in records.values():
            if record["kind"] not in ("claim", "link"):
                for name, value in context_rows(w, record, None):
                    rows.add_row(name, Text(str(value)))
        if rows.row_count:
            parts.append(rows)
        if source.get("text"):
            who = "You" if mine else source["speaker"]
            said = textwrap.shorten(" ".join(str(source["text"]).split()), 240, placeholder=" …")
            parts.append(Text.assemble((f"{who} wrote, {moment(source['timestamp'])}: ", "dim"), (f"“{said}”", "italic")))
        parts.append(Text("Accept all admits these to your model; it does not make them true. Backlog decides them "
                          "one by one. Not what you meant? Reject it, or say so in your answer." if waiting else
                          "Not what you meant? Undo it from History, or say so in your answer.", style="dim"))
        return parts, drawn

    def render_context(self):
        """What the current question builds on, below it: what the last answer added to the trees, then each
        forecast beside its results, then the other records the consultant attached, leaving out what the band
        shows."""
        if self.revision is not None:
            return None
        if self.story:
            return self.story_rows()
        w = self.workspace_value
        compared = self.compared()
        drawn = {r["ref"] for c in compared for r in [c["test"], *c["observations"], *c["reviews"]]}
        heard, told = self.heard()
        drawn |= told  # what the block above draws is not listed again below it
        parts = heard + [Text("")] * bool(compared) if heard else []
        parts += [comparison_block(w, c, self.pane_width() >= WIDE) for c in compared]
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

    def record_grid(self, records):
        """Records as one aligned label column, a blank row between records. The goal's safeguards
        are listed one to a line; a goal in Loop actions is left to the band and the Goal view."""
        rows = Table.grid(padding=(0, 2))
        rows.add_column(style="bold dim", max_width=24)
        rows.add_column()
        for record in records:
            if rows.row_count:
                rows.add_row("", "")
            for name, value in context_rows(self.workspace_value, record, None):
                if name == "Protect" and record["kind"] == "goal":
                    value = "\n".join(record["data"].get("protections") or []) or "none recorded"
                rows.add_row(name, Text(str(value)))
        return rows

    def render_records(self):
        """Goal: the goal in full. Loop actions: each test and the action that carries it out."""
        records = [r for r in self.workspace_value["records"] if r["kind"] in RECORD_KINDS[self.view_name]]
        return self.record_grid(records) if records else None

    def render_reasoning(self):
        """What is still open first, then the loop's records, then the trees as one line each."""
        w = self.workspace_value
        records = {r["ref"]: r for r in w["records"]}
        parts = []
        if w["uncertainty"]:
            open_items = {}
            for item in w["uncertainty"]:
                kind = records.get(item["ref"], {}).get("kind")
                what = re.sub(r" is not established\.?$", "", item["message"])
                open_items.setdefault(OPEN_KINDS.get(kind, "Other"), []).append(what)
            rows = Table.grid(padding=(0, 2))
            rows.add_column(style="bold dim", max_width=24)
            rows.add_column()
            for name, items in open_items.items():
                rows.add_row(name, Text(" · ".join(items)))
            parts += [Text.assemble(("Still open", "bold"), ("  not established yet", "dim")), rows]
        loop = [r for r in w["records"] if r["kind"] not in ("intervention", "claim", "link", "retraction")]
        if loop:
            parts += [Text("")] * bool(parts) + [Text("The loop", style="bold"), self.record_grid(loop)]
        trees = [t for t in w["trees"] if t["claims"]]
        withdrawn = [r for r in w["records"] if r["kind"] == "retraction"]
        if trees or withdrawn:
            rows = Table.grid(padding=(0, 2))
            rows.add_column(style="bold dim", max_width=24)
            rows.add_column()
            for tree in trees:
                count = len(tree["claims"])
                rows.add_row(TREE_TITLES[tree["tree"]][0], Text(f"{count} statement{'s' * (count != 1)}"))
            for record in withdrawn:
                rows.add_row("Withdrawn", Text(str(record["data"]["reason"])))
            parts += [Text("")] * bool(parts) + [Text.assemble(("In the trees", "bold"), ("  Ctrl+T opens them", "dim")),
                                                 rows]
        return Group(*parts) if parts else None

    def render_view(self):
        w, view = self.workspace_value, self.view_name
        title = dict(VIEW_LABELS)[view]
        lines = [f"## {title}", ""]
        if view == "history":
            if self.reconstructed_development():
                lines += ['This is the reconstructed development history from your prompt. '
                          'Each stage shows why the next step was needed and what entered the model. '
                          'The dates are import dates; historical dates were not supplied.', '',
                          'Reconstruction and adoption: **RC reconstruction editor (AI)**. '
                          'Original human and AI source words remain separately attributed.', '']
            lines.append("Every saved step, oldest first, and what entered the model. Enter opens one as it was; "
                         "u undoes a step's acceptance, after showing what goes with it.")
            return "\n".join(lines)
        if view == "backlog":
            return self.backlog_page()
        if view == "context":
            return self.context_page()
        if view == "sources":
            sources = [s for s in w["sources"].values() if "request_id" in s]
            # Who wrote matters with more than one voice, or when the one voice is not you (a goal someone shared).
            names = {s["speaker"] for s in sources}
            shared = len(names) > 1 or any(not same_person(name, self.speaker) for name in names)
            for source in sorted(sources, key=lambda s: s["request_id"], reverse=True):
                who = f"{md(source['speaker'])} · " if shared else ""
                lines += [f"###### {who}{md(moment(source['timestamp']))}", "",
                          "> " + md(source["text"] or "(empty)").replace("\n", "  \n> "), ""]
            for source in w['sources'].values():
                if 'content_base64' not in source:
                    continue
                lines += [f"###### {md(source.get('speaker', 'Unknown'))} · {md(source.get('name', 'Source'))}", ""]
                # Literal text, never document instructions or executable markup.
                content = base64.b64decode(source['content_base64'])
                try:
                    text = content.decode('utf-8')
                except UnicodeDecodeError:
                    lines += [f"Binary attachment: {len(content)} bytes retained locally.", ""]
                else:
                    lines += ["> " + md(text).replace("\n", "  \n> "), ""]
            return "\n".join(lines) if len(lines) > 2 else "\n".join(lines + ["Nothing written yet."])
        if view == "trees":
            return self.trees_page()
        if view == "tests":
            if not w["comparisons"]:
                lines.append("No test yet.")
            return "\n".join(lines)
        kinds = RECORD_KINDS.get(view)
        shown = [r for r in w["records"] if (r["kind"] in kinds if kinds else r["kind"] != "intervention")]
        if not shown and not (view == "reasoning" and w["uncertainty"]):
            lines.append("Nothing recorded here yet.")
        return "\n".join(lines)

    def context_page(self):
        """Everything the live question rests on, complete and in one place: where the case is saved, the goal
        with all its fields, the tests in the model and their boundaries, what is being answered, what waits
        and any breach. Local; nothing is sent."""
        w = self.workspace_value
        state = "read-only" if self.story or self.revision is not None else "saved"
        lines = ["## Case context", "", "Everything the current question rests on, in full. Local: nothing is sent.",
                 "", f"**{md(w['case_name'])}** · {state} at revision {w['revision']} · answering as "
                 f"{md(self.speaker)} · proposals are {'accepted automatically' if w.get('acceptance') == 'automatic' else 'held for you'}",
                 ""]
        for breach in w.get("breaches") or []:
            lines += [f"> **Breach:** {md(breach['measure'])}: {md(breach['value'])}, outside {md(breach['bound'])}", ""]
        goal = self.pinned_goal()
        lines += ["### Goal", ""]
        if goal is None:
            lines += ["No goal in the model yet." + (" One waits in Backlog." if any(
                e["entry"] == "proposal" and e["kind"] == "goal" for e in self.backlog()) else ""), ""]
        else:
            data = goal["data"]
            lines += [f"- **Goal** ({goal['ref']}): {md(data['statement'])}"
                      + (" · provisional: no measure yet" if not data.get("measure") else "")]
            lines += [f"- **{name.capitalize()}:** {md(data[name]) if data.get(name) else 'not known yet'}"
                      for name in ("measure", "baseline", "horizon", "scope")]
            lines += [f"- **Protect:** {md(p)}" for p in data.get("protections") or []] or ["- **Protect:** none recorded"]
            lines.append("")
        tests = [c for c in self.case.workspace(view="tests")["comparisons"]]
        lines += ["### Tests in the model", ""]
        for comparison in tests:
            data = comparison["test"]["data"]
            periods = ", ".join(dict.fromkeys(f["period"] for f in data.get("forecast") or [] if f.get("period")))
            lines += [f"- **{md(data['statement'])}** ({comparison['test']['ref']}) · scope: "
                      f"{md(data.get('scope') or 'not known yet')} · period: {md(periods or 'not known yet')} · "
                      f"stop if: {md(data.get('stop_condition') or 'not known yet')} · review: "
                      f"{md(data['review_date'] + '; no reminder scheduled' if data.get('review_date') else 'no date')}"]
        lines += ["- None yet."] * (not tests) + [""]
        question = (w["question"] or {}).get("data", {})
        lines += ["### Answering", "", f"- {md(question.get('primary_prompt') or 'The first question: what is happening?')}"
                  + (f" ({w['target']['response_target']}, revision {w['target']['base_revision']})"
                     if w["target"]["response_target"] else ""), ""]
        waiting = [e for e in self.backlog() if e["entry"] == "proposal"]
        flagged = [e for e in self.backlog() if e["entry"] == "review"]
        pending = w.get("pending_requests") or []
        lines += ["### What waits", "",
                  f"- {len(waiting)} proposal{'s' * (len(waiting) != 1)} in Backlog, not yet in the model",
                  f"- {len(flagged)} record{'s' * (len(flagged) != 1)} flagged for review",
                  f"- {len(pending)} answer{'s' * (len(pending) != 1)} saved but not answered yet",
                  f"- {sum(1 for s in w['membership'].values() if s == 'accepted')} records accepted into the model", ""]
        return "\n".join(lines)

    def trees_page(self):
        """The Trees page above the drawing: the tree's name, its question, which way to read it and what it
        does not say yet; for the overview, how it works. With nothing recorded, the six questions and the ways
        to start."""
        w = self.workspace_value
        if not self.has_trees():
            lines = ["## Trees", "", "No trees yet. They answer six questions about a goal:", ""]
            lines += [f"- ○ **{name}**: {question}" for name, question in TREE_TITLES.values()]
            if self.provider == "guided":
                lines += ["", "To grow them as you talk, switch to Claude or a local model: Ctrl+P, **Consultant**. "
                              "The built-in guide asks the loop's questions in order; it does not add to the trees."]
            else:
                lines += ["", "They grow as you talk: tell the consultant what causes the problem, what conflict "
                              "keeps you stuck, what stands in the way, or what you plan to do."]
            lines += ["", "Or bring in trees you already have: Ctrl+P, **Import trees**.", "",
                      "###### To see six finished trees first: on the home screen, Explore a real commons."]
            return "\n".join(lines)
        shown, news = self.shown_tree(), self.tree_news(live_only=False)
        lines = []
        if self.query_one("#views").has_class("hidden"):  # no Views list to name the trees: a strip instead
            strip = [f"**▸ {name}**" if key == shown else name
                     for key, name in [*list(TREE_NAV.items())[1:], ("all", "All six")]]
            lines += [" · ".join(strip), ""]
        if shown == "all":
            lines += ["## All six trees", "", "Six questions, each folded at what its tree is for.", "",
                      "###### Space unfolds a branch here; Enter opens its tree."]
        else:
            name, question = TREE_TITLES[shown]
            lines += [f"## {name}", "", question, "", f"###### {READING[shown]}"]
            # What the tree holds and what it does not say yet, so its unfinished state shows without a prompt.
            tree = next(t for t in w["trees"] if t["tree"] == shown)
            if tree["claims"]:
                lines += ["", f"###### {md(tally_line(tree))}"]
        if news:
            step = "This step" if self.revision is not None else "The last step"
            lines += ["", f"*{step}: {md(tree_summary(news))}. NEW and REWORDED mark those statements.*"]
        waiting = [e for e in self.backlog() if e["entry"] == "proposal" and e["kind"] in ("claim", "link", "retraction")]
        if waiting:
            lines += ["", f"###### {len(waiting)} proposal{'s' * (len(waiting) != 1)} for the trees wait in Backlog; "
                          "they are drawn here once accepted."]
        return "\n".join(lines)

    # ----- the backlog ----------------------------------------------------
    def backlog_page(self):
        """The Backlog page above its list: what waits, how acceptance works now, and a goal to decide first."""
        w, entries = self.workspace_value, self.backlog()
        lines = ["## Backlog", ""]
        if self.revision is not None or self.story:
            return "\n".join(lines + ["The backlog is live: Back to now to decide what waits."])
        automatic = w["acceptance"] == "automatic"
        if not entries:
            lines.append("Nothing waits. What a reply proposes appears here until you accept or reject it."
                         if not automatic else
                         "Nothing waits. Replies' proposals enter your model as they arrive, under your automatic "
                         "acceptance (Commands to change it).")
            return "\n".join(lines)
        proposals = sum(e["entry"] == "proposal" for e in entries)
        reviews = len(entries) - proposals
        said = [f"{proposals} proposal{'s' * (proposals != 1)} wait" + ("s" if proposals == 1 else "")] * bool(proposals)
        said += [f"{reviews} record{'s' * (reviews != 1)} flagged for review"] * bool(reviews)
        lines += [" and ".join(said) + ", in the order they are best decided: what an entry needs comes first.", ""]
        if any(e["decide_first"] for e in entries):
            lines += ["**A new goal is proposed. Decide it first: everything else is judged against the goal.**", ""]
        lines.append("###### Enter: choices · a: accept · r: reject · h: a flagged record still holds. Accepting "
                     "admits it to your model; it does not make it true." + (
                         " New replies are accepted automatically." if automatic else ""))
        return "\n".join(lines)

    def entry_row(self, number, entry):
        """One Backlog row: its place, what it is, its words, and what it waits for or why it is flagged."""
        record = entry["record"]
        where = TREE_TITLES[entry["tree"]][0] if entry.get("tree") else KIND_NAMES[entry["kind"]]
        if entry["kind"] == "claim":
            where += ", " + ROLE_LABELS[record["data"]["role"]].lower()
        elif entry["kind"] == "goal":
            where = "Goal" + (", new version" if entry.get("replaces") else "")
        text = Text(f"{number:>2}. ", style="dim")
        if entry["entry"] == "review":
            text.append("Review  ", style=themed("$warning", self.theme_variables))
        elif entry["decide_first"]:
            text.append("Decide first  ", style="bold " + themed("$warning", self.theme_variables))
        text.append(f"{where}: ", style="bold dim")
        text.append(textwrap.shorten(" ".join(str(entry["summary"]).split()), 90, placeholder=" …"))
        if entry["waits_for"]:
            text.append("  · waits for " + ", ".join(self.entry_name(ref) for ref in entry["waits_for"]), style="dim")
        for flag in entry.get("flags", []):
            change = {"new_version": "was reworded", "withdrawn": "was withdrawn", "undone": "was undone"}[flag["change"]]
            text.append(f"  · stated before “{textwrap.shorten(flag['cites_summary'], 40, placeholder='…')}” {change}",
                        style="dim")
        return text

    def entry_name(self, ref):
        """A waiting proposal named by its place in the Backlog, so a reader can find it there."""
        for number, entry in enumerate(self.backlog(), 1):
            if entry["entry"] == "proposal" and entry["ref"] == ref:
                return f"{number}"
        return ref

    def fill_backlog(self, listing):
        entries = self.backlog()
        current = listing.highlighted
        listing.clear_options()
        listing.add_options([Option(self.entry_row(n, e), id=f"{e['entry']}:{e['ref']}")
                             for n, e in enumerate(entries, 1)])
        if entries:
            listing.highlighted = current if current is not None and current < len(entries) else 0

    def chosen_entry(self):
        listing = self.query_one("#backlog-list", OptionList)
        entries = self.backlog()
        if self.view_name != "backlog" or listing.highlighted is None or listing.highlighted >= len(entries):
            return None
        return entries[listing.highlighted]

    def entry_details(self, entry, markdown=True):
        """An entry in full: the exact record, the words it came from, what it needs, and any review.
        Markdown for a dialog; plain text (``markdown=False``) for the panel beside the list."""
        record, data = entry["record"], entry["record"]["data"]
        md = globals()["md"] if markdown else str
        lines = []
        if entry["entry"] == "review":
            lines += ["**Flagged for review.** It was stated before something it cites changed. Nothing about it has "
                      "changed and it is not marked false.", ""]
            for flag in entry["flags"]:
                change = {"new_version": "was reworded", "withdrawn": "was withdrawn", "undone": "was undone"}
                lines.append(f"- It cites “{md(flag['cites_summary'])}”, which {change[flag['change']]}"
                             + (f" to “{md(flag['now_summary'])}”." if flag.get("now_summary") else "."))
            lines.append("")
        bold = (lambda text: f"**{text}**") if markdown else str
        end = "  " if markdown else ""
        for name, value in context_rows(self.workspace_value, record, None):
            if entry["kind"] != "link":
                lines.append(f"{bold(md(name))}: {md(value)}{end}")
        if entry["kind"] == "link":
            lines.append(f"{bold(TREE_TITLES[data['tree']][0] + ' link')}: {md(self.link_words(record))}{end}")
            if data.get("assumption"):
                lines.append(f"{bold('Assuming')}: {md(data['assumption'])}{end}")
        if entry.get("replaces"):
            lines.append(f"{bold('New version of')}: {md(entry['replaces']['summary'])}{end}")
        if entry["waits_for"]:
            lines.append(f"{bold('Waits for')}: " + "; ".join(md(self.record_words(ref)) for ref in entry["waits_for"])
                         + end)
        words = [w for w in entry.get("words") or [] if w]
        if words:
            lines += ["", "From the words: " + " ".join(f"“{md(' '.join(w.split()))}”" for w in words)]
        return "\n".join(lines)

    def record_words(self, ref):
        """A record in words: a statement's own, or for a link or withdrawal the statements it concerns."""
        records = {r["ref"]: r for r in self.case.inspect()["case"]["records"]}
        return describe(records[ref], records) if ref in records else ref

    def link_words(self, record):
        records = {r["ref"]: r for r in self.case.inspect()["case"]["records"]}
        return describe(record, records)

    @on(OptionList.OptionSelected, "#backlog-list")
    def backlog_selected(self, event):
        entry = self.chosen_entry()
        if entry is None:
            return
        choices = ([("still_holds", "Still holds · records that you looked and it stands"),
                    ("about", "Answer about this · puts its words in your answer; nothing is sent")]
                   if entry["entry"] == "review" else
                   [("accept", "Accept · admits it to your model, with what it needs"),
                    ("reject", "Reject · final, with what needs it")])
        title = ("Review: " if entry["entry"] == "review" else "Proposed: ") + textwrap.shorten(
            " ".join(str(entry["summary"]).split()), 70, placeholder="…")
        self.push_screen(ChoiceScreen(title, self.entry_details(entry), choices + [("back", "Back")]),
                         lambda key: self.entry_chosen(entry, key))

    def entry_chosen(self, entry, key):
        if key in ("accept", "reject", "still_holds"):
            self.perform(key, [entry["ref"]])
        elif key == "about":
            self.answer_about_record(entry["record"])

    def action_decide(self, action):
        entry = self.chosen_entry()
        if entry is None:
            return
        if (action == "still_holds") != (entry["entry"] == "review"):
            self.notify("Accept and reject decide a proposal; a flagged record is reviewed with h (still holds).",
                        severity="warning")
            return
        self.perform(action, [entry["ref"]])

    def perform(self, action, refs, confirmed=False):
        """Ask the application to record a decision. When it would take more than was chosen (or is an undo),
        the application lists everything first, and nothing changes until the person confirms."""
        if self.story or self.revision is not None:
            self.notify("This is a record of what happened; Back to now to decide.")
            return
        revision = self.workspace_value["revision"]
        if action == "still_holds":
            result = self.case.still_holds(refs[0], self.speaker, revision)
        else:
            result = getattr(self.case, action)(refs, self.speaker, revision, confirmed=confirmed)
        if result["status"] == "confirm":
            self.push_screen(ChoiceScreen(self.decision_title(action, result), self.consequences(action, result),
                                          [("confirm", "Confirm" + (": undo, finally" if action == "undo" else "")),
                                           ("back", "Back, nothing changes")]),
                             lambda key: key == "confirm" and self.perform(action, refs, confirmed=True))
            return
        if result["status"] != "saved":
            self.notify(result.get("message") or result["status"], severity="warning", timeout=8)
            self.refresh_workspace()
            return
        self._history = None
        self.refresh_workspace()
        self.refresh_views()
        self.notify(self.decided_words(action, result))
        self.schedule_checkpoint()

    def decision_title(self, action, result):
        count = len(result["refs"])
        return {"accept": f"Accept {count} together?", "reject": f"Reject {count} together?",
                "undo": "Undo? This is final."}[action]

    def consequences(self, action, result):
        verb = {"accept": "Enters your model", "reject": "Rejected, finally", "undo": "Leaves your model"}[action]
        lines = [f"**{verb}:**", ""] + [f"- {md(self.record_words(ref))}" for ref in result["refs"]]
        if result.get("leaves"):
            lines += ["", "**Leaves your trees with it, because it joins what is withdrawn:**", ""]
            lines += [f"- {md(self.record_words(ref))}" for ref in result["leaves"]]
        if result["closes"]:
            lines += ["", "**Closed, because what they need will not be in your model:**", ""]
            lines += [f"- {md(self.record_words(ref))}" for ref in result["closes"]]
        if result["flags"]:
            lines += ["", "**Flagged for review, because they cite what changes:**", ""]
            lines += [f"- {md(self.record_words(flag['ref']))}" for flag in result["flags"]]
        if action == "undo":
            lines += ["", "History keeps the words, the proposal, its acceptance and this undo. An undo cannot be "
                          "undone, and what leaves does not return to the Backlog; the consultant may propose it again."]
        return "\n".join(lines)

    def decided_words(self, action, result):
        count = len(result["refs"])
        done = {"accept": f"Accepted {count}: in your model now.", "reject": f"Rejected {count}.",
                "undo": f"Undone: {count} left your model.", "still_holds": "Recorded: it still holds.",
                "acceptance": "Saved."}[action]
        more = []
        if result.get("leaves"):
            more.append(f"{len(result['leaves'])} link{'s' * (len(result['leaves']) != 1)} left your trees with it")
        if result.get("closes"):
            more.append(f"{len(result['closes'])} waiting proposal{'s' * (len(result['closes']) != 1)} closed")
        if result.get("flags"):
            more.append(f"{len(result['flags'])} flagged for review in Backlog")
        return done + (" " + "; ".join(more) + "." if more else "")

    @on(Button.Pressed, "#accept-all")
    def accept_all_pressed(self):
        if self.import_waiting():
            self.adopt_import()
        else:
            self.accept_reply()

    def import_waiting(self):
        """Pending records introduced by the reconstruction, excluding later replies."""
        if self.story or self.revision is not None or not self.workspace_value['proposals']:
            return []
        pending = self.workspace_value['proposals']
        previous_records, previous_requests = set(), set()
        imported = []
        for snapshot in self.history()['snapshots']:
            requests = set(snapshot['applied_requests'])
            reconstruction = any((snapshot.get('adapter_versions') or {}).get(request) == 'commons-import/2'
                                 for request in requests - previous_requests)
            if reconstruction:
                imported.extend(r['ref'] for r in snapshot['records']
                                if r['ref'] not in previous_records and r['ref'] in pending)
            previous_records = {r['ref'] for r in snapshot['records']}
            previous_requests = requests
        return imported

    def adopt_import(self):
        refs = self.import_waiting()
        if refs:
            self.perform('accept', refs)

    def accept_reply(self):
        waiting = self.reply_waiting()
        if waiting:
            self.perform("accept", [r["ref"] for r in waiting])

    def acceptance_mode(self):
        if self.workspace_value is not None and not self.story and self.revision is None:
            return self.workspace_value['acceptance']
        return None

    def set_acceptance(self, mode):
        result = self.case.set_acceptance(mode, self.speaker, self.workspace_value["revision"])
        if result["status"] != "saved":
            self.notify(result.get("message") or result["status"], severity="warning")
            return
        self._history = None
        self.refresh_workspace()
        self.notify("From now on, a reply's proposals enter your model as it arrives; each can be undone from "
                    "History. What already waits still waits." if mode == "automatic" else
                    "From now on, a reply's proposals wait in Backlog for you.")

    def action_undo_step(self):
        """u in History: undo what the chosen step accepted and is still in the model, after showing what goes."""
        timeline = self.query_one("#timeline", OptionList)
        refs = self.undoable(timeline.highlighted)
        if not refs:
            self.notify("Nothing this step accepted is in your model now.", severity="warning")
            return
        self.perform("undo", refs)

    def undoable(self, revision):
        """What the step at ``revision`` accepted that is still accepted now."""
        if revision is None or self.story or self.workspace_value is None:
            return []
        entries = self.history()["entries"]
        if revision >= len(entries):
            return []
        membership = self.case.workspace(view="backlog")["membership"]
        return [ref for decision in entries[revision]["decisions"] if decision["action"] == "accept"
                for ref in decision["refs"] if membership.get(ref) == "accepted"]

    def answer_about_record(self, record):
        """Put a flagged record's words at the end of the answer, as Answer about this does for a statement."""
        editor = self.query_one("#editor", TextArea)
        words = describe(record) if record["kind"] != "link" else self.link_words(record)
        editor.insert(("" if not editor.text or editor.text.endswith(("\n", " ")) else "\n") + f"About “{words}”: ",
                      editor.document.end)
        self.show_view("next")
        editor.focus()

    def folded(self):
        """The statements drawn folded: in the overview every tree's starting statements, except those
        opened there; in one tree, those folded with Space."""
        if self.shown_tree() == "all":
            step = self.marked_step(live_only=False)
            fresh = set(step["fresh"]) if step else set()
            starts = set()
            for tree in self.workspace_value["trees"]:
                below = branches(tree)
                for ref in roots(tree):
                    seen, todo = set(), [ref]
                    while todo:
                        for child in below[todo.pop()]:
                            if child not in seen:
                                seen.add(child)
                                todo.append(child)
                    # A short branch is shown whole, and so is one the last step added to; a long branch,
                    # or a wholly new one (its start says NEW, its fold how much changed), starts folded.
                    if len(seen) > OVERVIEW_OPEN and not (seen & fresh and ref not in fresh):
                        starts.add(ref)
            return starts ^ self._overview_open
        return self._folds.get(self.shown_tree(), set())

    def render_trees(self):
        """The six trees, drawn from the recorded claims and links, coloured by role; the chosen
        statement lies on a band of the hand's tint."""
        if not self.has_trees():
            self._tree_spans = []
            return None
        width = max(40, self.query_one("#main").size.width - 7)
        shown = self.shown_tree()
        step = self.marked_step(live_only=False)
        fresh = step["fresh"] if step else ()
        spans, columns, echoes = [], {}, []
        lines = trees_lines(self.workspace_value["trees"], width, only=None if shown == "all" else shown,
                            fresh=fresh, spans=spans, folded=self.folded(), title=shown == "all", columns=columns,
                            echoes=echoes)
        self._tree_spans = spans
        chosen = next((range(start, end) for ref, start, end in spans if ref == self.selected_claim), range(0))
        # Working in one tree, the chosen statement's chunk stays bright and the rest is dimmed, never hidden.
        # Not in all six, which is for seeing the whole, nor in a Cloud's boxes, which are a chunk already.
        self._dimmed = self.dims() and not columns
        bright = (bright_lines(spans, echoes, neighbours(self.tree_of(self.selected_claim), self.selected_claim),
                               self.selected_claim) if self._dimmed else None)
        return styled(lines, self.theme_variables, marked=chosen, width=width,
                      columns=columns.get(self.selected_claim), bright=bright)

    def refit_dimming(self):
        """Focus moved: brighten the whole tree again when the keyboard left the chosen statement, or dim
        around it when the keyboard came back."""
        if self.workspace_value is not None and self.view_name == "trees" and self.dims() != self._dimmed:
            self.render_all()

    def dims(self):
        """Whether the tree on screen dims what lies outside the chosen statement's chunk: in one tree, with a
        statement chosen there, while the keyboard is on the drawing or on that statement's details."""
        focus = getattr(self.focused, "id", None)
        return (self.view_name == "trees" and self.shown_tree() != "all" and self.drawn_selection() is not None
                and focus in ("canvas", "inspector"))

    def tree_of(self, ref):
        return next((t for t in self.workspace_value["trees"] if any(c["ref"] == ref for c in t["claims"])), None)

    def chosen_folds(self):
        """Whether the chosen statement has branches, and whether they are folded now."""
        ref = self.drawn_selection()
        tree = self.tree_of(ref) if ref else None
        if tree is None or not branches(tree)[ref]:
            return False, False
        return True, ref in self.folded()

    def toggle_fold(self):
        """Space in the drawing: fold the chosen statement's branches away, or unfold them."""
        can, _ = self.chosen_folds()
        if not can:
            return
        ref = self.drawn_selection()
        target = self._overview_open if self.shown_tree() == "all" else self._folds.setdefault(self.shown_tree(), set())
        target ^= {ref}
        self.render_all()
        self.call_after_refresh(self.keep_statement_in_view)

    # ----- choosing and inspecting a statement ---------------------------
    def drawn_selection(self):
        """The chosen statement, if the tree on screen draws it."""
        return self.selected_claim if any(ref == self.selected_claim for ref, _, _ in self._tree_spans) else None

    def statement_focused(self):
        """The drawing took focus: choose its first statement unless one on screen is already chosen."""
        if self.drawn_selection() is None and self._tree_spans:
            self.selected_claim = self._tree_spans[0][0]
            self.render_all()
        self.call_after_refresh(self.keep_statement_in_view)

    def choose_statement(self, step):
        """↑↓ in the drawing: the previous or next statement, in reading order."""
        refs = [ref for ref, _, _ in self._tree_spans]
        if not refs:
            return
        current = self.drawn_selection()
        index = refs.index(current) + step if current else 0
        self.selected_claim = refs[max(0, min(len(refs) - 1, index))]
        self.render_all()
        self.schedule_checkpoint()
        self.call_after_refresh(self.keep_statement_in_view)

    def keep_statement_in_view(self):
        from textual.geometry import Region
        span = next(((start, end) for ref, start, end in self._tree_spans if ref == self.drawn_selection()), None)
        if span is None:
            return
        canvas = self.query_one("#canvas")
        top = canvas.virtual_region.y + span[0]
        self.query_one("#main").scroll_to_region(Region(0, top, 1, max(1, span[1] - span[0])),
                                                 animate=False, immediate=True)

    def statement_origins(self, ref, words=300):
        """Where a statement came from: each cited input as who, when and their own words
        (shortened to ``words`` characters unless None), and each cited file by name."""
        sources, origins = self.history()["sources"], []
        for item in self.workspace_value["attribution"].get(ref, []):
            source = sources.get(item["source_ref"], {})
            if "request_id" in source:
                text = " ".join(str(source.get("text") or "").split())
                origins.append((f"{source.get('speaker') or 'Someone'}, {day(source.get('timestamp'))}, wrote:",
                                textwrap.shorten(text, words, placeholder=" …") if words and text else text))
            elif source:
                # A file's attribution says what it is ("Imported LTP document; …"), not who brought it in.
                when = f", brought in {short_day(source['timestamp'])}" if source.get("timestamp") else ""
                title = f"{source.get('speaker') or 'Unknown'} · {source.get('name') or item['source_ref']}{when}:"
                try:
                    text = base64.b64decode(source.get('content_base64', '')).decode('utf-8')
                except UnicodeDecodeError:
                    text = 'Binary source retained locally.'
                text = ' '.join(text.split())
                origins.append((title, textwrap.shorten(text, words, placeholder=' …') if words and text else text))
        return origins

    def statement_text(self, width, words=300):
        ref = self.drawn_selection()
        if ref is None:
            return None
        lines = statement_details(self.workspace_value["trees"], ref, width, self.statement_origins(ref, words))
        return styled(lines, self.theme_variables)

    def render_inspector(self):
        """Beside the trees on a wide terminal: the chosen statement's details, updated as you move."""
        panel = self.query_one("#inspector")
        # The panel's border, padding and scroll bar take six of its columns.
        details = None
        if self.terminal.width >= INSPECTOR_FROM and self.view_name == "trees":
            details = self.statement_text(INSPECTOR_WIDTH - 6)
        elif self.terminal.width >= INSPECTOR_FROM and self.view_name == "backlog" and self.chosen_entry():
            details = Text(self.entry_details(self.chosen_entry(), markdown=False))
        shown = details is not None
        if shown:
            self.query_one("#inspector-text", Static).update(details)
        if panel.has_class("hidden") == shown:
            panel.set_class(not shown, "hidden")
            # The trees are redrawn for the width the panel leaves them.
            self.call_after_refresh(self.render_all)
        if self.focused is panel and not shown:
            self.query_one("#main").focus()

    def answer_about(self):
        """Begin an answer about the chosen statement: its own words, its role and its tree go at the end of
        the draft, and the keyboard goes there. What someone then writes ("that's not a root cause") says
        which statement it means, in the words that are kept. It is ordinary text, to change or delete before
        sending; nothing is sent, and the answer still answers the current question."""
        ref = self.drawn_selection()
        if ref is None:
            return
        if self.story or self.revision is not None:
            self.notify("This is a record of what happened; nothing here can be answered. "
                        + ("Start your own goal to write." if self.story else "Back to now to answer."))
            return
        tree = self.tree_of(ref)
        claim = next(c for c in tree["claims"] if c["ref"] == ref)
        quote = (f"About “{claim['statement']}” ({ROLE_LABELS[claim['role']].lower()}, "
                 f"{TREE_TITLES[tree['tree']][0]}): ")
        editor = self.query_one("#editor", TextArea)
        text = editor.text
        lead = "" if not text.strip() or text.endswith("\n\n") else "\n" if text.endswith("\n") else "\n\n"
        editor.move_cursor(editor.document.end)
        editor.insert(lead + quote)
        editor.focus()

    def open_statement(self):
        """Enter on a chosen statement: its details in full, over the trees (Esc returns); in the
        overview, the statement's own tree, with it still chosen."""
        ref = self.drawn_selection()
        if ref is None:
            return
        if self.shown_tree() == "all":
            self.show_tree(self.tree_of(ref)["tree"])
            self.statement_focused()
            return
        self.push_screen(StatementScreen(lambda width: self.statement_text(width, words=None)))

    # ----- looking back -------------------------------------------------
    def reconstructed_development(self):
        return any(str(version).startswith('commons-import/2')
                   for version in (self.history()['snapshots'][-1].get('adapter_versions') or {}).values())

    def fill_timeline(self, timeline):
        """One row per saved step, in columns: the day (only where it changes), the time, who (only when
        more than one person has written), the step, and what it changed. A step that changed nothing is quiet."""
        entries = self.history()["entries"]
        names = {e["speaker"] for e in entries if e["speaker"]}
        shared = len(names) > 1 or (not self.reconstructed_development() and
                                   any(not same_person(name, self.speaker) for name in names))
        rows = []
        for entry in entries:
            when, time = self.when_parts(entry)
            created = entry["revision"] == 0
            title = "The goal was created" if created else self.step_title(entry)
            change = "" if created else (change_summary(entry["counts"]) if entry["counts"] else
                                         f"{len(entry['proposed'])} proposed" if entry["proposed"] else
                                         change_summary(entry["counts"]))
            rows.append((when, time, (entry["speaker"] or "unknown") if shared and not created else "", title, change))
        widths = [max(len(row[column]) for row in rows) for column in range(3)]
        title_width = min(36, max(len(row[3]) for row in rows))
        options, previous = [], None
        for entry, (when, time, who, title, change) in zip(entries, rows):
            quiet = not change or change == "no change to the model" or change.endswith(" proposed")
            label = Text()
            label.append((when if when != previous else "").ljust(widths[0]), style="dim")
            previous = when
            for value, width in ((time, widths[1]), (who, widths[2])):
                if width:
                    label.append("  " + value.ljust(width), style="dim")
            shown = title if len(title) <= title_width else title[:title_width - 1] + "…"
            label.append("  " + shown.ljust(title_width), style="dim" if quiet else "")
            label.append("  " + change, style="dim" if quiet else themed("$stood-behind", self.theme_variables))
            if entry["revision"] == len(entries) - 1:
                label.append("   ● now", style="dim")
            options.append(Option(label, id=str(entry["revision"])))
        current = timeline.highlighted
        timeline.clear_options()
        timeline.add_options(options)
        timeline.highlighted = current if current is not None and current < len(options) else (
            self.revision if self.revision is not None else len(options) - 1)

    def when_parts(self, entry):
        """A step's day and time on the person's own clock; a story keeps its own dates and has no times."""
        if self.story:
            return self.when(entry), ""
        stamp = moment(entry["timestamp"])
        day_part, _, time = stamp.rpartition(", ")
        return (day_part, time) if day_part and re.fullmatch(r"\d\d:\d\d", time) else (stamp, "")

    def step_title(self, entry):
        """A story chapter's title, else the question this step answered, else the decision it records."""
        chapter = self.chapters.get(entry["revision"], {})
        if not chapter and entry["request_id"] is None and entry["decisions"]:
            decision = entry["decisions"][0]
            return decision_words(decision).capitalize()
        versions = self.history()['snapshots'][entry['revision']].get('adapter_versions') or {}
        if versions.get(entry['request_id']) == 'commons-import/2':
            return entry['decision'] or 'Reconstructed development'
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
        if entry["text"]:
            paragraphs = [md(part).replace("\n", "  \n> ") for part in entry["text"].split("\n\n")]
            lines += ["> " + "\n>\n> ".join(paragraphs), ""]
        notes = [chapter[key] for key in ("words_note",) if chapter.get(key)]
        if chapter.get("source"):
            notes.append(f"Source: {chapter['source']}")
        if notes:
            lines += [f"*{md(' · '.join(notes))}*", ""]
        lines += ["### What entered the model", "", change_summary(entry["counts"]), ""]
        now = history["snapshots"][self.revision]["records"]
        everything = {r["ref"]: r for r in now}
        accepted = [ref for d in entry["decisions"] if d["action"] == "accept" for ref in d["refs"]]
        before = {r["ref"] for r in history["snapshots"][self.revision - 1]["records"]}
        start = (history["snapshots"][self.revision].get("membership") or {}).get("proposals_from", len(now))
        index = {r["ref"]: i for i, r in enumerate(now)}
        entered = [r["ref"] for r in now if r["ref"] not in before and index[r["ref"]] < start] + accepted
        lines += [self.change_line(everything[ref], everything) for ref in entered if everything[ref]["kind"] != "intervention"]
        if entry["proposed"]:
            lines += ["", "### Proposed, waiting for a decision", ""]
            lines += [self.change_line(everything[ref], everything) for ref in entry["proposed"]]
        for decision in entry["decisions"]:
            if decision["action"] in ("reject", "undo") or decision["closes"]:
                verb = {"reject": "Rejected", "undo": "Undone"}.get(decision["action"])
                if verb:
                    lines += ["", f"### {verb}", ""] + [self.change_line(everything[ref], everything)
                                                        for ref in decision["refs"]]
                if decision["closes"]:
                    lines += ["", "### Closed, because what they needed was not in the model", ""]
                    lines += [self.change_line(everything[ref], everything) for ref in decision["closes"]]
        lines = [line for line in lines if line is not None]
        question = (self.workspace_value["question"] or {}).get("data", {})
        if question.get("primary_prompt"):
            lines += ["", "### Asked next", "", md(question["primary_prompt"])]
        return "\n".join(lines)

    def change_line(self, record, everything):
        """One record in a step's page, as a list item in plain words."""
        data = record["data"]
        if record["kind"] == "claim":
            where = f"{TREE_TITLES[data['tree']][0]}, {ROLE_LABELS[data['role']].lower()}"
            if data.get("replaces") and data["replaces"] in everything:
                old = everything[data["replaces"]]["data"]["statement"]
                return f"- *Reworded, {md(where)}:* {md(data['statement'])}  \n  *was:* {md(old)}"
            return f"- *{md(where)}:* {md(data['statement'])}"
        if record["kind"] == "retraction":
            target = everything.get(data["target_ref"], {}).get("data", {})
            return (f"- *Withdrawn:* {md(target.get('statement') or data['target_ref'])}  \n"
                    f"  *why:* {md(data['reason'])}")
        if record["kind"] == "goal":
            return (f"- *Goal{', new version' if data.get('replaces') else ''}:* {md(data['statement'])}" +
                    (f"  \n  *measure:* {md(data['measure'])}" if data.get("measure") else ""))
        if record["kind"] == "test":
            forecast = "; ".join(f.get("expected") or "" for f in data.get("forecast") or [])
            return (f"- *Test{', new version' if data.get('replaces') else ''}:* {md(data['statement'])}  \n"
                    f"  *forecast, written first:* {md(forecast)}")
        if record["kind"] == "action":
            return f"- *Action planned:* {md(data['statement'])}"
        if record["kind"] == "note":
            return f"- *Note:* {md(data['text'])}"
        if record["kind"] == "link":
            return f"- *{md(TREE_TITLES[data['tree']][0])} link:* {md(self.link_words(record))}"
        return f"- *{KIND_NAMES[record['kind']]}:* {md(describe(record))}"

    def render_story_now(self):
        """The decision the story is waiting on leads; the action's details follow as rows."""
        question = (self.workspace_value["question"] or {}).get("data", {})
        lines = ["## The next action", ""]
        if question.get("primary_prompt"):
            lines += [md(question["primary_prompt"]), ""]
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
        if revision is not None and self.revision is None:
            self.begin_inspection()
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

    @on(OptionList.OptionHighlighted, "#timeline")
    @on(OptionList.OptionHighlighted, "#backlog-list")
    def list_moved(self, event):
        self.refresh_hints()
        if self.view_name == "backlog":
            self.render_inspector()

    @on(OptionList.OptionSelected, "#timeline")
    def moment_selected(self, event):
        self.begin_inspection()
        self.revision = int(event.option.id)  # set first, so the step page opens directly
        self.show_view("next")

    def marked_step(self, live_only=True):
        """The saved step whose tree changes are named and marked: on the live goal, the latest
        step if it was saved since the workspace opened (a reply or import just made); otherwise
        the past step being looked at, unless ``live_only``. None when there is nothing to mark."""
        entries = self.history()["entries"]
        if self.revision is not None:
            return None if live_only else entries[self.revision]
        return entries[-1] if entries[-1]["revision"] > self._opened_revision else None

    def tree_news(self, live_only=True):
        """What the marked step changed in the trees, tree by tree."""
        step = self.marked_step(live_only)
        return step["trees"] if step else {}

    def shown_tree(self):
        """The tree on screen: the last one chosen, else the overview of all six, where a first visit
        can see the whole before going into one tree."""
        if self.tree_choice:
            return self.tree_choice
        return "all" if self.has_trees() else TREE_ORDER[0]

    def show_view(self, name):
        if name != self.view_name:
            self.begin_inspection()
        self.view_name = name
        self.answer_ready = self.answer_ready and name != "next"
        self.refresh_workspace()
        self.refresh_views()
        self.query_one("#main").scroll_home(animate=False)
        if name == "next" and not self.explain and self.revision is None:
            self._origin = None  # back at the live question: nothing to return from
        self.schedule_checkpoint()

    def begin_inspection(self):
        """Remember where the person was before a local inspection began, so Esc can return there.
        Nested inspections keep the first origin. Focus on a control passed through on the way (a
        button, the Views list) is remembered as the answer being written, when there is one."""
        if self._origin is not None or self.workspace_value is None:
            return
        focus = self.focused
        editor = self.query_one("#editor")
        if (focus is None or focus.id in NAVIGATION_CONTROLS) and not self.story and self.revision is None:
            focus = editor
        self._origin = {"view": self.view_name, "explain": self.explain, "revision": self.revision,
                        "tree": self.tree_choice, "scroll": self.query_one("#main").scroll_y, "focus": focus}

    # ----- events -------------------------------------------------------
    @on(OptionList.OptionSelected, "#views")
    def view_selected(self, event):
        if event.option.id.startswith("tree:"):
            self.show_tree(event.option.id[5:])
        else:
            self.show_view(event.option.id)

    @on(Markdown.LinkClicked, "#content")
    def tree_clicked(self, event):
        if event.href.startswith("tree:") and event.href[5:] in TREE_ORDER + ["all"]:
            self.show_tree(event.href[5:])

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

    @on(Button.Pressed, "#retry-deeper")
    def retry_deeper_pressed(self):
        self.action_retry(deeper=True)

    @on(Button.Pressed, "#explain")
    def explain_pressed(self):
        self.action_explain()

    @on(Button.Pressed, "#moves")
    def moves_pressed(self):
        self.action_other_moves()

    @on(Button.Pressed, "#views-button")
    def views_pressed(self):
        self.open_menu("views")

    def action_command_palette(self):
        """Ctrl+P, or Commands in the footer: every command, in a filtered menu bound to the question."""
        self.open_menu("actions")

    def tab_target(self):
        """Where Tab goes from the views list: the open page's own list when it has one (the History
        timeline, the Trees drawing), else back to the answer. None when it just goes on to the next control."""
        for name in ("#timeline", "#backlog-list", "#canvas"):
            widget = self.query_one(name)
            if widget.display and widget.can_focus:
                return widget
        return None if self.query_one("#response").has_class("hidden") else self.query_one("#editor")

    def action_answer(self):
        """Tab in the views list."""
        target = self.tab_target()
        if target is None:
            self.screen.focus_next()
        else:
            target.focus()

    # ----- the footer ---------------------------------------------------
    def refresh_hints(self):
        if self.workspace_value is not None:
            before, after = self.footer_hints()
            self.query_one(HintBar).update_hints(before, after, summary=self.meter_texts())

    # ----- what paid replies cost -------------------------------------------
    def refresh_meter(self):
        """Read the usage log again (it is cached by size and time) and keep what it says for the footer."""
        if self.usage is not None:
            self._meter = self.usage.summary(case_id=self.case.inspect()["case"]["case_id"])
            self.refresh_hints()
        return self._meter

    def model_name(self):
        """The paid consultant's model in everyday words ("Haiku 5.5"), or None."""
        model = getattr(self.consultant, "model", None)
        return pricing.label(model) if self.provider == "anthropic" and model else None

    def meter_texts(self):
        """The footer's right end: what this session and this month cost, longest first, so the bar shows what
        fits and drops it before any hint. Words only, no colour. Nothing for the guide when nothing was spent."""
        summary = self._meter
        if summary is None:
            return []
        month, session = summary["month"], summary["session"]
        month_part = [month_meter(month, summary["budget"])] if summary["logging"] else []
        if self.provider == "anthropic":
            spent = [f"session ≈ {money(session['usd'])}"] if session["replies"] or session["no_reply"] else []
            tail = " · ".join(spent + month_part)
            name = self.model_name() or "Claude"
            family = name.split(" ")[0]
            texts = [f"{name} · {tail}", f"{family} · {tail}", tail] if tail else [name, family]
            return texts + month_part
        who = "local model" if self.provider == "lm-studio" else "offline guide"
        if not (month["replies"] or month["no_reply"]):
            return [] if self.provider == "guided" else [f"{who} · no charge", "no charge"]
        return [f"{who} · no charge · {month_part[0]}", f"no charge · {month_part[0]}", *month_part] if month_part \
            else [f"{who} · no charge"]

    def typical_reply(self, model):
        """A reply's likely cost on this model: the log's own average once there is one, else list price."""
        return (self.usage.typical(model) if self.usage is not None else None) or pricing.typical(model)

    def boost(self):
        """The model that answers one question with deeper reasoning, or None where none is offered: only with
        Claude, and only a configured model that differs from the one in use and costs more per reply. It is
        offered, never used on its own: a person asks for it, one reply at a time."""
        from reason_commons.adapters.anthropic import boost_model
        model, deeper = getattr(self.consultant, "model", None), boost_model()
        if self.provider != "anthropic" or self.story or self.tour or not model or not deeper or deeper == model:
            return None
        current, dearer = pricing.typical(model), pricing.typical(deeper)
        return deeper if current is not None and dearer is not None and dearer > current else None

    def boost_cost(self, deeper):
        """'≈ $0.05, about 12× a Haiku reply': from the log's own averages once each model has three recent
        replies, otherwise from a typical reply of each at list price."""
        model = self.consultant.model
        logged = [self.usage.typical(m) if self.usage is not None else None for m in (model, deeper)]
        mine, theirs = logged if None not in logged else (pricing.typical(model), pricing.typical(deeper))
        return f"≈ {money(theirs)}, about {round(theirs / mine)}× a {pricing.label(model).split()[0]} reply"

    def stand_in(self, deeper):
        """The consultant for one reply on ``deeper``, built once, here on the main thread."""
        if deeper not in self._stand_ins:
            try:
                self._stand_ins[deeper] = self._consultant_factory(self.provider, model=deeper)
            except Exception as exc:
                self.notify(f"Could not set up {pricing.label(deeper)}: {exc}", severity="error", timeout=8)
                return None
        return self._stand_ins[deeper]

    def spend_check(self, go, model=None):
        """Past the monthly budget, a send to a paid consultant asks once first. Nothing is blocked: "Not now"
        sends nothing and keeps the answer in the box. The budget is a notice, not a rule of the case."""
        summary = self.refresh_meter() if self.provider == "anthropic" else None
        limit = summary["budget"] if summary else None
        if not limit or summary["month"]["usd"] < limit:
            go()
            return
        reply = self.typical_reply(model or getattr(self.consultant, "model", None))
        body = (f"This month ≈ {money(summary['month']['usd'])} of your {money(limit)} budget (estimate)."
                + (f" This reply ≈ {money(reply)}." if reply else "")
                + "\n\nNothing is blocked: send this one now, or keep your answer for later.")

        def chosen(choice):
            if choice == "send":
                go()
            else:
                self.checkpoint()
                self.notify("Nothing was sent. Your answer is still in the box.")
        self.push_screen(ChoiceScreen("Past your monthly budget", body,
                                      [("send", "Send this one"), ("not-now", "Not now")]), chosen)

    def budget_changed(self):
        self.refresh_meter()

    def footer_hints(self):
        """What the footer says for the control that has the keyboard, as (before Commands, after Commands):
        hints of (key as drawn, what it does, the key to press, or None when it is not one key), with a
        shorter label for when the terminal is narrow."""
        focus = getattr(self.focused, "id", None)
        leave = ("^q", "Save & quit", "ctrl+q", "Quit")
        trees = (("^t", "Back to question", "ctrl+t", "Back") if self.view_name == "trees"
                 else ("^t", "Trees", "ctrl+t"))
        tab = ("tab", "Next control", "tab", "Next")
        back = ("tab", "Back to answer", "tab", "Answer") if self.tab_target() is self.query_one("#editor") else tab
        choose = ("↑↓", "Choose statement", None, "Choose")
        if focus == "views":
            return [("↑↓", "Choose view", None, "Choose"), ("⏎", "Open", "enter"), back], []
        if focus == "canvas":
            can, folded = self.chosen_folds()
            fold = [("space", "Unfold" if folded else "Fold", "space")] if can else []
            enter = ("⏎", "Open tree", "enter", "Open") if self.shown_tree() == "all" else ("⏎", "Details", "enter")
            # Last, so it is the first to say less or go: getting back matters more. All six is for seeing
            # the whole, where Enter opens a tree, so it is not offered there (the key still works).
            about = ([] if self.story or self.revision is not None or self.shown_tree() == "all"
                     else [("a", "Answer about this", "a", "About")])
            return [choose, *fold, enter, ("^n", "Next tree", "ctrl+n"), trees, *about], []
        if focus == "timeline":
            undo = [("u", "Undo this change", "u", "Undo")] if self.undoable(self.query_one("#timeline").highlighted) else []
            return [("↑↓", "Choose step", None, "Choose"), ("⏎", "Open that step", "enter", "Open"), *undo], [tab]
        if focus == "backlog-list":
            entry = self.chosen_entry()
            keys = ([("h", "Still holds", "h", "Holds")] if entry and entry["entry"] == "review" else
                    [("a", "Accept", "a"), ("r", "Reject", "r")])
            return [("↑↓", "Choose", None), ("⏎", "Choices", "enter"), *keys], [tab]
        if focus in ("main", "inspector"):
            return [("↑↓", "Scroll", None), trees], [back]
        if focus in ("commands", "help"):
            # The hints before Commands stay as they were, so it does not move when a click gives it focus.
            return [leave, trees], [("⏎", "Open", "enter"), tab]
        if focus in NAVIGATION_CONTROLS or focus in self.MOMENT_LABELS:
            return [leave, trees], [("⏎", "Press", "enter"), tab]
        return [leave, trees], [tab]  # the answer box

    @on(TextArea.Changed, "#editor")
    def draft_changed(self):
        if not self._restoring:
            self.schedule_checkpoint()
        self.fit_answer_box()

    # ----- actions ------------------------------------------------------
    def action_browse(self):
        """Esc: from the answer, browse without losing it; from an inspection, go back to where it began,
        with the view, scroll position, draft and caret as they were."""
        if self.focused is self.query_one("#editor") or self._origin is None:
            self.query_one("#main").focus()
            return
        origin, self._origin = self._origin, None
        self.explain, self.revision, self.tree_choice = origin["explain"], origin["revision"], origin["tree"]
        self.show_view(origin["view"])
        self._origin = None
        self.query_one("#main").scroll_to(y=origin["scroll"], animate=False)
        focus = origin["focus"]
        if focus is not None and focus.is_attached and focus.focusable:
            focus.focus()

    def action_help(self):
        self.push_screen(HelpScreen())

    def show_tree(self, key):
        self.tree_choice = key
        self.show_view("trees")

    def action_trees(self):
        """Ctrl+T: open the Trees view with the keys on the drawing, or go back to the current
        question and to the control that had focus before."""
        if self.view_name == "trees":
            before, self._focus_before_trees = self._focus_before_trees, None
            self.show_view("next")
            if before is not None and before.is_attached and before.focusable:
                before.focus()
            elif not self.story and self.revision is None:
                self.query_one("#editor").focus()
            return
        self._focus_before_trees = self.focused
        self.show_view("trees")
        canvas = self.query_one("#canvas")
        if canvas.can_focus:
            canvas.focus()

    def action_next_tree(self):
        """Ctrl+N: show the next tree (the six in turn, then all six together)."""
        if self.view_name == "trees":
            order = TREE_ORDER + ["all"]
            self.tree_choice = order[(order.index(self.shown_tree()) + 1) % len(order)]
        self.show_view("trees")
        if self.focused is self.query_one("#canvas"):
            self.statement_focused()

    def action_explain(self):
        if not self.explain:
            self.begin_inspection()
        self.explain = not self.explain
        self.show_view("next")

    def action_other_moves(self):
        self.open_menu("other_moves")

    # ----- menus ----------------------------------------------------------
    def menu_binding(self):
        """What a menu acts on: the question and revision on screen when it opened."""
        target = self.workspace_value["target"]
        return {"response_target": target["response_target"], "revision": target["base_revision"]}

    def menu_items(self, name):
        if name == "other_moves":
            return OTHER_MOVES
        if name == "views":
            return VIEW_LABELS
        return [(key, command_label(title, detail)) for key, title, detail, _ in self.action_list()]

    def open_menu(self, name, notice=None, text="", highlighted=None):
        if isinstance(self.screen, MenuScreen) or self.workspace_value is None:
            return
        question = (self.workspace_value["question"] or {}).get("data", {})
        # Other moves are alternatives to answering, so they show the whole question; Commands name it.
        decision = question.get("decision") or "the next question"
        context = (None if not question or name == "views" else
                   f"For “{decision}”: {question['primary_prompt']}" if name == "other_moves" else f"For “{decision}”")
        self._menu_name = name
        self.push_screen(MenuScreen(MENU_TITLES[name], self.menu_items(name), self.menu_binding(), context,
                                    notice, text, highlighted), lambda result: self.menu_chosen(name, result))

    def menu_changed(self, screen):
        """Keep the open menu in the cursor, so a resumed workspace can bring it back."""
        self._menu_state = {"name": self._menu_name, "filter": screen.query_one("#filter", Input).value,
                            "highlighted": screen.wanted, **(screen.binding or {})}
        self.schedule_checkpoint()

    def menu_chosen(self, name, result):
        """Act on a menu choice, but only for the question the menu was opened for."""
        self._menu_name = self._menu_state = None
        self.schedule_checkpoint()
        if result is None:
            return
        key, binding = result
        if binding != self.menu_binding():
            decision = (self.workspace_value["question"] or {}).get("data", {}).get("decision") or "the next question"
            self.open_menu(name, notice=f"The question changed while this menu was open, so nothing was done. "
                                        f"These are the choices for “{decision}”; choose again.")
            return
        if name == "views":
            self.show_view(key)
        elif name == "other_moves":
            self.other_move(key)
        else:
            runs = {k: run for k, _, _, run in self.action_list()}
            if key in runs:
                runs[key]()

    def restore_menu(self, menu):
        """A menu kept in the cursor comes back only for the same question and revision, and only
        with choices that exist here; anything else is refused locally, with nothing sent."""
        name, wanted = menu.get("name"), menu.get("highlighted")
        if name not in MENU_TITLES:
            return
        if {"response_target": menu.get("response_target"), "revision": menu.get("revision")} != self.menu_binding():
            self.notify("The menu you had open was for an earlier question, so it was not restored.", timeout=8)
            return
        notice = None
        if wanted and wanted not in [key for key, _ in self.menu_items(name)]:
            later = LATER_PROFILE_ACTIONS.get(wanted)
            notice = (f"“{later}” belongs to a later delivery profile and is not available in this version. "
                      "Nothing was sent; your draft is unchanged." if later else
                      "The choice you had is not available now; choose again.")
            self.notify(notice, severity="warning", timeout=10)
            wanted = None
        self.open_menu(name, notice=notice, text=menu.get("filter") or "", highlighted=wanted)

    def other_move(self, key):
        if key == "explain":
            if not self.explain:
                self.action_explain()
        elif key == "evidence":
            self.show_evidence()
        elif key == "goal":
            self.show_view("goal")
        else:
            self.action_send(intent=key)

    def show_evidence(self):
        """The saved sources the current question rests on: who said what, when, and attached files."""
        w = self.workspace_value
        question = (w["question"] or {}).get("data", {})
        records = {r["ref"]: r for r in w["records"]}
        sources = self.history()["sources"]
        lines = [f"## Evidence for “{md(question.get('decision') or 'the next question')}”", ""]
        cited = []
        for ref in question.get("required_context_refs") or []:
            for item in w["attribution"].get(ref, []):
                if item["source_ref"] not in cited:
                    cited.append(item["source_ref"])
        for ref in cited:
            source = sources.get(ref, {})
            if "request_id" in source:
                lines += [f"**{md(source.get('speaker') or 'Someone')}**, {day(source.get('timestamp'))}:", "",
                          "> " + md(source.get("text") or "").replace("\n", "  \n> "), ""]
            elif source:
                lines += [f"**File:** {md(source.get('name') or ref)}", ""]
        if not cited:
            lines.append("This question cites no saved sources.")
        self.push_screen(TextScreen("\n".join(lines)))

    def action_send(self, intent="answer", deeper=False):
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
        stand_in = self.deeper_consultant() if deeper else None
        if deeper and stand_in is None:
            return
        self.spend_check(lambda: self._send(intent, stand_in), getattr(stand_in, "model", None))

    def deeper_consultant(self):
        """The stand-in for one reply with deeper reasoning, or None (said why) where there is none."""
        deeper = self.boost()
        if deeper is None:
            self.notify("Deeper reasoning is offered only with Claude, when a model that reasons more deeply "
                        "than the one in use is set.")
            return None
        return self.stand_in(deeper)

    def asking(self, stand_in):
        """Get ready to consult: count from here, and let the stand-in, if any, answer the next consultation."""
        self._usage_mark = self.usage.mark() if self.usage is not None else None
        self.chosen.once = stand_in
        self._asking = pricing.label(stand_in.model) if stand_in is not None else None
        self.set_busy(True)

    def _send(self, intent, stand_in=None):
        """Send the answer in the box now (after any question about the budget)."""
        if self.busy:
            return
        text = self.query_one("#editor", TextArea).text
        if intent == "review_flags" and not text.strip():
            text = "Do the records flagged for review still hold?"
        self.asking(stand_in)
        target = self.workspace_value["target"]
        self.run_worker(lambda: self._submit(text, intent, target), thread=True, exclusive=True)

    def _submit(self, text, intent, target):
        try:
            result = self.case.retain_input(text, self.speaker, target["base_revision"],
                                            target["response_target"], intent=intent)
            if result["status"] == "input_retained":
                result = self.case.consult(result["request_id"])
        except Exception as exc:  # keep the draft; report the category only
            result = {"status": "not_saved", "message": f"Not saved ({type(exc).__name__})."}
        finally:
            self.chosen.once = None  # one reply only, whatever became of it
        self.call_from_thread(self._submitted, result, text)

    def action_retry(self, deeper=False):
        actions = self.retryable()
        if self.busy or not actions:
            if deeper and self.busy:
                self.notify("Still waiting for the consultant. You can keep browsing.")
            return
        request_id = actions[-1]["arguments"]["request_id"]
        if not self.retry_asks_again(request_id):
            if deeper:
                self.notify("Retry applies the reply already received, so it asks no one; nothing was sent.")
            self._retry(request_id)
            return
        stand_in = self.deeper_consultant() if deeper else None
        if deeper and stand_in is None:
            return
        self.spend_check(lambda: self._retry(request_id, stand_in), getattr(stand_in, "model", None))

    def retry_asks_again(self, request_id):
        """Whether Retry would ask the consultant again, rather than apply a reply it already received (one kept
        with no result that rejected it), which costs nothing."""
        attempts = {}
        for item in self.case.receipts(request_id)["attempts"]:
            attempts.setdefault(item.get("attempt"), []).append(item)
        return not any(any("proposal" in item for item in items)
                       and not any(item.get("status") in ("rejected", "stale") for item in items)
                       for items in attempts.values())

    def _retry(self, request_id, stand_in=None):
        if self.busy:
            return
        self.asking(stand_in)

        def work():
            try:
                result = self.case.retry(request_id)
            except Exception as exc:
                result = {"status": "not_saved", "message": f"Not saved ({type(exc).__name__})."}
            finally:
                self.chosen.once = None
            self.call_from_thread(self._submitted, result, None)
        self.run_worker(work, thread=True, exclusive=True)

    def _submitted(self, result, text):
        self.set_busy(False, refresh=False)
        self._history = None
        editor = self.query_one("#editor", TextArea)
        status = result["status"]
        sent = text is not None and editor.text == text
        # What this send cost: the requests the usage log took while it ran (none when a retry only applied a
        # reply already received), then whether the month passed 80% or 100% of the budget.
        paid = self.usage.since(self._usage_mark) if self.usage is not None and self._usage_mark is not None else []
        self._usage_mark = None
        before = self._meter["month"]["usd"] if self._meter else None
        self.refresh_meter()
        cost = spent_words(paid)
        deeper, self._asking = self._asking, None
        if deeper:  # one reply only: say so, and that Send goes back to the model in use
            priced = [entry["usd"] for entry in paid if entry["usd"] is not None]
            spent = f" (≈ {money(sum(priced))})" if paid and len(priced) == len(paid) else ""
            back = f" Send goes to {self.model_name()} again."
            cost = (f" {deeper} answered{spent}." if status == "saved" else cost) + back
        if status == "saved":
            if sent:
                editor.clear()
            self.explain = False
            # Never move the person: a reply that arrives while they browse waits on Next step.
            self.answer_ready = self.view_name != "next"
            news = self.tree_news()
            grown = f" In the trees: {tree_summary(news)}." if news else ""
            waiting = len(self.case.workspace(view="backlog")["backlog"]) and result.get("proposed") and not result.get(
                "accepted_automatically")
            proposed = f" {len(result['proposed'])} proposed; they wait in Backlog." if waiting else ""
            self.notify(("Answer ready: Next step shows the new question." if self.answer_ready else "Saved.")
                        + grown + proposed + cost)
        elif result.get("input_retained"):
            if sent:
                editor.clear()  # the words are retained in the case; Retry reuses them
            deeper_retry = self.boost()
            elsewhere = (f" Retry with {pricing.label(deeper_retry)} is in Commands." if deeper_retry
                         and self.terminal.width < 100 else "")
            self.notify(result.get("message", status) + ". Use Retry when the consultant is reachable." + elsewhere
                        + cost, severity="warning", timeout=8)
        else:
            self.notify(result.get("message", status) + " Your text is still in the editor." + cost,
                        severity="error", timeout=8)
        if before is not None and self._meter:
            share = crossed(before, self._meter["month"]["usd"], self._meter["budget"])
            if share:
                self.notify(budget_notice(share, self._meter["month"]["usd"], self._meter["budget"]), timeout=10)
        self.refresh_workspace()
        self.checkpoint()

    def set_busy(self, busy, refresh=True):
        self.busy = busy
        # Other moves stays open while waiting: its local inspections still work, and a move that
        # asks the consultant is refused until the pending reply is in.
        for name in ("#send", "#retry", "#retry-deeper"):
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
        # The delayed save can fire after the workspace is taken down; quitting already saved the draft.
        editors = self.query("#editor")
        if not editors:
            return
        editor = editors.first(TextArea)
        draft = editor.text
        target = self.workspace_value["target"]
        try:
            result = self.case.checkpoint({
                "view": self.view_name, "focus": "response" if editor.has_focus else "browse",
                "draft": draft, "caret": caret_index(draft, editor.cursor_location), "speaker": self.speaker,
                "response_target": target["response_target"], "base_revision": target["base_revision"],
                "display": {"tree": self.shown_tree(), "density": self.density},
                **({"selection": self.selected_claim} if self.selected_claim else {}),
                **({"menu": self._menu_state} if self._menu_state else {})})
        except Exception:
            return
        if result["status"] != "saved":
            self.notify("Draft not saved to disk. Copy your text somewhere safe.", severity="error")

    async def action_quit(self):
        if not self.busy:
            self.checkpoint()
        self.exit()

    # ----- Commands palette (Ctrl+P) ---------------------------------------
    def action_list(self):
        """Every action as (key, name, what it does and whether it stays local or asks the consultant, run)."""
        items = [("Send answer", "Asks the consultant with your answer (Ctrl+S)", self.action_send)]
        deeper = self.boost() if self.revision is None else None
        if deeper:
            name, base = pricing.label(deeper), self.model_name()
            items.append((f"Send with deeper reasoning ({name})",
                          f"Asks the consultant: {name} answers this one, then {base} again; {self.boost_cost(deeper)}",
                          lambda: self.action_send(deeper=True)))
        retryable = self.retryable()
        if retryable:
            items.append(("Retry", "Asks the consultant again with your saved answer", self.action_retry))
            if deeper and self.retry_asks_again(retryable[-1]["arguments"]["request_id"]):
                items.append((f"Retry with {name}", f"Asks the consultant again with your saved answer: {name} "
                              f"answers it, then {base} again; {self.boost_cost(deeper)}",
                              lambda: self.action_retry(deeper=True)))
        items += [("Explain this question", "Local: the saved explanation", self.action_explain),
                  ("Other moves", "Local explanations, or a move that asks the consultant; each says which",
                   self.action_other_moves)]
        items += [(f"View: {label}", "Local view, no consultant call", lambda key=key: self.show_view(key))
                  for key, label in VIEW_LABELS]
        items += [(f"Tree: {TREE_TITLES[key][0] if key in TREE_TITLES else 'All six trees'}",
                   "Local: show this tree (Ctrl+N cycles)", lambda key=key: self.show_tree(key))
                  for key in TREE_ORDER + ["all"]]
        if self.view_name == "trees" and self.drawn_selection() and not self.story and self.revision is None:
            items.append(("Answer about the chosen statement",
                          "Local: puts its words in your answer, to change as you like; nothing is sent (a)",
                          self.answer_about))
        if self.reply_waiting():
            items.append(("Accept all the last reply proposed",
                          "Local: admits them to your model, with what they need; no consultant call",
                          self.accept_reply))
        if self.import_waiting():
            items.append(('Adopt imported reasoning',
                          f'Local: accept {len(self.import_waiting())} imported proposals into your model; '
                          'acceptance does not establish their truth', self.adopt_import))
        if not self.story and self.revision is None:
            if self.workspace_value["acceptance"] == "review":
                items.append(("Accept proposals automatically",
                              "Local setting, recorded: later replies' proposals enter your model as they arrive",
                              lambda: self.set_acceptance("automatic")))
            else:
                items.append(("Hold proposals for review",
                              "Local setting, recorded: later replies' proposals wait in Backlog for you",
                              lambda: self.set_acceptance("review")))
            if any(e["entry"] == "review" for e in self.backlog()):
                items.append(("Ask about the open reviews",
                              "Asks the consultant whether the flagged records still hold; your answer goes with it",
                              lambda: self.action_send(intent="review_flags")))
        other = "expanded" if self.density == "compact" else "compact"
        items.append((f"Display: {other.capitalize()}",
                      "Local preference, saved with your draft: " + (
                          "repeat the complete goal, every safeguard and each test's boundaries in the band"
                          if other == "expanded" else "keep the band to the goal and its safeguards")
                      + "; a breach always stays", lambda: self.set_density(other)))
        items.append(("History: step back", "Local: the goal as it was one step earlier (←)", self.action_earlier))
        if self.revision is not None:
            items += [("History: step forward", "Local: one step later (→)", self.action_later),
                      ("History: back to now", "Local: the goal as it is now", lambda: self.go_to(None))]
        items += [("Consultant calls and cost",
                   "Local: how often the consultant was asked, and what Claude's replies cost, as estimated",
                   self.action_consultant_calls),
                  ("Export case", "Local: write a portable .reasoncase copy", self.action_export),
                  ("Import trees", "Local: bring in trees from an .ltp.yaml file; asks no consultant",
                   self.action_import_trees),
                  ("Export trees", "Local: write the trees to an .ltp.yaml file", self.action_export_trees)]
        items += [(f"Consultant: {label}", "Local setting: use this consultant from now on",
                   lambda key=key: self.switch_provider(key)) for key, label in PROVIDERS.items() if key != self.provider]
        items += [("Settings", "Local: change the theme and light or dark (F2)", self.action_settings),
                  ("Theme", f"Local: how Reason Commons looks; now {themes.title(self.theme)}", self.action_change_theme),
                  ("Help", "Local: keys and controls (F1); Explain this covers the reasoning", self.action_help),
                  ("Save and quit", "Local: keep your draft and close (Ctrl+Q)", self.action_quit)]
        return [(re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), name, detail, run) for name, detail, run in items]

    def set_density(self, density):
        """Compact (the default) or Expanded: a presentation preference, saved with the cursor; it records no
        reasoning and calls no consultant, and no density hides a breach."""
        self.density = density
        self.render_all()
        self.schedule_checkpoint()
        self.notify(f"Display: {density}. Saved with your draft; nothing else changed.")

    def get_system_commands(self, screen):
        for _, name, detail, run in self.action_list():
            yield SystemCommand(name, detail, run)

    def call_counts(self):
        """Consultant calls and offline imports, counted from each input's saved attempt receipts."""
        calls = offline = 0
        for request_id, source in self.case.sources()["sources"].items():
            if "request_id" not in source:
                continue
            attempts = {}
            for item in self.case.receipts(request_id)["attempts"]:
                attempts.setdefault(item.get("attempt"), {}).update(item)
            for attempt in attempts.values():
                if str(attempt.get("version", "")).startswith(OFFLINE_ADAPTERS):
                    offline += 1
                else:
                    calls += 1
        return calls, offline

    def action_consultant_calls(self):
        self.push_screen(CallsScreen(*self.call_counts(), report=self.cost_report()))

    def model_where(self):
        """Where the Claude model in use was chosen, in words."""
        from reason_commons.adapters.anthropic import DEFAULT_MODEL
        model = getattr(self.consultant, "model", None)
        environment = os.environ.get("REASON_COMMONS_ANTHROPIC_MODEL")
        saved = self.settings.get("anthropic", "model") if self.settings is not None else None
        if model == environment:
            return "your saved choice" if saved == model else "set by REASON_COMMONS_ANTHROPIC_MODEL"
        return "the default" if model == DEFAULT_MODEL else "chosen when this goal was opened"

    def cost_report(self):
        """What paid replies cost, from the usage log: this goal, the last reply, this session, today and this
        month by model against the budget, and the model in use. Estimates in words; no ids, no ISO times."""
        from reason_commons.adapters.anthropic import DEFAULT_MODEL
        summary = self.refresh_meter()
        if summary is None:
            return None
        rows = []  # (label, value), aligned as text: Textual draws a Rich grid's padding as nothing
        row = lambda label, value: rows.append((label, value))
        row("This goal", "Claude: " + replies_words(summary["goal"]))
        reply = summary["reply"]
        if reply is not None:
            tokens = reply["tokens"]
            row("Last reply", f"{pricing.label(reply['model'])} · {pricing.prompt_tokens(tokens):,} tokens in, "
                              f"{tokens['output']:,} out · "
                              + ("cost not known" if reply["usd"] is None else f"≈ {money(reply['usd'])}"))
        row("This session", replies_words(summary["session"]))
        month, limit = summary["month"], summary["budget"]
        if summary["logging"]:
            row("Today", replies_words(summary["today"]))
            if limit is None:
                standing = "no monthly budget set"
            elif month["usd"] > limit:
                standing = f"past your {money(limit)} budget; each send asks first, and nothing is blocked"
            else:
                standing = f"of your {money(limit)} budget ({int(month['usd'] * 100 / limit)}%)"
            row("This month", f"{replies_words(month)}, {standing}")
            for model, total in sorted(month["by_model"].items(), key=lambda item: -item[1]["usd"]):
                row("", f"{pricing.label(model)}: {replies_words(total)}")
            if month["no_reply"]:
                row("No reply", f"{month['no_reply']} this month: sent, with no reply back; they may still "
                                "have been billed")
        name = self.model_name()
        if name:
            row("Claude now", f"{name}, {self.model_where()}")
        else:
            row("Consultant now", ("LM Studio" if self.provider == "lm-studio" else "the built-in guide")
                + ": no charge")
        row("No charge", "LM Studio and the built-in guide")
        notes = []
        saved = self.settings.get("anthropic", "model") if self.settings is not None else None
        if name and saved not in (None, DEFAULT_MODEL) and saved == getattr(self.consultant, "model", None):
            notes.append(f"{pricing.label(DEFAULT_MODEL)} is now the default and costs least. Your saved choice, "
                         f"{name}, stays until you change it: F2 Settings, then You, on the home screen.")
        notes.append(f"Estimates at Anthropic's list prices of {day(pricing.AS_OF)}, from each reply's token counts; "
                     "your bill is in the Anthropic Console.")
        path = summary["path"]
        if path is None:
            notes.append("The usage log is off (REASON_COMMONS_USAGE_LOG=off), so only this session is counted.")
        else:
            home = str(Path.home())
            shown = "~" + str(path)[len(home):] if str(path).startswith(home + os.sep) else str(path)
            notes.append(f"Kept in {shown}, readable only by you: counts and estimates, never your words.")
        if summary["skipped"]:
            notes.append(skipped_words(summary["skipped"]))
        if summary["error"]:
            notes.append(f"The log could not be written ({summary['error']}); this session's replies are counted "
                         "here only.")
        width = max(len(label) for label, _ in rows) + 2
        lines = [Text.assemble((label.ljust(width), "bold"), value) for label, value in rows]
        return Group(Text("CLAUDE REPLIES", style="bold dim"), *lines, Text(""),
                     *[Text(note, style="dim") for note in notes])

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
            waiting = False
            try:
                summary = import_trees(self.store, os.path.expanduser(path), self.speaker)
                waiting = len(summary["proposed"]) > len(summary["accepted"])
                self.notify(f"Brought in {summary['claims']} statements and {summary['links']} links" +
                            (f"; {summary['notes']} items the trees cannot draw are kept as notes" if summary["notes"]
                             else "") + (". They wait in Backlog: accept what you want in your model." if waiting
                                         else ", into your model under your automatic acceptance."), timeout=8)
            except Exception as exc:
                self.notify(f"Import failed: {exc}", severity="error", timeout=10)
            finally:
                self.case = self._open(self.chosen)  # the same consultant, and no second setup of it
                self._history = None
            # What waits is decided in Backlog; what was accepted is drawn in the trees.
            self.show_view("backlog" if waiting else "trees")
        self.push_screen(PathScreen("Bring in trees from an LTP file (.ltp.yaml)", "",
                                    "Enter imports. What it brings waits in Backlog for you to accept. Esc cancels."),
                         chosen)

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
            self.notify("No Anthropic key yet, so requests will fail. Add one on the home screen (F2 Settings, "
                        "then You), or set ANTHROPIC_API_KEY.",
                        severity="warning", timeout=10)
        self.checkpoint()
        self.case.close()
        self.consultant, self.chosen, self._stand_ins = consultant, ChosenConsultant(consultant), {}
        self.case = self._open(self.chosen)
        self.provider = provider
        self.refresh_workspace()
        self.refresh_meter()
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
    start a goal, the guided tour, the real commons, or skipping setup. After that it has two
    sections: ways to start, and your goals as a table of name, stage and day last changed.
    Settings live behind F2 and the footer says what they are now.
    """

    TITLE = "Reason Commons"
    ENABLE_COMMAND_PALETTE = False
    CSS = ReasonCommonsApp.CSS + """
    #home { padding: 1 2; }
    #home-title { text-style: bold; color: $accent; }
    #home-intro { margin: 1 0; }
    #goals { height: auto; max-height: 1fr; border: none; background: transparent; padding: 0; }
    #goals > .option-list--option-highlighted { background: $hand-tint; color: $foreground; text-style: bold; }
    #goals > .option-list--option-disabled { color: $text-muted; text-style: bold; }
    """
    BINDINGS = [Binding("ctrl+q", "quit", "Quit", priority=True), Binding("f1", "help", "Help"),
                Binding("f2", "settings", "Settings")]
    # The ways to start: id, the mark before it, its name, and a quieter note after it.
    START = [("commons", "", "Continue Reason Commons", " · import prior work, then resume"),
             ("new", "+", "New goal", "")]

    def __init__(self, root, list_goals=find_goals, create=None, settings=None, checks=None, start_new=False):
        super().__init__(settings)
        self.root, self._list, self.start_new = Path(root), list_goals, start_new
        self._create = create or self._create_case
        self._checks = checks
        self.goals, self._marked, self._shown = [], None, False

    @property
    def first_run(self):
        return self.settings is not None and not self.settings.exists

    def compose(self) -> ComposeResult:
        with Vertical(id="home"):
            yield Static("Reason Commons", id="home-title")
            yield Static(id="home-intro")
            yield OptionList(id="goals")
        yield HintBar()

    def on_mount(self):
        super().on_mount()
        self.goals = self._list(self.root)
        self.show_options()
        if self.start_new:
            self.new_goal()

    def on_resize(self, event=None):
        if event is not None:
            self._terminal = event.size
        if self._shown:  # the columns are laid out for the width
            self.show_options(keep=self._marked)

    # ----- the list ---------------------------------------------------------
    GAP = "   "

    def columns(self):
        """Widths of the name, stage and day columns, which hug their contents so a row can be read across.
        A narrow screen gets no stage column."""
        room = max(20, self.terminal.width - 4) - 2  # the page's padding, then the mark
        gap = len(self.GAP)
        date = max([len("UPDATED")] + [cell_len(short_day(goal["changed"])) for goal in self.goals])
        stage = min(24, max([len("STAGE")] + [cell_len(goal["step"]) for goal in self.goals]))
        name = min(48, max([len("YOUR GOALS")] + [cell_len(goal["name"]) for goal in self.goals]))
        if name + stage + date + 2 * gap <= room:
            return name, stage, date
        name = room - stage - date - 2 * gap
        return (name, stage, date) if name >= 14 else (min(name + stage + gap, room - date - gap), 0, date)

    @staticmethod
    def fit(text, width):
        """The text on one line of exactly this many columns, a cut marked with an ellipsis."""
        text = " ".join(str(text).split())
        return set_cell_size(text, width - 1) + "…" if cell_len(text) > width else set_cell_size(text, width)

    def row(self, key, marked):
        """One selectable row. The marked row, which the highlight sits on, has no quiet colours.

        Built from Content, not markup, so a goal's name is only ever text, whatever characters it has."""
        pointer = "▸ " if marked else "  "
        quiet = lambda text: text if marked else (text, "$text-muted")
        if key.isdigit():
            goal = self.goals[int(key)]
            name, stage, date = self.columns()
            # Each gap stays with the cell before it, so a run of spaces is never a segment of its own.
            parts = [pointer + self.fit(goal["name"], name) + self.GAP]
            parts += [quiet(self.fit(goal["step"], stage) + self.GAP)] * bool(stage)
            return Content.assemble(*parts, quiet(short_day(goal["changed"])))
        _, sign, name, note = next(item for item in self.START if item[0] == key)
        return Content.assemble(pointer, (sign, "b $accent") if sign else " ", " ", name, quiet(note))

    def show_options(self, keep=None):
        goals = self.query_one("#goals", OptionList)
        goals.clear_options()
        if self.first_run:
            intro = "[b]Welcome.[/b] Continue the imported Reason Commons work, or start a goal of your own. Everything stays on this computer."
            options = [Option(option_label("Continue Reason Commons", "Source-backed prior reasoning, ready for your next contribution."), id="commons"),
                       Option(option_label("Start my first goal", "Use the offline guide. Name and consultant can be changed with F2 Settings."), id="start")]
            wanted, self._marked = "commons", None
        else:
            intro = "Continue useful work. Open a goal, contribute, and revisit the reasoning when needed."
            if not self.goals:
                intro += "\n\nYou have no goals yet. Start one below; it is saved as you go."
            wanted = keep or ("0" if self.goals else "commons")
            row = lambda key: Option(self.row(key, key == wanted), id=key)
            options = [Option(Content.assemble(("START", "b $text-muted")), disabled=True)]
            options += [row(item[0]) for item in self.START]
            if self.goals:
                name, stage, date = self.columns()
                head = self.GAP.join([self.fit("YOUR GOALS", name)] + [self.fit("STAGE", stage)] * bool(stage)
                                     + ["UPDATED"])
                options += [Option("", disabled=True), Option(Content.assemble(("  " + head, "b $text-muted")),
                                                              disabled=True), None]
                options += [row(str(index)) for index in range(len(self.goals))]
            self._marked = wanted
        self.query_one("#home-intro", Static).update(intro)
        goals.add_options(options)
        goals.highlighted = goals.get_option_index(wanted)
        goals.focus()
        self._shown = True
        self.refresh_hints()

    @on(OptionList.OptionHighlighted, "#goals")
    def highlight_moved(self, event):
        """Draw ▸ beside the highlighted row, and only there."""
        key = event.option.id
        if self.first_run or key == self._marked:
            return
        goals = self.query_one("#goals", OptionList)
        for old, marked in ((self._marked, False), (key, True)):
            if old is not None:
                goals.replace_option_prompt(old, self.row(old, marked))
        self._marked = key
        self.refresh_hints()

    # ----- the footer -------------------------------------------------------
    def refresh_hints(self):
        """Keys for the list, and on the right what the settings are now: 'David · offline guide · Optics'."""
        current = self.query_one("#goals", OptionList).highlighted_option
        opens = "Open" if current is not None and str(current.id).isdigit() else "Choose"
        about = [summary(self.settings)] if self.settings is not None else []
        title = themes.short_title(self.theme)
        voice = title.split(",")[0]  # without ", dark", when there is no room for it
        self.query_one(HintBar).update_hints(
            [("⏎", opens, "enter"), ("f1", "Help", "f1"), ("f2", "Settings", "f2"), ("^q", "Quit", "ctrl+q")],
            summary=[" · ".join(about + [title]), " · ".join(about + [voice]), " · ".join(about), title, voice],
            controls=False)

    # ----- choosing -----------------------------------------------------------
    @on(OptionList.OptionSelected, "#goals")
    def chosen(self, event):
        choice = event.option.id
        if choice == 'commons':
            from reason_commons.adapters.commons import continue_commons
            try:
                self.exit(continue_commons(self.root))
            except Exception as exc:
                self.notify(f'Could not open Reason Commons: {exc}', severity='error', timeout=8)
        elif choice in (SAMPLE, TOUR):
            self.exit(choice)
        elif choice == "setup":
            self.setup(first_run=True)
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
        def chosen(key):
            if key == 'help':
                self.push_screen(HelpScreen())
            elif key == 'setup':
                self.setup(first_run=self.first_run)
            elif key in (SAMPLE, TOUR):
                self.exit(key)
        choices = [('help', 'Using the workspace'), (TOUR, 'Practice with the guided tour'),
                   (SAMPLE, 'Explore an editorial example: Second Renaissance')]
        if self.settings is not None:
            choices.append(('setup', 'Choose your name and consultant'))
        self.push_screen(ChoiceScreen('Help and examples',
                         'Reason Commons keeps your words, model and history together. '
                         'Examples are separate from your working goals.', choices), chosen)

    def can_set_up(self):
        return self.settings is not None

    def settings_closed(self, result):
        if result == "setup":  # "You" in Settings: your name and consultant, the way first start asks
            self.setup(first_run=False)

    def keep_theme(self, name):
        super().keep_theme(name)
        if name:  # the list's colours and the footer follow the theme
            self.show_options(keep=self._marked)


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


def money(value):
    return pricing.money(value)


def replies_words(total):
    """'3 replies, ≈ $0.012', with any whose price is not known."""
    count = total["replies"]
    words = f"{count} {'reply' if count == 1 else 'replies'}, ≈ {money(total['usd'])}"
    return words + (f" ({total['unpriced']} at a price not known)" if total["unpriced"] else "")


def month_meter(total, limit):
    """The month in the footer: 'month ≈ $1.40 of $5', or 'month ≈ $5.20, over $5'."""
    spent = money(total["usd"])
    if limit is None:
        return f"month ≈ {spent}"
    return f"month ≈ {spent}, over {money(limit)}" if total["usd"] > limit else f"month ≈ {spent} of {money(limit)}"


def spent_words(entries):
    """What one send cost, for its notice: ' Reply ≈ $0.0049 (Haiku 5.5).' Nothing when nothing was paid for."""
    if not entries:
        return ""
    models = ", ".join(dict.fromkeys(pricing.label(entry["model"]) for entry in entries))
    if all(entry["outcome"] == "no_reply" for entry in entries):
        return f" No reply came from {models}; the request may still be billed."
    priced = [entry["usd"] for entry in entries if entry["usd"] is not None]
    if len(priced) < len(entries):
        return f" Reply from {models}; its cost is not known."
    return f" Reply ≈ {money(sum(priced))} ({models})."


def budget_notice(share, spent, limit):
    """Said once when this month's spending reaches 80% or 100% of the budget. The budget asks; it never blocks."""
    if share == 80:
        return (f"This month's Claude replies ≈ {money(spent)}: 80% of your {money(limit)} budget (estimate). "
                "Nothing is blocked.")
    return (f"This month's Claude replies ≈ {money(spent)}, past your {money(limit)} budget (estimate). "
            "Each send will ask first; nothing is blocked.")


def command_label(title, detail):
    """A command on one line: what it is, then, quieter, what it does and whether it asks the consultant."""
    text = Text(title, style="bold")
    text.append(" · " + detail, style="dim")
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
    cli_model = model
    from reason_commons.bootstrap import configured_consultant, create_case, open_case, usage_session
    settings = Settings.load()
    settings.apply()  # fills in only what flags and the environment leave unset
    store = Path(os.path.expanduser(store)).resolve()
    provider = provider or os.environ.get("REASON_COMMONS_PROVIDER") or "guided"
    speaker = speaker or os.environ.get("REASON_COMMONS_SPEAKER") or os.environ.get("USER") or "Me"
    usage = usage_session("workspace", settings=settings)
    # A model named here is for one reply with deeper reasoning; otherwise the one chosen at start, if any.
    factory = lambda chosen, model=None: configured_consultant(
        provider=chosen, model=model or (cli_model if chosen == provider else None),
        base_url=base_url if chosen == provider else None, usage=usage.record)
    if not store.exists():
        store.parent.mkdir(parents=True, exist_ok=True)
        create_case(store, name or store.name).close()
    app = ReasonCommonsApp(store, speaker, provider, lambda consultant: open_case(store, consultant=consultant),
                           factory, tour=tour, story=story, settings=settings,
                           usage=None if tour or story else usage)  # practice and reading show no meter
    return app.run()
