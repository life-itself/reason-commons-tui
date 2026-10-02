@J10 @J11 @J12 @J13
Feature: Turn a defensible next move into learning

  @S30 @p2 @v1 @semantic
  Scenario: Test before completing every Thinking Process tree
    Given two plausible explanations would lead to the same low-cost bounded test
    When the group asks what to do next
    Then the consultant may recommend that test with the uncertainty visible
    And completing a CRT, Cloud, FRT, PRT, and Transition Tree is not a prerequisite

  @S31 @p5 @later @semantic
  Scenario: Inspect a consequential adverse effect
    Given the group proposes freezing the plan while reserving urgent capacity
    When the consultant evaluates the proposal
    Then a partial future model marks its effects as predictions
    And the most consequential credible negative branch is shown
    And the next prompt asks for a prevention or stopping condition

  @S32 @p2 @v1 @automated
  Scenario: Record a prospective pilot with enough detail to review
    Given the group has supplied a baseline and a proposed bounded change
    When Sam commits to a pilot
    Then the pilot records the following review fields:
      | field                  |
      | owner and scope        |
      | intervention and dose  |
      | baseline and cohort    |
      | exact prediction       |
      | measurement method     |
      | observation window     |
      | protected conditions   |
      | stopping conditions    |
      | alternative explanation|
      | review date            |
    And unknown fields remain visibly unknown
    And the prediction is versioned before the outcome is supplied

  @S33 @p5 @later @semantic
  Scenario: Convert an implementation obstacle into a necessary intermediate objective
    Given the pilot cannot begin because no one owns urgent-request triage
    When the group examines the obstacle
    Then the workspace identifies "Every urgent request has an accountable triage owner" as a necessary condition
    And a next action names an owner and timing if supplied
    And "Solve triage" alone is not presented as an executable plan

  @S34 @p2 @v1 @semantic
  Scenario: Show the original prediction before interpreting a result
    Given pilot P1 predicted at least 80% on-time completion
    And its original responsiveness guardrail was at least 95% acknowledged within 24 hours
    When Sam reports 40 of 50 on time and 18 of 20 timely acknowledgements
    Then the review compares 80% with the unchanged delivery prediction
    And it compares 90% with the unchanged 95% responsiveness guardrail
    And the forecast is supported on delivery while the guardrail is breached
    And the next move addresses the breach before expansion

  @S35 @p2 @v1 @semantic
  Scenario: Improvement is not proof of a unique cause
    Given a pilot improved delivery while changing both release rules and urgent-request handling
    When the result is reviewed
    Then the result can support the bounded intervention
    And the causal explanation remains non-unique
    And supplier timing and order mix are checked as relevant alternatives

  @S36 @p2 @v1 @semantic
  Scenario Outline: Classify a review according to what actually happened
    Given a pilot with an unchanged prospective prediction
    And the review evidence is "<evidence>"
    When the group submits the outcome
    Then the affected prediction is classified as "<classification>"
    And the original forecast and source reports remain available

    Examples:
      | evidence                                          | classification         |
      | planned dose, comparable measures, target reached  | supported prediction   |
      | planned dose, comparable measures, target missed   | contradicted prediction|
      | the intervention never started                    | implementation failure |
      | the outcome denominator is unknown                | inconclusive           |

  @S37 @p2 @v1 @automated
  Scenario: A review date is not a scheduled automation
    Given a pilot has a review date of October 19
    When the pilot is saved
    Then the view says "Review October 19; no reminder scheduled"
    And no calendar event, message, background job, or external action is created

  @S38 @p3 @later @semantic
  Scenario: Recheck the constraint after improvement
    Given a bounded change improves delivery without proving the previous diagnosis
    When the group decides its next step
    Then the consultant asks what now limits the goal in the remaining horizon
    And it preserves useful practices while questioning any that no longer serve the goal

