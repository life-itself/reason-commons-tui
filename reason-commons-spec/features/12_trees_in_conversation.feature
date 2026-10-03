@J03 @J07 @J11 @J12 @J14
Feature: Grow the six thinking-process trees in conversation
  The trees use the LTP 1.0 vocabulary of the reasoncommons guide: a claim is one
  sourced statement in one tree with a role; a link is one typed relation between
  two claims of the same tree. Joint premise groups, rival routes and dependent
  review stay with the later causal and full-tools releases.

  @S128 @p2 @v1 @automated
  Scenario: Record a reported cause and its effect in the Current Reality Tree
    Given a case whose goal is "A clear next step after open evenings"
    When the operator says "Newcomers do not know the next step, because we never offer one"
    And the consultant proposes a symptom, a cause and a causes link citing that input
    Then the Current Reality Tree holds both statements and the link
    And the literal input remains the source of all three
    And the Trees view draws the symptom above its cause, labelled "because"

  @S129 @p2 @v1 @automated
  Scenario Outline: Reject a tree record that breaks the tree grammar
    Given a case whose goal is "A clear next step after open evenings"
    When the consultant proposes <record> with an ordinary note
    Then the entire proposal is rejected before commit
    And the raw input and failure receipt remain available

    Examples:
      | record                                              |
      | a goal role in the Current Reality Tree             |
      | a link between claims of two different trees        |
      | a link from a claim to itself                       |
      | a link to a claim proposed after the link           |
      | a link with a relation outside the LTP vocabulary   |

  @S130 @p2 @v1 @automated
  Scenario: Reword and withdraw without rewriting history
    Given a Current Reality Tree with a symptom, a cause and a causes link
    When the operator asks to word the cause more precisely and the consultant replaces it
    Then the tree shows the new wording, still linked to the symptom
    And the earlier wording stays in the case history
    When the operator withdraws the cause and the consultant records the withdrawal with a reason
    Then the tree no longer shows the cause or its link
    And a later proposal linking the withdrawn cause is rejected before commit

  @S131 @p2 @v1 @automated
  Scenario: Connect a test to the tree action it carries out
    Given a Transition Tree action "Prototype one next step after open evenings"
    When the operator records a test with a forecast that carries out that action
    And reports an observation for the test
    Then the Trees view shows the test's original forecast and reported result under the action
    And the test's original forecast is unchanged

  @S132 @p2 @v1 @automated
  Scenario: Bring in trees from an LTP file without inferring anything
    Given a case in the middle of the goal-action-review loop
    And an LTP 1.0 file with six statements, two single-premise links, one joint-premise link and one assessment
    When the operator brings in the file
    Then the file is retained as a source and every imported statement and link cites it
    And the joint-premise link and the assessment are kept as labelled notes
    And the current question carries on from the same step
    And the consultant is not called

  @S133 @p2 @v1 @automated
  Scenario: Export the trees and bring them back unchanged
    Given a case with imported trees
    When the operator exports the trees to a new LTP file and brings that file into a new case
    Then both cases show the same statements, roles, links and assumptions
    And exporting to an existing file is refused

  @S134 @p2 @v1 @automated
  Scenario: Browse the trees locally
    Given a case with imported trees
    When the operator opens the Trees view and then returns to the current question
    Then no consultant call and no revision occurs
