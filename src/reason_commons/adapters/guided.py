"""Deterministic, offline implementation of the Consultant port.

The built-in guide walks one person through the v1 loop (goal, test with an
original forecast, action, observation, review) one short question at a time.
It needs no model or key. Like every consultant, it only proposes: the
application validates and publishes. It records literal participant wording and
never infers measures, ownership, evidence or outcomes.
"""

from copy import deepcopy


PREFIX = "guided:"
SKIPPED = {"", "-", "skip", "n/a", "none", "unknown", "?"}

# Each step: decision title, primary prompt, rationale, and whether an answer is required.
STEPS = {
    "goal": ("Clarify the goal",
             "What do you want to achieve? Describe what would count as better, in your own words.",
             "Everything else (tests, actions, reviews) is judged against the goal. A clear "
             "description of success keeps later steps honest. Unknown details can stay open.", True),
    "goal_measure": ("Clarify the goal",
                     "How will you know it got better? Name a measure, where it stands today, "
                     "and by when you want it. Leave empty if you don't know yet.",
                     "A measure and a starting point make progress visible. Without them, "
                     "a later review can only report impressions.", False),
    "goal_protect": ("Clarify the goal",
                     "What must not get worse while you pursue this? One safeguard per line. "
                     "Leave empty if nothing comes to mind.",
                     "Safeguards protect what you already value. Reviews check them first, "
                     "so a gain bought with hidden damage is caught early.", False),
    "test_change": ("Choose a test",
                    "What small change will you try first? Pick something you can decide and do yourself.",
                    "A small, bounded trial teaches you quickly and cheaply. You can expand "
                    "it once the result supports doing so.", True),
    "test_forecast": ("Choose a test",
                      "What do you predict will happen if you make this change? Be concrete, "
                      "with a number if you can.",
                      "The original forecast is saved before any result exists and never changes. "
                      "Comparing it with what happens later is how you learn rather than "
                      "rationalize.", True),
    "test_review": ("Choose a test",
                    "When will you look at the result? A date or a period is enough. Leave empty to decide later.",
                    "A review date keeps the test from quietly running forever.", False),
    "test_stop": ("Choose a test",
                  "What would make you stop the test early? Leave empty if nothing would.",
                  "A stop condition decided in advance protects your safeguards when a test goes badly.", False),
    "action": ("Plan the next action",
               "What exactly is the next action, and when will it happen?",
               "A test only teaches you something once it is carried out. Naming one concrete "
               "action makes it easy to start.", True),
    "observe": ("Observe the result",
                "What actually happened? Report what you did and what you observed, with numbers "
                "and the period if you have them.",
                "Doing the work is not the same as it working. Write down what you observed, "
                "separately from what you hoped.", True),
    "review": ("Review against the forecast",
               "How does what happened compare with your original forecast? Check your safeguards first. "
               "Then decide: keep, adjust or drop the change?",
               "Comparing the result with the original forecast, and checking the safeguards, "
               "tells you whether to keep, adjust or drop the change.", True),
}


def _literal(text):
    value = (text or "").strip()
    return None if value.lower() in SKIPPED else value


class GuidedConsultant:
    """Offline step-by-step guide; selected explicitly as provider 'guided'."""

    version = "guided/1"

    def propose(self, request):
        value = request["input"]
        case = request["case"]
        sources = request["sources"]
        records = {r["ref"]: r for r in case["records"]}
        current = records.get(case["current_intervention"])
        step, inferred = self._step(current, records)
        answer = _literal(value["text"])
        request_id = value["request_id"]
        updates, context = [], {}
        # The change being forecast, so the next questions can show it: it is not a record until the test is.
        change = answer if step == "test_change" else (self._answer(case, sources, records, "test_change")
                                                       or (None, None))[1]

        if inferred and step in ("goal", "test_change"):
            # The last question came from another consultant. Keep the words; start the step cleanly.
            if answer:
                updates.append(self._note(value["text"], [request_id]))
            return self._proposal(value, updates, step, self._context(records), change=change,
                                  notice="The built-in guide continues from here. Your last answer is saved as a note.")

        if value["intent"] != "answer":
            # Advice and reformulation need a model; keep the person's words and the step.
            if answer:
                updates.append(self._note(value["text"], [request_id]))
            return self._proposal(value, updates, step, self._context(records), change=change, notice=(
                "The built-in guide cannot give advice or rephrase questions. Your note is saved. "
                "Choose Anthropic or LM Studio under Actions for an AI consultant."))

        notice = None
        if step == "goal":
            next_step = "goal_measure" if answer else "goal"
            notice = None if answer else "Please describe the goal in at least a few words."
        elif step == "goal_measure":
            next_step = "goal_protect"
        elif step == "goal_protect":
            statement = self._answer(case, sources, records, "goal")
            measure = self._answer(case, sources, records, "goal_measure")
            if statement is None:
                next_step = "goal"
            else:
                protections = [line.strip(" -*\t") for line in (answer or "").splitlines()
                               if _literal(line.strip(" -*\t"))]
                updates.append({"operation": "record_goal", "temporary_id": "goal", "data": {
                    "statement": statement[1], "measure": measure[1] if measure else None,
                    "protections": protections},
                    "source_refs": self._refs(statement, measure, request_id)})
                context["goal"] = "goal"
                next_step = "test_change"
        elif step == "test_change":
            next_step = "test_forecast" if answer else "test_change"
            notice = None if answer else "Please describe the change you want to try."
        elif step == "test_forecast":
            next_step = "test_review" if answer else "test_forecast"
            notice = None if answer else "A test needs a forecast, written before you start."
        elif step == "test_review":
            next_step = "test_stop"
        elif step == "test_stop":
            goal = self._latest(records, "goal")
            change = self._answer(case, sources, records, "test_change")
            forecast = self._answer(case, sources, records, "test_forecast")
            review = self._answer(case, sources, records, "test_review")
            if goal is None or change is None or forecast is None:
                next_step = "goal" if goal is None else "test_change"
            else:
                updates.append({"operation": "record_test", "temporary_id": "test", "data": {
                    "statement": change[1], "goal_ref": goal["ref"], "scope": None,
                    "forecast": [{"measure": goal["data"].get("measure") or "Result",
                                  "expected": forecast[1], "scope": None, "denominator": None}],
                    "stop_condition": answer, "review_date": review[1] if review else None},
                    "source_refs": self._refs(change, forecast, review, request_id)})
                context["test"] = "test"
                next_step = "action"
        elif step == "action":
            test = self._latest(records, "test")
            if answer and test:
                updates.append({"operation": "record_action", "temporary_id": "action", "data": {
                    "statement": answer, "test_ref": test["ref"], "execution": "planned",
                    "expected_state_attainment": "unknown"}, "source_refs": [request_id]})
                context["action"] = "action"
            next_step = "observe" if answer and test else "test_change" if not test else "action"
        elif step == "observe":
            test = self._latest(records, "test")
            if answer and test:
                measure = (test["data"].get("forecast") or [{}])[0].get("measure") or "Result"
                updates.append({"operation": "record_observation", "temporary_id": "observation", "data": {
                    "test_ref": test["ref"], "measure": measure, "value": answer,
                    "basis": "participant_report"}, "source_refs": [request_id]})
                context["observation"] = "observation"
            next_step = "review" if answer and test else "test_change" if not test else "observe"
        else:  # review
            test = self._latest(records, "test")
            observations = [r["ref"] for r in records.values()
                            if r["kind"] == "observation" and test and r["data"]["test_ref"] == test["ref"]]
            if answer and test:
                updates.append({"operation": "record_review", "temporary_id": "review", "data": {
                    "test_ref": test["ref"], "observation_refs": observations, "assessment": answer,
                    "goal_ref": test["data"]["goal_ref"]}, "source_refs": [request_id]})
                next_step = "test_change"
            else:
                next_step = "test_change" if not test else "review"
        return self._proposal(value, updates, next_step, self._context(records, context), notice,
                              change=change, after_review=step == "review" and bool(answer))

    def _step(self, current, records):
        """Return (step, inferred). The empty case's welcome question asks for the goal."""
        if current is None and not records:
            return "goal", False
        purpose = (current or {}).get("data", {}).get("purpose", "")
        if purpose.startswith(PREFIX) and purpose[len(PREFIX):] in STEPS:
            return purpose[len(PREFIX):], False
        return self._infer(records), True

    def _infer(self, records):
        # Another consultant asked last: continue from the recorded state.
        goal, test = self._latest(records, "goal"), self._latest(records, "test")
        if goal is None:
            return "goal"
        related = lambda kind: [r for r in records.values() if r["kind"] == kind and test
                                and r["data"].get("test_ref") == test["ref"]]
        if test is None or related("review"):
            return "test_change"
        if not related("action"):
            return "action"
        return "review" if related("observation") else "observe"

    @staticmethod
    def _latest(records, kind):
        matches = [r for r in records.values() if r["kind"] == kind]
        return max(matches, key=lambda r: int(r["ref"][1:].split("@")[0])) if matches else None

    @staticmethod
    def _answer(case, sources, records, step):
        """Latest applied (request_id, literal text) that answered a guided step."""
        for request_id in reversed(case["source_input_refs"]):
            source = sources.get(request_id, {})
            target = records.get(source.get("response_target"))
            purpose = target["data"].get("purpose") if target else (
                PREFIX + "goal" if source.get("response_target") is None else None)
            if purpose == PREFIX + step:
                text = _literal(source.get("text"))
                return (request_id, text) if text else None
        return None

    @staticmethod
    def _refs(*items):
        refs = []
        for item in items:
            ref = item[0] if isinstance(item, tuple) else item
            if ref and ref not in refs:
                refs.append(ref)
        return refs

    @staticmethod
    def _note(text, refs):
        return {"operation": "record_note", "temporary_id": "temp_note",
                "data": {"text": text, "basis": "participant_report"}, "source_refs": refs}

    def _context(self, records, new=None):
        refs = []
        for kind in ("goal", "test", "action", "observation"):
            if new and kind in new:
                refs.append(new[kind])
                continue
            latest = self._latest(records, kind)
            if latest is None:
                continue
            test = self._latest(records, "test")
            if kind in ("action", "observation") and new and "test" in new:
                continue
            if kind in ("action", "observation") and (test is None or latest["data"].get("test_ref") != test["ref"]):
                continue
            if kind == "test" and new and "goal" in new:
                continue
            refs.append(latest["ref"])
        return refs

    def _proposal(self, value, updates, step, context, notice=None, change=None, after_review=False):
        decision, prompt, rationale, _ = STEPS[step]
        if change and step in ("test_forecast", "test_review", "test_stop"):
            prompt = f"Your change: \"{' '.join(change.split())}\" {prompt}"
        if after_review and step == "test_change":
            prompt = ("Review saved. What is the next small change you want to try? It can be the same "
                      "change, adjusted. If the goal is met, you can stop here.")
        if notice:
            prompt = notice + " " + prompt
        intervention = {"kind": "question", "purpose": PREFIX + step, "decision": decision,
                        "primary_prompt": prompt, "rationale": rationale,
                        "required_context_refs": context,
                        "options": [{"id": "goal", "label": "Goal", "action": {"type": "view", "target": "goal"}},
                                    {"id": "sources", "label": "Your words",
                                     "action": {"type": "view", "target": "sources"}}]}
        goal = next((r for r in context if r == "goal" or r.startswith("G")), None)
        if goal:
            intervention["goal_ref"] = goal
        return {"schema_version": "1", "delivery_profile": "p2", "request_id": value["request_id"],
                "base_revision": value["base_revision"], "intervention": intervention,
                "proposed_updates": deepcopy(updates)}
