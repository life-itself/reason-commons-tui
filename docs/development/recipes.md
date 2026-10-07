# Recipes

Checklists for common changes. Each one is the [workflow](workflow.md) applied: the
scenario comes first, the rule goes in the narrowest layer, and the documents move
with the code.

## Add or change a domain rule

1. Find or write the scenario. For a rule the specification already covers,
   implement its steps; do not edit the feature.
2. Add the term to `src/reason_commons/domain/CONTEXT.md` if the language is new.
3. Enforce the rule in `domain/model.py`. If it constrains what a consultant may
   propose, express it in `domain/contract.py`; `adapters/provider_support.py`
   projects that contract into each provider's schema, so providers pick it up
   without their own copy.
4. Add negative cases to `tests/test_domain.py`. The rule must hold with no skill,
   agent, or interface present.
5. Run the gate. A provider's output is untrusted: domain validation, not the schema,
   decides what is published.

## Add an application use case

1. Write the scenario against the use case's inputs and outcomes, not a screen.
2. Implement it on `CaseApplication` in `application/service.py`, returning plain
   serializable values and copies, never repository or aggregate handles.
3. Publish it on `CaseCapabilities` in `application/ports.py` with an **identical
   signature**. `tests/test_architecture.py` fails otherwise. Only presentation-only
   state (checkpoints) and session lifecycle are exempt; they are listed in
   `.workflow.json`.
4. Expose it where participants need it: an MCP tool in `adapters/mcp_server.py`, and
   an offline command in `adapters/cli.py` if it is useful without an agent. These
   call the use case and add no rules.
5. If a result is shown to a person, render it from the shared presentation value in
   `adapters/rendering.py`. Do not recompute meaning in the renderer.
6. Decide whether the skill procedure should use it. Updating `SKILL.md` is a
   separate change with its own trace test.

## Add a consultant provider

1. Write scenarios in `tests/conversation/features/providers.feature` for selection,
   readiness, failure reporting and an end-to-end consultation. Add steps in
   `tests/conversation/steps/provider_steps.py`.
2. Implement the `Consultant` port in a new module under `adapters/`, using
   `adapters/provider_support.py` for the shared grammar, redirects and JSON
   handling. Tag exceptions with a `category` from the safe set and an integer
   `http_status`; never carry a message or body that could hold a secret.
3. Add `describe_settings` to the adapter and register the provider in
   `bootstrap.py` (`PROVIDERS`, `provider_settings`, `configured_consultant`). The
   application must not learn the provider's name.
4. Add a loopback fake in `tests/servers.py` and adapter tests for the wire protocol,
   limits, redirects, malformed replies and credential hygiene.
5. Document it in `docs/providers.md`: setup, settings, checking readiness, and what
   its failures mean. Keep the page neutral between providers.
6. Do not claim live quality from the fake. Live evidence belongs in
   [validation](../validation.md).

## Add an interface action (for example, a TUI key)

1. Map the action to an existing `CaseCapabilities` operation. If none fits, the gap
   is a missing application use case: add it first (previous recipe), then bind it.
2. Interface-owned state (focus, viewport, expansion, caret) is tested in adapter
   tests. Domain effects and local-versus-consultant routing are tested at the
   application boundary.
3. A confirmation or disabled control is a hint only. The use case must reject the
   same operation when called directly.
4. Follow `TUI-DESIGN.md` and the specification's interface scenarios; the TUI
   implements part of p1, and the gate lists which p1 scenarios are delivered.

## Change a skill procedure

1. Read what the procedure may rely on: the glossary and `application/ports.py`. Move
   any domain meaning that crept into `SKILL.md` back to its owner.
2. Change the workflow only: which capabilities, in what order, with what authority.
3. Update the trace tests in `tests/test_skills.py` and `tests/test_skill_agent.py`
   to assert calls, ordering, forbidden access and resulting state, not wording.
4. If behavior with a real model could change, run the opt-in evaluation and keep
   the evidence (see [validation](../validation.md)). Passing fakes does not show a
   model follows the procedure.
5. Confirm the application still enforces every rule without the skill.

## Fix a bug

1. Reproduce it as a failing scenario or test at the lowest layer that shows it.
2. Fix it in the layer that owns the behavior.
3. Keep the test. Check whether the same flaw could occur in the other adapter or
   interface, since they share a surface.

## Change the specification

Not without the user's explicit authorization. If you believe a scenario is wrong or
missing, write down which scenario, why, and the proposed change, then ask. The
delivery manifest and `reason-commons-spec/check_bundle.py` lock scope on purpose:
tagging a later scenario `@v1` is not a shortcut.
