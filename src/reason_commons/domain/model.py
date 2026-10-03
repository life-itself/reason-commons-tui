"""The p0 aggregate and the explicit v1 record/proposal contract."""

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
    "goal": {"statement", "scope", "horizon", "measure", "baseline", "protections"},
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
                   "from_ref": {"claim"}, "to_ref": {"claim"}, "replaces": {"claim"},
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
CONSULT_INTENTS = {"another_question", "direct_advice", "explain_observation"}


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


def validate_tree_record(record: dict, records: Mapping[str, dict], earlier: set,
                         withdrawn: set, replaced: set) -> None:
    """Tree records cite only earlier, still-current claims, so history reads in order."""
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
            require(records[data[key]]["data"]["tree"] == data["tree"], "A link joins claims of its own tree")
        require(data["from_ref"] != data["to_ref"], "A claim cannot be linked to itself")
    elif kind == "retraction":
        require(current(data["target_ref"]), "Only an earlier, current claim or link can be withdrawn")
        withdrawn.add(data["target_ref"])
    elif kind == "test" and data.get("claim_ref") is not None:
        require(current(data["claim_ref"]), "A test can only carry out an earlier, current claim")


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

    @classmethod
    def initial(cls, case_id: str, name: str, timestamp: str, timezone: str):
        text(name, "case name")
        return cls({"schema_version": SCHEMA, "delivery_profile": PROFILE, "case_id": case_id,
                    "name": name, "revision": 0, "parent": None, "timestamp": timestamp,
                    "timezone": timezone, "records": [], "current_intervention": None,
                    "applied_requests": [], "source_input_refs": [], "counters": {},
                    "adapter_versions": {}})

    def validate(self, sources: Mapping[str, dict]) -> None:
        shape(self.value, {"schema_version", "delivery_profile", "case_id", "name", "revision", "parent",
                           "timestamp", "timezone", "records", "current_intervention", "applied_requests",
                           "source_input_refs", "counters", "adapter_versions"},
              {"schema_version", "delivery_profile", "case_id", "name", "revision", "parent", "timestamp",
               "timezone", "records", "current_intervention", "applied_requests", "source_input_refs",
               "counters", "adapter_versions"}, "snapshot")
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
        records = {}
        for record in self.value["records"]:
            shape(record, {"ref", "kind", "data", "source_refs"}, {"ref", "kind", "data", "source_refs"}, "record")
            kind, ref = record["kind"], record["ref"]
            require(kind in PREFIXES, "Unavailable record kind")
            require(isinstance(ref, str) and bool(re.fullmatch(PREFIXES[kind] + r"[1-9]\d*@1", ref)), "Invalid record ID")
            require(ref not in records, "Duplicate record ID")
            require(int(ref[1:].split("@")[0]) <= counters.get(kind, 0), "ID exceeds allocation ledger")
            string_list(record["source_refs"], "source_refs")
            require(bool(record["source_refs"]) and all(s in sources for s in record["source_refs"]), "Unknown source")
            records[ref] = record
        withdrawn, replaced, earlier = set(), set(), set()
        for record in self.value["records"]:
            if record["kind"] == "intervention":
                validate_intervention(record["data"], records)
            else:
                validate_value(record["kind"], record["data"])
                for key, kinds in REFERENCE_KINDS.items():
                    if record["data"].get(key) is not None:
                        reference(record["data"][key], records)
                        require(records[record["data"][key]]["kind"] in kinds, f"Wrong reference kind: {key}")
                validate_tree_record(record, records, earlier, withdrawn, replaced)
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

    def apply(self, proposal: dict, input_record: dict, sources: Mapping[str, dict],
              revision: int, timestamp: str, timezone: str, adapter_version: str,
              reserved: Mapping[str, int] = None):
        validate_input(input_record)
        if input_record["base_revision"] != self.revision or input_record["response_target"] != self.target:
            raise StaleWork("Response is stale; re-evaluate against the current revision")
        shape(proposal, {"schema_version", "delivery_profile", "request_id", "base_revision", "intervention",
                         "proposed_updates"}, {"schema_version", "delivery_profile", "request_id", "base_revision",
                                               "intervention", "proposed_updates"}, "proposal")
        require(proposal["schema_version"] == SCHEMA and proposal["delivery_profile"] == PROFILE,
                "Proposal belongs to an unsupported schema or delivery profile")
        require(proposal["request_id"] == input_record["request_id"] and
                type(proposal["base_revision"]) is int and proposal["base_revision"] == self.revision,
                "Proposal request or revision mismatch")
        require(input_record["request_id"] not in self.value["applied_requests"], "Request already applied")
        result = self.to_dict()
        counters = result["counters"]
        for kind, number in (reserved or {}).items():
            counters[kind] = max(counters.get(kind, 0), number)

        def allocate(kind):
            counters[kind] = counters.get(kind, 0) + 1
            return f"{PREFIXES[kind]}{counters[kind]}@1"

        updates = proposal["proposed_updates"]
        require(isinstance(updates, list), "Updates must be a list")
        temporary = {}
        new_records = []
        for update in updates:
            shape(update, {"operation", "temporary_id", "data", "source_refs"},
                  {"operation", "data", "source_refs"}, "update")
            operation = update["operation"]
            require(isinstance(operation, str) and operation.startswith("record_"), "Unknown operation")
            kind = operation[7:]
            require(kind in FIELDS, "Update belongs to a later delivery profile")
            ref = allocate(kind)
            if "temporary_id" in update:
                temp = update["temporary_id"]
                text(temp, "temporary_id")
                require(temp not in temporary and temp not in {r["ref"] for r in result["records"]}, "Duplicate temporary ID")
                temporary[temp] = ref
            new_records.append({"ref": ref, "kind": kind, "data": deepcopy(update["data"]),
                                "source_refs": deepcopy(update["source_refs"])})

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
        new_records.append({"ref": target, "kind": "intervention", "data": intervention,
                            "source_refs": [input_record["request_id"]]})
        result["records"].extend(new_records)
        result.update(revision=revision, parent=self.revision, timestamp=timestamp, timezone=timezone,
                      current_intervention=target)
        result["applied_requests"].append(input_record["request_id"])
        result["source_input_refs"].append(input_record["request_id"])
        result["adapter_versions"][input_record["request_id"]] = adapter_version
        snapshot = Snapshot(result)
        snapshot.validate(sources)
        return snapshot


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
            require(set(previous.value["applied_requests"]) < set(snapshot.value["applied_requests"]),
                    "Revision must add an applied request")
            added = set(snapshot.value["applied_requests"]) - set(previous.value["applied_requests"])
            require(len(added) == 1, "A consulting revision applies exactly one request")
            request = sources[next(iter(added))]
            require(request["base_revision"] == previous.revision and request["response_target"] == previous.target,
                    "Applied input has the wrong revision or response target")
            require(snapshot.target not in old and new[snapshot.target]["source_refs"] == [request["request_id"]],
                    "A consulting revision must publish its sourced next intervention")
            require(set(snapshot.value["adapter_versions"]) == set(snapshot.value["applied_requests"]) and
                    all(snapshot.value["adapter_versions"].get(k) == v
                        for k, v in previous.value["adapter_versions"].items()), "Adapter provenance changed")
            require(all(snapshot.value["counters"].get(k, 0) >= v for k, v in previous.value["counters"].items()),
                    "Allocation ledger moved backwards")
        previous = snapshot
