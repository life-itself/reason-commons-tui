"""Personal settings chosen on first start: your name, consultant and model, the theme and a monthly budget.

They live outside every goal folder (never in a case or an export), in
``$REASON_COMMONS_CONFIG`` or ``$XDG_CONFIG_HOME/reason-commons/settings.yaml``
(default ``~/.config/reason-commons/settings.yaml``), readable only by you.
Precedence stays: command-line flags, then environment variables, then these
settings, then built-in defaults. The settings fill in environment variables
that are not already set, so every adapter keeps reading its usual variables.
"""

import os
from pathlib import Path
import tempfile

import yaml

VERSION = 1
CONSULTANTS = ("guided", "anthropic", "lm-studio")
# Settings key -> environment variable it fills in when that variable is unset.
ENVIRONMENT = {
    ("name",): "REASON_COMMONS_SPEAKER",
    ("consultant",): "REASON_COMMONS_PROVIDER",
    ("anthropic", "model"): "REASON_COMMONS_ANTHROPIC_MODEL",
    ("anthropic", "boost_model"): "REASON_COMMONS_ANTHROPIC_BOOST_MODEL",
    ("anthropic", "api_key"): "ANTHROPIC_API_KEY",
    ("lm_studio", "url"): "REASON_COMMONS_LM_STUDIO_URL",
    ("lm_studio", "model"): "REASON_COMMONS_LM_STUDIO_MODEL",
    ("theme",): "REASON_COMMONS_THEME",
    ("usage", "monthly_budget_usd"): "REASON_COMMONS_MONTHLY_BUDGET_USD",
}


def settings_path():
    explicit = os.environ.get("REASON_COMMONS_CONFIG")
    if explicit:
        return Path(os.path.expanduser(explicit))
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "reason-commons" / "settings.yaml"


def state_folder(environ=None):
    """Where Reason Commons keeps what it remembers for you that is not a choice: ``$XDG_STATE_HOME/reason-commons``
    (default ``~/.local/state/reason-commons``). Outside every goal, like the settings."""
    environ = os.environ if environ is None else environ
    state = environ.get("XDG_STATE_HOME") or ""
    base = Path(state) if os.path.isabs(state) else Path(os.path.expanduser("~/.local/state"))
    return base / "reason-commons"


def _get(data, keys):
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        return str(data)  # a number written by hand, such as a budget of 5
    return data if isinstance(data, str) and data.strip() else None


class Settings:
    """A small mapping saved as YAML; ``exists`` is False until first start finishes."""

    def __init__(self, path=None, data=None, exists=False):
        self.path = Path(path) if path else settings_path()
        self.data = data or {}
        self.exists = exists

    @classmethod
    def load(cls, path=None):
        path = Path(path) if path else settings_path()
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, yaml.YAMLError):
            return cls(path)
        return cls(path, data if isinstance(data, dict) else {}, exists=True)

    def get(self, *keys):
        return _get(self.data, keys)

    def set(self, value, *keys):
        target = self.data
        for key in keys[:-1]:
            target = target.setdefault(key, {})
        if value is None:
            target.pop(keys[-1], None)
        else:
            target[keys[-1]] = value

    def save(self):
        """Write atomically, readable and writable only by you (it may hold an API key)."""
        self.data["version"] = VERSION
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        handle, temporary = tempfile.mkstemp(prefix=".settings-", dir=self.path.parent)
        try:
            os.fchmod(handle, 0o600)
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write("# Reason Commons personal settings. Never copied into goals or exports.\n")
                yaml.safe_dump(self.data, stream, allow_unicode=True, sort_keys=False)
            os.replace(temporary, self.path)
        except BaseException:
            if os.path.exists(temporary):
                os.unlink(temporary)
            raise
        self.exists = True

    def apply(self, environ=None, override=False):
        """Fill in unset environment variables (all of them with override, after setup)."""
        environ = os.environ if environ is None else environ
        for keys, variable in ENVIRONMENT.items():
            value = self.get(*keys)
            if value and (override or not environ.get(variable)):
                environ[variable] = value
        if self.get("consultant") == "lm-studio" and override and not self.get("lm_studio", "model"):
            environ.pop("REASON_COMMONS_LM_STUDIO_MODEL", None)

    def overridden(self, environ=None):
        """Environment variables that were already set to something else and so win over these settings."""
        environ = os.environ if environ is None else environ
        return [variable for keys, variable in ENVIRONMENT.items()
                if self.get(*keys) and environ.get(variable) and environ[variable] != self.get(*keys)]


def describe(settings):
    """One line for the home screen: who you are and which consultant answers."""
    consultant = settings.get("consultant") or "guided"
    if consultant == "anthropic":
        what = f"Claude ({settings.get('anthropic', 'model') or 'default model'})"
    elif consultant == "lm-studio":
        what = f"LM Studio ({settings.get('lm_studio', 'model') or 'the loaded model'})"
    else:
        what = "built-in guide (offline)"
    return f"{settings.get('name') or 'no name yet'} · {what}"


SHORT_CONSULTANTS = {"guided": "offline guide", "anthropic": "Claude", "lm-studio": "local model"}


def summary(settings):
    """Who you are and who asks the questions, in a few words: 'David · offline guide'."""
    consultant = settings.get("consultant") or "guided"
    return " · ".join(part for part in (settings.get("name"), SHORT_CONSULTANTS.get(consultant, consultant))
                      if part)


def model_hint(model_id):
    """A plain trade-off for a Claude model, from its family name."""
    lowered = model_id.lower()
    if "opus" in lowered:
        return "most capable; slower and costs more"
    if "sonnet" in lowered:
        return "deeper reasoning; costs more per reply"
    if "haiku-5-5" in lowered:
        return "lowest cost; quick, lighter reasoning"
    if "haiku" in lowered:
        return "older; not validated as a consultant"
    if "fable" in lowered or "mythos" in lowered:
        return "top tier; highest cost"
    return ""
