"""The composition root is the only place that chooses concrete adapters."""

import uuid

from reason_commons.adapters.clock import UTCClock
from reason_commons.adapters.filesystem import FileCaseStore
from reason_commons.application.service import CaseApplication
from reason_commons.domain.model import Snapshot


def create_case(path, name="Untitled case", consultant=None, timezone="Europe/Berlin", clock=None):
    clock = clock or UTCClock()
    initial = Snapshot.initial(str(uuid.uuid4()), name, clock.now(), timezone)
    return CaseApplication(FileCaseStore.create(path, initial), clock, consultant, timezone)


def open_case(path, consultant=None, writable=True, clock=None):
    store = FileCaseStore(path, writable=writable)
    return CaseApplication(store, clock or UTCClock(), consultant, store.current().value["timezone"])


def import_case(bundle, destination, consultant=None, clock=None):
    store = FileCaseStore.import_bundle(bundle, destination)
    return CaseApplication(store, clock or UTCClock(), consultant, store.current().value["timezone"])

