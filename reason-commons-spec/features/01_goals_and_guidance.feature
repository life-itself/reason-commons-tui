@J01 @J02 @J03 @J04
Feature: Help a group make its next reasoning move
  The group does the consequential thinking; the consultant supplies structure,
  feedback, and a useful next question or recommendation.

  Background:
    Given a writable case store
    And an available consultant adapter

  @S01 @p2 @v1 @semantic
  Scenario: Begin with a situation rather than a TOC questionnaire
    Given a new case with no agreed goal
    When Sam submits "Late deliveries, changing priorities, overtime, and falling morale"
    Then the input is preserved with Sam's declared attribution
    And one prominent question asks what meaningful progress would look like and what must be protected
    And the visible context labels the goal as provisional
    And the effects are proposed as attributed notes with no invented relationships

  @S02 @p2 @v1 @semantic
  Scenario: Record a goal without inventing agreement or measures
    Given Sam proposes "At least 90% of orders on time by October 30"
    When the consultant creates the next useful response
    Then the goal it proposes records Sam as its source
    And absent baseline, scope, and protected conditions are shown as unknown
    And no other participant is recorded as agreeing
    And the next prompt addresses the most consequential missing item

  @S03 @p2 @v1 @automated
  Scenario: Show one recommended move and keep other paths available
    Given a bounded test proposal whose observation criterion is unknown
    When its current question is rendered
    Then exactly one primary prompt is visually distinguished from its decision context
    And the prompt asks the operator to supply the observation criterion
    And alternatives are available through visible "Other moves" controls
    And the foreground does not include an unsolicited TOC lesson

  @S04 @p2 @v1 @automated
  Scenario: Keep the information that changes the answer beside the question
    Given the current question concerns a pilot that may increase overtime
    And the case protects "Overtime at most 20 hours per week"
    When the pilot workspace is rendered
    Then the consequential goal and protected condition appear beside the question
    And compact status shows current focus, revision, and save status
    And an estimate is not relabeled as a measurement
    And the pilot workspace shows the relevant baseline and period

  @S05 @p3 @later @semantic
  Scenario: Change coaching style without forcing a discovery exercise
    Given the group has a working causal hypothesis
    When Sam activates Actions > Coaching > Direct advice
    And submits "Give us two concrete ways to test this"
    Then the preference change makes no consultant call
    And the semantic request produces ranked, concrete tests with tradeoffs
    And the group is not required to answer another Socratic question first

  @S06 @p2 @v1 @semantic
  Scenario: Treat an unclear or uncomfortable question as useful input
    Given a current question asks why Sales "disrupts" production
    When Priya submits "That wording blames us and does not fit what happens"
    Then the consultant preserves the correction
    And the next question uses neutral language about the scheduling mechanism
    And no record treats the correction as assent or irrational resistance

