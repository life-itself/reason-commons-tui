@J03 @J05 @J06 @J14 @J15 @J16 @J17
Feature: Continue useful work through the accepted minimal interface
  The sidebar follows recorded work. Commands retains the supporting capabilities.
  Offline fixtures establish observable behavior, not useful live consulting.

  @S176 @p4 @v1 @automated
  Scenario Outline: Reach supporting views even when the imported sidebar omits them
    Given the adopted RC import in the terminal workspace
    Then the sidebar omits the empty supporting view "<view>"
    When the operator chooses "View: <label>" through Commands
    Then the supporting view "<view>" opens locally with the live target unchanged

    Examples:
      | view      | label           |
      | tests     | Tests           |
      | actions   | Loop actions    |
      | reasoning | Reasoning       |
      | context   | Commons context |

  @S177 @p3 @v1 @automated
  Scenario: Save display density without recording reasoning
    Given the adopted RC import in the terminal workspace
    When the operator chooses "Display: Expanded" through Commands
    And the workspace is closed and reopened
    Then expanded density is retained without a revision or consultant call

  @S178 @p4 @v1 @automated
  Scenario: Expose the recorded acceptance policy in workspace Settings
    Given the adopted RC import in the terminal workspace
    When the operator changes Reasoning to Require acceptance using Settings
    Then the application records the operator's review policy without consulting
    And the already adopted argument remains in the model

  @S179 @p2 @v1 @automated
  Scenario: Begin an ordinary answer about a selected tree statement
    Given the adopted RC import in the terminal workspace
    When the operator chooses a tree statement and begins an answer about it
    Then its words enter the editable draft without a revision or consultant call
    And the draft still answers the same live question

  @S180 @p3 @v1 @automated
  Scenario: Use the offline loop without invented interpretation or outcomes
    Given a new commons with the offline guide
    When the operator supplies a goal, protections, forecast, action, observation and review
    Then the guide retains the literal contributions and their attribution
    And the original test forecast and reported result remain distinct
    And the next loop is available without a completed tree

  @S181 @p4 @v1 @automated
  Scenario: Import prior RC work once and resume without overwriting it
    Given a disposable goals home
    When Continue Reason Commons is opened and a draft is saved
    And Continue Reason Commons is opened again
    Then the same commons, revision, sources and draft are resumed

  @S182 @p4 @v1 @automated
  Scenario: Keep personal appearance settings outside reasoning history
    Given the adopted RC import in the terminal workspace
    When the operator changes light or dark using Settings
    And the workspace is closed and reopened
    Then the appearance preference is retained outside the commons
    And the personal setting creates no revision or consultant call

  @S183 @p4 @v1 @automated
  Scenario: Set a soft monthly budget locally
    Given the adopted RC import in the terminal workspace
    When the operator sets a monthly budget of five dollars using Settings
    Then the personal settings retain the budget outside the commons
    And the personal setting creates no revision or consultant call

  @S184 @p4 @v1 @automated
  Scenario: Ask for one reply with deeper reasoning and return to the chosen consultant
    Given a workspace with two offline model stand-ins
    When the operator sends an answer with deeper reasoning through Commands
    And the operator sends an ordinary answer
    Then each applied request names the model stand-in that produced it
    And the ordinary answer uses the original consultant

  @S185 @p4 @v1 @usability
  Scenario: Evaluate continuation from imported reasoning without transferring discovery back to the user
    Given the adopted RC import and participants unfamiliar with its reconstruction
    When they inspect why the interface was built and contribute a correction or development observation
    Then they distinguish original words, AI interpretation and actual adoption
    And they can continue without first choosing a test or naming the most important decision
    And human attention, AI cost and useful next actions are assessed separately from record volume

  @S186 @p4 @v1 @automated
  Scenario: Complete a guided practice tour with deliberate example submissions
    Given a disposable guided practice workspace
    When the operator fills and sends each tour example using its visible controls
    Then the tour reaches Loop complete with attributed literal example words
    And Finish tour returns to the goals home

  @S187 @p4 @v1 @automated
  Scenario: Browse the separate editorial example without consulting or contributing
    Given the packaged editorial example in a disposable reading workspace
    When the operator steps back through its history and opens its trees
    Then its attributed sources and earlier formulations remain locally inspectable
    And reading hides the response editor and creates no revision or consultant call
