"""The guided tour as data, and as a position in it. Nothing here draws a screen, so all of it can be tested
without a terminal.

A tour script (``tours/<name>.yaml``) tells a story in parts. A part has opening pages, then the workspace with
a few beats narrated in a strip, then a closing page; a loop part narrates whatever the built-in guide is asking
instead of fixed beats. The script is checked as it loads, so a renamed tree, a missing example answer or a line
too long for an 80-column strip fails a test instead of the tour.

``Tour`` is where the person is and what moves them on. Moving never changes a goal: only the workspace does
that, through its use cases. ``prepare`` brings a fresh copy of the tour's goal forward to where a part begins,
with the story's own answers, through the same use cases a person's answers go through; it never decides the
proposals the tour asks the person about. ``Progress`` remembers the part reached, outside every goal.
"""

from importlib.resources import files
import os
from pathlib import Path
import re
import tempfile
import textwrap

import yaml

from reason_commons.adapters.guided import PREFIX, STEPS
from reason_commons.adapters.settings import state_folder
from reason_commons.adapters.trees import TREE_TITLES

# The guide's steps a tour may need an example answer for: the test, the action, the result and the review.
EXAMPLE_STEPS = ("test_change", "test_forecast", "test_review", "test_stop", "action", "observe", "review")
# What a beat's button may do, and what it may wait for.
BUTTON_KEYS = {"label", "view", "tree", "select"}
UNTIL_KEYS = {"view", "tree", "selected", "decided"}
# Where a part's loop is done: the kind of record that must be in the model.
LOOP_ENDS = ("action", "review")
# Choices a page may offer.
CHOICES = {"next", "back", "contents", "leave", "own", "commons", "home"}
# The strip is three lines of words at 80 columns: the width its border and padding leave.
STRIP_WIDTH, STRIP_LINES = 74, 3
# A story page's words fit an 80 by 24 terminal under its heading and above its choices; a koan and a quote are
# indented behind a bar.
PAGE_WIDTH, PAGE_ROWS, QUOTE_WIDTH = 74, 15, 70
# The page before a closing koan that introduces the monastery, the first time.
INTRO = {"kicker": "One more thing", "heading": "An infirmary on the pass"}
# Words a tour never shows: retired stationery metaphors, and the method's abbreviations a newcomer cannot read.
BANNED = re.compile(r"\b((?i:cards?|decks?|stacks?)|CSF|NCs?|UDEs?|CRT|FRT|PRT|EC|TT|INJ\d*|NB\d*|IOs?|TOC|LTP)\b")


def load_tour(name="harrowfield"):
    script = yaml.safe_load(files("reason_commons.adapters").joinpath(f"tours/{name}.yaml").read_text("utf-8"))
    check(script)
    return script


def words(script):
    """Every piece of text the tour can put on screen."""
    def walk(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for key, item in value.items():
                if key not in ("id", "tree", "view", "until", "requires", "clock", "story"):
                    yield from walk(item)
        elif isinstance(value, list):
            for item in value:
                yield from walk(item)
    yield from walk({key: script[key] for key in script if key not in ("clock", "story")})


def lines(text, width=STRIP_WIDTH):
    return len(textwrap.wrap(" ".join(text.split()), width))


def paragraphs(text, width=PAGE_WIDTH):
    """Rows a block of paragraphs takes, with a blank row between them."""
    parts = [part for part in (text or "").split("\n\n") if part.strip()]
    return sum(lines(part, width) for part in parts) + max(len(parts) - 1, 0)


def page_rows(page, closing=False):
    """Rows a story page's words take, blocks apart by a blank row: what ``check`` holds to ``PAGE_ROWS``."""
    blocks = [paragraphs(page.get("text")),
              sum(1 + lines(quote, QUOTE_WIDTH) for _, _, quote in page.get("quotes", [])),
              paragraphs(page.get("after")), paragraphs(page.get("koan"), QUOTE_WIDTH)]
    if closing:
        blocks += [lines(page["key"]), 1]
    blocks = [rows for rows in blocks if rows]
    return sum(blocks) + len(blocks) - 1


def check(script, views=None):
    """Refuse a script the workspace cannot show as written. ``views`` names the workspace's views, if given."""
    def need(condition, message):
        if not condition:
            raise ValueError(f"Tour {script.get('name', '?')!r}: {message}")

    for key in ("name", "story", "player", "examples", "pending", "parts"):
        need(key in script, f"needs {key!r}")
    need(set(EXAMPLE_STEPS) <= set(script["examples"]), "needs an example answer for each of " + ", ".join(EXAMPLE_STEPS))
    need(set(script["examples"]) <= set(STEPS), "has an example for a step the guide does not ask")
    ids = [part.get("id") for part in script["parts"]]
    need(len(ids) == len(set(ids)) and all(ids), "parts need distinct ids")
    for part in script["parts"]:
        where = f"part {part['id']!r}"
        need(part.get("title") and part.get("pages"), f"{where} needs a title and at least one page")
        if part.get("tree"):
            need(part["tree"] in TREE_TITLES, f"{where} names an unknown tree")
            need(part["title"] == TREE_TITLES[part["tree"]][1],
                 f"{where} should be titled with its tree's own question: {TREE_TITLES[part['tree']][1]!r}")
        if part.get("clock"):
            need(part["clock"] in script.get("clock", {}), f"{where} names an unknown clock")
        if part.get("requires"):
            need(part["requires"] in LOOP_ENDS, f"{where} requires something prepare cannot reach")
        for page in part["pages"]:
            need(page.get("text") or page.get("koan") or page.get("quotes"), f"{where} has a page with nothing to read")
            need(page_rows(page) <= PAGE_ROWS, f"{where}: a page is longer than an 80 by 24 screen: "
                                               f"{(page.get('heading') or page.get('kicker'))!r}")
            for choice in page.get("choices", []):
                need(len(choice) == 3 and choice[0] in CHOICES, f"{where} has an unknown choice {choice!r}")
        loop = part.get("loop")
        if loop:
            need(loop.get("until") in LOOP_ENDS, f"{where}'s loop must end at one of {LOOP_ENDS}")
            need(loop.get("waiting") and loop.get("done"), f"{where}'s loop needs words for waiting and done")
            for step, text in loop.items():
                if step in STEPS:
                    need(lines(text) <= STRIP_LINES, f"{where}: {step} is longer than the strip")
        for beat in part.get("beats", []):
            need(beat.get("say"), f"{where} has a beat with nothing to say")
            need(lines(beat["say"]) <= STRIP_LINES, f"{where}: a beat is longer than the strip: {beat['say'][:40]}")
            button = beat.get("button")
            if button:
                need(set(button) <= BUTTON_KEYS and button.get("label"), f"{where} has an unclear button")
                need(set(button) - {"label"}, f"{where}: a button must do something")
                if "tree" in button:
                    need(button["tree"] in TREE_TITLES, f"{where}: a button opens an unknown tree")
                if views is not None and "view" in button:
                    need(button["view"] in views, f"{where}: a button opens an unknown view")
            until = beat.get("until")
            if until:
                need(len(until) == 1 and set(until) <= UNTIL_KEYS, f"{where} waits for something unclear")
                if "decided" in until:
                    need(until["decided"] in script["pending"], f"{where} waits for an unknown proposal")
                if "tree" in until:
                    need(until["tree"] in TREE_TITLES, f"{where} waits for an unknown tree")
                if views is not None and "view" in until:
                    need(until["view"] in views, f"{where} waits for an unknown view")
            done = beat.get("done")
            if isinstance(done, dict):
                need(set(done) == {"accepted", "rejected"}, f"{where}: a decision's words need both outcomes")
            for text in ([done] if isinstance(done, str) else list((done or {}).values())):
                need(lines(text) <= STRIP_LINES, f"{where}: a beat's outcome is longer than the strip")
        if part["id"] not in ("prologue", "epilogue"):
            closing = part.get("closing") or {}
            need(all(closing.get(key) for key in ("title", "koan", "key", "next")),
                 f"{where} needs a closing koan with its title, key and what comes next")
            need(page_rows(closing, closing=True) <= PAGE_ROWS, f"{where}: its closing page is too long")
            need(paragraphs(closing.get("intro")) <= PAGE_ROWS, f"{where}: its introduction is too long")
    for text in words(script):
        found = BANNED.search(text)
        if found:
            need(False, f"says {found.group(0)!r}, a word a newcomer should never meet: {text[:50]!r}")


class Tour:
    """Where the person is: a part, and a step in it. A step is a page, How this works, a beat of the strip, the
    guide's loop, or the closing page. A beat that waits for something moves on by itself when it happens there
    (or says how it turned out), but never onto a page: pages open only when the person asks."""

    def __init__(self, script, part=None):
        self.script, self.parts = script, script["parts"]
        self.index, self.at = (self.part_index(part) if part else 0), 0
        self.facts = {}
        # The beat whose condition was still open when the person reached it: only that one moves on by itself.
        self._waiting = None
        self.arrive()

    # ----- where ------------------------------------------------------------------------------------------
    def part_index(self, part_id):
        return next(i for i, part in enumerate(self.parts) if part["id"] == part_id)

    @property
    def part(self):
        return self.parts[self.index]

    def steps(self, index=None):
        part = self.parts[self.index if index is None else index]
        steps = [{"kind": "page", "page": page} for page in part["pages"]]
        if part.get("how"):
            steps.append({"kind": "how"})
        if part.get("loop"):
            steps.append({"kind": "loop", "loop": part["loop"]})
        steps += [{"kind": "beat", "beat": beat} for beat in part.get("beats", [])]
        closing = part.get("closing")
        if closing and closing.get("intro"):
            steps.append({"kind": "page", "page": dict(INTRO, text=closing["intro"])})
        if closing:
            steps.append({"kind": "closing", "closing": closing})
        return steps

    @property
    def step(self):
        return self.steps()[self.at]

    @property
    def on_page(self):
        return self.step["kind"] in ("page", "how", "closing")

    @property
    def numbered(self):
        """The parts people count: all but the prologue and the epilogue."""
        return [part for part in self.parts if part["id"] not in ("prologue", "epilogue")]

    def number(self, part=None):
        part = part or self.part
        return next((n for n, p in enumerate(self.numbered, start=1) if p is part), None)

    def first(self):
        return self.index == 0 and self.at == 0

    def last(self):
        return self.index == len(self.parts) - 1 and self.at == len(self.steps()) - 1

    def next_is_page(self):
        steps = self.steps()
        return self.at + 1 >= len(steps) or steps[self.at + 1]["kind"] in ("page", "how", "closing")

    # ----- moving -----------------------------------------------------------------------------------------
    def next(self):
        if self.at + 1 < len(self.steps()):
            self.at += 1
        elif self.index + 1 < len(self.parts):
            self.index, self.at = self.index + 1, 0
        self.arrive()
        return self

    def back(self):
        if self.at > 0:
            self.at -= 1
        elif self.index > 0:
            self.index -= 1
            self.at = len(self.steps()) - 1
        self.arrive()
        return self

    def goto(self, part_id):
        self.index, self.at = self.part_index(part_id), 0
        self.arrive()
        return self

    def arrive(self):
        """On reaching a beat, note whether its condition is still open: only then may it move on by itself."""
        beat = self.step.get("beat") or {}
        until = beat.get("until")
        self._waiting = (self.index, self.at) if until and not self.holds(until) else None

    def observe(self, facts):
        """The workspace's latest facts. Returns True when the strip has something new to say."""
        before = (self.index, self.at, self.met())
        self.facts = facts
        while (self.step["kind"] == "beat" and self._waiting == (self.index, self.at)
               and self.holds(self.step["beat"]["until"])):
            self._waiting = None
            if self.step["beat"].get("done") or self.next_is_page():
                break
            self.at += 1
            self.arrive()
        return before != (self.index, self.at, self.met())

    # ----- what holds -------------------------------------------------------------------------------------
    def holds(self, until, facts=None):
        facts = self.facts if facts is None else facts
        (kind, value), = until.items()
        if kind == "view":
            return facts.get("view") == value
        if kind == "tree":
            return facts.get("view") == "trees" and facts.get("tree") == value
        if kind == "selected":
            if facts.get("view") != "trees" or (self.part.get("tree") and facts.get("tree") != self.part["tree"]):
                return False
            return facts.get("selected") is not None if value == "any" else facts.get("selected") == value
        return (facts.get("decided") or {}).get(value) in ("accepted", "rejected")

    def met(self):
        step = self.step
        if step["kind"] == "beat":
            until = step["beat"].get("until")
            return bool(until) and self.holds(until)
        if step["kind"] == "loop":
            return step["loop"]["until"] in (self.facts.get("accepted") or ())
        return False

    # ----- what the strip says -----------------------------------------------------------------------------
    def say(self):
        """The strip's words for this step."""
        step = self.step
        if step["kind"] == "loop":
            loop = step["loop"]
            if self.met():
                return loop["done"]
            if self.facts.get("waiting"):
                return loop["waiting"]
            return loop.get(self.facts.get("asked")) or loop[next(s for s in loop if s in STEPS)]
        beat = step["beat"]
        done = beat.get("done")
        if done and self.met():
            if isinstance(done, dict):
                return done[(self.facts.get("decided") or {})[beat["until"]["decided"]]]
            return done
        return beat["say"]

    def button(self):
        """The beat's own button while what it helps with is still to do."""
        step = self.step
        if step["kind"] != "beat" or self.met():
            return None
        return step["beat"].get("button")

    def status(self):
        """The strip's quiet first line: which part, and its question."""
        number = self.number()
        title = self.part["title"]
        return f"Tour · Part {number} of {len(self.numbered)} · {title}" if number else f"Tour · {title}"


def guided_step(question):
    purpose = ((question or {}).get("data") or {}).get("purpose") or ""
    return purpose[len(PREFIX):] if purpose.startswith(PREFIX) else None


def accepted_kinds(case):
    """The kinds of record in the goal's model now."""
    membership = case.workspace(view="backlog")["membership"]
    return {record["kind"] for record in case.inspect()["case"]["records"]
            if membership.get(record["ref"]) == "accepted"}


def decided(script, records, membership):
    """For each proposal the tour asks about, by name: proposed, accepted, rejected or undone (None if absent)."""
    out = {}
    for name, statement in script["pending"].items():
        statement = " ".join(statement.split())
        ref = next((r["ref"] for r in records if r["kind"] == "claim" and r["data"].get("statement") == statement),
                   None)
        out[name] = membership.get(ref) if ref else None
    return out


def prepare(case, script, requirement, speaker, limit=30):
    """Bring a goal opened from the tour's package forward until ``requirement`` (a kind of loop record) is in its
    model, answering whatever the guide asks with the story's example and accepting what each reply proposes.
    Through the ordinary use cases, so every step is validated and saved as a person's would be. It never
    decides the proposals the tour asks the person about, and it never goes back. Returns the steps it took."""
    for steps in range(limit):
        if requirement in accepted_kinds(case):
            return steps
        w = case.workspace()
        waiting = [r["ref"] for r in (w.get("reply") or {}).get("records") or [] if r["status"] == "proposed"]
        if waiting:
            result = case.accept(waiting, speaker, w["revision"])
            if result["status"] == "confirm":
                result = case.accept(waiting, speaker, w["revision"], confirmed=True)
        else:
            step = guided_step(w["question"])
            if step not in script["examples"]:
                raise ValueError(f"The tour has no example answer for the guide's question {step!r}")
            target = w["target"]
            result = case.submit(script["examples"][step], speaker, target["base_revision"],
                                 target["response_target"])
        if result["status"] != "saved":
            raise RuntimeError(f"Could not prepare the tour's goal: {result.get('message', result['status'])}")
    raise RuntimeError(f"The tour's goal did not reach {requirement!r} in {limit} steps")


class TourClock:
    """The story's time for what is saved during the tour, so History reads as the story does: the Friday before
    the pilot, then the Monday it starts, then the third morning."""

    def __init__(self, script):
        self.times = script.get("clock") or {}
        self.value = self.times.get("default")

    def at(self, part):
        self.value = self.times.get(part.get("clock") or "default", self.value)

    def now(self):
        return self.value


class Progress:
    """The part of each tour a person reached, so the tour can resume there. Kept in the state folder, outside
    every goal and apart from the settings: taking the tour before setup must not end first start."""

    def __init__(self, path=None):
        self.path = Path(path) if path else state_folder() / "tour.yaml"

    def load(self):
        try:
            data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, yaml.YAMLError):
            return {}
        return data if isinstance(data, dict) else {}

    def reached(self, name):
        """(the part reached, whether the tour was finished), or (None, False)."""
        entry = self.load().get(name)
        if not isinstance(entry, dict):
            return None, False
        return entry.get("part"), bool(entry.get("finished"))

    def save(self, name, part, finished=False):
        """Remember the part; False when it could not be written (the tour carries on regardless)."""
        data = self.load()
        data[name] = {"part": part, "finished": bool(finished)}
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle, temporary = tempfile.mkstemp(prefix=".tour-", dir=self.path.parent)
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                yaml.safe_dump(data, stream, sort_keys=False)
            os.replace(temporary, self.path)
        except OSError:
            return False
        return True
