from copy import deepcopy
from typing import List, Optional

from reason_commons.domain.model import InvalidCase, StaleWork, validate_input
from reason_commons.application.ports import (CaseStore, Clock, Consultant,
                                              ConsultantResponseError, StoreError)


STORAGE_HELP = (
    "Committed YAML revisions are immutable by application policy: the app never overwrites them. "
    "Content hashes detect mismatches. An owner can edit files outside the app; "
    "these files are not tamper-proof evidence."
)


FAILURE_CATEGORIES = {"configuration", "http_error", "timeout", "connection"}


def consulting_view(snapshot):
    """What the consultant needs to know about membership: what is in the model, what still
    waits for the operator, and which records in the model are flagged for review."""
    membership = snapshot.membership()
    return {"acceptance": membership.acceptance,
            "in_model": membership.model(),
            "waiting": [e["ref"] for e in membership.backlog() if e["entry"] == "proposal"],
            "not_admitted": [ref for ref, s in membership.status.items() if s in {"rejected", "undone", "closed"}],
            "reviews": membership.flags()}


def failure_detail(error):
    """Safe diagnostics from any consultant failure; never its message or body.

    A consultant may tag its exception with a ``category`` from a fixed set and
    an integer ``http_status``. Anything else is reported as ``unknown``.
    """
    category = getattr(error, "category", None)
    detail = {"failure_category": category if category in FAILURE_CATEGORIES else "unknown"}
    status = getattr(error, "http_status", None)
    if type(status) is int and 100 <= status <= 599:
        detail["http_status"] = status
    return detail


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
        history, applied, decided = [], set(), 0
        for s in (s for s in snapshots if s.revision <= current.revision):
            requests = [r for r in s.value["applied_requests"] if r not in applied]
            decisions = s.value.get("decisions", [])
            history.append({"revision": s.revision, "parent": s.value["parent"], "timestamp": s.value["timestamp"],
                            "current_target": s.target, "request_id": requests[0] if requests else None,
                            "decisions": deepcopy(decisions[decided:])})
            applied.update(requests)
            decided = len(decisions)
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
        require(cursor["response_target"] == current.target and type(cursor["base_revision"]) is int
                and cursor["base_revision"] <= current.revision, "Cursor target is stale")
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
        # Decisions about proposals since the draft was begun do not make it stale; a new question does.
        if type(base_revision) is not int or base_revision > current.revision or current.target != response_target:
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
        if value["response_target"] != current.target:
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
                # Only words the case took in, this answer and supplied sources: a stale answer is not shown.
                taken_in = set(current.value["applied_requests"]) | {request_id}
                sources = {ref: source for ref, source in self._store.sources().items()
                           if "request_id" not in source or ref in taken_in}
                proposal = self._consultant.propose({"input": deepcopy(value), "case": current.to_dict(),
                                                    "sources": deepcopy(sources),
                                                    "model": consulting_view(current)})
            except ConsultantResponseError:
                return self._failure(request_id, "rejected", "Input retained; invalid structured response rejected",
                                     ["inspect_failure", "reevaluate_current_revision"], attempt)
            except Exception as exc:
                # Provider exception text can include credentials; retain category only.
                return self._failure(request_id, "unavailable", "Input retained; consultant unavailable",
                                     ["retry_retained_input"], attempt, detail=failure_detail(exc))
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
        except (InvalidCase, TypeError, KeyError, AttributeError) as exc:
            # Say which rule the reply broke. A validation message is the domain's own wording (any
            # proposal values in it are already retained with the attempt); other errors keep their type only.
            reason = str(exc)[:300] if isinstance(exc, InvalidCase) else f"malformed response ({type(exc).__name__})"
            return self._failure(request_id, "rejected", "Input retained; invalid or out-of-profile response rejected",
                                 ["inspect_failure", "reevaluate_current_revision"], attempt,
                                 detail={"reason": reason})
        except StoreError:
            return self._failure(request_id, "not_saved", "not saved; input and response retained",
                                 ["retry_retained_input", "choose_writable_export"], attempt)
        result = {"status": "saved", "request_id": request_id, "revision": snapshot.revision}
        automatic = [d for d in snapshot.value["decisions"] if d.get("request_id") == request_id]
        result["proposed"] = [r["ref"] for r in snapshot.value["records"][len(current.value["records"]):]
                              if r["kind"] != "intervention"]
        result["accepted_automatically"] = automatic[0]["refs"] if automatic else []
        try:
            self._store.receipt(request_id, attempt, result)
        except StoreError:
            # The committed snapshot's applied ledger is authoritative after publication.
            result["receipt_pending"] = True
        return result

    def retry(self, request_id: str) -> dict:
        return self.consult(request_id)

    # The operator's decisions about proposals. Each is one local revision with no consultant
    # call. When a decision would take more than the operator named (what a proposal needs,
    # what needs it, what cannot stand without it), it returns "confirm" with the full list and
    # changes nothing until it is called again with confirmed=True. An undo always confirms.

    def accept(self, refs: List[str], speaker: str, base_revision: int, confirmed: bool = False) -> dict:
        return self._decide("accept", refs, speaker, base_revision, confirmed)

    def reject(self, refs: List[str], speaker: str, base_revision: int, confirmed: bool = False) -> dict:
        return self._decide("reject", refs, speaker, base_revision, confirmed)

    def undo(self, refs: List[str], speaker: str, base_revision: int, confirmed: bool = False) -> dict:
        return self._decide("undo", refs, speaker, base_revision, confirmed)

    def still_holds(self, ref: str, speaker: str, base_revision: int) -> dict:
        return self._decide("still_holds", [ref], speaker, base_revision, True)

    def set_acceptance(self, mode: str, speaker: str, base_revision: int) -> dict:
        """Choose how later replies' proposals enter the model: "review" or "automatic"."""
        return self._decide("acceptance", [], speaker, base_revision, True, mode)

    def _decide(self, action, refs, speaker, base_revision, confirmed, value=None):
        current = self._store.current()
        if type(base_revision) is not int or base_revision != current.revision:
            return {"status": "stale", "message": "The case has changed; look at the decision again",
                    "recovery_actions": ["review_again"]}
        if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
            return {"status": "rejected", "message": "Name the records as a list"}
        try:
            snapshot, decision = current.decide(action, refs, speaker, self._store.sources(),
                                                self._store.next_revision(), self._clock.now(), self._timezone, value)
        except InvalidCase as exc:
            return {"status": "rejected", "message": str(exc)[:300]}
        membership = current.membership()
        before = {(f["ref"], f["cites"]) for f in membership.flags()}
        flags = [f for f in snapshot.membership().flags() if (f["ref"], f["cites"]) not in before]
        leaves = membership.leaves_after(decision) if action in {"accept", "reject", "undo"} else []
        outcome = {"action": action, "refs": decision["refs"], "closes": decision["closes"], "leaves": leaves,
                   "flags": flags}
        takes_more = set(decision["refs"]) != set(refs) or decision["closes"] or leaves
        if not confirmed and (action == "undo" or action in {"accept", "reject"} and takes_more):
            return {"status": "confirm", **outcome,
                    "message": "Final; it cannot be undone" if action == "undo" else "This takes more than you chose"}
        try:
            self._store.commit(snapshot, current.revision)
        except StaleWork:
            return {"status": "stale", "message": "The case has changed; look at the decision again",
                    "recovery_actions": ["review_again"]}
        except StoreError:
            return {"status": "not_saved", "message": "not saved; nothing was changed",
                    "recovery_actions": ["choose_writable_export"]}
        return {"status": "saved", "revision": snapshot.revision, "decision": decision["id"], **outcome}

    def _failure(self, request_id, status, message, recovery, attempt=0, persist=True, detail=None):
        result = {"status": status, "request_id": request_id, "message": message,
                  "recovery_actions": recovery, "input_retained": True, **(detail or {})}
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
