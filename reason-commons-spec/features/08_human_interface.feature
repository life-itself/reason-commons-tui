@J02 @J05 @J06 @J09 @J14 @J15 @J16
Feature: Make rigorous local work discoverable through workspace controls
  All human workflows use visible controls and exact stored targets.
  Menus use selection and activation; editors and filters keep text literal.
  No alternate interactive command grammar can satisfy these scenarios.

  @S54 @p1 @v1 @automated
  Scenario Outline: Send numeric answers without selecting a menu item
    Given Response owns focus on a current question
    When Sam types "<answer>" then activates Send
    Then exactly one consultant request preserves the literal answer "<answer>"
    And no historical question or alternatives view opens

    Examples:
      | answer |
      | 1      |
      | 5      |
      | 17     |

  @S55 @p1 @v1 @automated
  Scenario: Activate a selected local alternative from its stored mapping
    Given Other moves is focused for "Choose a test"
    And its selected Inspect evidence item binds to this question's saved sources
    When Sam presses Enter
    Then stored evidence is shown locally
    And the live question, revision and consultant call count are unchanged

  @S56 @p1 @v1 @automated
  Scenario: Request a labeled consultant alternative once
    Given Other moves shows Ask another question labeled "asks consultant"
    When Sam selects that item with arrows and presses Enter
    Then one consultant request contains the stored intent and response target
    And there is no second confirmation for the same explicit request

  @S57 @p1 @v1 @automated
  Scenario: Keep an unmatched menu filter local
    Given Other moves filter owns focus and none of its labels contains "5"
    When Sam types "5" and presses Enter
    Then no item is activated and No matches appears with Clear filter and Back
    And no consultant request, commons update or revision is created
    And the response draft is retained

  @S58 @p1 @v1 @automated
  Scenario: Leave alternatives and send a literal numeric answer
    Given Other moves is open for "Choose a test"
    When Sam presses Esc, focuses Response, types "5" and activates Send
    Then exactly one semantic request contains "5"
    And it answers "Choose a test" without recording a menu decision

  @S59 @p4 @later @automated
  Scenario: Record an exact position using independent visible fields
    Given Priya is the declared speaker and L3 version 1 is selected
    When Priya activates Record position
    Then the exact formulation, conditions, actor and independent fields are shown
    And no substantive value is preselected or recorded
    When Priya selects Wording Accurate and Belief Disputed then activates Save position
    Then one atomic revision records both values on L3 version 1
    And reliance, other actors and the live question are unchanged
    And the receipt says "no consultant call"

  @S60 @p4 @later @automated
  Scenario: A wording objection is distinct from rejecting causal truth
    Given L3 version 1 is selected and Sam's belief is unknown
    When Sam opens Record position, selects only Wording Inaccurate and saves
    Then only representation inaccurate is recorded
    And Return to question offers a literal response for replacement wording
    And the interface does not invent wording or change belief

  @S61 @p4 @later @automated
  Scenario: Cancel a position form without changing reasoning
    Given a position form and a retained response draft
    When Sam activates Cancel or presses Esc
    Then the prior view and exact draft are restored
    And no stance, revision or consultant call is created

  @S62 @p4 @later @automated
  Scenario: Ask for an explicit target from a multi-object view
    Given the reasoning view contains several links and none is selected
    When Sam activates Record position from Actions
    Then a local target picker shows readable relationship labels and scope
    And no link is selected from creation order or semantic similarity
    And no stance or consultant call occurs before explicit selection

  @S63 @p1 @v1 @automated
  Scenario: Reject a stale menu before applying a decision
    Given Other moves is bound to "Choose a test" at revision 10
    And the commons advances to revision 11 with a different current question
    When Sam activates the old selected item
    Then the old choice is not dispatched against either question
    And current choices are redisplayed with a stale-menu notice
    And selecting again is required before dispatch

  @S64 @p4 @later @automated
  Scenario: Invalidate an actor-bound position form on speaker change
    Given Sam has an open position form
    When the operator activates Actions > Change speaker > Priya
    Then the form is invalidated and redisplayed for Priya with no substantive preselection
    And no Sam decision or draft is attributed to Priya

  @S65 @p3 @later @automated
  Scenario: Object evidence remains local and exact
    Given an object detail view selects L3 version 1
    When Sam activates Evidence
    Then evidence for L3 version 1 is rendered from stored records
    And Details identifies the exact same version and source references
    And neither action creates a call or reasoning revision

  @S66 @p4 @later @automated
  Scenario: Keep a historical target distinct from the live one
    Given Sam is inspecting L3 version 1 and version 2 is current
    When Sam activates Record position
    Then the form labels version 1 as a historical formulation
    And a selected stance attaches only to version 1
    And Response still answers the current question

  @S67 @p1 @v1 @automated
  Scenario: Keep substantive prose literal even when it resembles an action
    Given Response owns focus
    When Sam types "I disagree because overtime worsens" then activates Send
    Then one semantic request preserves the entire statement
    And no local parser infers representation, belief or reliance

  @S68 @p1 @v1 @automated
  Scenario: Compress routine context and repeat consequential changes
    Given Compact display and an unchanged goal and protections
    When Sam opens Explain this and returns to the current question
    Then the pinned header shows commons, save status and speaker, and the focused control is framed
    And complete unchanged context is not duplicated inside each view
    And the goal and consequential safeguard band remain pinned
    When the goal changes or Sam activates Goal or Commons context
    Then complete goal, horizon, protections, test boundaries, response target and revision appear
    And requesting context makes no consultant call

  @S69 @p1 @v1 @automated
  Scenario: Keep a consequential breach visible while browsing
    Given urgent acknowledgement is 90 percent against a 95 percent guardrail
    When Sam opens History, test sources or Other moves in Compact display
    Then the unresolved breach and both values remain visible
    And a delivery success marker does not obscure the breach

  @S70 @p1 @v1 @automated
  Scenario: Revalidate a restored menu before activation
    Given a checkpoint contains Other moves, focus, display preference, operator and draft
    When a fresh process resumes the commons
    Then it restores and validates the menu bindings
    And it shows complete startup context and labeled choices before accepting activation
    And no reasoning revision or consultant call occurs

  @S71 @p4 @later @automated
  Scenario: Reveal precision without changing the domain model
    Given a readable reasoning view with IDs omitted by default
    When Sam activates Details
    Then exact IDs, versions, sources and view-scoped action IDs appear
    And propositions, support, selection and response target are unchanged
    And Search and Help use stored context without a provider call

  @S72 @p1 @v1 @automated
  Scenario Outline: Keep offline shell utilities free of interactive furniture
    Given a saved valid commons and unavailable provider
    When the shell command "<command>" is invoked
    Then it exits 0 without a provider call
    And stdout contains only "<output>"
    And diagnostics if any go to stderr

    Examples:
      | command                                       | output                    |
      | reason-commons --help                          | requested help            |
      | reason-commons --version                       | version                   |
      | reason-commons inspect case.reasoncase --json   | one versioned JSON object |
      | reason-commons history case.reasoncase --json   | one versioned JSON object |

  @S73 @p1 @v1 @usability
  Scenario: Evaluate first-hour use through visible controls
    Given five first-time participants and a fake-consultant fixture
    When they attempt the documented first-hour tasks without a manual
    Then individual completion, time, repair, help and routing errors are recorded
    And at least four complete core tasks within 15 minutes without moderator instructions
    And all predict the local or consultant consequence before selecting an action
    And any accidental call, wrong test version or lost draft fails the proposed release gate
    And no numerical usability rating is inferred from these results
