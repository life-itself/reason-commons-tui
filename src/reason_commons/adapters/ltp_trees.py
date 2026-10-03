"""Bring LTP 1.0 trees into a case, and write a case's trees back out.

Import goes through the ordinary use cases: the file is attached as a source,
a literal request is retained, and a deterministic, one-use proposal adapter
records one claim per entity and one link per relationship, citing the file.
The current question carries on unchanged. Anything the native trees cannot
hold (a joint premise group, a cross-tree link, an assessment) is kept as a
labelled note, so nothing in the file is silently dropped.

Export writes the trees as they stand now, in the same interchange format.
"""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import re

import yaml

from reason_commons.adapters.ltp_conversion import UniqueLoader
from reason_commons.domain.model import RELATIONS, ROLES, TREES, require, shape, string_list, text


IMPORT_REQUEST = "Bring in the trees from {name}"
SOURCE_ATTRIBUTION = "Imported LTP document; individual authorship is not inferred"


def read_trees(content):
    """Parse and check an LTP 1.0 document; return it with each entity's role."""
    require(isinstance(content, bytes) and len(content) <= 4 * 1024 * 1024, "Supply an LTP document up to 4 MiB")
    try:
        document = yaml.load(content.decode("utf-8"), Loader=UniqueLoader)
    except (yaml.YAMLError, UnicodeError):
        raise ValueError("The file is not valid YAML") from None
    require(isinstance(document, dict) and isinstance(document.get("ltp"), dict),
            "This is not an LTP file: it has no top-level ltp section")
    value = document["ltp"]
    require(str(value.get("schema_version", "")).startswith("1."), "Only LTP 1.x files can be read")
    for section in ("entities", "designations", "relationships", "assumptions", "assessments"):
        value.setdefault(section, [])
        require(isinstance(value[section], list), f"{section} must be a list")
    ids = set()
    for section in ("entities", "designations", "relationships", "assumptions", "assessments"):
        for row in value[section]:
            require(isinstance(row, dict), f"{section} entries must be objects")
            text(row.get("id"), "LTP ID")
            require(row["id"] not in ids, f"The ID {row['id']} is used twice")
            ids.add(row["id"])
    entities = {}
    for entity in value["entities"]:
        shape(entity, {"id", "tree", "statement", "provenance"}, {"id", "tree", "statement"}, "entity")
        text(entity["statement"], "statement")
        require(entity["tree"] in TREES, f"Unknown tree {entity['tree']!r}")
        entities[entity["id"]] = entity
    roles = {}
    for designation in value["designations"]:
        require(designation.get("entity_id") in entities, "A designation names an unknown entity")
        roles.setdefault(designation["entity_id"], []).append(designation.get("role"))
    for relation in value["relationships"]:
        shape(relation, {"id", "tree", "kind", "from_entity_ids", "to_entity_id", "logic"},
              {"id", "tree", "kind", "from_entity_ids", "to_entity_id"}, "relationship")
        string_list(relation["from_entity_ids"], "from_entity_ids")
        require(bool(relation["from_entity_ids"]) and all(
            ref in entities for ref in relation["from_entity_ids"] + [relation["to_entity_id"]]),
            "A relationship names an unknown entity")
    for assumption in value["assumptions"]:
        text(assumption.get("statement"), "assumption")
    return value, roles


class TreeImport:
    """A source-bound, one-use proposal: the file's trees as claims and links."""

    def __init__(self, value, roles, source_ref, source_hash, name):
        self.value, self.roles = deepcopy(value), deepcopy(roles)
        self.source_ref, self.source_hash, self.name = source_ref, source_hash, name
        self.version = "ltp-tree-import/1/source=" + source_hash
        self.calls = 0
        self.summary = {}

    def propose(self, request):
        self.calls += 1
        require(self.calls == 1, "An import applies once")
        refs = [self.source_ref]
        value, updates, kept = self.value, [], []
        entity_alias = {}

        def note(content):
            updates.append({"operation": "record_note", "temporary_id": f"temp_note_{len(kept)}",
                            "data": {"text": content, "basis": "participant_report"}, "source_refs": refs[:]})
            kept.append(content)

        for index, entity in enumerate(value["entities"]):
            alias = f"temp_claim_{index}"
            entity_alias[entity["id"]] = alias
            given = self.roles.get(entity["id"], [])
            role = next((r for r in given if entity["tree"] in ROLES.get(r, ())), "observation")
            if given and given != [role]:
                note(f"From {self.name}: {entity['id']} was designated {', '.join(map(str, given))}; "
                     f"it is drawn as {role} in the {entity['tree']} tree.")
            updates.append({"operation": "record_claim", "temporary_id": alias, "source_refs": refs[:],
                            "data": {"tree": entity["tree"], "role": role, "statement": entity["statement"]}})
        assumptions = {}
        for assumption in value["assumptions"]:
            assumptions.setdefault(assumption.get("relationship_id"), []).append(assumption["statement"])
        entities = {e["id"]: e for e in value["entities"]}
        links = 0
        for index, relation in enumerate(value["relationships"]):
            ends = relation["from_entity_ids"] + [relation["to_entity_id"]]
            reason = None
            if relation["kind"] not in RELATIONS:
                reason = f"its kind {relation['kind']!r} is not one the trees can draw"
            elif len(relation["from_entity_ids"]) > 1:
                reason = "it joins several premises, and joint premises arrive with the full causal tools"
            elif any(entities[e]["tree"] != relation["tree"] for e in ends):
                reason = "it crosses from one tree to another"
            elif relation["from_entity_ids"][0] == relation["to_entity_id"]:
                reason = "it links a statement to itself"
            if reason:
                note(f"From {self.name}: relationship {relation['id']} ({relation['kind']}) from "
                     f"{', '.join(relation['from_entity_ids'])} to {relation['to_entity_id']} is kept here "
                     f"as a note, because {reason}.")
                continue
            data = {"tree": relation["tree"], "relation": relation["kind"],
                    "from_ref": entity_alias[relation["from_entity_ids"][0]],
                    "to_ref": entity_alias[relation["to_entity_id"]]}
            if relation["id"] in assumptions:
                data["assumption"] = " · ".join(assumptions.pop(relation["id"]))
            updates.append({"operation": "record_link", "temporary_id": f"temp_link_{index}",
                            "data": data, "source_refs": refs[:]})
            links += 1
        for relation_id, statements in assumptions.items():
            note(f"From {self.name}: assumption about {relation_id}, which is not drawn: " + " · ".join(statements))
        for assessment in value["assessments"]:
            note(f"From {self.name}: assessment {assessment.get('id')} ({assessment.get('kind')}): "
                 f"{assessment.get('statement')}. It is the file's own conclusion, not one reached here.")
        case = request["case"]
        records = {r["ref"]: r for r in case["records"]}
        current = records.get(case["current_intervention"])
        goals = [e for e in value["entities"] if "goal" in self.roles.get(e["id"], []) and e["tree"] == "goal"]
        if current is None and not records and len(goals) == 1:
            # A fresh case takes the tree's goal as its goal, so the loop can start from it.
            # Mid-conversation, the goal stays whatever the conversation makes it.
            updates.append({"operation": "record_goal", "temporary_id": "goal", "source_refs": refs[:],
                            "data": {"statement": goals[0]["statement"], "scope": None, "horizon": None,
                                     "measure": None, "baseline": None, "protections": []}})
        if current:
            intervention = deepcopy(current["data"])
            intervention["primary_prompt"] = (f"The trees from {self.name} are in the Trees view. "
                                              + intervention["primary_prompt"])
        else:
            intervention = {"kind": "question", "purpose": "Choose a first test from the imported trees",
                            "decision": "Choose a test",
                            "primary_prompt": f"The trees from {self.name} are in the Trees view. Which change "
                                              "or action from them do you want to test first, and what do you "
                                              "expect to happen?",
                            "rationale": "The trees say what might work. A small test with a forecast written "
                                         "first shows whether it does.",
                            "required_context_refs": [],
                            "options": [{"id": "trees", "label": "Look at the trees",
                                         "action": {"type": "view", "target": "trees"}}]}
            if any(u["operation"] == "record_goal" for u in updates):
                intervention.update(goal_ref="goal", required_context_refs=["goal"])
        self.summary = {"claims": len(value["entities"]), "links": links, "notes": len(kept)}
        return {"schema_version": "1", "delivery_profile": "p2", "request_id": request["input"]["request_id"],
                "base_revision": request["input"]["base_revision"], "intervention": intervention,
                "proposed_updates": updates}


def import_trees(store, source, speaker, open_case=None):
    """Add the trees in an LTP file to an existing case; return a short summary."""
    if open_case is None:
        from reason_commons.bootstrap import open_case
    source = Path(source)
    content = source.read_bytes()
    value, roles = read_trees(content)
    text(speaker, "speaker")
    with open_case(store) as staging:
        source_ref = staging.add_source(source.name, content, SOURCE_ATTRIBUTION)
    importer = TreeImport(value, roles, source_ref, sha256(content).hexdigest(), source.name)
    with open_case(store, consultant=importer) as app:
        result = app.submit(IMPORT_REQUEST.format(name=source.name), speaker, **app.workspace()["target"])
    require(result["status"] == "saved", result.get("message") or "The trees were not saved")
    return {**importer.summary, "revision": result["revision"]}


def _slug(ref):
    return re.sub(r"[^a-z0-9]+", "-", ref.lower()).strip("-")


def ltp_document(workspace, project_id=None):
    """The case's current trees as an LTP 1.0 document (a dict)."""
    entities, designations, relationships, assumptions = [], [], [], []
    for tree in workspace["trees"]:
        for claim in tree["claims"]:
            entity = "e-" + _slug(claim["ref"])
            entities.append({"id": entity, "tree": tree["tree"], "statement": claim["statement"],
                             "provenance": {"path": f"reason-commons case {workspace['case_id']}#{claim['ref']}"}})
            designations.append({"id": "d-" + _slug(claim["ref"]), "entity_id": entity, "role": claim["role"]})
        for link in tree["links"]:
            relationship = "r-" + _slug(link["ref"])
            relationships.append({"id": relationship, "tree": tree["tree"], "kind": link["relation"],
                                  "from_entity_ids": ["e-" + _slug(link["from"])],
                                  "to_entity_id": "e-" + _slug(link["to"])})
            if link.get("assumption"):
                assumptions.append({"id": "a-" + _slug(link["ref"]), "relationship_id": relationship,
                                    "statement": link["assumption"]})
    project = project_id or (re.sub(r"[^a-z0-9]+", "-", workspace["case_name"].lower()).strip("-") or "case")
    return {"ltp": {"schema_version": "1.0", "project_id": project, "title": workspace["case_name"],
                    "entities": entities, "designations": designations, "relationships": relationships,
                    "assumptions": assumptions, "assessments": [], "changes": []}}


def export_trees(workspace, destination):
    """Write the trees to a new .ltp.yaml file."""
    destination = Path(destination)
    require(not destination.exists(), "Choose a new file name; the export does not overwrite files")
    document = ltp_document(workspace)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("# Exported from Reason Commons. The trees as they stand now.\n" +
                           yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100),
                           encoding="utf-8")
    return {"claims": len(document["ltp"]["entities"]), "links": len(document["ltp"]["relationships"])}
