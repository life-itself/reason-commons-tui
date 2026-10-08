"""The system's reply to one turn, in plain words: what it asked or recommended, and what it recorded.

A reply is the records it added: one intervention (the next question, recommendation or stop) and the notes, goal,
trial, action, result, review and diagram statements it recorded. Each recorded item says where it came from (whose
words in which turn), and a reference to an earlier item is given as that item's words. The labels are the reviewer's
words, not the method's ("as a problem", not "undesirable effect"); the system's own wording stays as written and is
marked as its own. Where that wording cites an item by its code (as in "the forecast in P1@1"), what the code names
follows in brackets, so the reviewer reads what the person saw and can still follow it.
"""

import re

BASIS = {"participant_report": "Recorded as something a person said (not checked)",
         "hypothesis": "Recorded as a possibility, not a fact",
         "observed": "Recorded as something observed"}
EXECUTION = {"unknown": "not known", "planned": "not yet, planned", "completed": "yes", "blocked": "no, blocked"}
ATTAINMENT = {"unknown": "not known yet", "pending": "not known yet", "met": "yes", "not_met": "no"}
ASKS = {"question": "asks", "recommendation": "recommends", "stop": "suggests stopping here"}
CODE = re.compile(r"\b[A-Z]\d+@\d+\b")
KIND_NAMES = {"goal": "the goal", "note": "the note", "test": "the trial", "action": "the action",
              "observation": "the result", "review": "the review", "intervention": "the system's earlier question",
              "claim": "the diagram statement", "link": "the link", "retraction": "the withdrawal"}
MOVE_NAMES = {"question": "the system's earlier question", "recommendation": "the system's earlier recommendation",
              "stop": "the system's earlier suggestion to stop"}
SHORT = 90  # a named item longer than this is cut, so a bracket never buries the sentence it explains
TREE_NAMES = {"goal": "the goal diagram", "current_reality": "the diagram of what is going wrong now",
              "conflict": "the conflict diagram", "future_reality": "the diagram of what should happen if they act",
              "prerequisite": "the diagram of obstacles and first steps", "transition": "the action-plan diagram"}
ROLES = {"goal": "the goal", "critical_success_factor": "something the goal needs",
         "necessary_condition": "something the goal needs", "undesirable_effect": "a problem",
         "intermediate_cause": "a cause", "root_cause": "an underlying cause",
         "critical_root_cause": "the main underlying cause", "cloud_objective": "the aim both sides share",
         "cloud_requirement": "a need", "cloud_prerequisite": "an action one side thinks it must take",
         "injection": "a proposed change", "desired_effect": "a hoped-for result",
         "implementation_objective": "an aim", "obstacle": "an obstacle", "intermediate_objective": "a step",
         "transition_existing_reality": "where things start", "transition_need": "why something must change",
         "transition_action": "an action", "transition_expected_effect": "what should then be seen",
         "observation": "an observation", "evidence": "evidence"}
ROLE_WORDS = {key: value.split(" ", 1)[1] if value.startswith(("a ", "an ", "the ")) else value
              for key, value in ROLES.items()}
RELATIONS = {"necessary_for": "is needed for", "causes": "causes", "contributes_to": "contributes to",
             "conflicts_with": "conflicts with", "requires": "requires", "satisfies": "meets",
             "overcomes": "overcomes", "precedes": "comes before", "produces": "leads to",
             "invalidates_assumption": "breaks an assumption behind", "implements": "carries out",
             "supersedes": "replaces", "supports": "supports", "challenges": "challenges", "refines": "refines",
             "enables": "makes possible"}


def base(ref):
    return ref.split("@")[0] if isinstance(ref, str) else ref


class Names:
    """What each earlier record says, to name it in place of its code."""

    def __init__(self, records):
        self.records = {}
        self.add(records)

    def add(self, records):
        for record in records:
            self.records[base(record["ref"])] = record

    def __call__(self, ref, short=False):
        record = self.records.get(base(ref))
        if not record:
            return "an earlier item"
        data = record["data"]
        if record["kind"] == "link":
            return f"from {self(data['from_ref'], short)} to {self(data['to_ref'], short)}"
        text = data.get("statement") or data.get("text") or data.get("primary_prompt") or data.get("measure")
        if not text:
            return "an earlier item"
        # A named item's own codes become what they are ("the goal"), so no unexplained code is left inside it.
        text = CODE.sub(lambda m: self.kind(m.group(0)), text)
        if short and len(text) > SHORT:
            text = text[:SHORT].rsplit(" ", 1)[0] + "…"
        return f"“{text}”"

    def kind(self, ref):
        record = self.records.get(base(ref))
        if not record:
            return "an earlier item"
        if record["kind"] == "intervention":
            return MOVE_NAMES.get(record["data"].get("kind"), KIND_NAMES["intervention"])
        return KIND_NAMES.get(record["kind"], "an item")

    def explain(self, text, seen=None):
        """The text as written, with what each record code in it names added in brackets: in full the first time
        in a reply (``seen`` holds the codes already explained), then by kind alone."""
        seen = set() if seen is None else seen

        def name(match):
            record = self.records.get(base(match.group(0)))
            if not record:
                return match.group(0)
            if base(match.group(0)) in seen:
                return f"{match.group(0)} [{self.kind(match.group(0))}]"
            seen.add(base(match.group(0)))
            named = f"{self.kind(match.group(0))} {self(match.group(0), short=True)}"
            details = [record["data"].get(key) for key in ("scope", "horizon")] if record["kind"] == "goal" else []
            if any(details):
                named += " (" + ", ".join(str(d) for d in details if d) + ")"
            protections = record["data"].get("protections") if record["kind"] == "goal" else None
            if protections:
                named += ", which also protects " + "; ".join(f"“{p}”" for p in protections)
            return f"{match.group(0)} [{named}]"
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
        parts.append(f"counted out of {item['denominator']}")
    for key in ("scope", "period", "bound"):
        if item.get(key):
            parts.append(str(item[key]))
    return ", ".join(parts)


def recorded_item(record, names):
    """(headline, detail lines) for one recorded item."""
    kind, data = record["kind"], record["data"]
    newer = " (a new wording of an earlier one)" if data.get("replaces") else ""
    basis = [BASIS[data["basis"]]] if data.get("basis") in BASIS else []
    if kind == "note":
        return f"A note: “{data['text']}”", basis
    if kind == "goal":
        return f"The goal{newer}: “{data['statement']}”", [
            f"Covers (the system's word: scope): {show(data.get('scope'))}",
            f"Deadline (horizon): {show(data.get('horizon'))}",
            f"Measured by (measure): {show(data.get('measure'))}",
            f"Where things stand now (baseline): {show(data.get('baseline'), 'unknown')}",
            f"Must not get worse (protections): {show(data.get('protections'), 'nothing said')}"]
    if kind == "test":
        lines = [f"Covers (scope): {show(data.get('scope'))}"]
        lines += [f"Prediction (forecast): {forecast_line(f)}" for f in data.get("forecast") or []] or [
            "Prediction (forecast): not said"]
        lines += [f"Stop if (stop condition): {show(data.get('stop_condition'))}",
                  f"Review on: {show(data.get('review_date'))}"]
        for key, label in (("baseline", "Where things stood before (baseline)"), ("dose", "How much of the change"),
                           ("alternative_explanation", "Another possible explanation")):
            if data.get(key):
                lines.append(f"{label}: {data[key]}")
        if data.get("goal_ref"):
            lines.append(f"Serves the goal {names(data['goal_ref'])}")
        return f"A trial{newer}: “{data['statement']}”", lines
    if kind == "action":
        lines = [f"Part of the trial {names(data['test_ref'])}", f"Who will do it: {show(data.get('owner'))}",
                 f"Who may approve it: {show(data.get('authority'))}",
                 f"Done yet: {EXECUTION.get(data.get('execution'), show(data.get('execution'), 'not known'))}"]
        if data.get("expected_state"):
            lines.append(f"What it should lead to: {data['expected_state']}")
        if data.get("expected_state_attainment"):
            lines.append("Has it had the effect it should have: "
                         + ATTAINMENT.get(data["expected_state_attainment"], "not known yet"))
        return f"An action{newer}: “{data['statement']}”", lines
    if kind == "observation":
        lines = [f"For the trial {names(data['test_ref'])}"]
        lines += [f"{label}: {data[key]}" for key, label in (("denominator", "Counted out of"), ("scope", "Covers"),
                                                             ("period", "Period")) if data.get(key)]
        return f"A result: {data['measure']} = {data['value']}", lines + basis
    if kind == "review":
        lines = [f"Of the trial {names(data['test_ref'])}"]
        if data.get("next_decision"):
            lines.append(f"The system's suggested next decision: {data['next_decision']}")
        return f"A review of the trial's results, in the system's words: “{data['assessment']}”", lines
    if kind == "claim":
        role = ROLE_WORDS.get(data["role"], data["role"].replace("_", " "))
        where = TREE_NAMES.get(data["tree"], data["tree"])
        return f"Added to {where}{newer}, with the system's label “{role}”: “{data['statement']}”", basis
    if kind == "link":
        start, end = names.tree(data["from_ref"]), names.tree(data["to_ref"])
        where = lambda tree: f" (in {TREE_NAMES[tree]})" if tree in TREE_NAMES and tree != data["tree"] else ""
        relation = RELATIONS.get(data["relation"], data["relation"].replace("_", " "))
        line = (f"The system's note on this link: {data['assumption']}" if data.get("assumption")
                else "The system gave no note on this link")
        return (f"Linked in {TREE_NAMES.get(data['tree'], data['tree'])}: {names(data['from_ref'])}{where(start)} "
                f"{relation} {names(data['to_ref'])}{where(end)}", [line])
    if kind == "retraction":
        return f"Withdrew {names(data['target_ref'])}", [f"Reason: {data['reason']}"]
    return f"Recorded a {kind}", []


def plain_reply(records, names, source_of, consultant):
    """The reply's parts: [{"kind": "move"|"recorded", "headline", "lines", "source"}], the move first."""
    parts = []
    for record in records:
        if record["kind"] == "intervention":
            data = record["data"]
            lines = []
            if data.get("decision"):
                lines.append(f"What it is helping decide: {data['decision']}")
            if data.get("rationale"):
                lines.append(f"Its reasons, in its own words: {data['rationale']}")
            options = [option.get("label") if isinstance(option, dict) else str(option)
                       for option in data.get("options") or []]
            if options:
                lines.append("Other choices it offered, as buttons on the person's screen: " + "; ".join(options))
            parts.insert(0, {"record": record, "lines": lines})
        else:
            parts.append({"record": record})
    seen = set()  # each code is explained in full once per reply, in reading order
    out = []
    for part in parts:
        record = part["record"]
        if record["kind"] == "intervention":
            data = record["data"]
            out.append({"kind": "move", "headline": f"{consultant} {ASKS.get(data['kind'], 'says')}: "
                                                    f"{names.explain(data['primary_prompt'], seen)}",
                        "lines": [names.explain(line, seen) for line in part["lines"]], "source": ""})
        else:
            headline, lines = recorded_item(record, names)
            out.append({"kind": "recorded", "headline": names.explain(headline, seen),
                        "lines": [names.explain(line, seen) for line in lines],
                        "source": source_of(record.get("source_refs") or [])})
    return out


# Words the system uses in its own replies, explained where a reply uses them.
GLOSSARY = (
    (r"\bthe case\b", "case", "everything the system has recorded in this conversation (it also calls this the "
                             "model)"),
    (r"\bthe model\b", "the model", "everything the system has recorded in this conversation (not the AI model)"),
    (r"\b(next|later|this|the|one) moves?\b", "move", "the system's next question or suggested step"),
    (r"\battributed\b", "attributed", "marked with who said it"),
    (r"\bprovisional\b", "provisional", "a first draft, not settled"),
    (r"\bqualitative\b", "qualitative", "described in words, not numbers"),
    (r"\bpilot\b", "pilot", "the trial"),
    (r"\b(the|this|a) test\b", "test", "the trial"),
    (r"\bforecast", "forecast", "the prediction"),
    (r"\bhorizon\b", "horizon", "the deadline"),
    (r"\bbaseline\b", "baseline", "where things stood before a change"),
    (r"\bscope\b", "scope", "what something covers"),
    (r"\bdenominators?\b", "denominator", "the number something is counted out of (in “40 of 50”, it is 50)"),
    (r"\bprotect(ion|ed)", "protection", "something that must be kept up while trying a change, such as a minimum "
                                          "that must not be missed"),
    (r"\bguardrail", "guardrail", "something that must not get worse while trying a change"),
    (r"\bstop condition\b", "stop condition", "the rule for when a trial is meant to stop; \"breached\" means that "
                                               "point was reached"),
    (r"\bsystem goal\b", "system goal", "the goal for the whole business unit (not a goal of the AI)"),
    (r"\bfrozen\b", "frozen", "fixed, no longer supposed to change"),
    (r"\b(decision )?authority\b", "authority", "who is allowed to decide"),
    (r"\bpremise\b", "premise", "what a question takes for granted"),
    (r"\bmechanism\b", "mechanism", "how something actually happens, step by step"),
    (r"\bparticipants?\b", "participant", "a person in the conversation"),
    (r"\bconstraint\b", "constraint", "the one thing that limits progress most"),
    (r"\bproxy\b", "proxy", "something measured in place of what really matters"),
    (r"\bbound\b", "bound", "a limit that must not be crossed"),
    (r"\bsourced\b", "sourced", "linked to the message it came from"),
    (r"\bdomain\b", "domain", "the system's built-in knowledge of this kind of work"),
)


def words_in(parts):
    """The system's own words in a reply that the page explains, in the order the glossary lists them."""
    text = " ".join([p["headline"] for p in parts] + [line for p in parts for line in p["lines"]])
    return [(word, meaning) for pattern, word, meaning in GLOSSARY if re.search(pattern, text, re.IGNORECASE)]
