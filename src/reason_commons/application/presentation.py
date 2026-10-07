"""Presentation-neutral reads of a frozen case revision, with no inference.

Only explicit formulation references become links. Unknown data stays unknown;
these trace links cannot be interpreted as causal, necessity or agreement edges.
Layout, Markdown and terminal drawing belong to adapters.
"""

from copy import deepcopy

from reason_commons.domain.model import TREES, require


VIEWS = ("next", "explain", "goal", "trees", "reasoning", "tests", "actions", "backlog", "history", "sources")
LINK_FIELDS = {"goal_ref": "concerns goal", "test_ref": "concerns test", "claim_ref": "carries out",
               "observation_refs": "uses observation", "required_context_refs": "uses context"}
LINK_LABELS = {("test", "goal_ref"): "tests progress toward", ("test", "claim_ref"): "carries out",
               ("action", "test_ref"): "work for",
               ("observation", "test_ref"): "reports result of", ("review", "test_ref"): "reviews"}
UNKNOWN_FIELDS = {"goal": ("scope", "horizon", "measure", "baseline", "protections"),
                  "test": ("scope", "stop_condition", "review_date"),
                  "action": ("owner", "authority", "execution", "expected_state_attainment"),
                  "observation": ("scope", "denominator", "period", "basis")}


def legacy_goal_aliases(records, membership):
    """Older imports recorded a file's goal twice: as the goal and as a Goal Tree statement in the
    goal role, from the same source in the same reply. Read such a pair as the one goal."""
    goals = [r for r in records.values() if r["kind"] == "goal" and membership.current(r["ref"])]
    aliases = {}
    for claim in records.values():
        if claim["kind"] == "claim" and claim["data"]["role"] == "goal" and claim["data"]["tree"] == "goal":
            twin = next((g for g in goals if g["source_refs"] == claim["source_refs"]
                         and g["data"]["statement"] == claim["data"]["statement"]), None)
            if twin:
                aliases[claim["ref"]] = twin["ref"]
    return aliases


def project_trees(records, membership=None):
    """The current state of each thinking-process tree in the model, exactly as recorded.

    Only accepted records appear; proposals wait in the backlog. The case's goal is the Goal
    Tree's top statement. A new version takes the place of the old one and keeps its links; a
    withdrawn claim or link disappears from the tree but stays in history. A link belongs to one
    tree and may use a statement from another, which then appears in this tree too, marked with
    its own tree. Nothing is inferred: a tree shows only claims and links someone recorded.
    """
    if membership is None:
        from reason_commons.domain.membership import Membership
        membership = Membership({"records": list(records.values())})
    aliases = legacy_goal_aliases(records, membership)
    replaced = membership.replacements()

    def latest(ref):
        return aliases.get(membership.latest(ref), membership.latest(ref))

    def earlier(ref):
        previous = {new: old for old, new in replaced.items()}
        chain = []
        while ref in previous:
            ref = previous[ref]
            chain.append(ref)
        return chain

    def home(record):
        return "goal" if record["kind"] == "goal" else record["data"]["tree"]

    def node(record, tree):
        ref = record["ref"]
        item = {"ref": ref, "role": "goal" if record["kind"] == "goal" else record["data"]["role"],
                "statement": record["data"]["statement"], "basis": record["data"].get("basis"),
                "earlier_wording": [records[r]["data"]["statement"] for r in earlier(ref)],
                "tests": [{"ref": t["ref"], "statement": t["data"]["statement"],
                           "forecast": [f.get("expected") for f in t["data"].get("forecast") or []],
                           "results": [o["data"]["value"] for o in records.values()
                                       if o["kind"] == "observation" and o["data"]["test_ref"] == t["ref"]
                                       and membership.accepted(o["ref"])]}
                          for t in records.values() if t["kind"] == "test" and membership.current(t["ref"])
                          and t["data"].get("claim_ref") and latest(t["data"]["claim_ref"]) == ref]}
        if home(record) != tree:
            item["from_tree"] = home(record)
        return item

    # The goal is the Goal Tree's top statement, whatever order it was recorded in.
    statements = sorted((r for r in records.values() if r["kind"] in {"claim", "goal"}
                         and membership.current(r["ref"]) and r["ref"] not in aliases),
                        key=lambda r: r["kind"] != "goal")
    trees = []
    for name in TREES:
        nodes = [node(r, name) for r in statements if home(r) == name]
        present = {n["ref"] for n in nodes}
        links = []
        for link in (r for r in records.values() if r["kind"] == "link" and r["data"]["tree"] == name):
            if not membership.drawn_link(link["ref"]):
                continue
            ends = latest(link["data"]["from_ref"]), latest(link["data"]["to_ref"])
            if ends[0] == ends[1]:
                continue
            for end in ends:
                if end not in present:
                    nodes.append(node(records[end], name))
                    present.add(end)
            links.append({"ref": link["ref"], "relation": link["data"]["relation"], "from": ends[0],
                          "to": ends[1], "assumption": link["data"].get("assumption")})
        trees.append({"tree": name, "claims": nodes, "links": links})
    return trees


def describe(record, records=None):
    """One readable line for a record, for backlog rows and decision lists. With ``records``, a link or
    withdrawal names the statements it concerns instead of their references."""
    data = record["data"]
    named = lambda ref: (f"“{describe(records[ref], records)}”" if records and ref in records else ref)
    if record["kind"] in {"claim", "goal"}:
        return data["statement"]
    if record["kind"] == "note":
        return data["text"]
    if record["kind"] == "link":
        return f"{named(data['from_ref'])} {data['relation'].replace('_', ' ')} {named(data['to_ref'])}"
    if record["kind"] == "retraction":
        return f"withdraw {named(data['target_ref'])}: {data['reason']}"
    if record["kind"] == "observation":
        return f"{data['measure']}: {data['value']}"
    if record["kind"] == "review":
        return data["assessment"]
    return data.get("statement", record["ref"])


def project_backlog(snapshot, records, membership, sources):
    entries = []
    for entry in membership.backlog():
        record = entry["record"]
        entry.update(kind=record["kind"], tree=record["data"].get("tree") if record["kind"] in {"claim", "link"}
                     else "goal" if record["kind"] == "goal" else None, summary=describe(record, records),
                     source_refs=list(record["source_refs"]),
                     words=[sources[s].get("text") for s in record["source_refs"] if s in sources
                            and "request_id" in sources[s]],
                     confidence=record.get("confidence"))
        if record["data"].get("replaces") in records:
            entry["replaces"] = {"ref": record["data"]["replaces"],
                                 "summary": describe(records[record["data"]["replaces"]], records)}
        for flag in entry.get("flags", []):
            flag["cites_summary"] = describe(records[flag["cites"]], records)
            if flag["now"]:
                flag["now_summary"] = describe(records[flag["now"]], records)
        entries.append(entry)
    return entries


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
    membership = snapshot.membership()
    all_records = records
    # Views show the model; proposals are listed apart, in the backlog, and never drawn as part of it.
    records = {ref: r for ref, r in all_records.items() if r["kind"] == "intervention" or membership.accepted(ref)}
    proposals = {ref: r for ref, r in all_records.items() if membership.status.get(ref) == "proposed"}
    goals = [r for r in records.values() if r["kind"] == "goal" and membership.current(r["ref"])]
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
    filters = {"backlog": set(), "goal": {"goal"}, "tests": {"test", "observation", "review"}, "trees": {"claim", "link"},
               "actions": {"action"}, "reasoning": set(UNKNOWN_FIELDS) | {"note", "review", "claim"}}
    if selection in proposals:
        included = set()
    elif selection in records:
        # Resolve complete context recursively; never draw a dangling conclusion.
        included = {selection}
    elif view in {"next", "explain"} and question:
        context = question["data"].get("required_context_refs") or []
        included = set(context) if context else {
            r["ref"] for r in records.values() if r["kind"] != "intervention"
            and set(r["source_refs"]) & set(question["source_refs"])}
        if question["data"].get("goal_ref"):
            included.add(question["data"]["goal_ref"])
        included &= set(records)
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
        waiting = [r for r in proposals.values() if r["kind"] == "goal"]
        unknowns.append({"ref": None, "field": "goal", "message": "A goal is proposed and waits for you."
                         if waiting else "No formal goal is recorded yet."})
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
        observations = [r for r in records.values() if r["kind"] == "observation" and r["data"]["test_ref"] == test["ref"]
                        and membership.current(r["ref"])]
        comparisons.append({"test": deepcopy(test), "observations": deepcopy(observations),
                            "reviews": [deepcopy(r) for r in records.values() if r["kind"] == "review"
                                        and r["data"]["test_ref"] == test["ref"] and membership.current(r["ref"])]})
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
    backlog = project_backlog(snapshot, all_records, membership, sources)
    reply = None
    if case["applied_requests"]:
        request_id = case["applied_requests"][-1]
        # A reply publishes its updates and then its question, so its records are the ones just before
        # the current question, back to the previous one. (An import's records cite its file, not the request.)
        order = case["records"]
        end = next(i for i, r in enumerate(order) if r["ref"] == case["current_intervention"])
        begin = max((i for i, r in enumerate(order[:end]) if r["kind"] == "intervention"), default=-1) + 1
        made = order[begin:end]
        automatic = [d for d in case.get("decisions", []) if d.get("request_id") == request_id]
        reply = {"request_id": request_id, "automatic": bool(automatic),
                 "records": [{"ref": r["ref"], "kind": r["kind"], "record": deepcopy(r),
                              "summary": describe(r, all_records),
                              "status": membership.status[r["ref"]]} for r in made]}
    if not historical:
        waiting = [e["ref"] for e in backlog if e["entry"] == "proposal"]
        if reply and any(r["status"] == "proposed" for r in reply["records"]):
            actions.append({"id": "accept_reply", "label": "Accept what the last reply proposed", "route": "local",
                            "capability": "accept", "arguments": {
                                "refs": [r["ref"] for r in reply["records"] if r["status"] == "proposed"],
                                "base_revision": case["revision"]}, "requires": ["speaker"]})
        if waiting:
            actions.append({"id": "view_backlog", "label": f"Decide the {len(waiting)} waiting proposals",
                            "route": "local", "capability": "workspace", "arguments": {"view": "backlog"}})
        if any(e["entry"] == "review" for e in backlog):
            actions.append({"id": "review_flags", "label": "Ask the consultant about the open reviews",
                            "route": "asks_consultant", "capability": "submit", "arguments": {
                                "intent": "review_flags", "base_revision": case["revision"],
                                "response_target": case["current_intervention"]}, "requires": ["text", "speaker"]})
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
            "record_count": len(all_records), "displayed_record_count": len(relevant),
            "attribution": {r["ref"]: [{"source_ref": s, "speaker": sources[s].get("speaker")}
                                         for s in r["source_refs"]] for r in all_records.values()},
            "selected_source": deepcopy(visible_sources.get(selection)),
            "sources": visible_sources if view == "sources" else {}, "uncertainty": unknowns,
            "diagram": {"kind": "recorded_references", "nodes": deepcopy(diagram_nodes), "links": diagram_links},
            "comparisons": comparisons, "available_actions": actions,
            "trees": project_trees(all_records, membership),
            "acceptance": membership.acceptance, "backlog": backlog, "reply": reply,
            "membership": {ref: status for ref, status in membership.status.items()},
            "proposals": deepcopy(proposals),
            "history": deepcopy(list(history)) if view == "history" else [],
            "pending_requests": deepcopy(list(pending)) if not historical else [],
            "draft": deepcopy(cursor or {}) if not historical else {}}
