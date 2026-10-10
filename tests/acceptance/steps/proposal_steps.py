"""Executable definitions for deciding what enters the model (S135-S150).

Every step drives application use cases: the fixture consultant proposes, and the
operator's decisions go through accept, reject, undo, still_holds and
set_acceptance. Nothing reaches into the store or the aggregate.
"""

from behave import given, when, then

from reason_commons.adapters.trees import plain, trees_lines
from tests.acceptance.steps.tree_steps import (case_with_goal, claim, crt, exactly, link, operator_says,
                                               propose_cause, tree)
from tests.support import accept_all, cursor, proposal, retain, submit

SPEAKER = "Sam"


def revision(context):
    return context.app.inspect()["case"]["revision"]


def backlog(context):
    return context.app.workspace(view="backlog")["backlog"]


def waiting(context):
    return [e["ref"] for e in backlog(context) if e["entry"] == "proposal"]


def reviews(context):
    return {e["ref"]: e["flags"] for e in backlog(context) if e["entry"] == "review"}


def decisions(context):
    return context.app.inspect()["case"]["decisions"]


def reply(context, *updates, text="An answer"):
    """One consultant reply proposing ``updates``; returns the refs it proposed."""
    context.provider.responses.append(exactly(*updates))
    result = submit(context.app, text)
    assert result["status"] == "saved", result
    return result["proposed"]


def decide(context, action, refs, **extra):
    context.decision = (action, refs)
    context.result = getattr(context.app, action)(refs, SPEAKER, revision(context), **extra)
    return context.result


# S135 Hold a reply's proposals in the backlog by default.

@then("the consultant's next question becomes the live question")
def live_question(context):
    workspace = context.app.workspace()
    assert workspace["question"]["source_refs"] == [context.result["request_id"]]
    assert workspace["target"]["response_target"] == workspace["question"]["ref"]


@then("the symptom, the cause and the link wait in the backlog, each citing the operator's words")
def three_wait(context):
    entries = [e for e in backlog(context) if e["entry"] == "proposal"]
    assert {e["ref"] for e in entries} == {"C1@1", "C2@1", "L1@1"}
    assert all(e["source_refs"] == [context.result["request_id"]] and e["words"] == [context.said] for e in entries)


@then("the Current Reality Tree is unchanged")
def crt_unchanged(context):
    current = tree(context, "current_reality")
    assert current["claims"] == [] and current["links"] == []


@then("a confidence the consultant gave is kept with each proposal without deciding anything")
def confidence_kept(context):
    entries = {e["ref"]: e for e in backlog(context)}
    assert entries["C1@1"]["confidence"] == 0.8 and entries["C2@1"]["confidence"] == 0.6
    membership = context.app.workspace()["membership"]
    assert membership["C1@1"] == membership["C2@1"] == "proposed"


# S136 Accept a reply's proposals together.

@given("the backlog holds a symptom, a cause and a causes link proposed from one input")
def three_proposed(context):
    case_with_goal(context, "A clear next step after open evenings")
    operator_says(context, "Newcomers do not know the next step, because we never offer one")
    propose_cause(context)
    assert context.app.checkpoint(cursor(context.app, draft="half a thought", selection=None))["status"] == "saved"
    context.before = context.app.inspect()
    context.calls = len(context.provider.calls)


@when("the operator accepts all three")
def accept_three(context):
    assert decide(context, "accept", ["C1@1", "C2@1", "L1@1"])["status"] == "saved"


@then("one new revision adds them to the Current Reality Tree without a consultant call")
def added_once(context):
    assert revision(context) == context.before["case"]["revision"] + 1
    assert len(context.provider.calls) == context.calls
    current = tree(context, "current_reality")
    assert [c["ref"] for c in current["claims"]] == ["C1@1", "C2@1"] and [l["ref"] for l in current["links"]] == ["L1@1"]


@then("the revision records who accepted them, when, and that they were accepted explicitly")
def recorded_acceptance(context):
    decision = decisions(context)[-1]
    assert decision["action"] == "accept" and decision["refs"] == ["C1@1", "C2@1", "L1@1"]
    assert decision["actor"] == SPEAKER and decision["mode"] == "explicit"
    assert decision["timestamp"] == context.app.inspect()["case"]["timestamp"]


@then("the cause keeps its basis, so an accepted hypothesis is still a hypothesis")
def basis_kept(context):
    proposed = next(r for r in context.before["case"]["records"] if r["ref"] == "C2@1")
    drawn = next(c for c in tree(context, "current_reality")["claims"] if c["ref"] == "C2@1")
    assert drawn["basis"] == proposed["data"]["basis"]


@then("the backlog is empty and the live question and draft are unchanged")
def nothing_else(context):
    after = context.app.inspect()
    assert backlog(context) == [] and after["case"]["current_intervention"] == context.before["case"]["current_intervention"]
    assert after["cursor"]["draft"] == context.before["cursor"]["draft"] == "half a thought"


# S137 Reject a proposal together with what needs it.

@when("the operator rejects the cause")
def reject_cause(context):
    context.before = context.app.inspect()
    decide(context, "reject", ["C2@1"])


@then("the operator is shown that the link, which needs the cause, is rejected with it")
def shown_rejection(context):
    assert context.result["status"] == "confirm" and context.result["refs"] == ["C2@1", "L1@1"]
    assert context.app.inspect() == context.before


@when("the operator confirms")
def confirm(context):
    action, refs = context.decision
    context.before_confirm = context.app.inspect()
    assert decide(context, action, refs, confirmed=True)["status"] == "saved", context.result


@then("the cause and the link leave the backlog and the symptom still waits")
def symptom_waits(context):
    assert waiting(context) == ["C1@1"]


@then("the commons history keeps both rejected proposals with the operator's decision")
def rejection_kept(context):
    refs = {r["ref"] for r in context.app.inspect()["case"]["records"]}
    assert {"C2@1", "L1@1"} <= refs
    decision = decisions(context)[-1]
    assert decision["action"] == "reject" and decision["refs"] == ["C2@1", "L1@1"] and decision["actor"] == SPEAKER


@then("neither can be accepted later")
def rejection_final(context):
    for ref in ("C2@1", "L1@1"):
        assert decide(context, "accept", [ref])["status"] == "rejected"


# S138 List the backlog in the order it is best decided.

@given("the backlog holds, from earlier replies, a Transition Tree action, a Current Reality cause, "
       "a causes link from that cause and a new version of the goal")
def mixed_backlog(context):
    case_with_goal(context, "A clear next step after open evenings")
    reply(context, claim("temp_ude", "Newcomers do not know the next step"))
    accept_all(context.app)
    reply(context, claim("temp_act", "Offer one clear invitation", tree="transition", role="transition_action"))
    reply(context, claim("temp_cause", "We never offer a next step", role="root_cause"),
          link("temp_link", "temp_cause", "C1@1"))
    reply(context, {"operation": "record_goal", "temporary_id": "goal", "data": {
        "statement": "Most newcomers reach a first practice", "protections": [], "replaces": "G1@1"}})


@when("the operator opens the backlog")
def open_backlog(context):
    context.entries = backlog(context)


@then("the new version of the goal comes first, marked to be decided first because the rest is judged against it")
def goal_first(context):
    first = context.entries[0]
    assert first["ref"] == "G1@2" and first["kind"] == "goal" and first["decide_first"]
    assert not any(e["decide_first"] for e in context.entries[1:])


@then("the cause comes before its link, which says it waits for the cause")
def cause_before_link(context):
    order = [e["ref"] for e in context.entries]
    assert order.index("C3@1") < order.index("L1@1")
    assert next(e for e in context.entries if e["ref"] == "L1@1")["waits_for"] == ["C3@1"]


@then("the Current Reality proposals come before the Transition Tree action")
def crt_before_tt(context):
    assert [e["ref"] for e in context.entries] == ["G1@2", "C3@1", "L1@1", "C2@1"]


@when("the operator accepts the link")
def accept_link(context):
    decide(context, "accept", ["L1@1"])


@then("the operator is shown that the cause is accepted with it")
def shown_prerequisite(context):
    assert context.result["status"] == "confirm" and context.result["refs"] == ["C3@1", "L1@1"]


@then("after confirming, both are in the Current Reality Tree while the new goal still waits")
def both_in(context):
    confirm(context)
    current = tree(context, "current_reality")
    assert "C3@1" in [c["ref"] for c in current["claims"]] and [l["ref"] for l in current["links"]] == ["L1@1"]
    assert "G1@2" in waiting(context)
    assert context.app.workspace(view="goal")["goals"][0]["ref"] == "G1@1"


# S139 Accept proposals automatically when the operator has chosen to.

@when("the consultant proposes a symptom, a cause and a causes link citing the operator's words")
def propose_with_setting(context):
    case_with_goal(context, "A clear next step after open evenings")
    context.before = context.app.inspect()
    operator_says(context, "Newcomers do not know the next step, because we never offer one")
    propose_cause(context)


@then("the revision that publishes the next question also adds all three to the Current Reality Tree")
def same_revision(context):
    case = context.app.inspect()["case"]
    assert case["revision"] == context.before["case"]["revision"] + 1 == context.result["revision"]
    current = tree(context, "current_reality")
    assert len(current["claims"]) == 2 and len(current["links"]) == 1 and backlog(context) == []


@then("it records that they were accepted automatically under the operator's setting")
def automatic_record(context):
    decision = decisions(context)[-1]
    assert decision["mode"] == "automatic" and decision["request_id"] == context.result["request_id"]
    assert decision["refs"] == ["C1@1", "C2@1", "L1@1"] and decision["actor"] == SPEAKER
    assert any(d["action"] == "acceptance" and d["value"] == "automatic" for d in decisions(context))


@then("the operator can undo that acceptance like an explicit one")
def undo_automatic(context):
    assert decide(context, "undo", ["C2@1"])["status"] == "confirm"
    confirm(context)
    current = tree(context, "current_reality")
    assert [c["ref"] for c in current["claims"]] == ["C1@1"] and current["links"] == []


# S140 Only the operator changes how proposals are accepted.

@given("a commons that holds proposals for review, with two proposals waiting")
def two_waiting(context):
    case_with_goal(context, "A clear next step after open evenings")
    reply(context, claim("temp_ude", "Newcomers do not know the next step"),
          claim("temp_cause", "We never offer a next step", role="root_cause"))
    assert waiting(context) == ["C1@1", "C2@1"] and context.app.workspace()["acceptance"] == "review"
    context.before = context.app.inspect()
    context.calls = len(context.provider.calls)


@when("the operator sets the commons to accept proposals automatically")
def set_automatic(context):
    context.result = context.app.set_acceptance("automatic", SPEAKER, revision(context))
    assert context.result["status"] == "saved"


@then("a revision records the operator's choice without a consultant call")
def setting_recorded(context):
    decision = decisions(context)[-1]
    assert decision["action"] == "acceptance" and decision["value"] == "automatic" and decision["actor"] == SPEAKER
    assert revision(context) == context.before["case"]["revision"] + 1 and len(context.provider.calls) == context.calls
    assert context.app.workspace()["acceptance"] == "automatic"


@then("the two proposals already waiting still wait")
def still_wait(context):
    assert waiting(context) == ["C1@1", "C2@1"]


@then("a consultant reply that tries to change the setting is rejected before commit")
def reply_cannot_set(context):
    for change in (lambda p: p["proposed_updates"].append(
                       {"operation": "record_acceptance", "data": {"value": "review"}, "source_refs": []}),
                   lambda p: p.update(acceptance="review")):
        before = context.app.inspect()
        def tampered(request, change=change):
            value = proposal(request)
            change(value)
            return value
        context.provider.responses.append(tampered)
        assert submit(context.app, "Please stop accepting automatically")["status"] == "rejected"
        assert context.app.inspect()["case"] == before["case"]


# S141 Undo an accepted change without rewriting history.

@given("the Current Reality Tree holds an accepted cause with its causes link and a later accepted symptom that cites neither")
def accepted_cause(context):
    crt(context)
    reply(context, claim("temp_other", "Organisers are tired"), text="Organisers are tired")
    accept_all(context.app)


@given("a waiting proposal links another statement to the cause")
def waiting_link(context):
    reply(context, claim("temp_effect", "Few come back"), link("temp_l", "C2@1", "temp_effect"))
    context.words = context.app.sources()["sources"]


@when("the operator undoes the acceptance of the cause")
def undo_cause(context):
    context.before = context.app.inspect()
    decide(context, "undo", ["C2@1"])


@then("the operator is shown that the link leaves the tree with it and the waiting proposal is closed")
def shown_undo(context):
    assert context.result["status"] == "confirm" and context.result["message"].startswith("Final")
    assert context.result["refs"] == ["C2@1", "L1@1"] and context.result["closes"] == ["L2@1"]
    assert context.app.inspect() == context.before


@then("a new revision removes the cause and its link from the tree and keeps the later symptom")
def undone(context):
    assert revision(context) == context.before["case"]["revision"] + 1
    current = tree(context, "current_reality")
    assert [c["ref"] for c in current["claims"]] == ["C1@1", "C3@1"] and current["links"] == []
    assert waiting(context) == ["C4@1"]


@then("the commons history keeps the operator's words, the proposals, their acceptance and the undo")
def history_kept(context):
    case = context.app.inspect()["case"]
    assert {"C2@1", "L1@1", "L2@1"} <= {r["ref"] for r in case["records"]}
    assert context.app.sources()["sources"] == context.words
    actions = [(d["action"], d["refs"]) for d in case["decisions"]]
    assert ("undo", ["C2@1", "L1@1"]) in actions
    assert any(action == "accept" and "C2@1" in refs for action, refs in actions)


@then("the undo is final: it cannot be undone and the cause does not return to the backlog")
def undo_final(context):
    assert decide(context, "undo", ["C2@1"], confirmed=True)["status"] == "rejected"
    assert decide(context, "accept", ["C2@1"])["status"] == "rejected"
    assert "C2@1" not in waiting(context)


# S142 and S143 Review flags and cascades.

def accepted(context, *updates):
    refs = reply(context, *updates)
    accept_all(context.app)
    return refs


def reword(context, old, statement, tree_name, role):
    accepted(context, claim("temp_new", statement, tree=tree_name, role=role, replaces=old))


@given("an accepted Conflict tree injection, a Future Reality link from that injection to a desired effect, "
       "and a test that carries out the injection")
def injection_with_dependents(context):
    case_with_goal(context, "A clear next step after open evenings")
    accepted(context, claim("temp_inj", "Invite at the end of each evening", tree="conflict", role="injection"),
             claim("temp_de", "Newcomers come to a first practice", tree="future_reality", role="desired_effect"),
             link("temp_lf", "temp_inj", "temp_de", tree="future_reality"),
             {"operation": "record_test", "temporary_id": "test", "data": {
                 "statement": "Invite at the end for a month", "goal_ref": "G1@1", "scope": None,
                 "forecast": [{"measure": "first practice", "expected": "6 of 30", "scope": None,
                               "denominator": "newcomers"}], "claim_ref": "temp_inj"}})
    context.before = context.app.inspect()


@when("the operator accepts a new wording of the injection")
def reword_injection(context):
    reword(context, "C1@1", "Invite everyone, warmly, at the end of each evening", "conflict", "injection")


@then("the link and the test are flagged for review, each naming the change that raised the flag")
def flagged(context):
    flags = reviews(context)
    assert set(flags) == {"L1@1", "P1@1"}
    assert all([(f["cites"], f["change"], f["by"]) for f in flags[ref]] == [("C1@1", "new_version", "C1@2")]
               for ref in flags)


@then("neither is changed, withdrawn or marked false")
def unchanged(context):
    records = {r["ref"]: r for r in context.app.inspect()["case"]["records"]}
    before = {r["ref"]: r for r in context.before["case"]["records"]}
    assert records["L1@1"] == before["L1@1"] and records["P1@1"] == before["P1@1"]
    assert [l["ref"] for l in tree(context, "future_reality")["links"]] == ["L1@1"]
    assert context.app.workspace()["membership"]["P1@1"] == "accepted"
    assert not any(r["kind"] == "retraction" for r in records.values())


@then("both flags wait in the backlog")
def both_flags(context):
    assert [e["entry"] for e in backlog(context)] == ["review", "review"]


@when("the operator marks the test as still holding")
def still_holds(context):
    context.result = context.app.still_holds("P1@1", SPEAKER, revision(context))
    assert context.result["status"] == "saved"


@then("the test's flag closes with the operator's decision recorded and the link's flag stays open")
def test_closed(context):
    assert set(reviews(context)) == {"L1@1"}
    decision = decisions(context)[-1]
    assert decision["action"] == "still_holds" and decision["refs"] == ["P1@1"]
    assert decision["about"] == [{"ref": "C1@1", "now": "C1@2"}] and decision["actor"] == SPEAKER


@given("an accepted Conflict tree requirement, an injection linked to it, and a Future Reality link from that "
       "injection to a desired effect")
def cloud_and_frt(context):
    case_with_goal(context, "A clear next step after open evenings")
    accepted(context, claim("temp_req", "Organisers need to keep evenings low-pressure", tree="conflict",
                            role="cloud_requirement"),
             claim("temp_inj", "Invite at the end of each evening", tree="conflict", role="injection"),
             link("temp_lc", "temp_inj", "temp_req", tree="conflict", relation="satisfies"),
             claim("temp_de", "Newcomers come to a first practice", tree="future_reality", role="desired_effect"),
             link("temp_lf", "temp_inj", "temp_de", tree="future_reality"))


@when("the operator accepts a new wording of the requirement")
def reword_requirement(context):
    reword(context, "C1@1", "Organisers need evenings that feel safe to newcomers", "conflict", "cloud_requirement")


@then("the Conflict tree link between the injection and the requirement is flagged for review")
def cloud_link_flagged(context):
    assert "L1@1" in reviews(context)


@then("the Future Reality link is not flagged, because nothing it cites has changed")
def frt_not_flagged(context):
    assert set(reviews(context)) == {"L1@1"}


@when("the consultant proposes a new wording of the injection and the operator accepts it")
def cascade_step(context):
    reword(context, "C2@1", "Invite everyone, warmly, at the end of each evening", "conflict", "injection")


@then("the Future Reality link is flagged for review in turn")
def frt_flagged(context):
    assert set(reviews(context)) == {"L1@1", "L2@1"}


@then("the backlog names, for each flag, the change that raised it")
def flags_named(context):
    flags = reviews(context)
    assert sorted((f["cites"], f["by"]) for f in flags["L1@1"]) == [("C1@1", "C1@2"), ("C2@1", "C2@2")]
    assert [(f["cites"], f["by"]) for f in flags["L2@1"]] == [("C2@1", "C2@2")]
    assert all(f["cites_summary"] and f["now_summary"] for entry in flags.values() for f in entry)


# S144 Keep one goal at the top of the Goal Tree.

@when("the consultant proposes a critical success factor that the goal requires and the operator accepts it")
def factor(context):
    accepted(context, claim("temp_csf", "Orders are planned against real capacity", tree="goal",
                            role="critical_success_factor"),
             link("temp_l", "temp_csf", "G1@1", tree="goal", relation="necessary_for"))


@then("the Goal Tree shows the commons' goal at its top with the factor beneath it")
def goal_on_top(context):
    goal_tree = tree(context, "goal")
    assert goal_tree["claims"][0]["ref"] == "G1@1" and goal_tree["claims"][0]["role"] == "goal"
    assert [(l["from"], l["to"]) for l in goal_tree["links"]] == [("C1@1", "G1@1")]
    drawing = plain(trees_lines(context.app.workspace(view="trees")["trees"], 100, only="goal"))
    assert drawing.index("At least 90% of orders on time") < drawing.index("Orders are planned against real capacity")


@then("the Goal view and the Goal Tree show the same goal")
def same_goal(context):
    goal = context.app.workspace(view="goal")["goals"]
    assert [g["ref"] for g in goal] == ["G1@1"] and tree(context, "goal")["claims"][0]["statement"] == \
        goal[0]["data"]["statement"]


@when("the consultant proposes a second goal that is not a new version of the current one")
def second_goal(context):
    context.before = context.app.inspect()
    context.provider.responses.append(exactly({"operation": "record_goal", "temporary_id": "goal",
                                                 "data": {"statement": "Ship faster", "protections": []}}))
    context.result = submit(context.app, "And a second goal")


@then("the proposal is rejected before commit because a commons has one goal")
def one_goal(context):
    assert context.result["status"] == "rejected" and "already has a goal" in context.result["reason"]
    assert context.app.inspect()["case"] == context.before["case"]


# S145 Use a statement from another tree in a link.

@given("an accepted Conflict tree injection")
def accepted_injection(context):
    case_with_goal(context, "A clear next step after open evenings")
    accepted(context, claim("temp_inj", "Invite at the end of each evening", tree="conflict", role="injection"))


@when("the consultant proposes a desired effect and a Future Reality link from that injection to it")
def frt_from_injection(context):
    reply(context, claim("temp_de", "Newcomers come to a first practice", tree="future_reality",
                         role="desired_effect"),
          link("temp_l", "C1@1", "temp_de", tree="future_reality"))


@when("the operator accepts both")
def accept_both(context):
    accept_all(context.app)


@then("the Future Reality Tree draws the injection, marked as from the Conflict tree, leading to the desired effect")
def borrowed(context):
    frt = tree(context, "future_reality")
    node = next(c for c in frt["claims"] if c["ref"] == "C1@1")
    assert node["from_tree"] == "conflict" and [(l["from"], l["to"]) for l in frt["links"]] == [("C1@1", "C2@1")]
    drawing = plain(trees_lines(context.app.workspace(view="trees")["trees"], 120, only="future_reality"))
    # The conflict tree's name on screen is the Evaporating Cloud.
    assert "Invite at the end of each evening" in drawing and "from the Evaporating Cloud" in drawing


@then("the injection stays one statement, so its new wording shows in both trees")
def one_statement(context):
    reword(context, "C1@1", "Invite everyone, warmly, at the end of each evening", "conflict", "injection")
    for name in ("conflict", "future_reality"):
        assert "Invite everyone, warmly, at the end of each evening" in [
            c["statement"] for c in tree(context, name)["claims"]]
    assert [(l["from"], l["to"]) for l in tree(context, "future_reality")["links"]] == [("C1@2", "C2@1")]


@then("a link whose two statements both belong to other trees than its own is rejected before commit")
def foreign_link(context):
    before = context.app.inspect()
    context.provider.responses.append(exactly(link("temp_l", "C1@2", "C2@1", tree="transition")))
    assert submit(context.app, "Link them in the Transition Tree")["status"] == "rejected"
    assert context.app.inspect()["case"] == before["case"]


# S146 Decide proposals while the consultant is working.

@given("the operator has sent an answer and the consultant has not replied")
def pending_answer(context):
    case_with_goal(context, "A clear next step after open evenings")
    reply(context, claim("temp_ude", "Newcomers do not know the next step"))
    context.request_id = retain(context.app, "It is because we never offer one")["request_id"]


@when("the operator accepts a waiting proposal")
def accept_while_pending(context):
    assert decide(context, "accept", ["C1@1"])["status"] == "saved"


@then("the consultant's reply is published when it arrives rather than treated as stale")
def published(context):
    context.provider.responses.append(exactly(
        claim("temp_cause", "We never offer a next step", role="root_cause"), link("temp_l", "temp_cause", "C1@1")))
    context.result = context.app.consult(context.request_id)
    assert context.result["status"] == "saved"


@then("its proposals are checked against the model as it stands after that acceptance")
def checked_after(context):
    assert "C1@1" in context.provider.calls[-1]["model"]["in_model"]
    link_entry = next(e for e in backlog(context) if e["ref"] == "L1@1")
    assert link_entry["waits_for"] == ["C2@1"]  # the effect is already in the model


# S147 Ask the consultant to draft amendments for open reviews.

@given("two accepted statements flagged for review")
def two_flagged(context):
    case_with_goal(context, "A clear next step after open evenings")
    accepted(context, claim("temp_ude", "Newcomers do not know the next step"),
             claim("temp_cause", "We never offer a next step", role="root_cause"),
             link("temp_l", "temp_cause", "temp_ude"),
             {"operation": "record_test", "temporary_id": "test", "data": {
                 "statement": "Offer a next step for a month", "goal_ref": "G1@1", "scope": None,
                 "forecast": [{"measure": "first practice", "expected": "6 of 30", "scope": None,
                               "denominator": "newcomers"}], "claim_ref": "temp_cause"}})
    reword(context, "C2@1", "Our open evenings end without an invitation", "current_reality", "root_cause")
    assert set(reviews(context)) == {"L1@1", "P1@1"}
    context.calls = len(context.provider.calls)


@when("the operator asks the consultant about the open reviews")
def ask_about_reviews(context):
    context.provider.responses.append(exactly({"operation": "record_retraction", "temporary_id": "temp_x",
                                                 "data": {"target_ref": "L1@1", "reason": "No longer what we mean"}}))
    case = context.app.inspect()["case"]
    context.result = context.app.submit("Do these still hold?", SPEAKER, case["revision"], case["current_intervention"],
                                        intent="review_flags")
    assert context.result["status"] == "saved"


@then("one consultant request carries the flagged statements and the changes that raised the flags")
def request_carries(context):
    assert len(context.provider.calls) == context.calls + 1
    request = context.provider.calls[-1]
    assert request["input"]["intent"] == "review_flags"
    assert {(f["ref"], f["cites"], f["by"]) for f in request["model"]["reviews"]} == {
        ("L1@1", "C2@1", "C2@2"), ("P1@1", "C2@1", "C2@2")}


@then("the amendments it proposes wait in the backlog like any other proposal")
def amendments_wait(context):
    assert context.result["proposed"] == ["X1@1"] and "X1@1" in waiting(context)
    assert [l["ref"] for l in tree(context, "current_reality")["links"]] == ["L1@1"]


# S148 Withdraw a statement together with the links that join it.

def test_record(alias, expected, **extra):
    return {"operation": "record_test", "temporary_id": alias, "data": {
        "statement": "Invite at the end for a month", "goal_ref": "G1@1", "scope": None,
        "forecast": [{"measure": "first practice", "expected": expected, "scope": None,
                      "denominator": "newcomers"}], **extra}}


def withdrawal(target):
    return {"operation": "record_retraction", "temporary_id": "temp_x",
            "data": {"target_ref": target, "reason": "Not what we think now"}}


@given("the Current Reality Tree holds an accepted cause with its causes link and a test that carries out the cause")
def cause_with_test(context):
    crt(context)
    accepted(context, test_record("test", "6 of 30", claim_ref="C2@1"))


@given("the consultant proposes withdrawing the cause")
def propose_withdrawal(context):
    assert reply(context, withdrawal("C2@1")) == ["X1@1"]


@when("the operator accepts the withdrawal")
def accept_withdrawal(context):
    context.before = context.app.inspect()
    decide(context, "accept", ["X1@1"])


@then("the operator is shown that the link leaves the tree with the cause and the test is flagged for review")
def shown_withdrawal(context):
    result = context.result
    assert result["status"] == "confirm" and result["refs"] == ["X1@1"], result
    assert result["leaves"] == ["L1@1"] and result["closes"] == []
    assert [(f["ref"], f["cites"], f["change"]) for f in result["flags"]] == [("P1@1", "C2@1", "withdrawn")]


@then("nothing changes until the operator confirms")
def nothing_yet(context):
    assert context.app.inspect() == context.before
    assert [l["ref"] for l in tree(context, "current_reality")["links"]] == ["L1@1"]


@then("a new revision removes the cause and its link from the tree and the test's flag waits in the backlog")
def withdrawn_with_link(context):
    assert revision(context) == context.before["case"]["revision"] + 1
    assert context.result["leaves"] == ["L1@1"]
    current = tree(context, "current_reality")
    assert [c["ref"] for c in current["claims"]] == ["C1@1"] and current["links"] == []
    assert list(reviews(context)) == ["P1@1"]


@then("in a commons set to accept proposals automatically, the same withdrawal waits for the operator")
def automatic_withdrawal_waits(context):
    context.automatic = True
    context.path = context.path.with_name("automatic-case")
    crt(context)
    assert reply(context, withdrawal("C2@1")) == ["X1@1"]
    assert waiting(context) == ["X1@1"]
    assert [l["ref"] for l in tree(context, "current_reality")["links"]] == ["L1@1"]
    assert not any(d["mode"] == "automatic" and "X1@1" in d["refs"] for d in decisions(context))


# S149 Cite only words the commons has taken in.

@given("an answer the operator sent became stale before the consultant replied to it")
def stale_answer(context):
    case_with_goal(context, "A clear next step after open evenings")
    context.stale = retain(context.app, "A second visit means within four weeks")["request_id"]
    reply(context, claim("temp_ude", "Newcomers do not know the next step"), text="The room is booked on Thursdays")
    assert context.app.consult(context.stale)["status"] == "stale"


@when("the operator sends another answer")
def another_answer(context):
    reply(context, claim("temp_cause", "We never offer a next step", role="root_cause"), text="We never offer one")


@then("the consultant's request does not carry the stale answer")
def request_without_stale(context):
    request = context.provider.calls[-1]
    assert context.stale not in request["sources"]
    assert request["input"]["request_id"] in request["sources"]


@then("a reply whose proposal cites the stale answer is rejected before commit, leaving the commons unchanged")
def citing_stale_rejected(context):
    before = context.app.inspect()
    def cites_stale(request):
        value = proposal(request)
        value["proposed_updates"].append({"operation": "record_note", "data": {
            "text": "A second visit means within four weeks", "basis": "participant_report"},
            "source_refs": [context.stale]})
        return value
    context.provider.responses.append(cites_stale)
    result = submit(context.app, "What would you advise?")
    assert result["status"] == "rejected" and context.stale in result["reason"], result
    assert context.app.inspect()["case"] == before["case"]


@then("the stale answer stays retained with its source, so the operator can send it again")
def stale_retained(context):
    assert context.app.sources()["sources"][context.stale]["text"] == "A second visit means within four weeks"
    pending = context.app.workspace()["pending_requests"]
    assert (context.stale, "stale") in [(p["input"]["request_id"], p["status"]) for p in pending]


# S150 Revise a test's forecast only before its first result.

def forecasts(context):
    return [(c["test"]["ref"], c["test"]["data"]["forecast"][0]["expected"])
            for c in context.app.workspace(view="tests")["comparisons"]]


@given('an accepted test forecasting "{expected}" and an accepted action that carries it out')
def test_with_action(context, expected):
    case_with_goal(context, "A clear next step after open evenings")
    accepted(context, test_record("test", expected),
             {"operation": "record_action", "temporary_id": "temp_a",
              "data": {"statement": "Give the invitation myself", "test_ref": "test"}})
    assert forecasts(context) == [("P1@1", expected)]


@when('the operator accepts a new version of the test forecasting "{expected}"')
def new_test_version(context, expected):
    assert accepted(context, test_record("temp_p", expected, replaces="P1@1")) == ["P1@2"]


@then("the Tests view shows one test with the new forecast, and the commons history keeps the earlier one")
def one_test(context):
    assert forecasts(context) == [("P1@2", "8 of 30")]
    records = {r["ref"]: r for r in context.app.inspect()["case"]["records"]}
    assert records["P1@1"]["data"]["forecast"][0]["expected"] == "6 of 30"


@then("the action is flagged for review because it was planned for the earlier version")
def action_flagged(context):
    assert {ref: [(f["cites"], f["change"], f["now"]) for f in flags] for ref, flags in reviews(context).items()} == {
        "A1@1": [("P1@1", "new_version", "P1@2")]}


@when("a result is reported for the test and accepted")
def result_accepted(context):
    accepted(context, {"operation": "record_observation", "temporary_id": "temp_obs", "data": {
        "test_ref": "P1@2", "measure": "first practice", "value": "9 of 31", "basis": "participant_report"}})


@then("a further new version of the test is rejected before commit, so the forecast stays as it was before the result")
def no_version_after_result(context):
    before = context.app.inspect()
    context.provider.responses.append(exactly(test_record("temp_p", "10 of 30", replaces="P1@2")))
    result = submit(context.app, "Make it 10 of 30")
    assert result["status"] == "rejected" and "result" in result["reason"], result
    assert context.app.inspect()["case"] == before["case"]
    assert forecasts(context) == [("P1@2", "8 of 30")]


@then("a result citing the earlier version of the test is rejected before commit")
def result_for_earlier_version(context):
    before = context.app.inspect()
    context.provider.responses.append(exactly({"operation": "record_observation", "temporary_id": "temp_obs",
        "data": {"test_ref": "P1@1", "measure": "first practice", "value": "3 of 10", "basis": "participant_report"}}))
    result = submit(context.app, "3 of 10 came")
    assert result["status"] == "rejected" and "P1@1" in result["reason"], result
    assert context.app.inspect()["case"] == before["case"]
