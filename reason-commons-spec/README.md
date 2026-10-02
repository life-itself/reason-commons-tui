# Reason Commons specification bundle

Reason Commons is a persistent terminal reasoning workspace from its first usable
release. Start with [the replacement TUI transcript](example-tui-session.txt),
then [the main specification](reason-commons-specification.md), section 0.
[TUI-DESIGN.md](../TUI-DESIGN.md) fixes the design direction and
[tui-reasoning-design.md](tui-reasoning-design.md) specifies rendering and input.
These are integrated requirements, not optional future proposals.

The transcript follows the fictional Payments deployment case from first use
through causal scrutiny, a scoped conflict, beneficial/adverse predictions,
preparation, a bounded pilot, a breached safeguard and a revised follow-up.
Its 120×40 screens use the room for boxes, complete ALL boundaries, both Cloud
sides and selected-object inspection. 80×24 and 40×24 views retain the logic.

V1 ships p0-p2: durable case, persistent TUI and complete goal/action/review
loop for one operator. It does not need formal graph authoring or group stances.
[The v1 session](example-mvp-session.txt) demonstrates that smaller scope with
visible controls and an original-forecast/outcome table, not typed commands.
The shell remains for launch, resume and offline automation; explicit `--plain`
selects the linear accessibility/compatibility presentation.

- 16 jobs to be done with observable signals and traceability.
- 11 `.feature` files: 127 named scenarios/outlines, expanding to 157 cases.
- V1: 64 scenarios and 86 expanded cases across p0-p2, including workspace,
  input/focus, recovery and readable review. Counts are acceptance work, not
  a feature count.
- Later p3-p5: 63 scenarios and 71 expanded cases for causal models, facilitated
  positions/Cloud, full tools and cross-tool review.
- `cli-wireframes.txt`: 35 ASCII views of record payloads/optional plain output;
  9 are
  v1 views. These <=76-column fragments have no authority over TUI layout.
- `example-tui-session.txt`: the canonical cumulative p5 specimen, 15 consultant
  calls and 18 revisions. It replaces the shell transcript in spec section 9.
- `example-mvp-session.txt`: v1 specimen, 6 calls and 6 revisions, 80×24.
- `example-review-session.txt`: independent p5 correction/review specimen,
  3 calls and 3 revisions; before/after and dependent reviews remain visible.
- `example-shell-session.txt`: compatibility pointer to the new transcript.
- `build_tui_specimens.py`: deterministic authoring helper for the 37 ASCII frames;
  it is not a TUI application or a causal layout engine.
- `delivery-phases.json`: phase dependencies, explicit v1 IDs, artifact profiles
  and session ledgers. `check_bundle.py` validates and synchronizes the bundle.

## Development sequence

| Phase | Increment | Scenarios | Expanded cases |
|---|---|---:|---:|
| p0 | Durable minimal case | 9 | 9 |
| p1 | Persistent TUI workspace | 32 | 46 |
| p2 | Complete v1 goal-action-review loop | 23 | 31 |
| p3 | Partial causal reasoning | 29 | 31 |
| p4 | Facilitated positions and Cloud | 16 | 16 |
| p5 | Full tools and cross-tool review | 18 | 24 |

Scenario-local phase, release and evaluation tags select acceptance sets, not
runtime stages. [Delivery gates](delivery-phases.md) require actual terminal,
semantic and participant evaluation. Build cumulatively; ship v1 after p2.

```sh
python3 reason-commons-spec/build_tui_specimens.py
python3 reason-commons-spec/check_bundle.py --sync
python3 reason-commons-spec/check_bundle.py --select v1 --list
python3 reason-commons-spec/check_bundle.py --select through-p4 --list
python3 -m unittest discover -s reason-commons-spec -p 'test_*.py'
```

Edit the builder's authored copy to revise screen content, rebuild specimens,
then synchronize the main spec. Other features/fragments can be edited directly
before `--sync`. The checker verifies frame geometry, ASCII, event/call/revision
ledgers, tags, profiles, outline rows, traceability, envelopes and appendices.
It does not run product behavior or validate consulting quality, accessibility,
learnability or lovability. This repository is a specification, not a runnable
product; future Gherkin step definitions and prototype evaluation remain work.

[interface-improvement-plan.md](interface-improvement-plan.md) retains historical
rationale. Its older release boundary is superseded by the current contract.
