"""Presentation-neutral reads of a frozen case revision, with no inference.

Only explicit formulation references become links. Unknown data stays unknown;
these trace links cannot be interpreted as causal, necessity or agreement edges.
Layout, Markdown and terminal drawing belong to adapters.
"""

from copy import deepcopy

from reason_commons.domain.model import require


VIEWS = ("next", "explain", "goal", "reasoning", "tests", "actions", "history", "sources")
LINK_FIELDS = {"goal_ref": "concerns goal", "test_ref": "concerns test",
               "observation_refs": "uses observation", "required_context_refs": "uses context"}
LINK_LABELS = {("test", "goal_ref"): "tests progress toward", ("action", "test_ref"): "work for",
               ("observation", "test_ref"): "reports result of", ("review", "test_ref"): "reviews"}
UNKNOWN_FIELDS = {"goal": ("scope", "horizon", "measure", "baseline", "protections"),
                  "test": ("scope", "stop_condition", "review_date"),
                  "action": ("owner", "authority", "execution", "expected_state_attainment"),
                  "observation": ("scope", "denominator", "period", "basis")}


def project_workspace(snapshot, sources, *, view="next", selection=None, live_revision=None,
                      cursor=None, history=(), pending=()):
    require(view in VIEWS, "Unknown workspace view")
    case = snapshot.to_dict()
    records = {r["ref"]: r for r in case["records"]}
    published_sources = {s for r in records.values() for s in r["source_refs"]}
    visible_sources = {k: deepcopy(v) for k, v in sources.items()
                       if live_revision == case["revision"] or k in published_sources}
    require(selection is None or selection in records or selection in visible_sources,
            "Selection does not exist in this revision")
    question = records.get(case["current_intervention"])
    goals = [r for r in records.values() if r["kind"] == "goal"]
    links = []
    for record in records.values():
        for field, label in LINK_FIELDS.items():
            targets = record["data"].get(field)
            if not isinstance(targets, list):
                targets = [targets] if targets else []
            for target in targets:
                if target in records:
                    links.append({"from": record["ref"], "to": target, "field": field,
                                  "label": LINK_LABELS.get((record["kind"], field), label)})
    filters = {"goal": {"goal"}, "tests": {"test", "observation", "review"},
               "actions": {"action"}, "reasoning": set(UNKNOWN_FIELDS) | {"note", "review"}}
    if selection in records:
        # Resolve complete context recursively; never draw a dangling conclusion.
        included = {selection}
    elif view in {"next", "explain"} and question:
        context = question["data"].get("required_context_refs") or []
        included = set(context) if context else {
            r["ref"] for r in records.values() if r["kind"] != "intervention"
            and set(r["source_refs"]) & set(question["source_refs"])}
        if question["data"].get("goal_ref"):
            included.add(question["data"]["goal_ref"])
    elif view in filters:
        included = {r["ref"] for r in records.values() if r["kind"] in filters[view]}
    else:
        included = {r["ref"] for r in records.values() if r["kind"] != "intervention"}
    while True:
        connected = {e["to"] for e in links if e["from"] in included}
        if connected <= included:
            break
        included |= connected
    relevant = [r for r in records.values() if r["ref"] in included]
    unknowns = []
    if not goals:
        unknowns.append({"ref": None, "field": "goal", "message": "No formal goal is recorded yet."})
    for record in relevant:
        for field in UNKNOWN_FIELDS.get(record["kind"], ()):
            if record["data"].get(field) in (None, [], "unknown"):
                unknowns.append({"ref": record["ref"], "field": field,
                                 "message": field.replace("_", " ") + " is not established."})
        if record["kind"] == "test":
            for index, forecast in enumerate(record["data"].get("forecast") or []):
                for field in ("measure", "expected", "scope", "denominator", "period"):
                    if forecast.get(field) is None:
                        unknowns.append({"ref": record["ref"], "field": f"forecast.{index}.{field}",
                                         "message": f"Forecast {index + 1}: {field} is not established."})
    diagram_refs = {r["ref"] for r in relevant if r["kind"] != "intervention"}
    diagram_links = [e for e in links if e["from"] in diagram_refs and e["to"] in diagram_refs]
    diagram_nodes = [r for r in relevant if any(r["ref"] in (e["from"], e["to"]) for e in diagram_links)]
    comparisons = []
    for test in (r for r in relevant if r["kind"] == "test"):
        observations = [r for r in records.values() if r["kind"] == "observation" and r["data"]["test_ref"] == test["ref"]]
        comparisons.append({"test": deepcopy(test), "observations": deepcopy(observations),
                            "reviews": [deepcopy(r) for r in records.values() if r["kind"] == "review"
                                        and r["data"]["test_ref"] == test["ref"]]})
    historical = live_revision is not None and live_revision != case["revision"]
    actions = [{"id": "view_" + name, "label": name.title(), "route": "local", "capability": "workspace",
                "arguments": {"view": name, "revision": case["revision"]}} for name in VIEWS]
    if historical:
        actions.append({"id": "return_live", "label": "Return to the live question", "route": "local",
                        "capability": "workspace", "arguments": {"view": "next"}})
    if not historical:
        actions += [{"id": intent, "label": label, "route": "asks_consultant", "capability": "submit",
                     "arguments": {"intent": intent, "base_revision": case["revision"],
                                   "response_target": case["current_intervention"]}, "requires": ["text", "speaker"]}
                    for intent, label in [("answer", "Answer or contribute a correction"),
                                          ("direct_advice", "Ask for direct advice"),
                                          ("another_question", "Ask a different question"),
                                          ("explain_observation", "Ask for help with an observation")]]
    for option in question["data"].get("options", []) if question else []:
        action = option["action"]
        if action["type"] == "consult":
            if historical:
                continue
            arguments = {"intent": action["intent"], "base_revision": case["revision"],
                         "response_target": case["current_intervention"]}
            route, capability, required = "asks_consultant", "submit", ["text", "speaker"]
        else:
            target = action["target"]
            arguments = {"view": {"current_question": "next"}.get(target, target),
                         "revision": case["revision"]}
            if target.startswith("test:"):
                arguments.update(view="tests", selection=target.split(":", 1)[1])
            route, capability, required = "local", "workspace", []
        actions.append({"id": "option_" + option["id"], "label": option["label"], "route": route,
                        "capability": capability, "arguments": arguments, "requires": required})
    actions.append({"id": "export", "label": "Export the live portable case", "route": "local",
                    "capability": "export", "requires": ["destination"]})
    if not historical:
        actions += [{"id": "retry_" + p["input"]["request_id"], "label": "Explicitly retry " + p["input"]["request_id"],
                     "route": "asks_consultant", "capability": "retry",
                     "arguments": {"request_id": p["input"]["request_id"]}} for p in pending
                    if p["status"] != "stale" and p["input"]["base_revision"] == case["revision"]
                    and p["input"]["response_target"] == case["current_intervention"]]
    return {"schema_version": "1", "case_id": case["case_id"], "case_name": case["name"],
            "revision": case["revision"], "live_revision": live_revision, "historical": historical,
            "view": view, "selection": selection,
            "target": {"base_revision": case["revision"], "response_target": case["current_intervention"]},
            "question": deepcopy(question), "goals": deepcopy(goals), "records": deepcopy(relevant),
            "record_count": len(records), "displayed_record_count": len(relevant),
            "attribution": {r["ref"]: [{"source_ref": s, "speaker": sources[s].get("speaker")}
                                         for s in r["source_refs"]] for r in records.values()},
            "selected_source": deepcopy(visible_sources.get(selection)),
            "sources": visible_sources if view == "sources" else {}, "uncertainty": unknowns,
            "diagram": {"kind": "recorded_references", "nodes": deepcopy(diagram_nodes), "links": diagram_links},
            "comparisons": comparisons, "available_actions": actions,
            "history": deepcopy(list(history)) if view == "history" else [],
            "pending_requests": deepcopy(list(pending)) if not historical else [],
            "draft": deepcopy(cursor or {}) if not historical else {}}
