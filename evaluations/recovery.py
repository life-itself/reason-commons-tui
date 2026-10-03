"""Non-destructive real-server failures and received-response recovery.

No server shutdown or unloading of a model someone else may be using. A
connection interrupt is scoped to a disposable worker, not the LM Studio app.
"""

import os
from pathlib import Path
import subprocess
import sys
import time

from reason_commons.adapters.lm_studio import LMStudioConsultant
from reason_commons.application.ports import StoreError
from reason_commons.application.service import CaseApplication
from reason_commons.bootstrap import create_case, open_case
from evaluations.report import check


class CountConsultant:
    def __init__(self, delegate):
        self.delegate = delegate
        self.calls = 0

    @property
    def version(self):
        return self.delegate.version

    def propose(self, request):
        self.calls += 1
        return self.delegate.propose(request)


class CommitFault:
    def __init__(self, store):
        self.store = store

    def commit(self, *args):
        raise StoreError("Authored storage fault after real provider response")

    def __getattr__(self, name):
        return getattr(self.store, name)


class NoInference:
    version = "evaluation/no-inference"

    def __init__(self):
        self.calls = 0

    def propose(self, request):
        self.calls += 1
        raise AssertionError("Recovery must use the received proposal")


def _configured(original, **overrides):
    values = dict(model=original.model, base_url=original.base_url, api_key=original._api_key,
                  timeout=original.timeout, temperature=original.temperature, max_tokens=original.max_tokens)
    values.update(overrides)
    return LMStudioConsultant(**values)


def run_recovery_suite(report, transport):
    probes = (
        ("timeout", {"timeout": 0.001}, "A synthetic observation for a local recovery check.", "unavailable"),
        ("unknown_model", {"model": "reason-commons-evaluation-nonexistent-model"}, "Synthetic input.", "unavailable"),
        ("truncated_generation", {"max_tokens": 1}, "Synthetic input.", "rejected"),
        ("context_overflow", {}, "Synthetic oversized context. " + "unrelated observation " * 20000, "unavailable"),
    )
    for name, config, text, expected in probes:
        identity = "recovery-" + name
        print("RUN " + identity, flush=True)
        provider = CountConsultant(_configured(transport, **config))
        path = report.directory / identity
        with create_case(str(path), consultant=provider) as app:
            result = app.submit(text, "Sam", 0, None)
            request_id = result["request_id"]
            checks = [check("real failure category", result["status"] == expected, result["status"]),
                      check("no automatic provider retry", provider.calls == 1, provider.calls),
                      check("no reasoning revision committed", app.inspect()["case"]["revision"] == 0)]
        # Reopen offline first: failure/retry state survives the process session.
        with open_case(str(path), writable=False) as app:
            source = app.sources()["sources"][request_id]
            checks += [check("literal input survives restart", source["text"] == text and source["speaker"] == "Sam"),
                       check("failure receipt survives restart", any(a.get("status") == expected
                             for a in app.receipts(request_id)["attempts"]))]
        # The deliberately oversized input cannot become a smaller implicit retry.
        if name == "context_overflow":
            report.append({"id": identity, "case": str(path), "checks": checks,
                           "result": result, "next": "Explicitly revise context; no truncation or smaller-input retry"})
            continue
        good = CountConsultant(_configured(transport))
        with open_case(str(path), consultant=good) as app:
            recovered = app.retry(request_id)
            checks += [check("explicit retry uses original identity", recovered.get("request_id") == request_id),
                       check("explicit retry publishes", recovered["status"] == "saved", recovered["status"])]
            if recovered["status"] == "saved":
                revision = app.inspect()["case"]["revision"]
                again = app.retry(request_id)
                checks.append(check("applied retry is idempotent without another inference",
                                    again.get("already_applied") is True and good.calls == 1
                                    and app.inspect()["case"]["revision"] == revision))
        report.append({"id": identity, "case": str(path), "checks": checks,
                       "result": result, "recovered": recovered})

    _received_recovery(report, transport)
    _interrupted_worker(report, transport)


def _received_recovery(report, transport):
    identity = "recovery-received_response"
    print("RUN " + identity, flush=True)
    path = report.directory / identity
    provider = CountConsultant(transport)
    original = create_case(str(path), consultant=provider)
    with CaseApplication(CommitFault(original._store), original._clock, provider) as app:
        result = app.submit("We want fewer late deliveries while protecting urgent requests.", "Sam", 0, None)
    checks = [check("commit fault follows real retained response", result["status"] == "not_saved", result["status"])]
    forbidden = NoInference()
    with open_case(str(path), consultant=forbidden) as app:
        recovered = app.retry(result["request_id"])
        checks += [check("restart publishes original received proposal", recovered["status"] == "saved", recovered["status"]),
                   check("restart recovery makes zero inferences", forbidden.calls == 0, forbidden.calls),
                   check("original model provenance retained", app.inspect()["case"]["adapter_versions"].get(
                         result["request_id"]) == transport.version)]
    report.append({"id": identity, "case": str(path), "checks": checks,
                   "setup": "real LM response, authored storage commit fault", "result": result, "recovered": recovered})


def _interrupted_worker(report, transport):
    identity = "recovery-interrupted_client"
    print("RUN " + identity, flush=True)
    path = report.directory / identity
    marker = report.directory / "interrupted-request-started"
    root = Path(__file__).resolve().parents[1]
    environment = dict(os.environ, PYTHONPATH=str(root / "src") + os.pathsep + str(root))
    process = subprocess.Popen([sys.executable, "-m", "evaluations.recovery", str(path), str(marker),
                                transport.model, transport.base_url], env=environment,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    interrupted = False
    try:
        deadline = time.monotonic() + 15
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        if marker.exists():
            # The worker has entered the real HTTP call. Terminate only this client.
            time.sleep(0.5)
            if process.poll() is None:
                process.kill()
                interrupted = True
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
    checks = [check("disposable client killed during provider call", interrupted)]
    good = CountConsultant(transport)
    with open_case(str(path), consultant=good) as app:
        sources = app.sources()["sources"]
        request_id = next(s for s in sources if "request_id" in sources[s])
        retained = sources[request_id]
        checks += [check("retained input and exact initial target survive process kill",
                         retained["text"] == "A synthetic situation with late deliveries." and
                         retained["base_revision"] == 0 and retained["response_target"] is None),
                   check("no unconfirmed revision visible", app.inspect()["case"]["revision"] == 0)]
        result = app.retry(request_id)
        checks.append(check("explicit retry after client interruption publishes", result["status"] == "saved", result["status"]))
    report.append({"id": identity, "case": str(path), "checks": checks, "recovered": result,
                   "setup": "client process killed after entering real HTTP; server remains running"})


if __name__ == "__main__":
    path, marker, model, url = sys.argv[1:]

    class StartedConsultant(LMStudioConsultant):
        def chat_completion(self, payload):
            Path(marker).write_text("HTTP call entered")
            return super().chat_completion(payload)

    provider = StartedConsultant.from_env(model=model, base_url=url)
    with create_case(path, consultant=provider) as app:
        app.submit("A synthetic situation with late deliveries.", "Sam", 0, None)
