from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread

import jsonschema
import pytest

from reason_commons.adapters.lm_studio import LMStudioConsultant, LMStudioError
from reason_commons.bootstrap import create_case, open_case
from reason_commons.domain.contract import proposal_schema
from tests.servers import lm_studio_server_instance
from tests.support import bounded_case, proposal, submit


@pytest.fixture
def server():
    yield from lm_studio_server_instance()


def input_request():
    return {"input": {"request_id": "in001", "base_revision": 0, "text": "A participant report"},
            "case": {}, "sources": {}}


def test_adapter_sends_full_case_with_structured_schema_and_records_provenance(server, tmp_path):
    server.models = ["local-chat-model"]
    adapter = LMStudioConsultant(base_url=server.url)
    with create_case(tmp_path / "case", "LM fixture", consultant=adapter) as app:
        assert submit(app)["status"] == "saved"
        assert adapter.model == "local-chat-model"
        assert [(method, path) for method, path, _, _ in server.requests] == [
            ("GET", "/v1/models"), ("POST", "/v1/chat/completions")]
        _, _, headers, payload = server.requests[-1]
        assert "Authorization" not in headers
        assert payload["stream"] is False and payload["model"] == "local-chat-model"
        assert payload["response_format"]["json_schema"]["strict"] is True
        request = json.loads(payload["messages"][1]["content"])
        assert request["input"]["text"] == "A participant report"
        assert request["input"]["request_id"] in request["sources"]
        assert request["case"]["revision"] == 0
        assert app.inspect()["case"]["adapter_versions"]["in000001"] == adapter.version
        assert "Reasoning Commons" in payload["messages"][0]["content"]


def test_provider_schema_separates_sources_context_and_plain_protections(server, tmp_path):
    with create_case(tmp_path / "case", consultant=LMStudioConsultant("model", server.url)) as app:
        assert submit(app)["status"] == "saved"
    schema = server.requests[-1][3]["response_format"]["json_schema"]["schema"]
    updates = schema["properties"]["proposed_updates"]
    assert updates["minItems"] == 1
    goal = updates["items"]["anyOf"][0]["properties"]
    jsonschema.validate(["Protect urgent work"], goal["data"]["properties"]["protections"])
    jsonschema.validate(["in000001"], goal["source_refs"])
    context = schema["properties"]["intervention"]["properties"]["required_context_refs"]
    jsonschema.validate(["goal", "temp_pilot"], context)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(["in000001"], context)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(["in999999"], goal["source_refs"])


def test_adapter_freezes_procedure_and_context_for_session_provenance(server, tmp_path, monkeypatch):
    adapter = LMStudioConsultant("model", server.url)
    version = adapter.version
    # Resources cannot be reread halfway through a live evaluation and still
    # claim the original policy version.
    monkeypatch.setattr("reason_commons.adapters.lm_studio.files", lambda *a: (_ for _ in ()).throw(AssertionError()))
    with create_case(tmp_path / "case", consultant=adapter) as app:
        assert submit(app)["status"] == "saved"
    assert adapter.version == version


def test_explicit_model_is_verified_and_token_is_not_persisted(server, tmp_path):
    adapter = LMStudioConsultant("selected-model", server.url, api_key="fixture-secret")
    with create_case(tmp_path / "case", consultant=adapter) as app:
        assert submit(app)["status"] == "saved"
        assert server.requests[0][0:2] == ("GET", "/v1/models")
        assert server.requests[0][2]["Authorization"] == "Bearer fixture-secret"
        assert server.requests[1][3]["model"] == "selected-model"
        assert "fixture-secret" not in str(app.history()) + str(app.receipts("in000001"))
    assert not any(b"fixture-secret" in path.read_bytes() for path in (tmp_path / "case").rglob("*.yaml"))


@pytest.mark.parametrize("models", [[], ["first", "second"]])
def test_ambiguous_or_missing_model_never_starts_generation(server, models):
    server.models = models
    with pytest.raises(LMStudioError, match="Choose a model"):
        LMStudioConsultant(base_url=server.url).propose(input_request())
    assert [request[0] for request in server.requests] == ["GET"]


def test_unadvertised_model_cannot_silently_fall_back_and_can_be_explicitly_retried(server, tmp_path):
    adapter = LMStudioConsultant("not-served", server.url)
    with create_case(tmp_path / "case", consultant=adapter) as app:
        result = submit(app, "Retain this exact contribution")
        assert result["status"] == "unavailable"
        assert [r[0] for r in server.requests] == ["GET"]
        assert app.inspect()["case"]["revision"] == 0
        assert app.inspect()["case"]["adapter_versions"] == {}
        server.models.append("not-served")
        assert app.retry(result["request_id"])["status"] == "saved"
        assert [r[0] for r in server.requests] == ["GET", "GET", "POST"]


def test_actual_response_model_must_match_requested_model_before_publication(server, tmp_path):
    server.response_model = "model-b"
    adapter = LMStudioConsultant("model-a", server.url)
    with create_case(tmp_path / "case", consultant=adapter) as app:
        result = submit(app)
        assert result["status"] == "rejected"
        assert app.inspect()["case"]["revision"] == 0
        assert app.inspect()["case"]["adapter_versions"] == {}
        server.response_model = None
        assert app.retry(result["request_id"])["status"] == "saved"
        assert app.inspect()["case"]["adapter_versions"][result["request_id"]] == adapter.version


def test_verified_model_cache_cannot_authorize_a_different_payload_model(server):
    adapter = LMStudioConsultant("model-a", server.url)
    with pytest.raises(LMStudioError, match="configured verified model"):
        adapter.chat_completion({"model": "model-b", "messages": []})
    assert [r[0] for r in server.requests] == ["GET"]


def test_missing_response_model_is_rejected_even_when_content_is_valid(server, tmp_path):
    server.custom = ({"model": None, "choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]},)
    with create_case(tmp_path / "case", consultant=LMStudioConsultant("model", server.url)) as app:
        assert submit(app)["status"] == "rejected"
        assert app.inspect()["case"]["revision"] == 0


@pytest.mark.parametrize("response", [
    b"not-json",
    {"choices": []},
    {"choices": ["wrong-type"]},
    {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": "[]"}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": '{"key":1,"key":2}'}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": '{"value":NaN}'}}]},
    {"choices": [{"finish_reason": "stop", "message": {"refusal": "No", "content": "{}"}}]},
])
def test_invalid_or_truncated_provider_output_rejects_without_commit(server, tmp_path, response):
    server.custom = (response,)
    with create_case(tmp_path / "case", consultant=LMStudioConsultant("model", server.url)) as app:
        result = submit(app, "Preserve my input")
        assert result["status"] == "rejected"
        assert app.inspect()["case"]["revision"] == 0
        assert app.sources()["sources"][result["request_id"]]["text"] == "Preserve my input"
        assert len(server.requests) == 2
        assert any(a.get("status") == "rejected" for a in app.receipts(result["request_id"])["attempts"])


def test_http_failure_retains_input_and_explicit_retry_uses_same_identity(server, tmp_path):
    server.custom = ({"error": "do not store this provider secret"}, 503)
    with create_case(tmp_path / "case", consultant=LMStudioConsultant("model", server.url)) as app:
        failed = submit(app)
        assert failed["status"] == "unavailable" and len(server.requests) == 2
        assert "provider secret" not in str(app.receipts(failed["request_id"]))
        server.custom = None
        assert app.retry(failed["request_id"])["status"] == "saved"
        calls = len(server.requests)
        assert app.retry(failed["request_id"])["already_applied"]
        assert len(server.requests) == calls
        first, second = [json.loads(call[3]["messages"][1]["content"])["input"] for call in server.requests if call[0] == "POST"]
        assert first == second


def test_redirect_never_forwards_case_or_token(server):
    server.custom = (b"", 307, {"Location": server.url + "/unexpected"})
    with pytest.raises(LMStudioError, match="307"):
        LMStudioConsultant("model", server.url, api_key="fixture-secret").propose(input_request())
    assert len(server.requests) == 2


def test_model_swap_on_existing_case_does_not_require_provider_memory(server, tmp_path):
    first = LMStudioConsultant("model-a", server.url)
    with create_case(tmp_path / "case", consultant=first) as app:
        assert submit(app)["status"] == "saved"
        old_records = app.inspect()["case"]["records"]
    server.author = proposal
    second = LMStudioConsultant("model-b", server.url)
    with open_case(tmp_path / "case", consultant=second) as app:
        assert submit(app, "A follow-up with a different model")["status"] == "saved"
        case = app.inspect()["case"]
        assert case["records"][:len(old_records)] == old_records
        assert case["adapter_versions"] == {"in000001": first.version, "in000002": second.version}
        request = json.loads(server.requests[-1][3]["messages"][1]["content"])
        assert request["case"]["records"] == old_records
        assert len(request["sources"]) == 2


def test_environment_configuration_keeps_secrets_out_of_version(monkeypatch):
    monkeypatch.setenv("REASON_COMMONS_LM_STUDIO_MODEL", "my-model")
    monkeypatch.setenv("REASON_COMMONS_LM_STUDIO_URL", "http://localhost:8080")
    monkeypatch.setenv("LM_STUDIO_API_TOKEN", "secret")
    monkeypatch.setenv("REASON_COMMONS_LM_STUDIO_TIMEOUT", "30")
    adapter = LMStudioConsultant.from_env()
    assert adapter.model == "my-model" and adapter.timeout == 30
    assert adapter.base_url == "http://localhost:8080/v1"
    assert "secret" not in adapter.version
    override = LMStudioConsultant.from_env(model="chosen-model", base_url="http://localhost:9000/v1")
    assert override.model == "chosen-model" and override.base_url == "http://localhost:9000/v1"


@pytest.mark.parametrize("url", ["ftp://localhost:1234", "http://secret@localhost:1234", "http://localhost:1234/v2",
                                 "http://localhost:1234?token=secret", "http://localhost:1234/#fragment"])
def test_invalid_or_credential_bearing_urls_fail_before_request(url):
    with pytest.raises(ValueError):
        LMStudioConsultant(base_url=url)


def test_schema_matches_all_authored_record_kinds_and_rejects_unavailable_types():
    schema = proposal_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    request = input_request()
    jsonschema.validate(bounded_case(request), schema)
    from examples.p0_slice import AuthoredConsultant
    for turn in range(4):
        request["case"]["applied_requests"] = ["previous"] * turn
        jsonschema.validate(AuthoredConsultant().propose(request), schema)
    invalid = bounded_case(request)
    invalid["proposed_updates"].append({"operation": "record_stance", "data": {}, "source_refs": ["in001"]})
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid, schema)
