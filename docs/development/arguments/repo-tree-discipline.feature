Feature: Develop Reason Commons through proposed tree updates
  David expects that opening a coding agent and adding features would bring back
  the loss of MVP discipline he saw before. We propose that every change to this
  repository is explained as a tree update first: agents propose it, the
  participant accepts or rejects it, and each commit names it.

  This is a development-method argument with no product scenarios. Its causal
  explanations and predicted benefit need evidence; the pytest checks of the
  trailer and hook test behavior, not whether the discipline helps.

# RC-ARGUMENT-BEGIN
# rc-argument: schema 1 | proposal repo-tree-discipline | status proposed
#
#   @goal @argument
#   Rule: Goal - one added condition
#     Inherited RC goal: help people and groups advance goals they value through
#     useful TOC reasoning, including RC's own development. This adds a proposed
#     necessary condition; it does not replace the accepted goal.
#
#     @gt_support @supports
#     Example: Explicable changes support developing RC with RC
#       Given we predict that changes stay explicable in the development trees and unargued features are questioned before they are built [DE frt_benefit]
#       And assuming RC's development is one of the goals RC serves; no measured benefit is claimed
#       Then every change to the repository can be explained as an update to the development trees [NC gt_condition]
#
#   @current_reality @argument
#   Rule: Current reality - why discipline would erode
#     David forecasts the problem from experience. Both explanations are
#     hypotheses; the finding about the repository is Claude's, not David's.
#
#     @crt_optional_cause @contributes_to
#     Example: The convention is optional and unchecked
#       Given Claude found that the argument convention applies only when a proposal is authored or substantially revisited, and nothing checks that a change has one [cause crt_optional]
#       And assuming agents do what the entry instructions require rather than what they merely permit
#       Then David reports that opening a coding agent and adding features would recreate his earlier problems with MVP discipline [UDE crt_ude]
#       But this link still needs semantic evidence
#
#     @crt_agent_cause @causes
#     Example: Agents complete requests by default
#       Given we suspect that coding agents complete the requested change by default instead of asking whether it serves a recorded goal [cause crt_agent_default]
#       And assuming nothing in the session asks for the tree reason before the work starts
#       Then David reports that opening a coding agent and adding features would recreate his earlier problems with MVP discipline [UDE crt_ude]
#       But this link still needs semantic evidence
#
#   @conflict @argument
#   Rule: Conflict - deliberately not formed
#     Not established: doing what the participant asks and keeping scope
#     disciplined can look opposed. We do not form a cloud. The participant keeps
#     the decision, the agent recommends, and an override is recorded in the trees
#     rather than refused or hidden.
#
#   @future_reality @argument
#   Rule: Future reality - what we expect the change to do
#     A candidate injection, its predicted benefit and a possible cost.
#     Automated checks establish neither prediction.
#
#     @frt_benefit_route @produces
#     Example: Proposals before code keep changes explicable
#       When we have agents propose a tree update before building and require each guarded commit to name its tree update or an upkeep reason [injection frt_injection]
#       And assuming participants read the proposals and the arguments are not perfunctory
#       Then we predict that changes stay explicable in the development trees and unargued features are questioned before they are built [DE frt_benefit]
#       But this prediction still needs usability evidence
#
#     @frt_negative_branch @contributes_to
#     Example: Negative branch - ceremony instead of reasoning
#       When we have agents propose a tree update before building and require each guarded commit to name its tree update or an upkeep reason [injection frt_injection]
#       And assuming the protocol is applied to small fixes or satisfied by formulaic arguments
#       Then we predict that the protocol could slow useful small changes or produce ceremonial arguments nobody reads [NBR frt_risk]
#       But this prediction still needs usability evidence
#
#   @prerequisite @argument
#   Rule: Prerequisites - what must be true first
#     Proposed implementation conditions for a discipline agents actually follow.
#
#     @prt_requires_protocol @requires
#     Example: Agents need one protocol to follow
#       Given we want to make every change to this repository explicable as a tree update without burdensome record keeping [objective prt_objective]
#       And assuming agents read the repository's entry instructions at the start of a session
#       Then we must first ensure that agents read one protocol saying when to propose, when to recommend against and how the participant decides [IO prt_protocol]
#
#     @prt_requires_check @requires
#     Example: Discipline needs a check that cannot be skipped silently
#       Given we want to make every change to this repository explicable as a tree update without burdensome record keeping [objective prt_objective]
#       And assuming an unchecked instruction can be skipped without anyone noticing
#       Then we must first ensure that a mechanical check distinguishes a commit linked to an argument from an unlinked one [IO prt_check]
#
#     @prt_obstacle_resolution @overcomes
#     Example: A check makes skipping visible
#       Given we must first ensure that a mechanical check distinguishes a commit linked to an argument from an unlinked one [IO prt_check]
#       And assuming the hook is enabled or the branch check runs before review
#       Then this overcomes the obstacle that agent instructions alone are advisory and can be skipped silently [obstacle prt_obstacle]
#
#   @transition @argument
#   Rule: Transition - what we will build
#     Proposed actions and their observable effects, then an evaluation in use.
#     No action is marked executed in this proposed argument.
#
#     Background: Recorded, but not yet linked to any step
#       Given Claude found that a readable argument notation and its validator exist, but only one feature uses them [reality tt_reality]
#       And we need to make the tree reason the first thing an agent produces for a new request [need tt_need]
#       And we observe the next agent-assisted changes and record whether proposals were useful, skipped or ceremonial [action tt_evaluate]
#
#     @tt_protocol_implements @implements
#     Example: The protocol tells agents what to do first
#       When we write the tree-update protocol into AGENTS.md and docs/development/tree-updates.md [action tt_protocol]
#       And assuming Claude Code and Codex both load AGENTS.md
#       Then we must first ensure that agents read one protocol saying when to propose, when to recommend against and how the participant decides [IO prt_protocol]
#
#     @tt_protocol_produces @produces
#     Example: A feature request is first answered with a proposal
#       When we write the tree-update protocol into AGENTS.md and docs/development/tree-updates.md [action tt_protocol]
#       And assuming this is an instruction, not a guarantee of agent behavior
#       Then an agent's first reply to a new feature request is a proposed tree update or a stated recommendation against it [effect tt_protocol_effect]
#
#     @tt_check_implements @implements
#     Example: The trailer links each commit to its argument
#       When we add a Tree-update commit trailer, a commit-msg hook and a branch check [action tt_check]
#       And assuming the trailer links a commit to an argument and does not judge the argument
#       Then we must first ensure that a mechanical check distinguishes a commit linked to an argument from an unlinked one [IO prt_check]
#
#     @tt_check_produces @produces
#     Example: An unlinked guarded commit is rejected
#       When we add a Tree-update commit trailer, a commit-msg hook and a branch check [action tt_check]
#       And assuming the hook is enabled with core.hooksPath
#       Then a guarded commit without a resolvable proposal or an upkeep reason is rejected [effect tt_check_effect]
#
#   @sources @argument
#   Rule: Sources - retained words and declared speakers
#
#     @user_report
#     Example: Words attributed to David
#       Given David wrote:
#         """
#         recently work was done to improve this repo's ability to practice what it preaches.
#
#
#         there is still work to be done in this regard.  in a word, it is making sure that any changes to this repo (e.g. i open codex and start adding features - which would recreate some of the problems that i'd had before around mvp discipline) actually use the reason commons process, i.e. they are recorded in terms of tree updates in a disciplined way.  how can we achieve this?   can we update files that agents look into and make this explicit?  can we make agents refuse or recommend against work that is not explicable in terms of the trees?  and make the coding agent respond with the proposed tree updates so the user can accept them or reject them?
#         """
#
#     @editor
#     Example: Words attributed to Claude
#       Given Claude wrote:
#         """
#         This is a proposed development argument interpreting David's request of 11 October 2026. A read of the repository found the readable argument notation, its validator and one argument (contribution feedback), and no instruction or check requiring an argument for other changes. The causal explanations, predicted benefit, negative branch, prerequisites and actions below are authored hypotheses and proposals, not observations, approvals or measured outcomes.
#         """
# RC-ARGUMENT-END
