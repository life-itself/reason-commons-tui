from pathlib import Path
import tempfile

from reason_commons.bootstrap import create_case
from tests.support import ScriptedConsultant


def before_scenario(context, scenario):
    context.temporary = tempfile.TemporaryDirectory()
    context.path = Path(context.temporary.name) / "case"
    context.consultant = ScriptedConsultant()
    context.app = create_case(context.path, "Payments", consultant=context.consultant)


def after_scenario(context, scenario):
    context.app.close()
    context.temporary.cleanup()
