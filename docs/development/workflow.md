# Development workflow

The loop for every change, then how to know it is finished, then when to stop and
ask. The recipes in [recipes.md](recipes.md) apply it to common changes.

## The loop

**0. Orient.** Read `AGENTS.md`, [the overview](README.md), `ARCHITECTURE.md` and
`src/reason_commons/domain/CONTEXT.md`, plus the specification scenarios the change
touches. Run the gate once so you know the starting state, including any failures
that are already there.

**1. Classify the change.** Decide which owner it concerns (see the table in the
overview): a domain rule, an application use case, an adapter, a skill procedure, an
interface, or documentation only. This decides where the code goes and which tests
apply. If it spans several, split it into steps.

**2. Specify first.** Write or extend the scenario in the right place (see
[testing strategy](testing-strategy.md#where-a-new-scenario-goes)), in domain
language, through use cases. Do not touch the specification features without
authorization. Run it and confirm it fails for the right reason.

**3. Write the steps.** Steps define the interface the code must satisfy, so write
them before the implementation. Drive the application use cases only.

**4. Implement in the narrowest layer that can enforce it.** Domain rule in
`domain/`, orchestration in `application/`, protocol or format in `adapters/`,
selection in `bootstrap.py`. Never give the skill or the TUI a rule the application
does not enforce. If you need an outward import, a port is missing.

**5. Go green.** Make the scenario pass with the least code that does so, then tidy.
Run the neighboring suites, not only the new one.

**6. Cover what Gherkin should not.** Add adapter tests for bytes, sockets, exit
codes, limits and input normalization. Add a domain test for a new rule's negative
cases. Add or adjust skill tests if a procedure or host changed.

**7. Prove the tests can fail.** Mutation-check the new scenarios in a scratch copy
(see [testing strategy](testing-strategy.md#proving-a-test-can-fail)).

**8. Update the documents the change touches.** At minimum: `CONTEXT.md` for a new
term, `ARCHITECTURE.md` for a boundary or guarantee, the user guides for anything a
participant sets or sees, and `docs/p0-delivery.md` when scope changes. Run every
command and check every path you wrote.

**9. Run the full gate** and report.

## Definition of done

- [ ] A scenario or test specified the behavior before the code existed.
- [ ] The rule is enforced by the domain or application, not only by a skill or UI.
- [ ] Specification scenarios are unchanged (or a change was explicitly authorized).
- [ ] New scenarios were shown to fail, and a deliberate break was caught.
- [ ] `python3 scripts/check_p0.py` passes, or each failure that cannot run in this
      environment is named, with its cause.
- [ ] The shared capability surface covers any new semantic operation, and
      `tests/test_architecture.py` passes.
- [ ] No credential, provider message or response body is stored or logged.
- [ ] Documents and examples match the behavior, with commands actually run.
- [ ] The summary says what was verified, what was not, and what remains.

## Stop and ask

Do not guess. Stop and ask the user when:

- the work seems to require changing a specification scenario or its delivery tags;
- two authoritative sources disagree;
- a domain-significant operation has no place on `CaseCapabilities`;
- the change would add a second bounded context or an outward dependency;
- the work would make a provider call, spend money, or touch anyone's real commons data
  beyond a disposable fixture;
- you cannot make the gate pass without weakening a test or hiding a failure.

## Working practices

- **Small, whole changes.** One behavior per commit, with its scenario, steps, code,
  tests and documents together. Commit only when asked.
- **Never edit what you did not read.** Read the file and its neighbors first.
- **Disposable commons.** Experiments use temporary stores. Do not write into a
  participant's commons root, and never store credentials in a commons or an export.
- **Leave scope honest.** P0 is implemented; p1 and p2 are partly delivered, and the
  gate prints which p1 scenarios are still outstanding. Do not describe planned
  behavior as delivered.
- **Prefer the plain solution.** No event bus, generic dispatcher, service container
  or framework until a real need appears.
