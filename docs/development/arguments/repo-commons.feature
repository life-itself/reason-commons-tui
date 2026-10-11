Feature: Keep a commons in the git repository its people share
  The old reason-commons skill kept its YAML in the reasoncommons repository, so
  David's and Rufus's updates travelled by commit and pull. Reason Commons keeps
  goals in each person's home folder, which git does not track. We propose keeping a
  commons in the repository, under commons/, with the repository's Claude Code
  settings pointing the skill there, and moving the Reason Commons development goal
  into the reasoncommons repository so Rufus can judge whether it replaces the old
  method.

  This argument has no product scenarios. An adapter test covers opening a commons
  without its cursor file; whether sharing through git works for David and Rufus
  needs their use.

# RC-ARGUMENT-BEGIN
# rc-argument: schema 1 | proposal repo-commons | status proposed
#
#   @goal @argument
#   Rule: Goal - an existing condition this serves
#     Inherited RC goal: help people and groups advance goals they value through
#     useful TOC reasoning. This serves a necessary condition already in the
#     development commons; it adds none and replaces nothing.
#
#     @gt_support @supports
#     Example: Sharing through the repository keeps the interface usable together
#       Given we predict that David and Rufus share one commons through commit, push and pull, in the workspace or the skill, so Rufus can confirm it replaces the old method [DE frt_benefit]
#       And assuming people who already share a repository find sharing through it easier than any separate channel
#       Then keep the interface minimal enough to understand and use during important work [NC gt_minimal]
#
#   @current_reality @argument
#   Rule: Current reality - why the work is not shared
#     David reports the problem; the finding about where goals are kept is Claude's.
#
#     @crt_home_cause @causes
#     Example: Goals are kept in the home folder
#       Given Claude found that the workspace and the plugin keep goals in ~/ReasonCommons unless REASON_COMMONS_HOME says otherwise, and nothing documented keeping a commons in a repository [cause crt_home]
#       And assuming nobody sets REASON_COMMONS_HOME to a folder inside a repository
#       Then David reports that the new work is saved in each person's home folder, untracked by git, whereas the old skill's YAML lived in the shared repository and travelled by commit and pull [UDE crt_ude]
#
#   @conflict @argument
#   Rule: Conflict - deliberately not formed
#     Not established: taking turns on a goal is a cost of sharing through git, not
#     one side of a cloud. Merging concurrent work is outside the storage design.
#
#   @future_reality @argument
#   Rule: Future reality - what we expect the change to do
#     A candidate injection, its predicted benefit and three possible costs.
#
#     @frt_benefit_route @produces
#     Example: A commons in the repository travels with it
#       When we keep a commons in a git repository under commons/, with the repository's committed Claude Code settings pointing the skill there [injection frt_injection]
#       And assuming David and Rufus pull before working on a goal and push when they stop
#       Then we predict that David and Rufus share one commons through commit, push and pull, in the workspace or the skill, so Rufus can confirm it replaces the old method [DE frt_benefit]
#       But this prediction still needs usability evidence
#
#     @frt_turns_route @contributes_to
#     Example: Negative branch - concurrent additions conflict
#       When we keep a commons in a git repository under commons/, with the repository's committed Claude Code settings pointing the skill there [injection frt_injection]
#       And assuming two people add to the same goal between pulls
#       Then we predict that both write the same next revision and git cannot merge them, so the second to push must give way [NBR frt_turns]
#
#     @frt_public_route @contributes_to
#     Example: Negative branch - a public repository publishes the commons
#       When we keep a commons in a git repository under commons/, with the repository's committed Claude Code settings pointing the skill there [injection frt_injection]
#       And assuming the repository is public, as reasoncommons is
#       Then we predict that participants' words, sources and consultant receipts are published with it [NBR frt_public]
#
#     @frt_forget_route @contributes_to
#     Example: Negative branch - the workspace needs the setting each time
#       When we keep a commons in a git repository under commons/, with the repository's committed Claude Code settings pointing the skill there [injection frt_injection]
#       And assuming the workspace reads REASON_COMMONS_HOME from the shell, not from the repository
#       Then we predict that someone who starts the workspace without the setting sees their home goals instead of the repository's [NBR frt_forget]
#       But this prediction still needs usability evidence
#
#   @prerequisite @argument
#   Rule: Prerequisites - what must be true first
#     Conditions for a commons that people clone, pull and push.
#
#     @prt_requires_private @requires
#     Example: Locks and drafts must not travel
#       Given we want to keep a commons in a repository that people clone, pull and push [objective prt_objective]
#       And assuming a lock or a draft committed by one person would block or confuse another
#       Then we must first ensure that the writer lock and each person's cursor stay out of git, and a clone without them still opens [IO prt_private]
#
#     @prt_requires_settings @requires
#     Example: The skill must find the repository's goals
#       Given we want to keep a commons in a repository that people clone, pull and push [objective prt_objective]
#       And assuming the plugin's server otherwise uses the home folder
#       Then we must first ensure that the repository's committed settings reach the plugin's server [IO prt_settings]
#
#     @prt_requires_untouched @requires
#     Example: Work in progress must stay as it is
#       Given we want to keep a commons in a repository that people clone, pull and push [objective prt_objective]
#       And assuming David's checkout of reasoncommons holds uncommitted changes
#       Then we must first ensure that the changes to reasoncommons leave David's uncommitted work untouched [IO prt_untouched]
#
#     @prt_cursor_resolution @overcomes
#     Example: A missing cursor no longer stops a clone
#       Given we must first ensure that the writer lock and each person's cursor stay out of git, and a clone without them still opens [IO prt_private]
#       And assuming a missing cursor is read as a new commons's empty one
#       Then this overcomes the obstacle that a commons would not open without its cursor file [obstacle prt_cursor]
#
#   @transition @argument
#   Rule: Transition - what we will build
#     Proposed actions and their observable effects, then an evaluation in use.
#     No action is marked executed in this proposed argument.
#
#     Background: Recorded, but not yet linked to any step
#       Given Claude found that a committed .claude/settings.json setting REASON_COMMONS_HOME to commons made the plugin create goals in the repository's commons folder [reality tt_reality]
#       And we need to give the repository one Reason Commons goal that David and Rufus both open [need tt_need]
#       And we observe Rufus installing from the reasoncommons README and working on the goal, and record whether he judges it to replace the old skill [action tt_evaluate]
#
#     @tt_cursor_implements @implements
#     Example: A commons opens without its cursor
#       When we read a missing cursor file as an empty cursor, export it as one, and ignore writer.lock and cursor.yaml in git [action tt_cursor]
#       And assuming the workspace already starts a new commons from an empty cursor
#       Then we must first ensure that the writer lock and each person's cursor stay out of git, and a clone without them still opens [IO prt_private]
#
#     @tt_repo_implements @implements
#     Example: The repository points the skill at its commons
#       When we copy the Reason Commons development goal to commons/reason-commons in reasoncommons, with its .gitignore entries, its .claude/settings.json and a README section [action tt_repo]
#       And assuming Claude Code applies a repository's project settings to the servers it starts
#       Then we must first ensure that the repository's committed settings reach the plugin's server [IO prt_settings]
#
#     @tt_worktree_implements @implements
#     Example: A separate worktree keeps David's changes as they are
#       When we make the reasoncommons changes on a branch in a separate worktree from origin/main [action tt_worktree]
#       And assuming a worktree shares history but not working files
#       Then we must first ensure that the changes to reasoncommons leave David's uncommitted work untouched [IO prt_untouched]
#
#     @tt_repo_produces @produces
#     Example: A clone opens the goal and a commit travels
#       When we copy the Reason Commons development goal to commons/reason-commons in reasoncommons, with its .gitignore entries, its .claude/settings.json and a README section [action tt_repo]
#       And assuming this is checked with throwaway clones on the developer's machine, not by Rufus
#       Then a clone opens the goal in the workspace and the skill, and a revision committed in one clone appears in another after a pull [effect tt_repo_effect]
#
#   @sources @argument
#   Rule: Sources - retained words and declared speakers
#
#     @user_report
#     Example: Words attributed to David
#       Given David wrote:
#         """
#         suppose i want to share this with rufus.  until now, he's been working using the skill at ~/github/reasoncommons/ltp-project, which references a yaml file.  the skill we've just developed has been developed in order to replace that skill.   but that yaml file was included in ~/github/reasoncommons so when he or i made updates to the file they would be reflected when those updates were committed to the repo and pulled.
#
#         now, updates (the yaml files, immutable i believe) are added to the user's home directory.  so they're not tracked by git, right?
#
#         here's what i'd like to do:
#
#         updates should actually be scoped for a git repo.  a commons should be coupled to a git repo.  the reason commons work we've been dogfooding in this tui should be coupled to the ~/github/reasoncommons repo - but as i said, it is currently using the obsoleted skill.
#
#         i would like to phase this out-  but first i need to make the work tracked by github in the reasoncommons repo, and second, add instructions for installing this repos (~/github/reason-commons-tui - and using it either as a skill or tui) in the readme of that repo. and third, easily sharing this update with rufus so he can confirm that our new work adequately replaces the old methodology
#
#         1. yes i agree we should leave out the personal work.  we also need to consolidate reason-commons-development and reason-commons   - no reason to have both
#         2. yes it can be published.
#         3. there's no reason to migrate - reason commons will replace this.
#         """
#
#     @editor
#     Example: Words attributed to Claude
#       Given Claude wrote:
#         """
#         This is a proposed development argument interpreting David's request of 11 October 2026 and his answers, accepted in conversation the same day. A check found that goals default to ~/ReasonCommons, that a committed .claude/settings.json setting REASON_COMMONS_HOME steered the plugin's server to a repository's commons folder, that a commons would not open without cursor.yaml, that the older reason-commons goal is a superseded reconstruction whose conversation sources the development goal already holds, and that the conversation and ledger are already public in reason-commons-tui. Trailing spaces in David's words were not kept. The causes, predicted benefit, negative branches, prerequisites and actions below are authored hypotheses and proposals, not observations or measured outcomes.
#         """
# RC-ARGUMENT-END
