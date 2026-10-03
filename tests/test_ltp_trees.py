"""LTP 1.0 trees come in through the ordinary use cases and go back out unchanged."""

import pytest
import yaml

from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.adapters.ltp_trees import export_trees, import_trees, ltp_document
from reason_commons.adapters.sample import build_sample
from reason_commons.adapters.trees import plain, trees_lines
from reason_commons.bootstrap import create_case, open_case


DOCUMENT = {"ltp": {
    "schema_version": "1.0", "project_id": "delivery", "title": "Shorten delivery",
    "entities": [
        {"id": "g", "tree": "goal", "statement": "Committed work is delivered within two weeks."},
        {"id": "csf", "tree": "goal", "statement": "Work in progress stays below capacity."},
        {"id": "ude", "tree": "current_reality", "statement": "Delivery takes far longer than the work."},
        {"id": "root", "tree": "current_reality", "statement": "Work is committed without regard to capacity."},
        {"id": "other", "tree": "current_reality", "statement": "Priorities change weekly."},
        {"id": "act", "tree": "transition", "statement": "Move commitment to the week of work."},
    ],
    "designations": [
        {"id": "d-g", "entity_id": "g", "role": "goal"},
        {"id": "d-csf", "entity_id": "csf", "role": "critical_success_factor", "parent_designation_id": "d-g"},
        {"id": "d-ude", "entity_id": "ude", "role": "undesirable_effect"},
        {"id": "d-root", "entity_id": "root", "role": "root_cause"},
        {"id": "d-act", "entity_id": "act", "role": "transition_action"},
    ],
    "relationships": [
        {"id": "r1", "tree": "goal", "kind": "necessary_for", "from_entity_ids": ["csf"], "to_entity_id": "g"},
        {"id": "r2", "tree": "current_reality", "kind": "causes", "from_entity_ids": ["root"], "to_entity_id": "ude"},
        {"id": "r3", "tree": "current_reality", "kind": "causes", "from_entity_ids": ["root", "other"],
         "to_entity_id": "ude"},
    ],
    "assumptions": [{"id": "a1", "relationship_id": "r2", "statement": "Nothing else limits when work starts."}],
    "assessments": [{"id": "as1", "kind": "critical_root_cause", "tree": "current_reality",
                     "statement": "Committing without capacity explains the delay.", "subject_ids": ["d-root"],
                     "depends_on": ["r2"]}],
    "changes": []}}


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "delivery.ltp.yaml"
    path.write_text(yaml.safe_dump(DOCUMENT))
    return path


def test_import_into_a_fresh_case_draws_the_trees_and_keeps_what_they_cannot_hold(tmp_path, source):
    case = tmp_path / "case"
    create_case(case, "Delivery").close()
    summary = import_trees(case, source, "David")
    assert summary == {"claims": 6, "links": 2, "notes": 2, "revision": 1}
    with open_case(case, writable=False) as app:
        workspace = app.workspace(view="trees")
        records = app.inspect()["case"]["records"]
        sources = app.sources()["sources"]
    trees = {t["tree"]: t for t in workspace["trees"]}
    assert trees["current_reality"]["links"][0]["assumption"] == "Nothing else limits when work starts."
    # The unmarked entity is drawn as an observation rather than guessed at.
    assert [c["role"] for c in trees["current_reality"]["claims"]] == ["undesirable_effect", "root_cause", "observation"]
    notes = [r["data"]["text"] for r in records if r["kind"] == "note"]
    assert any("r3" in n and "several premises" in n for n in notes)
    assert any("as1" in n and "not one reached here" in n for n in notes)
    # A fresh case takes the tree's goal as its own; every claim cites the attached file.
    assert [r["data"]["statement"] for r in records if r["kind"] == "goal"] == ["Committed work is delivered within two weeks."]
    file_ref = next(k for k, v in sources.items() if v.get("name") == "delivery.ltp.yaml")
    assert all(r["source_refs"] == [file_ref] for r in records if r["kind"] in {"claim", "link", "note"})
    drawing = plain(trees_lines(workspace["trees"], 80, only="current_reality"))
    assert "└─ because ─ ROOT CAUSE\n   Work is committed without regard to capacity.\n" \
           "   assuming Nothing else limits when work starts." in drawing


def test_import_mid_loop_keeps_the_current_question(tmp_path, source):
    case = tmp_path / "case"
    create_case(case, "Delivery").close()
    with open_case(case, consultant=GuidedConsultant()) as app:
        app.submit("Deliver within two weeks", "David", **app.workspace()["target"])
        before = app.workspace()["question"]["data"]
    import_trees(case, source, "David")
    with open_case(case, consultant=GuidedConsultant()) as app:
        after = app.workspace()["question"]["data"]
        assert after["purpose"] == before["purpose"] == "guided:goal_measure"
        assert after["primary_prompt"].endswith(before["primary_prompt"])
        # The guide carries on from the same step.
        app.submit("Days from commitment to delivery", "David", **app.workspace()["target"])
        assert app.workspace()["question"]["data"]["purpose"] == "guided:goal_protect"
        assert len([r for r in app.inspect()["case"]["records"] if r["kind"] == "goal"]) == 0


def test_export_round_trips(tmp_path, source):
    case, again = tmp_path / "case", tmp_path / "again"
    create_case(case, "Delivery").close()
    import_trees(case, source, "David")
    with open_case(case, writable=False) as app:
        first = app.workspace(view="trees")
    exported = tmp_path / "out.ltp.yaml"
    assert export_trees(first, exported) == {"claims": 6, "links": 2}
    with pytest.raises(ValueError):
        export_trees(first, exported)
    create_case(again, "Again").close()
    import_trees(again, exported, "David")
    with open_case(again, writable=False) as app:
        second = app.workspace(view="trees")
    shape = lambda w: [(t["tree"], [(c["role"], c["statement"]) for c in t["claims"]],
                        [(l["relation"], l["assumption"]) for l in t["links"]]) for t in w["trees"]]
    assert shape(first) == shape(second)
    assert ltp_document(second)["ltp"]["title"] == "Again"


def test_rejects_files_that_are_not_ltp(tmp_path):
    case = tmp_path / "case"
    create_case(case, "Delivery").close()
    bad = tmp_path / "bad.yaml"
    bad.write_text("title: not an ltp file\n")
    with pytest.raises(ValueError, match="no top-level ltp"):
        import_trees(case, bad, "David")
    with open_case(case, writable=False) as app:
        assert app.inspect()["case"]["revision"] == 0


def test_finished_example_has_all_six_trees(tmp_path):
    path = build_sample(tmp_path / "example")
    with open_case(path, writable=False) as app:
        trees = app.workspace(view="trees")["trees"]
        assert all(t["claims"] for t in trees)
        assert app.inspect()["cursor"]["view"] == "tests"


def test_command_line_draws_imports_and_exports(tmp_path, source):
    from tests.support import cli
    case = tmp_path / "case"
    create_case(case, "Delivery").close()
    result = cli("trees", case, "--import", source, "--speaker", "David")
    assert result.returncode == 0 and "6 statements and 2 links; 2 items kept as notes" in result.stdout
    drawing = cli("trees", case, "--width", "80").stdout
    assert "Goal Tree" in drawing and "└─ needs ─ CRITICAL SUCCESS FACTOR" in drawing
    assert "Current Reality Tree" in cli("show", case, "--view", "trees").stdout
    assert cli("trees", case, "--export", tmp_path / "out.ltp.yaml").returncode == 0
    assert yaml.safe_load((tmp_path / "out.ltp.yaml").read_text())["ltp"]["schema_version"] == "1.0"
