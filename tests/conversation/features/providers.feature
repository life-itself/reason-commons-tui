@conversation @automated @providers
Feature: The consultant is a replaceable choice made outside the commons
  A participant chooses which model consults: a local model through LM Studio,
  or Anthropic. The choice is explicit, checkable offline, and never stored in
  commons state. A failure explains what to check without exposing a secret, and
  the participant's literal words are always kept for an explicit retry.

  Scenario: Use the local model when nothing else is chosen
    Given no consultant has been chosen
    When I check the consultant settings
    Then LM Studio is selected by default
    And no request has been sent to any provider

  Scenario: Choose Anthropic with the environment
    Given the environment chooses Anthropic with an API key
    When I check the consultant settings
    Then Anthropic is selected by the environment and is ready
    And the settings name ANTHROPIC_API_KEY but never show its value

  Scenario: An explicit choice overrides the environment
    Given the environment chooses Anthropic with an API key
    When I explicitly choose "lm-studio"
    Then LM Studio is selected by an explicit choice
    And the composed consultant is the LM Studio consultant

  Scenario: Reject an unknown provider by name
    When I explicitly choose "openai"
    Then the choice is rejected and names lm-studio and anthropic as the valid providers

  Scenario: Say what is missing when Anthropic has no key
    Given the environment chooses Anthropic without an API key
    When I check the consultant settings
    Then Anthropic is not ready because ANTHROPIC_API_KEY is not set

  Scenario: Keep the participant's words when Anthropic is not configured
    Given the environment chooses Anthropic without an API key
    And a commons opened with the configured consultant
    When David contributes to the empty commons
    Then the application reports the consultant unavailable because of configuration
    And David's literal words are retained for explicit retry
    And no revision was published
    And the commons can still be read offline

  Scenario Outline: Explain a provider failure without revealing its secret
    Given a consultant that fails with a <category> problem containing a secret
    And a commons opened with that consultant
    When David contributes to the empty commons
    Then the application reports the consultant unavailable because of <category>
    And the participant is told to <check>
    And the secret appears nowhere in the saved commons

    Examples:
      | category      | check                                  |
      | configuration | run the providers check                |
      | http_error    | check the credential and model access  |
      | timeout       | allow more time or check provider load |
      | connection    | check the provider is running          |

  Scenario: Switch consultants on the same commons
    Given a commons consulted by "first-model"
    When the commons is reopened with the consultant "second-model"
    And David replies to the displayed question
    Then the earlier records and forecast are unchanged
    And each applied request records the consultant that produced it

  Scenario: Consult Anthropic end to end
    Given an Anthropic server and an environment choosing it with an API key
    And a commons opened with the configured consultant
    When David contributes to the empty commons
    Then a question is saved
    And the API key is not stored in the commons or its export

  Scenario: Claude Haiku 5.5 consults when no Claude model is chosen
    Given an Anthropic server and an environment choosing it with an API key
    And a commons opened with the configured consultant
    When David contributes to the empty commons
    Then a question is saved
    And the commons records that Claude Haiku 5.5 produced it
    And the consultant settings name claude-haiku-5-5 as the default Claude model

  Scenario: Count what a Claude reply cost outside the commons
    Given an Anthropic server and an environment choosing it with an API key
    And a commons opened with the configured consultant, counting its usage
    When David contributes to the empty commons
    Then a question is saved
    And the usage log counts one Claude Haiku 5.5 reply of 12000 tokens in and 900 out, about $0.00165
    And the commons and its export hold no token counts or cost
    And the usage log holds no words from the commons, no commons name, no path and no key

  Scenario: Consult a local model end to end
    Given a local LM Studio server and an environment choosing it
    And a commons opened with the configured consultant
    When David contributes to the empty commons
    Then a question is saved
    And the commons records that LM Studio produced it

  Scenario: Keep the experimental agent runner local-model only
    Given the environment chooses Anthropic with an API key
    And an empty commons store
    When I contribute using the experimental agent runner
    Then the command is rejected because that runner requires lm-studio
    And nothing was retained in the commons
