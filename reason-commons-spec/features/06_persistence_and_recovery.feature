@J14 @J15
Feature: Preserve the commons across sessions and failures
  Successful reasoning transactions produce complete immutable-by-policy YAML
  revisions. Navigation and drafts use a separate resumable cursor checkpoint.

  @S39 @p0 @v1 @automated
  Scenario: Resume without reconstructing the consultation
    Given a saved commons with a current question, attributed notes, a bounded test, and an answer draft
    When the participant quits and resumes the same commons in a new process
    Then the same reasoning revision, response target, view cursor, and draft are restored
    And the goal, notes, test, and last prediction are unchanged
    And resumption makes no consultant call

  @S40 @p0 @v1 @automated
  Scenario: Save every complete reasoning update without overwriting earlier revisions
    Given committed revision 13
    When a valid semantic response is committed
    Then a complete revision 14 is available with parent 13 and source input references
    And revision 13 remains byte-for-byte unchanged
    And the intervention and the goal, note, test or tree updates it proposes appear together
    And "saved" is shown only after the local commit succeeds

  @S41 @p3 @later @automated
  Scenario: Keep inspection read-only and rollback explicit
    Given revision 14 is current and revision 3 exists
    When Sam selects revision 3 in History and opens it
    Then revision 3 is displayed as historical and read-only
    And the commons remains at revision 14
    When Sam activates Restore reasoning, reviews source revision 3 and activates Append restored reasoning
    Then a new revision 15 reproduces revision 3's reasoning state
    And it records both revision 14 as parent and revision 3 as restored source
    And revision 14 is retained

  @S42 @p0 @v1 @automated
  Scenario: Export a portable handoff independent of provider conversation memory
    Given a saved commons containing interventions, sources, attributed notes, a goal, and a bounded test
    When Sam exports a ".reasoncase" bundle and imports it into a fresh process
    Then stable identifiers and revision ancestry are preserved
    And all referenced source records and the original prediction can be inspected offline
    And no hidden provider conversation is required
    And the imported commons opens without a consultant call

  @S43 @p0 @v1 @automated
  Scenario: Recover from a provider failure without losing or duplicating input
    Given Sam's input has been stored under request "in014"
    When the consultant adapter times out
    Then the current question and committed reasoning revision remain unchanged
    And "Input retained; consultant unavailable" is displayed with a visible Retry retained input control
    When Sam retries "in014" successfully
    Then the valid response creates exactly one committed intervention and one revision
    And the failed attempt is preserved separately from reasoning revisions

  @S44 @p0 @v1 @automated
  Scenario: Reject an invalid response without applying a partial update
    Given a stored semantic input and current revision 14
    When the adapter returns an unknown goal reference or an ownership claim without cited explicit input
    Then no intervention or commons update is committed
    And the input and failure receipt remain available
    And a local recovery message explains the next available action

  @S45 @p0 @v1 @automated
  Scenario: A save failure never looks like a saved commons
    Given the commons store cannot complete a durable write
    When the participant submits an answer
    Then "not saved" is visible
    And no consultant call begins if the raw input cannot first be retained
    And the text remains in the editor or memory while the process is open
    And the participant can copy it or choose a writable export destination

  @S46 @p0 @v1 @automated
  Scenario: Detect stale work instead of silently overwriting another update
    Given an adapter request was based on revision 14
    And a reply to another input has advanced the commons to revision 15 with a new question
    When that adapter response arrives
    Then it is not applied to revision 15
    And the receipt offers a re-evaluation against the current revision
    And no last-write-wins merge is performed

  @S47 @p1 @v1 @automated
  Scenario: Keep offline navigation useful
    Given a saved commons and an unavailable consultant adapter
    When Sam opens options, rationale, history, or the bounded test
    Then every stored view works without the adapter
    And semantic work is clearly pending until an adapter is available

  @S48 @p0 @v1 @automated
  Scenario: Ordinary dated files do not imply tamper-proof evidence
    Given the store uses YAML revisions and content hashes
    When Sam opens storage help
    Then it explains that the app never overwrites committed revisions
    And it does not claim protection from an owner editing files outside the app

