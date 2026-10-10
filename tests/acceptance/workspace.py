"""Interface fixtures for the p1 workspace scenarios.

``Workspace`` runs the real Textual app headlessly and drives it the way a person
does: keys, Tab and Enter. Behave steps are synchronous and Textual's test pilot is
async, so the app lives in one long-lived task on its own event loop and each step
hands it a job. Outcomes are read at the application boundary (the consultant's
calls, the commons' revisions and retained inputs) and from what is on screen.

``build_forge`` makes the Forge commons of the navigation scenarios through the
application use cases: eight consultant replies and two tree imports, which call no
consultant, give revision 10 with the current question "Choose a test".
"""

import asyncio
from copy import deepcopy
import html
import re
import threading

import yaml

from reason_commons.adapters.ltp_trees import import_trees
from reason_commons.adapters.tui import ReasonCommonsApp
from reason_commons.bootstrap import create_case, open_case
from tests.support import ScriptedConsultant, proposal

SPEAKER = "Sam"
PROVIDER = "fixture"


class Workspace:
    """The persistent workspace on a commons folder, with a counting fixture consultant."""

    def __init__(self, path, consultant, size=(120, 40), speaker=SPEAKER):
        self.path, self.consultant, self.size = path, consultant, size
        # While a step holds a consultant reply back, key presses must not wait for it.
        self.wait_for_replies = True
        self.app = ReasonCommonsApp(path, speaker, PROVIDER, lambda c: open_case(path, consultant=c),
                                    lambda provider: consultant)
        self.loop = asyncio.new_event_loop()
        ready = self.loop.create_future()
        self.task = self.loop.create_task(self._main(ready))
        self.loop.run_until_complete(ready)

    async def _main(self, ready):
        self.jobs = asyncio.Queue()
        async with self.app.run_test(size=self.size) as pilot:
            self.pilot = pilot
            await pilot.pause()
            ready.set_result(None)
            while True:
                job, done = await self.jobs.get()
                if job is None:
                    break
                try:
                    done.set_result(await job(pilot))
                except BaseException as exc:  # handed back to the step that asked
                    done.set_exception(exc)

    def _do(self, job):
        done = self.loop.create_future()
        self.jobs.put_nowait((job, done))
        return self.loop.run_until_complete(done)

    def press(self, *keys, wait=None):
        """Press keys, then let any consultant request finish first unless replies are held back."""
        wait = self.wait_for_replies if wait is None else wait

        async def go(pilot):
            await pilot.press(*keys)
            if wait:
                await self.app.workers.wait_for_complete()
            await pilot.pause()
        self._do(go)

    def type(self, text):
        self.press(*["enter" if c == "\n" else "space" if c == " " else c for c in text])

    def settle(self):
        async def go(pilot):
            await self.app.workers.wait_for_complete()
            await pilot.pause()
        self._do(go)

    def resize(self, width, height):
        async def go(pilot):
            await pilot.resize_terminal(width, height)
            await pilot.pause()
        self._do(go)

    def read(self, function):
        """Run ``function(app)`` inside the app's own task, where widgets may be queried."""
        async def go(pilot):
            return function(self.app)
        return self._do(go)

    def focused(self):
        return self.read(lambda app: getattr(app.focused, "id", None))

    def screen_text(self):
        """What is visible right now, as plain text."""
        svg = re.sub(r"<style.*?</style>", "", self.read(lambda app: app.export_screenshot()), flags=re.S)
        return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", svg)).replace("\xa0", " ").split())

    def tab_to(self, control, limit=30):
        """Tab until the control with this id has focus, as a person would."""
        for _ in range(limit):
            if self.focused() == control:
                return
            self.press("tab")
        raise AssertionError(f"Tab never reached {control}; focus is on {self.focused()}")

    def running(self):
        return not self.task.done() and self.read(lambda app: app.is_running)

    def case(self, function):
        """Read the commons through the workspace's own application session."""
        return self.read(lambda app: function(app.case))

    def close(self):
        if self.task.done():
            return
        done = self.loop.create_future()
        self.jobs.put_nowait((None, done))
        self.loop.run_until_complete(self.task)
        self.loop.close()


class HeldConsultant(ScriptedConsultant):
    """A consultant whose next reply waits until the step releases it."""

    def __init__(self, responses=None):
        super().__init__(responses)
        self.release = threading.Event()
        self.release.set()

    def hold(self):
        self.release.clear()

    def propose(self, request):
        self.release.wait(10)
        return super().propose(request)


def ask(decision, prompt, rationale, *, goal=None, context=(), updates=()):
    """A consultant reply: keep the literal input as a note and ask the next question."""
    def build(request):
        value = proposal(request)
        records = request["case"]["records"]
        refs = {"goal": next((r["ref"] for r in records if r["kind"] == "goal"), None)}
        notes = [r["ref"] for r in records if r["kind"] == "note"]
        value["proposed_updates"] += [{**deepcopy(u), "source_refs": [request["input"]["request_id"]]}
                                      for u in updates]
        value["intervention"].update(decision=decision, primary_prompt=prompt, rationale=rationale,
                                     purpose="clarify_next_decision")
        if goal or refs["goal"]:
            value["intervention"]["goal_ref"] = goal or refs["goal"]
        wanted = [refs.get(name) or (notes[int(name[5:])] if name.startswith("note:") else name)
                  for name in context]
        if wanted:
            value["intervention"]["required_context_refs"] = wanted
        return value
    return build


GOAL = {"operation": "record_goal", "temporary_id": "goal", "data": {
    "statement": "90% of orders delivered on time", "scope": "Forge workshop orders", "horizon": "October 30",
    "measure": "orders delivered on time / orders due", "baseline": "71% in September",
    "protections": ["95% of urgent requests acknowledged within four hours"]}}
# Each consultant reply in order: the participant's words, and the question asked next.
FORGE_REPLIES = [
    ("Late deliveries keep upsetting our customers.",
     ask("Define success", "What would count as dependable delivery for Forge?",
         "Everything after this is judged against the goal.")),
    ("90% of orders on time by October 30, and we keep acknowledging urgent requests within four hours.",
     ask("Inspect the baseline", "How many orders arrive on time today, and how do you know?",
         "A baseline makes a later result comparable.", updates=[GOAL])),
    ("The September delivery report says 71% of 412 orders shipped on time.",
     ask("Name what gets in the way", "What most often makes an order late?",
         "Causes point to changes worth testing.")),
    ("Priorities change daily, so jobs get interrupted halfway.",
     ask("Check the safeguard", "How would you notice urgent requests waiting too long?",
         "A safeguard is checked before any gain is claimed.")),
    ("We log acknowledgements in the urgent inbox; last month 96% within four hours.",
     ask("Compare explanations", "Could threatened delivery dates be causing the priority changes instead?",
         "Two explanations predict different things.")),
    ("Maybe both. Sales changes dates when a customer pushes.",
     ask("Pick a change", "Which change could you try within two weeks on your own authority?",
         "A small change you control is quick to learn from.")),
    ("Freeze each day's plan by 9:00 and keep two urgent slots open.",
     ask("Set the scope", "Which orders and which weeks would the trial cover?",
         "A bounded trial keeps any harm small.")),
    ("Payments orders only, for the next two weeks.",
     ask("Choose a test", "What do you expect the frozen plan with urgent slots to change, and by how much?",
         "A forecast written before the trial is what the result will be compared with.",
         context=("goal", "note:2", "note:3"))),
]
# Two imports bring in trees (no consultant call); each carries the current question on.
FORGE_TREES = {
    2: {"ltp": {"schema_version": "1.0", "project_id": "forge", "title": "Why orders are late",
                "entities": [{"id": "late", "tree": "current_reality", "statement": "Orders ship late"},
                             {"id": "interrupt", "tree": "current_reality",
                              "statement": "Jobs are interrupted halfway"},
                             {"id": "priorities", "tree": "current_reality",
                              "statement": "Priorities change daily"}],
                "designations": [{"id": "d1", "entity_id": "late", "role": "undesirable_effect"},
                                 {"id": "d2", "entity_id": "interrupt", "role": "intermediate_cause"},
                                 {"id": "d3", "entity_id": "priorities", "role": "root_cause"}],
                "relationships": [{"id": "r1", "tree": "current_reality", "kind": "causes",
                                   "from_entity_ids": ["interrupt"], "to_entity_id": "late"},
                                  {"id": "r2", "tree": "current_reality", "kind": "causes",
                                   "from_entity_ids": ["priorities"], "to_entity_id": "interrupt"}],
                "assumptions": [{"id": "a1", "relationship_id": "r1",
                                 "statement": "Recovery time after an interruption is not planned"}]}},
    4: {"ltp": {"schema_version": "1.0", "project_id": "forge", "title": "Respond or keep the plan",
                "entities": [{"id": "objective", "tree": "conflict", "statement": "Customers can rely on Forge"},
                             {"id": "respond", "tree": "conflict", "statement": "Respond to urgent needs"},
                             {"id": "change", "tree": "conflict", "statement": "Change the plan immediately"}],
                "designations": [{"id": "d1", "entity_id": "objective", "role": "cloud_objective"},
                                 {"id": "d2", "entity_id": "respond", "role": "cloud_requirement"},
                                 {"id": "d3", "entity_id": "change", "role": "cloud_prerequisite"}],
                "relationships": [{"id": "r1", "tree": "conflict", "kind": "necessary_for",
                                   "from_entity_ids": ["respond"], "to_entity_id": "objective"},
                                  {"id": "r2", "tree": "conflict", "kind": "requires",
                                   "from_entity_ids": ["respond"], "to_entity_id": "change"}],
                "assumptions": []}},
}


def build_forge(path, consultant, replies=FORGE_REPLIES, trees=FORGE_TREES):
    """The Forge commons at revision 10: after the given number of consultant replies, a tree import
    follows the replies named in ``trees``. Every step goes through a use case. Sam created the commons to
    accept proposals automatically, so each reply's records are in the model in the reply's own revision
    and the commons' history keeps the numbers the navigation scenarios name."""
    create_case(path, "Forge", acceptance="automatic", actor=SPEAKER).close()
    consultant.responses.extend(build for _, build in replies)
    for index, (words, _) in enumerate(replies, start=1):
        with open_case(path, consultant=consultant) as app:
            target = app.workspace()["target"]
            result = app.submit(words, SPEAKER, target["base_revision"], target["response_target"])
            assert result["status"] == "saved", result
        if index in trees:
            source = path.parent / f"forge-{index}.ltp.yaml"
            source.write_text(yaml.safe_dump(trees[index], sort_keys=False))
            import_trees(path, str(source), SPEAKER)
    return path
