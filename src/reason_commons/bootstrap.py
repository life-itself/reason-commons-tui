"""The composition root is the only place that chooses concrete adapters."""

import os
import uuid
from pathlib import Path

from reason_commons.adapters.clock import UTCClock
from reason_commons.adapters.filesystem import ArchiveCaseStore, FileCaseStore
from reason_commons.application.ports import StoreError
from reason_commons.application.service import CaseApplication
from reason_commons.domain.model import Snapshot


PROVIDERS = ("lm-studio", "anthropic", "guided")
DEFAULT_PROVIDER = "lm-studio"


def _choose_provider(provider, environ=os.environ):
    """Explicit choice beats the environment, which beats the local default."""
    for value, source in ((provider, "explicit"), (environ.get("REASON_COMMONS_PROVIDER"), "environment")):
        if value is not None and value.strip():
            name = value.strip().lower()
            if name not in PROVIDERS:
                raise ValueError(f"Unknown provider {value!r}; choose one of: {', '.join(PROVIDERS)}")
            return name, source
    return DEFAULT_PROVIDER, "default"


def provider_settings(provider=None, model=None, base_url=None, environ=os.environ):
    """What would be used and whether it is ready: offline, no request, no secret value."""
    name, source = _choose_provider(provider, environ)
    if name == "guided":
        settings = {"model": "built-in guide", "model_source": "default", "endpoint": None,
                    "credential": {"variable": None, "required": False, "present": False}, "problems": []}
        return {"provider": name, "selected_by": source, "providers": list(PROVIDERS),
                **settings, "ready": True}
    if name == "anthropic":
        from reason_commons.adapters.anthropic import AnthropicConsultant as Adapter
    else:
        from reason_commons.adapters.lm_studio import LMStudioConsultant as Adapter
    settings = Adapter.describe_settings(model=model, base_url=base_url, environ=environ)
    return {"provider": name, "selected_by": source, "providers": list(PROVIDERS),
            **settings, "ready": not settings["problems"]}


def configured_consultant(provider=None, model=None, base_url=None):
    """Explicit provider selection at composition, with no hosted fallback."""
    name, _ = _choose_provider(provider)
    if name == "guided":
        from reason_commons.adapters.guided import GuidedConsultant
        return GuidedConsultant()
    if name == "anthropic":
        from reason_commons.adapters.anthropic import AnthropicConsultant
        return AnthropicConsultant.from_env(model=model, base_url=base_url)
    from reason_commons.adapters.lm_studio import LMStudioConsultant
    return LMStudioConsultant.from_env(model=model, base_url=base_url)


def create_case(path, name="Untitled case", consultant=None, timezone="Europe/Berlin", clock=None,
                acceptance="review", actor=None):
    clock = clock or UTCClock()
    initial = Snapshot.initial(str(uuid.uuid4()), name, clock.now(), timezone, acceptance, actor)
    return CaseApplication(FileCaseStore.create(path, initial), clock, consultant, timezone)


def open_case(path, consultant=None, writable=True, clock=None):
    if Path(path).suffix == ".reasoncase":
        if writable:
            raise StoreError("Archives are read-only; explicitly import into a new store to edit")
        store = ArchiveCaseStore(path)
    else:
        store = FileCaseStore(path, writable=writable)
    return CaseApplication(store, clock or UTCClock(), consultant, store.current().value["timezone"])


def import_case(bundle, destination, consultant=None, clock=None):
    store = FileCaseStore.import_bundle(bundle, destination)
    return CaseApplication(store, clock or UTCClock(), consultant, store.current().value["timezone"])
