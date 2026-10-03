"""Host permissions and agent traces; deterministic tests do not prove live skill quality."""

import json

import pytest

from reason_commons.adapters.skill_agent import ContributionToolHost, LMStudioSkillAgent
from reason_commons.bootstrap import create_case
from evaluations.fixtures import NoteConsultant
from tests.support import fixture_app


class ToolModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.payloads = []
        self.model = "fixture-agent"

    def chat_completion(self, payload):
        self.payloads.append(payload)
        return self.responses.pop(0)


def call(name, arguments, identity="call-1"):
    return {"choices": [{"finish_reason": "tool_calls", "message": {"role": "assistant", "content": None,
            "tool_calls": [{"id": identity, "type": "function", "function": {
                "name": name, "arguments": json.dumps(arguments)}}]}}]}


def done(text="Saved in000001"):
    return {"choices": [{"finish_reason": "stop", "message": {"content": text}}]}


def test_agent_executes_literal_contribution_through_capabilities(tmp_path):
    provider = NoteConsultant()
    model = ToolModel([call("inspect", {}), call("retain_input", {
        "text": "5\n:options", "speaker": "Sam", "base_revision": 0, "response_target": None}, "call-2"),
        call("consult", {"request_id": "in000001"}, "call-3"), done()])
    with create_case(tmp_path / "case", consultant=provider) as app:
        host = ContributionToolHost(app, text="5\n:options", speaker="Sam")
        outcome = LMStudioSkillAgent(model, "Skill procedure", "Domain context").run(host, {"operation": "contribute"})
        assert outcome["status"] == "completed"
        assert [t["name"] for t in outcome["trace"]] == ["inspect", "retain_input", "consult"]
        assert all(t["allowed"] for t in outcome["trace"])
        assert provider.calls == 1 and app.inspect()["case"]["revision"] == 1
        assert app.sources()["sources"]["in000001"]["text"] == "5\n:options"
        assert "Skill procedure" in model.payloads[0]["messages"][0]["content"]
        assert any(m["role"] == "tool" for m in model.payloads[-1]["messages"])


def test_agent_tool_grammar_fixes_the_authorized_literal_input_without_mutating_shared_tools(tmp_path):
    from reason_commons.adapters.skill_agent import TOOLS
    text = "Please retain this as my note: 5\n:options\n"
    model = ToolModel([call("inspect", {}), call("retain_input", {
        "text": text, "speaker": "Sam", "declarations": {}, "base_revision": 0, "response_target": None}, "b"),
        call("consult", {"request_id": "in000001"}, "c"), done()])
    with create_case(tmp_path / "case", consultant=NoteConsultant()) as app:
        host = ContributionToolHost(app, text=text, speaker="Sam")
        LMStudioSkillAgent(model, "procedure", "context").run(host, {
            "operation": "contribute", "text": text, "speaker": "Sam", "declarations": {}})
        assert app.sources()["sources"]["in000001"]["text"] == text
        grammar = next(t["function"]["parameters"]["properties"] for t in model.payloads[0]["tools"]
                       if t["function"]["name"] == "retain_input")
        assert grammar["text"]["const"] == text and grammar["speaker"]["const"] == "Sam"
        shared = next(t["function"]["parameters"]["properties"] for t in TOOLS
                      if t["function"]["name"] == "retain_input")
        assert "const" not in shared["text"]


@pytest.mark.parametrize("name,arguments", [
    ("_store", {}), ("export", {"destination": "/tmp/unapproved"}),
    ("consult", {"request_id": "in000001"}), ("retry", {"request_id": "in000001"}),
    ("retain_input", {"text": "changed", "speaker": "Sam", "base_revision": 0, "response_target": None}),
    ("retain_input", {"text": "literal", "speaker": "Priya", "base_revision": 0, "response_target": None}),
    ("retain_input", {"text": "literal", "speaker": "Sam", "base_revision": True, "response_target": None}),
    ("retain_input", {"text": "literal", "speaker": "Sam", "base_revision": 0, "response_target": None,
                       "declarations": {"ownership": ["Sam"]}}),
    ("inspect", {"path": "case.yaml"}),
])
def test_blocked_agent_requests_remain_visible_and_make_no_semantic_change(tmp_path, name, arguments):
    provider = NoteConsultant()
    with create_case(tmp_path / "case", consultant=provider) as app:
        host = ContributionToolHost(app, text="literal", speaker="Sam")
        result = host.invoke(name, arguments)
        assert result["status"] == "tool_error"
        assert host.trace[0]["allowed"] is False
        assert provider.calls == 0 and app.inspect()["case"]["revision"] == 0


def test_failure_cannot_authorize_silent_retry_or_new_retention(tmp_path):
    provider = NoteConsultant(fail=True)
    with create_case(tmp_path / "case", consultant=provider) as app:
        host = ContributionToolHost(app, text="literal", speaker="Sam")
        assert host.invoke("retain_input", {"text": "literal", "speaker": "Sam", "base_revision": 0,
                                           "response_target": None})["status"] == "input_retained"
        assert host.invoke("consult", {"request_id": "in000001"})["status"] == "unavailable"
        assert host.invoke("consult", {"request_id": "in000001"})["status"] == "tool_error"
        assert host.invoke("retry", {"request_id": "in000001"})["status"] == "tool_error"
        assert host.invoke("retain_input", {"text": "literal", "speaker": "Sam", "base_revision": 0,
                                           "response_target": None})["status"] == "tool_error"
        assert provider.calls == 1


def test_failed_retention_does_not_expose_consult_authority(tmp_path):
    provider = NoteConsultant()
    app, fault = fixture_app(tmp_path / "case", provider)
    with app:
        fault.fail("retain")
        host = ContributionToolHost(app, text="literal", speaker="Sam")
        assert host.invoke("retain_input", {"text": "literal", "speaker": "Sam", "base_revision": 0,
                                           "response_target": None})["status"] == "not_saved"
        assert host.invoke("consult", {"request_id": "in000001"})["status"] == "tool_error"
        assert provider.calls == 0


def test_explicit_retry_uses_exact_existing_input(tmp_path):
    provider = NoteConsultant(fail=True)
    with create_case(tmp_path / "case", consultant=provider) as app:
        original = app.submit("original", "Priya", 0, None)
        provider.fail = False
        host = ContributionToolHost(app, retry_request=original["request_id"])
        assert host.invoke("retry", {"request_id": "in999999"})["status"] == "tool_error"
        assert host.invoke("retry", {"request_id": original["request_id"]})["status"] == "saved"
        assert app.sources()["sources"][original["request_id"]]["text"] == "original"
        assert len(app.sources()["sources"]) == 1 and provider.calls == 2


@pytest.mark.parametrize("response", [
    {"choices": []}, {"choices": [{"finish_reason": "length", "message": {"content": "incomplete"}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": None}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": ""}}]},
    {"choices": [{"finish_reason": "tool_calls", "message": {"tool_calls": "not a list"}}]},
])
def test_incomplete_or_malformed_agent_response_is_not_success(tmp_path, response):
    with create_case(tmp_path / "case") as app:
        host = ContributionToolHost(app, text="literal", speaker="Sam")
        outcome = LMStudioSkillAgent(ToolModel([response]), "procedure", "context").run(host, {})
        assert outcome["status"] == "invalid_agent_response" and host.trace == []


def test_agent_cannot_announce_success_into_existence(tmp_path):
    with create_case(tmp_path / "case") as app:
        host = ContributionToolHost(app, text="literal", speaker="Sam")
        outcome = LMStudioSkillAgent(ToolModel([done("I saved everything")]), "procedure", "context").run(host, {})
        assert outcome["status"] == "completed"  # Model loop finished; application outcome is independent.
        assert outcome["trace"] == [] and app.inspect()["case"]["revision"] == 0


def test_tool_loop_is_bounded(tmp_path):
    with create_case(tmp_path / "case") as app:
        host = ContributionToolHost(app, text="literal", speaker="Sam")
        model = ToolModel([call("inspect", {}, "a"), call("inspect", {}, "b")])
        assert LMStudioSkillAgent(model, "procedure", "context", max_rounds=2).run(host, {})["status"] == "round_limit"


def test_agent_can_project_open_and_resume_without_submission_or_consultation(tmp_path):
    provider = NoteConsultant()
    with create_case(tmp_path / "case", consultant=provider) as app:
        model = ToolModel([call("workspace", {"view": "next"}), done("Start this case")])
        host = ContributionToolHost(app)
        result = LMStudioSkillAgent(model, "procedure", "context").run(host, {"operation": "open"})
        assert result["status"] == "completed" and provider.calls == 0
        assert host.trace[0]["result"]["workspace"]["question"] is None
        assert app.inspect()["case"]["revision"] == 0
        assert host.invoke("retain_input", {"text": "invented", "speaker": "David", "base_revision": 0,
                                           "response_target": None})["status"] == "tool_error"


def test_bound_reply_target_cannot_be_changed_by_agent(tmp_path):
    provider = NoteConsultant()
    with create_case(tmp_path / "case", consultant=provider) as app:
        displayed = app.workspace()["target"]
        app.submit("Someone else advances the case", "Sam", **displayed)
        host = ContributionToolHost(app, text="My original reply", speaker="David", target=displayed)
        current = app.workspace()["target"]
        rejected = host.invoke("retain_input", {"text": "My original reply", "speaker": "David", **current})
        assert rejected["status"] == "tool_error" and not host.trace[-1]["allowed"]
        assert provider.calls == 1
