"""Draw the six thinking-process trees used in the README and docs/the-trees.md.

The content is the Second Renaissance analysis in the reasoncommons guide
(github.com/life-itself/reasoncommons, ltp/02 to ltp/07), with labels shortened to
fit a box. The pictures are illustrations of the method: the app does not draw
these trees yet. Each SVG follows the reader's light or dark colour scheme.

    python3 scripts/draw_trees.py
"""

from html import escape
from pathlib import Path
import textwrap

OUT = Path(__file__).resolve().parents[1] / "docs" / "images" / "trees"
FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'

# Kind: (label shown above the text, light colour, dark colour).
KINDS = {
    "goal": ("GOAL", "#1a7f37", "#3fb950"),
    "csf": ("CRITICAL SUCCESS FACTOR", "#1a7f37", "#3fb950"),
    "nc": ("NECESSARY CONDITION", "#1a7f37", "#3fb950"),
    "symptom": ("SYMPTOM", "#bc4c00", "#f0883e"),
    "root": ("ROOT CAUSE", "#cf222e", "#f85149"),
    "constraint": ("ROOT CAUSE · LIKELY CONSTRAINT", "#cf222e", "#f85149"),
    "objective": ("SHARED OBJECTIVE", "#1a7f37", "#3fb950"),
    "need": ("NEED", "#0969da", "#4493f8"),
    "want": ("WHAT WE THINK WE MUST DO", "#8250df", "#ab7df8"),
    "breaker": ("CHANGE THAT DISSOLVES THE CONFLICT", "#0969da", "#4493f8"),
    "injection": ("CHANGE WE MAKE", "#0969da", "#4493f8"),
    "effect": ("DESIRED EFFECT", "#1a7f37", "#3fb950"),
    "risk": ("NEGATIVE BRANCH", "#cf222e", "#f85149"),
    "obstacle": ("OBSTACLE", "#bc4c00", "#f0883e"),
    "io": ("INTERMEDIATE OBJECTIVE", "#0969da", "#4493f8"),
    "action": ("ACTION", "#8250df", "#ab7df8"),
    "next": ("ACTION · DO THIS FIRST", "#8250df", "#ab7df8"),
    "seen": ("WHAT WE EXPECT TO SEE", "#1a7f37", "#3fb950"),
}


class Tree:
    def __init__(self, name, title, question, edge_note, width, box_w, line_chars, source):
        self.name, self.title, self.question, self.edge_note = name, title, question, edge_note
        self.width, self.box_w, self.chars, self.source = width, box_w, line_chars, source
        self.nodes, self.edges, self.notes = {}, [], []

    def node(self, key, kind, text, x, y, w=None, chars=None):
        lines = textwrap.wrap(text, chars or self.chars)
        self.nodes[key] = {"kind": kind, "lines": lines, "x": x, "y": y, "w": w or self.box_w,
                           "h": 34 + 18 * len(lines)}

    def edge(self, a, b, style="solid", label=None, sides=None):
        self.edges.append((a, b, style, label, sides))

    def note(self, text, x, y, anchor="start"):
        self.notes.append((text, x, y, anchor))

    def svg(self):
        height = max(n["y"] + n["h"] for n in self.nodes.values()) + 56
        height = max([height] + [y + 44 for _, _, y, _ in self.notes])
        kinds = sorted({n["kind"] for n in self.nodes.values()})
        light = "\n".join(f"  .k-{k} {{ --c: {KINDS[k][1]}; }}" for k in kinds)
        dark = " ".join(f".k-{k} {{ --c: {KINDS[k][2]}; }}" for k in kinds)
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {height}" '
               f'width="{self.width}" height="{height}" role="img" aria-label="{escape(self.aria())}">',
               f"<title>{escape(self.title)}: {escape(self.question)}</title>",
               "<style>",
               light,
               f"  .box {{ fill: var(--c); fill-opacity: .07; stroke: var(--c); stroke-width: 1.5; }}",
               "  .k-constraint .box, .k-next .box { stroke-width: 3; }",
               f"  .kind {{ font: 600 10.5px {FONT}; letter-spacing: .06em; fill: var(--c); }}",
               f"  .text {{ font: 14px {FONT}; fill: #1f2328; }}",
               f"  .title {{ font: 600 20px {FONT}; fill: #1f2328; }}",
               f"  .question {{ font: 15px {FONT}; fill: #424a53; }}",
               f"  .note {{ font: italic 13px {FONT}; fill: #59636e; }}",
               "  .edge { fill: none; stroke: #8b949e; stroke-width: 1.5; }",
               "  .dashed { stroke-dasharray: 6 4; }",
               "  .conflict { stroke: #cf222e; stroke-width: 2.5; stroke-dasharray: 7 5; }",
               "  .risk { stroke: #cf222e; stroke-dasharray: 6 4; }",
               "  #a path { fill: #8b949e; } #r path { fill: #cf222e; }",
               "  @media (prefers-color-scheme: dark) {",
               f"    {dark}",
               "    .text, .title { fill: #e6edf3; } .question { fill: #c9d1d9; } .note { fill: #9198a1; }",
               "    .conflict, .risk { stroke: #f85149; } #r path { fill: #f85149; }",
               "  }",
               "</style>",
               '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
               'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z"/></marker>'
               '<marker id="r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
               'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z"/></marker></defs>',
               f'<text class="title" x="24" y="36">{escape(self.title)}</text>',
               f'<text class="question" x="24" y="60">{escape(self.question)}</text>',
               f'<text class="note" x="{self.width - 24}" y="36" text-anchor="end">{escape(self.edge_note)}</text>']
        for edge in self.edges:
            out.append(self.path(*edge))
        for key, n in self.nodes.items():
            out.append(f'<g class="k-{n["kind"]}">')
            out.append(f'<rect class="box" x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" rx="9"/>')
            out.append(f'<text class="kind" x="{n["x"] + 12}" y="{n["y"] + 20}">{KINDS[n["kind"]][0]}</text>')
            for i, line in enumerate(n["lines"]):
                out.append(f'<text class="text" x="{n["x"] + 12}" y="{n["y"] + 42 + 18 * i}">{escape(line)}</text>')
            out.append("</g>")
        for text, x, y, anchor in self.notes:
            out.append(f'<text class="note" x="{x}" y="{y}" text-anchor="{anchor}">{escape(text)}</text>')
        out.append(f'<text class="note" x="24" y="{height - 18}">{escape(self.source)}</text>')
        out.append("</svg>")
        return "\n".join(out) + "\n"

    def aria(self):
        parts = [f"{self.title}. {self.question}"]
        parts += [f"{KINDS[n['kind']][0].capitalize()}: {' '.join(n['lines'])}." for n in self.nodes.values()]
        return " ".join(parts)

    def anchor(self, n, side):
        x, y, w, h = n["x"], n["y"], n["w"], n["h"]
        return {"top": (x + w / 2, y), "bottom": (x + w / 2, y + h),
                "left": (x, y + h / 2), "right": (x + w, y + h / 2)}[side]

    def path(self, a, b, style, label, sides):
        na, nb = self.nodes[a], self.nodes[b]
        if sides is None:
            sides = ("top", "bottom") if nb["y"] + nb["h"] <= na["y"] else \
                    ("bottom", "top") if na["y"] + na["h"] <= nb["y"] else \
                    ("right", "left") if na["x"] < nb["x"] else ("left", "right")
        (x1, y1), (x2, y2) = self.anchor(na, sides[0]), self.anchor(nb, sides[1])
        gap = 4
        if sides[0] in ("top", "bottom"):
            y1 += -gap if sides[0] == "top" else gap
            y2 += gap if sides[1] == "bottom" else -gap
            my = (y1 + y2) / 2
            d = f"M{x1:.1f} {y1:.1f} C{x1:.1f} {my:.1f} {x2:.1f} {my:.1f} {x2:.1f} {y2:.1f}"
        else:
            x1 += gap if sides[0] == "right" else -gap
            x2 += -gap if sides[1] == "left" else gap
            mx = (x1 + x2) / 2
            d = f"M{x1:.1f} {y1:.1f} C{mx:.1f} {y1:.1f} {mx:.1f} {y2:.1f} {x2:.1f} {y2:.1f}"
        cls = {"solid": "edge", "dashed": "edge dashed", "conflict": "edge conflict", "risk": "edge risk"}[style]
        marker = "r" if style in ("conflict", "risk") else "a"
        start = f' marker-start="url(#{marker})"' if style == "conflict" else ""
        svg = f'<path class="{cls}" d="{d}"{start} marker-end="url(#{marker})"/>'
        if label:
            lx, ly = (x1 + x2) / 2, (y1 + y2) / 2
            svg += f'\n<text class="note" x="{lx + 8:.1f}" y="{ly + 4:.1f}">{escape(label)}</text>'
        return svg


def columns(count, box_w, gap, left=24):
    return [left + i * (box_w + gap) for i in range(count)]


def between(xs, i, j, box_w, w=None):
    """x for a box of width w centred over columns i..j."""
    w = w or box_w
    return (xs[i] + xs[j] + box_w) / 2 - w / 2


def goal_tree():
    t = Tree("goal-tree", "Goal Tree", "What must be true for us to reach the goal?",
             "arrows: is necessary for", 1056, 158, 20,
             "Second Renaissance example, from reasoncommons/ltp/02-goal-tree.md (labels shortened)")
    xs = columns(6, 158, 12)
    t.node("g", "goal", "A wiser, weller, regenerative civilisation, co-initiated consciously",
           between(xs, 0, 5, 158, 360), 86, 360, 42)
    for i, (key, text) in enumerate([("csf1", "People durably embody wiser views, values and practices"),
                                     ("csf2", "The group learns and revises its strategy from evidence and objections"),
                                     ("csf3", "Proven practices settle in pockets and can be passed on")]):
        t.node(key, "csf", text, between(xs, 2 * i, 2 * i + 1, 158, 300), 210, 300, 36)
        t.edge(key, "g")
    for i, (key, parent, text) in enumerate([
            ("nc2", "csf1", "A clear path from first contact to lasting practice"),
            ("nc3", "csf1", "Practices can be repeated at deeper levels"),
            ("nc1", "csf2", "Progress is defined without reducing it to activity counts"),
            ("nc6", "csf2", "Strategy maps are living, challengeable commons"),
            ("nc4", "csf3", "Contributors grow into facilitators and stewards"),
            ("nc5", "csf3", "Dense practice groups get support and stay outward-facing")]):
        t.node(key, "nc", text, xs[i], 336)
        t.edge(key, parent)
    return t


def current_reality_tree():
    t = Tree("current-reality-tree", "Current Reality Tree", "Why are we not there yet? What causes what we see?",
             "arrows: causes", 1060, 236, 28,
             "Second Renaissance example, from reasoncommons/ltp/03-current-reality-tree.md (labels shortened)")
    xs = columns(4, 236, 22)
    row = {5: 86, 4: 180, 3: 274, 2: 368, 1: 462, 0: 556}
    t.node("ude2", "symptom", "The group is busy, yet lasting adoption stays low", between(xs, 1, 2, 236, 270), row[5], 270, 32)
    t.node("ude3", "symptom", "Core organisers are overloaded and risk burnout", xs[0], row[4])
    t.node("ude6", "symptom", "Others admire the work but don't reproduce it", xs[1], row[4])
    t.node("ude5", "symptom", "Pockets are hard to form and stay fragile", xs[1], row[3])
    t.node("ude1", "symptom", "Many resonate, but few enter sustained practice", xs[0], row[2])
    t.node("ude4", "symptom", "Newcomers don't know the next step", xs[0], row[1])
    t.node("rc1", "constraint", "No reliable path from interest to practice", xs[0], row[0])
    t.node("rc2", "root", "Progress is not defined in a way people accept", xs[2], row[2])
    t.node("rc0", "root", "No agreed way to check and revise the map", xs[2], row[1])
    t.node("rc3", "root", "No regular rhythm of practice, action and learning", xs[3], row[2])
    for a, b in [("rc1", "ude4"), ("ude4", "ude1"), ("ude1", "ude3"), ("ude1", "ude5"), ("ude5", "ude6"),
                 ("ude6", "ude2"), ("rc0", "rc2"), ("rc2", "ude2"), ("rc3", "ude2")]:
        t.edge(a, b)
    t.note("Every symptom here is provisional: the group has not", 540, 580)
    t.note("yet checked it against lived experience.", 540, 600)
    return t


def evaporating_cloud():
    t = Tree("evaporating-cloud", "Evaporating Cloud", "What conflict keeps us stuck, and which assumption is false?",
             "arrows: in order to", 1010, 250, 30,
             "Second Renaissance example, from reasoncommons/ltp/04-evaporating-clouds.md (labels shortened)")
    t.node("d", "want", "Act like a movement now: scale, speed, message, accessibility", 24, 96)
    t.node("dp", "want", "Act like a monastery or lab now: depth, slowness, practice, rigour", 24, 330)
    t.node("b", "need", "Be visible enough to attract people, resources and legitimacy", 370, 96)
    t.node("c", "need", "Be embodied enough to represent the new paradigm with integrity", 370, 330)
    t.node("a", "objective", "Durable cultural transformation", 736, 222, 250, 30)
    t.edge("d", "b")
    t.edge("dp", "c")
    t.edge("b", "a", sides=("right", "left"))
    t.edge("c", "a", sides=("right", "left"))
    t.edge("d", "dp", "conflict", sides=("bottom", "top"))
    t.note("conflict", 162, 254)
    t.note("Hidden assumption: both draw on the same scarce", 24, 476)
    t.note("organiser capacity and cannot be staged or combined.", 24, 496)
    t.node("inj", "breaker", "A broad public invitation built around deep, protected practice pockets: "
           "reach feeds practice, practice grows future facilitators", 370, 460, 616, 72)
    return t


def future_reality_tree():
    t = Tree("future-reality-tree", "Future Reality Tree",
             "If we make these changes, do they lead to the goal? What could go wrong?",
             "arrows: leads to", 1068, 136, 16,
             "Second Renaissance example, from reasoncommons/ltp/05-future-reality-tree.md (labels shortened)")
    xs = columns(7, 136, 12)
    t.node("g", "goal", "Wiser, weller, regenerative civilisation", between(xs, 3, 4, 136, 220), 86, 220, 26)
    t.node("de6", "effect", "Verified lasting adoption grows", xs[6], 86)
    effects = [("de1", 1, "Real change is told apart from busyness"), ("de2", 3, "More people sustain practice"),
               ("de3", 4, "Leadership capacity grows"), ("de4", 5, "Stable pockets form"),
               ("de5", 6, "Mature practices can be reproduced")]
    for key, col, text in effects:
        t.node(key, "effect", text, xs[col], 226)
    for (a, _, _), (b, _, _) in zip(effects, effects[1:]):
        t.edge(a, b)
    t.edge("de5", "de6")
    t.edge("de6", "g", sides=("left", "right"))
    injections = [("i0", 0, "de1", "Steward and revise the trees"), ("i2", 1, "de1", "Mixed-method progress measure"),
                  ("i4", 2, "de1", "A practice, action and learning rhythm"),
                  ("i3", 3, "de2", "Transparent, consent-based entry path"),
                  ("i5", 4, "de3", "Graduated stewardship"), ("i6", 5, "de4", "Dense, outward-facing pockets"),
                  ("i7", 6, "de5", "Maturity-rated replication library")]
    for key, col, effect, text in injections:
        t.node(key, "injection", text, xs[col], 380)
        t.edge(key, effect)
    t.node("n1", "risk", "Counting replaces real change", between(xs, 0, 1, 136, 220), 536, 220, 26)
    t.node("n2", "risk", "People feel funnelled; trust falls", between(xs, 3, 4, 136, 220), 536, 220, 26)
    t.edge("i2", "n1", "risk", "may cause")
    t.edge("i3", "n2", "risk", "may cause")
    t.note("Each risk gets a trim:", 752, 556)
    t.note("mixed evidence and peer review;", 752, 576)
    t.note("free choice and easy exit.", 752, 596)
    return t


def prerequisite_tree():
    t = Tree("prerequisite-tree", "Prerequisite Tree", "What stands in the way, and what has to come first?",
             "arrows: is overcome by · comes before", 900, 300, 38,
             "Second Renaissance example, from reasoncommons/ltp/06-prerequisite-tree.md (labels shortened)")
    steps = [("Goal, symptoms and arrows are not yet checked", "A stewarded model, accepted for provisional use"),
             ("A progress measure may be contested or reductive", "A mixed-method progress measure is agreed"),
             ("No next step; people may resist being funnelled", "A transparent, consent-based entry path"),
             ("Agreeing in principle doesn't change practice", "Recurring practice at deeper levels"),
             ("Delegating risks quality or a status hierarchy", "Accountable, graduated stewardship"),
             ("Values are hard to sustain without a container", "An outward-facing pilot pocket runs"),
             ("Practices stay tacit or spread shallowly", "A maturity-rated, adaptable practice library")]
    top = 86
    t.node("goal", "injection", "Scale through depth: reach built around protected practice pockets", 536, top, 340, 40)
    for i, (obstacle, objective) in enumerate(reversed(steps)):
        n = len(steps) - i
        y = top + 86 + i * 90
        t.node(f"o{n}", "obstacle", obstacle, 24, y, 380, 46)
        t.node(f"i{n}", "io", objective, 536, y, 340, 40)
        t.edge(f"o{n}", f"i{n}", label=None, sides=("right", "left"))
    t.edge("i7", "goal")
    for n in range(1, 7):
        t.edge(f"i{n}", f"i{n + 1}")
    t.note("start here", 706, top + 86 + 6 * 90 + 90, "middle")
    return t


def transition_tree():
    t = Tree("transition-tree", "Transition Tree", "What exactly do we do, and what should we see when it works?",
             "arrows: should produce · achieves", 1020, 330, 40,
             "Second Renaissance example, from reasoncommons/ltp/07-transition-tree.md (labels shortened)")
    lanes = [("next", "Hold one time-boxed, stewarded review of the goal, the symptoms and the likely constraint",
              "A dated model: what is confirmed, what is disputed, who stewards it", "A provisional shared model"),
             ("action", "Draft one mixed-method definition of lasting adoption",
              "One measure that can be tested, not treated as the truth", "A progress measure is agreed"),
             ("action", "Prototype one clear next step from an open evening to a first practice",
              "Where people accept, decline, pause or leave, recorded without pressure", "A consent-based entry path"),
             ("action", "Run one short recurring-practice group",
              "Evidence about retention, practice and safety", "Recurring practice")]
    y = 86
    for i, (kind, action, seen, objective) in enumerate(lanes, 1):
        t.node(f"a{i}", kind, action, 24, y, 330, 40)
        t.node(f"s{i}", "seen", seen, 396, y, 330, 40)
        t.node(f"o{i}", "io", objective, 768, y, 228, 26)
        t.edge(f"a{i}", f"s{i}", sides=("right", "left"))
        t.edge(f"s{i}", f"o{i}", sides=("right", "left"))
        y += t.nodes[f"a{i}"]["h"] + 26
    t.note("Each action is a small test with a forecast. That part is what the app runs today.", 24, y + 4)
    return t


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for make in (goal_tree, current_reality_tree, evaporating_cloud, future_reality_tree,
                 prerequisite_tree, transition_tree):
        tree = make()
        (OUT / f"{tree.name}.svg").write_text(tree.svg(), encoding="utf-8")
        print(f"wrote docs/images/trees/{tree.name}.svg")


if __name__ == "__main__":
    main()
