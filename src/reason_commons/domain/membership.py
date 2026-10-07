"""What is in the model, what waits for a decision, and what needs review.

A case's records hold everything the consultant proposed. Membership is derived
from the snapshot's decisions: a proposal enters the model when it is accepted and
leaves it if that acceptance is undone. Records published before the case kept
decisions (``membership.proposals_from``) are in the model by definition.

Nothing here infers meaning. Order, readiness, closures and review flags follow
only the explicit references records make to each other.
"""

from copy import deepcopy

from reason_commons.domain.model import TREES, InvalidCase

# A record cannot stand without what it cites through these fields.
STRUCTURAL = ("from_ref", "to_ref", "replaces", "target_ref", "test_ref")
# A record cites these as reasoning it relies on; a change to them asks for review.
FLAGGED = ("from_ref", "to_ref", "claim_ref", "goal_ref", "test_ref", "observation_refs")
REFERENCE_FIELDS = ("goal_ref", "test_ref", "claim_ref", "from_ref", "to_ref", "replaces", "target_ref")
# Methodological order: a new goal first, then the trees in their usual order, then the loop.
TREE_STAGE = {tree: index + 1 for index, tree in enumerate(TREES)}
KIND_STAGE = {"goal": 0, "test": 7, "action": 8, "observation": 9, "review": 10, "note": 11}
STATUS_BY_ACTION = {"accept": "accepted", "reject": "rejected", "undo": "undone"}


def cited(record):
    """Every (field, ref) a record cites, in a stable order."""
    data = record["data"]
    pairs = [(field, data[field]) for field in REFERENCE_FIELDS if isinstance(data.get(field), str)]
    pairs += [("observation_refs", ref) for ref in data.get("observation_refs") or []]
    return pairs


def identity(ref):
    return ref.split("@")[0]


class Membership:
    """The membership of every non-intervention record in one snapshot value."""

    def __init__(self, value):
        self.value = value
        self.records = {r["ref"]: r for r in value["records"] if r["kind"] != "intervention"}
        self.index = {r["ref"]: i for i, r in enumerate(value["records"])}
        settings = value.get("membership")
        self.start = settings["proposals_from"] if settings else len(value["records"])
        self.acceptance = settings["acceptance"] if settings else "review"
        self.status = {ref: "accepted" if self.index[ref] < self.start else "proposed" for ref in self.records}
        self.decisions = []
        for decision in value.get("decisions", []):
            self.record(decision)

    def record(self, decision):
        self.decisions.append(decision)
        status = STATUS_BY_ACTION.get(decision["action"])
        for ref in decision.get("refs", []) if status else []:
            self.status[ref] = status
        for ref in decision.get("closes", []):
            self.status[ref] = "closed"

    # The model as it stands.

    def accepted(self, ref):
        return self.status.get(ref) == "accepted"

    def replacements(self):
        return {r["data"]["replaces"]: ref for ref, r in self.records.items()
                if self.accepted(ref) and r["kind"] in {"claim", "goal", "test"} and r["data"].get("replaces")}

    def withdrawn(self):
        return {r["data"]["target_ref"]: ref for ref, r in self.records.items()
                if self.accepted(ref) and r["kind"] == "retraction"}

    def latest(self, ref):
        replaced = self.replacements()
        while ref in replaced:
            ref = replaced[ref]
        return ref

    def current(self, ref):
        return self.accepted(ref) and ref not in self.replacements() and ref not in self.withdrawn()

    def model(self):
        """Refs in the model now: accepted, not replaced by a newer version, not withdrawn."""
        return [ref for ref in self.records if self.current(ref)]

    def drawn_link(self, ref):
        """A current link whose two statements are still in the model."""
        data = self.records[ref]["data"]
        withdrawn = self.withdrawn()
        ends = [self.latest(data["from_ref"]), self.latest(data["to_ref"])]
        return (self.current(ref) and all(self.accepted(e) and e not in withdrawn for e in ends)
                and ends[0] != ends[1])

    def goals(self, proposing=False):
        """Current goals in the model, and when proposing, goals still waiting too."""
        return [ref for ref, r in self.records.items() if r["kind"] == "goal" and (
            self.current(ref) or proposing and self.status[ref] == "proposed"
            and ref not in {o["data"].get("replaces") for o in self.records.values()
                            if o["kind"] == "goal" and self.status[o["ref"]] == "proposed"})]

    # Readiness.

    def requirement(self, ref, together=frozenset(), proposing=False):
        """None when ``ref`` can enter the model with ``together``; otherwise why not.

        Returns ("waits", [refs]) when it cites proposals still waiting, or
        ("blocked", reason) when it can never be accepted as things stand.
        When ``proposing``, a waiting prerequisite is no obstacle.
        """
        record, waits = self.records[ref], []
        withdrawn = self.withdrawn()
        for field, target in cited(record):
            if target in together or target not in self.records:
                continue
            status = self.status[target]
            if status == "proposed":
                waits.append(target)
                continue
            if status != "accepted":
                return "blocked", f"it relies on {target}, which was {status}"
            if field in {"replaces", "target_ref"} and not self.current(target):
                return "blocked", f"{target} has already been replaced or withdrawn"
            if field in {"from_ref", "to_ref", "claim_ref"} and self.latest(target) in withdrawn:
                return "blocked", f"{target} has been withdrawn"
            if field == "test_ref" and self.latest(target) != target:
                return "blocked", f"it cites {target}, an earlier version of the test; cite {self.latest(target)}"
        if record["kind"] == "test" and record["data"].get("replaces") in self.records:
            test = identity(record["data"]["replaces"])
            if any(r["kind"] == "observation" and self.current(o) and identity(r["data"]["test_ref"]) == test
                   for o, r in self.records.items()):
                return "blocked", (f"a result for {record['data']['replaces']} is already in the model, so its "
                                   "forecast stays as it was; a changed plan is a new test")
        if record["kind"] == "goal" and not record["data"].get("replaces"):
            others = [g for g in self.goals(proposing) if g != ref and g not in together]
            if others:
                return "blocked", (f"the case already has a goal ({others[-1]}); a different goal is a "
                                   "new version of it")
        if proposing or not waits:
            return None
        return "waits", waits

    def accept_closure(self, refs):
        """The proposals to accept together: ``refs`` and every waiting proposal they need."""
        chosen, queue = set(), list(refs)
        while queue:
            ref = queue.pop()
            if ref in chosen:
                continue
            if self.status.get(ref) != "proposed":
                raise InvalidCase(f"{ref} is not waiting for a decision")
            chosen.add(ref)
            queue += [t for _, t in cited(self.records[ref]) if self.status.get(t) == "proposed"]
        for ref in chosen:
            problem = self.requirement(ref, frozenset(chosen))
            if problem:
                raise InvalidCase(f"{ref} cannot be accepted: {problem[1]}")
        targets = [self.records[r]["data"].get("replaces") or (self.records[r]["data"].get("target_ref")
                   if self.records[r]["kind"] == "retraction" else None) for r in chosen]
        targets = [t for t in targets if t]
        if len(targets) != len(set(targets)):
            raise InvalidCase("Two of these proposals change the same record; accept one of them")
        return self.ordered(chosen)

    def dependents(self, refs, statuses, fields=None):
        """Records with one of ``statuses`` that cite ``refs``, transitively."""
        found, changed = set(refs), True
        while changed:
            changed = False
            for ref, record in self.records.items():
                if ref not in found and self.status[ref] in statuses and any(
                        target in found for field, target in cited(record) if fields is None or field in fields):
                    found.add(ref)
                    changed = True
        return found

    def reject_closure(self, refs):
        for ref in refs:
            if self.status.get(ref) != "proposed":
                raise InvalidCase(f"{ref} is not waiting for a decision")
        return self.ordered(self.dependents(refs, {"proposed"}))

    def undo_closure(self, refs):
        for ref in refs:
            if not self.accepted(ref):
                raise InvalidCase(f"{ref} is not in the model, so there is nothing to undo")
        return self.ordered(self.dependents(refs, {"accepted"}, STRUCTURAL))

    def closes_after(self, decision):
        """Waiting proposals that can never be accepted once ``decision`` is recorded."""
        after = Membership(self.value)
        after.record(decision)
        closed = []
        changed = True
        while changed:
            changed = False
            for ref in after.records:
                if after.status[ref] == "proposed":
                    problem = after.requirement(ref)
                    if problem and problem[0] == "blocked":
                        after.status[ref] = "closed"
                        closed.append(ref)
                        changed = True
        return self.ordered(closed)

    def leaves_after(self, decision):
        """Links in the trees now that ``decision`` takes out without naming them.

        Accepting a withdrawal takes its statement's links with it: they cannot be
        drawn without it. Records the decision names, and links it withdraws, are not
        listed again here.
        """
        after = Membership(self.value)
        after.record(decision)
        named = set(decision["refs"]) | {self.records[ref]["data"]["target_ref"] for ref in decision["refs"]
                                         if self.records[ref]["kind"] == "retraction"}
        return self.ordered([ref for ref, record in self.records.items() if record["kind"] == "link"
                             and ref not in named and self.drawn_link(ref) and not after.drawn_link(ref)])

    def ordered(self, refs):
        return sorted(refs, key=self.index.__getitem__)

    # Review flags.

    def flags(self):
        """Open review flags: a record in the model that cites a record which has since changed.

        Only explicit references raise a flag, and only changes made since the case kept
        decisions. A flag closes when the flagged record changes or leaves the model, or
        when the operator says it still holds against the record as it now stands.
        """
        replaced, withdrawn = self.replacements(), self.withdrawn()
        undone = {}
        for decision in self.decisions:
            if decision["action"] == "undo":
                undone.update({ref: decision["id"] for ref in decision["refs"]})
        affirmed = {}
        for decision in self.decisions:
            if decision["action"] == "still_holds":
                affirmed.setdefault(decision["refs"][0], set()).update(
                    (a["ref"], a["now"]) for a in decision["about"])
        flags = []
        for ref, record in self.records.items():
            if not self.current(ref) or record["kind"] == "link" and not self.drawn_link(ref):
                continue
            for field, target in cited(record):
                if field not in FLAGGED or target not in self.records or self.current(target):
                    continue
                if target in replaced:
                    by, change, now = replaced[target], "new_version", self.latest(target)
                    if now in withdrawn:
                        by, change, now = withdrawn[now], "withdrawn", None
                elif target in withdrawn:
                    by, change, now = withdrawn[target], "withdrawn", None
                elif target in undone:
                    by, change, now = undone[target], "undone", None
                else:
                    continue
                if by in self.index and self.index[by] < self.start:
                    continue  # changed before the case kept decisions
                if (target, now or "gone") in affirmed.get(ref, set()):
                    continue
                flags.append({"ref": ref, "cites": target, "field": field, "change": change, "by": by,
                              "now": now})
        return flags

    def stage(self, ref):
        record = self.records[ref]
        if record["kind"] in {"claim", "link"}:
            return TREE_STAGE[record["data"]["tree"]]
        if record["kind"] == "retraction":
            return self.stage(record["data"]["target_ref"])
        return KIND_STAGE[record["kind"]]

    def backlog(self):
        """Waiting proposals and open flags, in the order they are best decided.

        A proposal follows every waiting proposal it cites. Among entries that are free
        to go next, a new goal comes first, then the trees in method order, then tests,
        actions, observations, reviews and notes; older entries before newer ones.
        """
        entries = {}
        for ref, record in self.records.items():
            if self.status[ref] == "proposed":
                waits = [t for _, t in cited(record) if self.status.get(t) == "proposed"]
                entries[("proposal", ref)] = {
                    "entry": "proposal", "ref": ref, "record": deepcopy(record), "stage": self.stage(ref),
                    "waits_for": list(dict.fromkeys(waits)), "decide_first": record["kind"] == "goal",
                    "sequence": self.index[ref]}
        decision_position = {d["id"]: len(self.index) + n for n, d in enumerate(self.decisions)}
        for flag in self.flags():
            # One review per record, naming every change it was stated before.
            key = ("review", flag["ref"])
            sequence = self.index.get(flag["by"], decision_position.get(flag["by"], 0))
            if key in entries:
                entries[key]["flags"].append(flag)
                entries[key]["sequence"] = max(entries[key]["sequence"], sequence)
                continue
            entries[key] = {"entry": "review", "ref": flag["ref"], "record": deepcopy(self.records[flag["ref"]]),
                            "stage": self.stage(flag["ref"]), "waits_for": [], "decide_first": False,
                            "sequence": sequence, "flags": [flag]}
        placed, ordered = set(), []
        while len(ordered) < len(entries):
            ready = [key for key, e in entries.items() if key not in placed
                     and all(("proposal", w) in placed for w in e["waits_for"])]
            key = min(ready, key=lambda k: (entries[k]["stage"], entries[k]["sequence"], k))
            placed.add(key)
            ordered.append(entries[key])
        return ordered
