"""The case aggregate and the explicit v1 record/proposal contract.

A consultant reply publishes its next question and adds its updates as proposals;
the operator's decisions (``decide``) put proposals into the model. Membership,
readiness, order and review flags are derived in ``membership``.
"""

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Dict, Mapping, Sequence


class InvalidCase(ValueError):
    pass


class StaleWork(InvalidCase):
    pass


SCHEMA = "1"
PROFILE = "p2"  # v1 data contract; delivery milestone remains p0
PREFIXES = {"goal": "G", "note": "N", "test": "P", "action": "A",
            "observation": "B", "review": "R", "intervention": "I",
            "claim": "C", "link": "L", "retraction": "X"}
# A small closed registry: generic notes cannot smuggle executable graph fields.
FIELDS = {
    # A goal is the Goal Tree's top statement; a case has one, and changes it by new versions.
    "goal": {"statement", "scope", "horizon", "measure", "baseline", "protections", "replaces"},
    "note": {"text", "basis"},
    "test": {"statement", "goal_ref", "scope", "forecast", "stop_condition", "review_date", "claim_ref"},
    "action": {"statement", "test_ref", "owner", "authority", "execution", "expected_state_attainment"},
    "observation": {"test_ref", "measure", "value", "scope", "denominator", "period", "basis"},
    "review": {"test_ref", "observation_refs", "assessment", "next_decision", "goal_ref"},
    # Thinking-process trees, in the LTP 1.0 vocabulary. A claim is one sourced
    # proposition placed in a tree; a link is one explicit, typed relation between
    # two claims of the same tree; a retraction withdraws either without rewriting it.
    "claim": {"tree", "role", "statement", "basis", "replaces"},
    "link": {"tree", "relation", "from_ref", "to_ref", "assumption"},
    "retraction": {"target_ref", "reason"},
}
REQUIRED = {"goal": {"statement"}, "note": {"text"},
            "test": {"statement", "goal_ref", "scope", "forecast"},
            "action": {"statement", "test_ref"},
            "observation": {"test_ref", "measure", "value"},
            "review": {"test_ref", "assessment"},
            "claim": {"tree", "role", "statement"},
            "link": {"tree", "relation", "from_ref", "to_ref"},
            "retraction": {"target_ref", "reason"}}
REQUIRED_REFERENCES = {"test": {"goal_ref"}, "action": {"test_ref"},
                       "observation": {"test_ref"}, "review": {"test_ref"},
                       "link": {"from_ref", "to_ref"}, "retraction": {"target_ref"}}
# Fields that cite another record, and the kinds each may cite.
REFERENCE_KINDS = {"goal_ref": {"goal"}, "test_ref": {"test"}, "claim_ref": {"claim"},
                   "from_ref": {"claim", "goal"}, "to_ref": {"claim", "goal"}, "replaces": {"claim", "goal"},
                   "target_ref": {"claim", "link"}}
TREES = ("goal", "current_reality", "conflict", "future_reality", "prerequisite", "transition")
ALL_TREES = set(TREES)
# Which trees each role belongs to (reasoncommons skills/ltp-project/references/vocabulary.md).
ROLES = {"goal": {"goal"}, "critical_success_factor": {"goal"}, "necessary_condition": {"goal"},
         "undesirable_effect": {"current_reality", "future_reality"},
         "intermediate_cause": {"current_reality"}, "root_cause": {"current_reality"},
         "critical_root_cause": {"current_reality"}, "cloud_objective": {"conflict"},
         "cloud_requirement": {"conflict"}, "cloud_prerequisite": {"conflict"},
         "injection": {"conflict", "future_reality"}, "desired_effect": {"future_reality"},
         "implementation_objective": {"prerequisite"}, "obstacle": {"prerequisite"},
         "intermediate_objective": {"prerequisite"}, "transition_existing_reality": {"transition"},
         "transition_need": {"transition"}, "transition_action": {"transition"},
         "transition_expected_effect": {"transition"}, "observation": ALL_TREES, "evidence": ALL_TREES}
RELATIONS = {"necessary_for", "causes", "contributes_to", "conflicts_with", "requires", "satisfies",
             "overcomes", "precedes", "produces", "invalidates_assumption", "implements", "supersedes",
             "supports", "challenges", "refines", "enables"}
# A record needs its defining text and relationships. Scope and supplementary
# context can explicitly remain unknown; an unformed claim belongs in a note.
REQUIRED_TEXT = {kind: fields - {"scope", "forecast"} for kind, fields in REQUIRED.items()}
INTERVENTION_FIELDS = {"kind", "goal_ref", "purpose", "decision", "primary_prompt",
                       "rationale", "required_context_refs", "options"}
INTERVENTION_REQUIRED = {"kind", "purpose", "primary_prompt", "rationale"}
INTERVENTION_KINDS = {"question", "recommendation", "stop"}
FORECAST_FIELDS = {"measure", "expected", "scope", "denominator", "period", "bound"}
FORECAST_REQUIRED = {"measure", "expected", "scope", "denominator"}
ENUM_FIELDS = {"basis": {"hypothesis", "participant_report", "observed"},
               "tree": ALL_TREES, "role": set(ROLES), "relation": RELATIONS,
               "execution": {"unknown", "planned", "completed", "blocked"},
               "expected_state_attainment": {"unknown", "pending", "met", "not_met"}}
VIEW_TARGETS = {"goal", "history", "sources", "current_question", "trees"}
CONSULT_INTENTS = {"another_question", "direct_advice", "explain_observation", "review_flags"}
# How a case admits proposals: held for the operator's review (the default), or accepted
# automatically under the operator's own setting.
ACCEPTANCE = {"review", "automatic"}
DECISION_ACTIONS = {"accept", "reject", "undo", "still_holds", "acceptance"}
DECISION_FIELDS = {"id", "action", "refs", "closes", "mode", "actor", "timestamp", "value", "about", "request_id"}
UPDATE_FIELDS = {"operation", "temporary_id", "data", "source_refs", "confidence"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidCase(message)


def shape(value: Any, allowed: set, required: set, label: str) -> None:
    require(isinstance(value, dict), f"{label} must be an object")
    require(set(value) <= allowed, f"Unsupported {label} fields: {set(value) - allowed}")
    require(required <= set(value), f"Missing {label} fields: {required - set(value)}")


def text(value: Any, label: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")


def string_list(value: Any, label: str) -> None:
    require(isinstance(value, list) and all(isinstance(v, str) for v in value),
            f"{label} must be a list of text")


def validate_value(kind: str, data: dict) -> None:
    shape(data, FIELDS[kind], REQUIRED[kind], kind)
    for field in REQUIRED_TEXT[kind]:
        text(data[field], field)
    for key, value in data.items():
        if key == "forecast":
            require(isinstance(value, list) and bool(value), "A test needs a prospective forecast")
            for measure in value:
                shape(measure, FORECAST_FIELDS, FORECAST_REQUIRED, "forecast measure")
                for field, content in measure.items():
                    if content is not None:
                        text(content, field)
        elif key in {"protections", "observation_refs"}:
            string_list(value, key)
        elif value is not None:
            text(value, key)
    for field, values in ENUM_FIELDS.items():
        if field in data:
            require(data[field] in values, f"Unknown {field}")
    if kind == "claim":
        require(data["tree"] in ROLES[data["role"]], f"Role {data['role']} does not belong in the {data['tree']} tree")


def validate_intervention(data: dict, records: Mapping[str, dict]) -> None:
    shape(data, INTERVENTION_FIELDS, INTERVENTION_REQUIRED, "intervention")
    require(data["kind"] in INTERVENTION_KINDS, "Unknown intervention kind")
    for key in ("purpose", "primary_prompt", "rationale"):
        text(data[key], key)
    if "decision" in data:
        text(data["decision"], "decision")
    if data.get("goal_ref") is not None:
        reference(data["goal_ref"], records, "goal")
    refs = data.get("required_context_refs", [])
    string_list(refs, "required_context_refs")
    for ref in refs:
        reference(ref, records)
    options = data.get("options", [])
    require(isinstance(options, list), "Options must be a list")
    ids = set()
    for option in options:
        shape(option, {"id", "label", "action"}, {"id", "label", "action"}, "option")
        text(option["id"], "option id")
        require(option["id"] not in ids, "Duplicate option")
        ids.add(option["id"])
        text(option["label"], "option label")
        action = option["action"]
        require(isinstance(action, dict), "Action must be an object")
        if action.get("type") == "view":
            shape(action, {"type", "target"}, {"type", "target"}, "view action")
            target = action["target"]
            require(isinstance(target, str), "View target must be text")
            if target.startswith("test:"):
                reference(target[5:], records, "test")
            else:
                require(target in VIEW_TARGETS, "View belongs to an unavailable delivery profile")
        else:
            shape(action, {"type", "intent"}, {"type", "intent"}, "consult action")
            require(action["type"] == "consult" and action["intent"] in CONSULT_INTENTS,
                    "Action belongs to an unavailable delivery profile")


def tree_of(record: dict):
    """The tree a statement belongs to; the goal is the Goal Tree's top statement."""
    return "goal" if record["kind"] == "goal" else record["data"].get("tree")


def validate_tree_record(record: dict, records: Mapping[str, dict], earlier: set,
                         withdrawn: set, replaced: set) -> None:
    """Records published before the case kept decisions: they cite only earlier, current claims."""
    data, kind = record["data"], record["kind"]
    current = lambda ref: ref in earlier and ref not in withdrawn and ref not in replaced
    if kind == "claim" and data.get("replaces") is not None:
        old = data["replaces"]
        require(current(old), "A claim can only replace an earlier, current claim")
        require(records[old]["data"]["tree"] == data["tree"], "A replacement stays in the same tree")
        replaced.add(old)
    elif kind == "link":
        for key in ("from_ref", "to_ref"):
            require(current(data[key]), "A link joins earlier, current claims")
            require(records[data[key]]["kind"] == "claim" and records[data[key]]["data"]["tree"] == data["tree"],
                    "A link joins claims of its own tree")
        require(data["from_ref"] != data["to_ref"], "A claim cannot be linked to itself")
    elif kind == "retraction":
        require(current(data["target_ref"]), "Only an earlier, current claim or link can be withdrawn")
        withdrawn.add(data["target_ref"])
    elif kind == "test" and data.get("claim_ref") is not None:
        require(current(data["claim_ref"]), "A test can only carry out an earlier, current claim")


def validate_proposed_record(record: dict, records: Mapping[str, dict], earlier: set) -> None:
    """The grammar of a proposal, whatever its membership: it cites only earlier records."""
    data, kind = record["data"], record["kind"]
    for key, target in [(k, data.get(k)) for k in REFERENCE_KINDS] + [
            ("observation_refs", r) for r in data.get("observation_refs") or []]:
        if isinstance(target, str):
            require(target in earlier, f"{record['ref']} cites {target}, which is not an earlier record")
    if kind == "claim":
        require(data["role"] != "goal", "The case's goal is the Goal Tree's top statement; propose a goal, "
                                        "not a statement in the goal role")
    if data.get("replaces") is not None:
        old = records[data["replaces"]]
        require(old["kind"] == kind, "A new version replaces a record of its own kind")
        require(kind != "claim" or old["data"]["tree"] == data["tree"], "A replacement stays in the same tree")
    if kind == "link":
        ends = [records[data["from_ref"]], records[data["to_ref"]]]
        require(data["tree"] in {tree_of(end) for end in ends},
                "A link belongs to the tree of at least one of the statements it joins")
        require(len({end["ref"].split("@")[0] for end in ends}) == 2, "A statement cannot be linked to itself")



def reference(ref: str, records: Mapping[str, dict], kind: str = None) -> None:
    require(isinstance(ref, str) and ref in records, f"Unknown reference: {ref}")
    require(kind is None or records[ref]["kind"] == kind, f"Wrong reference kind: {ref}")


def validate_input(value: dict) -> None:
    shape(value, {"schema_version", "request_id", "base_revision", "response_target", "text",
                  "speaker", "intent", "declarations", "timestamp", "timezone"},
          {"schema_version", "request_id", "base_revision", "response_target", "text", "speaker",
           "intent", "declarations", "timestamp", "timezone"}, "input")
    require(value["schema_version"] == SCHEMA, "Unsupported input schema")
    require(bool(re.fullmatch(r"in\d{3,}", value["request_id"])), "Invalid request ID")
    require(type(value["base_revision"]) is int and value["base_revision"] >= 0, "Invalid input revision")
    require(value["response_target"] is None or isinstance(value["response_target"], str), "Invalid target")
    require(isinstance(value["text"], str), "Input text must be literal text")
    text(value["speaker"], "speaker")
    require(value["intent"] in {"answer"} | CONSULT_INTENTS, "Unavailable intent")
    shape(value["declarations"], {"ownership", "evidence"}, set(), "explicit declarations")
    for key, items in value["declarations"].items():
        string_list(items, key)
    for key in ("timestamp", "timezone"):
        text(value[key], key)


@dataclass(frozen=True)
class Snapshot:
    """One whole case revision; callers receive copies via to_dict."""

    value: Dict[str, Any]

    @property
    def revision(self) -> int:
        return self.value["revision"]

    @property
    def target(self):
        return self.value["current_intervention"]

    def to_dict(self) -> dict:
        return deepcopy(self.value)

    def membership(self):
        from reason_commons.domain.membership import Membership
        return Membership(self.value)

    @classmethod
    def initial(cls, case_id: str, name: str, timestamp: str, timezone: str,
                acceptance: str = "review", actor: str = None):
        """An empty case. Holding proposals for review is the default; whoever creates a case
        may choose automatic acceptance instead, and that choice is recorded as its first decision."""
        text(name, "case name")
        require(acceptance in ACCEPTANCE, "Choose review or automatic acceptance")
        decisions = []
        if acceptance != "review":
            text(actor, "who chose automatic acceptance")
            decisions.append({"id": "D1", "action": "acceptance", "refs": [], "closes": [], "mode": "explicit",
                              "actor": actor, "timestamp": timestamp, "value": acceptance})
        return cls({"schema_version": SCHEMA, "delivery_profile": PROFILE, "case_id": case_id,
                    "name": name, "revision": 0, "parent": None, "timestamp": timestamp,
                    "timezone": timezone, "records": [], "current_intervention": None,
                    "applied_requests": [], "source_input_refs": [], "counters": {},
                    "adapter_versions": {}, "membership": {"proposals_from": 0, "acceptance": acceptance},
                    "decisions": decisions})

    def validate(self, sources: Mapping[str, dict]) -> None:
        keys = {"schema_version", "delivery_profile", "case_id", "name", "revision", "parent", "timestamp",
                "timezone", "records", "current_intervention", "applied_requests", "source_input_refs",
                "counters", "adapter_versions"}
        # A case recorded before decisions existed has neither field; everything in it is in the model.
        shape(self.value, keys | {"membership", "decisions"},
              keys | ({"membership", "decisions"} if "membership" in self.value or "decisions" in self.value
                      else set()), "snapshot")
        require(self.value["schema_version"] == SCHEMA and self.value["delivery_profile"] == PROFILE,
                "Unsupported schema or delivery profile")
        require(type(self.revision) is int and self.revision >= 0, "Invalid revision")
        require(self.value["parent"] is None if self.revision == 0 else
                type(self.value["parent"]) is int and 0 <= self.value["parent"] < self.revision, "Invalid parent")
        for key in ("case_id", "name", "timestamp", "timezone"):
            text(self.value[key], key)
        counters = self.value["counters"]
        require(isinstance(counters, dict) and set(counters) <= set(PREFIXES) and
                all(type(v) is int and v >= 0 for v in counters.values()), "Invalid counters")
        require(isinstance(self.value["adapter_versions"], dict) and
                all(isinstance(k, str) and isinstance(v, str) for k, v in self.value["adapter_versions"].items()),
                "Invalid adapter metadata")
        require(isinstance(self.value["records"], list), "Records must be a list")
        start = len(self.value["records"])
        if "membership" in self.value:
            settings = self.value["membership"]
            shape(settings, {"proposals_from", "acceptance"}, {"proposals_from", "acceptance"}, "membership")
            start = settings["proposals_from"]
            require(type(start) is int and 0 <= start <= len(self.value["records"]), "Invalid proposal boundary")
            require(settings["acceptance"] in ACCEPTANCE, "Unknown acceptance setting")
        records = {}
        for position, record in enumerate(self.value["records"]):
            shape(record, {"ref", "kind", "data", "source_refs", "confidence"},
                  {"ref", "kind", "data", "source_refs"}, "record")
            if "confidence" in record:
                require(position >= start and record["kind"] != "intervention" and
                        type(record["confidence"]) in {int, float} and 0 <= record["confidence"] <= 1,
                        "Confidence is a number from 0 to 1 on a proposal")
            kind, ref = record["kind"], record["ref"]
            require(kind in PREFIXES, "Unavailable record kind")
            match = isinstance(ref, str) and re.fullmatch(PREFIXES[kind] + r"([1-9]\d*)@([1-9]\d*)", ref)
            require(bool(match), "Invalid record ID")
            require(ref not in records, "Duplicate record ID")
            require(int(match[1]) <= counters.get(kind, 0), "ID exceeds allocation ledger")
            if int(match[2]) > 1:
                old = record["data"].get("replaces") if isinstance(record["data"], dict) else None
                require(isinstance(old, str) and old.split("@")[0] == ref.split("@")[0],
                        "A later version replaces an earlier version of the same record")
            string_list(record["source_refs"], "source_refs")
            require(bool(record["source_refs"]) and all(s in sources for s in record["source_refs"]), "Unknown source")
            records[ref] = record
        withdrawn, replaced, earlier = set(), set(), set()
        for position, record in enumerate(self.value["records"]):
            if record["kind"] == "intervention":
                validate_intervention(record["data"], records)
            else:
                validate_value(record["kind"], record["data"])
                for key, kinds in REFERENCE_KINDS.items():
                    if record["data"].get(key) is not None:
                        reference(record["data"][key], records)
                        require(records[record["data"][key]]["kind"] in kinds, f"Wrong reference kind: {key}")
                if position < start:
                    validate_tree_record(record, records, earlier, withdrawn, replaced)
                else:
                    validate_proposed_record(record, records, earlier)
                for ref in record["data"].get("observation_refs", []):
                    reference(ref, records, "observation")
                owner = record["data"].get("owner")
                if owner is not None:
                    require(any(owner in sources[s].get("declarations", {}).get("ownership", [])
                                for s in record["source_refs"]), "Ownership requires cited explicit input")
                if record["data"].get("basis") == "observed":
                    require(any("observed" in sources[s].get("declarations", {}).get("evidence", [])
                                for s in record["source_refs"]), "Observed support requires cited explicit evidence")
            earlier.add(record["ref"])
        if self.target is not None:
            reference(self.target, records, "intervention")
        for field in ("applied_requests", "source_input_refs"):
            string_list(self.value[field], field)
            require(len(set(self.value[field])) == len(self.value[field]), "Duplicate request/source")
            require(all(s in sources and "request_id" in sources[s] for s in self.value[field]), "Missing retained input")
        require(set(self.value["applied_requests"]) == set(self.value["source_input_refs"]), "Incomplete request ledger")
        if "membership" in self.value:
            self._validate_decisions()

    def _validate_decisions(self):
        """Replay the operator's decisions; each must have been possible when it was made."""
        from reason_commons.domain.membership import Membership
        decisions = self.value["decisions"]
        require(isinstance(decisions, list), "Decisions must be a list")
        replay = Membership({**self.value, "decisions": []})
        acceptance = "review"
        for number, decision in enumerate(decisions, 1):
            shape(decision, DECISION_FIELDS, {"id", "action", "refs", "closes", "mode", "actor", "timestamp"},
                  "decision")
            require(decision["id"] == f"D{number}", "Decisions are numbered in order")
            action, refs = decision["action"], decision["refs"]
            require(action in DECISION_ACTIONS, "Unknown decision")
            require(decision["mode"] in {"explicit", "automatic"} and
                    (decision["mode"] == "explicit" or action == "accept"), "Only acceptance can be automatic")
            require(decision["mode"] == "explicit" or decision.get("request_id") in self.value["applied_requests"],
                    "An automatic acceptance belongs to the reply it came with")
            text(decision["actor"], "decision actor")
            text(decision["timestamp"], "decision timestamp")
            string_list(refs, "decision refs")
            string_list(decision["closes"], "closed proposals")
            require(all(r in replay.records for r in refs + decision["closes"]), "A decision names unknown records")
            require(len(set(refs)) == len(refs), "A decision names a record twice")
            if action == "accept":
                require(bool(refs) and all(replay.status[r] == "proposed" for r in refs),
                        "Only waiting proposals can be accepted")
                for ref in refs:
                    require(replay.requirement(ref, frozenset(refs)) is None, f"{ref} was not ready to accept")
            elif action == "reject":
                require(bool(refs) and set(replay.reject_closure(refs)) == set(refs),
                        "A rejection takes every waiting proposal that needs it")
            elif action == "undo":
                require(bool(refs) and set(replay.undo_closure(refs)) == set(refs),
                        "An undo takes everything that cannot stand without it")
            elif action == "still_holds":
                require(len(refs) == 1 and replay.current(refs[0]), "Still holds names one record in the model")
                about = decision.get("about")
                require(isinstance(about, list) and bool(about) and all(
                    isinstance(a, dict) and set(a) == {"ref", "now"} for a in about), "Still holds names its flags")
            else:
                require(refs == [] and decision.get("value") in ACCEPTANCE, "Invalid acceptance setting")
                acceptance = decision["value"]
            require(all(replay.status[r] == "proposed" for r in decision["closes"]),
                    "Only waiting proposals can be closed")
            replay.record(decision)
        require(self.value["membership"]["acceptance"] == acceptance, "Acceptance setting differs from decisions")

    def _successor(self, revision, timestamp, timezone):
        result = self.to_dict()
        # The first revision under decisions marks where proposals begin; what came before is in the model.
        result.setdefault("membership", {"proposals_from": len(result["records"]), "acceptance": "review"})
        result.setdefault("decisions", [])
        result.update(revision=revision, parent=self.revision, timestamp=timestamp, timezone=timezone)
        return result

    def apply(self, proposal: dict, input_record: dict, sources: Mapping[str, dict],
              revision: int, timestamp: str, timezone: str, adapter_version: str,
              reserved: Mapping[str, int] = None):
        """Publish a reply: its next question, and its updates as proposals.

        Under automatic acceptance, the proposals that are ready enter the model in this
        same revision, recorded as accepted under the operator's setting.
        """
        validate_input(input_record)
        # Decisions recorded since the input was written do not make the reply stale;
        # only a newer consultant question does.
        if input_record["response_target"] != self.target or input_record["base_revision"] > self.revision:
            raise StaleWork("Response is stale; re-evaluate against the current revision")
        shape(proposal, {"schema_version", "delivery_profile", "request_id", "base_revision", "intervention",
                         "proposed_updates"}, {"schema_version", "delivery_profile", "request_id", "base_revision",
                                               "intervention", "proposed_updates"}, "proposal")
        require(proposal["schema_version"] == SCHEMA and proposal["delivery_profile"] == PROFILE,
                "Proposal belongs to an unsupported schema or delivery profile")
        require(proposal["request_id"] == input_record["request_id"] and
                type(proposal["base_revision"]) is int and proposal["base_revision"] == input_record["base_revision"],
                "Proposal request or revision mismatch")
        require(input_record["request_id"] not in self.value["applied_requests"], "Request already applied")
        result = self._successor(revision, timestamp, timezone)
        counters = result["counters"]
        for kind, number in (reserved or {}).items():
            counters[kind] = max(counters.get(kind, 0), number)
        kinds = {r["ref"]: r["kind"] for r in result["records"]}

        def allocate(kind, replaces=None):
            if replaces is not None and kinds.get(replaces) == kind:
                # A new version keeps the record's identity: C3@1 becomes C3@2.
                name = replaces.split("@")[0]
                versions = [int(ref.split("@")[1]) for ref in kinds if ref.split("@")[0] == name]
                return f"{name}@{max(versions) + 1}"
            counters[kind] = counters.get(kind, 0) + 1
            return f"{PREFIXES[kind]}{counters[kind]}@1"

        updates = proposal["proposed_updates"]
        require(isinstance(updates, list), "Updates must be a list")
        temporary = {}
        new_records = []
        for update in updates:
            shape(update, UPDATE_FIELDS, {"operation", "data", "source_refs"}, "update")
            operation = update["operation"]
            require(isinstance(operation, str) and operation.startswith("record_"), "Unknown operation")
            kind = operation[7:]
            require(kind in FIELDS, "Update belongs to a later delivery profile")
            if "confidence" in update:
                require(type(update["confidence"]) in {int, float} and 0 <= update["confidence"] <= 1,
                        "Confidence is a number from 0 to 1")
            replaces = update["data"].get("replaces") if isinstance(update["data"], dict) else None
            ref = allocate(kind, temporary.get(replaces, replaces) if isinstance(replaces, str) else None)
            kinds[ref] = kind
            if "temporary_id" in update:
                temp = update["temporary_id"]
                text(temp, "temporary_id")
                require(temp not in temporary and temp not in {r["ref"] for r in result["records"]}, "Duplicate temporary ID")
                temporary[temp] = ref
            new_records.append({"ref": ref, "kind": kind, "data": deepcopy(update["data"]),
                                "source_refs": deepcopy(update["source_refs"])})
            if "confidence" in update:
                # Kept with the proposal; it decides nothing.
                new_records[-1]["confidence"] = update["confidence"]

        def resolve_data(data):
            require(isinstance(data, dict), "Record data must be an object")
            for key in REFERENCE_KINDS:
                if isinstance(data.get(key), str):
                    data[key] = temporary.get(data[key], data[key])
            for key in ("observation_refs", "required_context_refs"):
                if key in data:
                    string_list(data[key], key)
                    data[key] = [temporary.get(r, r) for r in data[key]]

        for record in new_records:
            resolve_data(record["data"])
        intervention = deepcopy(proposal["intervention"])
        resolve_data(intervention)
        for option in intervention.get("options", []):
            if isinstance(option, dict) and isinstance(option.get("action"), dict):
                target = option["action"].get("target")
                if isinstance(target, str) and target.startswith("test:"):
                    option["action"]["target"] = "test:" + temporary.get(target[5:], target[5:])
        target = allocate("intervention")
        result["records"].extend(new_records)
        result["records"].append({"ref": target, "kind": "intervention", "data": intervention,
                                  "source_refs": [input_record["request_id"]]})
        result.update(current_intervention=target)
        result["applied_requests"].append(input_record["request_id"])
        result["source_input_refs"].append(input_record["request_id"])
        result["adapter_versions"][input_record["request_id"]] = adapter_version
        # Structure first, then whether each proposal could ever be accepted as things stand.
        Snapshot(result).validate(sources)
        membership = Snapshot(result).membership()
        new = [r["ref"] for r in new_records]
        for ref in new:
            problem = membership.requirement(ref, frozenset(new), proposing=True)
            require(problem is None, f"{ref} cannot be proposed: {problem[1] if problem else ''}")
        if result["membership"]["acceptance"] == "automatic" and new:
            accepted = []
            for ref in new:
                if membership.requirement(ref, frozenset(accepted)) is None:
                    accepted.append(ref)
            changed = [membership.records[r]["data"].get("replaces") or (
                membership.records[r]["data"]["target_ref"] if membership.records[r]["kind"] == "retraction" else None)
                for r in accepted]
            changed = [c for c in changed if c]
            if accepted and len(changed) == len(set(changed)):
                decision = {"id": f"D{len(result['decisions']) + 1}", "action": "accept", "refs": accepted,
                            "closes": [], "mode": "automatic", "actor": input_record["speaker"],
                            "timestamp": timestamp, "request_id": input_record["request_id"]}
                decision["closes"] = membership.closes_after(decision)
                result["decisions"].append(decision)
        snapshot = Snapshot(result)
        snapshot.validate(sources)
        return snapshot

    def decide(self, action: str, refs: Sequence[str], actor: str, sources: Mapping[str, dict],
               revision: int, timestamp: str, timezone: str, value: str = None):
        """Record one decision of the operator's as a new revision; no consultant is involved.

        ``refs`` names what the operator chose. Acceptance also takes the waiting
        proposals they need, rejection those that need them, and undo whatever cannot
        stand without them; the returned decision lists everything it took.
        """
        membership = self.membership()
        refs = list(refs)
        text(actor, "actor")
        decision = {"id": f"D{len(self.value.get('decisions', [])) + 1}", "action": action, "closes": [],
                    "mode": "explicit", "actor": actor, "timestamp": timestamp}
        if action == "accept":
            decision["refs"] = membership.accept_closure(refs)
        elif action == "reject":
            decision["refs"] = membership.reject_closure(refs)
        elif action == "undo":
            decision["refs"] = membership.undo_closure(refs)
        elif action == "still_holds":
            require(len(refs) == 1, "Say which one record still holds")
            flags = [f for f in membership.flags() if f["ref"] == refs[0]]
            require(bool(flags), f"{refs[0]} has no open review")
            decision.update(refs=refs, about=[{"ref": f["cites"], "now": f["now"] or "gone"} for f in flags])
        elif action == "acceptance":
            require(value in ACCEPTANCE, "Choose review or automatic acceptance")
            require(value != membership.acceptance, f"The case already uses {value} acceptance")
            decision.update(refs=[], value=value)
        else:
            raise InvalidCase("Unknown decision")
        if action in {"accept", "reject", "undo"}:
            decision["closes"] = membership.closes_after(decision)
        result = self._successor(revision, timestamp, timezone)
        result["decisions"].append(decision)
        if action == "acceptance":
            result["membership"]["acceptance"] = value
        snapshot = Snapshot(result)
        snapshot.validate(sources)
        return snapshot, deepcopy(decision)


def validate_ancestry(history: Sequence[Snapshot], sources: Mapping[str, dict]) -> None:
    require(bool(history) and history[0].revision == 0, "Missing initial revision")
    previous = None
    for snapshot in history:
        snapshot.validate(sources)
        if previous is not None:
            require(snapshot.value["case_id"] == previous.value["case_id"] and
                    snapshot.value["parent"] == previous.revision, "Broken revision ancestry")
            old = {r["ref"]: r for r in previous.value["records"]}
            new = {r["ref"]: r for r in snapshot.value["records"]}
            require(all(new.get(ref) == record for ref, record in old.items()), "Committed records were rewritten")
            if "membership" in previous.value:
                require(snapshot.value.get("membership", {}).get("proposals_from") ==
                        previous.value["membership"]["proposals_from"], "Proposal boundary moved")
            else:
                require("membership" not in snapshot.value or
                        snapshot.value["membership"]["proposals_from"] == len(previous.value["records"]),
                        "Proposal boundary must follow the records already in the model")
            before = previous.value.get("decisions", [])
            decisions = snapshot.value.get("decisions", [])
            require(decisions[:len(before)] == before, "Committed decisions were rewritten")
            added_decisions = decisions[len(before):]
            added = set(snapshot.value["applied_requests"]) - set(previous.value["applied_requests"])
            require(set(previous.value["applied_requests"]) <= set(snapshot.value["applied_requests"]),
                    "Applied requests were removed")
            if not added:
                # A local decision: one recorded choice, no records, the same live question.
                require(len(added_decisions) == 1 and new.keys() == old.keys() and
                        snapshot.target == previous.target and
                        snapshot.value["adapter_versions"] == previous.value["adapter_versions"],
                        "A decision revision records exactly one decision and nothing else")
                require(added_decisions[0]["mode"] == "explicit", "A local decision is explicit")
            else:
                require(len(added) == 1, "A consulting revision applies exactly one request")
                request = sources[next(iter(added))]
                require(request["base_revision"] <= previous.revision and
                        request["response_target"] == previous.target,
                        "Applied input has the wrong revision or response target")
                require(snapshot.target not in old and new[snapshot.target]["source_refs"] == [request["request_id"]],
                        "A consulting revision must publish its sourced next intervention")
                require(all(d["mode"] == "automatic" and d.get("request_id") == request["request_id"]
                            for d in added_decisions) and len(added_decisions) <= 1,
                        "A reply records no decision but its own automatic acceptance")
                require(set(snapshot.value["adapter_versions"]) == set(snapshot.value["applied_requests"]) and
                        all(snapshot.value["adapter_versions"].get(k) == v
                            for k, v in previous.value["adapter_versions"].items()), "Adapter provenance changed")
            require(all(snapshot.value["counters"].get(k, 0) >= v for k, v in previous.value["counters"].items()),
                    "Allocation ledger moved backwards")
        previous = snapshot
