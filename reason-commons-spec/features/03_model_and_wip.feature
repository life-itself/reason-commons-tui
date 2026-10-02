@J07 @J08 @J10
Feature: Earn coherence without manufacturing certainty
  Model membership and support are separate attributes.
  Disconnected contributions stay visible in WIP.

  @S14 @p3 @later @semantic
  Scenario: Keep a relevant observation outside the graph until connected
    Given a partial model of priority changes and late orders
    When Sam submits "Suppliers are often late and new hires take weeks to become productive"
    Then both contributions receive stable WIP identifiers and source references
    And the existing causal graph is not given invented arrows
    And the receipt reports "2 reports retained in Unlinked"
    And one prominent question offers a useful move on the current focus

  @S15 @p3 @later @semantic
  Scenario: Promote a WIP item through an explicit causal formulation
    Given "W1" says "Orders finish late"
    And "W2" says "Priorities change during the week"
    When Sam submits "Changing priorities contributes to late orders when unfinished work is high because active jobs are interrupted"
    Then the model contains the reported propositions and hypothesized relationships
    And the joint causes are represented with an AND group
    And W1 and W2 remain retrievable through their original source records
    And the new relationships are not labeled empirically established

  @S16 @p3 @later @automated
  Scenario: Show a diagram only when it earns its space
    Given two conditions jointly lead to one reported effect
    When a question asks whether either condition alone is enough
    Then a diagram shows the two conditions, an AND junction, and the effect
    And uncertain links are marked and explained in text
    And the workspace includes only the mechanism needed for the question
    And no decisive condition is omitted to meet a node-count target

  @S17 @p2 @v1 @automated
  Scenario: Show no diagram for a question it would not clarify
    Given the next useful move is to name an experiment owner
    When the question is rendered
    Then it asks for the owner without a decorative causal diagram

  @S18 @p3 @later @semantic
  Scenario: Preserve contradictory claims instead of resolving them silently
    Given L3 claims that interrupted jobs contribute to late completion
    When Priya submits "Priority changes may follow threatened dates rather than cause them"
    Then the alternative is stored with Priya's attribution
    And L3 can remain in the working model while disputed
    And the next question requests evidence that could distinguish the directions
    And neither participant's claim is overwritten

  @S19 @p3 @later @automated
  Scenario: Capture literally without interpretation
    Given a current question and 2 WIP items
    When Sam activates Actions > Capture report, types "Morale feels worse after the second shift" and saves locally
    Then the exact text is added as an unclassified WIP item
    And the reasoning revision advances once
    And the consultant call count does not change
    And the current question remains the response target

  @S20 @p3 @later @automated
  Scenario: Connect known objects locally when the human supplies every relation field
    Given W1 and W2 are unconnected reported observations
    When Sam selects the two reports and activates Add relationship
    And supplies input Priorities change, output Orders finish late, condition "high WIP" and basis Hypothesis
    And activates Save relationship - local
    Then a human-authored conditional hypothesis is recorded
    And the items are included in the model through that relationship
    And the original wording, attribution, and earlier revision remain available
    And no consultant call or claim of validation is made

  @S21 @p3 @later @semantic
  Scenario: Do not infer a merge from similar wording
    Given W4 says "Morale is falling"
    When another participant captures "People seem discouraged"
    Then both source records are preserved
    And a possible duplicate may be suggested on the next semantic turn
    And merging requires an explicit decision about the intended meaning

  @S22 @p3 @later @semantic
  Scenario: Challenge a constraint hypothesis at the system level
    Given a large production queue and low on-time delivery
    When Sam submits "The largest queue must be our constraint"
    Then the consultant asks what improving that queue would change in the chosen goal and horizon
    And it requests evidence about effective capacity, load, and downstream absorption when relevant
    And a queue alone is not stored as a confirmed system constraint

  @S23 @p3 @later @semantic
  Scenario: Preserve units, periods, and denominators
    Given a baseline of 32 on-time orders out of 50 orders due in September
    When Sam reports "20 completed orders this week proves we improved"
    Then the receipt retains the new report with its period
    And the consultant asks for orders due and on-time completions for a comparable cohort
    And the old baseline is not replaced with an incomparable percentage

