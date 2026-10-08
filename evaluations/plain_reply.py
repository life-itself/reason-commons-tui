"""The assistant's reply to one turn, in plain words: what it asked or recommended, and what it saved.

A reply is the records it added: one intervention (the next question, recommendation or stop) and the notes, goal,
test, action, result, review and diagram statements it saved. Each saved item says where it came from (whose words in
which turn), and a reference to an earlier item is given as that item's words. Where the assistant's own wording cites
an item by its code (as in "the forecast in P1@1"), the words stay as written and what the code names follows in
brackets, so the reviewer reads what the person saw and can still follow it.
"""

import re

from reason_commons.adapters.trees import FROM_SIDE, ROLE_LABELS

BASIS = {"participant_report": "as reported", "hypothesis": "as a possibility, not a fact",
         "observed": "as an observed fact"}
EXECUTION = {"unknown": "not known", "planned": "planned", "completed": "done", "blocked": "blocked"}
ATTAINMENT = {"unknown": "not known yet", "pending": "not known yet", "met": "reached", "not_met": "not reached"}
ASKS = {"question": "asks", "recommendation": "recommends", "stop": "suggests stopping"}
CODE = re.compile(r"\b[A-Z]\d+@\d+\b")
KIND_NAMES = {"goal": "the goal", "note": "the note", "test": "the trial", "action": "the action",
              "observation": "the result", "review": "the review", "intervention": "the earlier question",
              "claim": "the diagram statement", "link": "the link", "retraction": "the withdrawal"}
TREE_NAMES = {"goal": "the goal diagram", "current_reality": "the diagram of what is going wrong now",
              "conflict": "the conflict diagram", "future_reality": "the diagram of what should happen if they act",
              "prerequisite": "the diagram of obstacles and first steps", "transition": "the action-plan diagram"}


def base(ref):
    return ref.split("@")[0] if isinstance(ref, str) else ref


class Names:
    """What each earlier record says, to name it in place of its ID."""

    def __init__(self, records):
        self.records = {}
        for record in records:
            self.records[base(record["ref"])] = record

    def add(self, records):
        for record in records:
            self.records[base(record["ref"])] = record

    def __call__(self, ref):
        record = self.records.get(base(ref))
        if not record:
            return "an earlier item"
        data = record["data"]
        text = data.get("statement") or data.get("text") or data.get("primary_prompt") or data.get("measure")
        return f"“{text}”" if text else "an earlier item"

    def explain(self, text):
        """The text as written, with what each record code in it names added in brackets."""
        def name(match):
            record = self.records.get(base(match.group(0)))
            if not record:
                return match.group(0)
            return f"{match.group(0)} [{KIND_NAMES.get(record['kind'], 'an item')} {self(match.group(0))}]"
        return CODE.sub(name, text) if isinstance(text, str) else text

    def tree(self, ref):
        record = self.records.get(base(ref))
        return (record or {}).get("data", {}).get("tree") or ("goal" if (record or {}).get("kind") == "goal" else None)


def unknown(value):
    return value in (None, "", "unknown", "Unknown") or (isinstance(value, list) and not value)


def show(value, missing="not said"):
    if unknown(value):
        return missing
    return "; ".join(map(str, value)) if isinstance(value, list) else str(value)


def forecast_line(item):
    parts = [f"{item.get('measure')}: {item.get('expected')}"]
    if item.get("denominator"):
        parts.append(f"out of {item['denominator']}")
    for key in ("scope", "period", "bound"):
        if item.get(key):
            parts.append(str(item[key]))
    return ", ".join(parts)


def saved_item(record, names):
    """(headline, detail lines) for one saved record."""
    kind, data = record["kind"], record["data"]
    newer = " (a new wording of an earlier item)" if data.get("replaces") else ""
    if kind == "note":
        return f"A note: “{data['text']}”", [f"Saved {BASIS[data['basis']]}"] if data.get("basis") else []
    if kind == "goal":
        return f"The goal{newer}: “{data['statement']}”", [
            f"For: {show(data.get('scope'))}", f"By: {show(data.get('horizon'))}",
            f"Measured by: {show(data.get('measure'))}", f"Starting point: {show(data.get('baseline'), 'unknown')}",
            f"Must be protected: {show(data.get('protections'), 'nothing said')}"]
    if kind == "test":
        lines = [f"Covers: {show(data.get('scope'))}"]
        lines += [f"Prediction: {forecast_line(f)}" for f in data.get("forecast") or []] or ["Prediction: not said"]
        lines += [f"Stop if: {show(data.get('stop_condition'))}", f"Review on: {show(data.get('review_date'))}"]
        for key, label in (("baseline", "Starting point"), ("dose", "How much of the change"),
                           ("alternative_explanation", "Another possible explanation")):
            if data.get(key):
                lines.append(f"{label}: {data[key]}")
        if data.get("goal_ref"):
            lines.append(f"Serves the goal {names(data['goal_ref'])}")
        return f"A trial{newer}: “{data['statement']}”", lines
    if kind == "action":
        lines = [f"For the trial {names(data['test_ref'])}", f"Who: {show(data.get('owner'))}",
                 f"Who may approve it: {show(data.get('authority'))}",
                 f"Status: {EXECUTION.get(data.get('execution'), show(data.get('execution'), 'not known'))}"]
        if data.get("expected_state"):
            lines.append(f"Expected result: {data['expected_state']}")
        if data.get("expected_state_attainment"):
            lines.append(f"Expected result reached: {ATTAINMENT.get(data['expected_state_attainment'])}")
        return f"An action{newer}: “{data['statement']}”", lines
    if kind == "observation":
        lines = [f"For the trial {names(data['test_ref'])}"]
        lines += [f"{label}: {data[key]}" for key, label in (("denominator", "Out of"), ("scope", "Covers"),
                                                             ("period", "Period")) if data.get(key)]
        if data.get("basis"):
            lines.append(f"Saved {BASIS[data['basis']]}")
        return f"A result: {data['measure']} = {data['value']}", lines
    if kind == "review":
        lines = [f"Of the trial {names(data['test_ref'])}"]
        if data.get("next_decision"):
            lines.append(f"Next decision: {data['next_decision']}")
        return f"A review of the trial's results: “{data['assessment']}”", lines
    if kind == "claim":
        role = ROLE_LABELS.get(data["role"], data["role"]).lower()
        lines = [f"As: {role}"] + ([f"Saved {BASIS[data['basis']]}"] if data.get("basis") else [])
        return f"Added to {TREE_NAMES.get(data['tree'], data['tree'])}{newer}: “{data['statement']}”", lines
    if kind == "link":
        start, end = names.tree(data["from_ref"]), names.tree(data["to_ref"])
        where = lambda tree: f" (in {TREE_NAMES[tree]})" if tree in TREE_NAMES and tree != data["tree"] else ""
        lines = [f"In {TREE_NAMES.get(data['tree'], data['tree'])}"]
        lines.append(f"Assumption: {data['assumption']}" if data.get("assumption") else "Assumption: none stated")
        relation = FROM_SIDE.get(data["relation"], data["relation"].replace("_", " "))
        return (f"A link: {names(data['from_ref'])}{where(start)} {relation} {names(data['to_ref'])}{where(end)}",
                lines)
    if kind == "retraction":
        return f"Withdrew {names(data['target_ref'])}", [f"Reason: {data['reason']}"]
    return f"Saved a {kind}", []


def plain_reply(records, names, source_of, consultant):
    """The reply's parts: [{"kind": "move"|"saved", "headline", "lines", "source"}], the move first."""
    parts = []
    for record in records:
        if record["kind"] == "intervention":
            data = record["data"]
            lines = []
            if data.get("decision"):
                lines.append(f"What it is deciding: {data['decision']}")
            if data.get("rationale"):
                lines.append(f"Why: {data['rationale']}")
            lines += [f"Another option: {option.get('label') or option}" if isinstance(option, dict)
                      else f"Another option: {option}" for option in data.get("options") or []]
            parts.insert(0, {"kind": "move", "headline": f"{consultant} {ASKS.get(data['kind'], 'says')}: "
                                                         f"{names.explain(data['primary_prompt'])}",
                             "lines": [names.explain(line) for line in lines], "source": ""})
        else:
            headline, lines = saved_item(record, names)
            parts.append({"kind": "saved", "headline": names.explain(headline),
                          "lines": [names.explain(line) for line in lines],
                          "source": source_of(record.get("source_refs") or [])})
    return parts
