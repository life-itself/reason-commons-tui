# Working on Reason Commons

Read `ARCHITECTURE.md` and the owning `src/reason_commons/domain/CONTEXT.md`
before changing case behavior. The existing specification and its scenario-local
delivery tags define scope. P0 is implemented; p1/p2 are not yet delivered.

Keep domain knowledge in the context/model and acceptance behavior in `.feature`
files. Skills consult those artifacts and call application capabilities. Domain
and application modules must not depend on interfaces, storage implementations,
skills or agents. `bootstrap.py` is the composition root.

Maintain semantic parity: every domain-significant local interactive operation
must be expressible through `CaseCapabilities`. A particular skill can use a
subset, but the shared capability surface must cover the operation. Focus,
viewport, expansion and caret state are exempt.

The TUI projects and accelerates interaction with application state. It defines
no reasoning invariants, consulting semantics or persistence behavior outside
application use cases. Enforce consequential rules at that boundary even when
the UI also supplies validation hints or confirmations.

Set up BDD fixtures and execute behavior through application use cases. Test
byte-level files, process locks and crash boundaries in adapter tests. Evaluate
skill capability traces and resulting state separately from application BDD.
Do not infer live-model quality or participant usability from fake-consultant
tests. Preserve the existing scenarios unless the user authorizes a specification
change; do not filter required cases to conceal undefined or failing steps.

Run `python3 scripts/check_p0.py` after application changes. Update the delivery
report when scope changes. New interfaces use the same application boundary;
normal human interaction follows the existing TUI contract, without a shell REPL.
