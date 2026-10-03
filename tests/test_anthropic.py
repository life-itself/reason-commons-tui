"""Native Anthropic protocol, provider selection and durable case integration."""

import asyncio
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Thread

import jsonschema
import pytest

from reason_commons.adapters.anthropic import AnthropicConsultant, AnthropicError, DEFAULT_MODEL
from reason_commons.application.ports import ConsultantResponseError
from reason_commons.bootstrap import configured_consultant, create_case, open_case
from tests.support import bounded_case, cli, submit


@pytest.fixture
def anthropic_server():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, value, status=200, headers=None):
            body = value if isinstance(value, bytes) else json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self.server.requests.append(("GET", self.path, dict(self.headers), None))
            if self.server.get_status != 200:
                self.respond({"error": "fixture-secret: unsafe server body"}, self.server.get_status)
            else:
                self.respond({"id": DEFAULT_MODEL, "max_input_tokens": 1000000})

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.server.requests.append(("POST", self.path, dict(self.headers), payload))
            if self.path == "/v1/messages/count_tokens":
                self.respond({"input_tokens": 12345})
                return
            if self.server.custom is not None:
                self.respond(*self.server.custom)
                return
            request = json.loads(payload["messages"][0]["content"])
            proposal = bounded_case(request)
            for i, update in enumerate(proposal["proposed_updates"]):
                update.setdefault("temporary_id", f"temp_update_{i}")
            jsonschema.validate(proposal, payload["tools"][0]["input_schema"])
            response = {"model": payload["model"], "stop_reason": "tool_use", "content": [
                {"type": "tool_use", "name": "submit_proposal", "id": "fixture-call", "input": proposal}]}
            if self.server.transform:
                self.server.transform(response)
            self.respond(response)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.requests, server.custom, server.transform, server.get_status = [], None, None, 200
    server.url = f"http://127.0.0.1:{server.server_port}/v1"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def adapter(server):
    return AnthropicConsultant(base_url=server.url, api_key="fixture-secret")


def test_native_consultation_sends_complete_context_and_persists_without_secret(anthropic_server, tmp_path):
    consultant = adapter(anthropic_server)
    store = tmp_path / "case"
    with create_case(store, consultant=consultant) as app:
        source = app.add_source("literal.txt", b"Original evidence", "Sam")
        result = submit(app)
        assert result["status"] == "saved"
        state = app.inspect()["case"]
        assert state["adapter_versions"]["in000001"] == consultant.version
        assert app.retry("in000001")["already_applied"]
    assert [(method, path) for method, path, _, _ in anthropic_server.requests] == [
        ("GET", "/v1/models/" + DEFAULT_MODEL), ("POST", "/v1/messages")]
    _, _, headers, payload = anthropic_server.requests[-1]
    assert headers["X-Api-Key"] == "fixture-secret"
    assert headers["Anthropic-Version"] == "2023-06-01"
    assert payload["model"] == DEFAULT_MODEL
    assert payload["tool_choice"] == {"type": "auto", "disable_parallel_tool_use": True}
    assert payload["stream"] is False
    assert "Reasoning Case" in payload["system"]
    request = json.loads(payload["messages"][0]["content"])
    assert source in request["sources"] and "in000001" in request["sources"]
    assert request["case"]["revision"] == 0
    assert request["input"]["text"] == "A participant report"
    with open_case(store, writable=False) as app:
        assert app.inspect()["case"] == state
    assert not any(b"fixture-secret" in path.read_bytes() for path in store.rglob("*.yaml"))


def test_count_tokens_is_read_only_and_uses_the_full_generation_prompt(anthropic_server):
    consultant = adapter(anthropic_server)
    request = {"input": {"request_id": "in001", "base_revision": 0, "text": "literal"}, "case": {}, "sources": {}}
    before = deepcopy(request)
    assert consultant.count_tokens(request) == 12345
    assert request == before
    assert anthropic_server.requests[-1][1] == "/v1/messages/count_tokens"
    payload = anthropic_server.requests[-1][3]
    assert "max_tokens" not in payload and "stream" not in payload
    assert json.loads(payload["messages"][0]["content"]) == request
    assert not any(path == "/v1/messages" for _, path, _, _ in anthropic_server.requests)


@pytest.mark.parametrize("change", [
    lambda r: r.update(stop_reason="max_tokens"),
    lambda r: r.update(stop_reason="refusal"),
    lambda r: r.update(stop_reason="end_turn"),
    lambda r: r.update(model="different-model"),
    lambda r: r.update(content=[]),
    lambda r: r["content"].append(deepcopy(r["content"][0])),
    lambda r: r["content"][0].update(name="execute_command"),
    lambda r: r["content"][0].update(input="invalid"),
    lambda r: r["content"][0]["input"].update(base_revision=999),
])
def test_invalid_responses_never_publish_or_retry_automatically(anthropic_server, tmp_path, change):
    anthropic_server.transform = change
    with create_case(tmp_path / "case", consultant=adapter(anthropic_server)) as app:
        result = submit(app)
        assert result["status"] == "rejected"
        assert app.inspect()["case"]["revision"] == 0
        assert app.workspace()["pending_requests"][0]["input"]["text"] == "A participant report"
    assert len(anthropic_server.requests) == 2


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500])
def test_http_failure_is_sanitized_and_explicit_recovery_keeps_input(anthropic_server, tmp_path, status):
    anthropic_server.get_status = status
    consultant = adapter(anthropic_server)
    with pytest.raises(AnthropicError) as error:
        consultant.model_metadata()
    assert error.value.http_status == status and "fixture-secret" not in str(error.value)
    with create_case(tmp_path / "case", consultant=consultant) as app:
        failed = submit(app, "Preserve this exact reply.\n2.")
        assert failed["status"] == "unavailable"
        assert "fixture-secret" not in str(app.receipts(failed["request_id"]))
        anthropic_server.get_status = 200
        saved = app.retry(failed["request_id"])
        assert saved["status"] == "saved" and saved["request_id"] == failed["request_id"]
    request = json.loads(anthropic_server.requests[-1][3]["messages"][0]["content"])
    assert request["input"]["text"] == "Preserve this exact reply.\n2."


@pytest.mark.parametrize("body", [b"not-json", b'{"model":"one","model":"two"}', b'{"bad":NaN}'])
def test_malformed_json_is_rejected(anthropic_server, body):
    anthropic_server.custom = (body,)
    with pytest.raises(ConsultantResponseError):
        adapter(anthropic_server).propose({"input": {"request_id": "in1", "base_revision": 0}, "case": {}, "sources": {}})


def test_redirect_cannot_forward_key_to_another_endpoint(anthropic_server):
    anthropic_server.custom = (b"", 307, {"Location": anthropic_server.url + "/capture"})
    with pytest.raises(AnthropicError) as error:
        adapter(anthropic_server).propose({"input": {"request_id": "in1", "base_revision": 0}, "case": {}, "sources": {}})
    assert error.value.http_status == 307
    assert len(anthropic_server.requests) == 2


def test_keyless_offline_reads_work_and_consult_stops_before_http(tmp_path):
    consultant = AnthropicConsultant()
    with create_case(tmp_path / "case", consultant=consultant) as app:
        assert app.workspace()["revision"] == 0
        assert submit(app)["status"] == "unavailable"
        assert app.inspect()["case"]["revision"] == 0
    with pytest.raises(AnthropicError, match="ANTHROPIC_API_KEY"):
        consultant.model_metadata()


def test_provider_selection_and_cli_keep_agent_runner_explicit(anthropic_server, tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-secret")
    monkeypatch.setenv("REASON_COMMONS_PROVIDER", "anthropic")
    monkeypatch.setenv("REASON_COMMONS_ANTHROPIC_URL", anthropic_server.url)
    assert isinstance(configured_consultant(), AnthropicConsultant)
    from reason_commons.adapters.lm_studio import LMStudioConsultant
    assert isinstance(configured_consultant(provider="lm-studio"), LMStudioConsultant)
    with pytest.raises(ValueError, match="Choose provider"):
        configured_consultant(provider="unknown")
    store = tmp_path / "case"
    cli("new", "--store", store)
    rejected = cli("contribute", store, "--speaker", "Sam", "--text", "literal", "--runner", "agent")
    assert rejected.returncode == 1 and "requires lm-studio" in rejected.stderr
    assert anthropic_server.requests == []
    with open_case(store, writable=False) as app:
        assert app.workspace()["pending_requests"] == []
    saved = cli("contribute", store, "--speaker", "Sam", "--text", "literal", "--json")
    assert saved.returncode == 0 and json.loads(saved.stdout)["result"]["status"] == "saved"


def test_desktop_launcher_loads_unexported_key_and_serves_native_anthropic(anthropic_server, tmp_path):
    mcp = pytest.importorskip("mcp")
    from mcp.client.stdio import stdio_client
    with create_case(tmp_path / "case"):
        pass
    shell = tmp_path / "shell"
    shell.mkdir()
    (shell / ".zshrc").write_text("ANTHROPIC_API_KEY=fixture-secret\nprint 'startup chatter'\n")
    root = Path(__file__).resolve().parents[1]
    environment = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    environment.update(ZDOTDIR=str(shell), PYTHONDONTWRITEBYTECODE="1")
    parameters = mcp.StdioServerParameters(command="/bin/zsh", args=[str(root / "scripts/run_mcp.zsh"),
        "--case-root", str(tmp_path), "--provider", "anthropic", "--base-url", anthropic_server.url],
        env=environment)

    async def run():
        async with stdio_client(parameters) as (read, write):
            async with mcp.ClientSession(read, write) as session:
                await session.initialize()
                view = await session.call_tool("workspace", {"case": "case", "view": "next"})
                assert view.structuredContent["workspace"]["revision"] == 0
                result = await session.call_tool("submit", {"case": "case", "text": "Synthetic native transport check.",
                    "speaker": "Fixture participant", "base_revision": 0, "response_target": None})
                assert result.structuredContent["status"] == "saved"
                assert result.structuredContent["workspace"]["revision"] == 1
    asyncio.run(run())
    assert anthropic_server.requests[-1][2]["X-Api-Key"] == "fixture-secret"
