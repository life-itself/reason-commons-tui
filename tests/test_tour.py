"""The guided tour's engine: its script, where a person is in it, how a fresh copy of its goal is brought forward
to a part, and the part remembered between visits. Nothing here draws a screen; tests/test_tour_view.py walks the
tour in the terminal."""

import copy
from importlib.resources import files

import pytest

from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.adapters.tour import (BANNED, PAGE_ROWS, Progress, Tour, TourClock, accepted_kinds, check,
                                          decided, guided_step, lines, load_tour, page_rows, prepare, words)
from reason_commons.adapters.trees import TREE_TITLES
from reason_commons.bootstrap import import_case, open_case

ARCHIVE = "stories/harrowfield.reasoncase"
PLAYER = "Ruth Okonjo"


@pytest.fixture(scope="module")
def script():
    return load_tour("harrowfield")


@pytest.fixture(scope="module")
def harrowfield(tmp_path_factory):
    path = tmp_path_factory.mktemp("tour") / "case"
    import_case(str(files("reason_commons.adapters").joinpath(ARCHIVE)), str(path)).close()
    return path


def fresh(tmp_path):
    """A throwaway copy of the tour's goal, as the tour opens one, with the built-in guide asking."""
    return import_case(str(files("reason_commons.adapters").joinpath(ARCHIVE)), str(tmp_path / "copy"),
                       consultant=GuidedConsultant())


def facts(**values):
    return values


# ----- the script ---------------------------------------------------------------------------------------------
def test_the_script_names_only_what_the_workspace_has(script, harrowfield):
    pytest.importorskip("textual")
    from reason_commons.adapters.tui import VIEW_LABELS

    check(script, views=[key for key, _ in VIEW_LABELS])
    assert script["story"] == "harrowfield" and script["player"] == PLAYER
    with open_case(harrowfield, writable=False) as case:
        trees = {tree["tree"]: {c["statement"] for c in tree["claims"]}
                 for tree in case.workspace(view="trees")["trees"]}
        state = case.inspect()["case"]
        membership = case.workspace(view="backlog")["membership"]
    # Every tree in the tour, once each, in the method's order, each part asking its tree's own question.
    toured = [part["tree"] for part in script["parts"] if part.get("tree")]
    assert toured == list(TREE_TITLES)
    for part in script["parts"]:
        for beat in part.get("beats", []):
            # A statement the tour points at is one the part's tree holds, word for word.
            for wanted in ((beat.get("button") or {}).get("select"), (beat.get("until") or {}).get("selected")):
                if wanted:
                    assert wanted in trees[part["tree"]], (part["id"], wanted)
    # The two decisions the tour asks for are the two waiting in the goal.
    assert decided(script, state["records"], membership) == {"occupancy": "proposed", "pharmacy": "proposed"}


def test_every_word_fits_and_none_is_jargon(script):
    shown = list(words(script))
    assert len(shown) > 100
    for text in shown:
        assert not BANNED.search(text), text
    for part in script["parts"]:
        for beat in part.get("beats", []):
            assert lines(beat["say"]) <= 3
        steps = Tour(script, part["id"]).steps()
        for step in steps:
            if step["kind"] == "page":
                assert page_rows(step["page"]) <= PAGE_ROWS
            if step["kind"] == "closing":
                assert page_rows(step["closing"], closing=True) <= PAGE_ROWS


@pytest.mark.parametrize("change, complaint", [
    (lambda s: s["parts"][1]["pages"][0].update(text="Shuffle the cards."), "'cards'"),
    (lambda s: s["parts"][1]["pages"][0].update(text="The Cards on the table."), "'Cards'"),
    (lambda s: s["parts"][3]["pages"][0].update(text="The CRT finds the cause."), "'CRT'"),
    (lambda s: s["parts"][2]["closing"].update(key="Read every NC."), "'NC'"),
    (lambda s: s["parts"][2]["beats"][0].update(say="word " * 60), "longer than the strip"),
    (lambda s: s["parts"][2]["pages"][0].update(text="word " * 400), "longer than an 80 by 24 screen"),
    (lambda s: s["parts"][4]["closing"].update(key="word " * 60), "closing page is too long"),
    (lambda s: s["parts"][2].update(title="Why the goal?"), "its tree's own question"),
    (lambda s: s["parts"][2]["beats"][0].update(until={"tree": "cause_and_effect"}), "unknown tree"),
    (lambda s: s["parts"][2]["beats"][3].update(until={"decided": "beds"}), "unknown proposal"),
    (lambda s: s["parts"][2]["beats"][2]["button"].update(view="queue"), "unknown view"),
    (lambda s: s["parts"][2]["beats"][2].update(until={"clicked": "x"}), "waits for something unclear"),
    (lambda s: s["examples"].pop("observe"), "needs an example answer"),
    (lambda s: s["parts"][2].pop("closing"), "needs a closing koan"),
    (lambda s: s["parts"][0]["pages"][0]["choices"].append(["jump", "Jump", ""]), "unknown choice"),
    (lambda s: s["parts"][8]["loop"].update(until="observe"), "loop must end"),
])
def test_a_script_the_workspace_cannot_show_is_refused(script, change, complaint):
    broken = copy.deepcopy(script)
    change(broken)
    with pytest.raises(ValueError, match=complaint):
        check(broken, views=["next", "backlog", "goal", "trees", "tests", "history"])


# ----- where a person is ----------------------------------------------------------------------------------------
def test_next_and_back_walk_every_step_and_number_the_nine_parts(script):
    tour = Tour(script)
    assert tour.first() and tour.on_page and tour.status() == "Tour · The hospital"
    assert tour.back().first()  # nothing before the first page
    seen = [(tour.part["id"], tour.step["kind"])]
    while not tour.last():
        seen.append((tour.next().part["id"], tour.step["kind"]))
    assert tour.next().last()  # nothing after the last page
    assert [part["id"] for part in tour.numbered] == [
        "workspace", "goal-tree", "current-reality", "cloud", "future-reality", "prerequisite", "transition",
        "monday", "day-three"]
    # Every numbered part opens with a page and closes with its koan; the loop parts hand over to the guide.
    for part in tour.numbered:
        kinds = [kind for where, kind in seen if where == part["id"]]
        assert kinds[0] == "page" and kinds[-1] == "closing", part["id"]
        assert ("loop" in kinds) == (part["id"] in ("monday", "day-three"))
    assert ("workspace", "how") in seen
    # Back retraces the same steps.
    back = [(tour.part["id"], tour.step["kind"])]
    while not tour.first():
        back.append((tour.back().part["id"], tour.step["kind"]))
    assert back[::-1] == seen
    tour.goto("cloud")
    assert tour.status() == "Tour · Part 4 of 9 · What conflict keeps us stuck?" and tour.at == 0
    assert tour.back().part["id"] == "current-reality" and tour.step["kind"] == "closing"


def at_beat(script, part, n):
    tour = Tour(script, part)
    while tour.step["kind"] != "beat":
        tour.next()
    for _ in range(n):
        tour.next()
    return tour


def test_a_waiting_beat_moves_on_when_it_happens_but_never_onto_a_page(script):
    tour = at_beat(script, "goal-tree", 0)
    assert tour.button() == {"label": "Open it", "tree": "goal"}
    assert not tour.observe(facts(view="trees", tree="current_reality"))
    # Opening the Goal Tree is what the beat waits for: the next beat speaks.
    assert tour.observe(facts(view="trees", tree="goal"))
    assert tour.step["beat"]["until"] == {"selected": "No one occupies a bed they no longer need"}
    # A statement chosen in another tree is not the one asked for.
    assert not tour.observe(facts(view="trees", tree="current_reality",
                                  selected="No one occupies a bed they no longer need"))
    tour.observe(facts(view="trees", tree="goal", selected="No one occupies a bed they no longer need"))
    assert tour.step["beat"]["until"] == {"view": "backlog"}
    tour.observe(facts(view="backlog"))
    # The decision's beat stays to say how it turned out, in words for each outcome.
    assert tour.step["beat"]["until"] == {"decided": "occupancy"} and tour.button() is None
    waiting = tour.say()
    tour.observe(facts(view="backlog", decided={"occupancy": "proposed"}))
    assert tour.say() == waiting and not tour.met()
    assert tour.observe(facts(view="backlog", decided={"occupancy": "rejected"}))
    assert tour.met() and tour.say().startswith("Rejected.") and tour.step["kind"] == "beat"
    tour.observe(facts(view="backlog", decided={"occupancy": "accepted"}))
    assert tour.say().startswith("Accepted.")
    # Next opens the closing page; nothing else does.
    assert tour.next().step["kind"] == "closing"

    # The last beat before a page stays on its beat when met.
    short = copy.deepcopy(script)
    short["parts"][Tour(script, "day-three").index]["beats"].pop()
    tour = at_beat(short, "day-three", 0)
    tour.observe(facts(view="tests"))
    assert tour.step["kind"] == "beat" and tour.met() and tour.button() is None
    assert tour.next().step["kind"] == "closing"


def test_a_beat_already_done_waits_for_next(script):
    # Going back to a beat whose condition already holds shows it done; the strip does not run ahead.
    tour = at_beat(script, "current-reality", 0)
    tour.observe(facts(view="trees", tree="current_reality"))
    assert tour.step["beat"]["until"] == {"decided": "pharmacy"}
    tour.back()
    assert tour.met() and tour.button() is None
    tour.observe(facts(view="trees", tree="current_reality", decided={"pharmacy": "accepted"}))
    assert tour.step["beat"]["until"] == {"tree": "current_reality"}
    # A beat reached when it already holds says so at once.
    tour.next()
    assert tour.met() and tour.say().startswith("Accepted, in Joy's words")


def test_the_loop_speaks_to_whatever_the_guide_asks(script):
    tour = Tour(script, "monday")
    tour.next()
    loop = script["parts"][tour.index]["loop"]
    assert tour.step["kind"] == "loop" and tour.button() is None
    tour.observe(facts(view="next", asked="test_forecast"))
    assert tour.say() == loop["test_forecast"]
    tour.observe(facts(view="next", asked="test_stop", waiting=True))
    assert tour.say() == loop["waiting"]
    tour.observe(facts(view="next", asked="action", accepted={"goal", "test"}))
    assert tour.say() == loop["action"] and not tour.met()
    assert tour.observe(facts(view="next", asked="observe", accepted={"goal", "test", "action"}))
    assert tour.met() and tour.say() == loop["done"]
    # The loop never leaves by itself: Next does.
    assert tour.step["kind"] == "loop"


# ----- the goal, brought forward ------------------------------------------------------------------------------------
def test_prepare_answers_as_ruth_up_to_a_part_and_leaves_the_two_decisions(script, tmp_path):
    with fresh(tmp_path) as case:
        assert guided_step(case.workspace()["question"]) == "test_change"
        assert "action" not in accepted_kinds(case)
        steps = prepare(case, script, "action", PLAYER)
        assert steps > 4 and {"test", "action"} <= accepted_kinds(case)
        assert prepare(case, script, "action", PLAYER) == 0  # already there: nothing more is saved
        revision = case.workspace()["revision"]
        test = next(r for r in case.inspect()["case"]["records"] if r["kind"] == "test")
        # The forecast is Ruth's, sealed as the test's own: what Thursday's review compares the result with.
        assert "8 in 10" in test["data"]["forecast"][0]["expected"]
        assert guided_step(case.workspace()["question"]) == "observe"

        prepare(case, script, "review", PLAYER)
        assert {"observation", "review"} <= accepted_kinds(case)
        assert case.workspace()["revision"] > revision
        state = case.inspect()["case"]
        membership = case.workspace(view="backlog")["membership"]
        assert decided(script, state["records"], membership) == {"occupancy": "proposed", "pharmacy": "proposed"}
        sources = case.sources()["sources"]
        speakers = {sources[q]["speaker"] for r in state["records"] if r["kind"] in ("test", "action", "review")
                    for q in r["source_refs"]}
        assert speakers == {PLAYER}


def test_prepare_stops_rather_than_guess(script, tmp_path):
    silent = copy.deepcopy(script)
    del silent["examples"]["test_forecast"]
    with fresh(tmp_path) as case:
        with pytest.raises(ValueError, match="test_forecast"):
            prepare(case, silent, "action", PLAYER)
        with pytest.raises(RuntimeError, match="did not reach"):
            prepare(case, script, "action", PLAYER, limit=2)


# ----- time and memory ----------------------------------------------------------------------------------------------
def test_the_story_clock_follows_the_parts(script):
    clock = TourClock(script)
    assert clock.now() == "2026-01-09T16:30:00+00:00"
    clock.at(Tour(script, "monday").part)
    assert clock.now() == "2026-01-12T09:00:00+00:00"
    clock.at(Tour(script, "day-three").part)
    assert clock.now() == "2026-01-15T08:45:00+00:00"
    # Back to an earlier part, the clock stays where the story got to.
    clock.at(Tour(script, "goal-tree").part)
    assert clock.now() == "2026-01-15T08:45:00+00:00"
    # Monday's answers, put in to get Thursday ready, are dated Monday.
    with clock.during(Tour(script, "monday").part):
        assert clock.now() == "2026-01-12T09:00:00+00:00"
    assert clock.now() == "2026-01-15T08:45:00+00:00"


def test_moving_into_a_part_sets_the_clock_and_remembers_the_part(script, tmp_path):
    progress, clock = Progress(tmp_path / "tour.yaml"), TourClock(script)
    tour = Tour(script, "transition", progress=progress, clock=clock)
    assert progress.reached("harrowfield") == ("transition", False)
    while tour.part["id"] == "transition":
        tour.next()
    assert progress.reached("harrowfield") == ("monday", False) and clock.now().startswith("2026-01-12")
    tour.goto("epilogue")
    assert progress.reached("harrowfield") == ("epilogue", True)


def test_the_part_reached_is_remembered_outside_every_goal(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    progress = Progress()
    assert progress.path == tmp_path / "state" / "reason-commons" / "tour.yaml"
    assert progress.reached("harrowfield") == (None, False)
    assert progress.save("harrowfield", "cloud")
    assert Progress().reached("harrowfield") == ("cloud", False)
    assert progress.save("harrowfield", "epilogue", finished=True)
    assert Progress().reached("harrowfield") == ("epilogue", True)
    # A damaged file is a tour not yet taken, and a folder that cannot be written loses only the bookmark.
    progress.path.write_text("- not\n- a mapping\n", encoding="utf-8")
    assert progress.reached("harrowfield") == (None, False)
    blocked = tmp_path / "file"
    blocked.write_text("", encoding="utf-8")
    assert not Progress(blocked / "tour.yaml").save("harrowfield", "cloud")
