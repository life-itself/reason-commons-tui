"""Locate external bindings while running the authoritative feature files in place."""

from pathlib import Path
from behave.runner import Runner


class AcceptanceRunner(Runner):
    def setup_paths(self):
        bindings = Path(__file__).resolve().parent
        self.config.steps_dir = str(bindings / "steps")
        self.config.environment_file = str(bindings / "environment.py")
        super().setup_paths()
