"""What enters the model: domain rules for proposals and decisions, with no skill, agent or interface present.

The acceptance scenarios (feature 13) drive these rules through the application; here the negative
cases are checked at the domain, and cases recorded before proposals needed acceptance are read.
"""

from copy import deepcopy
from pathlib import Path

import pytest

from reason_commons.adapters.mcp_server import CaseToolBridge
from reason_commons.bootstrap import create_case, import_case, open_case
from reason_commons.domain.model import InvalidCase, Snapshot, StaleWork, validate_ancestry
from tests.support import ScriptedConsultant, accept_all, proposal, submit
from tests.test_domain import aggregate

FIXTURE = Path(__file__).parent / "fixtures" / "recorded-before-proposals.reasoncase"


def update(kind, temp, **data):
    return {"operation": "record_" + kind, "temporary_id": temp, "data": data, "source_refs": ["in001"]}


def reply(case, value, sources, *updates, revision=1):
    body = proposal({"input": value})
    body["proposed_updates"] = list(updates)
    return case.apply(body, value, sources, revision, value["timestamp"], value["timezone"], "fixture/1")


def crt():
    """A reply proposing a symptom, a cause and the link between them."""
    case, value, sources = aggregate()
    return reply(case, value, sources,
                 update("claim", "temp_e", tree="current_reality", role="undesirable_effect", statement="Late"),
                 update("claim", "temp_c", tree="current_reality", role="root_cause", statement="Interrupted"),
                 update("link", "temp_l", tree="current_reality", relation="causes", from_ref="temp_c", to_ref="temp_e")
                 ), sources


def decide(case, sources, action, refs, value=None, revision=None):
    return case.decide(action, refs, "Sam", sources, revision or case.revision + 1, "2026-10-07T09:00:00+00:00",
                       "Europe/Berlin", value)


def test_a_reply_publishes_its_question_and_proposes_its_updates():
    case, sources = crt()
    membership = case.membership()
    assert case.target == "I1@1" and membership.model() == []
    assert [e["ref"] for e in membership.backlog()] == ["C1@1", "C2@1", "L1@1"]
    assert membership.backlog()[2]["waits_for"] == ["C2@1", "C1@1"]


def test_acceptance_takes_what_it_needs_and_rejection_what_needs_it():
    case, sources = crt()
    accepted, decision = decide(case, sources, "accept", ["L1@1"])
    assert decision["refs"] == ["C1@1", "C2@1", "L1@1"] and decision["mode"] == "explicit"
    assert accepted.membership().model() == ["C1@1", "C2@1", "L1@1"]
    rejected, decision = decide(case, sources, "reject", ["C1@1"])
    assert decision["refs"] == ["C1@1", "L1@1"] and rejected.membership().backlog()[0]["ref"] == "C2@1"
    with pytest.raises(InvalidCase):
        decide(rejected, sources, "accept", ["C1@1"])


def test_undo_takes_what_cannot_stand_without_it_is_final_and_keeps_history():
    case, sources = crt()
    accepted, _ = decide(case, sources, "accept", ["L1@1"])
    undone, decision = decide(accepted, sources, "undo", ["C2@1"])
    assert decision["refs"] == ["C2@1", "L1@1"]
    assert undone.membership().model() == ["C1@1"] and undone.membership().backlog() == []
    assert len(undone.value["records"]) == len(accepted.value["records"])
    for action in ("undo", "accept"):
        with pytest.raises(InvalidCase):
            decide(undone, sources, action, ["C2@1"])


def test_a_new_version_flags_what_cites_it_until_it_still_holds():
    case, value, sources = aggregate()
    case = reply(case, value, sources,
                 update("claim", "temp_e", tree="current_reality", role="undesirable_effect", statement="Late"),
                 update("claim", "temp_c", tree="current_reality", role="root_cause", statement="Interrupted"),
                 update("link", "temp_l", tree="current_reality", relation="causes", from_ref="temp_c", to_ref="temp_e"))
    case, _ = decide(case, sources, "accept", ["L1@1"])
    second = dict(value, request_id="in002", base_revision=case.revision, response_target=case.target)
    sources = {**sources, "in002": second}
    case = reply(case, second, sources, {**update("claim", "temp_n", tree="current_reality", role="root_cause",
                                                  statement="Jobs are interrupted", replaces="C2@1"),
                                         "source_refs": ["in002"]}, revision=case.revision + 1)
    assert case.membership().flags() == []  # a waiting new version changes nothing
    case, _ = decide(case, sources, "accept", ["C2@2"])
    flags = case.membership().flags()
    assert [(f["ref"], f["cites"], f["change"], f["now"]) for f in flags] == [("L1@1", "C2@1", "new_version", "C2@2")]
    held, decision = decide(case, sources, "still_holds", ["L1@1"])
    assert decision["about"] == [{"ref": "C2@1", "now": "C2@2"}] and held.membership().flags() == []
    with pytest.raises(InvalidCase):
        decide(held, sources, "still_holds", ["L1@1"])  # no open review left


def test_a_case_has_one_goal_and_a_change_is_its_new_version():
    case, value, sources = aggregate()
    goal = {"statement": "On time", "scope": None, "horizon": None, "measure": None, "baseline": None,
            "protections": []}
    case = reply(case, value, sources, update("goal", "goal", **goal))
    second = dict(value, request_id="in002", base_revision=case.revision, response_target=case.target)
    sources = {**sources, "in002": second}
    with pytest.raises(InvalidCase, match="already has a goal"):
        reply(case, second, sources, {**update("goal", "goal", **dict(goal, statement="Faster")),
                                      "source_refs": ["in002"]}, revision=2)
    newer = reply(case, second, sources, {**update("goal", "goal", **dict(goal, statement="Faster", replaces="G1@1")),
                                          "source_refs": ["in002"]}, revision=2)
    assert [r["ref"] for r in newer.value["records"] if r["kind"] == "goal"] == ["G1@1", "G1@2"]
    with pytest.raises(InvalidCase, match="goal role"):
        reply(case, second, sources, {**update("claim", "temp_g", tree="goal", role="goal", statement="Faster"),
                                      "source_refs": ["in002"]}, revision=2)


def test_a_link_belongs_to_the_tree_of_one_of_its_statements():
    case, value, sources = aggregate()
    claims = [update("claim", "temp_i", tree="conflict", role="injection", statement="Invite"),
              update("claim", "temp_d", tree="future_reality", role="desired_effect", statement="People come")]
    ok = reply(case, value, sources, *claims, update("link", "temp_l", tree="future_reality", relation="causes",
                                                    from_ref="temp_i", to_ref="temp_d"))
    assert ok.membership().records["L1@1"]["data"]["tree"] == "future_reality"
    with pytest.raises(InvalidCase, match="tree of at least one"):
        reply(case, value, sources, *claims, update("link", "temp_l", tree="transition", relation="causes",
                                                    from_ref="temp_i", to_ref="temp_d"))


@pytest.mark.parametrize("forge", [
    lambda v: v["decisions"].append({"id": "D2", "action": "accept", "refs": ["C1@1"], "closes": [],
                                     "mode": "explicit", "actor": "Sam", "timestamp": "t"}),  # accepted twice
    lambda v: v["decisions"][0].update(mode="automatic"),  # a local decision cannot be automatic
    lambda v: v["decisions"][0].update(refs=["L1@1"]),  # the link cannot enter without its statements
    lambda v: v["decisions"][0].update(id="D7"),
    lambda v: v["membership"].update(acceptance="automatic"),  # a setting no decision chose
    lambda v: v["records"][0].update(confidence=2),
])
def test_forged_decisions_are_rejected(forge):
    case, sources = crt()
    accepted, _ = decide(case, sources, "accept", ["L1@1"])
    value = deepcopy(accepted.value)
    forge(value)
    with pytest.raises(InvalidCase):
        Snapshot(value).validate(sources)


def test_ancestry_allows_one_decision_per_local_revision_and_no_rewriting():
    initial, value, sources = aggregate()
    case, _ = crt()
    accepted, _ = decide(case, sources, "accept", ["L1@1"])
    validate_ancestry([initial, case, accepted], sources)
    rewritten = deepcopy(accepted.value)
    rewritten["records"].append(deepcopy(rewritten["records"][0]) | {"ref": "N9@1"})
    with pytest.raises(InvalidCase):
        validate_ancestry([initial, case, Snapshot(rewritten)], sources)
    undone, _ = decide(accepted, sources, "undo", ["C2@1"])
    rewritten = deepcopy(undone.value)
    rewritten["decisions"][0]["actor"] = "Someone else"
    with pytest.raises(InvalidCase, match="decisions were rewritten"):
        validate_ancestry([initial, case, accepted, Snapshot(rewritten)], sources)


def test_decisions_do_not_make_a_pending_reply_stale_but_a_new_question_does():
    case, value, sources = aggregate()
    first = reply(case, value, sources, update("claim", "temp_e", tree="current_reality",
                                               role="undesirable_effect", statement="Late"))
    pending = dict(value, request_id="in002", base_revision=first.revision, response_target=first.target)
    sources = {**sources, "in002": pending}
    decided, _ = decide(first, sources, "accept", ["C1@1"])
    later = reply(decided, pending, sources, {**update("note", "temp_n", text="ok"), "source_refs": ["in002"]},
                  revision=decided.revision + 1)
    assert later.target == "I2@1"
    other = dict(value, request_id="in003", base_revision=first.revision, response_target=first.target)
    with pytest.raises(StaleWork):
        reply(later, other, {**sources, "in003": other}, revision=later.revision + 1)


def test_automatic_acceptance_admits_what_is_ready_in_the_reply_itself(tmp_path):
    with create_case(tmp_path / "case", "Auto", consultant=ScriptedConsultant(), acceptance="automatic",
                     actor="Sam") as app:
        result = submit(app, "A report")
        case = app.inspect()["case"]
        assert result["accepted_automatically"] == result["proposed"] == ["N1@1"]
        assert case["decisions"][0]["value"] == "automatic" and case["decisions"][1]["mode"] == "automatic"
        assert app.set_acceptance("review", "Sam", case["revision"])["status"] == "saved"
        submit(app, "Another")
        assert [e["ref"] for e in app.workspace(view="backlog")["backlog"]] == ["N2@1"]


def test_a_skill_host_cannot_switch_on_automatic_acceptance_unless_granted(tmp_path):
    bridge = CaseToolBridge(tmp_path, ScriptedConsultant())
    bridge.invoke("new_case", {"case": "payments", "name": "Payments"})
    refused = bridge.invoke("set_acceptance", {"case": "payments", "mode": "automatic", "speaker": "Agent",
                                               "base_revision": 0})
    assert refused["status"] == "rejected"
    granted = CaseToolBridge(tmp_path, ScriptedConsultant(), allow_acceptance_setting=True)
    assert granted.invoke("set_acceptance", {"case": "payments", "mode": "automatic", "speaker": "Sam",
                                             "base_revision": 0})["status"] == "saved"


def test_a_case_recorded_before_proposals_needed_acceptance_opens_unchanged(tmp_path):
    """The fixture was built by the release before this one: an import that recorded the file's goal twice
    (as the goal and as a Goal Tree claim), a cause, a link and a rewording, with no decisions at all."""
    with open_case(FIXTURE, writable=False) as archive:
        before = archive.inspect()["case"]
        assert "membership" not in before and "decisions" not in before
    with import_case(FIXTURE, tmp_path / "case", consultant=ScriptedConsultant()) as app:
        workspace = app.workspace(view="trees")
        # Everything in it is in the model; nothing waits and nothing is flagged.
        assert workspace["backlog"] == [] and set(workspace["membership"].values()) == {"accepted"}
        goal_tree = next(t for t in workspace["trees"] if t["tree"] == "goal")
        # The doubly recorded goal is read as the one goal, at the top of its tree.
        assert goal_tree["claims"][0]["ref"] == "G1@1" and goal_tree["links"][0]["to"] == "G1@1"
        crt_tree = next(t for t in workspace["trees"] if t["tree"] == "current_reality")
        assert "Work starts a week late" in [c["statement"] for c in crt_tree["claims"]]
        # The first change under the new contract marks where proposals begin; history is unchanged.
        records = len(before["records"])
        assert submit(app, "Something new")["status"] == "saved"
        case = app.inspect()["case"]
        assert case["membership"] == {"proposals_from": records, "acceptance": "review"}
        assert case["records"][:records] == before["records"]
        assert [e["ref"] for e in app.workspace(view="backlog")["backlog"]] == [case["records"][records]["ref"]]
        accept_all(app, "David")
