# Working on Reason Commons

How we develop (method, workflow, testing, recipes) is in
`docs/development/README.md`.

Read `ARCHITECTURE.md` and the owning `src/reason_commons/domain/CONTEXT.md`
before changing commons behavior. The existing specification and its scenario-local
delivery tags define scope. P0 is implemented; a personal-use TUI slice exists. Of p1, 31 of 32
scenarios are delivered (the gate lists which); of p2, the trees-in-conversation scenarios
(S128–S134), deciding what enters the model (S135–S150), the loop's records (S32, S37,
S95, S101), how the question is presented (S03, S04, S17, S93, S121) and leaving and
returning (S94); the gate lists the rest of p2 as outstanding.

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
