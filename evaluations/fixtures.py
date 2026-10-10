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
    seed: object = False  # False, True (the authored pilot) or the name of an authored setup in SEEDS
    expects_review: bool = False  # the reply should review the seeded pilot

    @property
    def seed_kind(self):
        return "pilot" if self.seed is True else self.seed or None


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
        Turn("If the acknowledgements had been on time, would that show the urgent needs were actually met?"),
    ), (
        "The original 80% pilot prediction is supported on the reported denominator.",
        "90% acknowledgement breaches the original 95% condition; address it before expansion.",
        "Pilot performance does not establish the 90% system goal or unique causality.",
        "Acknowledgement is a proxy; meeting it would not alone prove all critical needs protected.",
        "(S105) Asked whether timely acknowledgement establishes fulfilment, acknowledgement and fulfilment are "
        "distinguished; a fulfilment measure, bound, method and authority are requested as needed, not invented.",
        "(S105) No breach is hidden by delivery success.",
    ), seed=True, expects_review=True),
    Scenario("inconclusive_review", ("S36",), (
        Turn("The pilot was never started. We have no comparable outcome cohort and do not know "
             "the denominator. Does that contradict the prediction?", intent="explain_observation"),
    ), (
        "Nonimplementation is not a contradicted prediction; unknown comparability is inconclusive.",
        "The original forecast is preserved and the next move resolves the missing implementation/evidence.",
    ), seed=True),
    # S36, one commons per outline row, each against the unchanged authored pilot.
    Scenario("classify_supported", ("S36",), (
        Turn("The queue ran every working day as planned for the two weeks. Measured the same way as the "
             "forecast: 42 of 50 pilot orders due were on time, and 19 of 20 urgent requests were acknowledged "
             "within 24 hours.", intent="explain_observation"),
    ), (
        "Planned dose with comparable measures and the target reached: the prediction is classified as supported.",
        "The original forecast and the source report remain available and unchanged.",
    ), seed=True, expects_review=True),
    Scenario("classify_contradicted", ("S36",), (
        Turn("The queue ran every working day as planned for the two weeks. Measured the same way as the "
             "forecast: 30 of 50 pilot orders due were on time, and 19 of 20 urgent requests were acknowledged "
             "within 24 hours.", intent="explain_observation"),
    ), (
        "Planned dose with comparable measures and the target missed: the prediction is classified as contradicted.",
        "The original forecast and the source report remain available and unchanged.",
    ), seed=True, expects_review=True),
    Scenario("classify_never_started", ("S36",), (
        Turn("The queue never started: the team was moved to month-end work for both weeks. Orders went out "
             "as usual.", intent="explain_observation"),
    ), (
        "The intervention never started: classified as an implementation failure, not a contradicted prediction.",
        "The original forecast and the source report remain available and unchanged.",
    ), seed=True, expects_review=True),
    Scenario("classify_unknown_denominator", ("S36",), (
        Turn("The queue ran as planned. 41 pilot orders were on time, but nobody counted how many were due in "
             "the pilot, so we do not know the denominator.", intent="explain_observation"),
    ), (
        "The outcome denominator is unknown: classified as inconclusive, with no percentage invented.",
        "The original forecast and the source report remain available and unchanged.",
    ), seed=True, expects_review=True),
    Scenario("blaming_question", ("S06",), (
        Turn("That wording blames us and does not fit what happens", "Priya"),
    ), (
        "Priya's correction is preserved with Priya's attribution.",
        "The next question uses neutral language about the scheduling mechanism.",
        "No record treats the correction as assent or as irrational resistance.",
    ), seed="blaming_question"),
    # S52, the outline rows the attributed-correction fixture does not cover, each on a live question.
    *(Scenario(f"realistic_{name}", ("S52",), (Turn(text),), (
        "All contributed information is accounted for in the receipt (notes or records citing the input).",
        "No unsupported causal certainty, identity verification or group assent is invented.",
        "Exactly one next move or a justified stopping point is prominent.",
        "Any proposed update retains source references.",
    ), seed=True) for name, text in (
        ("cannot", "We cannot possibly do that"),
        ("twelve", "Here are twelve more problems: late materials, rework, absences, unclear specs, rush "
                   "orders, machine downtime, missing tools, slow approvals, overtime, morale, training gaps, "
                   "and customer changes."),
        ("blame", "Sales is lazy and Production never listens"),
        ("mixed", "Five possible causes, two observations, one demand: causes could be supplier delays, rush "
                  "orders, rework, absences or unclear specs; we saw 12 rush orders last week and 3 machines idle "
                  "on Tuesday; and we need the queue to keep running."))),
    Scenario("two_explanations", ("S30",), (
        Turn("We still have two explanations: priorities changing daily, or suppliers delivering late. Either "
             "way, freezing the daily plan for one week with one team would show us something cheaply. What "
             "should we do next?"),
    ), (
        "The consultant may recommend the low-cost bounded test with the uncertainty between the two "
        "explanations visible.",
        "Completing a CRT, Cloud, FRT, PRT and Transition Tree is not made a prerequisite of testing.",
    ), seed="two_explanations"),
    Scenario("immediate_action", ("S102",), (
        Turn("What should we do next?"),
    ), (
        "The recommendation identifies starting conditions, need, action and expected effect.",
        "Owner, authority, timing, observation criterion and contingency are explicit or left unknown, never "
        "invented.",
        "It asks for the most consequential missing item.",
        "A drawn or saved action does not create a real-world assignment.",
    ), seed="proposed_change"),
    Scenario("immature_cohort", ("S122",), (
        Turn("It is October 30, the review date. Of 120 orders due so far, 92 are confirmed on time and 8 late; "
             "the last 20, due in the final three business days, do not have final outcomes yet. Have we "
             "reached the goal?", intent="explain_observation"),
    ), (
        "The review retains the original forecast and labels the immature outcomes pending.",
        "It requests complete follow-up before claiming goal attainment.",
        "Missing observations are not treated as failures or successes.",
    ), seed="rolling_cohort", expects_review=True),
    # The open-evenings conversation of the live procedure (live-claude-test-prompt.md), split in two so a rejected
    # reply in one does not hide the other: the trees, then the test-result loop. They ask for the largest replies.
    Scenario("evenings_trees", ("S01", "S02", "S128"), (
        Turn("People come to our open evenings, are inspired, and we never see them again. Organisers are tired. "
             "I am not sure what success would look like yet.", "David"),
        Turn("Success would be that most newcomers come to a first practice within three weeks; today it is "
             "about 2 in 30. We must not pressure anyone, and organiser hours must not grow.", "David"),
        Turn("I think the cause is that we never offer a next step at the end of an evening. Nobody tells "
             "newcomers that a first practice exists.", "David"),
        Turn("There is a conflict: to keep evenings welcoming we must not push anyone, but to grow practice we "
             "must invite people explicitly. We could end each evening with one clear, no-pressure invitation. "
             "If we did, more newcomers would come to a first practice.", "David"),
    ), (
        "David's first report is kept in David's words; any goal is provisional, and no measure, baseline or "
        "agreement is invented.",
        "The stated success (most newcomers at a first practice within three weeks), the baseline of about 2 in 30 "
        "and both protections (no pressure; organiser hours do not grow) are recorded as David said them; a goal "
        "that already exists gets a new version, not a second goal.",
        "The cause David reports is in the Current Reality Tree with a causes link to the symptom it explains, in "
        "David's words.",
        "The conflict is in the Evaporating Cloud as David stated it: the two needs, the two actions that conflict "
        "and the no-pressure invitation as the injection; parts David did not state are asked about, not invented.",
        "The expected effect (more newcomers at a first practice) is linked in the Future Reality Tree from the "
        "Cloud's injection itself, not from a copy of it.",
        "Each next move is one prominent question or recommendation that takes up the latest input.",
    )),
    Scenario("evenings_loop", ("S01", "S02", "S131", "S34", "S36"), (
        Turn("People come to our open evenings, are inspired, and we never see them again. Organisers are tired. "
             "I am not sure what success would look like yet.", "David"),
        Turn("Success would be that most newcomers come to a first practice within three weeks; today it is "
             "about 2 in 30. We must not pressure anyone, and organiser hours must not grow.", "David"),
        Turn("Let's test ending each evening with one clear, no-pressure invitation to a first practice, for three "
             "weeks starting 16 October. I forecast 6 of 30 newcomers at a first practice. Stop if anyone says "
             "they felt pushed. I will give the invitation myself.", "David",
             declarations={"ownership": ["David"]}),
        Turn("9 of 31 came to a first practice. Nobody felt pushed; organiser hours were the same.", "David"),
    ), (
        "David's first report is kept in David's words; any goal is provisional, and no measure, baseline or "
        "agreement is invented.",
        "The stated success (most newcomers at a first practice within three weeks), the baseline of about 2 in 30 "
        "and both protections (no pressure; organiser hours do not grow) are recorded as David said them; a goal "
        "that already exists gets a new version, not a second goal.",
        "The test keeps David's original forecast exactly (6 of 30 newcomers at a first practice), the three-week "
        "window from 16 October and the stop condition.",
        "Giving the invitation is owned by David because David declared it; no other owner, date or measure is "
        "invented.",
        "The result (9 of 31) is reviewed against the unchanged forecast of 6 of 30 with both denominators kept and "
        "classified as supported; the protections are reported as held; it is not presented as proof of a unique "
        "cause.",
        "Each next move is one prominent question or recommendation that takes up the latest input.",
    )),
    # Held out: the same behaviour in different words, so a prompt tuned on the cases above is checked elsewhere.
    Scenario("heldout_correction", ("S06", "S52"), (
        Turn("Invoices go out late and customers keep complaining."),
        Turn("It is not that Finance is slow. Every invoice waits for a manager's approval, and the only manager "
             "who can approve is in on Fridays.", "Priya"),
    ), (
        "Priya's account is retained with Priya's attribution and is not treated as resistance or as agreement.",
        "The next question neutrally investigates the approval mechanism Priya describes without assigning blame.",
        "No unsupported causal certainty or group assent is invented.",
        "Exactly one next move or a justified stopping point is prominent.",
    )),
    Scenario("heldout_new_information", ("S52",), (
        Turn("Before the results: two of the five people on the pilot team left this week, and the "
             "warehouse moved to a new building on Monday."),
    ), (
        "All contributed information is accounted for in the receipt (notes or records citing the input).",
        "No unsupported causal certainty, identity verification or group assent is invented.",
        "Exactly one next move or a justified stopping point is prominent.",
        "Any proposed update retains source references.",
    ), seed=True),
    Scenario("heldout_immediate_action", ("S102",), (
        Turn("Where do we go from here?"),
    ), (
        "The recommendation identifies starting conditions, need, action and expected effect.",
        "Owner, authority, timing, observation criterion and contingency are explicit or left unknown, never "
        "invented.",
        "It asks for the most consequential missing item.",
        "A drawn or saved action does not create a real-world assignment.",
    ), seed="proposed_standup"),
    Scenario("heldout_immature_cohort", ("S122",), (
        Turn("Today is October 30. 75 orders were due by today: 61 are confirmed on time, 6 confirmed late, and 8 "
             "are still inside their three-day window. Did we hit the target?", intent="explain_observation"),
    ), (
        "The review retains the original forecast and labels the immature outcomes pending.",
        "It requests complete follow-up before claiming goal attainment.",
        "Missing observations are not treated as failures or successes.",
    ), seed="rolling_cohort", expects_review=True),
)


SEED_TEXT = ("Our Payments system goal is at least 90% of orders on time by October 30. "
             "We protect at least 95% of urgent acknowledgements within 24 hours. Baseline unknown. "
             "Before starting a two-week one-team priority-queue pilot, we predict at least 80% "
             "of pilot orders due on time and 95% of urgent requests acknowledged within 24 hours. "
             "Stop if acknowledgement falls below 95%; review on October 16.")


GOAL = {"statement": "At least 90% of orders on time", "scope": "Payments", "horizon": "October 30",
        "baseline": None, "measure": "on-time orders / orders due",
        "protections": ["At least 95% of urgent requests acknowledged within 24 hours"]}
SEEDS = {
    "blaming_question": {
        "text": "Late deliveries, changing priorities and overtime in Payments.",
        "prompt": "Why does Sales disrupt production so often?",
        "updates": [("record_goal", "goal", GOAL)]},
    "two_explanations": {
        "text": "Orders ship late. Maybe because priorities change daily, maybe because suppliers deliver late.",
        "prompt": "What should we do next?",
        "updates": [("record_goal", "goal", GOAL),
                    ("record_claim", "temp_late", {"tree": "current_reality", "role": "undesirable_effect",
                                                   "statement": "Orders ship late", "basis": "participant_report"}),
                    ("record_claim", "temp_prio", {"tree": "current_reality", "role": "root_cause",
                                                   "statement": "Priorities change daily", "basis": "hypothesis"}),
                    ("record_claim", "temp_supp", {"tree": "current_reality", "role": "root_cause",
                                                   "statement": "Suppliers deliver late", "basis": "hypothesis"}),
                    ("record_link", "temp_l1", {"tree": "current_reality", "relation": "causes",
                                                "from_ref": "temp_prio", "to_ref": "temp_late"}),
                    ("record_link", "temp_l2", {"tree": "current_reality", "relation": "causes",
                                                "from_ref": "temp_supp", "to_ref": "temp_late"})]},
    "proposed_change": {
        "text": "We want to try a daily priority queue with one Payments team for two weeks.",
        "prompt": "What happens next?",
        "updates": [("record_goal", "goal", GOAL),
                    ("record_test", "pilot", {
                        "statement": "Daily priority queue with one team for two weeks", "goal_ref": "goal",
                        "scope": "Payments, one team, two weeks",
                        "forecast": [{"measure": "on-time delivery", "expected": "80%", "scope": "Payments pilot",
                                      "denominator": "orders due", "period": "two weeks"}]})]},
    "proposed_standup": {
        "text": "We want the support team to hold its daily stand-up at 8am instead of 11am for three weeks.",
        "prompt": "What happens next?",
        "updates": [("record_goal", "goal", GOAL),
                    ("record_test", "pilot", {
                        "statement": "Support team stand-up at 8am for three weeks", "goal_ref": "goal",
                        "scope": "Payments support team, three weeks",
                        "forecast": [{"measure": "orders on time", "expected": "at least 85%",
                                      "scope": "Payments support team", "denominator": "orders due",
                                      "period": "three weeks"}]})]},
    "rolling_cohort": {
        "text": "Every order due October 1 to 30 counts; an order's outcome is final three business days after "
                "its due date. We forecast at least 85% on time. Review on October 30.",
        "prompt": "What happened by the review date?",
        "updates": [("record_goal", "goal", GOAL),
                    ("record_test", "pilot", {
                        "statement": "Daily priority queue for all Payments orders in October", "goal_ref": "goal",
                        "scope": "Payments orders due October 1-30 (rolling cohort)", "review_date": "October 30",
                        "forecast": [{"measure": "on-time delivery", "expected": "at least 85%",
                                      "scope": "Payments orders due October 1-30", "denominator": "orders due",
                                      "period": "October 1-30; outcomes final three business days after each "
                                                "due date"}]})]},
}


class SeedConsultant:
    """Authored setup, clearly distinguished from the evaluated live responses."""
    version = "evaluation-fixture/1"

    def __init__(self, kind="pilot"):
        self.kind = kind

    def propose(self, request):
        source = [request["input"]["request_id"]]
        if self.kind != "pilot":
            seed = SEEDS[self.kind]
            return {"schema_version": "1", "delivery_profile": "p2", "request_id": request["input"]["request_id"],
                    "base_revision": request["input"]["base_revision"],
                    "intervention": {"kind": "question", "goal_ref": "goal", "purpose": "authored_setup",
                                     "primary_prompt": seed["prompt"], "rationale": "Authored evaluation setup."},
                    "proposed_updates": [{"operation": op, "temporary_id": temp, "source_refs": source, "data": data}
                                         for op, temp, data in seed["updates"]]}
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
