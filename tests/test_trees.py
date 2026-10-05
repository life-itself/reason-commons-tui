"""Thinking-process trees grow through ordinary proposals and stay append-only."""

import pytest

from reason_commons.domain.model import InvalidCase
from tests.support import ScriptedConsultant, bounded_case, fixture_app, proposal, submit
from tests.test_domain import aggregate, apply


def claim(alias, statement, tree="current_reality", role="undesirable_effect", **extra):
    return {"operation": "record_claim", "temporary_id": alias,
            "data": {"tree": tree, "role": role, "statement": statement, **extra}, "source_refs": ["in001"]}


def link(alias, source, target, tree="current_reality", relation="causes", **extra):
    return {"operation": "record_link", "temporary_id": alias,
            "data": {"tree": tree, "relation": relation, "from_ref": source, "to_ref": target, **extra},
            "source_refs": ["in001"]}


def with_updates(*updates):
    def build(request):
        value = proposal(request)
        value["proposed_updates"] = [{**u, "source_refs": [request["input"]["request_id"]]} for u in updates]
        return value
    return build


def test_claims_and_links_resolve_temporary_references():
    case, value, sources = aggregate()
    update = proposal({"input": value})
    update["proposed_updates"] += [claim("temp_ude", "Newcomers do not know the next step"),
                                   claim("temp_root", "No reliable path from interest to practice", role="root_cause"),
                                   link("temp_link", "temp_root", "temp_ude", assumption="Nothing else blocks it")]
    records = {r["ref"]: r for r in apply(case, value, sources, update).value["records"]}
    assert records["L1@1"]["data"] == {"tree": "current_reality", "relation": "causes", "from_ref": "C2@1",
                                       "to_ref": "C1@1", "assumption": "Nothing else blocks it"}


@pytest.mark.parametrize("updates", [
    [claim("temp_a", "A goal in the wrong tree", role="goal")],
    [claim("temp_a", "Unknown tree", tree="solution")],
    [claim("temp_a", "Unknown role", role="vision")],
    [claim("temp_a", "Effect"), link("temp_l", "temp_a", "temp_a")],
    [claim("temp_a", "Effect"), claim("temp_b", "Need", tree="conflict", role="cloud_requirement"),
     link("temp_l", "temp_a", "temp_b")],
    [claim("temp_a", "Effect"), claim("temp_b", "Cause", role="root_cause"),
     link("temp_l", "temp_b", "temp_a", relation="so_that")],
    # A link must follow the claims it joins, so history reads in order.
    [link("temp_l", "temp_b", "temp_a"), claim("temp_a", "Effect"), claim("temp_b", "Cause", role="root_cause")],
    [{"operation": "record_retraction", "temporary_id": "temp_x",
      "data": {"target_ref": "goal", "reason": "Goals are not tree claims"}, "source_refs": ["in001"]}],
])
def test_rejects_invalid_tree_records(updates):
    case, value, sources = aggregate()
    update = bounded_case({"input": value})
    update["proposed_updates"] += updates
    with pytest.raises(InvalidCase):
        apply(case, value, sources, update)


def test_rewording_keeps_links_and_withdrawing_hides_them(tmp_path):
    consultant = ScriptedConsultant([
        with_updates(claim("temp_ude", "Few people practise"), claim("temp_root", "No path", role="root_cause"),
                     link("temp_link", "temp_root", "temp_ude")),
        with_updates(claim("temp_new", "No reliable path from interest to practice", role="root_cause",
                           replaces="C2@1")),
    ])
    app, _ = fixture_app(tmp_path / "case", consultant)
    assert submit(app, "Few practise because there is no path")["status"] == "saved"
    assert submit(app, "Say it more precisely")["status"] == "saved"
    tree = app.workspace(view="trees")["trees"][1]
    assert tree["tree"] == "current_reality"
    assert [c["statement"] for c in tree["claims"]] == ["Few people practise", "No reliable path from interest to practice"]
    assert tree["claims"][1]["earlier_wording"] == ["No path"]
    assert tree["links"] == [{"ref": "L1@1", "relation": "causes", "from": "C3@1", "to": "C1@1", "assumption": None}]
    # The original wording stays in the record history.
    assert any(r["ref"] == "C2@1" for r in app.inspect()["case"]["records"])

    consultant.responses.append(with_updates({"operation": "record_retraction", "temporary_id": "temp_x",
                                               "data": {"target_ref": "C3@1", "reason": "We no longer think so"},
                                               "source_refs": []}))
    assert submit(app, "Drop that cause")["status"] == "saved"
    tree = app.workspace(view="trees")["trees"][1]
    assert [c["ref"] for c in tree["claims"]] == ["C1@1"] and tree["links"] == []
    # A withdrawn claim cannot be linked again.
    consultant.responses.append(with_updates(claim("temp_c", "Another cause", role="root_cause"),
                                             link("temp_l", "C3@1", "C1@1")))
    assert submit(app, "Link the old cause")["status"] == "rejected"


def test_a_test_can_carry_out_a_tree_claim(tmp_path):
    def plan(request):
        value = bounded_case(request)
        value["proposed_updates"].insert(0, claim("temp_act", "Prototype one next step after open evenings",
                                                  tree="transition", role="transition_action"))
        value["proposed_updates"][0]["source_refs"] = [request["input"]["request_id"]]
        value["proposed_updates"][-1]["data"]["claim_ref"] = "temp_act"
        return value
    app, _ = fixture_app(tmp_path / "case", ScriptedConsultant([plan]))
    assert submit(app, "Pilot the open evening pathway")["status"] == "saved"
    workspace = app.workspace(view="trees")
    transition = next(t for t in workspace["trees"] if t["tree"] == "transition")
    assert transition["claims"][0]["tests"] == [{"ref": "P1@1", "statement": "Bounded release pilot",
                                                 "forecast": ["80%", "95%"], "results": []}]
    assert {"from": "P1@1", "to": "C1@1", "field": "claim_ref", "label": "carries out"} in app.workspace(view="tests")["diagram"]["links"]


def drawn_tree(name, claims, links):
    """A projected tree, as the workspace read returns it, for drawing tests."""
    return {"tree": name,
            "claims": [{"ref": ref, "role": role, "statement": statement, "basis": None, "earlier_wording": [],
                        "tests": []} for ref, role, statement in claims],
            "links": [{"ref": f"L{index}@1", "relation": relation, "from": source, "to": target,
                       "assumption": assumption}
                      for index, (relation, source, target, assumption) in enumerate(links, start=1)]}


def test_outline_draws_the_assumption_behind_every_link():
    from reason_commons.adapters.trees import plain, trees_lines
    cloud = drawn_tree("conflict", [("C1@1", "cloud_prerequisite", "Act like a movement now"),
                                    ("C2@1", "cloud_prerequisite", "Act like a monastery now")],
                       [("conflicts_with", "C1@1", "C2@1", "Both draw on the same few organisers")])
    # The root cause has two effects, so its second branch refers back to the first drawing.
    reality = drawn_tree("current_reality", [("C3@1", "undesirable_effect", "Organisers burn out"),
                                             ("C4@1", "undesirable_effect", "Few keep practising"),
                                             ("C5@1", "root_cause", "No path into practice")],
                         [("causes", "C5@1", "C3@1", "Newcomers lean on organisers"),
                          ("causes", "C5@1", "C4@1", "Without a next step people drift away")])
    text = plain(trees_lines([cloud, reality], width=200))
    for assumption in ("Both draw on the same few organisers", "Newcomers lean on organisers",
                       "Without a next step people drift away"):
        assert text.count("assuming " + assumption) == 1, assumption


def test_every_imported_assumption_is_drawn(tmp_path):
    from importlib.resources import files
    import yaml
    from reason_commons.adapters.ltp_trees import import_trees
    from reason_commons.adapters.trees import plain, trees_lines
    from reason_commons.bootstrap import create_case, open_case
    source = files("reason_commons.adapters").joinpath("sample-trees.ltp.yaml")
    create_case(tmp_path / "case", "Sample").close()
    import_trees(tmp_path / "case", str(source), "Sam")
    with open_case(tmp_path / "case", writable=False) as app:
        text = plain(trees_lines(app.workspace(view="trees")["trees"], width=1000))
    for assumption in yaml.safe_load(source.read_text())["ltp"]["assumptions"]:
        assert "assuming " + assumption["statement"] in text, assumption["id"]
