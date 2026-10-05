from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def before_scenario(context, scenario):
    context.temporary = tempfile.TemporaryDirectory()
    context.path = Path(context.temporary.name) / "case"
    context.apps = []
    context.workspaces = []


def after_scenario(context, scenario):
    for workspace in context.workspaces:
        workspace.close()
    for app in context.apps:
        app.close()
    context.temporary.cleanup()

