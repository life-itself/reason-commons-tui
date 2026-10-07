# Reason Commons specification bundle

Reason Commons is a persistent terminal reasoning workspace from its first usable
release; its executable is `reason-commons`. This folder holds the product
specification and authored specimens. The application elsewhere in this
repository implements part of it; [the delivery report](../docs/p0-delivery.md)
says which scenarios run today.

Start with [the v1 TUI journey](example-mvp-session.txt) for the release target,
or [the complete visual reasoning journey](example-tui-session.txt) for the
cumulative roadmap. Read [the main specification](reason-commons-specification.md),
[TUI-DESIGN.md](../TUI-DESIGN.md) and
[the rendering contract](tui-reasoning-design.md) before implementation.

The Payments journey follows goal definition, causal scrutiny, a scoped conflict,
beneficial/adverse forecasts, preparation, a bounded test, a breached safeguard
and a revised follow-up. The 120x40 canvas makes room for readable boxes, complete
ALL boundaries, both Cloud sides and selected-object evidence. The 80x24 and
40x24 views preserve the same logic. Every scene replaces the prior scene in one
persistent application; ACTION annotations describe keys and contributions.

V1 ships p0-p2: a durable case, persistent workspace and a complete goal/action/
review loop for one operator, with the six trees growing in its conversation.
The consultant drafts and the operator decides what enters the model: proposals
wait in a backlog unless the operator chose automatic acceptance, a change flags
what cites it for review, and any acceptance can be undone.
The trees' formal checks and group positions arrive later.
The shell launches/resumes and provides offline utilities. The
[accessible ordered presentation](accessibility.md) shares the same labeled
actions, literal editor, selection and deliberate submission. No interactive
command language or alternate shell conversation defines ordinary work.
Users work with questions, reports, relationships, goals, tests, actions and
reviews. Internal consultant records do not become numbered stationery objects.

- 17 jobs to be done with observable signals and traceability.
- 13 `.feature` files: 147 named scenarios/outlines, expanding to 183 cases.
- V1: 84 scenarios and 112 expanded cases across p0-p2.
- Later p3-p5: 63 scenarios and 71 expanded cases.
- 38 ASCII screens across three synchronized TUI specimens.
- `example-mvp-session.txt`: v1, 6 consultant calls and 9 revisions, 80x24;
  embedded first in specification section 8.
- `example-tui-session.txt`: cumulative p5, 15 calls and 18 revisions;
  the canonical full journey in section 9.
- `example-review-session.txt`: p5 correction/review, 3 calls and 3 revisions;
  before/after formulations and dependent reviews in section 10.
- `build_tui_specimens.py`: deterministic screen authoring helper; not a runnable
  TUI or a causal layout engine.
- `delivery-phases.json`: phase dependencies, v1 IDs, actual screen identities,
  interface policy and session ledgers.
- `check_bundle.py`: validates/synchronizes artifacts and rejects reintroduced
  legacy branding, stationery labels, command routing and numbered UI exchanges.

## Development sequence

| Phase | Increment | Scenarios | Expanded cases |
|---|---|---:|---:|
| p0 | Durable minimal case | 9 | 9 |
| p1 | Persistent TUI workspace | 32 | 47 |
| p2 | Complete v1 goal-action-review loop, trees in conversation, proposals decided in a backlog | 43 | 56 |
| p3 | Partial causal reasoning | 29 | 31 |
| p4 | Facilitated positions and Cloud | 16 | 16 |
| p5 | Full tools and cross-tool review | 18 | 24 |

Scenario-local tags select acceptance sets, not mandatory runtime stages.
[Delivery gates](delivery-phases.md) require actual terminal, semantic and
participant evaluation. Build cumulatively; ship v1 after p2.

```sh
python3 reason-commons-spec/build_tui_specimens.py
python3 reason-commons-spec/check_bundle.py --sync
python3 reason-commons-spec/check_bundle.py --select v1 --list
python3 reason-commons-spec/check_bundle.py --select through-p4 --list
python3 -m unittest discover -s reason-commons-spec -p 'test_*.py'
```

Edit the builder's authored copy, rebuild specimens, then synchronize the spec.
Features and supporting contracts are edited directly. The checker verifies
geometry, ASCII, exact screen identities, event/call/revision ledgers, tags,
profiles, outline rows, traceability, envelopes and embedded copies. Its regression
tests exercise document safeguards. They do not run application behavior, prove
consulting quality or establish accessibility, learnability or lovability.
