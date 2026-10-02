@J09 @J11
Feature: Represent a group's positions and conflicts faithfully

  @S24 @p4 @later @automated
  Scenario: Distinguish a faithful representation from belief
    Given L3 version 1 is a disputed causal hypothesis
    When Priya selects L3 version 1, opens Record position, chooses only Wording Accurate and saves
    Then her representation stance is recorded for that exact formulation
    And her belief remains disputed
    And other participants' stances remain unknown

  @S25 @p4 @later @automated
  Scenario: Reliance on a test does not establish belief or consensus
    Given pilot P1 version 1 has a prospective prediction
    When Sam selects pilot P1 version 1, opens Record decision, chooses Will run this bounded test and saves
    Then Sam's willingness to run that bounded pilot is recorded
    And no group's unanimous assent is inferred
    And disputed causal claims remain disputed

  @S26 @p4 @later @semantic
  Scenario: Attribute reported positions without claiming direct assent
    When Sam submits "Priya thinks the model is wrong"
    Then the source is Sam's report of Priya's position
    And Priya is not marked as directly endorsing a stance

  @S27 @p4 @later @automated
  Scenario: Do not carry agreement onto a substantively changed formulation
    Given Priya marked L3 version 1 as an accurate representation
    When the condition and effect of L3 are substantively revised
    Then the new formulation has a new version
    And the old stance remains attached to version 1
    And Priya's stance on the new version is unknown

  @S28 @p4 @later @semantic
  Scenario: Represent a conflict as legitimate needs and incompatible actions
    Given Sales wants responsiveness and Production wants dependable execution
    When the group explains why Sales changes the committed plan and Production freezes it
    Then a partial Cloud shows their shared objective and both needs
    And the conflicting actions are "Change the committed plan now" and "Keep the committed plan unchanged"
    And the assumptions making those actions seem necessary are inspectable
    And neither need is described as the obstacle to be defeated

  @S29 @p4 @later @semantic
  Scenario: Respect a real incompatibility
    Given two obligations require the same exclusive resource at the same time
    And no workable alternate arrangement is known
    When the group asks to resolve the conflict
    Then the consultant can describe the unresolved tradeoff and decision owner
    And it does not assert that every conflict has an evaporating solution

