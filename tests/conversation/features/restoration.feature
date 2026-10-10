@conversation @automated
Feature: Continue Reason Commons from a source-backed editorial import
  The imported working model distinguishes literal sources, reconstruction and
  a hypothetical implementation history instead of inventing human approvals.

  Scenario: Import prior work without fabricating a completed trial
    Given the source-backed Reason Commons working baseline
    When I inspect the imported reasoning and its sources
    Then the six partial trees include the already implemented interface
    And the import has no fabricated prospective test or historical human approval

  Scenario: Continue developing the system without being forced into a trial
    Given the source-backed Reason Commons working baseline
    When I contribute a development issue through the offline guide
    Then my literal contribution is proposed for review
    And the current question still invites a contribution to Reason Commons

  Scenario: Read why the interface was built before importing its reasoning
    Given the source-backed Reason Commons working baseline
    When I revisit the reconstructed development stages
    Then manual use precedes the implemented interface and the import
    And the adopted model retains the argument and has no dismissed proposals

  Scenario: Require acceptance for an imported development argument
    Given the reconstructed development argument imported for review
    Then its reasoning waits in the backlog instead of appearing as adopted trees
    When I accept the imported reasoning
    Then the complete development argument appears in the working model

  Scenario: Choose how future reasoning enters the model
    Given the source-backed Reason Commons working baseline
    When I require acceptance and contribute an additional observation
    Then the observation waits for my decision
    When I choose automatic acceptance and contribute another observation
    Then the new observation enters the model and the earlier one still waits
