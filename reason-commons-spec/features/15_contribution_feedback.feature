@J03 @J05 @J06 @J14 @J15 @J16 @J17
Feature: Make the effect of a contribution visible
  David sent a suggestion and could not tell whether it changed anything.
  The offline guide had saved and accepted his note; no tree changed and no
  adaptive AI analysis ran. We propose a lasting receipt that says what happened,
  plus markers on the trees that actually changed.

  The argument below is proposed reasoning. Its causal explanations and predicted
  benefit need evidence. The acceptance scenarios follow it and test behavior.
  Passing them does not adopt the argument or establish participant understanding.

# RC-ARGUMENT-BEGIN
# rc-argument: schema 1 | proposal contribution-feedback | status proposed
#
#   @goal @argument
#   Rule: Goal - one added condition
#     Inherited RC goal: help people advance valued goals with proportionate
#     reasoning effort. This adds a proposed necessary condition; it does not
#     replace the accepted goal.
#
#     @gt_support @supports
#     Example: Reading outcomes correctly supports the goal
#       Given we predict that participants correctly distinguish saved input, AI consultation, waiting proposals and changes to their model [DE frt_benefit]
#       And assuming correct interpretation supports continuing useful work; no measured benefit is claimed
#       Then participants can tell what their contributions did without burdensome record keeping [NC gt_condition]
#
#   @current_reality @argument
#   Rule: Current reality - why David saw no effect
#     David is unsure what sending did. Both explanations below are hypotheses;
#     the diagnosis of the offline guide is Codex's, not David's.
#
#     @crt_cues_cause @causes
#     Example: Weak cues make a saved contribution look ineffective
#       Given we suspect that a fleeting save notice and unchanged question can make a saved contribution look ineffective [cause crt_cues]
#       And assuming the person has no other clear visible outcome cue
#       Then David reports that after submitting, David could not tell whether his contribution had changed anything [UDE crt_ude]
#       But this link still needs semantic evidence
#
#     @crt_offline_cause @contributes_to
#     Example: The offline guide adds to the confusion
#       Given Codex found that the offline guide saved a literal note and supplied no adaptive analysis [cause crt_offline]
#       And assuming the person expects adaptive AI analysis and cannot identify the active consultant
#       Then David reports that after submitting, David could not tell whether his contribution had changed anything [UDE crt_ude]
#       But this link still needs semantic evidence
#
#   @conflict @argument
#   Rule: Conflict - deliberately not formed
#     Not established: no conflict has been established. The possible attention cost is a
#     negative branch of the future reality, not one side of a cloud. We do not
#     invent opposing needs just to fill in all six trees.
#
#   @future_reality @argument
#   Rule: Future reality - what we expect the change to do
#     A candidate injection, its predicted benefit and a possible attention
#     cost. Automated tests establish neither prediction.
#
#     @frt_benefit_route @produces
#     Example: A truthful receipt lets participants read outcomes correctly
#       When we show a lasting truthful contribution receipt and mark actual accepted tree changes [injection frt_injection]
#       And assuming receipts are accurate, readable and understood; participant evidence is outstanding
#       Then we predict that participants correctly distinguish saved input, AI consultation, waiting proposals and changes to their model [DE frt_benefit]
#       But this prediction still needs usability evidence
#
#     @frt_negative_branch @contributes_to
#     Example: Negative branch - the cues could cost attention or mislead
#       When we show a lasting truthful contribution receipt and mark actual accepted tree changes [injection frt_injection]
#       And assuming the cues are noisy, overly verbose or mistaken for proof of truth
#       Then we predict that receipts and markers could consume attention or falsely suggest that reasoning changed [NBR frt_risk]
#       But this prediction still needs usability evidence
#
#   @prerequisite @argument
#   Rule: Prerequisites - what must be true first
#     Required states and obstacles to accurate, usable outcome feedback.
#     These are proposed implementation conditions.
#
#     @prt_requires_outcomes @requires
#     Example: Legible outcomes need accurate outcome information
#       Given we want to make contribution outcomes legible without interrupting ongoing work [objective prt_objective]
#       And assuming the participant needs accurate outcome information
#       Then we must first ensure that durable outcomes and the actual consultant can be distinguished, including after reopening [IO prt_outcomes]
#
#     @prt_requires_markers @requires
#     Example: Legible outcomes need a local route to what changed
#       Given we want to make contribution outcomes legible without interrupting ongoing work [objective prt_objective]
#       And assuming changed locations need a local route to inspection
#       Then we must first ensure that changed tree destinations can be identified and acknowledged locally without marking unchanged trees [IO prt_markers]
#
#     @prt_obstacle_resolution @overcomes
#     Example: Distinguishable outcomes replace the generic notice
#       Given durable outcomes and the actual consultant can be distinguished, including after reopening [IO prt_outcomes]
#       And assuming the distinctions remain visible and accurate in relevant failure and acceptance states
#       Then this overcomes the obstacle that a generic Saved notice does not distinguish a literal note, waiting proposals, accepted changes or a failed reply [obstacle prt_obstacle]
#
#   @transition @argument
#   Rule: Transition - what we will build
#     Proposed implementation actions and their observable effects, followed by
#     participant evaluation. No action is marked executed in this proposed argument.
#
#     Background: Recorded, but not yet linked to any step
#       Given Codex found that published replies, membership and tree projections are available through application capabilities [reality tt_reality]
#       And we need to expose the saved contribution outcome where the participant continues working [need tt_need]
#       And we observe participants using offline, accepted, waiting and failed contribution outcomes; record interpretation errors and attention costs [action tt_evaluate]
#
#     @tt_receipt_implements @implements
#     Example: The receipt makes outcomes distinguishable
#       When we display a lasting receipt derived from the saved reply, actual consultant and current membership [action tt_receipt]
#       And assuming we use application state and never infer saving or consulting from model prose
#       Then durable outcomes and the actual consultant can be distinguished, including after reopening [IO prt_outcomes]
#
#     @tt_receipt_produces @produces
#     Example: The receipt is visible and survives reopening
#       When we display a lasting receipt derived from the saved reply, actual consultant and current membership [action tt_receipt]
#       And assuming this is an observable interface contract, not a forecast of participant comprehension
#       Then the receipt names the offline guide, a saved accepted note and unchanged trees; it survives reopening [effect tt_receipt_effect]
#
#     @tt_markers_implements @implements
#     Example: Markers make changed trees findable
#       When we mark accepted tree projection changes and clear the affected marker when that tree is opened [action tt_markers]
#       And assuming we compare accepted projections, not the presence of new pending proposals
#       Then changed tree destinations can be identified and acknowledged locally without marking unchanged trees [IO prt_markers]
#
#     @tt_markers_produces @produces
#     Example: Markers stay until the tree is inspected
#       When we mark accepted tree projection changes and clear the affected marker when that tree is opened [action tt_markers]
#       And assuming marker acknowledgement is presentation state and creates no reasoning revision
#       Then accepted tree changes are marked until inspected; pending proposals leave unchanged trees unmarked [effect tt_marker_effect]
#
#
#   @sources @argument
#   Rule: Sources - retained words and declared speakers
#
#     @user_report
#     Example: Words attributed to David
#       Given David wrote:
#         """
#         i left it automatic and entered it.  i don't think i saw anything get updated.  it needs stronger feedback to make sure it actually shows the user that their input led to some change!  a notifaction and/or a little red dot in the trees that are updated would be helpful.  or is the model not even connected
#         """
#
#     @editor
#     Example: Words attributed to Codex
#       Given Codex wrote:
#         """
#         This is a proposed development argument interpreting David's report. A read-only inspection found a guided/1 reply that saved and automatically accepted one literal note. No tree update or adaptive AI analysis occurred. The causal explanations, benefit, attention risk, prerequisites and implementation actions below are authored hypotheses and proposals, not participant observations, approvals or measured outcomes.
#         """
# RC-ARGUMENT-END


  @S188 @p4 @v1 @automated @addresses_crt_ude @implements_tt_receipt @verifies_tt_receipt_effect @verifies_prt_outcomes
  Scenario: Explain a saved offline contribution without suggesting AI analysis
    Given the adopted RC import with the offline guide and automatic acceptance
    When the operator contributes a suggestion about importing conversations
    Then a lasting receipt names the offline guide and the accepted note
    And the receipt says the trees are unchanged and how to choose AI analysis
    When the workspace is closed and reopened
    Then the same contribution receipt is reconstructed from the saved application state

  @S189 @p4 @v1 @automated @addresses_crt_ude @implements_tt_markers @verifies_tt_marker_effect @verifies_prt_markers
  Scenario: Mark accepted tree changes until the affected trees are opened
    Given a terminal commons accepting two tree proposals automatically
    When the operator contributes a suggestion about importing conversations
    Then the lasting receipt reports automatic acceptance and the affected trees
    And Trees and both affected tree destinations are marked updated
    When the operator opens one affected tree
    Then only that tree's update marker clears without a consultation or revision

  @S190 @p4 @v1 @automated @implements_tt_receipt @implements_tt_markers @verifies_prt_outcomes @verifies_tt_marker_effect
  Scenario: Distinguish waiting tree proposals from changes to the model
    Given a terminal commons holding two tree proposals for review
    When the operator contributes a suggestion about importing conversations
    Then the lasting receipt reports two proposals waiting in Backlog and unchanged trees
    And no tree destination is marked updated
    When the operator accepts the waiting proposals
    Then the receipt reflects acceptance and the affected trees are marked updated

  @S191 @p4 @v1 @usability @addresses_crt_ude @implements_tt_evaluate @verifies_frt_benefit @verifies_frt_risk
  Scenario: Evaluate whether contribution feedback supports accurate continuation
    Given participants using offline notes, automatically accepted tree changes, waiting proposals and a failed reply
    When they send a contribution and continue without moderator instructions
    Then they can identify what was saved, which consultant handled it and whether their model changed
    And they can find affected reasoning without confusing acceptance with truth
    And interpretation errors, recovery, time and attention costs are recorded separately from automated results
