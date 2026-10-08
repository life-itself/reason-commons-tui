"""How a reviewer with no background is asked about each fixture: plain questions, a background and the facts.

Each rubric criterion in ``evaluations/fixtures.py`` stays the official item a review decides. Here it becomes one
or more yes/no questions about what the system's reply did, each one idea, each about one turn (or about the whole
conversation), written without the method's vocabulary. A question asks plainly what happened ("Does the system make
up a percentage?"), never in a double negative; ``passes`` says which answer is the good one. A criterion's decision
comes from its questions (``combine``): every question answered the good way is a pass, any answered the bad way a
fail, otherwise it cannot be judged, and a question the reviewer did not understand leaves the criterion undecided.

The page is read once, top to bottom, by someone who knows nothing of the method or of the fixtures, so nothing here
may be used before it is introduced: a situation says only who is talking and what was set up before the
conversation; a fact belongs to the turn in which it becomes known (turn 0: set up before the conversation) and is
shown there; a question about a turn uses only what the reader has met by then, names the part of the reply it means
when that matters, and repeats a list rather than pointing back at one; and each thing keeps one name (the 95% rule
is always "the 95% minimum for urgent requests", and a person's own words are not swapped for synonyms). Where the
person or the system has other names for something, the fact says so.

``REVIEW`` maps each fixture to its plain title, situation, facts as (turn, label, value) rows, and one tuple of
questions per rubric criterion, in rubric order, with the criterion's own text so a changed rubric is noticed.
``{consultant}`` in a question is how the page names the assistant ("the system").
"""

from dataclasses import dataclass

from evaluations.fixtures import SCENARIOS


@dataclass(frozen=True)
class Ask:
    turn: object  # the turn the question is about, or None for every reply in the conversation
    text: str
    passes: str = "yes"  # the answer that meets the criterion: "no" when the question asks about a mistake


@dataclass(frozen=True)
class Case:
    title: str
    situation: str
    facts: tuple  # (turn, label, value) rows; turn 0 was set up before the conversation
    criteria: tuple  # (rubric text, (Ask, ...)) per rubric criterion


def Mistake(turn, text):
    """A question about a mistake the reply might make: answering No meets the criterion."""
    return Ask(turn, text, "no")


ANSWERS = {"yes": "Yes", "no": "No", "cant": "Can't tell", "unclear": "I don't understand the question"}

MINIMUM = "the 95% minimum for urgent requests"
MINIMUM_FACT = ("At least 95% of urgent requests must be acknowledged within 24 hours. \"Acknowledged\" means "
                "someone replies that the request was received; it does not mean the request was dealt with. The "
                "goal calls this a \"protection\" it must not break, and the trial uses the same 95% as its \"stop "
                "condition\": if acknowledgement drops below 95%, the trial stops. (The system may also say "
                "\"guardrail\".)")
TRIAL_NAMES = " (Sam and the system may call it the \"pilot\" or the \"test\".)"
FORECAST_NAME = " (Sam and the system may call it the \"forecast\".)"
GOAL_NAME = " (The system may call it the \"system goal\": the goal for the whole Payments department.)"
# What Sam set up before the conversation in the authored pilot setup.
PILOT = (
    (0, "Overall goal", "At least 90% of all Payments orders delivered on time by October 30." + GOAL_NAME),
    (0, "The 95% minimum for urgent requests", MINIMUM_FACT),
    (0, "Today's on-time rate", "Unknown: nobody has measured it"),
    (0, "The trial", "For two weeks, one team works through its orders using a daily priority queue (a list, "
                     "updated each day, of which orders to do first). Results are reviewed on October 16." + TRIAL_NAMES),
    (0, "The trial's prediction", "Written down before the trial started: at least 80% of the trial's orders on "
                                  "time, and at least 95% of urgent requests acknowledged within 24 hours." + FORECAST_NAME),
)
PILOT_SITUATION = ("Sam manages deliveries in a company's Payments department. Before this conversation, Sam set up "
                   "the goal, the minimum for urgent requests and the trial shown below, and the system asked what "
                   "happened in the trial.")
KEEPS_PREDICTION = ("Does {consultant} leave the trial's prediction (at least 80% on time) as it was written? (If the "
                    "reply doesn't change or replace the prediction, answer Yes.)")


def one_move(turn=None):
    return (Ask(turn, "Does {consultant}'s reply end with one clear next question or step (or explain why it is "
                      "reasonable to stop), rather than several questions at once?"),)


def kept_whole(who="Sam"):
    return (Ask(1, f"Is everything in {who}'s message kept somewhere in what {{consultant}} recorded? (It may be "
                   "grouped or shortened, but nothing should be left out.)"),)


NOTHING_INVENTED = (
    Mistake(1, "Does {consultant} state as a fact that one thing causes another, when Sam only suggested it?"),
    Mistake(1, "Does {consultant} claim to know, or to have checked, who anyone is?"),
    Mistake(1, "Does {consultant} say that a group agrees, when only Sam spoke?"),
)
SOURCED = (Ask(1, "Does each thing {consultant} recorded say which message it is based on?"),)


def realistic(rubric, title):
    return Case(title, PILOT_SITUATION + " This is Sam's answer.", PILOT, (
        (rubric[0], kept_whole()), (rubric[1], NOTHING_INVENTED), (rubric[2], one_move(1)), (rubric[3], SOURCED)))


def classified(rubric, title, results, verdict):
    return Case(title, PILOT_SITUATION + " Sam reports what happened.", PILOT + ((1, "What Sam reports", results),), (
        (rubric[0], (Ask(1, verdict),)),
        (rubric[1], (Ask(1, KEEPS_PREDICTION),
                     Ask(1, "Does {consultant} keep a note of Sam's report in Sam's exact words?"))),
    ))


def immature(rubric, title, results, unfinished):
    return Case(title, "Sam manages deliveries in a company's Payments department. Before this conversation, Sam set "
                       "up the goal and the trial shown below, and the system asked what happened by the review date.", (
        (0, "Overall goal", "At least 90% of all Payments orders delivered on time by October 30." + GOAL_NAME),
        (0, "The trial", "Covers every Payments order due between October 1 and 30. Results are reviewed on October "
                         "30." + TRIAL_NAMES),
        (0, "The trial's prediction", "Written down before the trial started: at least 85% of those orders on "
                                      "time." + FORECAST_NAME),
        (0, "When an order's result is known", "Three working days after its due date. So on October 30, the last "
                                               "orders of the month cannot be counted as on time or late yet."),
        (1, "What Sam reports on October 30", results)), (
        (rubric[0], (Ask(1, "Does {consultant} leave the trial's prediction (at least 85% on time) as it was written? "
                            "(If the reply doesn't change or replace the prediction, answer Yes.)"),
                     Ask(1, f"Does {{consultant}} say that {unfinished} have no final result yet?"))),
        (rubric[1], (Ask(1, "Before saying whether the goal was reached, does {consultant} say the final results are "
                            "needed first (or when to look again)?"),)),
        (rubric[2], (Mistake(1, f"Does {{consultant}} count {unfinished} as on time, or as late?"),)),
    ))


def immediate(rubric, title, trial, prediction):
    return Case(title, "Sam manages deliveries in a company's Payments department. Before this conversation, Sam set "
                       "up the goal, the minimum for urgent requests and the trial shown below. The trial has not "
                       "started. Sam now asks what to do next.", (
        (0, "Overall goal", "At least 90% of all Payments orders delivered on time by October 30." + GOAL_NAME),
        (0, "The 95% minimum for urgent requests", "At least 95% of urgent requests must be acknowledged within 24 "
                                                   "hours. \"Acknowledged\" means someone replies that the request "
                                                   "was received. The goal calls this a \"protection\" it must not "
                                                   "break."),
        (0, "Today's on-time rate", "Unknown: nobody has measured it"),
        (0, "The trial (not started yet)", trial + TRIAL_NAMES),
        (0, "The trial's prediction", prediction + FORECAST_NAME),
        (0, "Not decided yet", "Who will run the trial, who may approve it, when it starts, and what to do if it "
                               "goes wrong")), (
        (rubric[0], (Ask(1, "Sam asks what to do next. The system may answer with a recommendation or with a question; "
                            "judge whatever its reply says, including its reasons. Does it say what has been set up "
                            "so far (the goal and the trial)?"),
                     Ask(1, "Does it say what the trial is for (the 90% on-time goal)?"),
                     Ask(1, "Does it make clear what should happen next? (A question about what to settle first "
                            "counts.)"),
                     Ask(1, "Does it say what effect the trial is expected to have (the prediction above)?"))),
        (rubric[1], (Mistake(1, "Does {consultant} name someone to run the trial or approve it, when nobody has been "
                                "chosen? (If it only says this is not decided yet, answer No.)"),
                     Mistake(1, "Does {consultant} give a start date or timing for the trial that nobody gave? (If it "
                                "only says this is not decided yet, answer No.)"),
                     Mistake(1, "Does {consultant} make up a way of measuring the result that Sam didn't set up?"),
                     Mistake(1, "Does {consultant} make up what to do if the trial goes wrong? (If it only says this "
                                "is not decided yet, answer No.)"))),
        (rubric[2], (Ask(1, "Does {consultant} ask about one of the things listed as \"Not decided yet\"?"),
                     Ask(1, "Does {consultant} say why that one matters most right now?"))),
        (rubric[3], (Mistake(1, "Does {consultant} treat anyone as already in charge of the trial, when no one has "
                                "been named?"),)),
    ))


EVENINGS_SITUATION = ("David helps run open evenings for a community group. Newcomers enjoy them but rarely come "
                      "back. David starts a new conversation with the system to work out what to do.")
EVENINGS_GOAL = (
    (2, "What David wants", "Most newcomers come to a first practice within three weeks"),
    (2, "Where things stand now", "About 2 in 30 newcomers come to a first practice. (The system may call this the "
                                  "\"baseline\".)"),
    (2, "What must not happen", "Nobody is pressured, and organisers' hours do not grow. (The system may call these "
                                "\"protections\".)"),
)


def evenings_first(rubric):
    return (
        (rubric[0], (Ask(1, "Does {consultant} record David's first message in David's own words?"),
                     Ask(1, "If {consultant} records a goal at this point, does it treat it as a first draft rather "
                            "than settled?"),
                     Mistake(1, "Does {consultant} make up a target number, a starting point, or anyone agreeing?"))),
        (rubric[1], (Ask(2, "Does the goal {consultant} records match what David said: most newcomers at a first "
                            "practice within three weeks?"),
                     Ask(2, "Does it keep where things stand now, as David gave it (about 2 in 30)?"),
                     Ask(2, "Does it keep both things David wants to protect: nobody pressured, and organisers' "
                            "hours not growing?"),
                     Ask(2, "If a goal was already recorded in Turn 1, does {consultant} update that goal (shown as a "
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
            "Sam manages deliveries in a company's Payments department and starts a new conversation with the "
            "system. Over five turns, Sam describes the problem, sets a goal, plans a trial, starts it, and reports "
            "the results.",
            ((2, "Sam's goal", "At least 90% of Payments orders delivered on time by October 30"),
             (2, "Today's on-time rate", "Unknown (Sam says so). The system may call this the \"baseline\"."),
             (2, "The 95% minimum for urgent requests", "At least 95% of urgent requests must be acknowledged within "
                                                        "24 hours. \"Acknowledged\" means someone replies that the "
                                                        "request was received; it does not mean the request was "
                                                        "dealt with. (Sam calls it something to \"protect\".)"),
             (3, "The trial", "For two weeks, one Payments team works through its orders using a daily priority "
                              "queue (a list, updated each day, of which orders to do first). Results are reviewed "
                              "on October 16. Stop if acknowledgement falls below 95%." + TRIAL_NAMES),
             (3, "The trial's prediction", "At least 80% of the trial's orders on time, and at least 95% of urgent "
                                           "requests acknowledged within 24 hours." + FORECAST_NAME),
             (5, "The results, worked out", "40 of 50 orders on time = 80%, which meets the trial's prediction. "
                                            "18 of 20 urgent requests acknowledged within 24 hours = 90%, which is "
                                            "below the 95% minimum for urgent requests. Supplier reliability and the "
                                            "mix of orders also changed during the trial.")),
            ((r("goal_action_review")[0], (
                Ask(1, "After Sam's first message, does {consultant} ask what success would look like?"),
                Ask(1, "Does {consultant} also ask what must be protected (kept from getting worse) along the way?"),
                Mistake(1, "Does {consultant} ask Sam to rank or list the problems instead?"),
                Mistake(1, "Does {consultant} treat any goal as already agreed?"))),
             (r("goal_action_review")[1], (
                Ask(2, "Does the goal {consultant} records match what Sam said: at least 90% of Payments orders on "
                       "time, by October 30?"),
                Ask(2, "Sam said today's on-time rate is unknown. Does {consultant} leave it unknown, rather than "
                       "making up a number?"))),
             (r("goal_action_review")[2], (
                Ask(None, "Look at each of {consultant}'s replies. Does each one ask one clear question or make one "
                          "clear recommendation, rather than several at once?"),
                Ask(None, "Does each reply make clear what decision it is helping Sam make?"),
                Ask(None, "Do the replies mention another option Sam could take, where one exists?"))),
             (r("goal_action_review")[3], (
                Ask(3, "Does the trial {consultant} records keep what it covers: one Payments team using a daily "
                       "priority queue?"),
                Ask(3, "Does it keep what each percentage counts (orders due; urgent requests)?"),
                Ask(3, "Does it keep the timing: two weeks, reviewed on October 16?"),
                Ask(3, "Does it keep when to stop: if acknowledgement falls below 95%?"))),
             (r("goal_action_review")[4], (
                Mistake(4, "Sam says the queue was put in place, but there are no results yet. Does {consultant} say "
                           "or record that the queue has worked?"),)),
             (r("goal_action_review")[5], (
                Ask(5, "Does {consultant} work out that 40 of 50 is 80% on time?"),
                Ask(5, "Does {consultant} work out that 18 of 20 is 90% acknowledged?"),
                Ask(5, "Does {consultant} point out that 90% is below " + MINIMUM + "?"),
                Ask(5, "Does {consultant} say the shortfall on urgent requests must be looked into or fixed before "
                       "expanding the trial?"),
                Ask(5, "Does {consultant} keep the trial's result separate from Sam's goal (90% of all Payments "
                       "orders), rather than treating the trial as reaching it?"))),
             (r("goal_action_review")[6], (
                Ask(5, "Does {consultant} mention that the change in supplier reliability or in the mix of orders "
                       "could explain the result?"),
                Mistake(5, "Does {consultant} claim that the priority queue alone caused the result?"))))),
        "attributed_correction": Case(
            "A colleague objects to the question",
            "Sam manages deliveries in a company's Payments department and starts a new conversation with the "
            "system. In Turn 2 a colleague, Priya, replies instead of Sam. In Turn 3, Sam replies to the system's "
            "latest question.",
            ((2, "Good to know", "Nobody has mentioned Sales before Priya's message."),),
            ((r("attributed_correction")[0], (
                Ask(2, "Does {consultant} record what Priya said, and say it came from Priya?"),
                Mistake(2, "Does {consultant} treat Priya's objection as Priya being difficult or unreasonable?"))),
             (r("attributed_correction")[1], (
                Ask(2, "Does the question {consultant} asks in this reply follow up what Priya described (rush "
                       "requests arriving after the schedule is frozen, so production restarts work)?"),
                Ask(2, "Is the question {consultant} asks in this reply worded without blaming anyone (Sales, "
                       "production or anyone else)?"))),
             (r("attributed_correction")[2], (
                Ask(3, "After Sam says \"I don't know\", does {consultant} do or suggest something to find out (for "
                       "example, asking someone else or checking records), or explain why it is reasonable to stop "
                       "for now?"),
                Mistake(3, "In this reply, does {consultant} state as fact anything nobody said?"),
                Mistake(3, "Does {consultant} treat \"I don't know\" as Sam agreeing with Priya's account, or with "
                           "anything else?"))))),
        "guardrail_review": Case(
            "Should the Payments trial be expanded?",
            PILOT_SITUATION + " In Turn 1 Sam reports the results and asks whether to expand the trial. In Turn 2 "
            "Sam asks a follow-up question.",
            PILOT + ((1, "The results, worked out", "40 of 50 orders on time = 80%, which meets the trial's "
                                                    "prediction (but is not the 90% overall goal). 18 of 20 urgent "
                                                    "requests acknowledged within 24 hours = 90%, which is below the "
                                                    "95% minimum for urgent requests. Supplier reliability and the "
                                                    "mix of orders also changed during the trial."),),
            ((r("guardrail_review")[0], (
                Ask(1, "Does {consultant} say that 40 of 50 orders on time (80%) meets the trial's prediction of at "
                       "least 80%?"),)),
             (r("guardrail_review")[1], (
                Ask(1, "Does {consultant} point out that 18 of 20 (90%) is below " + MINIMUM + "?"),
                Ask(1, "Does {consultant} say the shortfall on urgent requests must be looked into or fixed before "
                       "expanding the trial?"))),
             (r("guardrail_review")[2], (
                Mistake(1, "Does {consultant} treat the trial as proof that all Payments orders will reach the 90% "
                           "goal?"),
                Mistake(1, "Does {consultant} claim that the priority queue alone caused the result, even though "
                           "supplier reliability and the mix of orders also changed?"))),
             (r("guardrail_review")[3], (
                Ask(None, "Across both replies together, does {consultant} make clear that acknowledging an urgent "
                          "request (replying that it was received) is not the same as actually dealing with it? "
                          "(This checks both replies at once, so your answer may match a question about Turn 2.)"),)),
             (r("guardrail_review")[4], (
                Ask(2, "Sam asks whether on-time acknowledgements would show the urgent requests were dealt with. "
                       "Does {consultant} say that acknowledging a request and dealing with it are different things?"),
                Ask(2, "To tell whether urgent requests were actually dealt with, the team would need things like: "
                       "what to measure, what level is good enough, how and by whom it is checked, and who decides. "
                       "Does {consultant} ask for at least one of these?"),
                Mistake(2, "Does {consultant} make up its own answer to any of these (what to measure, what level is "
                           "good enough, how and by whom it is checked, or who decides)?"))),
             (r("guardrail_review")[5], (
                Mistake(None, "Does {consultant} let the 80% on-time result (which met the trial's prediction) hide "
                              "or excuse the shortfall below " + MINIMUM + "?"),)))),
        "inconclusive_review": Case(
            "Sam reports that the trial never started",
            PILOT_SITUATION + " Sam reports what happened.",
            PILOT + ((1, "What Sam reports", "The trial never started. There is nothing comparable to measure, and "
                                             "nobody knows how many orders would have counted."),),
            ((r("inconclusive_review")[0], (
                Ask(1, "Does {consultant} say that, because the trial never started, the prediction was not shown "
                       "to be wrong?"),
                Ask(1, "Does {consultant} say the results cannot settle the question either way, since there is "
                       "nothing comparable to measure?"))),
             (r("inconclusive_review")[1], (
                Ask(1, KEEPS_PREDICTION),
                Ask(1, "Does {consultant}'s next step deal with the trial not having started, or with the missing "
                       "results?"))))),
        "classify_supported": classified(
            r("classify_supported"), "Sam reports the trial's results (42 of 50)",
            "The queue was used every working day for the two weeks. 42 of 50 orders on time = 84%, above the "
            "predicted 80%. 19 of 20 urgent requests acknowledged within 24 hours = 95%.",
            "Does {consultant} say the prediction held up, since 84% is above the predicted 80%?"),
        "classify_contradicted": classified(
            r("classify_contradicted"), "Sam reports the trial's results (30 of 50)",
            "The queue was used every working day for the two weeks. 30 of 50 orders on time = 60%, below the "
            "predicted 80%. 19 of 20 urgent requests acknowledged within 24 hours = 95%.",
            "Does {consultant} say the prediction was not met, since 60% is below the predicted 80%?"),
        "classify_never_started": classified(
            r("classify_never_started"), "Sam reports what happened during the trial weeks",
            "The queue was never used: the team was moved to month-end work for both weeks. Orders went out as usual.",
            "Does {consultant} say the trial was not carried out, rather than saying the prediction was wrong?"),
        "classify_unknown_denominator": Case(
            "Sam reports the trial's results (41 on time)",
            PILOT_SITUATION + " Sam reports what happened.",
            PILOT + ((1, "What Sam reports", "The queue was used as planned. 41 orders were on time, but nobody "
                                             "counted how many orders were due, so no percentage can be worked "
                                             "out."),),
            ((r("classify_unknown_denominator")[0], (
                Ask(1, "Does {consultant} say the result cannot be judged, because nobody knows how many orders were "
                       "due?"),
                Mistake(1, "Does {consultant} make up a percentage?"))),
             (r("classify_unknown_denominator")[1], (
                Ask(1, KEEPS_PREDICTION),
                Ask(1, "Does {consultant} keep a note of Sam's report in Sam's exact words?"))))),
        "blaming_question": Case(
            "The question blames a team",
            "Sam manages deliveries in a company's Payments department. Before this conversation, Sam set up a "
            "goal, and the system asked: \"Why does Sales disrupt production so often?\" (We wrote that question "
            "to set up this test; you are not judging it.) Priya, who works in Sales, replies.",
            (),
            ((r("blaming_question")[0], (
                Ask(1, "Does {consultant} record Priya's objection, and say it came from Priya?"),)),
             (r("blaming_question")[1], (
                Ask(1, "Is the question {consultant} asks in this reply worded without blaming Sales or anyone else?"),
                Ask(1, "Does the question {consultant} asks in this reply ask how the scheduling actually works (what "
                       "happens to the work), rather than who is at fault?"))),
             (r("blaming_question")[2], (
                Mistake(1, "Does {consultant} treat Priya's objection as agreement?"),
                Mistake(1, "Does {consultant} treat Priya's objection as Priya being difficult or unreasonable?"))))),
        **{name: realistic(r(name), title) for name, title in (
            ("realistic_cannot", "\"We cannot possibly do that\""),
            ("realistic_twelve", "Twelve more problems at once"),
            ("realistic_blame", "An angry answer that blames two teams"),
            ("realistic_mixed", "Causes, observations and a demand in one message"))},
        "two_explanations": Case(
            "Two possible causes, one cheap test",
            "Sam manages deliveries in a company's Payments department. Orders are shipping late, and there are two "
            "possible explanations. Before this conversation, Sam set up a goal and both explanations, and the "
            "system asked what to do next.",
            ((0, "The problem", "Orders ship late"),
             (0, "Possible cause 1", "Priorities change every day"),
             (0, "Possible cause 2", "Suppliers deliver late")),
            ((r("two_explanations")[0], (
                Ask(1, "Does {consultant} allow going ahead with Sam's one-week test (recommending it, or at least "
                       "not ruling it out)?"),
                Ask(1, "Does {consultant} keep it clear that it is still unknown which explanation is right?"))),
             (r("two_explanations")[1], (
                Mistake(1, "Does {consultant} insist that Sam first finish a full analysis (such as completing a set "
                           "of diagrams) before trying the test?"),)))),
        "immediate_action": immediate(
            r("immediate_action"), "What should we do next? (priority queue)",
            "For two weeks, one Payments team works through its orders using a daily priority queue (a list, updated "
            "each day, of which orders to do first).",
            "80% of the trial's orders on time."),
        "immature_cohort": immature(
            r("immature_cohort"), "Review day comes before the results are final (October)",
            "120 orders were due by October 30. 92 are confirmed on time and 8 confirmed late. The last 20 were due "
            "in the final three working days, so their results are not known yet.", "the last 20 orders"),
        "evenings_trees": Case(
            "Open evenings: newcomers don't come back (diagrams)", EVENINGS_SITUATION,
            EVENINGS_GOAL + (
                (3, "The cause David names", "Nobody offers newcomers a next step at the end of an evening"),
                (4, "The conflict David describes", "To keep evenings welcoming, they must not push anyone; to grow "
                                                    "practice, they must invite people explicitly. David's way out: "
                                                    "end each evening with one clear, no-pressure invitation.")),
            evenings_first(r("evenings_trees")) + (
                (r("evenings_trees")[2], (
                    Ask(3, "Does {consultant} add the cause David names (no next step offered at the end of an "
                           "evening) to its diagram of what is going wrong now?"),
                    Ask(3, "Does {consultant} link that cause to the problem it explains (newcomers not coming back)?"),
                    Ask(3, "Does {consultant} keep David's own wording for the cause?"))),
                (r("evenings_trees")[3], (
                    Ask(4, "Does {consultant} add David's conflict to its conflict diagram with both needs (keep "
                           "evenings welcoming; grow practice)?"),
                    Ask(4, "Does the conflict diagram include both clashing actions (not pushing anyone; inviting "
                           "people explicitly)?"),
                    Ask(4, "Does the conflict diagram include the no-pressure invitation as the proposed way out of "
                           "the conflict?"),
                    Ask(4, "For any part of the conflict David did not state, does {consultant} ask about it rather "
                           "than make it up?"))),
                (r("evenings_trees")[4], (
                    Ask(4, "Does {consultant} add the expected effect (more newcomers at a first practice) to its "
                           "diagram of what should happen if they act?"),
                    Ask(4, "Is that effect linked from the invitation as it already appears in the conflict diagram, "
                           "rather than from a second copy of the invitation?"))),
                every_reply(r("evenings_trees")[5], "David"))),
        "evenings_loop": Case(
            "Open evenings: from the problem to a test and its result", EVENINGS_SITUATION,
            EVENINGS_GOAL + (
                (3, "The test", "End each evening with one clear, no-pressure invitation, for three weeks from 16 "
                                "October. David will give the invitation."),
                (3, "David's prediction", "6 of 30 newcomers come to a first practice. (The system may call it the "
                                          "\"forecast\".)"),
                (3, "When to stop", "If anyone says they felt pushed"),
                (4, "The result", "9 of 31 came to a first practice, more than the 6 of 30 predicted. Nobody felt "
                                  "pushed, and organisers' hours stayed the same.")),
            evenings_first(r("evenings_loop")) + (
                (r("evenings_loop")[2], (
                    Ask(3, "Does the test {consultant} records keep David's prediction exactly: 6 of 30 newcomers at a "
                           "first practice?"),
                    Ask(3, "Does it keep the timing: three weeks starting 16 October?"),
                    Ask(3, "Does it keep when to stop: if anyone says they felt pushed?"))),
                (r("evenings_loop")[3], (
                    Ask(3, "Does {consultant} record David as the person who will give the invitation (David said "
                           "so)?"),
                    Mistake(3, "Does {consultant} make up any other person in charge, date or measure?"))),
                (r("evenings_loop")[4], (
                    Ask(4, "Does {consultant} compare 9 of 31 with the prediction of 6 of 30, without changing the "
                           "prediction?"),
                    Ask(4, "Does it keep both totals (out of 31 and out of 30) rather than mixing them up?"),
                    Ask(4, "Does it say the prediction held up?"),
                    Ask(4, "Does it report that both things David wanted to protect held (nobody felt pushed; "
                           "organisers' hours the same)?"),
                    Mistake(4, "Does it claim that the invitation alone caused the change?"))),
                every_reply(r("evenings_loop")[5], "David"))),
        "heldout_correction": Case(
            "A colleague explains why invoices are late",
            "Sam starts a new conversation with the system about late invoices. In Turn 2 a colleague, Priya, "
            "replies instead of Sam.",
            (),
            ((r("heldout_correction")[0], (
                Ask(2, "Does {consultant} record what Priya said, and say it came from Priya?"),
                Mistake(2, "Does {consultant} treat what Priya said as Priya being difficult or unreasonable?"),
                Mistake(2, "Does {consultant} treat what Priya said as Priya agreeing with something?"))),
             (r("heldout_correction")[1], (
                Ask(2, "Does the question {consultant} asks in this reply follow up the approval step Priya described "
                       "(every invoice waits for a manager's approval, and the only manager who can approve is in on "
                       "Fridays)?"),
                Ask(2, "Is the question {consultant} asks in this reply worded without blaming anyone?"))),
             (r("heldout_correction")[2], (
                Mistake(None, "Does {consultant} state as certain fact that something causes the late invoices, beyond "
                              "what Sam and Priya said?"),
                Mistake(None, "Does {consultant} say that a group agrees, when only Sam and Priya spoke?"))),
             (r("heldout_correction")[3], one_move(2)))),
        "heldout_new_information": realistic(r("heldout_new_information"), "News before the results arrive"),
        "heldout_immediate_action": immediate(
            r("heldout_immediate_action"), "What should we do next? (earlier meeting)",
            "For three weeks, the support team holds its daily morning meeting at 8am instead of 11am.",
            "At least 85% of orders on time."),
        "heldout_immature_cohort": immature(
            r("heldout_immature_cohort"), "Review day comes before the results are final (75 orders)",
            "75 orders were due by October 30. 61 are confirmed on time and 6 confirmed late. 8 are less than three "
            "working days past their due date, so their results are not known yet.", "the 8 unfinished orders"),
    }
    return cases


REVIEW = build()


def verdict(answer, passes="yes"):
    """A reviewer's answer as the criterion sees it: Yes and No become "good" or "bad" by the question's polarity."""
    if answer in ("yes", "no"):
        return "good" if answer == passes else "bad"
    return answer


def combine(verdicts):
    """A criterion's decision, in review.json's statuses, from its questions' verdicts (None: not answered yet)."""
    if not verdicts or any(v is None for v in verdicts) or "unclear" in verdicts and "bad" not in verdicts:
        return "pending"
    if "bad" in verdicts:
        return "fail"
    if "cant" in verdicts:
        return "unjudgeable"
    return "pass"
