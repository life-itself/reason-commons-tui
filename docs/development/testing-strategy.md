# Testing strategy

Different tests answer different questions. Keep them apart so each stays
deterministic where it can be, and honest about what it does not prove.

## The five kinds of test

| Kind | Question it answers | Drives | Lives in |
|---|---|---|---|
| **Domain** | Is the rule enforceable with no skill or agent present? | Domain objects directly | `tests/test_domain.py` |
| **Application acceptance (BDD)** | Does the application do what the scenario says? | Application use cases, with a fixture consultant | `tests/acceptance/` (spec scenarios), `tests/conversation/` (conversation and provider scenarios) |
| **Interface acceptance (BDD)** | Does the workspace do what a p1 scenario says, through its visible controls? | The real TUI, by keys, with a fixture consultant | `tests/acceptance/steps/workspace_steps.py`, `tests/acceptance/workspace.py` |
| **Adapter** | Does an adapter honor its port, down to bytes, sockets and exit codes? | The real adapter against a fake or temp resource | `tests/test_storage.py`, `test_anthropic.py`, `test_lm_studio.py`, `test_providers.py`, `test_mcp_*.py`, `test_ltp_conversion.py` |
| **Skill** | Does an agent use the capabilities correctly? | A skill host or harness over fake ports | `tests/test_skills.py`, `test_skill_agent.py`, `test_invocation.py` |
| **Live evaluation** | Does a real model do useful work end to end? | A real model, opt-in | `evaluations/`, `scripts/evaluate_lm_studio.py`, `scripts/check_anthropic.py --smoke` |

Domain, acceptance, adapter and skill tests run in the gate and need no model, key
or network beyond loopback. Live evaluations are slow, costly and non-deterministic,
so keep them few, retain their evidence, and never make them part of the gate.

## Acceptance (BDD)

- **Gherkin states what must be true**, in the language of `CONTEXT.md`, not how the
  code does it. Avoid screens, files, classes and HTTP in scenario text.
- **Step definitions use the narrowest stable boundary**: the application use
  cases. They do not reach into aggregates, repositories, files or UI widgets.
- **Fixtures are set up through use cases too.** Outbound ports may be replaced:
  `ScriptedConsultant` for the consultant, `FaultStore` to inject storage failures
  at the port. Never put faults inside step assertions.
- **No LLM.** Acceptance uses a deterministic consultant. Do not infer live-model
  quality from fake-consultant tests.
- **Byte-level behavior is an adapter test**: file formats, process locks, crash
  boundaries, wire protocols, redirects and exit codes are asserted there, not in
  Gherkin.
- **Isolation.** Each scenario gets its own temporary commons. Anything global, such as
  environment variables, is cleared and restored in `environment.py`.

### Interface acceptance (p1)

The p1 scenarios are about the workspace itself: focus, Tab and Enter, literal
typing, Esc, resizing. Their steps drive the real Textual app headlessly through
`tests/acceptance/workspace.py`, pressing keys as a person would, and never call
widget methods to cause an effect. They read outcomes at the application boundary
(the fixture consultant's calls, revisions, retained inputs and receipts) and from
what is on screen. Fixtures are still built through use cases: the Forge commons of
the navigation scenarios is eight consultant replies and two tree imports.

Behave steps are synchronous and Textual's pilot is async, so the app runs in one
long-lived task on its own event loop and each step hands it a job. A step that
holds a consultant reply back (to browse while it is pending) sets
`wait_for_replies` to false until it releases it.

### The specification is immutable by default

`reason-commons-spec/features/` is the acceptance contract. Preserve the existing
scenarios unless the user explicitly authorizes a specification change. Never hide
a failing or undefined step by filtering scenarios; the gate checks that every
selected scenario actually ran and passed. Tags select sets and are scenario-local
(`@p0`–`@p5`, `@v1`/`@later`, `@automated`/`@semantic`/`@usability`); see
`reason-commons-spec/delivery-phases.md`.

### Where a new scenario goes

1. Is the behavior already in the specification? Implement its steps. Do not add a
   duplicate.
2. Is it new participant-visible behavior outside the specification, such as
   conversation flow or provider choice? Add it under `tests/conversation/features/`
   with `@conversation @automated`, and put its steps in `tests/conversation/steps/`.
   The gate runs every scenario in that directory.
3. Would it require changing or contradicting a specification scenario? Stop and
   ask.

## Skill tests

A skill is a procedure an intelligent executor follows, so its tests ask different
questions from application tests. Keep them in separate suites.

- Assert **effects and decisions**, not prose. Check which capabilities were called,
  in what order, which forbidden ones were not, what was retained, and the resulting
  commons state. Never assert the model's wording.
- Example assertions: `retain_input` precedes `consult`; no capability outside the
  invocation's authorization was reached; a blocked request is recorded; the saved
  result, not the agent's claim, decides success.
- The deterministic workflow driver is the baseline. A real tool-calling model
  running the actual `SKILL.md` is a live evaluation, with an authored downstream
  consultant to separate procedure from consulting quality.
- Gherkin can describe skill behavior too, but its steps drive a **skill harness**
  over fake ports, not the application steps used for acceptance.
- The application must not rely on the skill to be correct. If a skill test is the
  only protection for a rule, the rule is in the wrong place; see
  [architecture principles](architecture-principles.md).

## Proving a test can fail

A scenario that has only ever passed proves little. For each new or changed
scenario:

1. Run it before the implementation exists and confirm it fails for the right
   reason: undefined steps first, then the missing behavior.
2. After it passes, copy the repository to a scratch directory, deliberately break
   the behavior it claims to protect, and confirm that scenario fails. Restore
   nothing in your working tree; the scratch copy is disposable.

Typical breaks: drop the new field, let the lower-priority source win, leak the
secret into a message, swallow an error.

## Running things

Install with `python3 -m pip install -e '.[test,mcp]'`. Without installation, prefix
commands with `PYTHONPATH=src:.`.

```sh
python3 scripts/check_p0.py                                   # the full gate
python3 -m pytest -q                                          # implementation tests
python3 -m behave --tags "@p0 and @automated"                 # original p0 scenarios
python3 -m behave --runner tests.conversation.runner:ConversationRunner \
  tests/conversation/features                                 # conversation scenarios
```

`check_p0.py` runs the bundle check, the specification regressions, pytest, the p0
scenarios and the conversation scenarios, and verifies that every selected
scenario executed and passed.

## Reporting results honestly

State what ran and what did not. If a test cannot run in your environment (a
missing shell, an incompatible SDK version, no loopback sockets), say so and name
the test; do not describe the gate as passing. A green fake-consultant run
establishes the integration, not model quality, and the live evaluation evidence
is kept separate (see [validation](../validation.md)).
