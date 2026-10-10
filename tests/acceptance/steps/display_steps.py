"""Executable definitions for the workspace's display contract (S68, S69, S94).

Cases are built through the application use cases (``question_steps.case_with``) and read in the real
workspace, driven with keys the way a person drives it.
"""

from behave import given, then, when

from tests.acceptance.steps.question_steps import GOAL, asking, case_with, content, pilot_forecast, reported_results

PILOT = {"operation": "record_test", "temporary_id": "test", "data": {
    "statement": "Keep two urgent slots open each day", "goal_ref": "G1@1", "scope": "Payments orders",
    "stop_condition": "Stop if overtime passes 20 hours in any week", "review_date": "October 19",
    "forecast": [{"measure": "orders delivered on time / orders due", "expected": "80%", "scope": "Payments orders",
                  "denominator": "orders due", "period": "October 5-16"}]}}


def screen(context):
    return context.workspace.screen_text()


def choose_view(context, label):
    """Open a view from the visible Views list with the keyboard."""
    context.workspace.tab_to("views")
    options = context.workspace.read(lambda app: [str(o.prompt).strip("▸ ").strip()
                                                  for o in app.query_one("#views").options])
    current = context.workspace.read(lambda app: app.query_one("#views").highlighted or 0)
    steps = options.index(label) - current
    context.workspace.press(*(["down"] * steps if steps > 0 else ["up"] * -steps), "enter")


def unchanged(context):
    revision = context.workspace.case(lambda case: case.inspect()["case"]["revision"])
    return len(context.consultant.calls) == context.calls_before and revision == context.revision_before


# S68 Compress routine context and repeat consequential changes.

@given("Compact display and an unchanged goal and protections")
def compact_display(context):
    goal = {**GOAL, "data": {**GOAL["data"], "protections": ["Overtime at most 20 hours per week",
                                                             "No defects shipped to customers"]}}
    case_with(context, [
        ("90% on time by October 30", asking("Pick a change", "What will you try?", "Try one change.",
                                             updates=[goal]), None),
        ("Keep two urgent slots open on Payments, October 5-16", asking(
            "Name the first action", "Who opens the urgent slots each morning, and from when?",
            "A test teaches only once it is carried out.", updates=[PILOT]), None)])
    context.workspace.settle()
    assert context.workspace.read(lambda app: app.density) == "compact"
    context.revision_before = context.workspace.case(lambda case: case.inspect()["case"]["revision"])
    context.goal = goal["data"]


@when("Sam opens Explain this and returns to the current question")
def explain_and_return(context):
    context.workspace.tab_to("explain")
    context.workspace.press("enter")
    assert "Why this question" in content(context)
    context.workspace.press("escape")
    assert "Why this question" not in content(context)


@then("the pinned header shows commons, save status and speaker, and the focused control is framed")
def header(context):
    assert "Forge Sam · Saved" in screen(context)
    assert context.workspace.focused() == "editor"


@then("complete unchanged context is not duplicated inside each view")
def not_duplicated(context):
    shown = screen(context)
    for words in (context.goal["statement"], *context.goal["protections"]):
        assert shown.count(words) == 1, (words, shown)  # pinned once in the band, not again in the page
    for view in ("Tests", "Loop actions"):
        choose_view(context, view)
        assert screen(context).count(context.goal["statement"]) <= 1
    choose_view(context, "Next step")


@then("the goal and consequential safeguard band remain pinned")
def band_pinned(context):
    shown = screen(context)
    assert f"Goal {context.goal['statement']}" in shown
    assert "Overtime at most 20 hours per week" in shown and "No defects shipped to customers" in shown


@when("the goal changes or Sam activates Goal or Commons context")
def activate_context(context):
    choose_view(context, "Commons context")


@then("complete goal, horizon, protections, test boundaries, response target and revision appear")
def complete_context(context):
    assert context.workspace.read(lambda app: app.view_name) == "context"
    shown = content(context).replace("**", "").replace("\\", "")  # the page, before it wraps on screen
    for words in (context.goal["statement"], "Horizon: October 30", "Measure: orders delivered on time / orders due",
                  "Baseline: 71% in September", "Protect: Overtime at most 20 hours per week",
                  "Protect: No defects shipped to customers", "Keep two urgent slots open each day",
                  "scope: Payments orders", "period: October 5-16", "stop if: Stop if overtime passes 20 hours",
                  "review: October 19; no reminder scheduled", "Who opens the urgent slots each morning",
                  f"saved at revision {context.revision_before}"):
        assert words in shown, (words, shown)


@then("requesting context makes no consultant call")
def no_call(context):
    assert unchanged(context)


# S69 Keep a consequential breach visible while browsing.

@given("urgent acknowledgement is 90 percent against a 95 percent guardrail")
def acknowledgement_breach(context):
    context.review_size = (120, 40)
    pilot_forecast(context)
    reported_results(context)
    context.workspace.settle()
    context.revision_before = context.workspace.case(lambda case: case.inspect()["case"]["revision"])


BREACH = "Breach urgent requests acknowledged within four hours: 18 of 20 (90%), outside at least 95%"


@when("Sam opens History, test sources or Other moves in Compact display")
def browse(context):
    assert context.workspace.read(lambda app: app.density) == "compact"
    context.seen = {}
    for view in ("History", "Your words"):
        choose_view(context, view)
        context.seen[view] = screen(context)
    choose_view(context, "Next step")
    context.workspace.tab_to("moves")
    context.workspace.press("enter")
    context.seen["Other moves"] = screen(context)
    context.workspace.press("escape")


@then("the unresolved breach and both values remain visible")
def breach_everywhere(context):
    for name, shown in context.seen.items():
        assert BREACH in shown, (name, shown)
    assert unchanged(context)


@then("a delivery success marker does not obscure the breach")
def success_does_not_hide(context):
    # Delivery met its forecast (40 of 50, 80%); nothing marks the pilot a success over the breach.
    for name, shown in context.seen.items():
        assert "success" not in shown.lower() and BREACH in shown, name


# S94 Leave a question open and return without reconstructing it.

@given("a live question and an answer draft")
def live_question_and_draft(context):
    case_with(context, [("90% on time by October 30", asking(
        "Inspect the baseline", "How many orders ship on time today, and how do you know?",
        "A baseline makes a later result comparable.", updates=[GOAL]), None)])
    context.workspace.settle()
    context.draft = "About 71% in September,\nfrom the delivery report"
    context.workspace.tab_to("editor")
    context.workspace.type(context.draft)
    context.target = context.workspace.read(lambda app: app.workspace_value["target"])
    context.revision_before = context.workspace.case(lambda case: case.inspect()["case"]["revision"])


@when("the operator opens history and returns with Esc")
def history_and_back(context):
    choose_view(context, "History")
    assert "Every saved step" in screen(context)
    context.workspace.press("escape")


@then("the open question, response target, and exact draft are restored")
def restored(context):
    assert context.workspace.read(lambda app: app.view_name) == "next"
    assert "How many orders ship on time today" in screen(context)
    assert context.workspace.read(lambda app: app.workspace_value["target"]) == context.target
    assert context.workspace.read(lambda app: app.query_one("#editor").text) == context.draft
    assert context.workspace.focused() == "editor"


@then("inspection creates no reasoning revision or consultant call")
def no_revision(context):
    assert unchanged(context)
