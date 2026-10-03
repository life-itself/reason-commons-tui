"""Rules stay enforceable with no skill or agent present."""

from copy import deepcopy

import pytest

from reason_commons.domain.model import InvalidCase, Snapshot, StaleWork
from tests.support import bounded_case, proposal


def aggregate():
    case = Snapshot.initial("case-id", "Payments", "2026-10-02T08:00:00+00:00", "Europe/Berlin")
    input_record = {"schema_version": "1", "request_id": "in001", "base_revision": 0,
                    "response_target": None, "text": "Pilot", "speaker": "Sam", "intent": "answer",
                    "declarations": {}, "timestamp": "2026-10-02T08:00:00+00:00", "timezone": "Europe/Berlin"}
    return case, input_record, {"in001": input_record}


def apply(case, value, sources, update):
    return case.apply(update, value, sources, 1, value["timestamp"], value["timezone"], "fixture/1")


def test_locally_allocated_ids_resolve_references_and_preserve_unknowns():
    case, value, sources = aggregate()
    next_case = apply(case, value, sources, bounded_case({"input": value}))
    assert case.value["records"] == []
    records = {r["ref"]: r for r in next_case.value["records"]}
    assert records["P1@1"]["data"]["goal_ref"] == "G1@1"
    assert records["I1@1"]["data"]["required_context_refs"] == ["G1@1", "P1@1"]
    assert records["G1@1"]["data"]["baseline"] is None
    assert records["G1@1"]["source_refs"] == ["in001"]


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(delivery_profile="p3"),
    lambda p: p.update(base_revision=999),
    lambda p: p.update(request_id="in999"),
    lambda p: p["intervention"].update(goal_ref="G999@1"),
    lambda p: p["intervention"].update(stances=[]),
    lambda p: p["intervention"].update(options=[{"id": "O1", "label": "Record position",
                                                "action": {"type": "view", "target": "stances"}}]),
    lambda p: p["proposed_updates"][0]["data"].update(relationships=[]),
    lambda p: p["proposed_updates"][0].update(source_refs=["in999"]),
    lambda p: p["proposed_updates"][0]["data"].update(basis="observed"),
    lambda p: p["proposed_updates"].append({"operation": "record_stance", "data": {}, "source_refs": ["in001"]}),
])
def test_rejects_whole_invalid_proposal(mutation):
    case, value, sources = aggregate()
    update = bounded_case({"input": value})
    mutation(update)
    with pytest.raises(InvalidCase):
        apply(case, value, sources, update)
    assert case.value["records"] == [] and case.revision == 0


def test_ownership_needs_cited_declaration_and_is_not_inferred_from_prose():
    case, value, sources = aggregate()
    value["text"] = "Sam should own the pilot"
    update = bounded_case({"input": value})
    update["proposed_updates"].append({"operation": "record_action", "data": {
        "statement": "Run pilot", "test_ref": "test", "owner": "Sam"}, "source_refs": ["in001"]})
    with pytest.raises(InvalidCase, match="Ownership"):
        apply(case, value, sources, update)
    value["declarations"]["ownership"] = ["Sam"]
    assert apply(case, value, sources, update).revision == 1


def test_stale_target_and_base_are_both_checked():
    case, value, sources = aggregate()
    value["response_target"] = "I999@1"
    with pytest.raises(StaleWork):
        apply(case, value, sources, proposal({"input": value}))


def test_forecast_cannot_be_overwritten_in_a_new_revision():
    from reason_commons.domain.model import validate_ancestry
    case, value, sources = aggregate()
    first = apply(case, value, sources, bounded_case({"input": value}))
    second_value = deepcopy(value)
    second_value.update(request_id="in002", base_revision=1, response_target=first.target)
    sources["in002"] = second_value
    second = first.apply(proposal({"input": second_value}), second_value, sources, 2,
                         value["timestamp"], value["timezone"], "fixture/1")
    second.value["records"][2]["data"]["forecast"][0]["expected"] = "99%"
    with pytest.raises(InvalidCase, match="rewritten"):
        validate_ancestry([case, first, second], sources)


@pytest.mark.parametrize("kind,field,data", [
    ("test", "goal_ref", {"statement": "Pilot", "scope": None, "forecast": [
        {"measure": "on-time", "expected": "80%", "scope": None, "denominator": None}]}),
    ("action", "test_ref", {"statement": "Implement queue"}),
    ("observation", "test_ref", {"measure": "on-time", "value": "80%"}),
    ("review", "test_ref", {"assessment": "Inconclusive"}),
])
def test_required_relationship_cannot_be_null_in_runtime_or_projected_schema(kind, field, data):
    import jsonschema
    from reason_commons.domain.contract import proposal_schema
    case, value, sources = aggregate()
    update = proposal({"input": value})
    update["proposed_updates"].append({"operation": "record_" + kind, "source_refs": ["in001"],
                                      "data": {**data, field: None}})
    with pytest.raises(InvalidCase, match=field):
        apply(case, value, sources, update)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(update, proposal_schema())
    assert case.revision == 0 and case.value["records"] == []


@pytest.mark.parametrize("kind,field", [("goal", "statement"), ("note", "text"),
                                      ("test", "statement"), ("action", "statement"),
                                      ("observation", "measure"), ("observation", "value"),
                                      ("review", "assessment")])
def test_record_cannot_have_null_defining_text_while_optional_unknowns_remain_allowed(kind, field):
    from reason_commons.domain.model import REQUIRED, validate_value
    from reason_commons.domain.contract import proposal_schema
    import jsonschema
    data = {name: "Explicit text" for name in REQUIRED[kind]}
    if kind == "test":
        data.update(scope=None, forecast=[{"measure": "delivery", "expected": "80%",
                                          "scope": None, "denominator": None}])
    data[field] = None
    with pytest.raises(InvalidCase, match=field):
        validate_value(kind, data)
    schema = next(s for s in proposal_schema()["properties"]["proposed_updates"]["items"]["anyOf"]
                  if s["properties"]["operation"]["const"] == "record_" + kind)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"operation": "record_" + kind, "data": data, "source_refs": ["in001"]}, schema)
