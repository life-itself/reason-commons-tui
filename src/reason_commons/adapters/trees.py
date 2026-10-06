"""Draw the recorded thinking-process trees as indented terminal outlines.

The input is the ``trees`` part of a workspace read. Drawing adds no meaning:
every line comes from a recorded claim, link or test. The outline reads top
down, from what a tree is for (a goal, a symptom, an objective) to what it
rests on. Each statement opens its line, led in by the relation word that ties
it to the one above ("because: ..."), so a branch reads as a sentence; its role
follows as a quiet tag, and the assumption behind the link hangs under it. A
claim reached by two paths is drawn once and referred to the second time.

A chain does not step to the right: when a statement's only branch with more
below it is its last, that branch continues the spine at the same indent, so a
Prerequisite Tree reads as a ladder rather than a staircase. A complete
Evaporating Cloud is drawn as its five boxes, both sides at equal weight.

Where paths meet, which an outline would otherwise hide, a statement's line says
how many of its tree's ends it leads to ("leads to 3 of 4 undesirable effects").
A test that carries a statement out reads as a sealed prediction: its forecast,
saved before any result, then what was reported.
"""

import textwrap

from rich.cells import cell_len


# Each tree's name, and the question it answers (README, "Six questions, six trees").
TREE_TITLES = {
    "goal": ("Goal Tree", "What must be true for us to reach the goal?"),
    "current_reality": ("Current Reality Tree", "Why are we not there yet?"),
    "conflict": ("Evaporating Cloud", "What conflict keeps us stuck?"),
    "future_reality": ("Future Reality Tree", "If we change this, will it work, and what could go wrong?"),
    "prerequisite": ("Prerequisite Tree", "What stands in the way, and what comes first?"),
    "transition": ("Transition Tree", "What exactly do we do next?"),
}
# Which way to read each tree's outline: the meaning of its branches, said once under its name.
READING = {
    "goal": "Read down: each statement needs the ones beneath it.",
    "current_reality": "Read down: each effect happens because of the causes beneath it.",
    "conflict": "Read down: the shared objective needs both needs, each need requires an action, and the two "
                "actions conflict.",
    "future_reality": "Read down: each effect follows from what is beneath it; after it, what could go wrong.",
    "prerequisite": "Read the ladder from the bottom: what is lowest comes first.",
    "transition": "Read down: why it must change, what we expect to see, and the action that produces it.",
}
# The question worth asking of a statement in each tree (tui-reasoning-design.md, "Typed visual grammar").
WORTH_ASKING = {
    "goal": "Could success occur without this condition here?",
    "current_reality": "When would this route fail to produce the effect?",
    "conflict": "Is this action the only way to meet the legitimate need?",
    "future_reality": "What could defeat the benefit or harm another need?",
    "prerequisite": "Is this state demonstrated, or has an action merely finished?",
    "transition": "What would establish the expected effect?",
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
# Colour families for the terminal: what we want, what is wrong, what we do, and what we think we must do.
# They name the theme's families (adapters/themes.py) rather than colours; the TUI resolves them.
WANT, WRONG, DO, PROPOSE = "$stood-behind", "$disagreed", "$hand", "$proposed"
ROLE_STYLES = {
    "goal": WANT, "critical_success_factor": WANT, "necessary_condition": WANT,
    "desired_effect": WANT, "transition_expected_effect": WANT, "cloud_objective": WANT,
    "undesirable_effect": WRONG, "obstacle": WRONG, "intermediate_cause": WRONG,
    "root_cause": "bold " + WRONG, "critical_root_cause": "bold " + WRONG,
    "cloud_requirement": DO, "injection": DO, "intermediate_objective": DO,
    "implementation_objective": DO, "transition_need": DO, "transition_existing_reality": DO,
    "cloud_prerequisite": PROPOSE, "transition_action": PROPOSE,
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
# A link read from either end, for a statement's details: what this statement does to the other,
# and what the other does to it. "C causes E" reads "causes E" on C and "because C" on E.
FROM_SIDE = {"necessary_for": "is needed for", "causes": "causes", "contributes_to": "contributes to",
             "conflicts_with": "conflicts with", "requires": "requires", "satisfies": "meets",
             "overcomes": "overcomes", "precedes": "comes before", "produces": "produces",
             "invalidates_assumption": "breaks an assumption behind", "implements": "carries out",
             "supersedes": "replaces", "supports": "supports", "challenges": "challenges", "refines": "refines",
             "enables": "makes possible"}
TO_SIDE = {"necessary_for": "needs", "causes": "because", "contributes_to": "partly because",
           "conflicts_with": "conflicts with", "requires": "required by", "satisfies": "met by",
           "overcomes": "overcome by", "precedes": "comes after", "produces": "produced by",
           "invalidates_assumption": "has an assumption broken by", "implements": "carried out by",
           "supersedes": "replaced by", "supports": "supported by", "challenges": "challenged by",
           "refines": "refined by", "enables": "made possible by"}
# Roots are drawn ends first: what a tree is for comes before what serves it.
ROLE_ORDER = ["goal", "critical_success_factor", "necessary_condition", "undesirable_effect", "desired_effect",
              "cloud_objective", "implementation_objective", "transition_expected_effect", "transition_need",
              "transition_existing_reality", "critical_root_cause", "root_cause", "intermediate_cause",
              "cloud_requirement", "cloud_prerequisite", "injection", "obstacle", "intermediate_objective",
              "transition_action", "observation", "evidence"]
# A tree whose question puts one kind of root first: a Future Reality Tree asks "will it work" before
# "what could go wrong", so its desired effects come before its negative branches.
ROOTS_FIRST = {"future_reality": ["desired_effect"]}
# What a tree is drawn towards, for saying how many of them a statement leads to: the convergence a Current
# Reality Tree is drawn to find, and in a Future Reality Tree a change's benefits beside its harms. A count
# of recorded links, read upward; it is not a diagnosis of the constraint.
ENDS = {"current_reality": ["undesirable_effect"], "future_reality": ["desired_effect", "undesirable_effect"],
        "goal": ["critical_success_factor"]}
ENDS_PLURAL = {"undesirable_effect": "undesirable effects", "desired_effect": "desired effects",
               "critical_success_factor": "critical success factors"}
# In a Future Reality Tree almost everything leads to the desired effects; what is worth saying is what each
# change we make leads to, benefits and harms together. Elsewhere any statement may say it.
ENDS_FROM = {"future_reality": {"injection"}}
# Glues a tag's words so it never breaks across lines.
GLUE = " "


def _number(ref):
    return int(ref[1:].split("@")[0])


def _family(role):
    """A role's colour family without its weight, for a marker or a tag."""
    return ROLE_STYLES.get(role, "dim").replace("bold ", "")


def _width(segments):
    """Terminal cells, not characters: ⚡ takes two."""
    return sum(cell_len(text) for text, _ in segments)


def _wrap(parts, width, first, rest):
    """Word-wrap styled text into lines of segments, each line opening with ``first`` or ``rest``.

    A word may change style part way; words joined by GLUE stay on one line, and a tag that moves to
    the next line loses its leading glue. A word longer than a line is cut where the line ends."""
    words, word = [], []
    for text, style in parts:
        for index, chunk in enumerate(text.split(" ")):
            if index and word:
                words.append(word)
                word = []
            if chunk:
                word.append((chunk, style))
    if word:
        words.append(word)
    lines, line, used = [], [], 0
    for word in words:
        room = max(10, width - _width(first if not lines else rest))
        if line and used + 1 + _width(word) > room:
            lines.append(line)
            line, used = [], 0
            room = max(10, width - _width(rest))
        if not line and word[0][0].startswith(GLUE):
            word = [(word[0][0].lstrip(GLUE), word[0][1])] + word[1:]
        if line:
            line.append((" ", ""))
            used += 1
        while _width(word) > room - used:  # a word with no place to break
            cut, taken = [], 0
            for text, style in word:
                keep = text[:max(0, room - used - taken)]
                if keep:
                    cut.append((keep, style))
                taken += len(keep)
            if not cut:
                break
            lines.append(line + cut)
            line, used = [], 0
            room = max(10, width - _width(rest))
            word = _drop(word, taken)
        line += word
        used += _width(word)
    lines.append(line)
    return [(first if index == 0 else rest) + [(text.replace(GLUE, " "), style) for text, style in line]
            for index, line in enumerate(lines)]


def _drop(word, count):
    """A word's segments without its first ``count`` characters."""
    out = []
    for text, style in word:
        if count >= len(text):
            count -= len(text)
            continue
        out.append((text[count:], style))
        count = 0
    return out


def _shape(tree):
    """A tree's hierarchy: each claim's (link, claim) children, its asides, and its roots in drawing order."""
    claims = {c["ref"]: c for c in tree["claims"]}
    children, has_parent, asides = {ref: [] for ref in claims}, set(), {ref: [] for ref in claims}
    for link in tree["links"]:
        if link["relation"] in ASIDE:
            asides[link["from"]].append((ASIDE[link["relation"]], link["to"], link.get("assumption")))
            continue
        upper, lower = ((link["from"], link["to"]) if link["relation"] in DOWNWARD
                        else (link["to"], link["from"]))
        children[upper].append((link, lower))
        has_parent.add(lower)
    first = ROOTS_FIRST.get(tree["tree"], [])
    roots = sorted((ref for ref in claims if ref not in has_parent),
                   key=lambda ref: (first.index(claims[ref]["role"]) if claims[ref]["role"] in first else len(first),
                                    ROLE_ORDER.index(claims[ref]["role"]), _number(ref)))
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
    return claims, children, asides, roots


def roots(tree):
    """The statements a tree is drawn from: what it is for, in drawing order."""
    return _shape(tree)[3]


def branches(tree):
    """Each statement's reference with the references drawn directly below it (none for a leaf)."""
    return {ref: [child for _, child in below] for ref, below in _shape(tree)[1].items()}


def _above(children):
    """Each statement's references with those it hangs under: one for a plain branch, more where paths meet."""
    above = {ref: [] for ref in children}
    for upper, below in children.items():
        for _, lower in below:
            above[lower].append(upper)
    return above


def neighbours(tree, ref):
    """The chosen statement's chunk: itself, every statement it hangs under, and those directly below it."""
    children = _shape(tree)[1]
    return {ref, *_above(children)[ref], *(child for _, child in children[ref])}


def leads_to(tree, ref, above=None):
    """The statements of the tree's ends (``ENDS``) that this one reaches by following its links upward.
    ``above`` is the tree's ``_above`` map, when the caller has it already."""
    ends = ENDS.get(tree["tree"], [])
    if not ends:
        return []
    above = _above(_shape(tree)[1]) if above is None else above
    roles = {c["ref"]: c["role"] for c in tree["claims"]}
    seen, todo = set(), [ref]
    while todo:
        for upper in above[todo.pop()]:
            if upper not in seen:
                seen.add(upper)
                todo.append(upper)
    seen.discard(ref)
    return sorted((r for r in seen if roles[r] in ends), key=_number)


def reach(tree, ref, above=None):
    """'leads to 3 of 4 undesirable effects', when a statement reaches two or more of its tree's ends; else None.

    Paths meeting is the one relation an outline hides, since a statement reached twice is drawn once; this
    says it on the statement's own line, as a count of recorded links."""
    roles = {c["ref"]: c["role"] for c in tree["claims"]}
    if tree["tree"] in ENDS_FROM and roles[ref] not in ENDS_FROM[tree["tree"]]:
        return None
    reached = leads_to(tree, ref, above)
    if len(reached) < 2:
        return None
    parts = []
    for role in ENDS[tree["tree"]]:
        count = sum(1 for r in reached if roles[r] == role)
        total = sum(1 for r in roles.values() if r == role)
        noun = ENDS_PLURAL[role] if total > 1 else ROLE_LABELS[role].lower()
        if count:
            parts.append(f"the {noun}" if total == 1 else f"both {noun}" if count == total == 2
                         else f"all {total} {noun}" if count == total else f"{count} of {total} {noun}")
    return ("needed for " if tree["tree"] == "goal" else "leads to ") + " and ".join(parts)


def tally(tree):
    """What a tree holds and what it does not say yet: its statements and links, the links that state no
    assumption and the statements that state no basis. Counts of recorded fields; nothing is judged."""
    return {"statements": len(tree["claims"]), "links": len(tree["links"]),
            "no_assumption": sum(1 for link in tree["links"] if not link.get("assumption")),
            "no_basis": sum(1 for claim in tree["claims"] if not claim.get("basis"))}


def tally_line(tree):
    """'12 statements · 11 links · 4 links state no assumption · 12 statements state no basis'."""
    counts = tally(tree)

    def counted(number, one, many):
        return f"{number} {one if number == 1 else many}"
    parts = [counted(counts["statements"], "statement", "statements"), counted(counts["links"], "link", "links")]
    if counts["no_assumption"]:
        parts.append(counted(counts["no_assumption"], "link states", "links state") + " no assumption")
    if counts["no_basis"]:
        parts.append(counted(counts["no_basis"], "statement states", "statements state") + " no basis")
    return " · ".join(parts)


def test_lines(test, lead, width):
    """A test that carries out a statement, read as a sealed prediction: what it tries, the forecast written
    before any result, and what was reported, each on its own line."""
    forecast = "; ".join(f for f in test["forecast"] if f) or "none"
    result = "; ".join(test["results"]) or "not observed yet"
    lines = _wrap([("◆ ", WANT), ("Test: ", "bold"), (test["statement"], "")], width, lead, lead + [("  ", "")])
    lines += _wrap([("original forecast, saved before any result: ", "italic dim"), (forecast, WANT)], width,
                   lead + [("  ", "")], lead + [("  ", "")])
    lines += _wrap([("result: ", "italic dim"), (result, "" if test["results"] else "dim")], width,
                   lead + [("  ", "")], lead + [("  ", "")])
    return lines


def tree_lines(tree, width=80, fresh=(), spans=None, folded=(), title=True, columns=None, echoes=None,
               whole=True):
    """One tree as lines of (text, style) segments; an empty style is plain text.

    Claims whose references are in ``fresh`` are marked NEW (the ones a past revision added), and those
    in ``folded`` are drawn without what lies below them, which is counted instead. When ``spans`` is a
    list, each drawn statement is appended to it as (ref, first line, end line), in reading order, so an
    interface can choose a statement and keep it in view; ``echoes``, when a list, receives each reference
    back to a statement drawn above as (ref, the statement it is drawn under, first line, end line). A
    complete Evaporating Cloud with room for it is drawn as boxes; then ``columns``, when a dict, receives
    each box's (first column, end column). A ``tree`` that is only part of one (not ``whole``) says nothing
    about how many of its ends a statement leads to, since the rest of the paths are not there to count."""
    name, question = TREE_TITLES[tree["tree"]]
    lines = [[(name, "bold"), ("  " + question, "italic")], []] if title else []
    if not tree["claims"]:
        return lines + [[("Nothing in this tree yet.", "dim")]]
    if tree["tree"] == "conflict" and not folded and whole:
        boxes = cloud_lines(tree, width, fresh)
        if boxes is not None:
            drawing, found, places = boxes
            if spans is not None:
                spans += [(ref, start + len(lines), end + len(lines)) for ref, start, end in found]
            if columns is not None:
                columns.update(places)
            return lines + drawing
    claims, children, asides, starts = _shape(tree)
    above = _above(children)
    drawn = set()

    def under(ref, seen=None):
        """Every statement under this one, each once."""
        seen = set() if seen is None else seen
        for _, child in children[ref]:
            if child not in seen:
                seen.add(child)
                under(child, seen)
        return seen

    def assuming(assumption, rest):
        # Every link's assumption is drawn where the link is, including a back-reference or an aside.
        if assumption:
            lines.extend(_wrap([("assuming " + assumption, "italic dim")], width, rest + [("┆ ", "dim")],
                               rest + [("┆ ", "dim")]))

    def draw(ref, lead, rest, below, relation=None, assumption=None, parent=None):
        """``lead`` opens the statement's first line and ``rest`` its others; its branches hang from ``below``.
        ``parent`` is the statement it is drawn under."""
        claim = claims[ref]
        parts = [(relation + ":", "italic dim"), (" ", "")] if relation else []
        if ref in drawn:
            first = len(lines)
            short = textwrap.shorten(claim["statement"], 50, placeholder="…")
            lines.extend(_wrap(parts + [("↑ ", "dim"), (short, ""), (f" {GLUE}(shown{GLUE}above)", "dim")],
                               width, lead, rest))
            assuming(assumption, rest)
            if echoes is not None:
                echoes.append((ref, parent, first, len(lines)))
            return
        drawn.add(ref)
        first = len(lines)
        opens = folded and ref in folded and children[ref]
        parts.append((claim["statement"], "bold" if not relation else ""))
        tag = f" {GLUE}·{GLUE}" + ROLE_LABELS[claim["role"]].lower().replace(" ", GLUE)
        parts.append((tag, _family(claim["role"])))
        if claim.get("basis"):
            parts.append((f"{GLUE}·{GLUE}{BASIS[claim['basis']]}", "dim"))
        meets = reach(tree, ref, above) if whole else None
        if meets:
            parts.append((f" {GLUE}·{GLUE}" + meets, "italic"))
        if ref in fresh:
            parts.append((" " + ("REWORDED" if claim.get("earlier_wording") else "NEW"), "bold " + DO))
        if opens:
            hidden = under(ref)
            changed = len(hidden & set(fresh))
            parts.append((f" ▸{GLUE}{len(hidden)}{GLUE}below" + (f",{GLUE}{changed}{GLUE}changed" if changed else ""), DO))
        lines.extend(_wrap(parts, width, lead, rest))
        assuming(assumption, rest)
        for label, other, aside_assumption in asides[ref]:
            target = claims.get(other)
            if target:
                mark = ("⚡ " + label + ": ", "bold " + WRONG) if label == "conflicts with" else ("→ " + label + ": ", "bold")
                lines.extend(_wrap([mark, (textwrap.shorten(target["statement"], 60, placeholder="…"), "")],
                                   width, rest, rest))
                assuming(aside_assumption, rest)
        for test in claim.get("tests", []):
            lines.extend(test_lines(test, rest, width))
        if spans is not None:
            spans.append((ref, first, len(lines)))
        if opens:
            return
        # Short branches first, so a long chain does not separate a claim from its leaves.
        branches = sorted(children[ref], key=lambda pair: (bool(children[pair[1]]), _number(pair[1])))
        deeper = [child for _, child in branches if children[child]]
        spine = None
        if len(deeper) == 1 and branches[-1][1] == deeper[0]:
            spine = branches.pop()
        for index, (link, child) in enumerate(branches):
            last = index == len(branches) - 1 and spine is None
            draw(child, below + [("└─ " if last else "├─ ", "dim")], below + [("   " if last else "│  ", "dim")],
                 below + [("   " if last else "│  ", "dim")], BELOW[link["relation"]], link.get("assumption"), ref)
        if spine is not None:
            link, child = spine
            if child in drawn:  # drawn on another path: refer to it like any other branch
                draw(child, below + [("└─ ", "dim")], below + [("   ", "dim")], below + [("   ", "dim")],
                     BELOW[link["relation"]], link.get("assumption"), ref)
            else:
                lines.append(below + [("│", "dim")])
                step(child, below, BELOW[link["relation"]], link.get("assumption"), ref)

    def step(ref, base, relation=None, assumption=None, parent=None):
        """A statement on a spine: a marker in its colour at ``base``, its branches hanging from there."""
        goes_on = bool(children[ref]) and not (folded and ref in folded)
        draw(ref, base + [("● ", _family(claims[ref]["role"]))], base + [("│ " if goes_on else "  ", "dim")],
             base, relation, assumption, parent)

    for index, ref in enumerate(starts):
        if index:
            lines.append([])
        step(ref, [])
    return lines


def trees_lines(trees, width=80, only=None, fresh=(), spans=None, folded=(), title=True, columns=None, echoes=None):
    """All trees (or one), separated by a blank line; the rest as for ``tree_lines``."""
    lines = []
    for tree in trees:
        if only and tree["tree"] != only:
            continue
        if lines:
            lines += [[], []]
        found, referred = [], []
        drawn = tree_lines(tree, width, fresh, found, folded, title, columns, referred)
        if spans is not None:
            spans += [(ref, start + len(lines), end + len(lines)) for ref, start, end in found]
        if echoes is not None:
            echoes += [(ref, parent, start + len(lines), end + len(lines)) for ref, parent, start, end in referred]
        lines += drawn
    return lines


def bright_lines(spans, echoes, chunk, chosen):
    """The drawn lines that stay at full contrast while ``chosen`` is worked on: the statements in its chunk
    (``neighbours``), and each reference back that joins the chosen statement to one of them."""
    keep = set()
    for ref, start, end in spans:
        if ref in chunk:
            keep.update(range(start, end))
    for ref, parent, start, end in echoes:
        if chosen in (ref, parent) and {ref, parent} <= chunk:
            keep.update(range(start, end))
    return keep


def cloud_lines(tree, width, fresh=()):
    """A complete Evaporating Cloud as its five boxes, or None when it is not complete or there is no room.

    Complete means a shared objective, two needs that each serve it, two actions that each one need
    requires, and the conflict between those actions: five statements, five links, nothing else. The
    objective sits on top, each need under it with the action it requires below, and the conflict between
    the two actions, so both sides carry equal weight. Each link's assumption is numbered on the drawing
    and written out underneath. Returns (lines, spans, columns) as ``tree_lines`` describes them."""
    gap = 6
    column = min(40, (width - gap) // 2)
    if column < 20:
        return None
    claims = {c["ref"]: c for c in tree["claims"]}
    by_role = {}
    for claim in tree["claims"]:
        by_role.setdefault(claim["role"], []).append(claim["ref"])
    if (len(claims) != 5 or len(by_role.get("cloud_objective", [])) != 1 or len(by_role.get("cloud_requirement", [])) != 2
            or len(by_role.get("cloud_prerequisite", [])) != 2 or any(c.get("tests") for c in claims.values())
            or len(tree["links"]) != 5):
        return None
    objective = by_role["cloud_objective"][0]
    needs = sorted(by_role["cloud_requirement"], key=_number)
    between = {frozenset((link["from"], link["to"])): link for link in tree["links"]}
    serves = [between.get(frozenset((need, objective))) for need in needs]
    actions = [next((a for a in by_role["cloud_prerequisite"] if frozenset((need, a)) in between), None) for need in needs]
    if None in serves or None in actions or actions[0] == actions[1]:
        return None
    requires = [between[frozenset((need, action))] for need, action in zip(needs, actions)]
    conflict = between.get(frozenset(actions))
    if (conflict is None or conflict["relation"] != "conflicts_with"
            or any(link["relation"] in ASIDE for link in serves + requires)):
        return None

    total = 2 * column + gap
    centres = [column // 2, column + gap + column // 2]
    lines, spans, places = [], [], {}

    def place(row, segments, at):
        """Put segments on a row starting at column ``at``, padding with spaces."""
        row += [(" " * (at - _width(row)), "")] if at > _width(row) else []
        return row + segments

    def box(ref):
        """A labelled box as rows of segments, all ``column`` wide."""
        claim = claims[ref]
        label = [(ROLE_LABELS[claim["role"]], _family(claim["role"]))]
        if ref in fresh:
            label.append(("  " + ("REWORDED" if claim.get("earlier_wording") else "NEW"), "bold " + DO))
        inner = column - 4
        text = textwrap.wrap(claim["statement"], inner) or [""]
        return ([label, [("╭" + "─" * (column - 2) + "╮", "dim")]]
                + [[("│ ", "dim"), (line.ljust(inner), ""), (" │", "dim")] for line in text]
                + [[("╰" + "─" * (column - 2) + "╯", "dim")]])

    def tee(rows):
        """A box's bottom edge with a connector leaving from its middle."""
        rows[-1] = [("╰" + "─" * (column // 2 - 1) + "┬" + "─" * (column - column // 2 - 2) + "╯", "dim")]
        return rows

    def pair(left, right, middle=None):
        """Two boxes side by side, the shorter padded, with ``middle`` (a row index -> segments) in the gap."""
        height = max(len(left), len(right))
        for side in (left, right):
            filler = [("│ ", "dim"), (" " * (column - 4), ""), (" │", "dim")]
            while len(side) < height:
                side.insert(len(side) - 1, list(filler))
        start = len(lines)
        for index in range(height):
            row = place(list(left[index]), [], column)
            row = place(row, (middle or {}).get(index, []), column)
            lines.append(place(row, right[index], column + gap))
        return start, len(lines)

    def mark(number):
        return f"({number})"

    # The shared objective, centred, and the branch down to the two needs.
    top = tee(box(objective))
    left_edge = (total - column) // 2
    start = len(lines)
    for row in top:
        lines.append(place([], row, left_edge))
    spans.append((objective, start, len(lines)))
    places[objective] = (left_edge, left_edge + column)
    middle = left_edge + column // 2
    lines.append(place([], [("╭" + "─" * (middle - centres[0] - 1) + "┴" + "─" * (centres[1] - middle - 1) + "╮",
                             "dim")], centres[0]))
    row = place([], [("│ ", "dim"), (BELOW[serves[0]["relation"]] + " ", "italic dim"), (mark(4), DO)], centres[0])
    lines.append(place(row, [("│ ", "dim"), (BELOW[serves[1]["relation"]] + " ", "italic dim"), (mark(5), DO)],
                       centres[1]))
    # The needs, and what each requires.
    start, end = pair(tee(box(needs[0])), tee(box(needs[1])))
    for side, ref in enumerate(needs):
        spans.append((ref, start, end))
        places[ref] = (side * (column + gap), side * (column + gap) + column)
    row = place([], [("│ ", "dim"), (BELOW[requires[0]["relation"]] + " ", "italic dim"), (mark(1), DO)], centres[0])
    lines.append(place(row, [("│ ", "dim"), (BELOW[requires[1]["relation"]] + " ", "italic dim"), (mark(2), DO)],
                       centres[1]))
    # The two actions, with the conflict between them.
    left, right = box(actions[0]), box(actions[1])
    start, end = pair(left, right, {2: [("◀─⚡─▶", "bold " + WRONG)], 3: [("  ", ""), (mark(3), "bold " + WRONG)]})
    for side, ref in enumerate(actions):
        spans.append((ref, start, end))
        places[ref] = (side * (column + gap), side * (column + gap) + column)
    # Spans in reading order: the objective, then each side from its need to its action.
    order = [objective, needs[0], actions[0], needs[1], actions[1]]
    spans.sort(key=lambda span: order.index(span[0]))
    lines += [[], [("Each link rests on an assumption; the cloud evaporates when one turns out to be false.", "dim")]]
    for number, link in enumerate([requires[0], requires[1], conflict, serves[0], serves[1]], start=1):
        lead = [(mark(number) + " ", "bold " + WRONG if number == 3 else DO), ("┆ ", "dim")]
        if link.get("assumption"):
            lines.extend(_wrap([("assuming " + link["assumption"], "italic dim")], width, lead,
                               [(" " * len(mark(number) + " "), ""), ("┆ ", "dim")]))
        else:
            lines.append(lead + [("no assumption recorded yet", "dim")])
    return lines, spans, places


def statement_details(trees, ref, width=60, origins=()):
    """One statement in full, as lines of segments: what it is, its wording, the question worth asking
    of it, every link read from its side with the assumption behind it, the tests that carry it out, its
    earlier wordings and where it came from. ``origins`` are (heading, words) pairs the caller resolved
    from the sources the statement cites; nothing here is inferred beyond the recorded claims and links.
    The order follows the rendering contract: wording, relationships, then history."""
    tree = next(t for t in trees if any(c["ref"] == ref for c in t["claims"]))
    claims = {c["ref"]: c for c in tree["claims"]}
    claim = claims[ref]
    lines = []

    def para(text, style="", indent=""):
        for line in textwrap.wrap(str(text), max(20, width - len(indent))) or [""]:
            lines.append([(indent, ""), (line, style)])

    def heading(text):
        lines.extend([[], [(text, "bold dim")]])

    lines.extend(_wrap([(ROLE_LABELS[claim["role"]].capitalize(), "bold " + _family(claim["role"])),
                        (f" {GLUE}·{GLUE}" + TREE_TITLES[tree["tree"]][0].replace(" ", GLUE), "dim")], width, [], []))
    lines.append([])
    para(claim["statement"], "bold")
    para("Basis: " + BASIS[claim["basis"]] if claim.get("basis") else "Basis not stated", "dim")
    heading("Worth asking")
    para(WORTH_ASKING[tree["tree"]], "italic", "  ")
    groups = {}
    for link in tree["links"]:
        if link["from"] == ref:
            groups.setdefault(FROM_SIDE[link["relation"]], []).append((link["to"], link))
        elif link["to"] == ref:
            groups.setdefault(TO_SIDE[link["relation"]], []).append((link["from"], link))
    for phrase, related in groups.items():
        heading(phrase.capitalize())
        for other, link in related:
            role = claims[other]["role"]
            lines.extend(_wrap([("● ", _family(role)), (claims[other]["statement"], "")], width, [("  ", "")],
                               [("    ", "")]))
            # A link with nothing said about why it holds says so where you are looking, not in a dialog.
            lines.extend(_wrap([("assuming " + link["assumption"], "italic dim") if link.get("assumption")
                                else ("no assumption stated yet", "dim")], width,
                               [("    ┆ ", "dim")], [("    ┆ ", "dim")]))
    meets = reach(tree, ref)
    if meets:
        heading(meets[0].upper() + meets[1:])
        for other in leads_to(tree, ref):
            lines.extend(_wrap([("● ", _family(claims[other]["role"])), (claims[other]["statement"], "")], width,
                               [("  ", "")], [("    ", "")]))
    for test in claim.get("tests", []):
        heading("Test that carries it out")
        para(test["statement"], "", "  ")
        para("Original forecast, saved before any result: " + ("; ".join(f for f in test["forecast"] if f) or "none"),
             WANT, "  ")
        para("Result: " + ("; ".join(test["results"]) or "not observed yet"), "", "  ")
    if claim.get("earlier_wording"):
        heading("Earlier wording")
        for wording in claim["earlier_wording"]:
            para(wording, "italic", "  ")
    if origins:
        heading("Where it came from")
        for title, words in origins:
            para(title, "dim", "  ")
            if words:
                para(words, "", "    ")
    return lines


def plain(lines):
    return "\n".join("".join(text for text, _ in line) for line in lines).rstrip() + "\n"
