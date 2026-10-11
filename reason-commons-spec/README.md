# Reason Commons specification bundle

The accepted simplified app is **v1**. Scenario-local tags describe its scope and
an editorial dependency progression, plus a findable future backlog. This is a
plausible development argument, not an authenticated historical release sequence.
See [the reconciliation matrix](../docs/v1-reconciliation.md),
[the current delivery report](../docs/v1-delivery.md) and
[the delivery contract](delivery-phases.md).

The product helps people find useful next actions while reducing analysis and
record keeping. People supply values and real-world knowledge. RC includes its
own AI cost, human attention and accumulated reasoning in that assessment.
A complete tree or trial is never required merely to continue a conversation.

Both `features/` and `tests/conversation/features/` carry stable scenario identities,
release, increment and evaluation tags. The manifest declares their runners.
`@v1` means accepted baseline scope; `@automated` selects deterministic execution.
`@semantic` and `@usability` evaluate existing capabilities without implying that
their evidence is complete. `@later` retains unimplemented richer requirements.

- 17 `.feature` files: 187 named scenarios/outlines, expanding to 229 cases.
- V1: 128 scenarios and 162 expanded cases.
- Future: 59 scenarios and 67 expanded cases.
- 38 ASCII screens across three synchronized authored illustrations.

| Phase | Increment | Scenarios | Expanded cases |
|---|---|---:|---:|
| p0 | Durable attributed records | 9 | 9 |
| p1 | Proposals and acceptance | 10 | 10 |
| p2 | Inspectable reasoning and history | 12 | 17 |
| p3 | Guided work and revision | 63 | 86 |
| p4 | Import prior work and continue | 34 | 40 |
| p5 | Richer causal tools | 28 | 30 |
| p6 | Facilitated group positions | 13 | 13 |
| p7 | Full reasoning and implementation tools | 18 | 24 |

`p0`–`p4` culminate in v1; `p5`–`p7` describe future increments. These are delivery
labels. Serialized `delivery_profile: "p2"` remains the compatible v1 wire/archive
profile; it is not renamed when increments change.

`example-mvp-session.txt` illustrates a fictional v1 test loop (six authored
consultations, nine revisions); it abstracts layout and is not a runtime capture.
`example-tui-session.txt` and `example-review-session.txt` are explicitly future
p7 illustrations of richer logic and group positions. Their legacy profiles
remain p5. Actual v1 screenshots are generated from disposable application
fixtures, with [RC-on-RC](../docs/restoration/working-import.md) the primary example.
The Second Renaissance example is a separate editorial source-based illustration;
its drafted interpretations do not establish participant adoption or trial success.

```sh
.venv/bin/python reason-commons-spec/build_tui_specimens.py
.venv/bin/python reason-commons-spec/check_bundle.py --sync
.venv/bin/python reason-commons-spec/check_bundle.py --select v1 --list
.venv/bin/python reason-commons-spec/check_bundle.py --select later --list
.venv/bin/python reason-commons-spec/check_bundle.py --select through-p5 --list
.venv/bin/python scripts/check_v1.py
```

The checker verifies scope, counts, traceability, ASCII geometry, screen identities,
legacy profiles, authored ledgers and synchronized copies. The gate executes every
selected automated identity and expanded row through the appropriate boundary.
Neither establishes useful live consulting, participant usability or accessibility.
Edit the specimen builder, rebuild, then synchronize embedded copies. Features and
supporting contracts are edited directly with specification authorization.
