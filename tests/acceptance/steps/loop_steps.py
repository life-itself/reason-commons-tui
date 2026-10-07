"""Executable definitions for the goal-action-review loop in the case engine (S32, S37, S95, S101).

Setup and behavior go through application use cases: the fixture consultant proposes, the operator
accepts, and outcomes are read from the workspace and its text rendering. Nothing reaches into the store.
"""

from behave import given, when, then

from reason_commons.adapters.rendering import render_workspace
from tests.acceptance.steps.tree_steps import exactly, new_app
from tests.support import accept_all, submit

GOAL = {"operation": "record_goal", "temporary_id": "goal", "data": {
    "statement": "90% of orders delivered on time", "scope": "Forge workshop orders", "horizon": "October 30",
    "measure": "orders delivered on time / orders due", "baseline": "71% in September",
    "protections": ["95% of urgent requests acknowledged within four hours"]}}
FORECAST = [{"measure": "orders delivered on time / orders due", "expected": "80%", "scope": "Payments orders",
             "denominator": "orders due", "period": "October 5-16"},
            {"measure": "urgent requests acknowledged within four hours", "expected": "at least 95%",
             "scope": "urgent Payments requests", "denominator": "urgent requests", "period": "October 5-16",
             "bound": "at least 95%"}]


def pilot(review_date="October 19", **extra):
    return {"operation": "record_test", "temporary_id": "test", "data": {
        "statement": "Freeze each day's plan by 9:00 and keep urgent slots open", "goal_ref": "G1@1",
        "scope": "Payments orders, two weeks", "dose": "two urgent slots every day",
        "baseline": "71% of 412 Payments orders on time in September", "forecast": FORECAST,
        "stop_condition": "Stop if urgent acknowledgement falls below 95%", "review_date": review_date, **extra}}


def action(**data):
    return {"operation": "record_action", "temporary_id": "temp_a", "data": {
        "statement": "Maya freezes the plan at 9:00 each day", "test_ref": "test", "owner": "Maya",
        "authority": "Declared by Maya", "execution": "planned", "expected_state_attainment": "pending",
        "expected_state": "The day's plan is unchanged after 9:00 except through the urgent slots", **data}}


def say(context, text, *updates, declarations=None):
    context.provider.responses.append(exactly(*updates))
    result = submit(context.app, text, declarations=declarations)
    assert result["status"] == "saved", result
    return result


def forge_goal(context):
    new_app(context)
    say(context, "90% on time by October 30; keep acknowledging urgent requests within four hours", GOAL)
    accept_all(context.app)


def records(context):
    return {r["ref"]: r for r in context.app.inspect()["case"]["records"]}


def comparison(context, ref="P1@1"):
    return next(c for c in context.app.workspace(view="tests")["comparisons"] if c["test"]["ref"] == ref)


def text_view(context, view="tests"):
    return render_workspace(context.app.workspace(view=view))


# S32 Record a prospective pilot with enough detail to review.

@given("the group has supplied a baseline and a proposed bounded change")
def baseline_and_change(context):
    forge_goal(context)
    say(context, "September: 71% of 412 Payments orders on time. We could freeze the plan by 9:00.")
    accept_all(context.app)


@when("Sam commits to a pilot")
def commit_pilot(context):
    say(context, "Let's run it on Payments for two weeks; Maya owns it", pilot(), action(),
        declarations={"ownership": ["Maya"]})
    context.before_outcome = context.app.inspect()["case"]["revision"]
    accept_all(context.app)


@then("the pilot records the following review fields:")
def review_fields(context):
    fields = {f["field"]: f["value"] for f in comparison(context)["review_fields"]}
    assert list(fields) == [row["field"].strip() for row in context.table], list(fields)
    assert fields["owner and scope"] == "Maya · Payments orders, two weeks"
    assert fields["intervention and dose"].endswith("two urgent slots every day")
    assert fields["exact prediction"].startswith("80%") and fields["observation window"] == "October 5-16"
    assert "95% of urgent requests acknowledged within four hours" in fields["protected conditions"]
    assert fields["review date"] == "October 19"


@then("unknown fields remain visibly unknown")
def unknowns_visible(context):
    fields = {f["field"]: f["value"] for f in comparison(context)["review_fields"]}
    assert fields["alternative explanation"] is None
    assert "Alternative explanation: unknown" in text_view(context)


@then("the prediction is versioned before the outcome is supplied")
def versioned_first(context):
    test = records(context)["P1@1"]
    assert test["data"]["forecast"] == FORECAST
    history = context.app.history()["revisions"]
    first = next(s["revision"] for s in history if any(r["ref"] == "P1@1" for r in s["records"]))
    assert first <= context.before_outcome
    assert not any(r["kind"] == "observation" for r in records(context).values())


# S37 A review date is not a scheduled automation.

@given("a pilot has a review date of October 19")
def pilot_with_review_date(context):
    forge_goal(context)
    say(context, "Freeze the plan for two weeks on Payments; review on October 19", pilot())
    context.calls = len(context.provider.calls)
    context.files = sorted(p.relative_to(context.path.parent) for p in context.path.parent.rglob("*"))


@when("the pilot is saved")
def save_pilot(context):
    context.decision = accept_all(context.app)


@then('the view says "{words}"')
def view_says(context, words):
    assert words in text_view(context), text_view(context)


@then("no calendar event, message, background job, or external action is created")
def nothing_scheduled(context):
    assert len(context.provider.calls) == context.calls
    case_files = {p.relative_to(context.path.parent).parts[0] for p in context.path.parent.rglob("*")}
    assert case_files <= {f.parts[0] for f in context.files}  # nothing outside the case folder
    assert set(context.decision) <= {"status", "revision", "decision", "action", "refs", "closes", "leaves", "flags"}


# S95 Revisit test relevance when its referenced goal changes.

@given("test P1 version 1 explicitly serves goal G1 version 1")
def test_serves_goal(context):
    forge_goal(context)
    say(context, "Freeze the plan; Maya owns it", pilot(), action(), declarations={"ownership": ["Maya"]})
    accept_all(context.app)
    say(context, "Payments: 9 of 10 orders on time so far, Priya says it feels calmer",
        {"operation": "record_observation", "temporary_id": "temp_o", "data": {
            "test_ref": "P1@1", "measure": "orders delivered on time / orders due", "value": "9 of 10",
            "basis": "participant_report"}})
    accept_all(context.app)
    context.before = records(context)


@when("goal G1 receives a substantively different version 2")
def new_goal(context):
    say(context, "Our real goal is that customers can plan around our promised dates",
        {"operation": "record_goal", "temporary_id": "goal", "data": {
            "statement": "Customers can plan around Forge's promised dates", "replaces": "G1@1",
            "protections": ["95% of urgent requests acknowledged within four hours"]}})
    accept_all(context.app)


@then("P1 retains its original prediction and goal reference")
def p1_unchanged(context):
    assert records(context)["P1@1"] == context.before["P1@1"]
    assert records(context)["P1@1"]["data"]["goal_ref"] == "G1@1"


@then("its relevance to the current goal is marked review needed")
def relevance_review(context):
    flags = {e["ref"]: e["flags"] for e in context.app.workspace(view="backlog")["backlog"] if e["entry"] == "review"}
    assert [(f["cites"], f["change"], f["now"]) for f in flags["P1@1"]] == [("G1@1", "new_version", "G1@2")]
    assert "Review needed" in text_view(context) and "earlier version of the goal" in text_view(context)


@then("the next test decision shows that review need")
def next_decision_shows(context):
    say(context, "What should we test next?")
    workspace = context.app.workspace()
    assert [r["ref"] for r in workspace["test_reviews"]] == ["P1@1"]
    assert "Review needed" in render_workspace(workspace)


@then("neither the old result nor the participants' positions are rewritten")
def nothing_rewritten(context):
    now = records(context)
    assert all(now[ref] == record for ref, record in context.before.items())


# S101 Complete an action without claiming its expected effect occurred.

@given("a test action with an expected intermediate state and observation criterion")
def planned_action(context):
    forge_goal(context)
    say(context, "Freeze the plan; Maya owns it", pilot(), action(), declarations={"ownership": ["Maya"]})
    accept_all(context.app)
    assert records(context)["A1@1"]["data"]["expected_state"]


@when("the operator explicitly records that the action was completed")
def record_completion(context):
    context.before = records(context)
    completed = action(execution="completed", expected_state_attainment="unknown", replaces="A1@1", test_ref="P1@1")
    say(context, "Maya froze the plan at 9:00 every day this week", completed, declarations={"ownership": ["Maya"]})
    accept_all(context.app)


@then("execution is completed and expected-effect attainment remains unknown")
def completed_not_attained(context):
    current = [r for r in context.app.workspace(view="actions")["records"] if r["kind"] == "action"]
    assert [(r["ref"], r["data"]["execution"], r["data"]["expected_state_attainment"]) for r in current][-1] == (
        "A1@2", "completed", "unknown")
    # A reply may not claim the expected state was reached before a result is in the model.
    before = context.app.inspect()
    attained = action(execution="completed", expected_state_attainment="met", replaces="A1@2", test_ref="P1@1")
    context.provider.responses.append(exactly(attained))
    result = submit(context.app, "It worked", declarations={"ownership": ["Maya"]})
    assert result["status"] == "rejected" and "result" in result["reason"], result
    assert context.app.inspect()["case"] == before["case"]


@then('the receipt says "{words}"')
def receipt_says(context, words):
    assert words in text_view(context, "next"), text_view(context, "next")


@then("neither the prediction nor the system goal is marked achieved")
def nothing_achieved(context):
    now = records(context)
    assert now["P1@1"] == context.before["P1@1"] and now["G1@1"] == context.before["G1@1"]
    assert not any(r["kind"] in {"observation", "review"} for r in now.values())
    assert "achieved" not in text_view(context, "next").lower()
