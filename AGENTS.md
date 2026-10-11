# Working on Reason Commons

How we develop (method, workflow, testing, recipes) is in
`docs/development/README.md`.

Read `ARCHITECTURE.md` and the owning `src/reason_commons/domain/CONTEXT.md`
before changing commons behavior. The accepted simplified app is v1. Scenario-local tags in both specification and
conversation features define scope; `reason-commons-spec/delivery-phases.json`
defines their runners and dependency progression (p0–p4 for v1; p5–p7 future).
Read `docs/v1-reconciliation.md` for dispositions and reachable capabilities, and
`docs/v1-delivery.md` for current evidence. Delivery labels are distinct from the
compatible serialized `delivery_profile: p2`. The development progression and
RC-on-RC story are editorial/hypothetical, not authenticated by Git history.

## Every change is a proposed tree update

Reason Commons is developed with Reason Commons. Before editing any file, classify
the request as argued, new argument, upkeep or not explicable, following
`docs/development/tree-updates.md`:

- **New behavior, scope or method:** reply first with a proposed tree update (the
  template in that document) and make no edits until the participant accepts it.
- **Not explicable in the trees:** recommend against it and say why; build it only
  if the participant overrides, and record that override in the argument.
- **Upkeep** (no reasoning changes) proceeds, with its reason stated.

A feature request is never upkeep. Every commit touching guarded paths ends with
`Tree-update: <proposal-id>` or `Tree-update: upkeep - <reason>`; run
`python3 scripts/check_tree_updates.py` before opening a pull request.

## Working rules

Keep domain knowledge in the context/model and acceptance behavior in `.feature`
files. Skills consult those artifacts and call application capabilities.
New development proposals keep their sourced tree argument and scenario links in
the owning feature; see `docs/development/feature-arguments.md`. Authored updates
remain proposals, and automated checks do not certify causal or participant claims.
Domain and application modules must not depend on interfaces, storage implementations,
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

Run `python3 scripts/check_v1.py` after application or scope changes
(`scripts/check_p0.py` remains a compatibility entry point). Update the current
delivery report when scope changes. New interfaces use the same application boundary;
normal human interaction follows the existing TUI contract, without a shell REPL.
