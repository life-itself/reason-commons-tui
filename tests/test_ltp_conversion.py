"""Legacy reasoning survives continuation conversion without gaining new authority."""

import base64
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from reason_commons.adapters.ltp_conversion import convert_ltp, read_ltp
from reason_commons.bootstrap import import_case, open_case
from reason_commons.domain.model import InvalidCase
from tests.support import accept_all, ScriptedConsultant, cli, submit


def legacy():
    return {"ltp": {"schema_version": "1.0", "project_id": "legacy", "title": "Existing commons",
        "entities": [
            {"id": "goal", "tree": "goal", "statement": "People use the reasoning tool", "provenance": {"path": "source.md#L3"}},
            {"id": "old", "tree": "current_reality", "statement": "Nobody uses it", "provenance": {"path": "source.md#L5"}},
            {"id": "new", "tree": "current_reality", "statement": "The founders use it", "provenance": {"path": "source.md#L9"}},
            {"id": "action", "tree": "transition", "statement": "Run a real user trial", "provenance": {"path": "source.md#L11"}},
            {"id": "effect", "tree": "transition", "statement": "Learn from actual use", "provenance": {"path": "source.md#L12"}}],
        "designations": [
            {"id": "d-goal", "entity_id": "goal", "role": "goal"},
            {"id": "d-old", "entity_id": "old", "role": "undesirable_effect"},
            {"id": "d-new", "entity_id": "new", "role": "observation"},
            {"id": "d-action", "entity_id": "action", "role": "transition_action"},
            {"id": "d-effect", "entity_id": "effect", "role": "transition_expected_effect", "parent_designation_id": "d-action"}],
        "relationships": [
            {"id": "supersession", "tree": "current_reality", "kind": "supersedes", "from_entity_ids": ["new"], "to_entity_id": "old"},
            {"id": "forecast", "tree": "transition", "kind": "produces", "from_entity_ids": ["action"], "to_entity_id": "effect"}],
        "assumptions": [{"id": "assumption", "statement": "The trial will be informative", "relationship_id": "forecast"}],
        "assessments": [{"id": "assessment", "kind": "breaks_conflict", "tree": "conflict", "statement": "This is proposed",
                         "subject_ids": ["d-action"], "depends_on": ["assumption", "forecast"]}], "changes": []}}


def source_file(tmp_path, value=None):
    source = tmp_path / "original.ltp.yaml"
    source.write_bytes(("# Preserve this comment and exact bytes\n" + yaml.safe_dump(value or legacy(), sort_keys=False)).encode())
    return source


def convert(source, store, bundle):
    return convert_ltp(source, store, bundle, speaker="David", request_text="Convert this existing reasoning so we can continue.")


def test_conversion_preserves_all_claims_original_bytes_provenance_and_supersession(tmp_path):
    source = source_file(tmp_path)
    before = source.read_bytes()
    store, bundle = tmp_path / "case", tmp_path / "case.reasoncase"
    report = convert(source, store, bundle)
    assert report["model_inference_calls"] == 0
    assert report["source_sha256"] == sha256(before).hexdigest()
    assert report["native_record_counts"] == {"goal": 1, "note": 10, "intervention": 1}
    assert source.read_bytes() == before
    for section, rows in legacy()["ltp"].items():
        if isinstance(rows, list):
            assert set(report["legacy_to_native"][section]) == {row["id"] for row in rows}
    with open_case(store, writable=False) as app:
        records = {r["ref"]: r for r in app.inspect()["case"]["records"]}
        assert records[report["native_goal_ref"]]["data"]["statement"] == "People use the reasoning tool"
        assert records[report["native_goal_ref"]]["data"]["baseline"] is None
        for entity in legacy()["ltp"]["entities"]:
            note = records[report["legacy_to_native"]["entities"][entity["id"]]]["data"]["text"]
            assert entity["statement"] in note and entity["provenance"]["path"] in note
        old = records[report["legacy_to_native"]["entities"]["old"]]["data"]["text"]
        assert "Historical qualification" in old and "new supersedes" in old
        relation = records[report["legacy_to_native"]["relationships"]["supersession"]]["data"]["text"]
        assert "supersedes" in relation and "without a native graph edge" in relation
        assert records[report["legacy_to_native"]["entities"]["new"]]["data"]["basis"] == "participant_report"
        assert not any(r["kind"] in {"action", "test", "observation", "review"} for r in records.values())
        original = app.sources()["sources"][report["source_ref"]]
        assert base64.b64decode(original["content_base64"]) == before
        assert "not inferred" in original["speaker"]
        assert app.workspace()["question"]["data"]["required_context_refs"]
    with open_case(bundle, writable=False) as app:
        assert base64.b64decode(app.sources()["sources"][report["source_ref"]]["content_base64"]) == before


def test_portable_case_can_continue_in_a_new_immutable_snapshot(tmp_path):
    source = source_file(tmp_path)
    store, bundle = tmp_path / "case", tmp_path / "case.reasoncase"
    convert(source, store, bundle)
    old_bytes = {p.name: p.read_bytes() for p in (store / "revisions").glob("*.yaml")}
    consultant = ScriptedConsultant()
    with import_case(bundle, tmp_path / "continued", consultant=consultant) as app:
        first = app.inspect()["case"]
        result = submit(app, "I choose the real user trial. Its success criteria are not agreed yet.")
        assert result["status"] == "saved" and result["revision"] == 2
        after = app.inspect()["case"]
        assert after["parent"] == 1 and after["records"][:len(first["records"])] == first["records"]
        assert consultant.calls[0]["case"] == first
        assert len(app.history()["revisions"]) == 3
    assert old_bytes == {p.name: p.read_bytes() for p in (tmp_path / "continued" / "revisions").glob("*.yaml") if p.name in old_bytes}
    assert len(consultant.calls) == 1


def test_continuation_view_is_focused_and_full_reasoning_remains_inspectable(tmp_path):
    source = source_file(tmp_path)
    store = tmp_path / "case"
    report = convert(source, store, tmp_path / "case.reasoncase")
    with open_case(store) as app:
        # The converted baseline waits for the operator like any import.
        assert len(app.workspace(view="backlog")["backlog"]) == 11 and app.workspace()["records"] == [
            r for r in app.workspace()["records"] if r["kind"] == "intervention"]
        accept_all(app)
    with open_case(store, writable=False) as app:
        next_view = app.workspace()
        reasoning = app.workspace(view="reasoning")
        assert next_view["record_count"] == 12
        assert len(next_view["records"]) == 3 and len(reasoning["records"]) == 11
        assert report["legacy_to_native"]["entities"]["action"] in {r["ref"] for r in next_view["records"]}
        assert reasoning["diagram"]["links"] == []
    shown = cli("show", store, "--format", "json")
    assert shown.returncode == 0 and json.loads(shown.stdout)["workspace"] == next_view


@pytest.mark.parametrize("mutation", [
    lambda v: v["ltp"].update(schema_version="2.0"),
    lambda v: v["ltp"]["relationships"][0].update(to_entity_id="missing"),
    lambda v: v["ltp"]["designations"][0].update(parent_designation_id="missing"),
    lambda v: v["ltp"]["entities"].append(deepcopy(v["ltp"]["entities"][0])),
    lambda v: v["ltp"]["designations"].append({"id": "second-goal", "entity_id": "new", "role": "goal"}),
    lambda v: v["ltp"].update(changes=[{"id": "change", "unknown_history": True}]),
    lambda v: v["ltp"]["assumptions"][0].update(relationship_id="missing"),
    lambda v: v["ltp"]["assessments"][0].update(depends_on=["missing"]),
])
def test_invalid_or_ambiguous_import_is_rejected_before_case_creation(tmp_path, mutation):
    value = legacy()
    mutation(value)
    source = source_file(tmp_path, value)
    with pytest.raises(InvalidCase):
        convert(source, tmp_path / "case", tmp_path / "case.reasoncase")
    assert not (tmp_path / "case").exists() and not (tmp_path / "case.reasoncase").exists()


def test_duplicate_yaml_keys_and_existing_destinations_are_rejected(tmp_path):
    with pytest.raises(InvalidCase, match="Duplicate"):
        read_ltp(b'ltp: {}\nltp: {}\n')
    source = source_file(tmp_path)
    store = tmp_path / "case"
    store.mkdir()
    marker = store / "keep.txt"
    marker.write_text("unchanged")
    with pytest.raises(InvalidCase):
        convert(source, store, tmp_path / "case.reasoncase")
    assert marker.read_text() == "unchanged" and len(list(store.iterdir())) == 1
