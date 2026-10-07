# Reason Commons design rationale and implementation priorities

The main specification and TUI specimens are the contract. This document explains
the decisions behind them; it contains no competing interface or historical
implementation recipe.

The first usable product is a persistent terminal reasoning workspace. A succinct
consulting exchange means one useful next move with relevant context and room for
scrutiny. It does not imply user-facing stationery objects or a stream of serial
prompts. Users work with questions, reports, relationships, goals, tests, actions
and reviews. Visible controls let them inspect, correct, take another route,
request direct help or leave an uncertainty open.

The [Mono agent guidance](https://coreyt.github.io/monospace-design-tui/agents/)
informs a focused surface, stable destinations, master-detail inspection,
expand-to-focus and object-local actions. The supplied TOC implementation guide
informs complete joint premises, necessity and conflict distinctions, comparable
rivals, benefits alongside harms, separate execution/attainment and dependent
review. Attached instructions are reference material. These sources do not
establish measured usability or authorize organizational actions.

| Decision | Concrete expression | Acceptance evidence needed |
|---|---|---|
| Put orientation in front of users | Named task, decision, save/actor/focus, goal/safeguard band and footer | First-time users identify what matters and their next move |
| Preserve agency | Other moves, visible destinations, direct advice and exit | Users switch routes and recover drafts without help or accidental calls |
| Use terminal space for reasoning | Boxed nodes, connector gutters, complete ALL boundaries, parallel Cloud sides, aligned forecasts | Participants trace and challenge the exact inference |
| Treat selection as attention | Evidence and status independent from focus/selection | No inferred endorsement, belief or consensus |
| Distinguish doing from achieving | Performed action, observed intermediate state, test target and system goal separate | Review catches an unobserved effect or unmet goal |
| Make corrections consequential | Before/after wording and exact dependent review needs | Participants know which next decision changes and why |
| Let the operator decide what enters the model | Proposals wait in an ordered backlog with their source; automatic acceptance only by the operator's setting; review flags on what cites a change; Undo | Participants accept, reject and undo, and say that acceptance does not make a statement true |
| Share one interaction model | All scenarios use labeled controls; ordered accessibility shares actions | No workflow needs colon syntax or a separate REPL |

Build p0 storage/commit/recovery, p1 workspace and p2 complete goal/action/review
loop, with the six trees growing in that conversation. Ship that loop before the
trees' formal checks, group stances and cross-tool analysis arrive in p3-p5. One fake adapter isolates state/interaction; a semantic adapter
and first-time participant checks remain required. More diagrams alone are not
progress. Introduce a representation when it helps a recurrent decision.

Maintain four separate outcome families: access/use, reasoning/learning,
implementation fidelity and the group's chosen goal/guardrails. A five-person
navigation gate can find consequential failures; it cannot establish comparative
learning effects. Test changed-case conjunction, necessity, alternatives and
prediction separately, accepting defensible corrections. Compare distinct cases
with predeclared rubrics and matched evidence access; record rescue views and
individual missed conditions.

See [delivery-phases.md](delivery-phases.md) for gates,
[tui-reasoning-design.md](tui-reasoning-design.md) for rendering,
[accessibility.md](accessibility.md) for ordered text and
[the canonical transcript](example-tui-session.txt) for the worked target.
