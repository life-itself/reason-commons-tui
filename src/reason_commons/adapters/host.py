"""The coding agent hosting the skill as the consultant (provider ``host``).

The agent reads what any provider is sent (``consultation_package``) and hands its proposal
back; ``HostConsultant`` returns that one proposal to the application's ``consult``, which
receives, validates and publishes it or refuses it with a receipt, exactly as for a provider.
Nothing here decides whether a request may be consulted. The agent and model are what the
agent declares: recorded in the consultant version, never verified.
"""

from copy import deepcopy
from hashlib import sha256
import re

from reason_commons.adapters.provider_support import consulting_prompt, consulting_resources, request_schema
from reason_commons.application.ports import ConsultantResponseError
from reason_commons.domain.model import FIELDS, PROFILE, SCHEMA


NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
TRANSPORT = (
    "\n\nHOST TRANSPORT\nYou are the consultant for this one request, as any provider would be. Reason only from "
    "this procedure, the domain context and the request that came with them: chat history, files and anything else "
    "you know about the participant are not part of the commons and must not shape the proposal. Return the complete "
    "proposal by calling the propose tool exactly once, with the proposal as its proposal argument and with agent "
    "and model naming yourself as truthfully as you can; the application records them and cannot check them. The "
    "proposal is a JSON object matching the schema that came with this request. Its top level has exactly six "
    f"fields: schema_version (\"{SCHEMA}\"), delivery_profile (\"{PROFILE}\"), request_id, base_revision, "
    "intervention and proposed_updates. Everything about the next move (kind, purpose, primary_prompt, rationale, "
    "goal_ref, decision, options, required_context_refs) goes inside the intervention object; never invent another "
    "field. An update's data has only the fields of its operation: "
    + "; ".join(f"record_{kind}: {', '.join(sorted(fields))}" for kind, fields in FIELDS.items()) + ". "
    "The proposal is data for validation. It saves nothing by itself, and every update in it waits for the "
    "participant's decision: as the consultant, never accept, reject or undo anything.")


def consultation_package(state):
    """A consultation the application found due, with the procedure and schema every consultant is given."""
    return {**state, "prompt": consulting_prompt(TRANSPORT), "schema": request_schema(state["request"])}


class HostConsultant:
    """Hands one proposal the hosting agent wrote to the application, once."""

    def __init__(self, proposal, agent, model):
        for value, label in ((agent, "agent"), (model, "model")):
            if not isinstance(value, str) or not NAME.fullmatch(value):
                raise ValueError(f"Declare the {label} as a short name of letters, digits, dots, hyphens or underscores")
        self.agent, self.model = agent, model
        self._proposal = deepcopy(proposal)
        self.called = False
        procedure, context = consulting_resources()
        self._procedure, self._context = procedure + TRANSPORT, context

    @property
    def version(self):
        return (f"host/adapter=1/agent={self.agent}/model={self.model}/verified=no"
                f"/procedure={sha256(self._procedure.encode()).hexdigest()[:16]}"
                f"/context={sha256(self._context.encode()).hexdigest()[:16]}")

    def propose(self, request):
        if self.called:
            raise ConsultantResponseError("A host consultant hands over one proposal")
        self.called = True
        if not isinstance(self._proposal, dict):
            raise ConsultantResponseError("The proposal must be a JSON object")
        return deepcopy(self._proposal)
