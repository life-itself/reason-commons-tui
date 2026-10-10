"""Executable definitions for how the live question is presented (S03, S04, S17, S93, S121).

Each commons is built through the application use cases with a counting fixture consultant, then opened in
the real workspace, which is read the way a person reads it: what is on screen, in which control.
"""

from behave import given, then, when

from reason_commons.bootstrap import create_case, open_case
from tests.acceptance.workspace import Workspace, ask
from tests.support import ScriptedConsultant

GOAL = {"operation": "record_goal", "temporary_id": "goal", "data": {
    "statement": "90% of orders delivered on time", "scope": "Forge workshop orders", "horizon": "October 30",
    "measure": "orders delivered on time / orders due", "baseline": "71% in September",
    "protections": ["Overtime at most 20 hours per week"]}}
TOC_LESSON = ("Theory of Constraints", "Current Reality Tree", "Evaporating Cloud", "Thinking Process",
              "undesirable effect", "injection")


def asking(decision, prompt, rationale, purpose=None, goal=None, updates=()):
    """A consultant reply asking ``prompt``; ``purpose`` replaces the fixture's coded purpose."""
    build = ask(decision, prompt, rationale, goal=goal, updates=updates)

    def reply(request):
        value = build(request)
        if purpose:
            value["intervention"]["purpose"] = purpose
        return value
    return reply


def case_with(context, replies, acceptance="automatic", size=(120, 40)):
    """A commons built from (words, reply, declarations) and opened in the workspace."""
    create_case(context.path, "Forge", acceptance=acceptance, actor="Sam").close()
    builder = ScriptedConsultant([reply for _, reply, _ in replies])
    for words, _, declarations in replies:
        with open_case(context.path, consultant=builder) as app:
            target = app.workspace()["target"]
            result = app.submit(words, "Sam", target["base_revision"], target["response_target"],
                                declarations=declarations or {})
            assert result["status"] == "saved", result
    context.consultant = ScriptedConsultant()
    context.consultant.calls.extend(builder.calls)
    context.calls_before = len(context.consultant.calls)
    context.workspace = Workspace(context.path, context.consultant, size=size)
    context.workspaces.append(context.workspace)


def screen(context):
    return context.workspace.screen_text()


def content(context):
    return context.workspace.read(lambda app: app.query_one("#content").source)


def canvas(context):
    return context.workspace.read(lambda app: str(app.query_one("#canvas").render())
                                  if not app.query_one("#canvas").has_class("hidden") else "")


# Background of feature 01.

@given("a writable commons store")
def writable_store(context):
    assert context.path.parent.exists() and not context.path.exists()


@given("an available consultant adapter")
def available_consultant(context):
    context.consultant = ScriptedConsultant()


# S03 Show one recommended move and keep other paths available.

@given("a bounded test proposal whose observation criterion is unknown")
def test_without_criterion(context):
    test = {"operation": "record_test", "temporary_id": "test", "data": {
        "statement": "Freeze each day's plan by 9:00 for two weeks", "goal_ref": "G1@1", "scope": "Payments orders",
        "forecast": [{"measure": None, "expected": "fewer late orders", "scope": "Payments orders",
                      "denominator": None}]}}
    case_with(context, [
        ("90% on time by October 30, without more than 20 hours of overtime a week",
         asking("Define the change", "What will you change?", "A change comes before a forecast.", updates=[GOAL]),
         None),
        ("Freeze the plan by 9:00 for two weeks on Payments",
         asking("Choose the observation", "What will you count to see whether the frozen plan worked, and out of "
                "how many orders?", "Without an observation criterion the forecast cannot be checked.",
                updates=[test]), None)], acceptance="review")


@when("its current question is rendered")
@when("the current question is rendered")
def current_question_rendered(context):
    context.workspace.settle()


@then("exactly one primary prompt is visually distinguished from its decision context")
def one_prompt(context):
    source = content(context)
    headings = [line for line in source.splitlines() if line.startswith("## ")]
    assert headings == ["## Choose the observation"], headings
    assert source.count("What will you count") == 1 and screen(context).count("What will you count") == 1


@then("the prompt asks the operator to supply the observation criterion")
def asks_for_criterion(context):
    assert "What will you count" in screen(context)
    assert "Measure not stated yet" in screen(context)  # the waiting test's criterion is shown as unknown


@then('alternatives are available through visible "Other moves" controls')
def other_moves_visible(context):
    assert "Other moves" in screen(context)
    assert context.workspace.read(lambda app: app.query_one("#moves").display and not app.query_one("#moves").disabled)


@then("the foreground does not include an unsolicited TOC lesson")
def no_lesson(context):
    shown = content(context) + canvas(context)
    assert not [term for term in TOC_LESSON if term.lower() in shown.lower()], shown


# S04 Keep the information that changes the answer beside the question.

@given("the current question concerns a pilot that may increase overtime")
def overtime_pilot(context):
    context.pilot = {"operation": "record_test", "temporary_id": "test", "data": {
        "statement": "Keep two urgent slots open each day", "goal_ref": "G1@1", "scope": "Payments orders",
        "baseline": "about 18 hours of overtime a week (Sam's estimate)",
        "forecast": [{"measure": "orders delivered on time / orders due", "expected": "80%",
                      "scope": "Payments orders", "denominator": "orders due", "period": "October 5-16"}]}}


@given('the commons protects "{protection}"')
def protects(context, protection):
    goal = {**GOAL, "data": {**GOAL["data"], "protections": [protection]}}
    case_with(context, [
        ("90% on time by October 30", asking("Pick a change", "What will you try?", "Try one change.",
                                             updates=[goal]), None),
        ("Keep two urgent slots open on Payments, October 5-16",
         asking("Check the safeguard", "Could the urgent slots push overtime above the limit, and how would you "
                "know?", "The safeguard is checked before any gain is claimed.", updates=[context.pilot]), None)])
    records = context.workspace.case(lambda case: case.inspect()["case"]["records"])
    assert any(r["ref"] == "P1@1" for r in records)  # the question builds on the pilot


@when("the pilot workspace is rendered")
def pilot_rendered(context):
    context.workspace.settle()


@then("the consequential goal and protected condition appear beside the question")
def goal_beside(context):
    band = context.workspace.read(lambda app: app.query_one("#pinned").display)
    assert band and "Goal 90% of orders delivered on time Protect Overtime at most 20 hours per week" in screen(context)
    assert "Could the urgent slots push overtime" in screen(context)


@then("compact status shows save status, the focused control is framed, and Commons context gives the revision")
def compact_status(context):
    assert "Forge Sam · Saved" in screen(context)
    assert context.workspace.focused() == "editor"  # the frame marks the focused pane
    context.workspace.read(lambda app: app.show_view("context"))
    context.workspace.settle()
    revision = context.workspace.case(lambda case: case.inspect()["case"]["revision"])
    assert f"saved at revision {revision}" in screen(context)
    assert len(context.consultant.calls) == context.calls_before
    context.workspace.read(lambda app: app.show_view("next"))
    context.workspace.settle()


@then("an estimate is not relabeled as a measurement")
def estimate_kept(context):
    shown = screen(context)
    assert "Sam's estimate" in shown and "measured" not in shown.lower() and "OBSERVED" not in shown


@then("the pilot workspace shows the relevant baseline and period")
def baseline_and_period(context):
    shown = screen(context)
    assert "Baseline about 18 hours of overtime a week" in shown and "Period October 5-16" in shown


# S17 Show no diagram for a question it would not clarify.

@given("the next useful move is to name an experiment owner")
def owner_question(context):
    claims = [{"operation": "record_claim", "temporary_id": "temp_e", "data": {
                  "tree": "current_reality", "role": "undesirable_effect", "statement": "Orders ship late"}},
              {"operation": "record_claim", "temporary_id": "temp_c", "data": {
                  "tree": "current_reality", "role": "root_cause", "statement": "Priorities change daily"}},
              {"operation": "record_link", "temporary_id": "temp_l", "data": {
                  "tree": "current_reality", "relation": "causes", "from_ref": "temp_c", "to_ref": "temp_e"}}]
    test = {"operation": "record_test", "temporary_id": "test", "data": {
        "statement": "Freeze each day's plan by 9:00", "goal_ref": "G1@1", "scope": "Payments orders",
        "forecast": [{"measure": "orders delivered on time / orders due", "expected": "80%",
                      "scope": "Payments orders", "denominator": "orders due"}]}}
    case_with(context, [
        ("90% on time by October 30", asking("Name a cause", "What makes orders late?", "Causes point to "
                                             "changes.", updates=[GOAL]), None),
        ("Priorities change daily, so orders ship late", asking("Pick a change", "What will you try?",
                                                               "Try one change.", updates=claims), None),
        ("Freeze the plan by 9:00 on Payments", asking("Name the owner", "Who will run this trial, and can they "
                                                      "stop it if it hurts?", "A trial needs someone who can "
                                                      "carry it out.", updates=[test]), None)])


@when("the question is rendered")
def question_rendered(context):
    context.workspace.settle()


@then("it asks for the owner without a decorative causal diagram")
def no_diagram(context):
    assert "Who will run this trial" in screen(context)
    drawn = canvas(context)
    assert "Priorities change daily" not in drawn and "because" not in drawn and "●" not in drawn, drawn


# S93 Show the decision and goal served by the live question.

@given("a stored intervention with purpose, decision, and goal version G1 version 1")
def stored_intervention(context):
    provisional = {"operation": "record_goal", "temporary_id": "goal", "data": {
        "statement": "Fewer orders ship late", "protections": ["Overtime at most 20 hours per week"]}}
    case_with(context, [
        ("Orders keep shipping late", asking(
            "Inspect the baseline", "How many orders ship on time today, and how do you know?",
            "Knowing today's rate lets a later result be compared with G1@1, the goal as now worded.",
            purpose="Make a later result comparable with where you start", goal="goal", updates=[provisional]),
         None)])


@then("the decision purpose is readable beside its one primary prompt")
def purpose_readable(context):
    source = content(context)
    assert "## Inspect the baseline" in source and "Make a later result comparable" in source
    assert source.index("Make a later result comparable") < source.index("How many orders ship on time")


@then("the rationale links the task to that exact goal formulation")
def rationale_goal(context):
    context.workspace.tab_to("explain")
    context.workspace.press("enter")
    shown = screen(context)
    assert "Knowing today's rate lets a later result be compared" in shown
    assert "Fewer orders ship late" in content(context)  # the exact formulation the question serves
    assert len(context.consultant.calls) == context.calls_before
    context.workspace.press("escape")


@then("a provisional goal remains labeled provisional")
def provisional_label(context):
    assert "Goal provisional · Fewer orders ship late" in screen(context)


# S121 Compare the original pilot forecast with outcomes inside the workspace.

@given("an original pilot delivery forecast of 80 percent and acknowledgement bound of 95 percent")
def pilot_forecast(context):
    context.replies = [
        ("90% on time by October 30", asking("Pick a change", "What will you try?", "Try one change.",
                                             updates=[GOAL]), None),
        ("Freeze the plan on Payments, October 5-16; Maya runs it", asking(
            "Observe", "What happened?", "Results are compared with the forecast written first.", updates=[
                {"operation": "record_test", "temporary_id": "test", "data": {
                    "statement": "Freeze each day's plan by 9:00 with two urgent slots", "goal_ref": "G1@1",
                    "scope": "Payments orders, October 5-16",
                    "forecast": [{"measure": "orders delivered on time", "expected": "80%",
                                  "scope": "Payments orders", "denominator": "orders due",
                                  "period": "October 5-16"},
                                 {"measure": "urgent requests acknowledged within four hours",
                                  "expected": "at least 95%", "bound": "at least 95%",
                                  "scope": "urgent Payments requests", "denominator": "urgent requests",
                                  "period": "October 5-16"}]}},
                {"operation": "record_action", "temporary_id": "temp_a", "data": {
                    "statement": "Maya freezes the plan at 9:00 each day", "test_ref": "test", "owner": "Maya",
                    "authority": "Declared by Maya", "execution": "completed",
                    "expected_state_attainment": "unknown"}}]), {"ownership": ["Maya"]})]


@given("reported delivery is 80 percent and acknowledgement is 90 percent")
def reported_results(context):
    observations = [{"operation": "record_observation", "temporary_id": f"temp_o{i}", "data": {
        "test_ref": "P1@1", "measure": measure, "value": value, "scope": scope, "denominator": denominator,
        "period": "October 5-16", "basis": "participant_report"}} for i, (measure, value, scope, denominator) in
        enumerate([("orders delivered on time", "40 of 50 (80%)", "Payments orders", "orders due"),
                   ("urgent requests acknowledged within four hours", "18 of 20 (90%)", "urgent Payments requests",
                    "urgent requests")])]
    case_with(context, context.replies + [("40 of 50 on time; 18 of 20 urgent requests acknowledged in time",
                                           asking("Review the pilot", "What do you make of this result?",
                                                  "The forecast was written first.", updates=observations), None)],
              size=getattr(context, "review_size", (90, 70)))


@when("the review screen is rendered")
def review_rendered(context):
    context.workspace.read(lambda app: app.show_view("tests"))
    context.workspace.settle()


@then("original forecast and actual result are aligned by measure with scope and denominators")
def aligned(context):
    shown = screen(context)
    for words in ("ORIGINAL FORECAST", "REPORTED RESULT", "orders delivered on time", "80%", "40 of 50 (80%)",
                  "scope: Payments orders", "denominator: orders due", "18 of 20 (90%)",
                  "denominator: urgent requests"):
        assert words in shown, (words, shown)


@then("the acknowledgement breach remains visible despite delivery success")
def breach_visible(context):
    breaches = context.workspace.read(lambda app: app.workspace_value["breaches"])
    assert [(b["measure"], b["value"], b["bound"]) for b in breaches] == [
        ("urgent requests acknowledged within four hours", "18 of 20 (90%)", "at least 95%")]
    shown = screen(context)
    assert "BREACH" in shown and "at least 95%" in shown


@then("action execution, observed effects and the 90 percent system goal are distinct")
def distinct(context):
    shown = screen(context)
    assert "Action" in shown and "done as reported" in shown
    assert "System goal" in shown and "90% of orders delivered on time" in shown
    assert "judged by its own measure, not by this pilot" in shown
