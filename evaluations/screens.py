"""Replay a semantic run through the real workspace and keep the screens its operator would have seen.

A run's report holds every reply the consultant gave, and its case holds every input with its speaker, intent,
declarations and time. Replaying them builds the same case again, but the evaluated turns go through the Textual
workspace: the turn's words are put in the answer box and sent the way a person sends them (Send, or the Other
moves entry for a turn that asked for advice or an observation), and a stand-in consultant returns the recorded
reply instead of calling a model. What the workspace shows as each reply lands, the changes it names included,
is exported as SVG.

Nothing is judged here. The replay refuses to produce screens unless it reproduces the recorded case exactly:
the same request identities, the same replies and the same revisions. Setup inputs go through the application
use cases, as the run's own setup did, and are not drawn.
"""

import asyncio
from copy import deepcopy
from pathlib import Path

from textual.widgets import TextArea

from reason_commons.adapters.settings import Settings
from reason_commons.adapters.tui import ReasonCommonsApp
from reason_commons.bootstrap import create_case, open_case

SIZES = {"wide": (120, 40), "small": (80, 24)}
# The intents a person sends from Other moves, with the entry's words.
OTHER_MOVES = {"direct_advice": "Ask for direct advice", "explain_observation": "Ask for help planning an observation"}
NO_DECLARATION_CONTROL = ("The workspace has no control for declaring an owner or observed evidence, so this turn's "
                          "declaration was sent the way the command line sends it; the screen after it is the "
                          "workspace's own.")


class ReplayMismatch(ValueError):
    """The replay did not reproduce the recorded run, so its screens would not be the run's."""


class ReplayClock:
    """Each step happens at the time recorded for it, so dates on screen are the run's."""

    def __init__(self, value):
        self.value = value

    def now(self):
        return self.value


class ReplayConsultant:
    """Returns the reply recorded for each request, attempt by attempt; an attempt that recorded none fails."""

    def __init__(self, attempts):
        self.attempts = {request: list(items) for request, items in attempts.items()}
        self.version = "evaluation-replay/1"

    def propose(self, request):
        items = self.attempts.get(request["input"]["request_id"])
        if not items:
            raise ReplayMismatch(f"No recorded attempt for {request['input']['request_id']}")
        item = items.pop(0)
        if item is None:
            raise ConnectionError("The recorded attempt received no reply")
        self.version = item["version"]
        return deepcopy(item["proposal"])


def recorded_case(report_directory, run_id):
    """The run's own case: its folder, or the archive exported when the run ended."""
    folder = Path(report_directory) / run_id
    if folder.is_dir():
        return folder
    archive = folder.with_name(run_id + ".reasoncase")
    if archive.exists():
        return archive
    raise ReplayMismatch(f"{run_id}: neither the case folder nor its .reasoncase is beside the report")


def attempts_of(receipts):
    """Each attempt's reply in order, or None for an attempt that received none."""
    by_number = {}
    for item in receipts["attempts"]:
        by_number.setdefault(item["attempt"], None)
        if "proposal" in item:
            by_number[item["attempt"]] = {"proposal": item["proposal"], "version": item["version"]}
    return [by_number[number] for number in sorted(by_number)]


def comparable(value):
    """A case's history without what differs between any two copies: its identity and wall-clock times."""
    if isinstance(value, dict):
        return {k: comparable(v) for k, v in value.items() if k not in {"case_id", "timestamp"}}
    if isinstance(value, list):
        return [comparable(v) for v in value]
    return value


def read_run(report_directory, run):
    """The recorded case's inputs, replies and history, checked against the report's own turns."""
    with open_case(str(recorded_case(report_directory, run["id"])), writable=False) as case:
        history = case.history()["revisions"]
        sources = case.sources()["sources"]
        inputs = sorted((s for s in sources.values() if "request_id" in s), key=lambda s: s["request_id"])
        attempts = {s["request_id"]: attempts_of(case.receipts(s["request_id"])) for s in inputs}
    evaluated = [turn["result"].get("request_id") for turn in run["turns"]]
    for turn, request in zip(run["turns"], evaluated):
        source = sources.get(request) if request else None
        if not source or source["text"] != turn["text"] or source["speaker"] != turn["speaker"]:
            raise ReplayMismatch(f"{run['id']} turn {turn['number']}: the case's input is not the report's")
        if attempts_of(turn.get("receipts") or {"attempts": []}) != attempts[request]:
            raise ReplayMismatch(f"{run['id']} turn {turn['number']}: the case's replies are not the report's")
    return history, inputs, attempts, evaluated


def screenshot(app, directory, name):
    path = Path(directory) / f"{name}.svg"
    path.write_text(app.export_screenshot(), encoding="utf-8")
    return path.name


async def type_answer(app, pilot, text):
    """Put the words in the answer box, with the caret after them, as a person leaves it before sending."""
    editor = app.query_one("#editor", TextArea)
    editor.load_text(text)
    editor.move_cursor(editor.document.end)
    editor.focus()
    await pilot.pause()


async def send(app, pilot, source):
    """Send what the answer box holds as the workspace sends it."""
    if source.get("declarations"):
        # The command line's path: retain the input with its declaration, then consult; the workspace then
        # receives the result as it receives its own.
        target = app.workspace_value["target"]
        app.set_busy(True)

        def work():
            try:
                result = app.case.retain_input(source["text"], app.speaker, target["base_revision"],
                                               target["response_target"], intent=source["intent"],
                                               declarations=source["declarations"])
                if result["status"] == "input_retained":
                    result = app.case.consult(result["request_id"])
            except Exception as exc:
                result = {"status": "not_saved", "message": f"Not saved ({type(exc).__name__})."}
            app.call_from_thread(app._submitted, result, source["text"])
        app.run_worker(work, thread=True, exclusive=True)
    elif source["intent"] == "answer":
        app.action_send()
    else:
        app.other_move(source["intent"])
    await app.workers.wait_for_complete()
    await pilot.pause(0.3)


async def views(app, pilot, directory, prefix):
    """The reply as it lands, at both sizes, then each view a reviewer may need, as a person would open them."""
    shots = [{"file": screenshot(app, directory, f"{prefix}-next"), "view": "Next step", "size": "120×40"}]
    await pilot.resize_terminal(*SIZES["small"])
    await pilot.pause(0.3)
    shots.append({"file": screenshot(app, directory, f"{prefix}-next-80x24"), "view": "Next step",
                  "size": "80×24"})
    await pilot.resize_terminal(*SIZES["wide"])
    await pilot.pause(0.3)
    workspace = app.case.workspace(view="trees")
    wanted = [("context", "Case context")]
    # The Goal Tree always holds the case's goal; the view is worth drawing once anything else is in the trees.
    if any(tree["claims"] for tree in workspace["trees"] if tree["tree"] != "goal") or any(
            len(tree["claims"]) > 1 for tree in workspace["trees"] if tree["tree"] == "goal"):
        wanted.insert(0, ("trees", "Trees"))
    if app.case.workspace(view="backlog").get("backlog"):
        wanted.append(("backlog", "Backlog"))
    for name, label in wanted:
        app.show_view(name)
        await pilot.pause(0.3)
        shots.append({"file": screenshot(app, directory, f"{prefix}-{name}"), "view": label, "size": "120×40"})
    app.show_view("next")
    await pilot.pause()
    return shots


async def drive(path, provider, clock, consultant, turns, directory):
    """One workspace session per speaker, as an operator relaunches with --speaker; each turn sent through it."""
    screens = []
    index = 0
    while index < len(turns):
        speaker = turns[index]["speaker"]
        # Reviewers judge the replies, so a new goal's first-use note stays out of their screens.
        app = ReasonCommonsApp(str(path), speaker, provider,
                               lambda c: open_case(str(path), consultant=c, clock=clock), lambda _: consultant,
                               settings=Settings(data={"welcome": "hidden"}))
        async with app.run_test(size=SIZES["wide"]) as pilot:
            await pilot.pause()
            while index < len(turns) and turns[index]["speaker"] == speaker:
                source = turns[index]
                clock.value = source["timestamp"]
                prefix = f"turn{index + 1}"
                entry = {"number": index + 1, "request_id": source["request_id"], "speaker": speaker,
                         "intent": source["intent"], "sent_with": OTHER_MOVES.get(source["intent"], "Send"),
                         "notes": [], "screens": []}
                await type_answer(app, pilot, source["text"])
                if index == 0:  # the question as the operator first met it; later ones are the last reply's
                    entry["before"] = {"file": screenshot(app, directory, f"{prefix}-answering"),
                                       "view": "Next step, answer typed", "size": "120×40"}
                if source.get("declarations"):
                    entry["notes"].append(NO_DECLARATION_CONTROL)
                await send(app, pilot, source)
                entry["screens"] = await views(app, pilot, directory, prefix)
                screens.append(entry)
                index += 1
            if getattr(app, "_save_timer", None):
                app._save_timer.stop()  # a pending draft save must not fire while the app shuts down
            await pilot.pause(0.5)  # let the last view finish drawing before the workspace closes
    return screens


def replay_run(report_directory, run, provider, work, directory):
    """Rebuild the run's case in ``work`` and write its screens to ``directory``; return what each turn shows."""
    history, inputs, attempts, evaluated = read_run(report_directory, run)
    first = history[0]
    actor = next((d["actor"] for d in first.get("decisions", []) if d["action"] == "acceptance"), None)
    clock = ReplayClock(first["timestamp"])
    Path(work).mkdir(parents=True, exist_ok=True)
    path = Path(work) / run["id"]
    consultant = ReplayConsultant(attempts)
    case = create_case(str(path), first["name"], consultant=consultant, timezone=first["timezone"], clock=clock,
                       acceptance=first.get("membership", {}).get("acceptance", "review"), actor=actor)
    with case:
        for source in inputs:
            if source["request_id"] in evaluated:
                break
            clock.value = source["timestamp"]
            current = case.inspect()["case"]
            case.submit(source["text"], source["speaker"], current["revision"], current["current_intervention"],
                        intent=source["intent"], declarations=source.get("declarations") or None,
                        request_id=source["request_id"])
    turns = [next(s for s in inputs if s["request_id"] == request) for request in evaluated if request]
    Path(directory).mkdir(parents=True, exist_ok=True)
    screens = asyncio.run(drive(path, provider, clock, consultant, turns, directory))
    with open_case(str(path), writable=False) as replayed:
        if comparable(replayed.history()["revisions"]) != comparable(history):
            raise ReplayMismatch(f"{run['id']}: the replay did not reproduce the recorded case")
        sent = sorted((s for s in replayed.sources()["sources"].values() if "request_id" in s),
                      key=lambda s: s["request_id"])
    # Each input as the run retained it: the same words, speaker, target, intent, declarations and time.
    if sent != inputs:
        raise ReplayMismatch(f"{run['id']}: the workspace sent different inputs than the run")
    return screens
