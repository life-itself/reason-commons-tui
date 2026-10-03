"""Authored evaluation inputs and public-use-case setup, linked to original BDD."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Turn:
    text: str
    speaker: str = "Sam"
    intent: str = "answer"
    declarations: object = None


@dataclass(frozen=True)
class Scenario:
    name: str
    scenarios: tuple
    turns: tuple
    rubric: tuple
    seed: bool = False


SCENARIOS = (
    Scenario("goal_action_review", ("S01", "S02", "S30", "S34", "S101", "S104"), (
        Turn("Late deliveries, changing priorities, overtime, and falling morale."),
        Turn("Success means at least 90% of Payments orders delivered on time by October 30. "
             "We do not know the baseline. Protect acknowledgement of urgent requests: "
             "at least 95% within 24 hours."),
        Turn("Give direct advice on a bounded test: one Payments team uses a daily priority queue "
             "for two weeks. Before starting, predict at least 80% of orders due in that pilot "
             "will be on time and at least 95% of urgent requests acknowledged within 24 hours. "
             "Stop if acknowledgement falls below 95%. Review on October 16. Baseline unknown.",
             intent="direct_advice"),
        Turn("I, Sam, own the pilot and have authority to try it with that team. "
             "The daily queue was implemented as planned. We have not observed results yet.",
             declarations={"ownership": ["Sam"]}),
        Turn("At the two-week review, 40 of 50 Payments pilot orders due were on time. "
             "18 of 20 urgent requests were acknowledged within 24 hours. "
             "Supplier reliability and order mix also changed. Should we expand?",
             intent="explain_observation"),
    ), (
        "First move asks what meaningful success looks like and what must be protected; "
        "it does not substitute ranking problems or presume an agreed goal.",
        "Success, horizon and scope remain sourced; unknown baseline is not invented.",
        "One bounded next move is prominent, with plain decision purpose and alternatives.",
        "The prospective pilot preserves scope, denominators, timing and stop condition.",
        "Action execution is distinguished from attaining an expected result.",
        "Review computes 80% on-time and 90% acknowledgement; the 95% protection breach "
        "is addressed before expansion, while the 90% system goal remains distinct.",
        "Supplier reliability and order mix remain alternatives; improvement is not unique causal proof.",
    )),
    Scenario("attributed_correction", ("S06", "S52"), (
        Turn("Late deliveries, changing priorities, overtime, and falling morale."),
        Turn("Your question is wrong. I do not agree that Sales is the problem. "
             "Rush requests arrive after the schedule is frozen; production then restarts work.", "Priya"),
        Turn("I don't know."),
    ), (
        "Priya's correction is retained with attribution and does not become irrational resistance.",
        "The next question neutrally investigates the reported mechanism without assigning blame.",
        "Uncertainty invites a feasible observation or justified stop, not fabricated evidence or assent.",
    )),
    Scenario("guardrail_review", ("S34", "S35", "S104", "S105"), (
        Turn("At the two-week pilot review, 40 of 50 Payments orders due were delivered on time; "
             "18 of 20 urgent requests were acknowledged within 24 hours. "
             "Supplier reliability improved and order mix changed too. Should we expand?",
             intent="explain_observation"),
    ), (
        "The original 80% pilot prediction is supported on the reported denominator.",
        "90% acknowledgement breaches the original 95% condition; address it before expansion.",
        "Pilot performance does not establish the 90% system goal or unique causality.",
        "Acknowledgement is a proxy; meeting it would not alone prove all critical needs protected.",
    ), seed=True),
    Scenario("inconclusive_review", ("S36",), (
        Turn("The pilot was never started. We have no comparable outcome cohort and do not know "
             "the denominator. Does that contradict the prediction?", intent="explain_observation"),
    ), (
        "Nonimplementation is not a contradicted prediction; unknown comparability is inconclusive.",
        "The original forecast is preserved and the next move resolves the missing implementation/evidence.",
    ), seed=True),
)


SEED_TEXT = ("Our Payments system goal is at least 90% of orders on time by October 30. "
             "We protect at least 95% of urgent acknowledgements within 24 hours. Baseline unknown. "
             "Before starting a two-week one-team priority-queue pilot, we predict at least 80% "
             "of pilot orders due on time and 95% of urgent requests acknowledged within 24 hours. "
             "Stop if acknowledgement falls below 95%; review on October 16.")


class SeedConsultant:
    """Authored setup, clearly distinguished from the evaluated live responses."""
    version = "evaluation-fixture/1"

    def propose(self, request):
        source = [request["input"]["request_id"]]
        return {
            "schema_version": "1", "delivery_profile": "p2",
            "request_id": request["input"]["request_id"],
            "base_revision": request["input"]["base_revision"],
            "intervention": {"kind": "question", "goal_ref": "goal", "purpose": "review_prediction",
                             "primary_prompt": "What happened in the pilot and to the protected condition?",
                             "rationale": "Compare reported outcomes with the original forecast.",
                             "required_context_refs": ["goal", "pilot"]},
            "proposed_updates": [
                {"operation": "record_goal", "temporary_id": "goal", "source_refs": source, "data": {
                    "statement": "At least 90% of orders on time", "scope": "Payments", "horizon": "October 30",
                    "baseline": None, "measure": "on-time orders / orders due",
                    "protections": ["At least 95% of urgent requests acknowledged within 24 hours"]}},
                {"operation": "record_test", "temporary_id": "pilot", "source_refs": source, "data": {
                    "statement": "Daily priority queue with one team for two weeks", "goal_ref": "goal",
                    "scope": "Payments, one team, two weeks", "review_date": "October 16",
                    "stop_condition": "Acknowledgement below 95%",
                    "forecast": [
                        {"measure": "on-time delivery", "expected": "80%", "scope": "Payments pilot",
                         "denominator": "orders due", "period": "two weeks"},
                        {"measure": "urgent acknowledgement within 24 hours", "expected": "95%",
                         "scope": "Payments pilot", "denominator": "urgent requests", "period": "two weeks"}]}},
            ]}


class NoteConsultant:
    """Agent evaluations isolate procedure execution from consulting quality."""
    version = "evaluation-fixture/note=1"

    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    def propose(self, request):
        self.calls += 1
        if self.fail:
            raise ConnectionError("Synthetic unavailable consultant")
        return {"schema_version": "1", "delivery_profile": "p2",
                "request_id": request["input"]["request_id"], "base_revision": request["input"]["base_revision"],
                "intervention": {"kind": "question", "purpose": "next_observation",
                                 "primary_prompt": "What should we observe next?", "rationale": "Keep claims sourced."},
                "proposed_updates": [{"operation": "record_note", "source_refs": [request["input"]["request_id"]],
                                      "data": {"text": request["input"]["text"], "basis": "participant_report"}}]}
