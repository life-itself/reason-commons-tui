"""One authorized skill invocation over an already composed commons session."""

from copy import deepcopy
from importlib.resources import files
import inspect

from reason_commons.adapters.skill_agent import ContributionToolHost, LMStudioSkillAgent
from reason_commons.adapters.skills import RetainedContributionWorkflow
from reason_commons.application.ports import CaseCapabilities
from reason_commons.adapters.rendering import workspace_output
from reason_commons.domain.model import CONSULT_INTENTS


def procedure_text():
    return files("reason_commons.adapters").joinpath("contribution_skill/SKILL.md").read_text(encoding="utf-8")


class HostCapabilities:
    """Adapt the existing deterministic driver to the same bounded tool host."""

    def __init__(self, host):
        self.host = host

    def __getattr__(self, name):
        if name not in {"inspect", "retain_input", "consult", "retry"}:
            raise AttributeError(name)

        def call(*args, **kwargs):
            arguments = inspect.signature(getattr(CaseCapabilities, name)).bind(None, *args, **kwargs).arguments
            arguments.pop("self")
            return self.host.invoke(name, dict(arguments))
        return call


def run_contribution(app, consultant, *, text=None, speaker=None, declarations=None,
                     retry_request=None, runner="procedure", intent="answer", target=None):
    """Run once; derive publication status from capability results, never prose.

    The procedure runner is an explicit deterministic alternative, not a fallback
    after agent failure. Neither runner starts an implicit semantic retry.
    """
    if runner not in {"agent", "procedure"}:
        raise ValueError("Unknown skill runner")
    if intent not in {"answer"} | CONSULT_INTENTS:
        raise ValueError("Unknown consultant intent")
    if target is not None and (not isinstance(target, dict) or
            set(target) != {"base_revision", "response_target"} or type(target["base_revision"]) is not int
            or not (target["response_target"] is None or isinstance(target["response_target"], str))):
        raise ValueError("Supply the exact displayed revision and response target")
    if retry_request is None:
        if not isinstance(text, str) or not text.strip() or not isinstance(speaker, str) or not speaker.strip():
            raise ValueError("Supply a nonempty literal contribution and declared speaker")
    elif not isinstance(retry_request, str) or not retry_request:
        raise ValueError("Supply the original retained request identity")
    declarations = deepcopy(declarations or {})
    host = ContributionToolHost(app, text=text, speaker=speaker, declarations=declarations,
                                retry_request=retry_request, intent=intent, target=target)
    authorization = ({"operation": "retry", "request_id": retry_request, "explicitly_authorized": True}
                     if retry_request is not None else
                     {"operation": "contribute", "text": text, "speaker": speaker, "declarations": declarations,
                      "intent": intent, "target": target})
    if runner == "agent":
        context = files("reason_commons.domain").joinpath("CONTEXT.md").read_text(encoding="utf-8")
        agent = LMStudioSkillAgent(consultant, procedure_text(), context)
        outcome = agent.run(host, authorization)
        version = agent.version
    else:
        workflow = RetainedContributionWorkflow(HostCapabilities(host))
        if retry_request is not None:
            workflow.retry_retained(retry_request)
        else:
            workflow.contribute(text, speaker, declarations, intent=intent, target=target)
        outcome = {"status": "completed"}
        version = "retained-contribution-procedure/1"
    semantic = [e for e in host.trace if e["name"] not in {"inspect", "workspace"}]
    applied = [e for e in semantic if e["allowed"] and e["result"].get("status") != "tool_error"]
    result = {k: deepcopy(v) for k, v in applied[-1]["result"].items() if k not in {"workspace", "rendered"}} if applied else {"status": "skill_incomplete"}
    if not applied and retry_request is None:
        result.update(draft=text, speaker=speaker, recovery_actions=["copy_text", "run_contribution_again"])
    if result.get("status") == "input_retained":
        result["recovery_actions"] = ["consult_retained_input"]
    names = [e["name"] for e in semantic]
    expected = (["retry"] if retry_request is not None else
                ["retain_input", "consult"] if names and semantic[0]["result"].get("status") == "input_retained"
                else ["retain_input"])
    complete = (names == expected and all(e["allowed"] for e in host.trace)
                and (retry_request is not None or bool(host.trace) and host.trace[0]["name"] in {"inspect", "workspace"})
                and outcome["status"] == "completed")
    workspace = app.workspace()
    return {"result": result, "procedure_completed": complete, "runner": runner,
            "agent_status": outcome["status"], "agent_reply": outcome.get("final"),
            "runner_version": version, "provider_version": consultant.version,
            "trace": deepcopy(host.trace), "revision": workspace["revision"],
            "current_intervention": workspace["question"],
            **workspace_output(workspace, result=result, speaker=speaker)}
