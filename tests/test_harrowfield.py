"""The Harrowfield goal the guided tour opens: built from its story file through the application, packaged, and
shaped so that each tree says what the tour points at."""

from importlib.resources import files

import pytest

from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.adapters.story import build_story, load_story
from reason_commons.adapters.timeline import revision_changes
from reason_commons.adapters.trees import cloud_lines, reach
from reason_commons.bootstrap import import_case, open_case
from tests.test_story import comparable

ARCHIVE = "stories/harrowfield.reasoncase"
CORE = ("Discharge is decided on the day, late in a sickest-first round, and preparation to leave starts only after "
        "that decision")


@pytest.fixture(scope="module")
def harrowfield(tmp_path_factory):
    path = tmp_path_factory.mktemp("harrowfield") / "case"
    import_case(str(files("reason_commons.adapters").joinpath(ARCHIVE)), str(path)).close()
    return path


def trees_of(path):
    with open_case(path, writable=False) as case:
        return {tree["tree"]: tree for tree in case.workspace(view="trees")["trees"]}


def test_the_story_file_builds_the_packaged_goal(tmp_path, harrowfield):
    story = load_story("harrowfield")
    built = build_story(tmp_path / "fresh", story)
    with open_case(built, writable=False) as fresh, open_case(harrowfield, writable=False) as packaged:
        assert fresh.workspace()["revision"] == len(story["chapters"])
        # The package is the story file, built: rerun scripts/build_story.py harrowfield after editing it.
        assert comparable(fresh) == comparable(packaged)


def test_every_statement_in_a_story_file_is_whole():
    """In a YAML flow mapping an unquoted comma ends the value, so a statement would be cut short silently."""
    for name in ("harrowfield", "second-renaissance"):
        for chapter in load_story(name)["chapters"]:
            for item in chapter.get("add", []):
                assert set(item) <= {"id", "tree", "role", "statement", "basis"}, (name, item)
            for item in chapter.get("links", []):
                assert set(item) <= {"from", "to", "relation", "assumption"}, (name, item)


def test_the_trees_say_what_the_tour_points_at(harrowfield):
    trees = trees_of(harrowfield)
    assert {name: len(tree["claims"]) for name, tree in trees.items()} == {
        "goal": 17, "current_reality": 21, "conflict": 5, "future_reality": 30, "prerequisite": 21,
        "transition": 30}
    # Many complaints, one cause: a single statement reaches all ten undesirable effects, and it is the one
    # marked as the likely constraint.
    crt = trees["current_reality"]
    whole = [c for c in crt["claims"] if reach(crt, c["ref"]) == "leads to all 10 undesirable effects"]
    assert [(c["statement"], c["role"]) for c in whole] == [(CORE, "critical_root_cause")]
    # The Cloud is complete, so the workspace draws its five boxes, wide or at 80 columns.
    assert cloud_lines(trees["conflict"], 116) and cloud_lines(trees["conflict"], 71)
    assumptions = [link["assumption"] for link in trees["conflict"]["links"]]
    assert "Only the consultant's morning round can trigger a discharge" in assumptions
    # Occupancy is a measure, not a condition: nothing accepted in the Goal Tree says the hospital must be full.
    assert not any("occupancy" in c["statement"].lower() for c in trees["goal"]["claims"])
    # Each harm has a trim that challenges it, and a trim never claims to lead anywhere.
    frt = trees["future_reality"]
    trims = {link["from"] for link in frt["links"] if link["relation"] == "challenges"}
    harms = {c["ref"] for c in frt["claims"] if c["role"] == "undesirable_effect"}
    assert len(trims) == 6 and {link["to"] for link in frt["links"] if link["relation"] == "challenges"} == harms
    assert all(reach(frt, ref) is None for ref in trims)
    # The step the tour's loop tests, with what it expects to see.
    statements = {c["statement"] for c in trees["transition"]["claims"]}
    assert "Full kit ready by 08:00 for at least 80% of next-day discharges, by the morning checklist" in statements


def test_two_proposals_wait_and_the_guide_asks_for_the_first_test(harrowfield):
    with open_case(harrowfield, writable=False) as case:
        backlog = case.workspace(view="backlog")["backlog"]
        state = case.inspect()["case"]
        question = case.workspace()["question"]["data"]
    # Graham's condition and Joy's correction, each a statement and the link that joins it to its tree.
    assert [entry["entry"] for entry in backlog] == ["proposal"] * 4
    assert backlog[0]["summary"] == "Keep occupancy at 95% or more"
    assert backlog[2]["summary"].startswith("Pharmacy starts on take-home medicines")
    assert state["membership"]["acceptance"] == "review"
    assert question["purpose"] == "guided:test_change" and question["decision"] == "Choose a test"
    goals = [r for r in state["records"] if r["kind"] == "goal"]
    assert len(goals) == 1 and goals[0]["data"]["measure"] and len(goals[0]["data"]["protections"]) == 2
    # The loop has not started: the person taking the tour runs it.
    assert not [r for r in state["records"] if r["kind"] in ("test", "action", "observation", "review")]


def test_the_guide_carries_on_from_the_handover(tmp_path):
    path = tmp_path / "copy"
    with import_case(str(files("reason_commons.adapters").joinpath(ARCHIVE)), str(path),
                     consultant=GuidedConsultant()) as case:
        target = case.workspace()["target"]
        result = case.submit("At 15:00 the registrar confirms tomorrow's likely discharges.", "Ruth Okonjo",
                             target["base_revision"], target["response_target"])
        assert result["status"] == "saved"
        asked = case.workspace()["question"]["data"]
    # The first answer was taken as the change to test, not kept as a note: the guide asks for the forecast.
    assert asked["purpose"] == "guided:test_forecast"
    assert asked["primary_prompt"].startswith("Your change: \"At 15:00 the registrar")


def test_every_voice_is_heard(harrowfield):
    with open_case(harrowfield, writable=False) as case:
        entries = revision_changes(case.history()["revisions"], case.sources()["sources"])
    speakers = {entry["speaker"] for entry in entries[1:] if entry.get("text")}
    assert {"Ruth Okonjo", "Dr Samir Haddad", "Joy Mensah", "Dr Helen Marsh", "Graham Teller",
            "Director of Nursing", "Pharmacy", "County social care", "Junior doctors"} <= speakers
