"""Build a goal whose history tells a story, one saved revision per chapter.

A story file (``stories/*.yaml``) lists chapters in order: when, who, the words
they actually wrote, and what those words changed in the trees and the loop.
Each chapter goes through the ordinary use cases: the words are retained as the
speaker's literal input, the chapter's source is attached, and a one-use,
deterministic proposal records the chapter's changes citing both. So the
History, Your words and Trees views read exactly as they would for a goal that
grew this way, and the engine validates every step.

The adapter adds no reasoning of its own; the story file is the authority on
what each chapter changed, and it says which parts are an editor's reading.
"""

from copy import deepcopy
from importlib.resources import as_file, files
from pathlib import Path

import yaml

from reason_commons.adapters.ltp_trees import read_trees
from reason_commons.domain.model import RELATIONS, ROLES, require

STORY_VERSION = "story/1"


def load_story(name="second-renaissance"):
    return yaml.safe_load(files("reason_commons.adapters").joinpath(f"stories/{name}.yaml").read_text("utf-8"))


class FixedClock:
    """The time each chapter happened, so revisions carry their real dates."""

    def __init__(self, value):
        self.value = value

    def now(self):
        return self.value


class StoryState:
    """Story identifiers and the record references they currently stand for."""

    def __init__(self):
        self.refs, self.alias, self.links, self.goal = {}, {}, set(), None
        self.test = None

    def resolve(self, key):
        while key in self.alias:
            key = self.alias[key]
        require(key in self.refs, f"The story refers to {key!r} before it exists or after it was withdrawn")
        return key

    def ref(self, key):
        return self.refs[self.resolve(key)]

    def rename(self, old, new):
        self.alias[old] = new
        self.links = {tuple(new if part == old else part for part in link[:2]) + link[2:] for link in self.links}

    def drop(self, key):
        del self.refs[key]
        self.links = {link for link in self.links if key not in link[:2]}


class Chapter:
    """A one-use proposal adapter for one chapter of a story."""

    def __init__(self, chapter, state, source_ref, model=None):
        self.chapter, self.state, self.source_ref, self.model = chapter, state, source_ref, model
        self.version = f"{STORY_VERSION}/{chapter['date']}"
        self.calls, self.keys = 0, []

    def propose(self, request):
        self.calls += 1
        require(self.calls == 1, "A chapter applies once")
        chapter, state = self.chapter, self.state
        cite = [request["input"]["request_id"], self.source_ref]
        updates, keys = [], []
        known = {}  # story ids created in this chapter -> temporary ids
        replacing = {}  # story ids created in this chapter -> the earlier id each replaces

        def update(kind, data, key=None):
            temp = f"temp_{kind}_{len(updates)}"
            updates.append({"operation": "record_" + kind, "temporary_id": temp, "data": data,
                            "source_refs": cite[:]})
            keys.append(key)
            return temp

        def target(key):
            if key in known:
                return known[key]
            return state.ref(key)

        def tree_of(key):
            return trees[key] if key in trees else self._tree(key)

        trees = {}

        def claim(key, tree, role, statement, basis=None, replaces=None):
            data = {"tree": tree, "role": role, "statement": statement}
            if basis:
                data["basis"] = basis
            if replaces:
                data["replaces"] = state.ref(replaces)
                replacing[key] = state.resolve(replaces)
            known[key] = update("claim", data, ("claim", key, replaces))
            trees[key] = tree

        def link(source, end, relation, assumption=None):
            key = (canon(source), canon(end), relation)
            if key in state.links or key in made:
                return
            made.add(key)
            tree = tree_of(source)
            require(tree == tree_of(end), f"Link {source} -> {end} crosses trees")
            data = {"tree": tree, "relation": relation, "from_ref": target(source), "to_ref": target(end)}
            if assumption:
                data["assumption"] = assumption
            update("link", data, ("link", key))

        made = set()

        def canon(key):
            """Links are compared by the identity a claim had before this chapter reworded it."""
            if key in replacing:
                return replacing[key]
            return key if key in known else state.resolve(key)

        if chapter.get("goal"):
            goal = chapter["goal"]
            temp = update("goal", {"statement": goal["statement"], "scope": None, "horizon": None,
                                   "measure": goal.get("measure"), "baseline": None, "protections": []},
                          ("goal", None, None))
            known["__goal__"] = temp
        for item in chapter.get("reword", []):
            old = state.resolve(item["id"])
            claim(item["new"], self._tree(old), self._role(old, request), item["statement"], replaces=old)
        for item in chapter.get("add", []):
            claim(item["id"], item["tree"], item["role"], item["statement"], item.get("basis"))
        notes = list(chapter.get("notes", []))
        if self.model:
            value, roles, replaces = self.model
            entities = {e["id"]: e for e in value["entities"]}
            for entity in value["entities"]:
                given = roles.get(entity["id"], [])
                role = next((r for r in given if entity["tree"] in ROLES.get(r, ())), "observation")
                claim(entity["id"], entity["tree"], role, entity["statement"], replaces=replaces.get(entity["id"]))
            assumptions = {}
            for assumption in value["assumptions"]:
                assumptions.setdefault(assumption.get("relationship_id"), []).append(assumption["statement"])
            for relation in value["relationships"]:
                ends = relation["from_entity_ids"] + [relation["to_entity_id"]]
                if (relation["kind"] not in RELATIONS or len(relation["from_entity_ids"]) > 1
                        or any(entities[e]["tree"] != relation["tree"] for e in ends)):
                    notes.append(f"From the July model: relationship {relation['id']} ({relation['kind']}) is "
                                 "kept as a note because the trees cannot draw it.")
                    continue
                link(relation["from_entity_ids"][0], relation["to_entity_id"], relation["kind"],
                     " · ".join(assumptions.pop(relation["id"], [])) or None)
        for item in chapter.get("links", []):
            link(item["from"], item["to"], item["relation"], item.get("assumption"))
        for item in chapter.get("withdraw", []):
            update("retraction", {"target_ref": state.ref(item["id"]), "reason": item["reason"]},
                   ("withdraw", state.resolve(item["id"]), None))
        for text in notes:
            update("note", {"text": text, "basis": "participant_report"}, None)
        loop = chapter.get("loop") or {}
        goal_ref = known.get("__goal__") or state.goal
        if loop.get("test"):
            test = loop["test"]
            data = {"statement": test["statement"], "goal_ref": goal_ref, "scope": test.get("scope"),
                    "forecast": deepcopy(test["forecast"]), "stop_condition": test.get("stop_condition"),
                    "review_date": test.get("review_date"),
                    "claim_ref": target(test["carries_out"]) if test.get("carries_out") else None}
            known["__test__"] = update("test", data, ("test", None, None))
        if loop.get("action"):
            action = loop["action"]
            update("action", {"statement": action["statement"], "test_ref": known["__test__"],
                              "owner": action.get("owner"), "authority": None,
                              "execution": action.get("execution", "planned"),
                              "expected_state_attainment": "pending"}, None)
        intervention = {"kind": "recommendation" if chapter.get("final") else "question",
                        "purpose": "story", "decision": chapter["title"],
                        "primary_prompt": chapter["question"],
                        "rationale": " ".join((chapter.get("why") or chapter["summary"]).split()),
                        "required_context_refs": [], "options": []}
        if goal_ref:
            intervention["goal_ref"] = goal_ref
        self.keys = keys
        return {"schema_version": "1", "delivery_profile": "p2", "request_id": request["input"]["request_id"],
                "base_revision": request["input"]["base_revision"], "intervention": intervention,
                "proposed_updates": updates}

    def _tree(self, key):
        return self.state.trees[self.state.resolve(key)]

    def _role(self, key, request):
        return self.state.roles[self.state.resolve(key)]

    def settle(self, records):
        """After saving: learn the references the engine gave this chapter's records."""
        state = self.state
        new = records[-(len(self.keys) + 1):-1]
        require(len(new) == len(self.keys), "The chapter was not saved as proposed")
        for record, key in zip(new, self.keys):
            if key is None:
                continue
            kind = key[0]
            if kind == "goal":
                state.goal = record["ref"]
            elif kind == "test":
                state.test = record["ref"]
            elif kind == "claim":
                _, story_id, replaced = key
                if replaced:
                    old = state.resolve(replaced)
                    state.refs.pop(old, None)
                    state.rename(old, story_id)
                state.refs[story_id] = record["ref"]
                state.trees[story_id] = record["data"]["tree"]
                state.roles[story_id] = record["data"]["role"]
            elif kind == "link":
                state.links.add(key[1])
            elif kind == "withdraw":
                state.drop(key[1])


class Narrator:
    """The consultant for the whole build: each chapter's one-use proposal in turn."""

    def __init__(self):
        self.chapter = None

    @property
    def version(self):
        return self.chapter.version

    def propose(self, request):
        return self.chapter.propose(request)


def build_story(path, story=None):
    """Create the story's goal at path (which must not exist); return path."""
    from reason_commons.bootstrap import create_case
    story = story or load_story()
    chapters = story["chapters"]
    clock, narrator, state = FixedClock(chapters[0]["date"]), Narrator(), StoryState()
    state.trees, state.roles = {}, {}
    with create_case(path, story["name"], consultant=narrator, clock=clock) as app:
        for chapter in chapters:
            clock.value = chapter["date"]
            model = None
            if chapter.get("model"):
                source = files("reason_commons.adapters").joinpath(chapter["model"]["file"])
                with as_file(source) as local:
                    value, roles = read_trees(Path(local).read_bytes())
                model = (value, roles, chapter["model"].get("replaces", {}))
            content = (chapter["words"].rstrip() + "\n\n" + chapter["source"] + "\n"
                       + chapter.get("where", "") + ("\n" + chapter["words_note"] if chapter.get("words_note")
                                                      else "")).encode()
            source_ref = app.add_source(chapter["source"], content, chapter["speaker"])
            narrator.chapter = Chapter(chapter, state, source_ref, model)
            declarations = {}
            owner = ((chapter.get("loop") or {}).get("action") or {}).get("owner")
            if owner:
                declarations["ownership"] = [owner]
            if chapter.get("observed"):
                declarations["evidence"] = ["observed"]
            target = app.workspace()["target"]
            result = app.submit(chapter["words"], chapter["speaker"], target["base_revision"],
                                target["response_target"], declarations=declarations)
            require(result["status"] == "saved",
                    f"Chapter {chapter['title']!r} was not saved: {result.get('message', result['status'])}")
            narrator.chapter.settle(app.inspect()["case"]["records"])
        target = app.workspace()["target"]
        app.checkpoint({"view": "next", "focus": "browse", "draft": "", "caret": 0, "speaker": story["reader"],
                        "response_target": target["response_target"], "base_revision": target["base_revision"]})
    return path


def chapter_index(story=None):
    """Revision number -> chapter, for the story strip (revision 0 is the empty goal)."""
    story = story or load_story()
    return {number: chapter for number, chapter in enumerate(story["chapters"], start=1)}
