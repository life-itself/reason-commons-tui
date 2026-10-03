"""The composition root is the only place that chooses concrete adapters."""

import os
import uuid
from pathlib import Path

from reason_commons.adapters.clock import UTCClock
from reason_commons.adapters.filesystem import ArchiveCaseStore, FileCaseStore
from reason_commons.application.ports import StoreError
from reason_commons.application.service import CaseApplication
from reason_commons.domain.model import Snapshot


def configured_consultant(provider=None, model=None, base_url=None):
    """Explicit provider selection at composition, with no hosted fallback."""
    provider = provider or os.environ.get("REASON_COMMONS_PROVIDER", "lm-studio")
    if provider == "lm-studio":
        from reason_commons.adapters.lm_studio import LMStudioConsultant
        return LMStudioConsultant.from_env(model=model, base_url=base_url)
    if provider == "anthropic":
        from reason_commons.adapters.anthropic import AnthropicConsultant
        return AnthropicConsultant.from_env(model=model, base_url=base_url)
    raise ValueError("Choose provider lm-studio or anthropic")


def create_case(path, name="Untitled case", consultant=None, timezone="Europe/Berlin", clock=None):
    clock = clock or UTCClock()
    initial = Snapshot.initial(str(uuid.uuid4()), name, clock.now(), timezone)
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
