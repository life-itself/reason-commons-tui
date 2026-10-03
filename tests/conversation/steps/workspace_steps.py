from behave import given, when, then

from reason_commons.bootstrap import open_case
from examples.p0_slice import AuthoredConsultant
from tests.support import bounded_case, submit


def save_question(context):
    assert submit(context.app, "Original participant input")["status"] == "saved"
    context.displayed = context.app.workspace()
    context.before = context.app.inspect()
    context.calls_before = len(context.consultant.calls)


@given("a new case")
def new(context):
    pass


@given("a saved question")
def saved(context):
    save_question(context)


@given("a question that another contribution has advanced")
def advanced(context):
    save_question(context)
    assert submit(context.app, "Another participant contribution")["status"] == "saved"
    context.calls_before = len(context.consultant.calls)


@given("a saved goal and prospective test")
def goal_test(context):
    context.consultant.responses.append(bounded_case)
    save_question(context)


@given("a completed pilot with recorded observations and a safeguard review")
def reviewed(context):
    context.consultant.default = AuthoredConsultant().propose
    for text, declarations in [("Pilot", None), ("Sam owns and completed work", {"ownership": ["Sam"]}),
                               ("Measured observations", None), ("Pause for safeguard breach", None)]:
        assert submit(context.app, text, declarations=declarations)["status"] == "saved"


@when("I open the next workspace")
def open_next(context):
    context.workspace = context.app.workspace()


@when("David replies with literal multiline text to the displayed question")
@when("David replies to the previously displayed question")
def reply(context):
    context.literal = "5\n:options\nMy exact reply.\n"
    context.result = context.app.submit(context.literal, "David", **context.displayed["target"])
    context.workspace = context.app.workspace()


@when("I reopen the case and inspect explanation, sources and history")
def reopen(context):
    context.app.close()
    context.app = open_case(context.path, writable=False)
    context.workspace = context.app.workspace(view="explain")
    context.sources = context.app.workspace(view="sources")
    context.history = context.app.workspace(view="history")


@when("David explicitly asks for direct advice with literal text")
def advice(context):
    context.literal = "Please advise on this question."
    context.result = context.app.submit(context.literal, "David", intent="direct_advice", **context.displayed["target"])


@when("I open the tests workspace")
def tests(context):
    context.workspace = context.app.workspace(view="tests")


@when("I inspect the first published revision")
def historical(context):
    context.workspace = context.app.workspace(view="tests", revision=1)


@when("I open the reasoning workspace")
def reasoning(context):
    context.workspace = context.app.workspace(view="reasoning")


@then("the formal goal is unknown and no question has been invented")
def empty(context):
    assert context.workspace["goals"] == [] and context.workspace["question"] is None
    assert any(u["field"] == "goal" for u in context.workspace["uncertainty"])


@then("no consultation has occurred")
def no_consult(context):
    assert context.consultant.calls == []


@then("the reply is attributed and saved against that exact question")
def retained(context):
    assert context.result["status"] == "saved"
    value = context.app.sources()["sources"][context.result["request_id"]]
    assert value["text"] == context.literal and value["speaker"] == "David"
    assert {k: value[k] for k in context.displayed["target"]} == context.displayed["target"]


@then("the workspace presents the newly saved question")
def new_question(context):
    assert context.workspace["revision"] == context.result["revision"] == 2
    assert context.workspace["question"]["ref"] != context.displayed["question"]["ref"]
    assert context.workspace["target"]["response_target"] == context.workspace["question"]["ref"]


@then("exactly one additional consultation has occurred")
def one(context):
    assert len(context.consultant.calls) == context.calls_before + 1


@then("the stored rationale and original attributed text are available")
def rationale(context):
    assert context.workspace["question"]["data"]["rationale"] == "Keep the next move bounded."
    source = context.sources["sources"]["in000001"]
    assert source["text"] == "Original participant input" and source["speaker"] == "Sam"
    assert [s["revision"] for s in context.history["history"]] == [0, 1]


@then("the saved revision and consultant count are unchanged")
def unchanged(context):
    assert context.app.inspect() == context.before
    assert len(context.consultant.calls) == context.calls_before


@then("the application reports stale and does not consult")
def stale(context):
    assert context.result["status"] == "stale"
    assert len(context.consultant.calls) == context.calls_before


@then("the saved input has the direct advice intent and the displayed anchor")
def intent(context):
    retained(context)
    assert context.app.sources()["sources"][context.result["request_id"]]["intent"] == "direct_advice"


@then("the original forecast and actual results remain distinct")
def original(context):
    comparison = context.workspace["comparisons"][0]
    assert [f["expected"] for f in comparison["test"]["data"]["forecast"]] == ["80%", "95%"]
    assert [o["data"]["value"] for o in comparison["observations"]] == ["80%", "90%"]


@then("the breached safeguard and work execution remain visible")
def safeguard(context):
    assert context.workspace["comparisons"][0]["reviews"][0]["data"]["assessment"] == "Acknowledgement below original 95% bound"
    action = next(r for r in context.app.workspace(view="actions")["records"] if r["kind"] == "action")
    assert action["data"]["execution"] == "completed" and action["data"]["expected_state_attainment"] == "unknown"
    assert context.workspace["goals"][0]["data"]["protections"] == ["Urgent acknowledgement at least 95%"]


@then("later observations and reviews are absent and only local moves are available")
def no_future(context):
    assert context.workspace["historical"]
    comparison = context.workspace["comparisons"][0]
    assert comparison["observations"] == [] and comparison["reviews"] == []
    assert all(a["route"] == "local" for a in context.workspace["available_actions"])


@then("its diagram links the test to its goal with the recorded meaning")
def links(context):
    assert context.workspace["diagram"]["links"] == [{"from": "P1@1", "to": "G1@1", "field": "goal_ref",
                                                        "label": "tests progress toward"}]


@then("no causal edge has been inferred from participant prose")
def no_causality(context):
    assert all(edge["field"] in {"goal_ref", "test_ref", "observation_refs", "required_context_refs"}
               for edge in context.workspace["diagram"]["links"])
    assert {r["ref"] for r in context.workspace["diagram"]["nodes"]} == {"P1@1", "G1@1"}
