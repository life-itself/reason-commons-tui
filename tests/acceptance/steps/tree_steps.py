"""Executable definitions for the trees-in-conversation scenarios (S128-S134).

Setup and behavior go through application use cases and the LTP adapter's
public functions; no step writes commons files directly. What the consultant
proposes waits until the operator accepts it, so steps accept explicitly.
"""

from behave import given, when, then
import yaml

from reason_commons.adapters.ltp_trees import export_trees, import_trees
from reason_commons.adapters.trees import plain, trees_lines
from reason_commons.bootstrap import create_case, open_case
from tests.support import ScriptedConsultant, accept_all, automatic, fixture_app, proposal, retain, submit
from tests.test_ltp_trees import DOCUMENT


def new_app(context):
    context.provider = ScriptedConsultant()
    context.app, context.faults = fixture_app(context.path, context.provider)
    context.apps.append(context.app)
    if getattr(context, "automatic", False):
        automatic(context.app)


@given("a commons set to accept proposals automatically")
def automatic_case(context):
    context.automatic = True


def recording(*updates):
    """A consultant reply that records the given updates, citing the input it answers."""
    def build(request):
        value = proposal(request)
        rid = request["input"]["request_id"]
        value["proposed_updates"] += [{**u, "source_refs": [rid]} for u in updates]
        return value
    return build


def exactly(*updates):
    """A consultant reply proposing exactly these updates, citing the input it answers."""
    def build(request):
        value = proposal(request)
        rid = request["input"]["request_id"]
        value["proposed_updates"] = [{**u, "source_refs": [rid]} for u in updates]
        return value
    return build


def claim(alias, statement, tree="current_reality", role="undesirable_effect", **extra):
    return {"operation": "record_claim", "temporary_id": alias,
            "data": {"tree": tree, "role": role, "statement": statement, **extra}}


def link(alias, source, target, tree="current_reality", relation="causes"):
    return {"operation": "record_link", "temporary_id": alias,
            "data": {"tree": tree, "relation": relation, "from_ref": source, "to_ref": target}}


def tree(context, name):
    return next(t for t in context.app.workspace(view="trees")["trees"] if t["tree"] == name)


@given('a commons whose goal is "{goal}"')
def case_with_goal(context, goal):
    new_app(context)
    context.provider.responses.append(recording({"operation": "record_goal", "temporary_id": "goal",
                                                 "data": {"statement": goal, "protections": []}}))
    assert submit(context.app, goal)["status"] == "saved"
    accept_all(context.app)


@when('the operator says "{text}"')
def operator_says(context, text):
    context.said = text


@when("the consultant proposes a symptom, a cause and a causes link citing that input")
def propose_cause(context):
    context.provider.responses.append(exactly(
        {**claim("temp_ude", "Newcomers do not know the next step"), "confidence": 0.8},
        {**claim("temp_cause", "We never offer a next step", role="root_cause", basis="participant_report"),
         "confidence": 0.6},
        link("temp_link", "temp_cause", "temp_ude")))
    context.result = submit(context.app, context.said)
    assert context.result["status"] == "saved"


@when("the operator accepts them")
def accept_them(context):
    accept_all(context.app)


@then("the Current Reality Tree holds both statements and the link")
def crt_holds(context):
    crt = tree(context, "current_reality")
    assert [c["statement"] for c in crt["claims"]] == ["Newcomers do not know the next step", "We never offer a next step"]
    assert [(l["relation"], l["from"], l["to"]) for l in crt["links"]] == [("causes", "C2@1", "C1@1")]


@then("the literal input remains the source of all three")
def literal_source(context):
    rid = context.result["request_id"]
    assert context.app.sources()["sources"][rid]["text"] == context.said
    records = [r for r in context.app.inspect()["case"]["records"] if r["kind"] in {"claim", "link"}]
    assert len(records) == 3 and all(r["source_refs"] == [rid] for r in records)


@then('the Trees view draws the symptom above its cause, labelled "{label}"')
def drawn(context, label):
    drawing = plain(trees_lines(context.app.workspace(view="trees")["trees"], 80, only="current_reality"))
    # The branch word leads into the cause's statement, and its role follows it.
    assert drawing.index("Newcomers do not know") < drawing.index(f"└─ {label}: ") < \
        drawing.index("We never offer a next step") < drawing.index("· root cause")


INVALID = {
    "a goal role in the Current Reality Tree": [claim("temp_a", "A goal", role="goal")],
    "a statement in the goal role, beside the commons goal": [claim("temp_a", "A second goal", tree="goal", role="goal")],
    "a link whose claims both belong to other trees": [
        claim("temp_a", "Effect"), claim("temp_b", "Need", tree="conflict", role="cloud_requirement"),
        link("temp_l", "temp_a", "temp_b", tree="future_reality")],
    "a link from a claim to itself": [claim("temp_a", "Effect"), link("temp_l", "temp_a", "temp_a")],
    "a link to a claim proposed after the link": [
        claim("temp_a", "Effect"), link("temp_l", "temp_b", "temp_a"), claim("temp_b", "Cause", role="root_cause")],
    "a link with a relation outside the LTP vocabulary": [
        claim("temp_a", "Effect"), claim("temp_b", "Cause", role="root_cause"),
        link("temp_l", "temp_b", "temp_a", relation="so_that")],
}


@when("the consultant proposes {record} with an ordinary note")
def propose_invalid(context, record):
    context.request_id = retain(context.app)["request_id"]
    context.before = context.app.inspect()
    context.provider.responses.append(recording(*INVALID[record]))
    context.result = context.app.consult(context.request_id)


@given("a Current Reality Tree with a symptom, a cause and a causes link")
def crt(context):
    case_with_goal(context, "A clear next step after open evenings")
    operator_says(context, "Newcomers do not know the next step, because we never offer one")
    propose_cause(context)
    accept_all(context.app)


@when("the operator asks to word the cause more precisely and accepts the consultant's new wording")
def reword(context):
    context.provider.responses.append(recording(
        claim("temp_new", "Open evenings end without any invitation to practise", role="root_cause", replaces="C2@1")))
    assert submit(context.app, "Say the cause more precisely")["status"] == "saved"
    accept_all(context.app)


@then("the tree shows the new wording, still linked to the symptom")
def reworded(context):
    crt = tree(context, "current_reality")
    cause = next(c for c in crt["claims"] if c["role"] == "root_cause")
    assert cause["statement"] == "Open evenings end without any invitation to practise"
    assert cause["earlier_wording"] == ["We never offer a next step"]
    assert [(l["from"], l["to"]) for l in crt["links"]] == [(cause["ref"], "C1@1")]
    assert cause["ref"] == "C2@2"  # a new version of the same statement


@then("the link is flagged for review because it was stated for the earlier wording")
def link_flagged(context):
    reviews = [e for e in context.app.workspace(view="backlog")["backlog"] if e["entry"] == "review"]
    assert [(e["ref"], [(f["cites"], f["change"], f["now"]) for f in e["flags"]]) for e in reviews] == [
        ("L1@1", [("C2@1", "new_version", "C2@2")])]


@then("the earlier wording stays in the commons history")
def earlier_kept(context):
    records = {r["ref"]: r for r in context.app.inspect()["case"]["records"]}
    assert records["C2@1"]["data"]["statement"] == "We never offer a next step"


@when("the operator withdraws the cause and accepts the consultant's withdrawal with its reason")
def withdraw(context):
    context.provider.responses.append(recording({"operation": "record_retraction", "temporary_id": "temp_x",
                                                 "data": {"target_ref": "C2@2", "reason": "Not what we think now"}}))
    assert submit(context.app, "Drop that cause")["status"] == "saved"
    accept_all(context.app)


@then("the tree no longer shows the cause or its link")
def withdrawn(context):
    crt = tree(context, "current_reality")
    assert [c["ref"] for c in crt["claims"]] == ["C1@1"] and crt["links"] == []


@then("a later proposal linking the withdrawn cause is rejected before commit")
def relink_rejected(context):
    before = context.app.inspect()
    context.provider.responses.append(recording(link("temp_l", "C2@2", "C1@1")))
    assert submit(context.app, "Link it again")["status"] == "rejected"
    assert context.app.inspect()["case"] == before["case"]


@given('a Transition Tree action "{statement}"')
def transition_action(context, statement):
    case_with_goal(context, "A clear next step after open evenings")
    context.provider.responses.append(recording(claim("temp_act", statement, tree="transition",
                                                      role="transition_action")))
    assert submit(context.app, statement)["status"] == "saved"
    context.action = statement


@when("the operator records a test with a forecast that carries out that action")
def test_for_action(context):
    context.provider.responses.append(recording({"operation": "record_test", "temporary_id": "test", "data": {
        "statement": "End each open evening with one clear invitation", "goal_ref": "G1@1", "scope": None,
        "forecast": [{"measure": "first practice within 3 weeks", "expected": "6 of 30", "scope": None,
                      "denominator": "newcomers"}], "claim_ref": "C1@1"}}))
    assert submit(context.app, "Invite at the end; I expect 6 of 30")["status"] == "saved"
    context.forecast = next(r for r in context.app.inspect()["case"]["records"] if r["kind"] == "test")["data"]["forecast"]


@when("reports an observation for the test")
def observe(context):
    context.provider.responses.append(recording({"operation": "record_observation", "temporary_id": "temp_obs",
                                                 "data": {"test_ref": "P1@1", "measure": "first practice within 3 weeks",
                                                          "value": "9 of 31", "basis": "participant_report"}}))
    assert submit(context.app, "9 of 31 came")["status"] == "saved"


@then("the Trees view shows the test's original forecast and reported result under the action")
def test_under_action(context):
    drawing = plain(trees_lines(context.app.workspace(view="trees")["trees"], 100, only="transition"))
    assert drawing.index(context.action) < drawing.index("◆ Test: End each open evening with one clear invitation\n"
                                                         "    original forecast, saved before any result: 6 of 30\n"
                                                         "    result: 9 of 31")


@then("the test's original forecast is unchanged")
def forecast_unchanged(context):
    test = next(r for r in context.app.inspect()["case"]["records"] if r["kind"] == "test")
    assert test["data"]["forecast"] == context.forecast


@given("a commons in the middle of the goal-action-review loop")
def mid_loop(context):
    from reason_commons.adapters.guided import GuidedConsultant
    create_case(context.path, "Delivery").close()
    with open_case(context.path, consultant=GuidedConsultant()) as app:
        for answer in ("Deliver committed work within two weeks", "Days from commitment to delivery", "Quality"):
            assert app.submit(answer, "Sam", **app.workspace()["target"])["status"] == "saved"
        context.question = app.workspace()["question"]["data"]


@given("an LTP 1.0 file with six statements, two single-premise links, one joint-premise link and one assessment")
def ltp_file(context):
    context.file = context.path.parent / "delivery.ltp.yaml"
    context.file.write_text(yaml.safe_dump(DOCUMENT))


@when("the operator brings in the file")
def bring_in(context):
    context.summary = import_trees(context.path, context.file, "Sam")


@then("the file is retained as a source and every imported statement and link cites it")
def cites_file(context):
    with open_case(context.path, writable=False) as app:
        sources, records = app.sources()["sources"], app.inspect()["case"]["records"]
    file_ref = next(k for k, v in sources.items() if v.get("name") == "delivery.ltp.yaml")
    # Six statements (the file's goal is proposed as the commons' goal) and two links.
    imported = [r for r in records if r["kind"] in {"claim", "link"} or file_ref in r["source_refs"]
                and r["kind"] == "goal"]
    assert len(imported) == 6 + 2 and all(r["source_refs"] == [file_ref] for r in imported)


@then("everything the file brings in waits in the backlog until the operator accepts it")
def file_waits(context):
    with open_case(context.path, writable=False) as app:
        workspace = app.workspace(view="backlog")
    waiting = {e["ref"] for e in workspace["backlog"] if e["entry"] == "proposal"}
    assert set(context.summary["proposed"]) <= waiting and not context.summary["accepted"]
    assert all(not t["claims"] for t in workspace["trees"] if t["tree"] != "goal")


@then("the joint-premise link and the assessment are kept as labelled notes")
def kept_as_notes(context):
    with open_case(context.path, writable=False) as app:
        notes = [r["data"]["text"] for r in app.inspect()["case"]["records"] if r["kind"] == "note"
                 and r["data"]["text"].startswith("From delivery.ltp.yaml")]
    assert len(notes) == 2 and any("several premises" in n for n in notes) and any("assessment" in n for n in notes)


@then("the current question carries on from the same step")
def same_step(context):
    with open_case(context.path, writable=False) as app:
        question = app.workspace()["question"]["data"]
    assert question["purpose"] == context.question["purpose"]
    assert question["primary_prompt"].endswith(context.question["primary_prompt"])


@then("the consultant is not called")
def no_consultant(context):
    with open_case(context.path, writable=False) as app:
        case = app.inspect()["case"]
    assert case["adapter_versions"][case["applied_requests"][-1]].startswith("ltp-tree-import/1/")


@given("a commons with imported trees")
def imported_case(context):
    create_case(context.path, "Delivery").close()
    ltp_file(context)
    bring_in(context)
    with open_case(context.path) as app:
        accept_all(app)


@when("the operator exports the trees to a new LTP file and brings that file into a new commons")
def round_trip(context):
    with open_case(context.path, writable=False) as app:
        context.first = app.workspace(view="trees")
    context.exported = context.path.parent / "out.ltp.yaml"
    export_trees(context.first, context.exported)
    context.again = context.path.parent / "again"
    create_case(context.again, "Again").close()
    import_trees(context.again, context.exported, "Sam")


@when("the operator accepts everything the file brings in")
def accept_import(context):
    with open_case(context.again) as app:
        accept_all(app)
        context.second = app.workspace(view="trees")


@then("both commons show the same statements, roles, links and assumptions")
def same_trees(context):
    shape = lambda w: [(t["tree"], [(c["role"], c["statement"]) for c in t["claims"]],
                        [(l["relation"], l["assumption"]) for l in t["links"]]) for t in w["trees"]]
    assert shape(context.first) == shape(context.second)


@then("exporting to an existing file is refused")
def refuse_overwrite(context):
    before = context.exported.read_bytes()
    try:
        export_trees(context.first, context.exported)
    except ValueError:
        assert context.exported.read_bytes() == before
    else:
        raise AssertionError("Export overwrote an existing file")


@when("the operator opens the Trees view and then returns to the current question")
def browse_trees(context):
    context.provider = ScriptedConsultant()
    context.app = open_case(context.path, consultant=context.provider)
    context.apps.append(context.app)
    context.revision = context.app.inspect()["case"]["revision"]
    assert context.app.workspace(view="trees")["trees"][0]["claims"]
    context.app.workspace(view="next")


@then("no consultant call and no revision occurs")
def nothing_happens(context):
    assert context.provider.calls == [] and context.app.inspect()["case"]["revision"] == context.revision
