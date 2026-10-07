"""Machine-readable projection of the domain's existing proposal registry.

Providers can constrain output using this contract. The aggregate validator
remains authoritative for references, provenance and transactional invariants.
"""

from reason_commons.domain.model import (CONSULT_INTENTS, ENUM_FIELDS, FIELDS, FORECAST_FIELDS,
                                         FORECAST_REQUIRED, INTERVENTION_FIELDS, INTERVENTION_KINDS,
                                         INTERVENTION_REQUIRED, PROFILE, REQUIRED, REQUIRED_TEXT, SCHEMA, VIEW_TARGETS)


def object_schema(properties, required):
    return {"type": "object", "properties": properties, "required": sorted(required),
            "additionalProperties": False}


def proposal_schema():
    text = {"type": "string", "minLength": 1}
    nullable_text = {"type": ["string", "null"]}
    def text_list():
        # Each schema branch is independently refinable by a provider. Sharing
        # mutable arrays lets source constraints accidentally change protections.
        return {"type": "array", "items": {"type": "string", "minLength": 1}}
    forecast = object_schema({field: nullable_text for field in sorted(FORECAST_FIELDS)}, FORECAST_REQUIRED)
    updates = []
    for kind, fields in FIELDS.items():
        properties = {}
        for field in sorted(fields):
            if field in ENUM_FIELDS:
                properties[field] = {"type": "string", "enum": sorted(ENUM_FIELDS[field])}
            elif field in {"protections", "observation_refs"}:
                properties[field] = text_list()
            elif field == "forecast":
                properties[field] = {"type": "array", "items": forecast, "minItems": 1}
            else:
                properties[field] = text if field in REQUIRED_TEXT[kind] else nullable_text
        # confidence: how faithfully the update represents what was said. It is kept with the
        # proposal and decides nothing; the operator's decision puts a proposal into the model.
        updates.append(object_schema({"operation": {"const": "record_" + kind}, "temporary_id": text,
                                      "data": object_schema(properties, REQUIRED[kind]), "source_refs": text_list(),
                                      "confidence": {"type": "number", "minimum": 0, "maximum": 1}},
                                     {"operation", "data", "source_refs"}))
    # Temporary test references are resolved by the aggregate after allocation.
    actions = {"anyOf": [object_schema({"type": {"const": "view"}, "target": {"anyOf": [
        {"type": "string", "enum": sorted(VIEW_TARGETS)}, {"type": "string", "pattern": "^test:.+"}]}},
        {"type", "target"}), object_schema({"type": {"const": "consult"},
        "intent": {"type": "string", "enum": sorted(CONSULT_INTENTS)}}, {"type", "intent"})]}
    intervention = {field: text for field in INTERVENTION_FIELDS}
    intervention.update(kind={"type": "string", "enum": sorted(INTERVENTION_KINDS)},
                        goal_ref=nullable_text, required_context_refs=text_list(),
                        options={"type": "array", "items": object_schema({"id": text, "label": text,
                            "action": actions}, {"id", "label", "action"})})
    return object_schema({"schema_version": {"type": "string", "const": SCHEMA},
                          "delivery_profile": {"type": "string", "const": PROFILE},
                          "request_id": text, "base_revision": {"type": "integer", "minimum": 0},
                          "intervention": object_schema(intervention, INTERVENTION_REQUIRED),
                          "proposed_updates": {"type": "array", "items": {"anyOf": updates}}},
                         {"schema_version", "delivery_profile", "request_id", "base_revision",
                          "intervention", "proposed_updates"})
