@conversation @providers
Feature: The coding agent hosting the skill can be the consultant
  David found that the skill he used before needed no API key, while the TUI and
  its MCP server need one for any hosted consulting. We propose a host consultant:
  the coding agent that hosts the skill drafts the reply on the participant's own
  subscription, and the application receives, validates and commits or rejects it
  exactly as it does a provider's.

  The argument below is proposed reasoning. Its causal explanations, predicted
  benefit and risks need evidence. The scenarios after it test behavior with
  fixture replies. Passing them proves the integration, not the quality of
  host-model consulting, and does not adopt the argument.

# RC-ARGUMENT-BEGIN
# rc-argument: schema 1 | proposal host-consultant | status proposed
#
#   @goal @argument
#   Rule: Goal - an existing condition this serves
#     Inherited RC goal: help people and groups advance goals they value through
#     useful TOC reasoning. This serves a necessary condition already in the
#     development commons; it adds none and replaces nothing.
#
#     @gt_support @supports
#     Example: Consulting without a key keeps the interface usable
#       Given we predict that participants use the TUI's consulting and decisions through a skill on their own coding-agent subscription, with no API key, on the same commons folders [DE frt_benefit]
#       And assuming a separate key and bill are a setup barrier comparable to ineffective UX; no adoption measure is claimed
#       Then keep the interface minimal enough to understand and use during important work [NC gt_minimal]
#
#   @current_reality @argument
#   Rule: Current reality - why the skill needs a key
#     David reports the problem. Both explanations are Claude's findings in the
#     repository, not David's; that they cause his difficulty is a hypothesis.
#
#     @crt_server_cause @causes
#     Example: The server consults, and the agent only relays
#       Given Claude found that the MCP server chooses a provider when it starts and the application calls that provider itself, so the coding agent hosting the skill only relays [cause crt_server_calls]
#       And assuming the adaptive consultant participants want is a hosted model
#       Then David reports that using Reason Commons through the TUI and its harness now needs an API key, which reduces usability and ease of adoption [UDE crt_ude]
#       But this link still needs semantic evidence
#
#     @crt_alternatives_cause @contributes_to
#     Example: The keyless options are a local model or the offline guide
#       Given Claude found that consulting without a key needs a local model or uses the offline guide, which supplies no adaptive analysis [cause crt_alternatives]
#       And assuming the participant has no capable local model or wants adaptive consulting
#       Then David reports that using Reason Commons through the TUI and its harness now needs an API key, which reduces usability and ease of adoption [UDE crt_ude]
#       But this link still needs semantic evidence
#
#   @conflict @argument
#   Rule: Conflict - deliberately not formed
#     Not established: keeping the consultant separate from the presenter and
#     using the agent already present can look opposed. That is a negative branch
#     of this change, recorded below, not one side of a cloud.
#
#   @future_reality @argument
#   Rule: Future reality - what we expect the change to do
#     A candidate injection, its predicted benefit and four possible costs.
#     Automated tests establish none of these predictions.
#
#     @frt_benefit_route @produces
#     Example: The hosting agent consults, and the application keeps its checks
#       When we let the coding agent hosting the skill draft the consultant's reply, which the application receives, validates and commits or rejects like any provider's [injection frt_injection]
#       And assuming the hosting agent follows the returned procedure well enough to produce valid proposals
#       Then we predict that participants use the TUI's consulting and decisions through a skill on their own coding-agent subscription, with no API key, on the same commons folders [DE frt_benefit]
#       But this prediction still needs usability evidence
#
#     @frt_unverified_route @contributes_to
#     Example: Negative branch - the model cannot be verified
#       When we let the coding agent hosting the skill draft the consultant's reply, which the application receives, validates and commits or rejects like any provider's [injection frt_injection]
#       And assuming someone reads the recorded consultant version as authenticated
#       Then we predict that the application cannot verify which model wrote a proposal, because the recorded version is what the agent declares [NBR frt_unverified]
#
#     @frt_dual_role_route @contributes_to
#     Example: Negative branch - the agent is both consultant and presenter
#       When we let the coding agent hosting the skill draft the consultant's reply, which the application receives, validates and commits or rejects like any provider's [injection frt_injection]
#       And assuming the procedure can instruct but not enforce what the agent reasons from or how it presents its own proposals
#       Then we predict that the agent presenting the commons could draw on chat context the commons does not hold, favour its own proposals or decide for the participant [NBR frt_dual_role]
#       But this prediction still needs usability evidence
#
#     @frt_allowance_route @contributes_to
#     Example: Negative branch - every turn uses the subscription allowance
#       When we let the coding agent hosting the skill draft the consultant's reply, which the application receives, validates and commits or rejects like any provider's [injection frt_injection]
#       And assuming the participant's subscription has usage limits and a finite context window
#       Then we predict that every turn, reads included, uses subscription allowance, and each consultation adds about 11k to 47k tokens to the chat, uncounted by the usage log [NBR frt_allowance]
#       But this prediction still needs usability evidence
#
#     @frt_quality_route @contributes_to
#     Example: Negative branch - consulting quality is unmeasured
#       When we let the coding agent hosting the skill draft the consultant's reply, which the application receives, validates and commits or rejects like any provider's [injection frt_injection]
#       And assuming the consulting procedure was validated with a provider's model over that provider's transport, not with a host agent
#       Then we predict that host-model consulting may be worse or better than the validated consultant, and fake-consultant tests cannot tell [NBR frt_quality]
#       But this prediction still needs semantic evidence
#
#   @prerequisite @argument
#   Rule: Prerequisites - what must be true first
#     Proposed implementation conditions for a host consultant the application
#     treats exactly like a provider.
#
#     @prt_requires_request @requires
#     Example: The agent needs the provider's request, and only when it is due
#       Given we want to let the hosting agent consult while the application keeps every check it applies to a provider's reply [objective prt_objective]
#       And assuming a reply drafted from different inputs could not be compared with a provider's
#       Then we must first ensure that the hosting agent receives exactly the request a provider would be sent, and only for a retained request awaiting a consultant [IO prt_same_request]
#
#     @prt_requires_path @requires
#     Example: The agent's reply goes through the provider's path
#       Given we want to let the hosting agent consult while the application keeps every check it applies to a provider's reply [objective prt_objective]
#       And assuming a separate path for host replies would let checks drift apart
#       Then we must first ensure that a supplied reply is received, validated, then committed or given a rejected receipt, as a provider's is [IO prt_same_path]
#
#     @prt_requires_fit @requires
#     Example: The consultation has to reach the agent whole
#       Given we want to let the hosting agent consult while the application keeps every check it applies to a provider's reply [objective prt_objective]
#       And assuming a truncated consultation would leave the agent reasoning from part of the commons
#       Then we must first ensure that a complete consultation fits in the host's tool result [IO prt_fits]
#
#     @prt_requires_discovery @requires
#     Example: The agent has to find this skill and server
#       Given we want to let the hosting agent consult while the application keeps every check it applies to a provider's reply [objective prt_objective]
#       And assuming an older single-file reason-commons skill may also be installed
#       Then we must first ensure that Claude Code finds this skill and its MCP server, not a skill that writes another format [IO prt_discovery]
#
#     @prt_size_resolution @overcomes
#     Example: A declared result size lets a real commons through
#       Given we must first ensure that a complete consultation fits in the host's tool result [IO prt_fits]
#       And assuming the client honours the result size the server declares for the consultation tool
#       Then this overcomes the obstacle that a consultation measured about 39k to 47k tokens on real commons, and Claude Code saves any tool result over 50,000 characters to a file the agent could not read whole [obstacle prt_size]
#
#   @transition @argument
#   Rule: Transition - what we will build
#     Proposed actions and their observable effects, then an evaluation in use.
#     No action is marked executed in this proposed argument.
#
#     Background: Recorded, but not yet linked to any step
#       Given Claude found that the MCP tools already reach every TUI command and view that reads or changes a commons, except importing and exporting trees, which the reason-commons trees command reaches [reality tt_reality]
#       And we need to let the hosting agent reply as the consultant without moving any rule into the skill [need tt_need]
#       And we observe a participant using the skill with the host consultant and no key, and record setup friction, allowance used, role confusion and proposal quality against the validated consultant [action tt_evaluate]
#
#     @tt_consultation_implements @implements
#     Example: One function builds the request for a provider and for the agent
#       When we add a consultation read to the application, built by the same function consult uses for a provider and refused for a request not awaiting a consultant [action tt_consultation]
#       And assuming an adapter adds the shared consulting procedure and proposal schema, not the application
#       Then we must first ensure that the hosting agent receives exactly the request a provider would be sent, and only for a retained request awaiting a consultant [IO prt_same_request]
#
#     @tt_consultation_produces @produces
#     Example: The agent sees what a provider would see
#       When we add a consultation read to the application, built by the same function consult uses for a provider and refused for a request not awaiting a consultant [action tt_consultation]
#       And assuming this is an interface contract, not a forecast of the agent's reasoning
#       Then the hosting agent receives the procedure, domain context, request and proposal schema every provider consultant is sent, and a refusal for an applied, stale or unknown request [effect tt_consultation_effect]
#
#     @tt_host_implements @implements
#     Example: The agent's proposal enters through consult
#       When we add a host provider to the MCP server whose consultation and propose tools hand the agent's proposal to the application's consult [action tt_host]
#       And assuming the per-call host consultant only returns the proposal it was given
#       Then we must first ensure that a supplied reply is received, validated, then committed or given a rejected receipt, as a provider's is [IO prt_same_path]
#
#     @tt_host_produces @produces
#     Example: A host reply is saved or refused like a provider's
#       When we add a host provider to the MCP server whose consultation and propose tools hand the agent's proposal to the application's consult [action tt_host]
#       And assuming the agent declares its name and model, which the application records but cannot check
#       Then a valid host proposal is saved with a host consultant version and waits for the participant; an invalid one gets a rejected receipt and the words are kept [effect tt_host_effect]
#
#     @tt_skill_produces @produces
#     Example: The skill reaches the TUI's operations without a key
#       When we write the host procedure and the consultant's role into the skill, with trees imported and exported through the reason-commons trees command [action tt_skill]
#       And assuming the hosting agent has a shell for that command
#       Then in a Claude Code session without a key a participant can create a goal, contribute, decide proposals, read the trees and backlog, and import and export trees [effect tt_skill_effect]
#
#     @tt_setup_implements @implements
#     Example: The server lets a whole consultation through
#       When we document a user-scope Claude Code recipe for the MCP server with the host provider, declare the consultation's result size on the server, and link the skill where Claude Code finds it [action tt_setup]
#       And assuming participants follow the documented recipe and the client honours the declared size
#       Then we must first ensure that a complete consultation fits in the host's tool result [IO prt_fits]
#
#     @tt_discovery_implements @implements
#     Example: The setup makes this skill the one Claude Code finds
#       When we document a user-scope Claude Code recipe for the MCP server with the host provider, declare the consultation's result size on the server, and link the skill where Claude Code finds it [action tt_setup]
#       And assuming the skill's description distinguishes it from the older single-file skill
#       Then we must first ensure that Claude Code finds this skill and its MCP server, not a skill that writes another format [IO prt_discovery]
#
#   @sources @argument
#   Rule: Sources - retained words and declared speakers
#
#     @user_report
#     Example: Words attributed to David
#       Given David wrote:
#         """
#         something i'm not sure about: before, the skill that was being used (the one this tui is meant to replace) did not require an api key (it was an agentic skill).  now that we're using a TUI and basically have developed a harness, we need an API key - which reduces usability and ease of adoption.  what to do about this?  is this repo still usable as a skill?
#
#         imagine we could do everything this TUI does, but as a skill
#
#         why can't the skill use the coding agent?  why would an API key be required?
#         """
#
#     @editor
#     Example: Words attributed to Claude
#       Given Claude wrote:
#         """
#         This is a proposed development argument interpreting David's questions of 11 October 2026, accepted in conversation on the same day. A read of the repository found that the MCP server composes its consultant at start-up and the application calls it, that the MCP tools reach every TUI command that reads or changes a commons except tree import and export, and that a complete consultation measured about 11k tokens on an empty commons and about 39k to 47k tokens on three real ones. The causal explanations, predicted benefit, negative branches, prerequisites and actions below are authored hypotheses and proposals, not observations, approvals or measured outcomes.
#         """
# RC-ARGUMENT-END

  @S192 @p4 @v1 @automated @addresses_crt_ude @implements_tt_host
  Scenario: Check the host consultant without any key
    Given no consultant credential is set
    When I check the consultant settings for the host consultant
    Then the host consultant is ready and needs no credential
    And the settings say the application cannot verify which model writes a proposal
    And no request has been sent to any provider

  @S193 @p4 @v1 @automated @implements_tt_consultation @verifies_prt_same_request @verifies_tt_consultation_effect
  Scenario: Give the hosting agent exactly what a provider would be sent
    Given a commons served to a hosting agent as its consultant
    And David's contribution to the empty commons is retained
    When the hosting agent asks for the consultation
    Then it receives the procedure, domain context, request and proposal schema every provider consultant is sent
    And no model was called and no revision was published

  @S194 @p4 @v1 @automated @addresses_crt_ude @implements_tt_host @verifies_prt_same_path @verifies_tt_host_effect
  Scenario: Save the hosting agent's proposal through the provider's path
    Given a commons served to a hosting agent as its consultant
    And David's contribution to the empty commons is retained
    When the hosting agent proposes a valid reply as "example-agent" with model "example-model"
    Then a question is saved and the reply's proposals wait for David's decision
    And the received proposal was retained before it was validated
    And the applied request records a host consultant version naming the declared agent and model

  @S195 @p4 @v1 @automated @implements_tt_host @verifies_prt_same_path @verifies_tt_host_effect
  Scenario: Reject an invalid host proposal and keep David's words
    Given a commons served to a hosting agent as its consultant
    And David's contribution to the empty commons is retained
    When the hosting agent proposes a reply that cites a record the commons does not have
    Then the reply is rejected with a receipt that names the broken rule
    And David's literal words are retained and no revision was published
    When the hosting agent proposes a valid reply as "example-agent" with model "example-model"
    Then a question is saved and the reply's proposals wait for David's decision

  @S196 @p4 @v1 @automated @implements_tt_consultation @implements_tt_host @verifies_prt_same_request @verifies_tt_consultation_effect
  Scenario Outline: Refuse a consultation and a proposal for a request not awaiting a consultant
    Given a commons served to a hosting agent as its consultant
    And a request that <state>
    When the hosting agent asks for the consultation
    Then the consultation is refused because the request <reason>
    When the hosting agent proposes a valid reply as "example-agent" with model "example-model"
    Then the proposal is refused because the request <reason>
    And the commons is unchanged

    Examples:
      | state                                  | reason                     |
      | was already answered                   | is already answered        |
      | was overtaken by a newer question      | is stale                   |
      | was never retained                     | was never retained         |

  @S197 @p4 @v1 @automated @addresses_crt_ude @implements_tt_host
  Scenario: Offer the host consultant only where an agent can answer
    Given a commons served to a hosting agent as its consultant
    Then the server offers consultation and propose instead of consult, submit and retry
    And changing the acceptance setting is still refused without the operator's grant
    When the commons is served with the offline guide instead
    Then the server offers consult, submit and retry and not consultation or propose
    When I explicitly choose "host" for the terminal workspace
    Then the choice is rejected because only an agent using the MCP server can be the host consultant

  @S198 @p4 @v1 @automated @addresses_crt_ude @implements_tt_host @verifies_tt_host_effect
  Scenario: Continue a host-consulted commons in the terminal workspace
    Given a commons served to a hosting agent as its consultant
    And David's contribution to the empty commons is retained
    And the hosting agent proposes a valid reply as "example-agent" with model "example-model"
    And David accepts one of the reply's proposals and rejects the other through the server
    When the commons is opened in the terminal workspace
    Then the saved question is shown with the host consultant as the one that asked it
    And the accepted proposal is in the model, the rejected one is not, and nothing waits

  @S199 @p4 @v1 @usability @addresses_crt_ude @implements_tt_evaluate @verifies_frt_benefit @verifies_frt_dual_role @verifies_frt_allowance
  Scenario: Evaluate the host consultant in a participant's own coding agent
    Given a participant with a coding-agent subscription and no API key
    When they set up the skill from the documentation and work on a goal of their own
    Then they can contribute, decide proposals and continue in the terminal workspace
    And setup friction, allowance used and any confusion between the agent's roles are recorded
    And the agent's proposals are reviewed for reasoning drawn from outside the commons

  @S200 @p4 @v1 @semantic @implements_tt_evaluate @verifies_frt_quality
  Scenario: Compare host-model consulting with the validated consultant
    Given the same retained contributions consulted by a hosting agent and by a validated provider consultant
    When reviewers judge both replies against the consulting procedure without knowing which is which
    Then the comparison is recorded separately from automated results
    And no quality claim is made for the host consultant until it exists
