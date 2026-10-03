"""Write the finished example's trees as an LTP 1.0 file.

The source is the Second Renaissance analysis in the reasoncommons guide
(github.com/life-itself/reasoncommons, ltp/ltp-model.yaml, MIT licence), the same
analysis the README draws. That model has its own format; this script maps it onto
the LTP 1.0 interchange vocabulary the app reads. A statement that appears in two
views becomes one statement per view, because an LTP statement belongs to one tree.

    python3 scripts/build_sample_trees.py path/to/reasoncommons/ltp/ltp-model.yaml
"""

from pathlib import Path
import re
import sys

import yaml

OUT = Path(__file__).resolve().parents[1] / "src" / "reason_commons" / "adapters" / "sample-trees.ltp.yaml"
VIEWS = {"goal-tree": "goal", "current-reality": "current_reality", "evaporating-cloud": "conflict",
         "future-reality": "future_reality", "prerequisite-tree": "prerequisite", "transition-tree": "transition"}
# (model type, tree) -> LTP role. The tree is consulted only where a type sits in two views.
ROLES = {"goal": "goal", "critical_success_factor": "critical_success_factor",
         "necessary_condition": "necessary_condition", "undesirable_effect": "undesirable_effect",
         "root_cause": "root_cause", "common_objective": "cloud_objective", "need": "cloud_requirement",
         "option": "cloud_prerequisite", "injection": "injection", "desirable_effect": "desired_effect",
         "negative_branch": "undesirable_effect", "obstacle": "obstacle",
         "intermediate_objective": "intermediate_objective", "action": "transition_action",
         "expected_effect": "transition_expected_effect"}
IN_TREE = {("goal", "future_reality"): "desired_effect", ("injection", "prerequisite"): "implementation_objective",
           ("intermediate_objective", "transition"): "transition_need"}
# model relation -> (LTP kind, reversed?)
RELATIONS = {"necessary_for": ("necessary_for", False), "causes": ("causes", False),
             "contributes_to": ("contributes_to", False), "reinforces": ("contributes_to", False),
             "may_cause": ("causes", False), "enables": ("enables", False), "produces": ("produces", False),
             "conflicts_with": ("conflicts_with", False), "believed_necessary_for": ("requires", True),
             "overcome_by": ("overcomes", True), "achieves": ("enables", False), "tests": ("supports", False),
             "reframes": ("refines", False)}


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def main(source):
    model = yaml.safe_load(Path(source).read_text())
    entities = {e["id"]: e for e in model["entities"]}
    assumptions = {a["id"]: a["statement"] for a in model["assumptions"]}
    links = {link["id"]: link for link in model["links"]}
    out = {"entities": [], "designations": [], "relationships": [], "assumptions": []}
    for view, tree in VIEWS.items():
        for ref in model["views"][view]["entities"]:
            entity = entities[ref]
            ident = f"{tree.replace('_', '-')}-{slug(ref)}"
            role = IN_TREE.get((entity["type"], tree), ROLES[entity["type"]])
            out["entities"].append({"id": ident, "tree": tree, "statement": entity["statement"],
                                    "provenance": {"path": f"reasoncommons/ltp/ltp-model.yaml#{ref}"}})
            out["designations"].append({"id": "d-" + ident, "entity_id": ident, "role": role})
        for ref in model["views"][view]["links"]:
            link = links[ref]
            kind, flip = RELATIONS[link["relation"]]
            source_id, target_id = (link["to"], link["from"]) if flip else (link["from"], link["to"])
            ident = f"{tree.replace('_', '-')}-{slug(ref)}"
            out["relationships"].append({"id": ident, "tree": tree, "kind": kind,
                                         "from_entity_ids": [f"{tree.replace('_', '-')}-{slug(source_id)}"],
                                         "to_entity_id": f"{tree.replace('_', '-')}-{slug(target_id)}"})
            if link.get("assumption") in assumptions:
                out["assumptions"].append({"id": "a-" + ident, "relationship_id": ident,
                                           "statement": assumptions[link["assumption"]]})
    document = {"ltp": {"schema_version": "1.0", "project_id": "second-renaissance-example",
                        "title": "Second Renaissance: why resonance is not becoming durable adoption",
                        **out, "assessments": [], "changes": []}}
    OUT.write_text("# The Second Renaissance analysis from the reasoncommons guide (ltp/ltp-model.yaml, MIT licence),\n"
                   "# mapped to LTP 1.0 by scripts/build_sample_trees.py for the app's finished example.\n" +
                   yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100))
    print(f"Wrote {OUT} ({len(out['entities'])} statements, {len(out['relationships'])} links)")


if __name__ == "__main__":
    main(sys.argv[1])
