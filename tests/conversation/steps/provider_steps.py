"""Provider choice and failure behavior, driven through composition and use cases."""

import json
import os
from unittest import mock
import zipfile

from behave import given, when, then

from reason_commons.adapters.lm_studio import LMStudioConsultant
from reason_commons.adapters.rendering import workspace_output, render_provider_settings
from reason_commons.bootstrap import configured_consultant, create_case, open_case, provider_settings
from tests.servers import anthropic_server_instance, lm_studio_server_instance
from tests.support import ScriptedConsultant, bounded_case, cli, submit

SECRET = "sk-fixture-secret-9f3a"
LITERAL = "We keep missing deliveries.\nSecond line, exactly as typed."


class ProviderFailure(Exception):
    """Carries a safe category and a message that must never reach case state."""

    def __init__(self, category, status=None):
        super().__init__(f"provider said: key {SECRET} was refused")
        self.category, self.http_status = category, status


class FailingConsultant:
    def __init__(self, category):
        self.version = "failing/1"
        self.failure = ProviderFailure(category, 401 if category == "http_error" else None)

    def propose(self, request):
        raise self.failure


def start(context, generator):
    server = next(generator)
    context.cleanups.append(lambda: next(generator, None))
    return server


def reopen_with(context, consultant):
    context.app.close()
    import shutil
    shutil.rmtree(context.path)
    context.app = create_case(context.path, "Payments", consultant=consultant)


def saved_text(context):
    parts = [path.read_bytes() for path in context.path.rglob("*") if path.is_file()]
    return b"\n".join(parts)


# ---- Choosing a provider -------------------------------------------------

@given("no consultant has been chosen")
def nothing_chosen(context):
    assert "REASON_COMMONS_PROVIDER" not in os.environ


@given("the environment chooses Anthropic with an API key")
def anthropic_with_key(context):
    os.environ.update(REASON_COMMONS_PROVIDER="anthropic", ANTHROPIC_API_KEY=SECRET)


@given("the environment chooses Anthropic without an API key")
def anthropic_without_key(context):
    os.environ["REASON_COMMONS_PROVIDER"] = "anthropic"


@when("I check the consultant settings")
def check_settings(context):
    with mock.patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("network used")) as opener:
        context.settings = provider_settings()
        context.rendered_settings = render_provider_settings(context.settings)
    context.requests_sent = opener.call_count


@when('I explicitly choose "{name}"')
def choose(context, name):
    try:
        context.settings = provider_settings(provider=name)
        context.composed = configured_consultant(provider=name)
        context.error = None
    except ValueError as error:
        context.error = error


@then("LM Studio is selected by default")
def lm_default(context):
    assert (context.settings["provider"], context.settings["selected_by"]) == ("lm-studio", "default")


@then("LM Studio is selected by an explicit choice")
def lm_explicit(context):
    assert (context.settings["provider"], context.settings["selected_by"]) == ("lm-studio", "explicit")


@then("the composed consultant is the LM Studio consultant")
def composed_lm(context):
    assert isinstance(context.composed, LMStudioConsultant)


@then("no request has been sent to any provider")
def no_requests(context):
    assert context.requests_sent == 0


@then("Anthropic is selected by the environment and is ready")
def anthropic_ready(context):
    assert (context.settings["provider"], context.settings["selected_by"]) == ("anthropic", "environment")
    assert context.settings["ready"] is True and context.settings["problems"] == []


@then("the settings name ANTHROPIC_API_KEY but never show its value")
def names_not_value(context):
    credential = context.settings["credential"]
    assert credential == {"variable": "ANTHROPIC_API_KEY", "required": True, "present": True}
    assert "ANTHROPIC_API_KEY" in context.rendered_settings
    assert SECRET not in json.dumps(context.settings) and SECRET not in context.rendered_settings


@then("Anthropic is not ready because ANTHROPIC_API_KEY is not set")
def anthropic_not_ready(context):
    assert context.settings["provider"] == "anthropic" and context.settings["ready"] is False
    assert any("ANTHROPIC_API_KEY" in problem for problem in context.settings["problems"])
    assert "ANTHROPIC_API_KEY" in context.rendered_settings and "not ready" in context.rendered_settings.lower()


@then("the choice is rejected and names lm-studio and anthropic as the valid providers")
def rejected(context):
    assert isinstance(context.error, ValueError)
    assert "lm-studio" in str(context.error) and "anthropic" in str(context.error)


# ---- Opening a case with a consultant ------------------------------------

@given("a case opened with the configured consultant")
def configured_case(context):
    reopen_with(context, configured_consultant())


@given("a consultant that fails with a {category} problem containing a secret")
def failing(context, category):
    context.failing = FailingConsultant(category)


@given("a case opened with that consultant")
def failing_case(context):
    reopen_with(context, context.failing)


@when("David contributes to the empty case")
def contribute_empty(context):
    context.result = context.app.submit(LITERAL, "David", 0, None)


# ---- Failure explanation and retention -----------------------------------

@then("the application reports the consultant unavailable because of {category}")
def unavailable(context, category):
    assert context.result["status"] == "unavailable", context.result
    assert context.result["failure_category"] == category
    if category == "http_error":
        assert context.result["http_status"] == 401


@then("David's literal words are retained for explicit retry")
def retained(context):
    request_id = context.result["request_id"]
    assert context.app.sources()["sources"][request_id]["text"] == LITERAL
    assert "retry_retained_input" in context.result["recovery_actions"]
    assert [r["input"]["request_id"] for r in context.app.workspace()["pending_requests"]] == [request_id]


@then("no revision was published")
def no_revision(context):
    assert context.app.inspect()["case"]["revision"] == 0


@then("the case can still be read offline")
def offline(context):
    with open_case(context.path, writable=False) as reader:
        assert reader.workspace()["revision"] == 0 and reader.receipts(context.result["request_id"])["attempts"]


@then("the participant is told to {check}")
def told(context, check):
    rendered = workspace_output(context.app.workspace(), result=context.result, speaker="David")["rendered"]
    for form in ("text", "markdown"):
        assert check in rendered[form].lower(), rendered[form]


@then("the secret appears nowhere in the saved case")
def no_secret(context):
    rendered = workspace_output(context.app.workspace(), result=context.result, speaker="David")["rendered"]
    assert SECRET.encode() not in saved_text(context)
    assert SECRET not in json.dumps(context.result) and SECRET not in json.dumps(rendered)


# ---- Switching consultants -----------------------------------------------

@given('a case consulted by "{name}"')
def consulted_by(context, name):
    context.consultant.version = f"fixture/{name}"
    context.consultant.responses.append(bounded_case)
    assert submit(context.app, "Pilot and original forecast")["status"] == "saved"
    context.displayed = context.app.workspace()
    context.history_before = context.app.history()["revisions"]


@when('the case is reopened with the consultant "{name}"')
def reopen_second(context, name):
    context.app.close()
    context.second = ScriptedConsultant()
    context.second.version = f"fixture/{name}"
    context.app = open_case(context.path, consultant=context.second)


@when("David replies to the displayed question")
def reply_displayed(context):
    context.result = context.app.submit("My reply to the displayed question", "David", **context.displayed["target"])
    assert context.result["status"] == "saved", context.result


@then("the earlier records and forecast are unchanged")
def earlier_unchanged(context):
    now = context.app.history()["revisions"]
    assert now[:len(context.history_before)] == context.history_before and len(now) > len(context.history_before)


@then("each applied request records the consultant that produced it")
def versions(context):
    assert context.app.inspect()["case"]["adapter_versions"] == {
        "in000001": "fixture/first-model", "in000002": "fixture/second-model"}


# ---- End to end through a real adapter and a loopback server --------------

@given("an Anthropic server and an environment choosing it with an API key")
def anthropic_server(context):
    context.server = start(context, anthropic_server_instance())
    os.environ.update(REASON_COMMONS_PROVIDER="anthropic", ANTHROPIC_API_KEY=SECRET,
                      REASON_COMMONS_ANTHROPIC_URL=context.server.url)


@given("a local LM Studio server and an environment choosing it")
def lm_studio_server(context):
    context.server = start(context, lm_studio_server_instance())
    context.server.models = ["local-chat-model"]
    os.environ.update(REASON_COMMONS_PROVIDER="lm-studio", REASON_COMMONS_LM_STUDIO_URL=context.server.url)


@then("a question is saved")
def question_saved(context):
    assert context.result["status"] == "saved", context.result
    assert context.app.workspace()["question"] is not None


@then("the API key is not stored in the case or its export")
def key_not_stored(context):
    sent = [headers for _, _, headers, _ in context.server.requests]
    assert sent and all(h.get("X-Api-Key") == SECRET for h in sent)
    bundle = context.path.parent / "handoff.reasoncase"
    context.app.export(str(bundle))
    with zipfile.ZipFile(bundle) as archive:
        exported = b"\n".join(archive.read(name) for name in archive.namelist())
    assert SECRET.encode() not in saved_text(context) and SECRET.encode() not in exported


@then("the case records that LM Studio produced it")
def lm_recorded(context):
    assert context.app.inspect()["case"]["adapter_versions"]["in000001"].startswith("lm-studio/")


# ---- Experimental agent runner -------------------------------------------

@given("an empty case store")
def empty_store(context):
    context.app.close()
    with open_case(context.path, writable=False) as reader:
        assert reader.workspace()["revision"] == 0


@when("I contribute using the experimental agent runner")
def agent_runner(context):
    context.command = cli("contribute", context.path, "--speaker", "David", "--text", LITERAL, "--runner", "agent")


@then("the command is rejected because that runner requires lm-studio")
def runner_rejected(context):
    assert context.command.returncode == 1 and "requires lm-studio" in context.command.stderr


@then("nothing was retained in the case")
def nothing_retained(context):
    with open_case(context.path, writable=False) as reader:
        assert reader.workspace()["pending_requests"] == [] and reader.workspace()["revision"] == 0
