@J02 @J03 @J05 @J06 @J07 @J09 @J12 @J13 @J14 @J15 @J16
Feature: Work in a persistent terminal workspace from the first usable release
  These are default TUI requirements, required in both standard and accessible presentations.
  Screen specimens specify visible behavior; a runtime and participant protocol
  are required to exercise them. Structural document checks cannot pass them.

  @S114 @p1 @v1 @automated
  Scenario: Launch the persistent workspace by default
    Given interactive terminal input and output at 120 columns by 40 rows
    When the operator launches a new commons without a presentation flag
    Then the full-screen workspace shows the question, response editor, destinations and footer
    And save status, declared operator and focused control remain visible
    And no tour or command syntax is required to answer or leave

  @S115 @p1 @v1 @automated
  Scenario: Treat all printable response text literally and submit deliberately
    Given the response editor is focused on current question "Choose a test"
    When the operator types or pastes "5 ? q / :options" and presses Enter
    Then those characters and the newline are retained in the draft
    And no navigation, quit, stance or consultant request occurs
    When the operator Tabs to Send and presses Enter
    Then exactly one request preserves the full literal draft for "Choose a test"

  @S116 @p1 @v1 @automated
  Scenario: Restore the question and exact draft after optional inspection
    Given a partially edited response with caret position and current question "Choose a test"
    When the operator opens Explain this and a stored source then returns with Esc
    Then the originating view, selection, semantic scroll anchor and draft caret are restored
    And the live response target remains "Choose a test"
    And no commons revision or consultant call is created

  @S117 @p1 @v1 @automated
  Scenario: Keep the first-release workspace usable at minimum terminal size
    Given a v1 goal and test with a material safeguard at 120 columns by 40 rows
    When the terminal resizes to 80 columns by 24 rows and back
    Then the question, safeguard, response and footer remain reachable and readable
    And hidden auxiliary panes have a visible Views destination
    And the draft, target, focus and selected exact record survive without restart

  @S118 @p1 @v1 @automated
  Scenario: Complete a consultant response without stealing inspection focus
    Given a durably retained submission and pending consultant request
    And the operator has selected a source in History
    When a valid next response completes
    Then an Answer ready notice is visible without changing the selected source or focus
    And returning to Next presents the committed next question
    And no second request or duplicate commit occurs

  @S119 @p1 @v1 @automated
  Scenario: Expose every required action without recalled commands
    Given the default TUI and focused response editor
    When the operator reaches Actions or Help using Tab and Enter
    Then the displayed controls identify valid actions and local or consultant consequences
    And stored explanation, sources, history, export and Save and quit have control paths
    And Help for controls is distinct from Explain this for reasoning

  @S120 @p1 @v1 @automated
  Scenario: Recover a failed request while retaining the workspace
    Given a retained response draft and provider failure after input retention
    When the operator opens the failure receipt and retries the retained input
    Then the receipt distinguishes input retained from uncommitted reasoning
    And retry uses the same request identity and applies at most once
    And view state, draft provenance and the correct live target remain recoverable

  @S121 @p2 @v1 @automated
  Scenario: Compare the original pilot forecast with outcomes inside the workspace
    Given an original pilot delivery forecast of 80 percent and acknowledgement bound of 95 percent
    And reported delivery is 80 percent and acknowledgement is 90 percent
    When the review screen is rendered
    Then original forecast and actual result are aligned by measure with scope and denominators
    And the acknowledgement breach remains visible despite delivery success
    And action execution, observed effects and the 90 percent system goal are distinct

  @S122 @p2 @v1 @semantic
  Scenario: Keep immature cohort outcomes pending at a review date
    Given a rolling October 1 through 30 cohort with a three-business-day outcome window
    When the operator reviews it on October 30 with final outcomes still immature
    Then the review retains the original forecast and labels those outcomes pending
    And it requests complete follow-up before claiming goal attainment
    And missing observations are not treated as failures or successes

  @S123 @p3 @later @automated
  Scenario: Render a joint causal inference with complete readable boundaries
    Given L3 has three joint premises including net unrecovered recheck time exceeding slack before release cutoff
    When the causal fragment is rendered
    Then all three premises are enclosed or joined by one explicit ALL operator
    And exactly one labeled hypothesis output terminates at its conclusion
    And independent alternative routes do not become extra members of that ALL

  @S124 @p3 @later @automated
  Scenario: Inspect one exact relation without losing the broader map
    Given a stored branch index and causal map at 120 columns by 40 rows
    When the operator selects L3 version 1
    Then the inspector shows its complete scope, inputs, output, warrant, sources and objections
    And occurrence evidence for nodes is not represented as proof of L3
    And selection is distinct from focus, support and endorsement

  @S125 @p3 @later @automated
  Scenario: Replace a narrow drawing with complete relation sentences
    Given L3 version 1 is disputed and has three joint premises
    When its view resizes through 120 by 40, 80 by 24 and 40 by 24
    Then the same exact premises, negations, conclusion, dispute and live target are retained
    And the narrow view says IF ALL and THEN instead of clipping node labels
    And no decisive premise remains collapsed while endorsement is requested

  @S126 @p4 @later @automated
  Scenario: Keep positions independent and drafts attributed when speakers change
    Given Maya has an unsent response and a position form for L3 version 1
    When the operator switches the declared speaker to Leo
    Then Maya's draft remains attributed to Maya and cannot be submitted as Leo's answer
    And the actor-bound position form is invalidated and redisplayed for Leo
    And wording, belief and exact-test reliance have independent controls with no substantive preselection
    And no assent, belief, reliance or consensus is inferred from the switch

  @S127 @p5 @later @automated
  Scenario: Display cross-tool consequences without converting trace references into causes
    Given a corrected claim has exact registered dependencies in Cloud, FRT and PRT records
    When the correction is inspected in the workspace
    Then before and after versions are aligned and each registered dependency says review needed
    And trace links name their dependency meaning and are excluded from causal traversal
    And historical positions, prior observations and action execution remain on their original records
    And the view does not claim the dependency list exhausts real-world consequences
