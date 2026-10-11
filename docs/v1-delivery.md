# Accepted v1 delivery and reconciliation

Status: accepted personal-use baseline, reconciled on 10 October 2026, with a
user-requested feedback and feature-argument follow-up on 11 October 2026 on
`codex/v1-spec-reconciliation`, from `030cbdd`. The current simplified app defines
release scope. [The full reconciliation matrix](v1-reconciliation.md) inventories
reachable capabilities and every disposition; [the delivery manifest](../reason-commons-spec/delivery-phases.json)
and scenario-local tags define the dependency progression and execution selection.

## What changed

All original S01–S150 identities and their useful requirements remain. Domain and
application execution are unchanged. The original reconciliation updated interface
help/module descriptions and verification/fixture tooling; the follow-up also
changes adapter feedback as described below. Dependency
increments p0–p4 culminate in v1; p5–p7 retain future features. Existing owned
conversation/provider cases gain S151–S175; S176–S187 cover previously missing
baseline operations and a distinct continuation usability evaluation. Outdated
Actions terminology and the richer Cloud contract are clarified. Basic supporting
views remain reachable through Commands despite the small imported sidebar.

Scope is separate from evidence: 132 v1 identities expand to 166 cases, comprising
112 automated identities / 138 cases, 16 semantic identities / 24 cases and four
usability identities / four cases. The future backlog contains 59 identities /
67 cases. The complete contract has 191 identities / 233 cases in 18 feature files.
No hardcoded delivered-subset list overrides these tags. The v1 gate verifies each
selected identity, each expanded row and every step actually passes.

READMEs, user guides, architecture/workflow, manifests, delivery reports,
evaluation guidance, contribution guidance, authored specimens and runtime
screenshots are reconciled. Older reports/plans retain dated evidence with
historical/superseded status. The development reconstruction remains explicitly
hypothetical/editorial; the demon is a metaphor for lost MVP discipline. Source
words, AI interpretation and actual adoption remain distinct.

## Reconciliation validation recorded on 10 October

The starting gate passed before retagging: 476 pytest tests, 26 structural checker
tests and 121 expanded acceptance cases across the original six delivered slices.
It used disposable commons and mock providers; local socket permission was needed
for mock-server tests. No paid/live consultant was used.

Final validation **passed**:

| Check | Actual result |
|---|---|
| Complete v1 gate through the compatible `check_p0.py` entry point | 477 pytest tests, 30 structural regressions; 109 automated identities / all 135 expanded cases executed and passed |
| Product acceptance | 84 identities / 107 cases passed |
| Owned conversation/provider acceptance | 25 identities / 28 cases passed |
| New-scenario sensitivity | All 11 purposeful mutations detected in disposable copies; unmodified baseline passed first |
| Runtime screenshots | 65 fixture records regenerated (14 RC import, 51 tutorial/editorial/offline-provider); source and PNG hashes recorded, imported views visually inspected |
| Step-capture utility | Four S176 outline rows, 16 passed steps with 16 images; no undefined selected steps or capture errors |
| Documentation / architecture / gate checks | 11 focused checks passed; 41 pages' relative links verified; no diff whitespace errors |
| Final help/setup wording and gate help | 26 targeted tests passed after the text corrections; both gate entry points display help without starting tests |
| Legacy-named engine example | Four authored revisions; resumed and exported/imported state identical |
| Data/provenance preservation | SHA-256 unchanged for all 11 protected archive, source and compatibility-fixture files |

[Machine-readable validation](v1-validation-results.json) records scope hashes and
counts; [mutation results](v1-mutation-results.json) name the removed behavior and
failing assertions; [integrity evidence](v1-integrity.json) retains original
protected-file hashes. [The screenshot manifest](images/runtime-manifest.json)
records actual runtime fixtures and image hashes. The general renderer now owns
`tutorial-*` home images, while the primary renderer owns `home`, `home-help` and
`first-start`, so one example no longer overwrites the other's pictures.

Visual checks covered imported Next step, 80×24 layout, history, an earlier stage's
narrative and changes, pending backlog, adoption, acceptance Settings, trees and
Commands' supporting views. The newly adopted review fixture retains its original
import-time note about awaiting review; membership, empty Backlog and History show
the actual later adoption. That earlier wording is not rewritten as a new event.
These are layout/state observations, not participant usability evidence.

`python3 scripts/check_p0.py` remains a compatible entry point to the complete v1
gate in `scripts/check_v1.py`; the project virtual environment supplies dependencies.
The checker separately validates synchronized embedded features, 38 authored ASCII
screens, response-envelope compatibility, scope and reconciliation inventory.
Authored screens are layout illustrations, including explicitly future sessions;
they are not recordings of the app or live-model evidence.

## Feedback and feature-argument follow-up, 11 October

David reported that submitting a contribution appeared to change nothing. Read-only
inspection found a saved `guided/1` reply and one automatically accepted literal
note; it had performed no adaptive AI analysis or tree update. This is a reported
usability problem and a concrete provider diagnosis, not evidence about all users.

The adapter follow-up makes the active consultant visible, keeps a lasting receipt
derived from published replies/membership, and marks actual accepted tree changes
until the affected destination is opened. Waiting proposals do not mark unchanged
trees. The receipt is reconstructed on reopening; update markers are session-local
presentation state. No provider is silently switched and no source/history is rewritten.

The complete proposed development argument now lives with S188–S191 in
[one feature](../reason-commons-spec/features/15_contribution_feedback.feature).
[The development convention](development/feature-arguments.md) gives each authored
claim/link one native proposal identity and explicit scenario references. Its 30
authored updates were submitted through use cases into a disposable review-mode
commons and checked against exactly 30 pending records, their source attribution
and resolved endpoints. The checker detects invalid identities, sources, links,
scenario references, repeated YAML keys and inappropriate automated benefit claims.
No tree argument was added to a participant's working commons.

The complete follow-up gate **passed**: 485 pytest tests, 30 structural regressions
and all 112 automated v1 identities / 138 expanded cases (87 product identities /
110 cases; 25 conversation identities / 28 cases). Four purposeful mutations were
detected in disposable copies: suppressing the receipt, dropping accepted markers,
marking unchanged pending trees, and omitting one authored proposal. All 68 runtime
fixtures were regenerated and their image hashes checked. The new receipt at
120 and 80 columns and the update markers were visually inspected. All 11 protected
files still match their original hashes; 14 focused argument, documentation,
architecture and gate checks also passed. The first follow-up run found a missing
image link while screenshots were still being generated; the completed rerun passed.

The machine-readable report preserves the 10 October run separately from this
follow-up. S191's participant evidence is outstanding. A production Gherkin importer
and a TUI capable of executing coding work remain future design; these tools
establish a correspondence, not those product capabilities.


## Human-readable feature argument follow-up, 11 October

David's supplied revision highlighted that the YAML argument made a human-facing
specification read like an application payload. The owning feature now follows
its sentence-based structure: named tree Rules, proposed Given/When/Then examples,
explicit assumptions and evidence limits. These explanatory examples are comments;
the four executable acceptance scenarios retain their exact steps and tags. Source
words appear at the end of the argument and retain their previous text exactly.

The checker derives the same 30 native claim/link proposals from explicit roles,
identities and declarations. Reused claim IDs must keep their sentence, role and
source; an inconsistency mutation was detected. The complete gate passed again:
487 pytest tests, 30 structural regressions and all 112 automated identities /
138 expanded cases. All 21 focused argument, documentation, development,
architecture and gate checks passed. Release scope, application behavior, protected
files and screenshots are unchanged by this follow-up. Human readability and
participant benefit still require human review; the parser is specification tooling,
not a production feature importer.

## Evidence outstanding

The release contract evaluates existing capabilities in 16 semantic and four
participant scenarios. Their complete live/participant evidence remains
outstanding, including newly recognized units, reported authorship, bounded Cloud
work, real incompatibility and imported continuation. Existing dated consultant,
skill-agent and regression observations are preserved in [validation](validation.md),
with their limitations. Automated state transitions, fake-provider replies and
screenshots do not establish useful consulting, reduced cognitive burden, useful
next actions, participant usability, accessibility with assistive technology,
source consent, agreement or real-world outcomes.

Future contracts remain discoverable in the matrix and through
`check_bundle.py --select later --list`. They do not enter the current application
gate. Native imports, archives, retained sources and compatible `p2` protocol
identifiers are preserved. The separate Second Renaissance example remains a
consent-draft editorial reading example, not an authenticated development history.
