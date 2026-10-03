from copy import deepcopy
from typing import Optional

from reason_commons.domain.model import InvalidCase, StaleWork, validate_input
from reason_commons.application.ports import (CaseStore, Clock, Consultant,
                                              ConsultantResponseError, StoreError)


STORAGE_HELP = (
    "Committed YAML revisions are immutable by application policy: the app never overwrites them. "
    "Content hashes detect mismatches. An owner can edit files outside the app; "
    "these files are not tamper-proof evidence."
)


class CaseApplication:
    """One writer session; synchronous use cases can run in a future TUI worker.

    Interfaces project state and invoke these use cases; they own no reasoning,
    consulting or persistence rules. Skills share the semantic capability surface.
    The application never trusts a skill to enforce case rules. Failed input
    retention leaves a copy in this session so an adapter can keep its editor.
    """

    def __init__(self, store: CaseStore, clock: Clock, consultant: Optional[Consultant] = None,
                 timezone: str = "Europe/Berlin"):
        self._store = store
        self._clock = clock
        self._consultant = consultant
        self._timezone = timezone
        self.unsaved_input = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._store.close()

    def inspect(self) -> dict:
        return {"schema_version": "1", "case": self._store.current().to_dict(),
                "cursor": deepcopy(self._store.cursor())}

    def history(self) -> dict:
        return {"schema_version": "1", "revisions": [s.to_dict() for s in self._store.history()]}

    def workspace(self, view: str = "next", revision: Optional[int] = None,
                  selection: Optional[str] = None) -> dict:
        """Read one frozen presentation model, locally, without changing state."""
        from reason_commons.application.presentation import project_workspace
        current = self._store.current()
        if revision is not None and (type(revision) is not int or revision < 0):
            raise InvalidCase("Revision must be a nonnegative integer")
        snapshots = self._store.history() if revision is not None or view == "history" else []
        snapshot = current
        if revision is not None:
            snapshot = next((s for s in snapshots if s.revision == revision and s.revision <= current.revision), None)
            if snapshot is None:
                raise InvalidCase("Revision is not in this case's published history")
        sources = self._store.sources()
        pending = []
        for value in sources.values():
            request_id = value.get("request_id")
            if request_id and request_id not in current.value["applied_requests"]:
                attempts = self._store.attempts(request_id)
                # File ordering is not attempt ordering (start sorts after result).
                # Preserve audit details in receipts; present only status here.
                latest = max((a.get("attempt", 0) for a in attempts), default=0)
                receipts = [a for a in attempts if a.get("attempt") == latest and "status" in a
                            and a["status"] != "started"]
                pending.append({"input": deepcopy(value), "attempt": latest,
                                "status": receipts[-1]["status"] if receipts else
                                "started" if latest else "input_retained"})
        history = [{"revision": s.revision, "parent": s.value["parent"], "timestamp": s.value["timestamp"],
                    "current_target": s.target} for s in snapshots if s.revision <= current.revision]
        return project_workspace(snapshot, sources, view=view, selection=selection, live_revision=current.revision,
                                 cursor=self._store.cursor(), history=history, pending=pending)

    def sources(self) -> dict:
        return {"schema_version": "1", "sources": deepcopy(self._store.sources())}

    def checkpoint(self, cursor: dict) -> dict:
        # Presentation schema stays separate from reasoning and can grow in p1.
        from reason_commons.domain.model import shape, require
        shape(cursor, {"view", "focus", "selection", "scroll_anchor", "draft", "caret", "speaker",
                       "response_target", "base_revision", "display", "menu", "save_status"},
              {"view", "focus", "draft", "caret", "speaker", "response_target", "base_revision"}, "cursor")
        require(isinstance(cursor["draft"], str) and type(cursor["caret"]) is int and
                0 <= cursor["caret"] <= len(cursor["draft"]), "Invalid draft/caret")
        current = self._store.current()
        require(cursor["response_target"] == current.target and cursor["base_revision"] == current.revision,
                "Cursor target is stale")
        for key in ("view", "focus", "speaker"):
            require(isinstance(cursor[key], str) and bool(cursor[key]), f"Invalid cursor {key}")
        try:
            self._store.checkpoint(deepcopy(cursor))
            return {"status": "saved", "revision": current.revision}
        except StoreError:
            self.unsaved_input = deepcopy(cursor)
            return {"status": "not_saved", "message": "not saved", "draft": cursor["draft"],
                    "recovery_actions": ["copy_text", "choose_writable_export"]}

    def retain_input(self, text: str, speaker: str, base_revision: int,
                     response_target: Optional[str], intent: str = "answer",
                     declarations: Optional[dict] = None, request_id: Optional[str] = None) -> dict:
        current = self._store.current()
        if current.revision != base_revision or current.target != response_target:
            return {"status": "stale", "message": "Re-evaluate against the current revision",
                    "draft": text, "recovery_actions": ["reevaluate_current_revision"]}
        request_id = request_id or self._store.next_request_id()
        value = {"schema_version": "1", "request_id": request_id, "base_revision": base_revision,
                 "response_target": response_target, "text": text, "speaker": speaker, "intent": intent,
                 "declarations": deepcopy(declarations or {}), "timestamp": self._clock.now(),
                 "timezone": self._timezone}
        validate_input(value)
        self.unsaved_input = deepcopy(value)
        try:
            self._store.retain(value)
        except StoreError:
            return {"status": "not_saved", "message": "not saved; input not retained", "draft": text,
                    "request_id": request_id, "recovery_actions": ["copy_text", "choose_writable_export"]}
        self.unsaved_input = None
        return {"status": "input_retained", "request_id": request_id, "revision": current.revision}

    def submit(self, text: str, speaker: str, base_revision: int, response_target: Optional[str],
               intent: str = "answer", declarations: Optional[dict] = None,
               request_id: Optional[str] = None) -> dict:
        retained = self.retain_input(text, speaker, base_revision, response_target, intent, declarations, request_id)
        return self.consult(retained["request_id"]) if retained["status"] == "input_retained" else retained

    def receipts(self, request_id: str) -> dict:
        self._store.input(request_id)  # validate identity before constructing file paths
        return {"schema_version": "1", "attempts": deepcopy(self._store.attempts(request_id))}

    def consult(self, request_id: str) -> dict:
        value = self._store.input(request_id)
        current = self._store.current()
        if request_id in current.value["applied_requests"]:
            try:
                self._store.confirm_durable()
            except StoreError:
                return self._failure(request_id, "not_saved", "not saved; publication durability unconfirmed",
                                     ["retry_retained_input"], persist=False)
            return {"status": "saved", "request_id": request_id, "revision": current.revision,
                    "already_applied": True}
        if value["base_revision"] != current.revision or value["response_target"] != current.target:
            return self._failure(request_id, "stale", "Response is stale; re-evaluate against the current revision",
                                 ["reevaluate_current_revision"])
        response = self._store.pending_response(request_id)
        attempt = response["attempt"] if response else 0
        if response is None:
            if self._consultant is None:
                return self._failure(request_id, "unavailable", "Input retained; consultant unavailable",
                                     ["retry_retained_input"])
            try:
                attempt = self._store.start_attempt(request_id)
            except StoreError:
                return self._failure(request_id, "not_saved", "not saved; input retained; request did not start",
                                     ["retry_retained_input"], persist=False)
            try:
                proposal = self._consultant.propose({"input": deepcopy(value), "case": current.to_dict(),
                                                    "sources": deepcopy(self._store.sources())})
            except ConsultantResponseError:
                return self._failure(request_id, "rejected", "Input retained; invalid structured response rejected",
                                     ["inspect_failure", "reevaluate_current_revision"], attempt)
            except Exception:
                # Provider exception text can include credentials; retain category only.
                return self._failure(request_id, "unavailable", "Input retained; consultant unavailable",
                                     ["retry_retained_input"], attempt)
            try:
                self._store.received(request_id, attempt, proposal, self._consultant.version)
                response = {"proposal": proposal, "version": self._consultant.version}
            except (StoreError, TypeError, ValueError):
                return self._failure(request_id, "not_saved", "not saved; input retained; response not retained",
                                     ["retry_retained_input"], attempt)
        try:
            # Read again after the adapter returns; a stale base never merges implicitly.
            current = self._store.current()
            snapshot = current.apply(response["proposal"], value, self._store.sources(), self._store.next_revision(),
                                     self._clock.now(), self._timezone, response["version"],
                                     self._store.reserved_counters())
            self._store.commit(snapshot, current.revision)
        except StaleWork:
            return self._failure(request_id, "stale", "Response is stale; re-evaluate against the current revision",
                                 ["reevaluate_current_revision"], attempt)
        except (InvalidCase, TypeError, KeyError, AttributeError):
            return self._failure(request_id, "rejected", "Input retained; invalid or out-of-profile response rejected",
                                 ["inspect_failure", "reevaluate_current_revision"], attempt)
        except StoreError:
            return self._failure(request_id, "not_saved", "not saved; input and response retained",
                                 ["retry_retained_input", "choose_writable_export"], attempt)
        result = {"status": "saved", "request_id": request_id, "revision": snapshot.revision}
        try:
            self._store.receipt(request_id, attempt, result)
        except StoreError:
            # The committed snapshot's applied ledger is authoritative after publication.
            result["receipt_pending"] = True
        return result

    def retry(self, request_id: str) -> dict:
        return self.consult(request_id)

    def _failure(self, request_id, status, message, recovery, attempt=0, persist=True):
        result = {"status": status, "request_id": request_id, "message": message,
                  "recovery_actions": recovery, "input_retained": True}
        if persist:
            try:
                self._store.receipt(request_id, attempt, result)
            except StoreError:
                result["receipt_pending"] = True
        return result

    def add_source(self, name: str, content: bytes, speaker: str) -> str:
        return self._store.add_source(name, content, speaker)

    def export(self, destination: str):
        recovery_cursor = None
        if self.unsaved_input is not None:
            recovery = self.unsaved_input
            recovery_cursor = self._store.cursor()
            recovery_cursor.update(view=recovery.get("view", "next"), focus="response",
                                   draft=recovery.get("text", recovery.get("draft", "")),
                                   speaker=recovery["speaker"], response_target=recovery["response_target"],
                                   base_revision=recovery["base_revision"])
            recovery_cursor["caret"] = len(recovery_cursor["draft"])
            recovery_cursor["save_status"] = "input_not_retained"
        self._store.export(destination, cursor_override=recovery_cursor)

    def storage_help(self) -> str:
        return STORAGE_HELP
