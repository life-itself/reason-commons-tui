@J03 @J15 @J16
Feature: Make the interface legible and the consultant evaluable

  @S49 @p1 @v1 @automated
  Scenario: Retain critical context on a narrow terminal
    Given the accessible ordered text presentation in a terminal 40 columns wide and 16 rows high
    When a test review is rendered
    Then compact status shows focus, revision, and save status
    And the question shows its consequential goal and protected condition
    And the Case context control exposes complete current context locally
    And lines wrap without horizontal scrolling
    And additional content is explicitly paged
    And "NEXT", uncertainty, and control labels do not depend on color

  @S50 @p3 @later @automated
  Scenario: Explain a graph through equivalent prose
    Given an AND relationship from N1 and N4 to N3
    When Sam activates Reasoning > Read as text
    Then the output says both conditions must hold in the hypothesis
    And the same identifiers, conditions, and epistemic statuses remain available

  @S51 @p1 @v1 @automated
  Scenario: Preserve a multiline draft across navigation
    Given Sam is composing a multiline answer with an embedded command-looking line
    When Sam opens history and then returns to the editor
    Then the exact draft is retained
    And its embedded line has not been executed as a command
    And submission invokes the consultant only once

  @S52 @p2 @v1 @semantic
  Scenario Outline: Evaluate realistic semantic input by invariants rather than exact prose
    Given a documented case fixture and a live question
    When the participant submits "<input>"
    Then all contributed information is accounted for in the receipt
    And no unsupported causal certainty, identity verification, or group assent is invented
    And exactly one next move or a justified stopping point is prominent
    And any recorded update retains source references

    Examples:
      | input                                             |
      | I don't know                                      |
      | We cannot possibly do that                        |
      | Here are twelve more problems                     |
      | Your question is wrong                            |
      | Sales is lazy and Production never listens         |
      | Five possible causes, two observations, one demand |

  @S53 @p3 @later @automated
  Scenario: Measure useful progress without rewarding agreement
    Given a group corrects two causal links and completes a pilot review
    When the case progress view is opened
    Then it reports the corrections, evidence obtained, decisions, and reviewed predictions
    And it does not score agreement, reply count, or WIP depletion as success
    And learning measures require an actual reasoning task or later unaided performance

