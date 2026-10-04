"""Draw the recorded thinking-process trees as indented terminal outlines.

The input is the ``trees`` part of a workspace read. Drawing adds no meaning:
every line comes from a recorded claim, link or test. The outline reads top
down, from what a tree is for (a goal, a symptom, an objective) to what it
rests on, with each link's meaning written on the branch. A claim reached by
two paths is drawn once and referred to the second time.
"""

import textwrap


# Each tree's name, and the question it answers (README, "Six questions, six trees").
TREE_TITLES = {
    "goal": ("Goal Tree", "What must be true for us to reach the goal?"),
    "current_reality": ("Current Reality Tree", "Why are we not there yet?"),
    "conflict": ("Evaporating Cloud", "What conflict keeps us stuck?"),
    "future_reality": ("Future Reality Tree", "If we change this, will it work, and what could go wrong?"),
    "prerequisite": ("Prerequisite Tree", "What stands in the way, and what comes first?"),
    "transition": ("Transition Tree", "What exactly do we do next?"),
}
ROLE_LABELS = {
    "goal": "GOAL", "critical_success_factor": "CRITICAL SUCCESS FACTOR",
    "necessary_condition": "NECESSARY CONDITION", "undesirable_effect": "UNDESIRABLE EFFECT",
    "intermediate_cause": "CAUSE", "root_cause": "ROOT CAUSE",
    "critical_root_cause": "ROOT CAUSE · LIKELY CONSTRAINT", "cloud_objective": "SHARED OBJECTIVE",
    "cloud_requirement": "NEED", "cloud_prerequisite": "WHAT WE THINK WE MUST DO",
    "injection": "CHANGE WE MAKE", "desired_effect": "DESIRED EFFECT",
    "implementation_objective": "OBJECTIVE", "obstacle": "OBSTACLE",
    "intermediate_objective": "INTERMEDIATE OBJECTIVE", "transition_existing_reality": "WHERE WE START",
    "transition_need": "WHY IT MUST CHANGE", "transition_action": "ACTION",
    "transition_expected_effect": "WHAT WE EXPECT TO SEE", "observation": "OBSERVATION", "evidence": "EVIDENCE",
}
# Colour families for the terminal: what we want, what is wrong, what we do.
ROLE_STYLES = {
    "goal": "green", "critical_success_factor": "green", "necessary_condition": "green",
    "desired_effect": "green", "transition_expected_effect": "green", "cloud_objective": "green",
    "undesirable_effect": "dark_orange", "obstacle": "dark_orange", "intermediate_cause": "dark_orange",
    "root_cause": "red", "critical_root_cause": "red",
    "cloud_requirement": "blue", "injection": "blue", "intermediate_objective": "blue",
    "implementation_objective": "blue", "transition_need": "blue", "transition_existing_reality": "blue",
    "cloud_prerequisite": "magenta", "transition_action": "magenta",
}
# How a claim drawn below relates to the claim above it, read top down.
BELOW = {"necessary_for": "needs", "causes": "because", "contributes_to": "partly because",
         "requires": "requires", "satisfies": "met by", "overcomes": "overcomes",
         "produces": "produced by", "implements": "carried out by", "enables": "made possible by",
         "supports": "supported by", "challenges": "challenged by"}
# Links that hang the target below the source rather than the other way round:
# a need sits above what it requires, an objective above the obstacle it overcomes.
DOWNWARD = {"requires", "overcomes"}
# Links that are not part of the hierarchy; they are written on the claim instead.
ASIDE = {"conflicts_with": "conflicts with", "precedes": "comes before",
         "invalidates_assumption": "breaks an assumption behind", "supersedes": "replaces",
         "refines": "refines"}
BASIS = {"hypothesis": "hypothesis", "participant_report": "reported", "observed": "observed"}
# Roots are drawn ends first: what a tree is for comes before what serves it.
ROLE_ORDER = ["goal", "critical_success_factor", "necessary_condition", "undesirable_effect", "desired_effect",
              "cloud_objective", "implementation_objective", "transition_expected_effect", "transition_need",
              "transition_existing_reality", "critical_root_cause", "root_cause", "intermediate_cause",
              "cloud_requirement", "cloud_prerequisite", "injection", "obstacle", "intermediate_objective",
              "transition_action", "observation", "evidence"]


def _number(ref):
    return int(ref[1:].split("@")[0])


def tree_lines(tree, width=80, fresh=()):
    """One tree as lines of (text, style) segments; an empty style is plain text.

    Claims whose references are in ``fresh`` are marked NEW (the ones a past revision added)."""
    name, question = TREE_TITLES[tree["tree"]]
    lines = [[(name, "bold"), ("  " + question, "italic")], []]
    claims = {c["ref"]: c for c in tree["claims"]}
    if not claims:
        return lines + [[("Nothing in this tree yet.", "dim")]]
    children, has_parent, asides = {ref: [] for ref in claims}, set(), {ref: [] for ref in claims}
    for link in tree["links"]:
        if link["relation"] in ASIDE:
            asides[link["from"]].append((ASIDE[link["relation"]], link["to"]))
            continue
        upper, lower = ((link["from"], link["to"]) if link["relation"] in DOWNWARD
                        else (link["to"], link["from"]))
        children[upper].append((link, lower))
        has_parent.add(lower)
    roots = sorted((ref for ref in claims if ref not in has_parent),
                   key=lambda ref: (ROLE_ORDER.index(claims[ref]["role"]), _number(ref)))
    # Every claim in a cycle has a parent; start such a group at its earliest claim.
    reachable = set()

    def reach(ref):
        if ref not in reachable:
            reachable.add(ref)
            for _, child in children[ref]:
                reach(child)
    for ref in roots:
        reach(ref)
    for ref in sorted(claims, key=_number):
        if ref not in reachable:
            roots.append(ref)
            reach(ref)

    drawn = set()

    def wrap(text, indent):
        return textwrap.wrap(text, max(20, width - len(indent))) or [""]

    def draw(ref, lead, rest, relation=None, assumption=None):
        claim = claims[ref]
        header = [(lead, "dim")]
        if relation:
            header.append((relation + " ─ ", "italic dim"))
        if ref in drawn:
            lines.append(header + [("↑ see above: ", "dim"), (textwrap.shorten(claim["statement"], 50), "")])
            return
        drawn.add(ref)
        # The statement is what people read; its role label is a quieter, coloured tag above it.
        header.append((ROLE_LABELS[claim["role"]], "dim " + ROLE_STYLES.get(claim["role"], "")))
        if claim.get("basis"):
            header.append(("  " + BASIS[claim["basis"]], "dim"))
        if ref in fresh:
            header.append(("  NEW", "bold reverse"))
        lines.append(header)
        for line in wrap(claim["statement"], rest):
            lines.append([(rest, "dim"), (line, "")])
        if assumption:
            for line in wrap("assuming " + assumption, rest):
                lines.append([(rest, "dim"), (line, "italic dim")])
        for label, other in asides[ref]:
            target = claims.get(other)
            if target:
                lines.append([(rest, "dim"), ("⚡ " + label + ": " if label == "conflicts with" else "→ " + label + ": ",
                                              "bold"), (textwrap.shorten(target["statement"], 60), "")])
        for test in claim.get("tests", []):
            forecast = "; ".join(f for f in test["forecast"] if f) or "none"
            result = "; ".join(test["results"]) or "not observed yet"
            for line in wrap(f"◆ Test: {test['statement']} · forecast {forecast} · result {result}", rest):
                lines.append([(rest, "dim"), (line, "green")])
        # Short branches first, so a long chain does not separate a claim from its leaves.
        below = sorted(children[ref], key=lambda pair: (bool(children[pair[1]]), _number(pair[1])))
        for index, (link, child) in enumerate(below):
            last = index == len(below) - 1
            draw(child, rest + ("└─ " if last else "├─ "), rest + ("   " if last else "│  "),
                 BELOW[link["relation"]], link.get("assumption"))

    for index, ref in enumerate(roots):
        if index:
            lines.append([])
        draw(ref, "", "")
    return lines


def trees_lines(trees, width=80, only=None, fresh=()):
    """All trees (or one), separated by a blank line."""
    lines = []
    for tree in trees:
        if only and tree["tree"] != only:
            continue
        if lines:
            lines += [[], []]
        lines += tree_lines(tree, width, fresh)
    return lines


def plain(lines):
    return "\n".join("".join(text for text, _ in line) for line in lines).rstrip() + "\n"
