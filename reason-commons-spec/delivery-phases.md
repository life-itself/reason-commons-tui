# V1 scope, development increments and evidence

The accepted simplified application is v1. The reconciliation authorized on
10 October 2026 aligns requirements with that baseline. It does not reconstruct
an authenticated engineering history or certify the product's effectiveness.
The demon was a metaphor for lost MVP discipline. Git can establish code changes;
it cannot authenticate the hypothetical development argument.

[The matrix](../docs/v1-reconciliation.md) gives every scenario a disposition and
maps reachable capabilities, including supporting views absent from the default
sidebar. [The current report](../docs/v1-delivery.md) records checks actually run;
[the old report](../docs/p0-delivery.md) preserves earlier evidence with its original
phase vocabulary. This document supersedes the old “ship after p2” roadmap.

## Tag contract and authority

Each scenario or outline has exactly one stable `@Snn` identity, increment
`@p0`–`@p7`, release `@v1` or `@later`, and evaluation kind:

- `@automated`: deterministic application, interface or adapter behavior. The gate
  runs every selected identity and every expanded row, refusing skipped or undefined
  steps. Authored consultants establish transitions, never consulting quality.
- `@semantic`: useful consulting assessed against a professional rubric and retained
  actual proposals. A v1 tag means the capability exists; evidence can remain pending.
- `@usability`: participant protocols and individual results, including assistive
  technology use. Agent inspection and automated UI checks cannot complete them.

Scope/identity tags are scenario-local, never inherited from Feature or Examples.
Outlines cannot mix scope. `@Jnn` links jobs. Both `features/` and
`../tests/conversation/features/` are authoritative tagged sources declared in
`delivery-phases.json`; the latter retains its separate runner and provider fixtures.
The reviewed v1 ID list locks scope, while the gate derives execution directly
from `@v1 and @automated`. There are no secondary delivered-ID lists.

Tags select requirements, not runtime stages or participant questionnaires.
Evidence status is recorded separately in the matrix and delivery/validation
reports. Future requirements are not incomplete automated v1 coverage.

## Editorial development progression

| Increment | Dependency and observable result | Release |
|---|---|---|
| p0 Durable attributed records | Retain literal inputs and sources; validate closed schema and exact references; atomic publication, immutable ancestry, explicit retry, stale-target rejection, one writer and portable archives | v1 foundation |
| p1 Proposals and acceptance | On durable records, distinguish retention from model membership; explicit/automatic admission, dependency confirmation, final rejection and undo, operator-controlled policy | v1 foundation |
| p2 Inspectable reasoning and history | On accepted membership, inspect goals, six partial trees, single typed links, source words, versions, stage history and explicit-reference review flags; import/export LTP without inference | v1 foundation |
| p3 Guided work and revision | On inspectable records, offer one next move, literal editor, responsive local navigation, fixed offline loop, forecasts/results, action/effect distinctions, correction, draft restoration and accessible ordered text | v1 working interface |
| p4 Import prior work and continue | Bring prior RC development into that interface with honest provenance and actual adoption; free-form continuation, collision-safe resume, Settings, provider choice, usage/cost controls and one deliberate deeper reply | accepted v1 baseline |
| p5 Richer causal tools | Joint-premise groups, rival routes, WIP integration, structured local authoring, evidence/assumption detail, feedback/comparison views and review beyond explicit references | future |
| p6 Facilitated group positions | Exact-version wording/belief/reliance and actor-bound forms; speaker switching without draft reassignment or invented consensus | future |
| p7 Full reasoning and implementation tools | Richer goal/forecast/prerequisite/action representations, adverse paths, criteria, shared requirements and cross-tool traceability/review | future |

Every increment depends on the preceding one. This is one plausible order of
responsibilities culminating in the accepted app, not the sequence people must
follow in RC or a claim about historical releases. P0 includes the compatible
record schema, so later increments can exercise richer fixtures without demanding
later interaction. Each scenario uses an isolated fixture through application use
cases; none depends on another scenario having run.

V1 already draws all six partial trees and a complete five-box Cloud, with one goal
at the Goal Tree's top and single links allowed across trees. Future full tools
means richer semantics and checks, not the first existence of those trees.
Commands/Views exposes Tests, Loop actions, Reasoning and Commons context even when
the imported sidebar omits them. Density, theme, caret and folding are presentation
state. Decisions, sources and persistence remain application capabilities.

## Scope is not a wire profile or an evidence certificate

The existing v1 protocol and archives use `delivery_profile: "p2"`. Preserve that
value, `CaseCapabilities`, `case` keys and `.reasoncase` compatibility. Future
illustrations use legacy profiles p3/p5; those are unsupported by the v1 runtime.
Changing delivery increments is not a migration of records or providers.

The accepted release scope remains v1 even while semantic and participant evidence
is outstanding. The automated gate checks all deterministic v1 behavior; completion
of that gate alone makes no effectiveness, live-model or participant claim. Scope
reconciliation must not retag a required failing automated baseline as future.

## Selection and complete execution

```sh
.venv/bin/python reason-commons-spec/check_bundle.py --select v1 --list
.venv/bin/python reason-commons-spec/check_bundle.py --select later --list
.venv/bin/python reason-commons-spec/check_bundle.py --select p5 --list
.venv/bin/python reason-commons-spec/check_bundle.py --select through-p5 --list
.venv/bin/python scripts/check_v1.py
```

`v1` selects p0–p4; `p5` selects one future increment; `through-p5` includes all
prior regressions. The historical `scripts/check_p0.py` command delegates to the
same complete v1 gate. It also runs the structural regressions and all implementation,
architecture and adapter tests. Live provider calls are opt-in and outside the gate.

## Outstanding evaluations of v1

Use S73 and S111 for first-time navigation and the test/review loop; use S185 for
RC-on-RC continuation and provenance. Start without a manual at 120×40 and 80×24,
with varied terminal/domain experience, and include assistive-technology users in
the ordered workflow. Record each person's actions, confusion, repairs and reasoning.
The existing proposed navigation target is four of five completing core tasks in
15 minutes without moderator commands; treat this as a formative protocol, not a
population estimate. Everyone should predict the consultant boundary, distinguish
acceptance from truth and action authority, and recover drafts and exact targets.
Consequential failures require repairs and new participant checks.

Semantic evaluations assess neutrality, useful next moves, causal restraint,
units/denominators, original forecasts, protection breaches and immature outcomes.
The expanded inventory also identifies reported positions and bounded Cloud
reasoning already expressible by v1. Existing live runs and AI pre-screens remain
in [validation](../docs/validation.md); they do not complete attributed human review.
A missing evaluation fixture stays visible as an evidence gap.

Future comparisons (S88, S109, S112) retain their own protocols. Confidence thresholds,
editing proposals before adoption, TUI source attachment, and home rename/delete
are explicit candidate backlog in the matrix; they are not silently promised by v1.
Authenticated simultaneous users, reminders, remote synchronization and external
execution remain outside release scope. A review date schedules nothing.
