"""A replaceable workflow using only published application capabilities.

This deterministic driver is the skill evaluation baseline, not an LLM or a
semantic consultant. A real agent can make the same capability calls.
"""

from reason_commons.application.ports import CaseCapabilities


class RetainedContributionWorkflow:
    def __init__(self, capabilities: CaseCapabilities):
        self.capabilities = capabilities

    def contribute(self, text, speaker, declarations=None):
        context = self.capabilities.inspect()["case"]
        retained = self.capabilities.retain_input(text, speaker, context["revision"],
                                                  context["current_intervention"], declarations=declarations)
        if retained["status"] != "input_retained":
            return retained
        return self.capabilities.consult(retained["request_id"])

    def retry_retained(self, request_id):
        # Explicit retry uses the original request, target, attribution, and input.
        return self.capabilities.retry(request_id)

