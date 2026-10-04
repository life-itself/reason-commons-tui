"""What each saved revision changed, read from the case's own history.

Display only: every entry is counted from records the engine saved, and the
words and speaker come from the retained input that produced the revision.
"""

from datetime import datetime

KIND_WORDS = {"goal": ("goal set", "goal set"), "test": ("test with a forecast", "tests with forecasts"),
              "action": ("action planned", "actions planned"), "observation": ("result reported", "results reported"),
              "review": ("review", "reviews"), "note": ("note", "notes"), "link": ("link", "links")}


def revision_changes(snapshots, sources):
    """One entry per revision, oldest first: when, who, what they wrote, and what changed."""
    entries, seen = [], set()
    for snapshot in snapshots:
        records = snapshot["records"]
        new = [r for r in records if r["ref"] not in seen]
        seen.update(r["ref"] for r in records)
        request = snapshot["applied_requests"][-1] if snapshot["applied_requests"] else None
        source = sources.get(request, {}) if request else {}
        question = next((r for r in records if r["ref"] == snapshot["current_intervention"]), None)
        counts = {}
        for record in new:
            kind = record["kind"]
            if kind == "claim":
                kind = "reworded" if record["data"].get("replaces") else "claim"
            elif kind == "retraction":
                kind = "withdrawn"
            elif kind == "intervention":
                continue
            counts[kind] = counts.get(kind, 0) + 1
        entries.append({
            "revision": snapshot["revision"], "timestamp": snapshot["timestamp"],
            "speaker": source.get("speaker"), "text": source.get("text"),
            "decision": (question or {}).get("data", {}).get("decision"),
            "fresh": {r["ref"] for r in new if r["kind"] == "claim"},
            "counts": counts})
    return entries


def change_summary(counts):
    """A short line such as '9 statements · 8 links · goal set'."""
    parts = []
    for kind, (one, many) in [("claim", ("statement added", "statements added")),
                              ("reworded", ("statement reworded", "statements reworded")),
                              ("withdrawn", ("withdrawn", "withdrawn"))] + list(KIND_WORDS.items()):
        number = counts.get(kind)
        if number:
            parts.append(f"{number} {one if number == 1 else many}" if kind != "goal" else one)
    return " · ".join(parts) or "no recorded change"


def day(timestamp):
    """'5 Jun 2026' from an ISO timestamp, or the text unchanged when it cannot be read."""
    try:
        value = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return str(timestamp)
    return f"{value.day} {value:%b %Y}"


def next_action(records):
    """The open action: planned or blocked, its test not yet observed. The latest one wins."""
    by_ref = {r["ref"]: r for r in records}
    observed = {r["data"]["test_ref"] for r in records if r["kind"] == "observation"}
    open_actions = [r for r in records if r["kind"] == "action" and r["data"].get("test_ref") not in observed
                    and r["data"].get("execution") in (None, "unknown", "planned", "blocked")]
    if not open_actions:
        return None
    action = open_actions[-1]
    test = by_ref.get(action["data"].get("test_ref"))
    claim = by_ref.get((test or {}).get("data", {}).get("claim_ref"))
    return {"action": action, "test": test, "claim": claim}
