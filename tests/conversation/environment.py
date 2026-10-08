import os
from pathlib import Path
import tempfile

from reason_commons.bootstrap import create_case
from tests.support import ScriptedConsultant

# Provider choice and credentials come from the process environment. Every
# scenario starts with none of them, and gets back whatever it found.
PROVIDER_VARIABLES = (
    "REASON_COMMONS_PROVIDER", "REASON_COMMONS_ANTHROPIC_MODEL", "REASON_COMMONS_ANTHROPIC_URL",
    "REASON_COMMONS_ANTHROPIC_TIMEOUT", "ANTHROPIC_API_KEY", "REASON_COMMONS_LM_STUDIO_MODEL",
    "REASON_COMMONS_LM_STUDIO_URL", "REASON_COMMONS_LM_STUDIO_TIMEOUT", "LM_STUDIO_API_TOKEN",
    "REASON_COMMONS_USAGE_LOG", "REASON_COMMONS_MONTHLY_BUDGET_USD", "REASON_COMMONS_CONFIG")


def before_scenario(context, scenario):
    context.saved_environment = {name: os.environ.pop(name, None) for name in PROVIDER_VARIABLES}
    context.cleanups = []
    context.temporary = tempfile.TemporaryDirectory()
    # Each scenario has its own usage log and no saved settings.
    context.usage_log = Path(context.temporary.name) / "usage.jsonl"
    os.environ["REASON_COMMONS_USAGE_LOG"] = str(context.usage_log)
    os.environ["REASON_COMMONS_CONFIG"] = str(Path(context.temporary.name) / "settings.yaml")
    context.path = Path(context.temporary.name) / "case"
    context.consultant = ScriptedConsultant()
    context.app = create_case(context.path, "Payments", consultant=context.consultant)


def after_scenario(context, scenario):
    context.app.close()
    for cleanup in reversed(context.cleanups):
        cleanup()
    for name, value in context.saved_environment.items():
        os.environ.pop(name, None)
        if value is not None:
            os.environ[name] = value
    context.temporary.cleanup()
