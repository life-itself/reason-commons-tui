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
    heading("Goal and safeguards")
    if not workspace["goals"]:
        paragraph("No formal goal is recorded yet.")
    for goal in workspace["goals"]:
        for field in ("statement", "scope", "measure", "horizon", "baseline", "protections"):
            paragraph(field.capitalize() + ": " + literal(goal["data"].get(field)))
    if workspace["view"] == "history":
        heading("Published history · local")
        for revision in workspace["history"]:
            paragraph(f"Revision {revision['revision']} · {literal(revision['timestamp'])} · parent {revision['parent']}")
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
        paragraph("Test scope: " + literal(data.get("scope")) + "; review date: " + literal(data.get("review_date")))
        paragraph("Stop condition: " + literal(data.get("stop_condition")))
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
