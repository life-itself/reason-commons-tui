"""One local, append-only log of what each paid consultant request cost, kept outside every case.

The log holds token counts and estimates only: never a prompt, case text, a case's name, a path or
a key. It lives in ``$REASON_COMMONS_USAGE_LOG`` (a path, or ``off``), else
``$XDG_STATE_HOME/reason-commons/usage.jsonl``, else ``~/.local/state/reason-commons/usage.jsonl``,
readable only by you. Each line is one request, appended under a lock in a single write, so the
workspace, the command line and the MCP server can share it. Costs are estimates at list prices
(``pricing``); the Anthropic Console is the authority on what was billed.

The composition root hands a session's ``record`` to the consultant as its usage sink; the
application and the case never see it. A monthly budget is a notice for people, not a rule: nothing
here blocks a request.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import threading
import uuid

from reason_commons.adapters import pricing

VERSION = 1
LOG_VARIABLE = "REASON_COMMONS_USAGE_LOG"
BUDGET_VARIABLE = "REASON_COMMONS_MONTHLY_BUDGET_USD"
# What became of a request that reached Anthropic. no_reply: it was sent and no readable reply came
# back (a timeout, say), so it may still have been billed.
OUTCOMES = ("proposal", "max_tokens", "refusal", "no_proposal", "other_model", "no_reply")
ENTRY_POINTS = ("workspace", "accessible", "cli", "mcp", "check")
# Every key a line may hold. Nothing else is ever written.
KEYS = ("v", "at", "entry", "session", "case_id", "request_id", "provider", "model", "outcome", "tokens", "usd",
        "prices")
SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")


def log_path(environ=os.environ):
    """Where the log is, or None when ``REASON_COMMONS_USAGE_LOG`` is ``off``."""
    value = (environ.get(LOG_VARIABLE) or "").strip()
    if value.lower() == "off":
        return None
    if value:
        return Path(os.path.expanduser(value))
    state = environ.get("XDG_STATE_HOME") or ""
    base = Path(state) if os.path.isabs(state) else Path(os.path.expanduser("~/.local/state"))
    return base / "reason-commons" / "usage.jsonl"


def parse_budget(value):
    """Dollars a month from "5", "$5", "5.50" or a number; None for blank, none, 0 or anything unreadable."""
    if value is None or (isinstance(value, str) and value.strip().lower() in ("", "none", "off")):
        return None
    amount = pricing._amount(value)
    return amount if amount else None


def budget(environ=os.environ, saved=None):
    """The monthly budget and where it is set: (dollars or None, "environment", "settings" or None).

    ``REASON_COMMONS_MONTHLY_BUDGET_USD`` wins over the saved ``usage.monthly_budget_usd``; a blank
    variable counts as unset, and none or 0 in it means no budget."""
    raw = environ.get(BUDGET_VARIABLE)
    if raw is not None and raw.strip():
        return parse_budget(raw), "environment"
    amount = parse_budget(saved)
    return amount, "settings" if amount is not None else None


def crossed(before, after, limit):
    """80 or 100 when spending went from below that share of the budget to at or above it, else None."""
    if not limit:
        return None
    for share in (100, 80):
        line = limit * share / 100
        if before < line <= after:
            return share
    return None


def _safe(value):
    return value if isinstance(value, str) and SAFE.fullmatch(value) else None


def _count(value):
    return value if type(value) is int and value >= 0 else 0


def _parsed(value):
    """A log line as the summaries use it (times as datetimes, dollars as Decimals), or None if unreadable."""
    if not isinstance(value, dict) or value.get("v") != VERSION or not isinstance(value.get("tokens"), dict):
        return None
    try:
        at = datetime.strptime(value["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        usd = None if value.get("usd") is None else Decimal(value["usd"])
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return None
    if usd is not None and (not usd.is_finite() or usd < 0):
        return None
    tokens = {kind: _count(value["tokens"].get(kind)) for kind in pricing.TOKEN_KINDS}
    return {"at": at, "usd": usd, "tokens": tokens, "entry": _safe(value.get("entry")),
            "session": _safe(value.get("session")), "case_id": _safe(value.get("case_id")),
            "request_id": _safe(value.get("request_id")), "model": _safe(value.get("model")) or "unknown",
            "outcome": value.get("outcome") if value.get("outcome") in OUTCOMES else "no_proposal"}


def totals(entries):
    """Requests, estimated dollars and tokens, overall and by model. Requests with no known price are
    counted as unpriced; requests that got no reply are counted apart, as they may still be billed."""
    result = {"replies": 0, "usd": Decimal(0), "unpriced": 0, "no_reply": 0, "by_model": {}}
    for entry in entries:
        for bucket in (result, result["by_model"].setdefault(entry["model"], {
                "replies": 0, "usd": Decimal(0), "unpriced": 0, "no_reply": 0, "input": 0, "output": 0})):
            if entry["outcome"] == "no_reply":
                bucket["no_reply"] += 1
            else:
                bucket["replies"] += 1
            if entry["usd"] is None:
                bucket["unpriced"] += 1
            else:
                bucket["usd"] += entry["usd"]
        model = result["by_model"][entry["model"]]
        model["input"] += pricing.prompt_tokens(entry["tokens"])
        model["output"] += entry["tokens"]["output"]
    return result


class UsageLog:
    """The log file: appended to under a lock, read back with unreadable lines skipped and counted."""

    def __init__(self, path, now=None):
        self.path = Path(path) if path else None
        # The current time, aware; tests and screenshots fix it.
        self.now = now or (lambda: datetime.now(timezone.utc))
        self._cached = (None, [], 0)

    @classmethod
    def from_env(cls, environ=os.environ, now=None):
        return cls(log_path(environ), now)

    def append(self, line):
        """Add one entry: one locked write, starting on a fresh line even after a torn one. Raises OSError."""
        import fcntl
        data = (json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            size = os.fstat(descriptor).st_size
            if size == 0:
                os.fchmod(descriptor, 0o600)
            elif os.pread(descriptor, 1, size - 1) != b"\n":
                data = b"\n" + data  # a write cut short before: keep it apart from this one
            if os.write(descriptor, data) != len(data):
                raise OSError("usage log write was cut short")
        finally:
            os.close(descriptor)  # closing releases the lock

    def read(self):
        """(entries, lines skipped), cached until the file's size or modification time changes."""
        if self.path is None:
            return [], 0
        try:
            status = self.path.stat()
        except OSError:
            return [], 0
        stamp = (status.st_size, status.st_mtime_ns)
        if self._cached[0] == stamp:
            return list(self._cached[1]), self._cached[2]
        try:
            data = self.path.read_bytes()
        except OSError:
            return [], 0
        lines = data.split(b"\n")
        skipped = 1 if lines.pop().strip() else 0  # a last line with no newline is still being written, or torn
        entries = []
        for line in lines:
            if not line.strip():
                continue
            try:
                entry = _parsed(json.loads(line))
            except (ValueError, RecursionError):
                entry = None
            if entry is None:
                skipped += 1
            else:
                entries.append(entry)
        self._cached = (stamp, entries, skipped)
        return list(entries), skipped


class UsageSession:
    """What one run of an entry point (the workspace, a command, the MCP server) spent.

    ``record`` is the sink a consultant reports to. It prices the request, appends it to the log and
    keeps a copy; it never raises, so a broken log never loses a paid reply. A write error is kept in
    ``error`` and the entry is still counted for this session."""

    def __init__(self, log, entry, overrides=None, saved_budget=None, environ=os.environ):
        self.log, self.entry = log, entry
        self.id = uuid.uuid4().hex[:12]
        self.overrides = overrides if isinstance(overrides, dict) else {}
        self.saved_budget, self.environ = saved_budget, environ
        self.mine, self.unwritten, self.error = [], [], None
        self._lock = threading.Lock()

    def budget(self):
        """(dollars a month or None, where it is set)."""
        return budget(self.environ, self.saved_budget)

    def record(self, event):
        try:
            line = self._line(event)
            entry = _parsed(line)
        except Exception:  # an event this code cannot read is not worth losing a reply over
            return
        with self._lock:
            self.mine.append(entry)
            if self.log.path is None:
                return
            try:
                self.log.append(line)
            except Exception as exc:
                self.error = type(exc).__name__
                self.unwritten.append(entry)

    def _line(self, event):
        tokens = {kind: _count((event.get("tokens") or {}).get(kind)) for kind in pricing.TOKEN_KINDS}
        model = _safe(event.get("model")) or "unknown"
        card = pricing.rates(model, tokens, self.overrides)
        usd = pricing.cost(model, tokens, self.overrides)
        prices = None
        if card is not None:
            source = "settings" if model in self.overrides and pricing._override(self.overrides[model]) else "list"
            prices = {"source": source, "as_of": pricing.AS_OF, **{kind: str(card[kind]) for kind in card}}
        outcome = event.get("outcome")
        line = {"v": VERSION, "at": self.log.now().astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "entry": self.entry, "session": self.id, "case_id": _safe(event.get("case_id")),
                "request_id": _safe(event.get("request_id")), "provider": _safe(event.get("provider")) or "anthropic",
                "model": model, "outcome": outcome if outcome in OUTCOMES else "no_proposal", "tokens": tokens,
                "usd": None if usd is None else str(usd), "prices": prices}
        return line

    def mark(self):
        """A place in this session's records, to ask later what a send added."""
        with self._lock:
            return len(self.mine)

    def since(self, mark):
        with self._lock:
            return list(self.mine[mark:])

    def last_for(self, request_id):
        """This session's latest record for a request, or None."""
        with self._lock:
            return next((entry for entry in reversed(self.mine) if entry["request_id"] == request_id), None)

    def summary(self, case_id=None):
        """This session, the last reply, this goal (all time), today and this month (local time), by model."""
        now = self.log.now().astimezone()
        logged, skipped = self.log.read()
        with self._lock:
            mine, unwritten = list(self.mine), list(self.unwritten)
        everything = logged + unwritten
        local = [(entry, entry["at"].astimezone()) for entry in everything]
        amount, source = self.budget()
        return {"reply": mine[-1] if mine else None, "session": totals(mine),
                "goal": totals([e for e in everything if case_id and e["case_id"] == case_id]),
                "today": totals([e for e, at in local if at.date() == now.date()]),
                "month": totals([e for e, at in local if (at.year, at.month) == (now.year, now.month)]),
                "budget": amount, "budget_source": source, "skipped": skipped, "path": self.log.path,
                "logging": self.log.path is not None, "error": self.error}

    def typical(self, model, days=90, at_least=3):
        """A typical reply's estimated cost for a model: the mean of its replies with a proposal in the
        last ``days``, once there are ``at_least`` of them; otherwise None."""
        since = self.log.now() - timedelta(days=days)
        logged, _ = self.log.read()
        with self._lock:
            unwritten = list(self.unwritten)
        found = [e["usd"] for e in logged + unwritten
                 if e["model"] == model and e["outcome"] == "proposal" and e["usd"] is not None and e["at"] >= since]
        return sum(found, Decimal(0)) / len(found) if len(found) >= at_least else None
