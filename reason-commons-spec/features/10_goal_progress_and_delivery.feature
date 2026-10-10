@J01 @J02 @J03 @J06 @J07 @J09 @J11 @J12 @J13 @J14 @J15 @J16
Feature: Connect reasoning to goal progress within the delivered scope
  The selected delivery profile limits controls, fixtures, and adapter updates.
  Later models remain specified without becoming requirements for v1.

  @S91 @p5 @later @automated
  Scenario: Preserve every delivered reasoning type in a portable handoff
    Given a full-tools commons with traceability, reviews, stances, and all six models
    When the operator exports and imports the commons offline
    Then exact versions and every typed relationship remain inspectable
    And review needs, open questions, observation criteria, and cursor are retained
    And no provider conversation is required

  @S92 @p3 @later @automated
  Scenario: Keep structured causal navigation useful offline
    Given a causal-profile commons and an unavailable consultant
    When the operator opens the model, WIP, assumptions, or stored comparison
    Then each supported view is reconstructed from stored records
    And no inference or discriminating prediction is invented
    And no consultant call or reasoning revision is created

  @S93 @p2 @v1 @automated
  Scenario: Show the decision and goal served by the live question
    Given a stored intervention with purpose, decision, and goal version G1 version 1
    When the current question is rendered
    Then the decision purpose is readable beside its one primary prompt
    And the rationale links the task to that exact goal formulation
    And a provisional goal remains labeled provisional

  @S94 @p2 @v1 @automated
  Scenario: Leave a question open and return without reconstructing it
    Given a live question and an answer draft
    When the operator opens history and returns with Esc
    Then the open question, response target, and exact draft are restored
    And inspection creates no reasoning revision or consultant call

  @S95 @p2 @v1 @automated
  Scenario: Revisit test relevance when its referenced goal changes
    Given test P1 version 1 explicitly serves goal G1 version 1
    When goal G1 receives a substantively different version 2
    Then P1 retains its original prediction and goal reference
    And its relevance to the current goal is marked review needed
    And the next test decision shows that review need
    And neither the old result nor the participants' positions are rewritten

  @S96 @p3 @later @automated
  Scenario: Inspect a typed goal connection without inventing a mechanism
    Given a reported unwanted effect linked to a goal criterion by "violates"
    And its proposed causal explanation remains incomplete
    When the stored goal-connection view is opened
    Then "violates" is presented as traceability rather than a causal arrow
    And missing connections and unresolved effects are named
    And a new connection requiring judgment is a labeled consultant option
    And browsing makes no consultant call

  @S97 @p5 @later @automated
  Scenario: Trace a change through distinct reasoning and implementation roles
    Given stored links from a goal through a CRT, Cloud, FRT, PRT, and action
    When the goal-connection view is opened
    Then each link names its causal, necessity, conflict, or traceability meaning
    And operating, conflict, and implementation objectives remain distinguishable
    And a present observation and future prediction remain separate records
    And unresolved unwanted effects and safeguards remain visible

  @S98 @p3 @later @automated
  Scenario: A revised premise requests review of its known dependent reasoning
    Given L2's reviewed formulation references premise N1 version 1
    When N1 receives a substantively revised version 2
    Then the change view shows old wording, new wording, source, and reason
    And L2 retains its original wording with a review-needed record
    And prior support is shown as applying to the older premise
    And support or rejection does not propagate automatically
    And unrelated semantic consequences are not claimed to be discovered

  @S99 @p4 @later @automated
  Scenario: Resolve a review without transferring another participant's belief
    Given a revised relationship and Priya's stance on its earlier formulation
    When Sam explicitly records a bounded decision under the remaining uncertainty
    Then Sam's decision cites the current formulation and unresolved review
    And Priya's earlier stance stays attached to its original version
    And Priya's current belief is unknown until she supplies it

  @S100 @p5 @later @semantic
  Scenario: A same-setup counterexample changes the questions across tools
    Given a CRT explanation that every sequence insertion adds setup time
    And the Cloud, FRT, and PRT contain explicitly linked dependent proposals
    When a participant supplies a credible same-setup counterexample
    Then the proposed revision qualifies the relevant CRT relationship
    And the Cloud's unchanged-sequence assumption is requested for review
    And the admission rule and setup-information requirement are requested for review
    And the late-order observation is not erased
    And no operational improvement is inferred from the model correction

  @S101 @p2 @v1 @automated
  Scenario: Complete an action without claiming its expected effect occurred
    Given a test action with an expected intermediate state and observation criterion
    When the operator explicitly records that the action was completed
    Then execution is completed and expected-effect attainment remains unknown
    And the receipt says "Action completed; result awaiting observation"
    And neither the prediction nor the system goal is marked achieved

  @S102 @p2 @v1 @semantic
  Scenario: Turn a recommendation into an immediate action with an observation
    Given a proposed bounded change and unknown decision authority
    When the operator asks what to do next
    Then the recommendation identifies starting conditions, need, action, and expected effect
    And owner, authority, timing, observation criterion, and contingency are explicit or unknown
    And it asks for the most consequential missing item
    And a drawn or saved action does not create a real-world assignment

  @S103 @p5 @later @automated
  Scenario: Keep attained prerequisites distinct from executable readiness
    Given two independent intermediate objectives with attainment criteria
    And both are necessary before a supervised pilot
    When both states have cited observations satisfying their criteria
    Then the pilot is labeled "prerequisites met"
    And the objectives remain parallel rather than ordered by entry time
    And missing resources, authority, or sufficient action steps remain unknown
    And the pilot is not labeled ready solely from its dependency graph

  @S104 @p2 @v1 @semantic
  Scenario: Distinguish a supported pilot target from achievement of the goal
    Given the goal is 90 percent on-time delivery
    And a bounded pilot prospectively predicts 80 percent
    When comparable results show 40 of 50 orders on time
    Then the pilot target is supported and the 90 percent goal remains unmet
    And the review shows protected conditions and implementation fidelity separately
    And a next decision addresses remaining goal progress and relevant uncertainty

  @S105 @p2 @v1 @semantic
  Scenario: Check whether the measured safeguard covers the protected need
    Given urgent responsiveness matters and only acknowledgement is measured
    When the operator asks whether timely acknowledgements establish fulfillment
    Then acknowledgement and fulfillment are distinguished
    And a fulfillment measure, acceptable bound, method, and authority are requested as needed
    And missing values remain unknown rather than receiving invented defaults
    And no breach is hidden by delivery success

  @S106 @p5 @later @automated
  Scenario: Share a requirement without confusing necessity with attainment
    Given a necessary condition supports two critical success factors
    When the goal overview and focused requirement are opened
    Then both appearances reference the same versioned condition
    And the critical success factors and supporting requirements are distinguished
    And current attainment is separate from its necessity warrant
    And meeting the requirement does not establish sufficiency for the goal

  @S107 @p1 @v1 @automated
  Scenario Outline: Refuse a restored out-of-profile action locally
    Given the v1 delivery profile and a retained response draft
    And a stale cursor or action reference requests "<action>"
    When the workspace revalidates that action reference
    Then a local notice says the action belongs to a later delivery profile
    And Help, navigation and Actions omit it as an available operation
    And no consultant call, revision or draft loss occurs

    Examples:
      | action              |
      | Explore causal model|
      | Record position     |
      | Record test reliance|
      | Restore reasoning   |

  @S108 @p0 @v1 @automated
  Scenario: Reject an adapter update outside the delivered schema
    Given the v1 schema allows only goal, note, intervention, test, action, observation, bounded review, and typed tree claim, link and retraction records, and the operator's decisions about them
    When an adapter proposal includes an untyped relationship graph or structured stance update
    Then the entire proposal is rejected before commit
    And the raw input and failure receipt remain available
    And later fields are not silently stored or partially applied

  @S109 @p5 @later @usability
  Scenario: Change medium when narrow output cannot support the comparison
    Given a decision requires simultaneous review of interacting future branches
    When ordered 40-column records do not let a participant make the comparison
    Then a wider read-only export or another medium is offered
    And decisive qualifications are not shortened away
    And the failed narrow comparison and rescue are recorded in evaluation

  @S110 @p1 @v1 @automated
  Scenario: Do not advertise an out-of-profile option from an adapter
    Given a v1 semantic response contains an option opening a Cloud view
    When the response is validated
    Then the proposal is rejected with a local unsupported-action receipt
    And the input, live response target, and prior revision remain intact
    And no menu exposes the unavailable option

  @S111 @p2 @v1 @usability
  Scenario: Evaluate the complete goal action review loop without a tree lesson
    Given first-time participants and a v1 fixture with a fake consultant
    When they define success, inspect the purpose, record a test, resume, and review results
    Then they identify the next action, authority, observation, and stopping condition
    And they distinguish action execution, intermediate effect, pilot result, and goal attainment
    And completion, reference repairs, missed conditions, and reasoning are reported individually
    And no TOC vocabulary lesson or complete tree is required

  @S112 @p5 @later @usability
  Scenario: Evaluate design hypotheses without confusing navigation with improvement
    Given predeclared rubrics and distinct comparable cases
    When joint-premise, goal-connection, and revision-review displays are compared
    Then prompts and evidence access are held comparable for each design claim
    And order, experience, rescue views, and consequential failures are recorded
    And defensible alternative answers are accepted
    And access, reasoning, learning, implementation, and goal results are reported separately

  @S113 @p1 @v1 @automated
  Scenario: Cancel an options menu and retain the question and draft
    Given a displayed options menu and an answer draft
    When the operator activates Cancel or presses Esc
    Then the prior view, open question, and exact draft are restored
    And no revision or consultant call is created
