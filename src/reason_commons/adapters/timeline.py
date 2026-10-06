"""What each saved revision changed, read from the case's own history.

Display only: every entry is counted from records the engine saved, and the
words and speaker come from the retained input that produced the revision.
"""

from datetime import date, datetime
import re

from reason_commons.adapters.trees import TREE_TITLES

KIND_WORDS = {"goal": ("goal set", "goal set"), "test": ("test with a forecast", "tests with forecasts"),
              "action": ("action planned", "actions planned"), "observation": ("result reported", "results reported"),
              "review": ("review", "reviews"), "note": ("note", "notes"), "link": ("link", "links")}


def revision_changes(snapshots, sources):
    """One entry per revision, oldest first: when, who, what they wrote, and what changed."""
    entries, seen, previous = [], set(), None
    for snapshot in snapshots:
        records = snapshot["records"]
        new = [r for r in records if r["ref"] not in seen]
        seen.update(r["ref"] for r in records)
        request = snapshot["applied_requests"][-1] if snapshot["applied_requests"] else None
        source = sources.get(request, {}) if request else {}
        question = next((r for r in records if r["ref"] == snapshot["current_intervention"]), None)
        by_ref = {r["ref"]: r for r in records}
        counts, trees = {}, {}
        for record in new:
            kind = record["kind"]
            if kind == "claim":
                kind = "reworded" if record["data"].get("replaces") else "claim"
            elif kind == "retraction":
                kind = "withdrawn"
            elif kind == "intervention":
                continue
            counts[kind] = counts.get(kind, 0) + 1
            # The tree a change belongs to: its own, or for a withdrawal, the withdrawn record's.
            target = by_ref.get(record["data"].get("target_ref")) if kind == "withdrawn" else record
            tree = target["data"].get("tree") if target and target["kind"] in ("claim", "link") else None
            if tree:
                trees.setdefault(tree, {})
                trees[tree][kind] = trees[tree].get(kind, 0) + 1
        asked = next((r for r in (previous or {}).get("records", [])
                      if r["ref"] == (previous or {}).get("current_intervention")), None)
        previous = snapshot
        entries.append({
            "revision": snapshot["revision"], "timestamp": snapshot["timestamp"],
            "answered": (asked or {}).get("data", {}).get("decision"),
            "asked": (asked or {}).get("data", {}).get("primary_prompt"),
            "speaker": source.get("speaker"), "text": source.get("text"),
            "decision": (question or {}).get("data", {}).get("decision"),
            "fresh": {r["ref"] for r in new if r["kind"] == "claim"},
            "fresh_links": {r["ref"] for r in new if r["kind"] == "link"},
            # What was withdrawn, in the words it had: a statement's own, or a link's two ends.
            "withdrawn": [withdrawn_words(by_ref, r["data"]["target_ref"]) for r in new if r["kind"] == "retraction"],
            "counts": counts, "trees": trees})
    return entries


def withdrawn_words(records, ref):
    """A withdrawn record as words: a statement's own, or 'a link from … to …' for a link."""
    record = records.get(ref)
    if record is None:
        return ref
    if record["kind"] == "claim":
        return record["data"]["statement"]
    ends = [records.get(record["data"].get(side), {}).get("data", {}).get("statement", "?")
            for side in ("from_ref", "to_ref")]
    return f"the link from “{ends[0]}” to “{ends[1]}”"


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


def tree_summary(trees):
    """What one revision changed in the trees, tree by tree in their usual order:
    'Current Reality Tree: 2 statements added · 1 link'. A change to more than two
    trees (an import, say) is summed: '69 statements added · 61 links, in 6 trees'."""
    if len(trees) > 2:
        total = {}
        for counts in trees.values():
            for kind, number in counts.items():
                total[kind] = total.get(kind, 0) + number
        return f"{change_summary(total)}, in {len(trees)} trees"
    return "; ".join(f"{TREE_TITLES[tree][0]}: {change_summary(trees[tree])}" for tree in TREE_TITLES if tree in trees)


def day(timestamp):
    """'5 Jun 2026' from an ISO timestamp, or the text unchanged when it cannot be read."""
    try:
        value = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return str(timestamp)
    return f"{value.day} {value:%b %Y}"


def today():
    """Today's date on this computer; a function so that a test can fix it."""
    return date.today()


def stamp(timestamp, with_time):
    """A saved time as the person's own clock shows it: 'Oct 5' or 'Oct 5, 18:02'.

    The year appears only when it is not this year. Unlike ``day``, which keeps a stored date
    as it is (a story's dates are its own), this turns the stored time into local time, because
    it answers "when did I do this?". An unreadable value is returned unchanged.
    """
    try:
        # Python before 3.11 does not read a trailing Z, which other tools write for UTC.
        value = datetime.fromisoformat(re.sub(r"Z$", "+00:00", timestamp)).astimezone()
    except (TypeError, ValueError):
        return str(timestamp)
    text = f"{value:%b} {value.day}" + ("" if value.year == today().year else f", {value.year}")
    return text + (f", {value:%H:%M}" if with_time else "")


def short_day(timestamp):
    """'Oct 5': the day a goal was last changed."""
    return stamp(timestamp, with_time=False)


def moment(timestamp):
    """'Oct 3, 18:02': when someone wrote something."""
    return stamp(timestamp, with_time=True)


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
