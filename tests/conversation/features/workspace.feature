@conversation @automated
Feature: One persistent reasoning conversation across skill and local interfaces
  A participant works with the application's saved state.
  Local views explain and project it; only deliberate contributions consult.

  Scenario: Open an empty commons without inference
    Given a new commons
    When I open the next workspace
    Then the formal goal is unknown and no question has been invented
    And no consultation has occurred

  Scenario: Continue with literal participant text
    Given a saved question
    When David replies with literal multiline text to the displayed question
    Then the reply is attributed and saved against that exact question
    And the workspace presents the newly saved question
    And exactly one additional consultation has occurred

  Scenario: Resume and explain locally
    Given a saved question
    When I reopen the commons and inspect explanation, sources and history
    Then the stored rationale and original attributed text are available
    And the saved revision and consultant count are unchanged

  Scenario: Protect a reply from silent retargeting
    Given a question that another contribution has advanced
    When David replies to the previously displayed question
    Then the application reports stale and does not consult

  Scenario: Choose a consultant alternative explicitly
    Given a saved question
    When David explicitly asks for direct advice with literal text
    Then the saved input has the direct advice intent and the displayed anchor
    And exactly one additional consultation has occurred

  Scenario: Inspect results against the original forecast
    Given a completed pilot with recorded observations and a safeguard review
    When I open the tests workspace
    Then the original forecast and actual results remain distinct
    And the breached safeguard and work execution remain visible
    When I inspect the first published revision
    Then later observations and reviews are absent and only local moves are available

  Scenario: Draw only stored connections
    Given a saved goal and prospective test
    When I open the reasoning workspace
    Then its diagram links the test to its goal with the recorded meaning
    And no causal edge has been inferred from participant prose
