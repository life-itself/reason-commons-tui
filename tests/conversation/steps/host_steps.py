"""The coding agent hosting the skill as the consultant, driven through the MCP bridge and use cases."""

import asyncio
import os
from pathlib import Path
import shutil
from unittest import mock

from behave import given, when, then

from reason_commons.adapters.anthropic import AnthropicConsultant
from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.adapters.lm_studio import LMStudioConsultant
from reason_commons.adapters.mcp_server import CaseToolBridge
from reason_commons.adapters.provider_support import consulting_prompt, request_schema
from reason_commons.adapters.rendering import render_provider_settings
from reason_commons.bootstrap import open_case, provider_settings
from tests.support import ScriptedConsultant

LITERAL = "We keep missing deliveries.\nSecond line, exactly as typed."
CASE = "case"


def call(context, name, **arguments):
    return context.bridge.invoke(name, {"case": CASE, **arguments})


def reply(request_id, base_revision, cite=None):
    """A reply as a hosting agent would write it: one question and two notes in David's words."""
    notes = [{"operation": "record_note", "temporary_id": f"temp_note_{n}",
              "data": {"text": text, "basis": "participant_report"}, "source_refs": [request_id]}
             for n, text in enumerate(("We keep missing deliveries.", "Second line, exactly as typed."), 1)]
    intervention = {"kind": "question", "purpose": "clarify_next_decision",
                    "primary_prompt": "What should we observe next?", "rationale": "Keep the next move bounded.",
                    "required_context_refs": [cite] if cite else []}
    return {"schema_version": "1", "delivery_profile": "p2", "request_id": request_id,
            "base_revision": base_revision, "intervention": intervention, "proposed_updates": notes}


def retain(context, text=LITERAL):
    case = call(context, "inspect")["case"]
    result = call(context, "retain_input", text=text, speaker="David", base_revision=case["revision"],
                  response_target=case["current_intervention"])
    assert result["status"] == "input_retained", result
    return result["request_id"]


def propose(context, request_id, agent="example-agent", model="example-model", cite=None):
    base = call(context, "inspect")["case"]["revision"]
    return call(context, "propose", request_id=request_id, proposal=reply(request_id, base, cite),
                agent=agent, model=model)


def stored_files(context):
    root = context.root / CASE
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and p.name != "writer.lock"}


# ---- Settings -------------------------------------------------------------

@given("no consultant credential is set")
def no_credentials(context):
    assert not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("LM_STUDIO_API_TOKEN")


@when("I check the consultant settings for the host consultant")
def check_host_settings(context):
    with mock.patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("network used")) as opener:
        context.settings = provider_settings(provider="host")
        context.rendered_settings = render_provider_settings(context.settings)
    context.requests_sent = opener.call_count


@then("the host consultant is ready and needs no credential")
def host_ready(context):
    assert (context.settings["provider"], context.settings["ready"]) == ("host", True), context.settings
    assert context.settings["credential"] == {"variable": None, "required": False, "present": False}
    assert "Credential: none needed" in context.rendered_settings


@then("the settings say the application cannot verify which model writes a proposal")
def host_unverifiable(context):
    assert context.settings["model_verifiable"] is False
    assert "cannot verify" in context.rendered_settings


# ---- Serving a hosting agent ---------------------------------------------

@given("a commons served to a hosting agent as its consultant")
def served_to_host(context):
    context.app.close()  # each bridge call opens its own session, as the MCP server does
    context.root = Path(context.temporary.name)
    context.bridge = CaseToolBridge(context.root, None, host=True)


@given("David's contribution to the empty commons is retained")
def contribution_retained(context):
    context.request_id = retain(context)


@when("the hosting agent asks for the consultation")
def ask_consultation(context):
    context.revision_before = call(context, "inspect")["case"]["revision"]
    context.consultation = call(context, "consultation", request_id=context.request_id)


@then("it receives the procedure, domain context, request and proposal schema every provider consultant is sent")
def same_as_providers(context):
    consultation = context.consultation
    assert consultation["status"] == "awaiting_consultation", consultation
    # What a provider is sent for the same retained request, consulted in a copy of the commons.
    copy = context.root / "copy"
    shutil.copytree(context.root / CASE, copy, ignore=shutil.ignore_patterns("writer.lock"))
    recorder = ScriptedConsultant()
    with open_case(copy, consultant=recorder) as app:
        app.consult(context.request_id)
    assert consultation["request"] == recorder.calls[0]
    assert consultation["schema"] == request_schema(recorder.calls[0])
    # One procedure and domain context for every consultant; each adds only how to return the proposal.
    shared, transport = consulting_prompt(), consultation["prompt"]
    procedure, context_part = shared.split("\n\nDOMAIN CONTEXT\n")
    for prompt in (transport, LMStudioConsultant().system_prompt, AnthropicConsultant().system_prompt):
        assert prompt.startswith(procedure) and prompt.endswith("\n\nDOMAIN CONTEXT\n" + context_part)
    assert "propose" in transport and "submit_proposal" not in transport


@then("no model was called and no revision was published")
def nothing_called(context):
    assert call(context, "inspect")["case"]["revision"] == context.revision_before
    assert call(context, "receipts", request_id=context.request_id)["attempts"] == []


@when('the hosting agent proposes a valid reply as "{agent}" with model "{model}"')
@given('the hosting agent proposes a valid reply as "{agent}" with model "{model}"')
def propose_valid(context, agent, model):
    context.agent, context.model = agent, model
    context.result = propose(context, context.request_id, agent, model)


@then("a question is saved and the reply's proposals wait for David's decision")
def question_saved(context):
    result = context.result
    assert result["status"] == "saved", result
    assert len(result["proposed"]) == 2 and result["accepted_automatically"] == []
    backlog = call(context, "workspace", view="backlog")["workspace"]["backlog"]
    assert sorted(e["ref"] for e in backlog if e["entry"] == "proposal") == sorted(result["proposed"])
    question = call(context, "workspace")["workspace"]["question"]
    assert question["data"]["primary_prompt"] == "What should we observe next?"


@then("the received proposal was retained before it was validated")
def received_retained(context):
    attempts = call(context, "receipts", request_id=context.request_id)["attempts"]
    received = [a for a in attempts if "proposal" in a]
    assert received and received[-1]["proposal"]["proposed_updates"][0]["data"]["text"] == "We keep missing deliveries."


@then("the applied request records a host consultant version naming the declared agent and model")
def host_version(context):
    snapshot = call(context, "history")["revisions"][-1]
    version = snapshot["adapter_versions"][context.request_id]
    assert version.startswith("host/"), version
    assert f"/agent={context.agent}/" in version and f"/model={context.model}/" in version


@when("the hosting agent proposes a reply that cites a record the commons does not have")
def propose_invalid(context):
    context.revision_before = call(context, "inspect")["case"]["revision"]
    context.result = propose(context, context.request_id, cite="C9@1")


@then("the reply is rejected with a receipt that names the broken rule")
def rejected_with_reason(context):
    assert context.result["status"] == "rejected", context.result
    assert "C9@1" in context.result["reason"]
    attempts = call(context, "receipts", request_id=context.request_id)["attempts"]
    assert any(a.get("status") == "rejected" and "C9@1" in a.get("reason", "") for a in attempts)


@then("David's literal words are retained and no revision was published")
def words_kept(context):
    sources = call(context, "sources")["sources"]
    assert sources[context.request_id]["text"] == LITERAL
    assert call(context, "inspect")["case"]["revision"] == context.revision_before


# ---- Requests not awaiting a consultant -----------------------------------

@given("a request that {state}")
def request_in_state(context, state):
    if state == "was already answered":
        context.request_id = retain(context)
        assert propose(context, context.request_id)["status"] == "saved"
    elif state == "was overtaken by a newer question":
        context.request_id = retain(context)
        newer = retain(context, "A later contribution to the same question.")
        assert propose(context, newer)["status"] == "saved"
    elif state == "was never retained":
        context.request_id = "in000099"
    else:
        raise NotImplementedError(state)
    context.files_before = stored_files(context)


REFUSALS = {"is already answered": ("rejected", "already_applied"), "is stale": ("stale", "stale"),
            "was never retained": ("rejected", "not_retained")}


@then("the consultation is refused because the request {reason}")
def consultation_refused(context, reason):
    status, why = REFUSALS[reason]
    assert (context.consultation["status"], context.consultation["reason"]) == (status, why), context.consultation
    assert "request" not in context.consultation and "prompt" not in context.consultation


@then("the proposal is refused because the request {reason}")
def proposal_refused(context, reason):
    status, why = REFUSALS[reason]
    assert (context.result["status"], context.result["reason"]) == (status, why), context.result


@then("the commons is unchanged")
def unchanged(context):
    assert stored_files(context) == context.files_before


# ---- Where the host consultant is offered ---------------------------------

def offered(bridge):
    return {tool["name"] for tool in bridge.tools}


@then("the server offers consultation and propose instead of consult, submit and retry")
def host_tools(context):
    names = offered(context.bridge)
    assert {"consultation", "propose", "retain_input", "accept", "reject", "workspace"} <= names, names
    assert not names & {"consult", "submit", "retry"}, names


@then("changing the acceptance setting is still refused without the operator's grant")
def acceptance_refused(context):
    case = call(context, "inspect")["case"]
    result = call(context, "set_acceptance", mode="automatic", speaker="David", base_revision=case["revision"])
    assert result["status"] == "rejected", result
    assert call(context, "inspect")["case"]["membership"]["acceptance"] == "review"


@when("the commons is served with the offline guide instead")
def served_with_guide(context):
    context.bridge = CaseToolBridge(context.root, GuidedConsultant())


@then("the server offers consult, submit and retry and not consultation or propose")
def provider_tools(context):
    names = offered(context.bridge)
    assert {"consult", "submit", "retry"} <= names and not names & {"consultation", "propose"}, names


@when('I explicitly choose "host" for the terminal workspace')
def choose_host_for_tui(context):
    from reason_commons.adapters import tui
    with mock.patch.object(tui.ReasonCommonsApp, "run", side_effect=AssertionError("workspace opened")):
        try:
            tui.run(context.root / CASE, provider="host")
            context.error = None
        except ValueError as error:
            context.error = error


@then("the choice is rejected because only an agent using the MCP server can be the host consultant")
def host_rejected_for_tui(context):
    assert context.error is not None and "MCP" in str(context.error), context.error


# ---- The same commons in the terminal workspace ---------------------------

@given("David accepts one of the reply's proposals and rejects the other through the server")
def decide_through_server(context):
    accepted, rejected = context.result["proposed"]
    revision = call(context, "inspect")["case"]["revision"]
    assert call(context, "accept", refs=[accepted], speaker="David", base_revision=revision)["status"] == "saved"
    revision = call(context, "inspect")["case"]["revision"]
    assert call(context, "reject", refs=[rejected], speaker="David", base_revision=revision)["status"] == "saved"
    context.accepted, context.rejected = accepted, rejected


@when("the commons is opened in the terminal workspace")
def open_in_tui(context):
    from reason_commons.adapters.tui import ReasonCommonsApp
    path = context.root / CASE
    app = ReasonCommonsApp(path, "David", "guided", lambda c: open_case(path, consultant=c),
                           lambda provider: GuidedConsultant())

    async def run():
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            context.feedback = app.submission_feedback()
            context.question = app.workspace_value["question"]["data"]["primary_prompt"]
            context.reply_records = {r["ref"]: r["status"] for r in app.workspace_value["reply"]["records"]}
            context.backlog = app.case.workspace(view="backlog")["backlog"]
    asyncio.run(run())


@then("the saved question is shown with the host consultant as the one that asked it")
def tui_question(context):
    assert context.question == "What should we observe next?"
    assert "Coding agent" in context.feedback, context.feedback


@then("the accepted proposal is in the model, the rejected one is not, and nothing waits")
def tui_membership(context):
    assert context.reply_records == {context.accepted: "accepted", context.rejected: "rejected"}, context.reply_records
    assert context.backlog == []
