@J05 @J06 @J16
Feature: Navigate without asking the consultant to think
  Retrieval is local. Explicit structured decisions may also be local.
  Focus determines whether a key edits, filters, selects or activates a control.
  Response text is literal and reaches the consultant only through Send.

  Background:
    Given the persistent TUI workspace is active
    And case "forge" at revision 10 with current question "Choose a test"
    And History contains the earlier questions "Define success" and "Inspect the baseline"
    And the consultant call counter is 8

  @S07 @p1 @v1 @automated
  Scenario Outline: Open a stored view using its visible control
    When the participant activates "<control>" using Tab and Enter
    Then the view "<view>" is rendered from stored state
    And the consultant call counter remains 8
    And the reasoning revision remains 10

    Examples:
      | control                          | view                           |
      | Other moves                      | alternatives for this question |
      | History                          | questions and event history    |
      | Explain this                     | authored rationale             |
      | History > Define success         | archived Define success        |
      | History > Inspect the baseline   | archived Inspect the baseline  |
      | Help                             | control help                   |
      | Actions > Consultant calls       | adapter call count             |
      | Backlog                          | proposals waiting for decision |

  @S08 @p1 @v1 @automated
  Scenario: Send a numeric answer from the literal editor
    Given Response owns focus
    When the participant types "5" then activates Send
    Then exactly one consultant request contains the literal answer "5"
    And neither the alternatives nor a historical question opens

  @S09 @p1 @v1 @automated
  Scenario: Send text resembling a shortcut without an escape command
    Given Response owns focus
    When Sam types "q" then activates Send
    Then exactly one consultant request contains the literal answer "q"
    And the session does not quit

  @S10 @p1 @v1 @automated
  Scenario: Keep a misspelled action filter local
    Given Actions filter owns focus
    When Sam types "histroy"
    Then the interface shows no match with Clear filter and Back controls
    And no consultant call or reasoning revision is created
    And the filter and current response draft are retained

  @S11 @p1 @v1 @automated
  Scenario: Keep the current question stable while browsing
    When Sam opens History > Define success and presses Esc
    Then the previous view and draft are restored
    And the live response target remains "Choose a test"
    And quoting the historical question in Response does not change that target

  @S12 @p1 @v1 @automated
  Scenario: Distinguish a stored view from another consultant move
    Given Other moves contains Inspect rationale and Ask another question
    When Sam opens Other moves
    Then Inspect rationale says "local; opens saved explanation"
    And Ask another question says "asks consultant"
    When Sam selects Inspect rationale and presses Enter
    Then no consultant request is made
    When Sam returns and activates Ask another question
    Then one request contains the stored intent and current response target

  @S13 @p1 @v1 @automated
  Scenario: Explain the question through public supporting material
    Given the current question has stored rationale and evidence references
    When Sam activates Explain this
    Then the rationale and referenced reports are displayed
    And the view makes no claim to expose a private model thought trace
    And Esc restores the originating view and draft

  @S90 @p3 @later @automated
  Scenario Outline: Open a structured reasoning view locally after the causal release
    Given the causal delivery profile and stored records for "<control>"
    When the participant activates "<control>"
    Then the view "<view>" is rendered from stored state
    And the consultant call counter remains 8
    And the reasoning revision remains 10

    Examples:
      | control                        | view                  |
      | Reasoning                      | partial working model |
      | Unlinked                       | unlinked reports      |
      | Reasoning > Assumptions         | assumptions           |
