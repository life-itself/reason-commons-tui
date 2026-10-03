"""Separate conversational acceptance bindings; original product features stay intact."""
from pathlib import Path
from behave.runner import Runner


class ConversationRunner(Runner):
    def setup_paths(self):
        root = Path(__file__).resolve().parent
        self.config.steps_dir = str(root / "steps")
        self.config.environment_file = str(root / "environment.py")
        super().setup_paths()
