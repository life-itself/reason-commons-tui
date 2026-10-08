"""Deterministic text, chat Markdown and Mermaid over the same workspace read.

Renderers format stored values; they do not supply reasoning or infer outcomes.
The Markdown diagram contains explicit record references with labeled meanings.
"""

import base64
import html
import re


TITLES = {"goal": "Goal", "note": "Reported note", "test": "Original test", "action": "Action",
          "observation": "Observation", "review": "Review", "intervention": "Question",
          "claim": "Tree statement", "link": "Tree link", "retraction": "Withdrawal"}
LABELS = {"goal_ref": "Goal", "test_ref": "Test", "observation_refs": "Observations",
          "source_refs": "Sources", "required_context_refs": "Relevant context",
          "expected_state_attainment": "Expected state attainment", "execution": "Work execution"}



FAILURE_HINTS = {
    "configuration": "run the providers check (reason-commons providers)",
    "http_error": "check the credential and model access",
    "timeout": "allow more time or check provider load",
    "connection": "check the provider is running",
    "unknown": "run the providers check (reason-commons providers) and read the provider's own logs",
}

def value_text(value):
    if value is None or value == []:
        return "not recorded"
    if isinstance(value, dict):
        return "; ".join(f"{k.replace('_', ' ')}: {value_text(v)}" for k, v in value.items())
    if isinstance(value, list):
        return "; ".join(value_text(v) for v in value)
    return str(value)


def _literal(value, markdown):
    text = value_text(value)
    # Plain text retains literal content except terminal control characters.
    text = "".join(c if c in "\n\t" or ord(c) >= 32 and ord(c) != 127 else "�" for c in text)
    if not markdown:
        return text
    text = html.escape(text, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", text)


def render_mermaid(workspace):
    diagram = workspace["diagram"]
    if not diagram["links"]:
        return ""
    names = {r["ref"]: f"n{i}" for i, r in enumerate(diagram["nodes"])}
    lines = ["flowchart LR"]
    for record in diagram["nodes"]:
        data = record["data"]
        text = data.get("statement", data.get("assessment", data.get("text")))
        if text is None:
            text = f"{data.get('measure', 'Result')}: {value_text(data.get('value'))}"
        label = f"{TITLES[record['kind']]} {record['ref']}: {text}"
        # Numeric entities escape every non-ASCII label character and syntax
        # delimiter. Newlines become spaces, never a new Mermaid statement.
        label = "".join(c if c.isascii() and c.isalnum() or c in " .,:%/@_-" else
                        " " if c in "\r\n\t" else f"#{ord(c)};" for c in label)
        lines.append(f'  {names[record["ref"]]}["{label}"]')
    for edge in diagram["links"]:
        lines.append(f'  {names[edge["from"]]} -->|{edge["label"]}| {names[edge["to"]]}')
    return "\n".join(lines)


def render_workspace(workspace, *, markdown=False, result=None, speaker=None):
    lines = []
    def heading(text):
        lines.extend([("**" + text + "**") if markdown else text, ""])
    def paragraph(text):
        lines.extend([text, ""])
    def literal(value):
        return _literal(value, markdown)
    def record_details(record):
        heading(f"{TITLES[record['kind']]} {record['ref']}")
        attributed = workspace["attribution"].get(record["ref"], [])
        if attributed:
            paragraph("Sources: " + "; ".join(literal(a["speaker"] or "undeclared") + " · " + a["source_ref"] for a in attributed))
        for field, value in record["data"].items():
            label = LABELS.get(field, field.replace("_", " ").capitalize())
            paragraph(label + ": " + literal(value))
    def source_details(source):
        if "request_id" in source:
            heading("Participant contribution · " + source["request_id"])
            paragraph("Declared speaker: " + literal(source["speaker"]))
            paragraph(literal(source["text"]))
            paragraph("Declarations: " + literal(source.get("declarations") or None))
        else:
            heading("Supplied source · " + literal(source["name"]))
            paragraph("Declared speaker: " + literal(source["speaker"]))
            try:
                content = base64.b64decode(source["content_base64"], validate=True).decode("utf-8")
            except (UnicodeError, ValueError):
                content = "Binary attachment; content is retained in the portable case."
            paragraph(literal(content))

    status = "Stored revision"
    if result:
        status = {"saved": "Saved", "input_retained": "Input retained; consultation incomplete",
                  "not_saved": "Save not confirmed", "unavailable": "Consultant unavailable",
                  "rejected": "Proposal rejected", "stale": "Case changed; input needs re-evaluation",
                  "skill_incomplete": "Contribution procedure incomplete"}.get(result["status"], result["status"])
    heading(literal(workspace["case_name"]) + " · " + status + " · revision " + str(workspace["revision"]))
    if speaker:
        paragraph("Declared participant: " + literal(speaker))
    if workspace["historical"]:
        paragraph(f"Historical view. Live case is revision {workspace['live_revision']}. Return to the live question before answering.")
    if result and result.get("request_id"):
        paragraph("Contribution receipt: " + result["request_id"])
    if result and result.get("message"):
        paragraph(literal(result["message"]))
    if result and result.get("failure_category"):
        status = f", HTTP {result['http_status']}" if result.get("http_status") else ""
        paragraph(f"Provider problem ({result['failure_category']}{status}). To resolve: "
                  + FAILURE_HINTS.get(result["failure_category"], FAILURE_HINTS["unknown"]) + ".")
    if result and result.get("recovery_actions"):
        paragraph("Recovery: " + "; ".join(a.replace("_", " ") for a in result["recovery_actions"]) + ". Retry only when explicitly requested.")
    if result and result.get("draft") is not None:
        paragraph("Unretained contribution: " + literal(result["draft"]))
    question = workspace["question"]
    if question:
        data = question["data"]
        heading({"question": "Current question", "recommendation": "Current recommendation", "stop": "Current stop"}[data["kind"]])
        paragraph(literal(data["primary_prompt"]))
        paragraph("Purpose: " + literal(data["purpose"]))
        if data.get("decision"):
            paragraph("Decision: " + literal(data["decision"]))
        if workspace["view"] == "explain":
            heading("Why this question helps · stored explanation")
            paragraph(literal(data["rationale"]))
        for option in data.get("options", []):
            action = option["action"]
            route = "asks consultant" if action["type"] == "consult" else "local"
            paragraph("Stored option (" + route + "): " + literal(option["label"]))
    else:
        heading("Start this case")
        paragraph("What would you like to improve, and what must be protected? Contribute in your own words; unknown details can stay unknown.")
    for breach in workspace.get("breaches") or []:
        paragraph(f"Breach: {literal(breach['measure'])}: {literal(breach['value'])}, outside the bound "
                  f"{literal(breach['bound'])} (test {breach['test_ref']})")
    for notice in workspace.get("notices") or []:
        paragraph(literal(notice["message"]) + " (" + notice["ref"] + ")")
    for review in workspace.get("test_reviews") or []:
        changed = "an earlier version of the goal" if any(f["field"] == "goal_ref" for f in review["flags"]) else \
            "something that has since changed"
        paragraph(f"Review needed: test {review['ref']} " + literal(review["statement"])
                  + f" was planned for {changed}; check it still serves the current goal before the next test.")
    heading("Goal and safeguards")
    if not workspace["goals"]:
        paragraph("No formal goal is recorded yet.")
    for goal in workspace["goals"]:
        for field in ("statement", "scope", "measure", "horizon", "baseline", "protections"):
            paragraph(field.capitalize() + ": " + literal(goal["data"].get(field)))
    backlog = workspace.get("backlog") or []
    if backlog and not workspace["historical"]:
        proposals = [e for e in backlog if e["entry"] == "proposal"]
        reviews = [e for e in backlog if e["entry"] == "review"]
        heading("Waiting for you · not yet in the model" if proposals else "Open reviews")
        shown = backlog if workspace["view"] == "backlog" else backlog[:8]
        for entry in shown:
            if entry["entry"] == "review":
                changes = "; ".join(
                    f"{f['cites']} {'has a new version' if f['change'] == 'new_version' else 'was ' + f['change']}"
                    for f in entry["flags"])
                paragraph(f"Review {entry['ref']}: " + literal(entry["summary"]) + " · stated before " + changes)
                continue
            line = (f"Proposed {TITLES[entry['kind']].lower()} {entry['ref']}: " + literal(entry["summary"])
                    + (" · decide first" if entry["decide_first"] else "")
                    + (" · waits for " + ", ".join(entry["waits_for"]) if entry["waits_for"] else ""))
            paragraph(line)
            if entry["kind"] == "goal" or workspace["view"] == "backlog":
                for field, value in entry["record"]["data"].items():
                    if field not in {"statement", "text"} and value not in (None, []):
                        paragraph("  " + LABELS.get(field, field.replace("_", " ").capitalize()) + ": " + literal(value))
        if len(shown) < len(backlog):
            paragraph(f"And {len(backlog) - len(shown)} more in the backlog.")
        paragraph(f"{len(proposals)} proposals wait and {len(reviews)} records are flagged for review. "
                  + ("Proposals are accepted automatically under this case's setting. "
                     if workspace.get("acceptance") == "automatic" else "")
                  + "Accepting admits a statement to the model; it does not make it true.")
    if workspace["view"] == "history":
        heading("Published history · local")
        for revision in workspace["history"]:
            paragraph(f"Revision {revision['revision']} · {literal(revision['timestamp'])} · parent {revision['parent']}")
            for decision in revision.get("decisions", []):
                verb = {"accept": "accepted", "reject": "rejected", "undo": "undid", "still_holds":
                        "said still holds:", "acceptance": "set acceptance to"}[decision["action"]]
                what = decision.get("value") or ", ".join(decision["refs"])
                paragraph("  " + literal(decision["actor"]) + f" {verb} {what}"
                          + (" (automatically, under the case's setting)" if decision["mode"] == "automatic" else "")
                          + (" · closed " + ", ".join(decision["closes"]) if decision["closes"] else ""))
    elif workspace["view"] == "sources":
        for source in workspace["sources"].values():
            source_details(source)
    elif workspace["view"] == "trees" and not workspace["selection"]:
        from reason_commons.adapters.trees import plain, trees_lines
        drawing = plain(trees_lines(workspace["trees"]))
        lines.extend(["```", drawing.rstrip(), "```", ""] if markdown else [drawing.rstrip(), ""])
    elif workspace["selected_source"]:
        source_details(workspace["selected_source"])
    else:
        for record in workspace["records"]:
            record_details(record)
    if workspace["view"] in {"next", "explain"} and workspace.get("record_count", 0) > len(workspace["records"]) + 1:
        paragraph("Showing the saved question's relevant context. Reasoning and Sources expose the complete retained material.")
    if workspace["uncertainty"]:
        heading("What remains uncertain")
        for item in workspace["uncertainty"]:
            paragraph((item["ref"] + ": " if item["ref"] else "") + literal(item["message"]))
    for comparison in workspace["comparisons"]:
        heading("Original forecast and reported results · " + comparison["test"]["ref"])
        data = comparison["test"]["data"]
        paragraph("Test scope: " + literal(data.get("scope")))
        paragraph(f"Review {literal(data['review_date'])}; no reminder scheduled" if data.get("review_date")
                  else "Review date: unknown")
        paragraph("Stop condition: " + literal(data.get("stop_condition")))
        for field in comparison.get("review_fields") or []:
            paragraph(field["field"].capitalize() + ": " + (literal(field["value"]) if field["value"] else "unknown"))
        forecasts = data.get("forecast") or []
        if markdown and forecasts:
            lines.extend(["| Measure | Original forecast | Reported result |", "| --- | --- | --- |"])
            for forecast in forecasts:
                matching = [r for r in comparison["observations"] if r["data"]["measure"] == forecast.get("measure")]
                lines.append("| " + literal(forecast.get("measure")) + " | " +
                             literal({k: v for k, v in forecast.items() if k != "measure"}).replace("\n", "<br>") +
                             " | " + ("<br>".join(literal(r["data"]).replace("\n", "<br>") for r in matching)
                                      or "No observation recorded") + " |")
            lines.append("")
        for forecast in forecasts:
            if not markdown:
                paragraph("Original forecast: " + literal(forecast))
            matching = [r for r in comparison["observations"] if r["data"]["measure"] == forecast.get("measure")]
            for observation in matching if not markdown else []:
                paragraph("Reported observation " + observation["ref"] + ": " + literal(observation["data"]))
            if not matching and not markdown:
                paragraph("No observation recorded for this measure.")
        for observation in comparison["observations"]:
            if observation["data"]["measure"] not in {f.get("measure") for f in forecasts}:
                paragraph("Additional observation " + observation["ref"] + ": " + literal(observation["data"]))
        paragraph("Matching a measure name does not establish comparable scope, denominators or periods. Assessments are shown as recorded.")
    graph = render_mermaid(workspace)
    if not graph and workspace["view"] == "reasoning":
        heading("Recorded connections")
        paragraph("No connections are recorded yet. The saved wording is shown above.")
    if graph and workspace["view"] not in {"history", "sources", "explain"}:
        heading("Recorded connections")
        if markdown:
            paragraph("```mermaid\n" + graph + "\n```")
        else:
            for edge in workspace["diagram"]["links"]:
                paragraph(f"{edge['from']} -- {edge['label']} --> {edge['to']}")
        paragraph("These labeled connections trace saved records. Full wording, original forecasts and reported results appear above.")
    if workspace["pending_requests"]:
        heading("Retained contributions awaiting resolution")
        for pending in workspace["pending_requests"]:
            value = pending["input"]
            paragraph(value["request_id"] + " · " + literal(value["speaker"]) + " · based on revision " + str(value["base_revision"]))
            paragraph(literal(value["text"]))
            paragraph("Attempt status: " + literal(pending["status"]) + ". Explicit retry uses this retained contribution.")
    if workspace["draft"].get("draft"):
        heading("Retained editor draft")
        paragraph("Declared speaker: " + literal(workspace["draft"].get("speaker")))
        paragraph(literal(workspace["draft"]["draft"]))
    heading("Available next moves")
    for action in workspace["available_actions"]:
        paragraph(literal(action["label"]) + " · " + action["route"].replace("_", " "))
    if not workspace["historical"]:
        paragraph("You can contribute in your own words, inspect locally, or explicitly choose a consultant move.")
    return "\n".join(lines).rstrip() + "\n"


def workspace_output(workspace, result=None, speaker=None):
    return {"workspace": workspace, "rendered": {
        "markdown": render_workspace(workspace, markdown=True, result=result, speaker=speaker),
        "text": render_workspace(workspace, result=result, speaker=speaker),
        "mermaid": render_mermaid(workspace)}}


def render_provider_settings(settings):
    """Plain-text readiness report. Names credential variables, never their values."""
    credential = settings["credential"]
    state = ("set" if credential["present"] else "not set") + (" (required)" if credential["required"] else " (optional)")
    others = ", ".join(p for p in settings["providers"] if p != settings["provider"])
    chosen = {"explicit": "chosen explicitly", "environment": "chosen by REASON_COMMONS_PROVIDER",
              "default": "the default"}[settings["selected_by"]]
    source = {"explicit": "set explicitly", "environment": "from the environment", "default": "default",
              "auto": "selected automatically"}[settings["model_source"]]
    lines = [f"Provider: {settings['provider']} ({chosen})",
             f"Model: {settings['model']} ({source})",
             f"Endpoint: {settings['endpoint'] or 'none (works offline)'}",
             f"Credential: {credential['variable']} {state}" if credential["variable"] else "Credential: none needed"]
    if "max_tokens" in settings:
        lines.append(f"Output: up to {settings['max_tokens']} tokens; effort {settings['effort']}")
    lines.append("Status: " + ("ready (no request was sent to check)" if settings["ready"] else "not ready"))
    lines += [f"  - {problem}" for problem in settings["problems"]]
    lines.append(f"Other providers: {others}")
    return "\n".join(lines) + "\n"
