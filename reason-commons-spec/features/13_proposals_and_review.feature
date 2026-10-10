@J07 @J08 @J14 @J17
Feature: Decide what enters the model
  The consultant drafts what the operator's words could mean; the operator decides
  what enters the model. The goal, the six trees and the tests are one model, and
  every change the consultant proposes to any part of it waits in the backlog with
  its source until the operator accepts it, unless the operator has set the commons to
  accept proposals automatically. The backlog lists proposals in the order they are
  best decided. A change asks for review of whatever explicitly cites what it
  changed, and every acceptance can be undone. Accepting admits a statement into the
  working model; it does not make it true or record anyone's belief.

  @S135 @p2 @v1 @automated
  Scenario: Hold a reply's proposals in the backlog by default
    Given a commons whose goal is "A clear next step after open evenings"
    When the operator says "Newcomers do not know the next step, because we never offer one"
    And the consultant proposes a symptom, a cause and a causes link citing that input
    Then the consultant's next question becomes the live question
    And the symptom, the cause and the link wait in the backlog, each citing the operator's words
    And the Current Reality Tree is unchanged
    And a confidence the consultant gave is kept with each proposal without deciding anything

  @S136 @p2 @v1 @automated
  Scenario: Accept a reply's proposals together
    Given the backlog holds a symptom, a cause and a causes link proposed from one input
    When the operator accepts all three
    Then one new revision adds them to the Current Reality Tree without a consultant call
    And the revision records who accepted them, when, and that they were accepted explicitly
    And the cause keeps its basis, so an accepted hypothesis is still a hypothesis
    And the backlog is empty and the live question and draft are unchanged

  @S137 @p2 @v1 @automated
  Scenario: Reject a proposal together with what needs it
    Given the backlog holds a symptom, a cause and a causes link proposed from one input
    When the operator rejects the cause
    Then the operator is shown that the link, which needs the cause, is rejected with it
    When the operator confirms
    Then the cause and the link leave the backlog and the symptom still waits
    And the commons history keeps both rejected proposals with the operator's decision
    And neither can be accepted later

  @S138 @p2 @v1 @automated
  Scenario: List the backlog in the order it is best decided
    Given the backlog holds, from earlier replies, a Transition Tree action, a Current Reality cause, a causes link from that cause and a new version of the goal
    When the operator opens the backlog
    Then the new version of the goal comes first, marked to be decided first because the rest is judged against it
    And the cause comes before its link, which says it waits for the cause
    And the Current Reality proposals come before the Transition Tree action
    When the operator accepts the link
    Then the operator is shown that the cause is accepted with it
    And after confirming, both are in the Current Reality Tree while the new goal still waits

  @S139 @p2 @v1 @automated
  Scenario: Accept proposals automatically when the operator has chosen to
    Given a commons set to accept proposals automatically
    When the consultant proposes a symptom, a cause and a causes link citing the operator's words
    Then the revision that publishes the next question also adds all three to the Current Reality Tree
    And it records that they were accepted automatically under the operator's setting
    And the operator can undo that acceptance like an explicit one

  @S140 @p2 @v1 @automated
  Scenario: Only the operator changes how proposals are accepted
    Given a commons that holds proposals for review, with two proposals waiting
    When the operator sets the commons to accept proposals automatically
    Then a revision records the operator's choice without a consultant call
    And the two proposals already waiting still wait
    And a consultant reply that tries to change the setting is rejected before commit

  @S141 @p2 @v1 @automated
  Scenario: Undo an accepted change without rewriting history
    Given the Current Reality Tree holds an accepted cause with its causes link and a later accepted symptom that cites neither
    And a waiting proposal links another statement to the cause
    When the operator undoes the acceptance of the cause
    Then the operator is shown that the link leaves the tree with it and the waiting proposal is closed
    When the operator confirms
    Then a new revision removes the cause and its link from the tree and keeps the later symptom
    And the commons history keeps the operator's words, the proposals, their acceptance and the undo
    And the undo is final: it cannot be undone and the cause does not return to the backlog

  @S142 @p2 @v1 @automated
  Scenario: Ask for review of what cites a changed statement
    Given an accepted Conflict tree injection, a Future Reality link from that injection to a desired effect, and a test that carries out the injection
    When the operator accepts a new wording of the injection
    Then the link and the test are flagged for review, each naming the change that raised the flag
    And neither is changed, withdrawn or marked false
    And both flags wait in the backlog
    When the operator marks the test as still holding
    Then the test's flag closes with the operator's decision recorded and the link's flag stays open

  @S143 @p2 @v1 @automated
  Scenario: Let a change cascade one explicit step at a time
    Given an accepted Conflict tree requirement, an injection linked to it, and a Future Reality link from that injection to a desired effect
    When the operator accepts a new wording of the requirement
    Then the Conflict tree link between the injection and the requirement is flagged for review
    And the Future Reality link is not flagged, because nothing it cites has changed
    When the consultant proposes a new wording of the injection and the operator accepts it
    Then the Future Reality link is flagged for review in turn
    And the backlog names, for each flag, the change that raised it

  @S144 @p2 @v1 @automated
  Scenario: Keep one goal at the top of the Goal Tree
    Given a commons whose goal is "At least 90% of orders on time by October 30"
    When the consultant proposes a critical success factor that the goal requires and the operator accepts it
    Then the Goal Tree shows the commons' goal at its top with the factor beneath it
    And the Goal view and the Goal Tree show the same goal
    When the consultant proposes a second goal that is not a new version of the current one
    Then the proposal is rejected before commit because a commons has one goal

  @S145 @p2 @v1 @automated
  Scenario: Use a statement from another tree in a link
    Given an accepted Conflict tree injection
    When the consultant proposes a desired effect and a Future Reality link from that injection to it
    And the operator accepts both
    Then the Future Reality Tree draws the injection, marked as from the Conflict tree, leading to the desired effect
    And the injection stays one statement, so its new wording shows in both trees
    And a link whose two statements both belong to other trees than its own is rejected before commit

  @S146 @p2 @v1 @automated
  Scenario: Decide proposals while the consultant is working
    Given the operator has sent an answer and the consultant has not replied
    When the operator accepts a waiting proposal
    Then the consultant's reply is published when it arrives rather than treated as stale
    And its proposals are checked against the model as it stands after that acceptance

  @S147 @p2 @v1 @automated
  Scenario: Ask the consultant to draft amendments for open reviews
    Given two accepted statements flagged for review
    When the operator asks the consultant about the open reviews
    Then one consultant request carries the flagged statements and the changes that raised the flags
    And the amendments it proposes wait in the backlog like any other proposal

  @S148 @p2 @v1 @automated
  Scenario: Withdraw a statement together with the links that join it
    Given the Current Reality Tree holds an accepted cause with its causes link and a test that carries out the cause
    And the consultant proposes withdrawing the cause
    When the operator accepts the withdrawal
    Then the operator is shown that the link leaves the tree with the cause and the test is flagged for review
    And nothing changes until the operator confirms
    When the operator confirms
    Then a new revision removes the cause and its link from the tree and the test's flag waits in the backlog
    And in a commons set to accept proposals automatically, the same withdrawal waits for the operator

  @S149 @p2 @v1 @automated
  Scenario: Cite only words the commons has taken in
    Given an answer the operator sent became stale before the consultant replied to it
    When the operator sends another answer
    Then the consultant's request does not carry the stale answer
    And a reply whose proposal cites the stale answer is rejected before commit, leaving the commons unchanged
    And the stale answer stays retained with its source, so the operator can send it again

  @S150 @p2 @v1 @automated
  Scenario: Revise a test's forecast only before its first result
    Given an accepted test forecasting "6 of 30" and an accepted action that carries it out
    When the operator accepts a new version of the test forecasting "8 of 30"
    Then the Tests view shows one test with the new forecast, and the commons history keeps the earlier one
    And the action is flagged for review because it was planned for the earlier version
    When a result is reported for the test and accepted
    Then a further new version of the test is rejected before commit, so the forecast stays as it was before the result
    And a result citing the earlier version of the test is rejected before commit
