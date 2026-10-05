"""Executable definitions for the p1 workspace scenarios.

The steps drive the real workspace the way a person does (keys, Tab and Enter) and
read outcomes at the application boundary: the fixture consultant's calls, the
case's revisions and retained inputs. Setup goes through the use cases
(``tests/acceptance/workspace.py``); no step writes case files.
"""

import os

from behave import given, then, when

from reason_commons.bootstrap import create_case, open_case
from tests.acceptance.workspace import HeldConsultant, Workspace, ask, build_forge
from tests.support import ScriptedConsultant

TEST = {"operation": "record_test", "temporary_id": "test", "data": {
    "statement": "Freeze each day's plan by 9:00 with two urgent slots", "goal_ref": "G1@1",
    "scope": "Payments orders, two weeks",
    "forecast": [{"measure": "orders delivered on time", "expected": "80%", "scope": "Payments orders",
                  "denominator": "orders due"},
                 {"measure": "urgent requests acknowledged within four hours", "expected": "95%",
                  "scope": "Payments orders", "denominator": "urgent requests"}],
    "stop_condition": "Acknowledgement below 95%", "review_date": "October 16"}}


class Unavailable(ScriptedConsultant):
    """A consultant adapter that cannot be reached; every call is counted and fails."""

    def propose(self, request):
        self.calls.append(request)
        raise ConnectionError("offline")


def open_workspace(context, consultant=None, size=(120, 40), with_test=False):
    """The Forge case in the workspace; ``with_test`` adds a ninth reply recording a bounded test."""
    context.consultant = consultant or ScriptedConsultant()
    builder = ScriptedConsultant()
    replies = None
    if with_test:
        from tests.acceptance.workspace import FORGE_REPLIES
        replies = FORGE_REPLIES + [("Expect 80% on time, and keep 95% of urgent requests acknowledged.",
                                    ask("Plan the next action", "What is the first concrete action, and when?",
                                        "A test teaches only once it is carried out.",
                                        context=("goal",), updates=[TEST]))]
    build_forge(context.path, builder, **({"replies": replies} if replies else {}))
    context.consultant.calls.extend(builder.calls)  # the counter covers the case's whole history
    context.workspace = Workspace(context.path, context.consultant, size=size)
    context.workspaces.append(context.workspace)
    remember(context)


def remember(context):
    """The counters and live target a scenario compares against."""
    context.calls_before = len(context.consultant.calls)
    context.revision_before = revision(context)
    context.target_before = context.workspace.read(lambda app: app.workspace_value["target"])


def revision(context):
    return context.workspace.case(lambda case: case.inspect()["case"]["revision"])


def question(context):
    return context.workspace.read(lambda app: (app.workspace_value["question"] or {}).get("data", {}))


def new_calls(context):
    return context.consultant.calls[context.calls_before:]


def draft(context):
    return context.workspace.read(lambda app: app.query_one("#editor").text)


def caret(context):
    return context.workspace.read(lambda app: app.query_one("#editor").cursor_location)


def screen_name(context):
    return context.workspace.read(lambda app: type(app.screen).__name__)


def focus_editor(context):
    context.workspace.read(lambda app: app.query_one("#editor").focus())
    context.workspace.settle()
    assert context.workspace.focused() == "editor"


def activate_send(context):
    context.workspace.tab_to("send")
    context.workspace.press("enter")


def choose_in_list(context, list_id, words):
    """Arrow through a list until the highlighted item contains the words, then Enter."""
    w = context.workspace
    w.tab_to(list_id)

    def labels(app):
        options = app.screen.query_one("#" + list_id).options
        return [str(o.prompt) for o in options]
    index = next(i for i, label in enumerate(w.read(labels)) if words in label)
    current = w.read(lambda app: app.screen.query_one("#" + list_id).highlighted) or 0
    w.press(*(["down"] * (index - current) if index >= current else ["up"] * (current - index)))
    w.press("enter")


def menu_labels(context):
    return context.workspace.read(lambda app: [str(o.prompt) for o in app.screen.query_one("OptionList").options])


def choose_in_menu(context, words):
    """In an open menu, arrow to the item that contains the words and press Enter."""
    w = context.workspace
    labels = menu_labels(context)
    index = next(i for i, label in enumerate(labels) if words in label)
    current = w.read(lambda app: app.screen.query_one("OptionList").highlighted) or 0
    w.press(*(["down"] * (index - current) if index >= current else ["up"] * (current - index)))
    w.press("enter")


def activate(context, control):
    """Reach a visible control with Tab and activate it with Enter; 'A > B' then chooses B inside A."""
    w = context.workspace
    first, _, second = (part.strip() for part in control.partition(">"))
    buttons = {"Other moves": "moves", "Explain this": "explain", "Help": "help", "Actions": "actions",
               "Send": "send", "Retry": "retry"}
    if first in buttons:
        w.tab_to(buttons[first])
        w.press("enter")
    else:  # a destination in the Views list
        choose_in_list(context, "views", first)
    if not second:
        return
    if first == "History":
        choose_in_list(context, "timeline", second)
    elif first == "Actions":
        w.type(second)
        w.press("enter")
    else:
        choose_in_menu(context, second)


# ----- Background ----------------------------------------------------------------
@given("the persistent TUI workspace is active")
def workspace_active(context):
    context.wants_workspace = True


@given('case "forge" at revision {number:d} with current question "{decision}"')
def forge_at(context, number, decision):
    open_workspace(context)
    assert revision(context) == number and question(context)["decision"] == decision


@given('History contains the earlier questions "{first}" and "{second}"')
def history_contains(context, first, second):
    answered = context.workspace.read(lambda app: [e["answered"] for e in app.history()["entries"]])
    assert first in answered and second in answered, answered


@given("the consultant call counter is {count:d}")
def call_counter_is(context, count):
    assert len(context.consultant.calls) == count


@then("the consultant call counter remains {count:d}")
def call_counter_remains(context, count):
    assert len(context.consultant.calls) == count, len(context.consultant.calls)


@then("the reasoning revision remains {number:d}")
def revision_remains(context, number):
    assert revision(context) == number


# ----- S07: stored views behind visible controls -----------------------------------
@when('the participant activates "{control}" using Tab and Enter')
def activate_control(context, control):
    activate(context, control)


VIEWS = {
    "alternatives for this question": lambda c: screen_name(c) == "ChoiceScreen" and "Other moves" in c.workspace.screen_text(),
    "questions and event history": lambda c: c.workspace.read(lambda app: app.view_name) == "history"
    and "Define success" in c.workspace.screen_text(),
    "authored rationale": lambda c: c.workspace.read(lambda app: app.explain)
    and question(c)["rationale"] in c.workspace.screen_text(),
    "control help": lambda c: screen_name(c) == "HelpScreen" and "Keys" in c.workspace.screen_text(),
    "adapter call count": lambda c: screen_name(c) == "CallsScreen" and "Consultant calls in this goal: 8"
    in c.workspace.screen_text(),
}


@then('the view "{view}" is rendered from stored state')
def view_rendered(context, view):
    if view.startswith("archived "):
        decision = view[len("archived "):]
        moment = context.workspace.read(lambda app: (app.revision, app.view_name))
        text = context.workspace.screen_text()
        assert moment[0] is not None and moment[1] == "next", moment
        assert decision in text and "Read-only" in text, text[:300]
        return
    assert VIEWS[view](context), context.workspace.screen_text()[:600]


# ----- Literal response text and deliberate submission -----------------------------
@given("Response owns focus")
@given("Response owns focus on a current question")
def response_owns_focus(context):
    if not getattr(context, "workspace", None):
        open_workspace(context)
    focus_editor(context)
    remember(context)


@when('the participant types "{text}" then activates Send')
@when('Sam types "{text}" then activates Send')
def type_and_send(context, text):
    context.workspace.type(text)
    activate_send(context)


@then('exactly one consultant request contains the literal answer "{text}"')
@then('exactly one consultant request preserves the literal answer "{text}"')
def one_literal_request(context, text):
    calls = new_calls(context)
    assert len(calls) == 1 and calls[0]["input"]["text"] == text, [c["input"]["text"] for c in calls]


@then("neither the alternatives nor a historical question opens")
@then("no historical question or alternatives view opens")
def nothing_else_opens(context):
    assert screen_name(context) not in {"ChoiceScreen", "CommandPalette"}
    assert context.workspace.read(lambda app: (app.revision, app.view_name)) == (None, "next")


@then("the session does not quit")
def session_continues(context):
    assert context.workspace.running()


@then("one semantic request preserves the entire statement")
def whole_statement(context):
    calls = new_calls(context)
    assert len(calls) == 1 and calls[0]["input"]["text"] == "I disagree because overtime worsens"


@then("no local parser infers representation, belief or reliance")
def no_inference(context):
    value = new_calls(context)[0]["input"]
    assert value["intent"] == "answer" and not value.get("declarations")
    kinds = {r["kind"] for r in context.workspace.case(lambda case: case.inspect()["case"]["records"])}
    assert kinds <= {"goal", "note", "intervention", "test", "action", "observation", "review", "claim", "link",
                     "retraction"}


@given('the response editor is focused on current question "{decision}"')
def editor_on_question(context, decision):
    open_workspace(context)
    assert question(context)["decision"] == decision
    focus_editor(context)


@when('the operator types or pastes "{text}" and presses Enter')
def type_then_enter(context, text):
    context.typed = text
    context.workspace.type(text)
    context.workspace.press("enter")


@then("those characters and the newline are retained in the draft")
def draft_kept(context):
    assert draft(context) == context.typed + "\n", repr(draft(context))


@then("no navigation, quit, stance or consultant request occurs")
def nothing_happened(context):
    assert context.workspace.running() and not new_calls(context)
    assert context.workspace.read(lambda app: (app.view_name, app.revision)) == ("next", None)
    assert screen_name(context) == "Screen" and revision(context) == context.revision_before


@when("the operator Tabs to Send and presses Enter")
def tab_to_send(context):
    activate_send(context)


@then('exactly one request preserves the full literal draft for "{decision}"')
def full_draft_sent(context, decision):
    calls = new_calls(context)
    assert len(calls) == 1 and calls[0]["input"]["text"] == context.typed + "\n"
    assert calls[0]["input"]["response_target"] == context.target_before["response_target"]
    asked = context.workspace.case(lambda case: next(r for r in case.inspect()["case"]["records"]
                                                      if r["ref"] == calls[0]["input"]["response_target"]))
    assert asked["data"]["decision"] == decision


# ----- S51: a multiline draft survives navigation ------------------------------------
@given("Sam is composing a multiline answer with an embedded command-looking line")
def multiline_draft(context):
    open_workspace(context)
    focus_editor(context)
    context.typed = "Two things:\n:quit\nand keep the urgent slots"
    context.workspace.type(context.typed)


@when("Sam opens history and then returns to the editor")
def history_and_back(context):
    choose_in_list(context, "views", "History")
    assert context.workspace.read(lambda app: app.view_name) == "history"
    choose_in_list(context, "views", "Next step")
    context.workspace.tab_to("editor")


@then("the exact draft is retained")
def exact_draft(context):
    assert draft(context) == context.typed


@then("its embedded line has not been executed as a command")
def not_executed(context):
    assert context.workspace.running() and not new_calls(context)


@then("submission invokes the consultant only once")
def submitted_once(context):
    activate_send(context)
    calls = new_calls(context)
    assert len(calls) == 1 and calls[0]["input"]["text"] == context.typed


# ----- S114: the workspace by default --------------------------------------------------
@given("interactive terminal input and output at {width:d} columns by {height:d} rows")
def terminal_size(context, width, height):
    context.size = (width, height)


@when("the operator launches a new case without a presentation flag")
def launch_new(context):
    create_case(context.path, "Forge").close()
    context.consultant = ScriptedConsultant()
    context.workspace = Workspace(context.path, context.consultant, size=context.size)
    context.workspaces.append(context.workspace)
    remember(context)


@then("the full-screen workspace shows the question, response editor, destinations and footer")
def full_screen(context):
    text = context.workspace.screen_text()
    assert "What is happening, and what would count as better?" in text
    visible = context.workspace.read(lambda app: [app.query_one(f"#{n}").display for n in ("editor", "views")])
    assert all(visible) and "Next step" in text and "Save & quit" in text


@then("save status, declared operator and focused control remain visible")
def status_visible(context):
    text = context.workspace.screen_text()
    assert "Saved" in text and "Sam" in text and "Focus: Answer" in text


@then("no tour or command syntax is required to answer or leave")
def answer_and_leave(context):
    assert context.workspace.read(lambda app: not app.tour)
    context.workspace.type("Late deliveries keep upsetting customers")
    activate_send(context)
    assert len(new_calls(context)) == 1 and revision(context) == context.revision_before + 1
    context.workspace.press("ctrl+q")
    assert not context.workspace.running()


# ----- S119: every action through visible controls -------------------------------------
@given("the default TUI and focused response editor")
def default_tui(context):
    open_workspace(context)
    focus_editor(context)


@when("the operator reaches Actions or Help using Tab and Enter")
def reach_actions(context):
    activate(context, "Actions")

    def entries(app):
        from textual.command import CommandList
        return [str(o.prompt) for o in app.screen.query_one(CommandList).options]
    context.entries = context.workspace.read(entries)


@then("the displayed controls identify valid actions and local or consultant consequences")
def consequences_named(context):
    for entry in context.entries:
        name, _, detail = entry.partition("\n")
        assert "local" in detail.lower() or "asks the consultant" in detail.lower(), entry


@then("stored explanation, sources, history, export and Save and quit have control paths")
def control_paths(context):
    names = [entry.partition("\n")[0] for entry in context.entries]
    for wanted in ("Explain this question", "View: Your words", "View: History", "Export case", "Save and quit"):
        assert wanted in names, (wanted, names)


@then("Help for controls is distinct from Explain this for reasoning")
def help_distinct(context):
    w = context.workspace
    w.type("Help")
    w.press("enter")
    assert screen_name(context) == "HelpScreen" and "Keys" in w.screen_text()
    w.press("escape")
    activate(context, "Explain this")
    text = w.screen_text()
    assert question(context)["rationale"] in text and "Ctrl+S" not in text


# ----- S120: recovering a failed request ------------------------------------------------
@given("a retained response draft and provider failure after input retention")
def failure_after_retention(context):
    open_workspace(context, consultant=ScriptedConsultant([ConnectionError("offline")]))
    focus_editor(context)
    context.typed = "Freeze the plan and keep two urgent slots"
    context.workspace.type(context.typed)
    activate_send(context)


@when("the operator opens the failure receipt and retries the retained input")
def retry_from_receipt(context):
    context.receipt = context.workspace.screen_text()
    context.revision_at_failure = revision(context)
    activate(context, "Retry")


@then("the receipt distinguishes input retained from uncommitted reasoning")
def receipt_text(context):
    assert "Saved, but not answered yet" in context.receipt and context.typed in context.receipt
    assert context.revision_at_failure == context.revision_before


@then("retry uses the same request identity and applies at most once")
def same_identity(context):
    calls = new_calls(context)
    assert len(calls) == 2 and calls[0]["input"]["request_id"] == calls[1]["input"]["request_id"]
    assert revision(context) == context.revision_before + 1
    assert not context.workspace.read(lambda app: app.retryable())


@then("view state, draft provenance and the correct live target remain recoverable")
def recoverable(context):
    rid = new_calls(context)[0]["input"]["request_id"]
    source = context.workspace.case(lambda case: case.sources()["sources"][rid])
    assert source["text"] == context.typed and source["speaker"] == "Sam"
    live = context.workspace.read(lambda app: (app.view_name, app.workspace_value["target"]))
    assert live[0] == "next" and live[1]["response_target"] != context.target_before["response_target"]


# ----- S47: offline navigation ---------------------------------------------------------
@given("a saved case and an unavailable consultant adapter")
def offline_case(context):
    open_workspace(context, consultant=Unavailable(), with_test=True)


@when("Sam opens options, rationale, history, or the bounded test")
def open_stored_views(context):
    w, seen = context.workspace, {}
    activate(context, "Other moves")
    seen["options"] = screen_name(context) == "ChoiceScreen"
    w.press("escape")
    activate(context, "Explain this")
    seen["rationale"] = question(context)["rationale"] in w.screen_text()
    choose_in_list(context, "views", "History")
    seen["history"] = "Define success" in w.screen_text()
    choose_in_list(context, "views", "Tests")
    seen["test"] = "ORIGINAL FORECAST" in w.screen_text() and "80%" in w.screen_text()
    context.seen = seen


@then("every stored view works without the adapter")
def views_work(context):
    assert all(context.seen.values()), context.seen
    assert not new_calls(context)


@then("semantic work is clearly pending until an adapter is available")
def semantic_pending(context):
    choose_in_list(context, "views", "Next step")
    focus_editor(context)
    context.workspace.type("Payments orders only")
    activate_send(context)
    text = context.workspace.screen_text()
    assert "Saved, but not answered yet" in text and "Retry" in text
    assert revision(context) == context.revision_before


# ----- S118: an answer arrives while browsing ------------------------------------------
@given("a durably retained submission and pending consultant request")
def pending_request(context):
    open_workspace(context, consultant=HeldConsultant())
    focus_editor(context)
    context.workspace.type("Payments orders only, two weeks")
    context.consultant.hold()
    context.workspace.wait_for_replies = False
    context.workspace.press("ctrl+s")
    with open_case(context.path, writable=False) as case:
        assert any(s.get("text") == "Payments orders only, two weeks" for s in case.sources()["sources"].values())


@given("the operator has selected a source in History")
def select_in_history(context):
    choose_in_list(context, "views", "History")
    context.workspace.tab_to("timeline")
    context.workspace.press("up", "up")
    context.selected = context.workspace.read(lambda app: app.query_one("#timeline").highlighted)
    context.focus_before = context.workspace.focused()


@when("a valid next response completes")
def response_completes(context):
    context.consultant.release.set()
    context.workspace.wait_for_replies = True
    context.workspace.settle()


@then("an Answer ready notice is visible without changing the selected source or focus")
def answer_ready(context):
    assert "Answer ready" in context.workspace.screen_text()
    assert context.workspace.read(lambda app: (app.view_name, app.query_one("#timeline").highlighted)) == (
        "history", context.selected)
    assert context.workspace.focused() == context.focus_before


@then("returning to Next presents the committed next question")
def next_question(context):
    choose_in_list(context, "views", "Next step")
    assert "What should we observe next?" in context.workspace.screen_text()


@then("no second request or duplicate commit occurs")
def no_duplicate(context):
    assert len(new_calls(context)) == 1 and revision(context) == context.revision_before + 1


# ----- S117: minimum terminal size -----------------------------------------------------
@given("a v1 goal and test with a material safeguard at 120 columns by 40 rows")
def goal_and_test(context):
    open_workspace(context, with_test=True)
    focus_editor(context)
    context.workspace.type("Thursday, before the stand-up")
    w = context.workspace
    w.press("ctrl+t")
    w.press("down")
    w.press("ctrl+t")
    context.state = w.read(lambda app: (app.query_one("#editor").text, app.query_one("#editor").cursor_location,
                                        app.workspace_value["target"], getattr(app.focused, "id", None),
                                        app.selected_claim))
    assert context.state[3] == "editor" and context.state[4]


@when("the terminal resizes to 80 columns by 24 rows and back")
def resize_and_back(context):
    w = context.workspace
    w.resize(80, 24)
    context.narrow = w.screen_text()
    context.narrow_panes = w.read(lambda app: (app.query_one("#views").has_class("hidden"),
                                               app.query_one("#views-button").has_class("hidden")))
    w.resize(120, 40)


@then("the question, safeguard, response and footer remain reachable and readable")
def narrow_readable(context):
    text = context.narrow
    for words in ("What is the first concrete action", "Protect", "95% of urgent requests acknowledged",
                  "Answer as Sam", "Save & quit"):
        assert words in text, (words, text[:500])


@then("hidden auxiliary panes have a visible Views destination")
def views_destination(context):
    assert context.narrow_panes == (True, False)  # the list is hidden; the Views control is shown


@then("the draft, target, focus and selected exact record survive without restart")
def state_survives(context):
    after = context.workspace.read(lambda app: (app.query_one("#editor").text, app.query_one("#editor").cursor_location,
                                                app.workspace_value["target"], getattr(app.focused, "id", None),
                                                app.selected_claim))
    assert after == context.state and context.workspace.running()


# ----- Other moves -----------------------------------------------------------------------
@given('Other moves is open for "{decision}"')
def other_moves_open(context, decision):
    open_workspace(context)
    assert question(context)["decision"] == decision
    activate(context, "Other moves")
    assert screen_name(context) == "ChoiceScreen"


@when('Sam presses Esc, focuses Response, types "{text}" and activates Send')
def esc_then_send(context, text):
    w = context.workspace
    w.press("escape")
    w.tab_to("editor")
    w.type(text)
    activate_send(context)


@then('exactly one semantic request contains "{text}"')
def one_semantic(context, text):
    calls = new_calls(context)
    assert len(calls) == 1 and calls[0]["input"]["text"] == text


@then('it answers "{decision}" without recording a menu decision')
def answers_question(context, decision):
    value = new_calls(context)[0]["input"]
    assert value["response_target"] == context.target_before["response_target"] and value["intent"] == "answer"
    cursor = context.workspace.case(lambda case: case.inspect()["cursor"]) or {}
    assert not cursor.get("menu")


@given('Other moves shows Ask another question labeled "{label}"')
def other_moves_labelled(context, label):
    open_workspace(context)
    activate(context, "Other moves")
    assert any("Ask another question" in item and label in item for item in menu_labels(context)), menu_labels(context)


@when("Sam selects that item with arrows and presses Enter")
def choose_ask_another(context):
    choose_in_menu(context, "Ask another question")


@then("one consultant request contains the stored intent and response target")
@then("one request contains the stored intent and current response target")
def intent_request(context):
    calls = new_calls(context)
    assert len(calls) == 1, len(calls)
    value = calls[0]["input"]
    assert value["intent"] == "another_question"
    assert value["response_target"] == context.target_before["response_target"]


@then("there is no second confirmation for the same explicit request")
def no_second_confirmation(context):
    assert screen_name(context) == "Screen" and len(new_calls(context)) == 1


@given("Other moves contains Inspect rationale and Ask another question")
def other_moves_items(context):
    activate(context, "Other moves")
    labels = menu_labels(context)
    assert any("Inspect rationale" in item for item in labels) and any("Ask another question" in item for item in labels)
    context.workspace.press("escape")


@when("Sam opens Other moves")
def open_other_moves(context):
    activate(context, "Other moves")
    context.labels = menu_labels(context)


@then('Inspect rationale says "{words}"')
def rationale_label(context, words):
    assert any("Inspect rationale" in item and words in item for item in context.labels), context.labels


@then('Ask another question says "{words}"')
def another_label(context, words):
    assert any("Ask another question" in item and words in item for item in context.labels), context.labels


@when("Sam selects Inspect rationale and presses Enter")
def choose_rationale(context):
    choose_in_menu(context, "Inspect rationale")


@then("no consultant request is made")
def no_request(context):
    assert not new_calls(context)
    assert question(context)["rationale"] in context.workspace.screen_text()


@when("Sam returns and activates Ask another question")
def return_and_ask(context):
    activate(context, "Other moves")
    choose_in_menu(context, "Ask another question")


# ----- Esc restores what inspection changed --------------------------------------------
@when("Sam opens History > Define success and presses Esc")
def history_moment_and_back(context):
    focus_editor(context)
    context.workspace.type("Freeze the plan")
    context.before = context.workspace.read(lambda app: (app.view_name, app.query_one("#editor").text))
    activate(context, "History > Define success")
    assert context.workspace.read(lambda app: app.revision) is not None
    context.workspace.press("escape")


@then("the previous view and draft are restored")
def previous_restored(context):
    now = context.workspace.read(lambda app: (app.view_name, app.query_one("#editor").text))
    assert now == context.before and context.workspace.read(lambda app: app.revision) is None


@then('the live response target remains "{decision}"')
def live_target_remains(context, decision):
    assert context.workspace.read(lambda app: app.workspace_value["target"]) == context.target_before
    assert question(context)["decision"] == decision


@then("quoting the historical question in Response does not change that target")
def quoting_keeps_target(context):
    focus_editor(context)
    context.workspace.type(" Define success: What would count as dependable delivery for Forge?")
    activate_send(context)
    assert new_calls(context)[0]["input"]["response_target"] == context.target_before["response_target"]


@given("the current question has stored rationale and evidence references")
def rationale_and_evidence(context):
    data = question(context)
    assert data["rationale"] and data.get("required_context_refs")
    focus_editor(context)
    context.workspace.type("Freeze the plan")
    context.before = context.workspace.read(lambda app: (app.view_name, app.query_one("#editor").text))


@when("Sam activates Explain this")
def explain_this(context):
    activate(context, "Explain this")


@then("the rationale and referenced reports are displayed")
def rationale_shown(context):
    text = context.workspace.screen_text()
    assert question(context)["rationale"] in text
    assert "The September delivery report says 71% of 412 orders shipped on time." in text, text[:800]


@then("the view makes no claim to expose a private model thought trace")
def no_thought_trace(context):
    text = context.workspace.screen_text().lower()
    assert "saved explanation" in text and "thought" not in text and "thinking" not in text


@then("Esc restores the originating view and draft")
def esc_restores(context):
    context.workspace.press("escape")
    now = context.workspace.read(lambda app: (app.view_name, app.query_one("#editor").text))
    assert now == context.before and not context.workspace.read(lambda app: app.explain)


@given("a displayed options menu and an answer draft")
def menu_and_draft(context):
    open_workspace(context)
    focus_editor(context)
    context.workspace.type("Freeze the plan")
    context.before = context.workspace.read(lambda app: (app.view_name, app.query_one("#editor").text,
                                                         app.workspace_value["target"]))
    activate(context, "Other moves")
    assert screen_name(context) == "ChoiceScreen"


@when("the operator activates Cancel or presses Esc")
def cancel_menu(context):
    context.workspace.tab_to("cancel")
    context.workspace.press("enter")


@then("the prior view, open question, and exact draft are restored")
def prior_restored(context):
    assert screen_name(context) == "Screen"
    now = context.workspace.read(lambda app: (app.view_name, app.query_one("#editor").text,
                                              app.workspace_value["target"]))
    assert now == context.before


@then("no revision or consultant call is created")
@then("no case revision or consultant call is created")
def no_revision_or_call(context):
    assert not new_calls(context) and revision(context) == context.revision_before


@given('a partially edited response with caret position and current question "{decision}"')
def partial_response(context, decision):
    open_workspace(context)
    assert question(context)["decision"] == decision
    focus_editor(context)
    context.workspace.type("Freeze the plan by nine")
    context.workspace.press("left", "left", "left", "left", "left")
    context.before = context.workspace.read(lambda app: (app.view_name, app.query_one("#editor").text,
                                                         app.query_one("#editor").cursor_location,
                                                         app.query_one("#main").scroll_y))


@when("the operator opens Explain this and a stored source then returns with Esc")
def explain_source_and_back(context):
    activate(context, "Explain this")
    choose_in_list(context, "views", "Your words")
    assert context.workspace.read(lambda app: app.view_name) == "sources"
    context.workspace.press("escape")


@then("the originating view, selection, semantic scroll anchor and draft caret are restored")
def origin_restored(context):
    now = context.workspace.read(lambda app: (app.view_name, app.query_one("#editor").text,
                                              app.query_one("#editor").cursor_location,
                                              app.query_one("#main").scroll_y))
    assert now == context.before, (now, context.before)
    assert not context.workspace.read(lambda app: app.explain) and context.workspace.focused() == "editor"


# ----- S72: offline shell utilities --------------------------------------------------------
@given("a saved valid case and unavailable provider")
def saved_case_offline(context):
    import os
    build_forge(context.path, ScriptedConsultant())
    context.folder = context.path.parent
    with open_case(context.path) as case:
        case.export(str(context.folder / "case.reasoncase"))
    # Any provider call would fail: the configured consultant has no key and an unreachable URL.
    context.environment = {**os.environ, "REASON_COMMONS_PROVIDER": "anthropic",
                           "REASON_COMMONS_ANTHROPIC_URL": "http://127.0.0.1:9/v1", "NO_COLOR": "1"}
    context.environment.pop("ANTHROPIC_API_KEY", None)


@when('the shell command "{command}" is invoked')
def invoke_shell(context, command):
    import subprocess
    import sys
    from pathlib import Path
    words = command.split()
    assert words[0] == "reason-commons"
    root = Path(__file__).resolve().parents[3]
    environment = dict(context.environment, PYTHONPATH=os.pathsep.join([str(root / "src"), str(root)]))
    context.result = subprocess.run([sys.executable, "-m", "reason_commons", *words[1:]], cwd=context.folder,
                                    env=environment, capture_output=True, text=True, timeout=60)


@then("it exits 0 without a provider call")
def exits_cleanly(context):
    assert context.result.returncode == 0, context.result.stderr
    assert "anthropic" not in context.result.stderr.lower() and "unavailable" not in context.result.stderr.lower()


@then('stdout contains only "{output}"')
def stdout_only(context, output):
    import json
    import re
    out = context.result.stdout
    assert "\x1b[" not in out and out.strip()
    if output == "requested help":
        assert out.startswith("usage: reason-commons")
    elif output == "version":
        assert re.fullmatch(r"reason-commons \S+\n", out) or re.fullmatch(r"\S+\n", out), repr(out)
    else:
        value = json.loads(out)
        assert isinstance(value, dict) and value["schema_version"] == "1"


@then("diagnostics if any go to stderr")
def diagnostics_on_stderr(context):
    assert "Traceback" not in context.result.stdout and "Error" not in context.result.stdout


# ----- S110: an option from a later delivery profile ---------------------------------------
@given("a v1 semantic response contains an option opening a Cloud view")
def cloud_option(context):
    def reply(request):
        from tests.support import proposal
        value = proposal(request)
        value["intervention"]["options"] = [{"id": "cloud", "label": "Open the scoped Cloud view",
                                             "action": {"type": "view", "target": "cloud"}}]
        return value
    open_workspace(context, consultant=ScriptedConsultant([reply]))
    focus_editor(context)
    context.typed = "Sales and production want opposite things"
    context.workspace.type(context.typed)


@when("the response is validated")
def response_validated(context):
    activate_send(context)


@then("the proposal is rejected with a local unsupported-action receipt")
def rejected_receipt(context):
    rid = new_calls(context)[0]["input"]["request_id"]
    attempts = context.workspace.case(lambda case: case.receipts(rid)["attempts"])
    assert any(a.get("status") == "rejected" for a in attempts), attempts
    assert any("out-of-profile" in str(a.get("message", "")) for a in attempts), attempts
    assert "the consultant's reply was invalid" in context.workspace.screen_text()


@then("the input, live response target, and prior revision remain intact")
def intact(context):
    rid = new_calls(context)[0]["input"]["request_id"]
    assert context.workspace.case(lambda case: case.sources()["sources"][rid]["text"]) == context.typed
    assert revision(context) == context.revision_before
    assert context.workspace.read(lambda app: app.workspace_value["target"]) == context.target_before


@then("no menu exposes the unavailable option")
def option_not_offered(context):
    actions = context.workspace.read(lambda app: app.workspace_value["available_actions"])
    assert not any("cloud" in a["id"] for a in actions)
    activate(context, "Other moves")
    assert not any("Cloud" in label for label in menu_labels(context))
    context.workspace.press("escape")
