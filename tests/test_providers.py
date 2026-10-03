"""Provider-neutral composition, readiness reporting and failure diagnostics.

Behavior a participant sees is specified in tests/conversation/features/providers.feature.
These adapter-level tests cover the real adapters' categories, CLI exit codes and
input normalisation that the scenarios deliberately do not enumerate.
"""

import json

import pytest

from reason_commons.adapters.anthropic import AnthropicConsultant
from reason_commons.adapters.lm_studio import LMStudioConsultant
from reason_commons.application.service import failure_detail
from reason_commons.bootstrap import create_case, import_case, open_case, provider_settings
from tests.servers import anthropic_server_instance
from tests.support import cli, submit

KEYS = ("REASON_COMMONS_PROVIDER", "ANTHROPIC_API_KEY", "REASON_COMMONS_ANTHROPIC_MODEL",
        "REASON_COMMONS_ANTHROPIC_URL", "REASON_COMMONS_LM_STUDIO_MODEL", "REASON_COMMONS_LM_STUDIO_URL",
        "LM_STUDIO_API_TOKEN")


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for key in KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def anthropic_server():
    yield from anthropic_server_instance()


@pytest.mark.parametrize("value", ["anthropic", " Anthropic ", "ANTHROPIC"])
def test_provider_names_are_trimmed_and_case_insensitive(value):
    assert provider_settings(provider=value)["provider"] == "anthropic"


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_choices_count_as_not_chosen(value, monkeypatch):
    monkeypatch.setenv("REASON_COMMONS_PROVIDER", value)
    assert provider_settings()["selected_by"] == "default"
    assert provider_settings(provider=value)["selected_by"] == "default"


def test_settings_resolve_each_value_from_flag_environment_or_default(monkeypatch):
    base = provider_settings(provider="anthropic")
    assert (base["model_source"], base["endpoint"]) == ("default", "https://api.anthropic.com/v1")
    monkeypatch.setenv("REASON_COMMONS_ANTHROPIC_MODEL", "claude-from-environment")
    assert provider_settings(provider="anthropic")["model_source"] == "environment"
    chosen = provider_settings(provider="anthropic", model="claude-explicit", base_url="http://127.0.0.1:9/v1")
    assert (chosen["model"], chosen["model_source"], chosen["endpoint"]) == (
        "claude-explicit", "explicit", "http://127.0.0.1:9/v1")


def test_blank_anthropic_key_is_not_a_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")
    assert provider_settings(provider="anthropic")["ready"] is False


def test_lm_studio_token_is_optional_and_never_blocks_readiness(monkeypatch):
    local = provider_settings(provider="lm-studio")
    assert local["ready"] is True and local["credential"]["required"] is False
    monkeypatch.setenv("LM_STUDIO_API_TOKEN", "local-secret")
    assert provider_settings(provider="lm-studio")["credential"]["present"] is True
    assert "local-secret" not in json.dumps(provider_settings(provider="lm-studio"))


def test_failure_detail_admits_only_known_categories_and_real_statuses():
    class Failure(Exception):
        category, http_status = "invented", 99999
    assert failure_detail(Failure("secret")) == {"failure_category": "unknown"}
    Failure.category, Failure.http_status = "timeout", 504
    assert failure_detail(Failure()) == {"failure_category": "timeout", "http_status": 504}
    Failure.http_status = True  # bool is not a status
    assert failure_detail(Failure()) == {"failure_category": "timeout"}
    assert failure_detail(RuntimeError("anything")) == {"failure_category": "unknown"}


def test_real_anthropic_adapter_reports_configuration_without_http(tmp_path, anthropic_server):
    consultant = AnthropicConsultant(base_url=anthropic_server.url)  # no key
    with create_case(tmp_path / "case", consultant=consultant) as app:
        result = submit(app)
    assert (result["status"], result["failure_category"]) == ("unavailable", "configuration")
    assert anthropic_server.requests == []


def test_real_anthropic_adapter_reports_a_rejected_key_with_status(tmp_path, anthropic_server):
    anthropic_server.get_status = 401
    consultant = AnthropicConsultant(base_url=anthropic_server.url, api_key="fixture-secret")
    with create_case(tmp_path / "case", consultant=consultant) as app:
        result = submit(app)
        stored = app.receipts(result["request_id"])["attempts"]
    assert (result["failure_category"], result["http_status"]) == ("http_error", 401)
    assert any(a.get("failure_category") == "http_error" for a in stored)
    assert "fixture-secret" not in json.dumps(result) + json.dumps(stored)


def test_real_lm_studio_adapter_reports_an_unreachable_server(tmp_path):
    consultant = LMStudioConsultant(base_url="http://127.0.0.1:9/v1", model="m", timeout=2)
    with create_case(tmp_path / "case", consultant=consultant) as app:
        result = submit(app)
    assert (result["status"], result["failure_category"]) == ("unavailable", "connection")


def test_a_failure_receipt_survives_export_and_import(tmp_path):
    consultant = AnthropicConsultant(api_key=None)
    with create_case(tmp_path / "case", consultant=consultant) as app:
        result = submit(app)
        app.export(str(tmp_path / "handoff.reasoncase"))
    with import_case(str(tmp_path / "handoff.reasoncase"), str(tmp_path / "imported")) as app:
        attempts = app.receipts(result["request_id"])["attempts"]
    assert any(a.get("failure_category") == "configuration" for a in attempts)


def test_providers_command_exit_status_and_secret_hygiene(monkeypatch):
    ready = cli("providers", "--provider", "lm-studio")
    assert ready.returncode == 0 and "ready" in ready.stdout
    missing = cli("providers", "--provider", "anthropic")
    assert missing.returncode == 1 and "ANTHROPIC_API_KEY" in missing.stdout and "not ready" in missing.stdout
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-never-printed")
    keyed = cli("providers", "--provider", "anthropic", "--json")
    assert keyed.returncode == 0 and "sk-never-printed" not in keyed.stdout + keyed.stderr
    assert json.loads(keyed.stdout)["credential"] == {"variable": "ANTHROPIC_API_KEY", "required": True, "present": True}


def test_providers_command_reads_the_environment_choice_and_rejects_unknown(monkeypatch):
    monkeypatch.setenv("REASON_COMMONS_PROVIDER", "anthropic")
    assert "chosen by REASON_COMMONS_PROVIDER" in cli("providers").stdout
    monkeypatch.setenv("REASON_COMMONS_PROVIDER", "openai")
    rejected = cli("providers")
    assert rejected.returncode == 1 and "lm-studio" in rejected.stderr and "anthropic" in rejected.stderr


def test_contribution_with_a_missing_key_keeps_the_input_and_explains(tmp_path, monkeypatch):
    store = tmp_path / "case"
    cli("new", "--store", store)
    monkeypatch.setenv("REASON_COMMONS_PROVIDER", "anthropic")
    result = cli("contribute", store, "--speaker", "Sam", "--text", "literal words")
    assert result.returncode == 1 and "providers" in result.stdout
    with open_case(store, writable=False) as app:
        assert len(app.workspace()["pending_requests"]) == 1 and app.inspect()["case"]["revision"] == 0
