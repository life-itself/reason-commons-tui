import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

# What a scenario must not inherit or leave behind: the usage log, a monthly budget, saved settings.
ISOLATED = ("REASON_COMMONS_USAGE_LOG", "REASON_COMMONS_MONTHLY_BUDGET_USD", "REASON_COMMONS_CONFIG")


def before_scenario(context, scenario):
    context.temporary = tempfile.TemporaryDirectory()
    context.path = Path(context.temporary.name) / "case"
    context.apps = []
    context.workspaces = []
    context.saved_isolated = {name: os.environ.pop(name, None) for name in ISOLATED}
    os.environ["REASON_COMMONS_USAGE_LOG"] = str(Path(context.temporary.name) / "usage.jsonl")
    os.environ["REASON_COMMONS_CONFIG"] = str(Path(context.temporary.name) / "settings.yaml")


def after_scenario(context, scenario):
    for workspace in context.workspaces:
        workspace.close()
    for app in context.apps:
        app.close()
    for name, value in context.saved_isolated.items():
        os.environ.pop(name, None)
        if value is not None:
            os.environ[name] = value
    context.temporary.cleanup()

