@J03 @J07 @J10 @J11 @J12 @J13 @J16
Feature: Support the next reasoning operation across every Thinking Process
  Readability and visual fluency do not establish truth or understanding.

  @S74 @p3 @later @semantic
  Scenario: Preserve premises while leaving the inference to participants
    Given two agreed premises and an unarticulated mechanism
    When the consultant composes a question with visible premises to reason from
    Then the needed premises are visible and the mechanism is asked for
    And the renderer does not invent an arrow to fill the gap
    And the workspace identifies the decision the reasoning serves

  @S75 @p5 @later @automated
  Scenario: Expand scope when the current question needs interacting branches
    Given a proposed change may improve delivery and harm responsiveness
    When the current question is whether to run the pilot
    Then both relevant paths and decisive conditions are available together
    And a node-count heuristic does not remove a protection or alternative
    And a narrow terminal uses an aligned comparison or ordered text

  @S76 @p3 @later @automated
  Scenario: Distinguish attention from support and node evidence from link evidence
    Given two measured propositions joined by a hypothetical causal relation
    When that relation is focused in the model
    Then selection indicates only attention
    And the relation remains explicitly hypothetical despite measured endpoints
    And its evidence and dissent are independently inspectable

  @S77 @p3 @later @automated
  Scenario: Preserve location and uncertainty when collapsing a partial model
    Given a branch has a decisive AND condition and participant dissent
    When the renderer produces a partial view
    Then the view labels its boundary and local expansion route
    And the decisive condition and dissent remain visible if needed for the question
    And a summary retains references to the original claims
    And expanding stored branches makes no consultant call

  @S78 @p5 @later @automated
  Scenario: Test necessity without implying sufficiency in a goal map
    Given the goal requires a dependable plan and available materials
    When the question examines the plan requirement
    Then the relation says "requires" rather than using a causal connector
    And it asks whether the goal can occur without this condition in the stated scope
    And the view states that this requirement alone does not establish the goal

  @S79 @p3 @later @semantic
  Scenario: Inspect a CRT conjunction with a meaningful counterexample
    Given priority changes and high unfinished work jointly predict interruptions
    And the lateness link requires inability to recover before promised dates
    When the participant challenges the interruption-to-lateness claim
    Then the recovery condition appears beside that relation
    And a test considers whether all stated conditions hold
    And removing one route does not imply all lateness disappears

  @S80 @p3 @later @automated
  Scenario: Separate feedback episodes from circular justification
    Given earlier lateness may trigger later requests and further interruptions
    When the feedback view is shown
    Then successive episodes or relevant delays are labeled
    And layout does not imply known duration, strength, or proof
    And a static tree is not presented as a quantitative simulation

  @S81 @p4 @later @semantic
  Scenario: Preserve legitimate needs while questioning Cloud assumptions
    Given Sam reports Sales and Production needs and incompatible actions
    When a Cloud asks whether responsiveness requires immediate plan change
    Then the shared objective and both needs remain accessible with equal visual treatment
    And the arrow says "requires?" with scope and time of incompatibility
    And reported positions are not upgraded to direct endorsement
    And questioning necessity does not mean rejecting the need

  @S82 @p5 @later @semantic
  Scenario: Treat FRT branches as conditional prospective predictions
    Given a proposal freezes commitments and reserves urgent slots
    When the future view predicts fewer interruptions and better delivery
    Then predicted effects are distinguished from reported starting conditions
    And available material and recovery capacity remain visible where decisive
    And a new-case prediction includes alternatives and measurement scope
    And no original forecast is rewritten when results arrive

  @S83 @p5 @later @semantic
  Scenario: Test a negative branch and the adequacy of its safeguard
    Given urgent capacity may be insufficient for actual urgent needs
    When the proposed safeguard measures acknowledgement within 24 hours
    Then the view distinguishes acknowledgement from fulfilment of the need
    And it names the triggering condition, threatened protection, and stop owner if known
    And the prevention remains a proposal until its effect is evidenced

  @S84 @p5 @later @semantic
  Scenario: Convert a PRT obstacle into a state before naming the action
    Given no one owns urgent-request triage and this blocks the pilot
    When a prerequisite view is composed
    Then the obstacle and necessary state are shown distinctly
    And "Every urgent request has an accountable triage owner" is not itself marked executable
    And owner, authority, and timing remain unknown until explicitly supplied
    And independent prerequisites are not forced into a serial chain

  @S85 @p5 @later @semantic
  Scenario: Explain a Transition Tree action through condition and expected effect
    Given an urgent request has arrived and a daily triage owner is assigned
    When the action is to acknowledge receipt and state when a final answer will arrive
    Then the starting conditions, action, and expected effect are visible
    And supplier uncertainty need not imply inability to acknowledge receipt
    And completed action fidelity is recorded separately from timely acknowledgement
    And the step identifies a contingency if the expected effect does not occur

  @S86 @p3 @later @automated
  Scenario: Compare rival accounts without making geometry an evidence score
    Given scheduling and supplier accounts can both lead to lateness
    When the stored comparison view is opened
    Then both use aligned outcome wording, scope, and readable labels
    And actual evidence differences are explicit beside each account
    And prospective discriminating observations are inspectable
    And equal layout implies neither equal support nor mutual exclusivity

  @S87 @p5 @later @automated
  Scenario Outline: Preserve each representation's logic in accessible text
    Given a stored "<representation>" view with consequential uncertainty
    When Sam selects its text equivalent on a 40-column terminal
    Then the output preserves "<relation>" plus scope, conditions, and dissent
    And the same exact formulations remain accessible through details
    And reading and paging make no consultant call

    Examples:
      | representation | relation                                    |
      | goal map       | necessity without individual sufficiency    |
      | CRT            | joint causes and recovery condition         |
      | Cloud          | needs, actions, and necessity assumptions   |
      | FRT            | intervention and predicted consequences     |
      | negative branch| trigger, harm, prevention, and stop rule     |
      | PRT            | obstacle and required intermediate state    |
      | Transition Tree| condition, action, and expected effect      |

  @S88 @p5 @later @usability
  Scenario: Measure understanding separately from recognition and agreement
    Given a participant fluently repeats a displayed model
    When its learning effect is evaluated
    Then a task asks for a mechanism, condition, rival prediction, or changed-case action
    And aided performance is distinguished from unaided or delayed transfer
    And a defensible correction can score higher than repeating the consultant
    And confidence, satisfaction, implementation, and goal outcomes are recorded separately

  @S89 @p3 @later @semantic
  Scenario: Change support or stop when more drawing would not help the decision
    Given repeated premise recovery suggests a possible reference problem
    When the consultant shows the needed fragment and checks the next operation
    Then the benefit is assessed from the participant's actual reasoning
    And hesitation alone is not recorded as overload
    And a failed repair can lead to explaining, seeking facts, pausing, or addressing a concern
    And unresolved detail is retained when it would not change the next decision
