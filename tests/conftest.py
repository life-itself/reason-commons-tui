"""Every test runs with its own usage log and no monthly budget, so none touches the real log in
~/.local/state or inherits a budget from the shell. Subprocesses inherit the same environment."""

import pytest


@pytest.fixture(autouse=True)
def isolated_usage_log(tmp_path_factory, monkeypatch):
    monkeypatch.setenv("REASON_COMMONS_USAGE_LOG", str(tmp_path_factory.mktemp("usage") / "usage.jsonl"))
    monkeypatch.delenv("REASON_COMMONS_MONTHLY_BUDGET_USD", raising=False)
    # The saved settings could hold a budget or prices; a test that wants settings names its own file.
    monkeypatch.setenv("REASON_COMMONS_CONFIG", str(tmp_path_factory.mktemp("config") / "settings.yaml"))
