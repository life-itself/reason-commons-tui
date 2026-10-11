Feature: Install the skill and its server as one Claude Code plugin
  David wants to start sharing the skill with others, and asks whether it is
  packaged so that others can install it easily. We propose publishing a Claude
  Code plugin from this repository that bundles the skill with the MCP server and
  the host consultant, so a newcomer installs both with two commands.

  Packaging adds no application behavior, so this argument has no product
  scenarios. Its pytest checks cover the manifests and the skill link; whether
  newcomers actually find the install easy needs usability evidence.

# RC-ARGUMENT-BEGIN
# rc-argument: schema 1 | proposal skill-plugin | status proposed
#
#   @goal @argument
#   Rule: Goal - an existing condition this serves
#     Inherited RC goal: help people and groups advance goals they value through
#     useful TOC reasoning. This serves a necessary condition already in the
#     development commons; it adds none and replaces nothing.
#
#     @gt_support @supports
#     Example: An easy install keeps the skill usable for others
#       Given we predict that others install the skill and its server with two commands and no clone [DE frt_benefit]
#       And assuming a hard install stops people before they reach the interface; no adoption measure is claimed
#       Then keep the interface minimal enough to understand and use during important work [NC gt_minimal]
#
#   @current_reality @argument
#   Rule: Current reality - why installing the skill is hard
#     David asks the question; the finding about the install steps is Claude's.
#     That the steps deter others is a hypothesis.
#
#     @crt_steps_cause @causes
#     Example: Three manual steps, one of them a clone
#       Given Claude found that installing the skill takes a uv install with the MCP extra, registering the server by its full path, and a clone plus a symlink into the Claude skills folder, because the packaged skill sits deep inside uv's folders [cause crt_steps]
#       And assuming the people David shares it with are not developers of this repository
#       Then David reports that he is unsure the skill is packaged so that others can install it easily, as he starts sharing it [UDE crt_ude]
#       But this link still needs usability evidence
#
#   @conflict @argument
#   Rule: Conflict - deliberately not formed
#     Not established: no conflict has been reported. Following the main branch
#     instead of tagged releases is a negative branch below, not a cloud.
#
#   @future_reality @argument
#   Rule: Future reality - what we expect the change to do
#     A candidate injection, its predicted benefit and four possible costs.
#
#     @frt_benefit_route @produces
#     Example: A plugin installs the skill and the server together
#       When we publish a Claude Code plugin from this repository that bundles the skill with the MCP server and the host consultant [injection frt_injection]
#       And assuming the newcomer has uv and Claude Code installed
#       Then we predict that others install the skill and its server with two commands and no clone [DE frt_benefit]
#       But this prediction still needs usability evidence
#
#     @frt_first_start_route @contributes_to
#     Example: Negative branch - the first start builds the package
#       When we publish a Claude Code plugin from this repository that bundles the skill with the MCP server and the host consultant [injection frt_injection]
#       And assuming the server is built from GitHub the first time it starts, which took 19 seconds when measured
#       Then we predict that the first start may outlast Claude Code's wait for a server and show it as failed until it is retried [NBR frt_first_start]
#
#     @frt_unpinned_route @contributes_to
#     Example: Negative branch - an unpinned source follows the main branch
#       When we publish a Claude Code plugin from this repository that bundles the skill with the MCP server and the host consultant [injection frt_injection]
#       And assuming there are no tagged releases to pin
#       Then we predict that users get changes to the main branch unannounced, or stay on an older cached build [NBR frt_unpinned]
#
#     @frt_names_route @contributes_to
#     Example: Negative branch - the plugin renames the skill and its tools
#       When we publish a Claude Code plugin from this repository that bundles the skill with the MCP server and the host consultant [injection frt_injection]
#       And assuming Claude Code prefixes a plugin's skills and tools with the plugin's name
#       Then we predict that instructions naming the skill or its tools without the prefix no longer match what users see [NBR frt_names]
#
#     @frt_codex_route @contributes_to
#     Example: Negative branch - Codex users gain nothing
#       When we publish a Claude Code plugin from this repository that bundles the skill with the MCP server and the host consultant [injection frt_injection]
#       And assuming Codex does not read Claude Code plugins
#       Then we predict that Codex users keep the manual install [NBR frt_codex]
#
#   @prerequisite @argument
#   Rule: Prerequisites - what must be true first
#     Conditions for the plugin's server to start on a newcomer's machine.
#
#     @prt_requires_uv @requires
#     Example: The server's command must be found
#       Given we want to let a newcomer install the skill and its server without cloning the repository [objective prt_objective]
#       And assuming a server launched by a desktop app may not inherit the shell's PATH
#       Then we must first ensure that the plugin finds uv where it is usually installed, even when Claude Code's PATH lacks it [IO prt_uv]
#
#     @prt_requires_root @requires
#     Example: The commons folder must exist
#       Given we want to let a newcomer install the skill and its server without cloning the repository [objective prt_objective]
#       And assuming the server refuses a commons root that does not exist
#       Then we must first ensure that the commons folder exists before the server starts, in the same place the workspace uses [IO prt_root]
#
#     @prt_requires_one_skill @requires
#     Example: There must still be one skill source
#       Given we want to let a newcomer install the skill and its server without cloning the repository [objective prt_objective]
#       And assuming a copied skill can drift from the one the tests and agents use
#       Then we must first ensure that the plugin's skill is the packaged skill file, not a copy kept by hand [IO prt_one_skill]
#
#   @transition @argument
#   Rule: Transition - what we will build
#     Proposed actions and their observable effects, then an evaluation in use.
#     No action is marked executed in this proposed argument.
#
#     Background: Recorded, but not yet linked to any step
#       Given Claude found that uvx can start the server straight from the repository on GitHub, and that the skill names no tool by its full prefix [reality tt_reality]
#       And we need to give newcomers one install for the skill and its server [need tt_need]
#       And we observe newcomers installing from the README and record where they stop, how long the first start takes and whether the skill is found [action tt_evaluate]
#
#     @tt_plugin_implements_uv @implements
#     Example: The plugin's command looks for uv and makes the folder
#       When we add a marketplace and a plugin whose server command adds uv's usual folders to PATH, creates the commons folder and starts the server with the host consultant [action tt_plugin]
#       And assuming macOS or Linux, where the plugin's command runs in sh
#       Then we must first ensure that the plugin finds uv where it is usually installed, even when Claude Code's PATH lacks it [IO prt_uv]
#
#     @tt_plugin_implements_root @implements
#     Example: The plugin's command makes the commons folder
#       When we add a marketplace and a plugin whose server command adds uv's usual folders to PATH, creates the commons folder and starts the server with the host consultant [action tt_plugin]
#       And assuming the folder honours REASON_COMMONS_HOME as the workspace does
#       Then we must first ensure that the commons folder exists before the server starts, in the same place the workspace uses [IO prt_root]
#
#     @tt_link_implements @implements
#     Example: The plugin links the one skill
#       When we link the plugin's skill to the packaged skill file and check the link in pytest [action tt_link]
#       And assuming Claude Code copies a linked file into the installed plugin
#       Then we must first ensure that the plugin's skill is the packaged skill file, not a copy kept by hand [IO prt_one_skill]
#
#     @tt_plugin_produces @produces
#     Example: Two commands give a working skill
#       When we add a marketplace and a plugin whose server command adds uv's usual folders to PATH, creates the commons folder and starts the server with the host consultant [action tt_plugin]
#       And assuming this is checked in one session on the developer's machine, not with newcomers
#       Then a Claude Code session with only the plugin installed creates a goal and saves a host consultant's proposal, with no key [effect tt_plugin_effect]
#
#   @sources @argument
#   Rule: Sources - retained words and declared speakers
#
#     @user_report
#     Example: Words attributed to David
#       Given David wrote:
#         """
#         perfect.  let's commit all work so we can start sharing this with others.
#
#         also, is the skill packaged in a way that makes it easy to install for others?
#         """
#
#     @editor
#     Example: Words attributed to Claude
#       Given Claude wrote:
#         """
#         This is a proposed development argument interpreting David's question of 11 October 2026, accepted in conversation on the same day. A check found that the documented install left out the MCP extra, that installing the skill needs a clone and a symlink, that uvx starts the server from GitHub in about 19 seconds the first time and 1.7 seconds after, and that the skill names no tool by its full prefix. Claude Code's plugin behavior is taken from its documentation and must be verified in use. The causes, predicted benefit, negative branches, prerequisites and actions below are authored hypotheses and proposals, not observations or measured outcomes.
#         """
# RC-ARGUMENT-END
