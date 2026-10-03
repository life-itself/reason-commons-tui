"""User entry points against a real HTTP adapter, with authored model responses."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread

import pytest

from reason_commons.adapters.invocation import procedure_text, run_contribution
from reason_commons.adapters.lm_studio import LMStudioConsultant
from reason_commons.bootstrap import create_case, open_case
from tests.support import cli, fixture_app, proposal


@pytest.fixture
def skill_server():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, value, status=200):
            data = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.respond({"data": [{"id": "fixture-model"}]})

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if "tools" in payload:
                authorization = json.loads(payload["messages"][1]["content"])
                last = payload["messages"][-1]
                if self.server.claim_only:
                    message = {"content": "Everything saved"}
                elif last["role"] == "user":
                    name, args = (("retry", {"request_id": authorization["request_id"]})
                                  if authorization["operation"] == "retry" else ("inspect", {}))
                    message = self.call(name, args)
                else:
                    result = json.loads(last["content"])
                    previous = payload["messages"][-2]["tool_calls"][0]["function"]["name"]
                    if previous == "inspect":
                        case = result["case"]
                        message = self.call("retain_input", {"text": authorization["text"],
                            "speaker": authorization["speaker"], "declarations": authorization["declarations"],
                            "base_revision": case["revision"], "response_target": case["current_intervention"]})
                    elif previous == "retain_input" and result["status"] == "input_retained" and not self.server.stop_after_retain:
                        message = self.call("consult", {"request_id": result["request_id"]})
                    else:
                        message = {"content": "Application status: " + result["status"]}
                self.respond({"model": payload["model"], "choices": [{
                    "finish_reason": "tool_calls" if "tool_calls" in message else "stop", "message": message}]})
            else:
                self.server.consult_calls += 1
                if self.server.fail_consult:
                    self.respond({}, 503)
                else:
                    request = json.loads(payload["messages"][1]["content"])
                    self.server.inputs.append(request["input"])
                    response = proposal(request)
                    response["proposed_updates"][0]["temporary_id"] = "note"
                    self.respond({"model": payload["model"], "choices": [{"finish_reason": "stop",
                                  "message": {"content": json.dumps(response)}}]})

        def call(self, name, arguments):
            self.server.tool_count += 1
            return {"content": None, "tool_calls": [{"id": "call-" + str(self.server.tool_count),
                    "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}]}

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.url = f"http://127.0.0.1:{server.server_port}/v1"
    server.fail_consult = server.claim_only = server.stop_after_retain = False
    server.consult_calls = server.tool_count = 0
    server.inputs = []
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


@pytest.mark.parametrize("runner", ["agent", "procedure"])
def test_cli_contribution_preserves_literal_input_restarts_and_retry_is_idempotent(skill_server, tmp_path, runner):
    store, text = tmp_path / "case", "5\n:options\nExactly this text.\n"
    with create_case(store, "Own case"):
        pass
    source = tmp_path / "input.txt"
    source.write_text(text)
    result = cli("contribute", store, "--speaker", "Sam", "--text-file", source,
                 "--runner", runner, "--model", "fixture-model", "--base-url", skill_server.url, "--json")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["procedure_completed"] and report["result"]["status"] == "saved"
    request_id = report["result"]["request_id"]
    with open_case(store, writable=False) as app:
        assert app.inspect()["case"]["revision"] == 1
        assert app.sources()["sources"][request_id]["text"] == text
    retry = cli("retry", store, request_id, "--runner", runner, "--model", "fixture-model", "--base-url", skill_server.url, "--json")
    assert retry.returncode == 0 and json.loads(retry.stdout)["result"]["already_applied"]
    assert skill_server.consult_calls == 1
    assert json.loads(cli("receipts", store, request_id).stdout)["attempts"]


def test_cli_failure_retains_identity_and_explicit_retry_uses_it_after_restart(skill_server, tmp_path):
    store = tmp_path / "case"
    with create_case(store):
        pass
    skill_server.fail_consult = True
    failed = cli("contribute", store, "--speaker", "Sam", "--text", "literal", "--model", "fixture-model",
                 "--base-url", skill_server.url, "--json")
    assert failed.returncode == 1
    report = json.loads(failed.stdout)
    assert report["procedure_completed"] and report["result"]["status"] == "unavailable"
    assert skill_server.consult_calls == 1
    request_id = report["result"]["request_id"]
    skill_server.fail_consult = False
    retried = cli("retry", store, request_id, "--model", "fixture-model", "--base-url", skill_server.url, "--json")
    assert retried.returncode == 0 and json.loads(retried.stdout)["result"]["request_id"] == request_id
    assert skill_server.inputs[0]["text"] == "literal"
    assert skill_server.consult_calls == 2


@pytest.mark.parametrize("mode,status", [("claim_only", "skill_incomplete"), ("stop_after_retain", "input_retained")])
def test_model_claim_or_retention_alone_is_not_a_successful_cli_invocation(skill_server, tmp_path, mode, status):
    setattr(skill_server, mode, True)
    store = tmp_path / "case"
    with create_case(store):
        pass
    result = cli("contribute", store, "--speaker", "Sam", "--text", "literal", "--model", "fixture-model",
                 "--base-url", skill_server.url, "--runner", "agent", "--json")
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["result"]["status"] == status and not report["procedure_completed"]
    assert skill_server.consult_calls == 0
    with open_case(store, writable=False) as app:
        assert app.inspect()["case"]["revision"] == 0


def test_failed_retention_stops_runner_before_consulting(skill_server, tmp_path):
    consultant = LMStudioConsultant("fixture-model", skill_server.url)
    app, faults = fixture_app(tmp_path / "case", consultant)
    with app:
        faults.fail("retain")
        report = run_contribution(app, consultant, text="literal", speaker="Sam", runner="procedure")
        assert report["result"]["status"] == "not_saved" and report["procedure_completed"]
        assert skill_server.consult_calls == 0


def test_packaged_skill_references_remain_accessible():
    from importlib.resources import files
    import re
    root = files("reason_commons.adapters").joinpath("contribution_skill")
    assert procedure_text()
    for path in re.findall(r"\]\(([^)]+)\)", procedure_text()):
        assert root.joinpath(path).is_file(), path
