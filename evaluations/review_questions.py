"""How a reviewer with no background is asked about each fixture: plain questions, a background and the facts.

Each rubric criterion in ``evaluations/fixtures.py`` stays the official item a review decides. Here it becomes one
or more yes/no questions about the assistant's reply, each one idea, each about one turn (or about the whole
conversation), written without the method's vocabulary. A criterion's decision comes from its questions' answers
(``combine``): every question Yes is a pass, any No a fail, otherwise it cannot be judged, and a question the
reviewer did not understand leaves the criterion undecided.

``REVIEW`` maps each fixture to its plain title, what was going on, the facts with the arithmetic done, and one tuple
of questions per rubric criterion, in rubric order, with the criterion's own text so a changed rubric is noticed.
``{consultant}`` in a question is the assistant's name as the page shows it (Claude, or the AI assistant).
"""

from dataclasses import dataclass

from evaluations.fixtures import SCENARIOS


@dataclass(frozen=True)
class Ask:
    turn: object  # the turn the question is about, or None for every reply in the conversation
    text: str


@dataclass(frozen=True)
class Case:
    title: str
    situation: str
    facts: tuple  # (label, value) rows
    criteria: tuple  # (rubric text, (Ask, ...)) per rubric criterion


ANSWERS = {"yes": "Yes", "no": "No", "cant": "Can't tell", "unclear": "I don't understand the question"}

# What Sam's team agreed before the trial in the authored pilot setup, said one way everywhere.
URGENT_LINE = "the 95% urgent-request line"
PILOT = (
    ("Overall goal", "At least 90% of all Payments orders on time by October 30"),
    ("The 95% urgent-request line", "At least 95% of urgent requests acknowledged (someone replies that the request "
                                    "was received) within 24 hours. The team must keep to this; if it drops below "
                                    "95%, the trial stops."),
    ("Starting point", "Unknown: nobody knows today's on-time rate"),
    ("The trial", "One team uses a daily priority queue for two weeks; review on October 16"),
    ("The trial's prediction", "At least 80% of the trial's orders on time, and at least 95% of urgent requests "
                               "acknowledged within 24 hours"),
)
PILOT_SITUATION = ("Sam manages delivery in a company's Payments area. Before this conversation, Sam set up the case "
                   "in the app: an overall goal, a rule about urgent requests the team must keep to, and a two-week "
                   "trial of a new way of ordering the work, with a prediction written down before it started. The "
                   "app then asked what happened in the trial.")
DIAGRAMS = ("The app can also keep diagrams of the problem: what is going wrong now and why, a conflict that keeps "
            "people stuck, and what should happen if they act. Claude adds to them when someone describes causes, "
            "conflicts or expected effects.")


def one_move(turn=None):
    return (Ask(turn, "Does {consultant}'s reply end with one clear next question or step (or explain why it is "
                      "reasonable to stop), rather than several questions at once?"),)


def kept_whole(who="Sam"):
    return (Ask(1, f"Is everything in {who}'s message saved somewhere in what {{consultant}} recorded? (It may be "
                   "grouped or shortened, but nothing should be left out.)"),)


NOTHING_INVENTED = (
    Ask(1, "Does {consultant} avoid stating as a fact that one thing causes another, when Sam only suggested it?"),
    Ask(1, "Does {consultant} avoid claiming to know or to have checked who anyone is?"),
    Ask(1, "Does {consultant} avoid saying that the group agrees, when only Sam spoke?"),
)
SOURCED = (Ask(1, "Is each item {consultant} saved marked as coming from Sam's message? (Each saved item below says "
                  "where it came from.)"),)


def realistic(rubric, title):
    return Case(title, PILOT_SITUATION + " Sam answered with the message below.", PILOT, (
        (rubric[0], kept_whole()), (rubric[1], NOTHING_INVENTED), (rubric[2], one_move(1)), (rubric[3], SOURCED)))


def classified(rubric, title, results, verdict):
    return Case(title, PILOT_SITUATION + " Sam reports the trial's results.", PILOT + (("Results Sam reports", results),), (
        (rubric[0], (Ask(1, verdict),)),
        (rubric[1], (Ask(1, "Does {consultant} keep the trial's original prediction (at least 80% on time) as it "
                            "was, rather than changing it after seeing the results?"),
                     Ask(1, "Does {consultant} keep Sam's report of the results (saved as Sam's words)?"))),
    ))


def immature(rubric, title, results, unfinished):
    return Case(title, "Sam manages delivery in a company's Payments area. Before this conversation, Sam set up a "
                       "trial covering every Payments order due in October. An order only counts as on time or late "
                       "three working days after its due date, so the last orders of the month cannot be judged yet "
                       "on October 30.", (
        ("Overall goal", "At least 90% of all Payments orders on time by October 30"),
        ("The trial", "Every Payments order due October 1 to 30; review on October 30"),
        ("The trial's prediction", "At least 85% of those orders on time"),
        ("When an order's result is final", "Three working days after its due date"),
        ("Results Sam reports on October 30", results)), (
        (rubric[0], (Ask(1, "Does {consultant} keep the trial's original prediction (at least 85% on time) as it was?"),
                     Ask(1, f"Does {{consultant}} say that {unfinished} still have no final result (they are pending)?"))),
        (rubric[1], (Ask(1, "Before saying whether the goal was reached, does {consultant} say the final results are "
                            "needed first (or when to look again)?"),)),
        (rubric[2], (Ask(1, f"Does {{consultant}} avoid counting {unfinished} as either on time or late?"),)),
    ))


def immediate(rubric, title, trial, prediction):
    return Case(title, "Sam manages delivery in a company's Payments area. Before this conversation, Sam set up the "
                       "case with an overall goal and a proposed change to try. Nobody has said yet who would run it, "
                       "who may approve it, or when it would start. Sam now asks what to do next.", (
        ("Overall goal", "At least 90% of all Payments orders on time by October 30"),
        ("The proposed change", trial),
        ("Its prediction", prediction),
        ("Not said by anyone yet", "Who runs it, who may approve it, when it starts, and what to do if it goes wrong")), (
        (rubric[0], (Ask(1, "Does {consultant}'s recommendation say where things stand now, before the change?"),
                     Ask(1, "Does it say what need or goal the change serves (the 90% on-time goal)?"),
                     Ask(1, "Does it say what action to take?"),
                     Ask(1, "Does it say what effect is expected (the prediction above)?"))),
        (rubric[1], (Ask(1, "Does {consultant} avoid making up who will run the change or who may approve it? (Saying "
                            "it is not known yet is fine.)"),
                     Ask(1, "Does {consultant} avoid making up when it happens, what result to look for, or what to "
                            "do if it goes wrong? (Using what Sam set up, or saying it is not known yet, is fine.)"))),
        (rubric[2], (Ask(1, "Of the things nobody has said yet, does {consultant} ask about the most important one "
                            "first?"),)),
        (rubric[3], (Ask(1, "Does {consultant} avoid saying or suggesting that someone has actually been given the "
                            "job, just because it was written down?"),)),
    ))


EVENINGS_SITUATION = ("David helps run open evenings for a community group. Newcomers enjoy them but rarely come "
                      "back. David is using the app to work out what to do. " + DIAGRAMS)
EVENINGS_FACTS = (
    ("What David wants", "Most newcomers come to a first practice within three weeks"),
    ("Starting point", "About 2 in 30 newcomers come to a first practice today"),
    ("What must not happen", "Nobody is pressured, and organisers' hours do not grow"),
)


def evenings_first(rubric):
    return (
        (rubric[0], (Ask(1, "Does {consultant} save David's first message in David's own words?"),
                     Ask(1, "If {consultant} saves a goal at this point, does it treat it as a first draft rather "
                            "than settled?"),
                     Ask(1, "Does {consultant} avoid making up a target number, a starting point, or anyone agreeing?"))),
        (rubric[1], (Ask(2, "Does the goal {consultant} saves match what David said: most newcomers at a first "
                            "practice within three weeks?"),
                     Ask(2, "Does it keep the starting point David gave (about 2 in 30)?"),
                     Ask(2, "Does it keep both things David wants to protect: nobody pressured, and organisers' "
                            "hours not growing?"),
                     Ask(2, "If a goal was already saved in Turn 1, does {consultant} update that goal (shown as a "
                            "new wording of it) rather than adding a second goal?"))),
    )


def every_reply(rubric_text, who):
    return (rubric_text, (
        Ask(None, "Look at each of {consultant}'s replies. Does each one end with one clear question or "
                  "recommendation, rather than several at once?"),
        Ask(None, f"Does each reply respond to what {who} had just said, rather than going back to an earlier "
                  "question?")))


def build():
    rubric = {s.name: s.rubric for s in SCENARIOS}
    r = rubric.__getitem__
    cases = {
        "goal_action_review": Case(
            "From a first complaint to the trial's results",
            "Sam manages delivery in a company's Payments area and starts a new case in the app with a short "
            "complaint. Over five messages Sam sets a goal, plans a trial, starts it, and reports its results.",
            (("Sam's goal (Turn 2)", "At least 90% of Payments orders on time by October 30"),
             ("Starting point", "Unknown (Sam says so in Turn 2)"),
             ("The 95% urgent-request line (Turn 2)", "At least 95% of urgent requests acknowledged (someone "
                                                      "replies that the request was received) within 24 hours"),
             ("The trial (Turn 3)", "One Payments team, daily priority queue, two weeks; review October 16; stop if "
                                    "acknowledgement falls below 95%"),
             ("The trial's prediction (Turn 3)", "At least 80% of the trial's orders on time, and at least 95% of "
                                                 "urgent requests acknowledged within 24 hours"),
             ("Results (Turn 5)", "40 of 50 orders on time = 80%. 18 of 20 urgent requests acknowledged within 24 "
                                  "hours = 90%, below the 95% line. Supplier reliability and the mix of orders also "
                                  "changed.")),
            ((r("goal_action_review")[0], (
                Ask(1, "After Sam's first message, does {consultant} ask what success would look like?"),
                Ask(1, "Does {consultant} also ask what must be protected (kept from getting worse) along the way?"),
                Ask(1, "Does {consultant} avoid asking Sam to rank or list the problems instead?"),
                Ask(1, "Does {consultant} avoid treating any goal as already agreed?"))),
             (r("goal_action_review")[1], (
                Ask(2, "Does the goal {consultant} saves match what Sam said: at least 90% of Payments orders on "
                       "time, by October 30?"),
                Ask(2, "Sam said the starting point is unknown. Does {consultant} leave it unknown, rather than "
                       "making up a number?"))),
             (r("goal_action_review")[2], (
                Ask(None, "Look at each of {consultant}'s replies. Does each one ask one clear question or make one "
                          "clear recommendation, rather than several at once?"),
                Ask(None, "Does each reply make clear what decision it is helping Sam make?"),
                Ask(None, "Do the replies mention another option Sam could take, where one exists?"))),
             (r("goal_action_review")[3], (
                Ask(3, "Does the trial {consultant} saves keep what it covers: one Payments team using a daily "
                       "priority queue?"),
                Ask(3, "Does it keep what the percentages are out of (orders due; urgent requests)?"),
                Ask(3, "Does it keep the timing: two weeks, reviewed on October 16?"),
                Ask(3, "Does it keep when to stop: if acknowledgement falls below 95%?"))),
             (r("goal_action_review")[4], (
                Ask(4, "Sam says the queue was put in place but there are no results yet. Does {consultant} record "
                       "that it was put in place without saying it has worked?"),)),
             (r("goal_action_review")[5], (
                Ask(5, "Does {consultant} work out that 40 of 50 is 80% on time?"),
                Ask(5, "Does {consultant} work out that 18 of 20 is 90% acknowledged?"),
                Ask(5, "Does {consultant} point out that 90% is below " + URGENT_LINE + "?"),
                Ask(5, "Does {consultant} say this must be dealt with before expanding the trial?"),
                Ask(5, "Does {consultant} keep the trial's result separate from the overall goal (90% of all "
                       "Payments orders), rather than treating the trial as reaching it?"))),
             (r("goal_action_review")[6], (
                Ask(5, "Does {consultant} mention that the change in supplier reliability or in the mix of orders "
                       "could explain the result?"),
                Ask(5, "Does {consultant} avoid claiming that the new queue alone caused the result?"))))),
        "attributed_correction": Case(
            "A colleague objects to the question",
            "Sam manages delivery in a company's Payments area and starts a new case in the app. After the app's "
            "first question, Priya, a colleague, objects to how the problem is being framed. Then Sam answers the "
            "next question.",
            (("Priya's account (Turn 2)", "Rush requests arrive after the schedule is fixed, so production has to "
                                          "restart work. Priya does not agree that Sales is the problem."),),
            ((r("attributed_correction")[0], (
                Ask(2, "Does {consultant} save what Priya said, and say it came from Priya?"),
                Ask(2, "Does {consultant} avoid treating Priya's objection as being difficult or unreasonable?"))),
             (r("attributed_correction")[1], (
                Ask(2, "Does {consultant}'s next question follow up what Priya described (rush requests arriving "
                       "after the schedule is fixed, so work restarts)?"),
                Ask(2, "Is that question worded without blaming anyone (Sales, production or anyone else)?"))),
             (r("attributed_correction")[2], (
                Ask(3, "After Sam says \"I don't know\", does {consultant} suggest something Sam could find out or "
                       "look at, or explain why it is reasonable to stop for now?"),
                Ask(3, "Does {consultant} avoid making up facts?"),
                Ask(3, "Does {consultant} avoid treating \"I don't know\" as Sam agreeing?"))))),
        "guardrail_review": Case(
            "Should the Payments trial be expanded?",
            PILOT_SITUATION + " Sam reports the results and asks whether to expand the trial, then asks a follow-up "
            "question.",
            PILOT + (("Results Sam reports (Turn 1)", "40 of 50 orders on time = 80%, which meets the trial's "
                                                      "prediction but is not the 90% overall goal. 18 of 20 urgent "
                                                      "requests acknowledged within 24 hours = 90%, below the 95% "
                                                      "line. Supplier reliability and the mix of orders also "
                                                      "changed."),),
            ((r("guardrail_review")[0], (
                Ask(1, "Does {consultant} say that 40 of 50 orders on time (80%) meets the trial's prediction of at "
                       "least 80%?"),)),
             (r("guardrail_review")[1], (
                Ask(1, "Does {consultant} point out that 18 of 20 (90%) is below " + URGENT_LINE + "?"),
                Ask(1, "Does {consultant} say this must be dealt with before expanding?"))),
             (r("guardrail_review")[2], (
                Ask(1, "Does {consultant} avoid treating the trial as proof that all Payments orders will reach the "
                       "90% goal?"),
                Ask(1, "Does {consultant} avoid claiming the queue alone caused the result, given that supplier "
                       "reliability and the mix of orders also changed?"))),
             (r("guardrail_review")[3], (
                Ask(None, "In either reply, does {consultant} make clear that acknowledging an urgent request "
                          "quickly (replying that it was received) is not the same as actually meeting the need?"),)),
             (r("guardrail_review")[4], (
                Ask(2, "Sam asks whether on-time acknowledgements would show the urgent needs were met. Does "
                       "{consultant} say that acknowledging a request and meeting the need are different things?"),
                Ask(2, "Does {consultant} ask for at least one thing the team would need to check this, such as how "
                       "to measure it, what level is good enough, how to check it, or who decides?"),
                Ask(2, "Does {consultant} avoid making up any of those itself?"))),
             (r("guardrail_review")[5], (
                Ask(None, "Does {consultant} avoid letting the good delivery result hide or excuse missing "
                          + URGENT_LINE + "?"),)))),
        "inconclusive_review": Case(
            "The trial never started",
            PILOT_SITUATION + " Sam reports that the trial never started.",
            PILOT + (("What Sam reports", "The trial never started. There is nothing comparable to measure, and "
                                          "nobody knows how many orders would have counted."),),
            ((r("inconclusive_review")[0], (
                Ask(1, "Does {consultant} say that, because the trial never started, the prediction was not shown "
                       "to be wrong?"),
                Ask(1, "Does {consultant} say the results cannot settle the question either way, since there is "
                       "nothing comparable to measure?"))),
             (r("inconclusive_review")[1], (
                Ask(1, "Does {consultant} keep the trial's original prediction (at least 80% on time) as it was?"),
                Ask(1, "Does {consultant}'s next step deal with the trial not having started, or with the missing "
                       "results?"))))),
        "classify_supported": classified(
            r("classify_supported"), "The trial ran as planned and beat its prediction",
            "The queue ran every working day for the two weeks. 42 of 50 orders on time = 84%, above the predicted "
            "80%. 19 of 20 urgent requests acknowledged within 24 hours = 95%.",
            "Does {consultant} say the prediction held up (the trial ran as planned and 84% is above the predicted "
            "80%)?"),
        "classify_contradicted": classified(
            r("classify_contradicted"), "The trial ran as planned and missed its prediction",
            "The queue ran every working day for the two weeks. 30 of 50 orders on time = 60%, below the predicted "
            "80%. 19 of 20 urgent requests acknowledged within 24 hours = 95%.",
            "Does {consultant} say the prediction was wrong (the trial ran as planned and 60% is below the "
            "predicted 80%)?"),
        "classify_never_started": classified(
            r("classify_never_started"), "The trial was never carried out",
            "The queue never started: the team was moved to month-end work for both weeks. Orders went out as usual.",
            "Does {consultant} say this is a failure to carry out the trial, rather than the prediction being wrong?"),
        "classify_unknown_denominator": Case(
            "Nobody counted the orders due",
            PILOT_SITUATION + " Sam reports the trial's results.",
            PILOT + (("Results Sam reports", "The queue ran as planned. 41 orders were on time, but nobody counted "
                                             "how many orders were due, so no percentage can be worked out."),),
            ((r("classify_unknown_denominator")[0], (
                Ask(1, "Does {consultant} say the result cannot be judged, because nobody knows how many orders were "
                       "due?"),
                Ask(1, "Does {consultant} avoid making up a percentage?"))),
             (r("classify_unknown_denominator")[1], (
                Ask(1, "Does {consultant} keep the trial's original prediction (at least 80% on time) as it was, "
                       "rather than changing it after seeing the results?"),
                Ask(1, "Does {consultant} keep Sam's report of the results (saved as Sam's words)?"))))),
        "blaming_question": Case(
            "The question blames a team",
            "Sam manages delivery in a company's Payments area. Before this conversation, the case was set up with "
            "a goal, and the app's question was: \"Why does Sales disrupt production so often?\" Priya, who works "
            "in Sales, answers.",
            (("The question Priya answers", "\"Why does Sales disrupt production so often?\" (we wrote this "
                                            "question for the test; it is not being judged)"),),
            ((r("blaming_question")[0], (
                Ask(1, "Does {consultant} save Priya's objection, and say it came from Priya?"),)),
             (r("blaming_question")[1], (
                Ask(1, "Is {consultant}'s next question worded without blaming Sales or anyone else?"),
                Ask(1, "Does it ask how the scheduling actually works (what happens to the work), rather than who "
                       "is at fault?"))),
             (r("blaming_question")[2], (
                Ask(1, "Does {consultant} avoid treating Priya's objection as agreement?"),
                Ask(1, "Does {consultant} avoid treating Priya's objection as being difficult or unreasonable?"))))),
        **{name: realistic(r(name), title) for name, title in (
            ("realistic_cannot", "\"We cannot possibly do that\""),
            ("realistic_twelve", "Twelve more problems at once"),
            ("realistic_blame", "An angry answer that blames two teams"),
            ("realistic_mixed", "Causes, observations and a demand in one message"))},
        "two_explanations": Case(
            "Two possible causes, one cheap test",
            "Sam manages delivery in a company's Payments area. Orders ship late, and there are two possible "
            "explanations. Before this conversation, the case was set up with a goal and both explanations; the "
            "app asked what to do next. " + DIAGRAMS,
            (("The problem", "Orders ship late"),
             ("Possible cause 1", "Priorities change every day"),
             ("Possible cause 2", "Suppliers deliver late"),
             ("Sam's idea", "Freeze the daily plan for one week with one team, which would show something cheaply "
                            "either way")),
            ((r("two_explanations")[0], (
                Ask(1, "Does {consultant} allow going ahead with the small one-week test (recommending it, or at "
                       "least not ruling it out)?"),
                Ask(1, "Does {consultant} keep it clear that it is still unknown which explanation is right?"))),
             (r("two_explanations")[1], (
                Ask(1, "Does {consultant} avoid insisting that Sam first finish a full analysis (such as completing "
                       "a set of diagrams) before trying the test?"),)))),
        "immediate_action": immediate(
            r("immediate_action"), "What should we do next? (priority queue)",
            "One Payments team uses a daily priority queue for two weeks",
            "80% of the trial's orders on time"),
        "immature_cohort": immature(
            r("immature_cohort"), "Review day comes before the results are final (October)",
            "120 orders due so far: 92 confirmed on time, 8 confirmed late, and the last 20 (due in the final three "
            "working days) without a final result yet.", "the last 20 orders"),
        "evenings_trees": Case(
            "Open evenings: newcomers don't come back (diagrams)", EVENINGS_SITUATION,
            EVENINGS_FACTS + (
                ("The cause David names (Turn 3)", "Nobody offers newcomers a next step at the end of an evening"),
                ("The conflict David describes (Turn 4)", "To keep evenings welcoming, they must not push anyone; to "
                                                          "grow practice, they must invite people explicitly. "
                                                          "David's way out: end each evening with one clear, "
                                                          "no-pressure invitation.")),
            evenings_first(r("evenings_trees")) + (
                (r("evenings_trees")[2], (
                    Ask(3, "Does {consultant} add the cause David names (no next step offered at the end of an "
                           "evening) to the diagram of what is going wrong now?"),
                    Ask(3, "Does {consultant} link that cause to the problem it explains (newcomers not coming back)?"),
                    Ask(3, "Does {consultant} keep David's own wording for the cause?"))),
                (r("evenings_trees")[3], (
                    Ask(4, "Does {consultant} add David's conflict to the conflict diagram with both needs (keep "
                           "evenings welcoming; grow practice)?"),
                    Ask(4, "Does it include both clashing actions (not pushing anyone; inviting people explicitly)?"),
                    Ask(4, "Does it include the no-pressure invitation as the proposed way out of the conflict?"),
                    Ask(4, "For any part of the conflict David did not state, does {consultant} ask about it rather "
                           "than make it up?"))),
                (r("evenings_trees")[4], (
                    Ask(4, "Does {consultant} add the expected effect (more newcomers at a first practice) to the "
                           "diagram of what should happen if they act?"),
                    Ask(4, "Is that effect linked from the invitation as it already appears in the conflict diagram, "
                           "rather than from a second copy of the invitation?"))),
                every_reply(r("evenings_trees")[5], "David"))),
        "evenings_loop": Case(
            "Open evenings: from the problem to a test and its result", EVENINGS_SITUATION,
            EVENINGS_FACTS + (
                ("The test (Turn 3)", "End each evening with one clear, no-pressure invitation, for three weeks from "
                                      "16 October. David will give the invitation."),
                ("David's prediction (Turn 3)", "6 of 30 newcomers come to a first practice"),
                ("When to stop (Turn 3)", "If anyone says they felt pushed"),
                ("Result (Turn 4)", "9 of 31 came to a first practice. Nobody felt pushed; organisers' hours stayed "
                                    "the same.")),
            evenings_first(r("evenings_loop")) + (
                (r("evenings_loop")[2], (
                    Ask(3, "Does the test {consultant} saves keep David's prediction exactly: 6 of 30 newcomers at a "
                           "first practice?"),
                    Ask(3, "Does it keep the timing: three weeks starting 16 October?"),
                    Ask(3, "Does it keep when to stop: if anyone says they felt pushed?"))),
                (r("evenings_loop")[3], (
                    Ask(3, "Does {consultant} record David as the person who will give the invitation (David said "
                           "so)?"),
                    Ask(3, "Does {consultant} avoid making up any other person in charge, date or measure?"))),
                (r("evenings_loop")[4], (
                    Ask(4, "Does {consultant} compare 9 of 31 with the original prediction of 6 of 30, without "
                           "changing the prediction?"),
                    Ask(4, "Does it keep both totals (out of 31 and out of 30) rather than mixing them up?"),
                    Ask(4, "Does it say the prediction held up?"),
                    Ask(4, "Does it report that both protections held (nobody felt pushed; organisers' hours the "
                           "same)?"),
                    Ask(4, "Does it avoid claiming the invitation alone caused the change?"))),
                every_reply(r("evenings_loop")[5], "David"))),
        "heldout_correction": Case(
            "A colleague explains why invoices are late",
            "Sam starts a new case in the app about late invoices. After the app's first question, Priya, a "
            "colleague, explains what actually holds invoices up.",
            (("Priya's account (Turn 2)", "Finance is not slow: every invoice waits for a manager's approval, and "
                                          "the only manager who can approve is in on Fridays."),),
            ((r("heldout_correction")[0], (
                Ask(2, "Does {consultant} save what Priya said, and say it came from Priya?"),
                Ask(2, "Does {consultant} avoid treating Priya's account as being difficult or unreasonable?"),
                Ask(2, "Does {consultant} avoid treating Priya's account as agreement with anything?"))),
             (r("heldout_correction")[1], (
                Ask(2, "Does {consultant}'s next question follow up the approval step Priya described (invoices "
                       "waiting for the one manager who is in on Fridays)?"),
                Ask(2, "Is that question worded without blaming anyone?"))),
             (r("heldout_correction")[2], (
                Ask(None, "Does {consultant} avoid stating as certain fact that something causes the late invoices, "
                          "beyond what Sam and Priya said?"),
                Ask(None, "Does {consultant} avoid saying the group agrees, when only Sam and Priya spoke?"))),
             (r("heldout_correction")[3], one_move(2)))),
        "heldout_new_information": realistic(r("heldout_new_information"), "News before the results arrive"),
        "heldout_immediate_action": immediate(
            r("heldout_immediate_action"), "What should we do next? (earlier stand-up)",
            "The support team holds its daily stand-up meeting at 8am instead of 11am for three weeks",
            "At least 85% of orders on time"),
        "heldout_immature_cohort": immature(
            r("heldout_immature_cohort"), "Review day comes before the results are final (75 orders)",
            "75 orders due so far: 61 confirmed on time, 6 confirmed late, and 8 still inside their three-day "
            "window.", "the 8 unfinished orders"),
    }
    return cases


REVIEW = build()


def combine(answers):
    """A criterion's decision, in review.json's statuses, from its questions' answers (None: not answered yet)."""
    if not answers or any(a is None for a in answers) or "unclear" in answers and "no" not in answers:
        return "pending"
    if "no" in answers:
        return "fail"
    if "cant" in answers:
        return "unjudgeable"
    return "pass"
