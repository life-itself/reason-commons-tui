"""Shared provider grammar and defensive JSON/redirect handling.

This projects the existing domain contract; it supplies no consulting semantics.
"""

import json
from urllib.request import HTTPRedirectHandler

from reason_commons.domain.contract import proposal_schema
from reason_commons.domain.model import REFERENCE_KINDS, REQUIRED_REFERENCES


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def decode_json(value):
    def no_duplicates(pairs):
        result = {}
        for key, content in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = content
        return result

    def no_constant(value):
        raise ValueError("Nonstandard JSON constant")

    return json.loads(value, object_pairs_hook=no_duplicates, parse_constant=no_constant)


def request_schema(request):
    schema = proposal_schema()
    schema["properties"]["request_id"] = {"const": request["input"]["request_id"]}
    schema["properties"]["base_revision"] = {"const": request["input"]["base_revision"]}
    if request["input"].get("text", "").strip():
        # A provider must account for meaningful contributions. This narrows
        # the generation contract; aggregate validation still owns truth.
        schema["properties"]["proposed_updates"]["minItems"] = 1
    # Keep source IDs and formulation IDs in separate grammar namespaces.
    # Temporary aliases are a provider convention, not a new domain rule.
    aliases = ["goal", "test", "action", "review", "note", "delivery", "acknowledgement"]
    temporary = {"anyOf": [{"enum": aliases}, {"type": "string", "pattern": "^temp_[A-Za-z][A-Za-z0-9_]*$"}]}
    # Records the operator rejected or undid, or that were closed, can no longer be cited.
    gone = set((request.get("model") or {}).get("not_admitted", []))
    records = [r for r in request["case"].get("records", []) if r["ref"] not in gone]

    def refs(kinds=None):
        allowed = [r["ref"] for r in records if kinds is None or r["kind"] in kinds]
        choices = [temporary]
        if allowed:
            choices.append({"enum": allowed})
        return {"anyOf": choices}

    intervention_schema = schema["properties"]["intervention"]["properties"]
    intervention_schema["required_context_refs"]["items"] = refs()
    intervention_schema["goal_ref"] = {"anyOf": [refs({"goal"}), {"type": "null"}]}
    for update in schema["properties"]["proposed_updates"]["items"]["anyOf"]:
        update["properties"]["temporary_id"] = temporary
        update["required"] = sorted(set(update["required"]) | {"temporary_id"})
        if request["sources"]:
            update["properties"]["source_refs"]["items"] = {"enum": list(request["sources"])}
            update["properties"]["source_refs"]["minItems"] = 1
        fields = update["properties"]["data"]["properties"]
        record_kind = update["properties"]["operation"]["const"][7:]
        for name, kinds in REFERENCE_KINDS.items():
            if name in fields:
                fields[name] = (refs(kinds) if name in REQUIRED_REFERENCES.get(record_kind, set())
                                else {"anyOf": [refs(kinds), {"type": "null"}]})
        if "observation_refs" in fields:
            fields["observation_refs"]["items"] = refs({"observation"})
    return schema
