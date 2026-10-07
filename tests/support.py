"""Fixture adapters. Acceptance steps use application use cases for setup too."""

from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from reason_commons.application.ports import StoreError
from reason_commons.application.service import CaseApplication
from reason_commons.bootstrap import create_case


ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def timezone(name):
    """Run with this time zone as the computer's own, and put the real one back (``TZ`` and the C library's)."""
    original = os.environ.get("TZ")
    os.environ["TZ"] = name
    time.tzset()
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original
        time.tzset()


def proposal(request):
    return {"schema_version": "1", "delivery_profile": "p2",
            "request_id": request["input"]["request_id"], "base_revision": request["input"]["base_revision"],
            "intervention": {"kind": "question", "purpose": "clarify_next_decision",
                             "primary_prompt": "What should we observe next?", "rationale": "Keep the next move bounded."},
            "proposed_updates": [{"operation": "record_note", "data": {"text": request["input"]["text"],
                                      "basis": "participant_report"}, "source_refs": [request["input"]["request_id"]]}]}


def bounded_case(request, source=None):
    value = proposal(request)
    refs = [request["input"]["request_id"]] + ([source] if source else [])
    value["proposed_updates"] += [
        {"operation": "record_goal", "temporary_id": "goal", "data": {
            "statement": "90% on time", "scope": "Payments", "horizon": "October 30",
            "measure": "on-time deliveries / deliveries due", "baseline": None,
            "protections": ["95% acknowledged within four hours"]}, "source_refs": refs},
        {"operation": "record_test", "temporary_id": "test", "data": {
            "statement": "Bounded release pilot", "goal_ref": "goal", "scope": "Two weeks, Payments",
            "forecast": [{"measure": "delivery", "expected": "80%", "scope": "pilot", "denominator": "deliveries due"},
                         {"measure": "acknowledgement", "expected": "95%", "scope": "pilot", "denominator": "urgent requests"}],
            "stop_condition": "Acknowledgement below 95%", "review_date": "October 16"}, "source_refs": refs}]
    value["intervention"].update(goal_ref="goal", required_context_refs=["goal", "test"])
    return value


class ScriptedConsultant:
    version = "fixture/1"

    def __init__(self, responses=None):
        self.calls = []
        self.responses = list(responses or [])
        self.default = proposal

    def propose(self, request):
        self.calls.append(deepcopy(request))
        item = self.responses.pop(0) if self.responses else self.default
        if isinstance(item, Exception):
            raise item
        return item(request) if callable(item) else deepcopy(item)


class FaultStore:
    """Storage fault injection at the outbound port, not in step assertions."""

    def __init__(self, store):
        self.store = store
        self.failures = {}

    def fail(self, method, count=1):
        self.failures[method] = count

    def __getattr__(self, name):
        member = getattr(self.store, name)
        if not callable(member):
            return member

        def call(*args, **kwargs):
            if self.failures.get(name, 0):
                self.failures[name] -= 1
                raise StoreError(f"Injected {name} failure")
            return member(*args, **kwargs)
        return call


def fixture_app(path, consultant=None):
    original = create_case(path, "Payments")
    # Composition setup may choose outbound adapters; steps never call a repository.
    faults = FaultStore(original._store)
    app = CaseApplication(faults, original._clock, consultant)
    return app, faults


def submit(app, text="A participant report", request_id=None, declarations=None):
    case = app.inspect()["case"]
    return app.submit(text, "Sam", case["revision"], case["current_intervention"],
                      request_id=request_id, declarations=declarations)


def accept_all(app, speaker="Sam"):
    """Accept every waiting proposal, as an operator pressing Accept all would."""
    waiting = [e["ref"] for e in app.workspace(view="backlog")["backlog"] if e["entry"] == "proposal"]
    if not waiting:
        return None
    result = app.accept(waiting, speaker, app.inspect()["case"]["revision"], confirmed=True)
    assert result["status"] == "saved", result
    return result


def automatic(app, speaker="Sam"):
    """Set the case to accept proposals automatically."""
    result = app.set_acceptance("automatic", speaker, app.inspect()["case"]["revision"])
    assert result["status"] == "saved", result
    return result


def retain(app, text="A participant report", request_id=None):
    case = app.inspect()["case"]
    return app.retain_input(text, "Sam", case["revision"], case["current_intervention"], request_id=request_id)


def seed(app, consultant, revision=1):
    consultant.responses.append(bounded_case)
    assert submit(app, "Pilot and original forecast")["status"] == "saved"
    while app.inspect()["case"]["revision"] < revision:
        assert submit(app)["status"] == "saved"


def cursor(app, draft="5 requests?\n:options", **changes):
    case = app.inspect()["case"]
    value = {"view": "history", "focus": "response", "selection": "P1@1", "scroll_anchor": "forecast",
             "draft": draft, "caret": len(draft), "speaker": "Sam", "response_target": case["current_intervention"],
             "base_revision": case["revision"], "display": "compact"}
    value.update(changes)
    return value


def cli(*arguments):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", ""))
    return subprocess.run([sys.executable, "-m", "reason_commons", *map(str, arguments)],
                          env=env, capture_output=True, text=True, timeout=15)


def cli_json(*arguments):
    result = cli(*arguments)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)

