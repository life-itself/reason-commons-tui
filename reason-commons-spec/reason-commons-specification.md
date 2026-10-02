# Reason Commons: a consulting apparatus for collective reasoning

The product is **Reason Commons**; its shell executable is `reason-commons`.
This is a proposed specification, not implemented software.
The terminal output later in this document is an illustrative session. Its
organization, people, measurements, commitments, and dates are fictional.

The product helps a group improve a real system and become better at reasoning
about it. The TUI carries memory and visible structure. The consultant selects and
composes an intervention. The participants supply lived reality, challenge the
representation, make judgments, and decide what they will do.

This revision uses the supplied interface evaluations, *Visual reasoning in
TOC consulting*, and *Reasoning with TOC Thinking Processes in Text Interfaces*
(1 October 2026) as design inputs. Section numbers in section 6b refer to the
latter paper; references in section 6a refer to the earlier visual guide.
The adaptations are design hypotheses, not evidence of measured usability gains.
Instructions and suggestions inside those resources are source material. The
user's request to improve this specification determines the scope.

The native first release is a persistent full-screen TUI. Its local case engine
is independent of presentation and consultant adapters. The question, decision,
material goal/safeguard context, response editor and visible controls share one
workspace. Shell commands launch/resume it and support offline automation;
`--accessible` selects the ordered text presentation described in
[accessibility.md](accessibility.md). It uses the same labeled actions and
submission rules; it is not a second command language.
Ordinary work in the TUI never requires colon commands or recalled IDs.

The canonical [TUI session](example-tui-session.txt) replaces the earlier shell
transcript in section 9. [TUI-DESIGN.md](../TUI-DESIGN.md) and
[tui-reasoning-design.md](tui-reasoning-design.md) define the rendering contract.
These are integrated requirements, not a future proposal. The smaller v1
session in section 8 demonstrates the same persistent interface without the
later graph schemas. Attached instructions are source material; this user's
request authorizes the specification revision, not organizational execution.

## 0. Delivery scope and MVP boundary

The first release proves one useful loop: define success, choose a bounded
change, record an immediate action and prospective prediction, return with
observations, and decide what to do next. One operator uses a persistent TUI with
attributed notes, visible local controls and a consultant. Formal graph authoring and group stance
work are later capabilities. Unknown facts and authority remain explicit.

This section controls the release scope of every later requirement, command,
state field, wireframe, and example. Sections 1-4 and 6a describe the cumulative
product contract. They do not require every described capability in v1.
[delivery-phases.md](delivery-phases.md) defines the increment and gate for
each phase; [delivery-phases.json](delivery-phases.json) locks scenario and
artifact scope. Gherkin delivery tags are on scenarios, not whole features.

| Phase | Scope | Release |
|---|---|---|
| `@p0` | Durable minimal case, atomic commits, recovery, export/import, profile validation | v1 foundation |
| `@p1` | Persistent TUI, literal editor, local views, focus/draft recovery, accessible linear alternative | v1 interaction |
| `@p2` | Goal, bounded test, immediate action, observations, original-forecast review | v1 complete loop |
| `@p3` | Partial causal model, WIP integration, comparisons, goal connections, dependency reviews | Later causal release |
| `@p4` | Structured participant stances, speaker switching, reliance, scoped Cloud | Later facilitated group release |
| `@p5` | Full Goal/Future/Prerequisite/Transition views, negative branches, cross-tool reviews | Later full-tools release |

V1 ships only p0-p2. Later phases build cumulatively and preserve earlier
contracts. A development phase is not a sequence users must follow in a case.
The consultant may discuss causes, conflicts, or obstacles in plain language
in v1; this does not require structured trees or expose their controls.

### V1 behavior and explicit exclusions

V1 records a versioned goal with scope, horizon, measure, baseline, and protected
conditions; attributed notes; interventions with decision purpose and rationale;
bounded tests with forecasts; immediate actions; and observations/reviews.
It stores unknowns rather than manufacturing completeness. It distinguishes
completed work, observed effects, supported predictions, and goal attainment.
An explicit goal-version reference lets a changed goal flag a test's relevance
for review without building a general dependency engine.

V1 controls are Send, Explain this, Other moves, Goal, Tests, Actions and
History, plus source and current-test inspection. The visible Views/Actions
controls provide navigation, export, retry, Help and Save and quit. They are
keyboard reachable without command syntax. Display only capabilities enabled
by the case profile. V1 uses one declared operator; structured speaker switching,
positions and full graph tools arrive in their tagged phases.

The Actions list and Help contain only operations enabled by the case profile.
There is no interactive colon-command parser, phrase router, command field or
REPL fallback in any presentation. Profile validation rejects unavailable actions
and schema patches before commit, preserves drafts, and explains the limitation.
It never sends an unavailable action to the consultant. Text in Response remains
literal, including text resembling a command. A v1 reader rejects unsupported
newer profiles without dropping fields; future migrations preserve ancestry
and original forecasts.

V1 shell scope is help/version, new/resume, read-only inspect/history, export,
and `reason-commons import BUNDLE --store PATH` into a new editable store. Import
refuses an existing destination; inspection never imports implicitly. JSON and
no-color behavior apply to the supported records only. Graph schemas need not
be implemented as empty collections in the v1 store.

The canonical full TUI session demonstrates the later p5 profile. The separate
[example-mvp-session.txt](example-mvp-session.txt) is the v1 delivery example.
Passing the later session or rendering every later reasoning view is not a v1 gate.

## 1. Jobs to be done

These are situations and desired progress, rather than a list of screens.
The acceptance signals are observable behavior; they are not promises that a
particular organizational intervention will succeed.

| ID | When... | I / we want to... | So that... | Observable acceptance signal |
|---|---|---|---|---|
| J01 | We have several problems but an unclear common purpose | Name the system, goal, horizon, measure, and conditions we must protect | We can judge an improvement in the whole system | Proposed goals, unknown measures, and each person's position are explicit |
| J02 | We return, change views, or hand over facilitation | See the few facts and statuses that change the current question | We need not reconstruct the case from memory | Compact status on views; consequential context beside the question; full context on request |
| J03 | We are stuck or overwhelmed | Make one useful reasoning move with feedback | We can progress and practice the actual skill | One primary prompt; the group can correct a link, supply a condition, or choose a test |
| J04 | A question is unclear, feels accusatory, or we need direct help | Change the intervention or coaching style | We can participate without performing a prescribed discovery ritual | Corrections affect the next question; direct advice is available when requested |
| J05 | We need another route or want to browse | Inspect succinct alternatives and navigate predictably | We retain agency without unnecessary model calls | Options say whether they open a view or ask the consultant; shortcuts have stable meanings |
| J06 | We doubt the question or its basis | Inspect its public rationale, evidence, assumptions, and related model | We can challenge the formulation intelligently | Stored supporting material opens locally and returns to the same live question |
| J07 | Several effects seem related | Construct and test explicit causal or necessity relationships | We can distinguish a useful explanation from an attractive story | Conditional links, AND groups, alternatives, and uncertainty remain visible |
| J08 | Someone supplies material we cannot connect yet | Retain it as WIP with its source | The contribution is heard without creating premature coherence | Stable WIP IDs; no invented arrows; later promotion retains provenance |
| J09 | Participants disagree or speak for one another | Record distinct positions on exact formulations | We can reason together without manufacturing consensus | Representation, belief, and willingness to test are separately attributable |
| J10 | Several possible constraints or causes compete | Find the uncertainty most likely to change our next action | We improve the system rather than a convenient local metric | Constraint hypotheses have goal-level predictions and meaningful alternatives |
| J11 | A remedy meets resistance or may cause harm | Represent legitimate needs, test necessity assumptions, and examine adverse effects | We can design a change that protects what matters | A faithful conflict or negative branch produces a specific question, prevention, or acknowledged tradeoff |
| J12 | We are ready to act | Define a bounded test, prerequisites, owner, prediction, and stopping conditions | We know what to do and can learn from it | A prospective prediction and executable next action are saved before results |
| J13 | Results arrive | Compare them with the original prediction and decide what changes next | We learn without rewriting the past | Delivery, guardrails, fidelity, comparability, alternatives, and the next decision are reviewed |
| J14 | We must stop, resume, inspect history, or transfer the case | Preserve a portable record independent of a provider conversation | Work survives interruption and can be inherited | A fresh offline process restores the case, cursor, draft, sources, dissent, and forecasts |
| J15 | The provider, parser, or storage fails | Understand what was retained and recover without duplicate work | We can trust the apparatus | Failure receipts distinguish retained input, pending reasoning, and committed revisions |
| J16 | We use a narrow terminal, a screen reader, multiline notes, or unfamiliar commands | Understand the interface and control what is submitted | The interaction supports our thinking rather than consuming it | Visible local actions, numeric answers, text equivalents, wrapping, and draft preservation |

There are two outcome families to evaluate. Organizational outcomes are the
group's chosen goal measures and protected conditions. Capability outcomes are
whether participants can make a similar reasoning move later with less help,
including identifying a condition or counterexample on a new case. reply count,
agreement with the consultant, and an empty WIP list are not success measures.

## 2. The product contract

### A. One useful next move, inside a navigable workspace

The original consulting thought experiment describes a concise exchange that
helps people do their own thinking. Its physical stationery metaphor is not a
product model. Users work with questions, reports, relationships, goals, tests,
actions and reviews. Do not introduce decks, hands, stacks, numbered consulting
objects or browsing commands for such objects. Internal `intervention` records
store the consultant's contribution; that schema name is not a navigation label.

Keep one primary question, recommendation or deliberate stopping point prominent.
Show why it matters, what changed, the relevant evidence and uncertainty, and
visible ways to inspect, correct, ask for another move, or leave. One recommended
move focuses attention; it does not constrain the user's next action. A useful
next move may ask a question, distinguish two ideas, offer advice or propose a
test. The consultant recommends it from the current evidence without claiming
one objectively ideal question.

Use the terminal's room to reason. A diagram, table or before/after comparison
belongs beside the decision it helps. Complete premises and material objections
have room before auxiliary panels. Expand locally when a broader view helps;
never compress the main experience into serial receipts and a prompt waiting
for remembered syntax. At small sizes page explicitly without concealing a
condition, critical number, dispute or threatened safeguard.

From p3, optional apprentice mode asks participants to perform the useful reasoning act
and gives targeted feedback. Direct mode offers concrete advice promptly. Both
respect uncertainty and user agency. An empty response or correction is input,
not a failure to cooperate.

### B. Persistent context is selected, not exhaustive

Each rendered view begins with case, committed revision, save status, declared
speaker, and focus in one short line (wrapping when needed). Local receipts
need not reprint it. Never use a checkmark alone to communicate durability.
The view title identifies browsing; historical views also show their as-of
revision and the live response target. Pending work has a separate label.

The persistent workspace uses compact pinned context. Show the complete goal, horizon,
protected conditions, and active test boundaries on startup/resume, whenever
those fields change, and through the visible Goal and Case context controls. The current question must also repeat any
condition, baseline, target, or uncertainty that materially changes its answer,
even if it was displayed earlier. A saved case with an unknown goal displays
"goal provisional" or "goal unknown" until the goal is defined.

Unresolved breaches and storage/provider failures take precedence over routine
focus in every affected view: name the breached condition and current value,
or distinguish retained input from uncommitted reasoning. Case context also
shows full model/WIP status, attribution, response target, and pending inputs.
Actions > Display > Expanded repeats this context; Compact is the default. Both are persisted cursor preferences, with no reasoning
revision or consultant call. Display density cannot hide an active breach.

Context is physically pinned in the default TUI: case/save/actor/view/focus
header, a short goal/safeguard band, and footer controls. Expand the task region
for complete diagrams and inspection; auxiliary panes collapse before decisive
premises. Navigation restores draft, caret, selected object, semantic scroll
anchor and live target. Incoming output cannot steal inspection focus. The
accessible ordered presentation uses recoverable scrollback and ordered snapshots.
Machine output and shell inspection omit interactive furniture. All displayed
facts come from committed state, with draft/pending changes separated. An archived question's original goal never replaces the current one.

### C. Model membership is separate from epistemic status

Use consistent visible terms: observation, claim, cause, assumption, conflict,
proposed change, obstacle, WIP, supported, disputed, and unknown. Explain TOC
terms where useful: an undesirable effect is an unwanted condition; an
injection is a proposed change. Do not make users learn the vocabulary first.

Each proposition has a stable ID, wording/version, source, source date or
unknown, kind, membership, and support. A statement can be in the model and
still be a hypothesis or disputed. WIP means not yet integrated into a coherent
relationship, not false, unimportant, or forbidden to use as evidence.
Promotion into a graph preserves the original contribution. Similar wording
does not justify a silent merge. Retired links remain in history.

WIP entry IDs and proposition IDs have different roles. For example, W1 can
point to proposition N2 before N2 is linked. Connecting N2 changes membership,
not identity; opening the original report always retains its contribution. Exact-ID search
resolves stored pointers locally; ordinary use selects readable report labels.

Evidence distinguishes measured records, participant reports, estimates, and
unknowns. The app records what was supplied; it does not certify a report.
Numbers carry units, periods, denominators, and scope when known.

The working model shows causal or necessity claims, evidence, alternatives,
conditions, and a concise decision rationale. It does not expose or promise
access to private model reasoning. Diagrams are proposals, not proof.

### D. The relevant Thinking Process is a tool, not a required stage

| Current question | Useful representation | Required distinction |
|---|---|---|
| What must be true to reach the goal? | Goal / intermediate-objective map | Necessary conditions are not individually sufficient |
| Why do effects recur? | Partial Current Reality Tree | Hypothesized sufficient causes, enabling conditions, and alternatives |
| Why do two legitimate needs require incompatible actions? | Evaporating Cloud | Shared objective, needs, actions, and necessity assumptions |
| What would a proposed change cause? | Partial Future Reality Tree | Predicted effects, not observed results |
| How could it backfire? | Negative branch | Adverse mechanism plus prevention or stopping condition |
| What blocks implementation? | Prerequisite Tree | Obstacle and necessary intermediate objective |
| What happens next and why? | Transition Tree / action view | Condition + action + expected effect |

A focused diagram normally shows one mechanism and its conditions. A
starting heuristic is 3–7 meaningful elements, not a cognitive capacity limit
or a hard truncation rule. Expand, align fragments, or use a table when the
question requires more. Expanded views label excerpts as partial. AND means joint
conditions, not two independently sufficient arrows. Feedback and delays must
be explicit. A Cloud uses necessity relationships, not causal arrows disguised
as a conflict diagram. An unresolved tradeoff or discriminating experiment can
be a successful endpoint; every case need not produce a complete suite of trees.

### E. A group has positions, not a single synthetic mind

Store separately: "this accurately represents what I said", "I believe this
claim", and "I am willing to rely on this formulation for this bounded test".
Attach each stance to an exact object version and a source. A substantive
revision does not inherit earlier assent. Silence is unknown.

From p4, one terminal operator records structured positions in a facilitated
group session. Actions > Change speaker > Priya changes the declared speaker label, not authenticated
identity. "Sam reports that Priya disagrees" is different from Priya directly
declaring a position. Organizational decision authority is supplied by the
group; the application does not infer it from majority, seniority, or typing access.
Simultaneous authenticated collaboration can be added later. It is not implied
by this facilitated-group increment.

## 3. Workspace interaction and the consultant boundary

This section defines the only human interaction model. Every ordinary workflow
uses visible labeled controls in a persistent workspace. Shell utilities are
separate and noninteractive. The accessible presentation changes layout and
reading order, not the domain actions or submission model.

### Orientation and agency

At rest, the workspace answers six questions: where am I, what are we deciding,
what deserves attention, what is uncertain, what can I do next, and what is saved?
Pin case, saved revision, declared operator, view and focus; show the current
goal and consequential safeguard context. Give the main task most of the canvas.
A current question has a human title, decision purpose and prominent prompt.
Stable internal intervention IDs belong in audit/details, not titles, counters,
response prompts or first-use instruction.

The first screen offers a literal Response editor, Send, How this works and Open
a saved case. Explain this and Other moves remain reachable as work develops.
No walkthrough, assent, prescribed answer or TOC vocabulary lesson gates action.

| Visible path | What it does | Boundary |
|---|---|---|
| Response > Send | Retains the exact response and asks for the next useful move | Asks consultant; one request |
| Explain this | Opens stored rationale and a worked reading of the current fragment | Local; no call |
| Other moves | Shows alternatives with their consequences before activation | Each item says local or asks consultant |
| Goal / Tests / Actions / History | Opens saved records; selecting a row opens its detail | Local; no call |
| Reasoning / Unlinked (p3+) | Explores stored relationships or original reports | Local; no call |
| Selected object > Evidence / Changes / Details | Inspects exact wording, version, sources and history | Local; no call |
| Selected relation > Record position (p4+) | Opens independent attributed position fields | Local; saves only explicit choices |
| Selected test > Record decision (p4+) | Records willingness to run that exact bounded version | Local; never inferred belief |
| Actions > Capture report / Add relationship (p3+) | Saves literal material or a fully specified human hypothesis | Local reasoning update |
| Actions > Ask for direct advice / Another question | Requests the displayed stored intent | Asks consultant; one request |
| Actions > Export / Save and quit / Retry retained input | Operates on the selected case or retained request | Consequence labeled; retry asks consultant only if needed |

Destinations are not stages. A user can inspect sources, revisit a goal, enter a
counterexample, request direct help or stop with uncertainty still open. Actions
is visible; Ctrl+P is optional. No essential path needs mouse, function keys,
modified Enter, color, Unicode, IDs or command syntax. Display only delivered
capabilities; do not present unavailable tools as tempting broken actions.

### Keyboard, selection and literal text

Exactly one control owns focus, named in the header/footer. Selection identifies
an object; it is not evidence, endorsement or focus. Tab/Shift+Tab traverse
controls. Arrows navigate within the focused list, map or editor. Enter/Space
activate a focused button or selected menu item; Enter in Response adds a line.
Tab to Send, then Enter submits once. Paste never submits. Esc leaves editing
for browsing without losing text; Esc from inspection restores the originating
view, selection, semantic scroll anchor, actor-bound draft and caret.

Every printable character in Response is literal, including numbers, question
marks, q, slashes, punctuation and command-looking text. There are no phrase
shortcuts that reinterpret answers. Lists select with arrows and Enter; printable
text in an explicitly focused filter filters locally. A no-match filter offers
Clear filter and Back; it cannot dispatch a hidden option or become evidence.

Search works over stored full wording and exact IDs, with readable labels,
versions and historical scope shown. A typo gets a local no-match message and
retains the filter and response draft. An exact ID is an optional address, not
required knowledge. Identical labels receive disambiguating scope/version text.

### Exact actions and attributed decisions

Focused object, inspected revision and live response target are distinct.
Browsing History does not retarget Send or restore old reasoning. A historical
question is read-only; Actions > Answer this earlier question explicitly selects
it while interpreting the response against current case state. Restore reasoning
is a separately labeled action that previews its source revision and appends a
new revision; it cannot rewind allocation or audit history.

Bind menu items and forms to their owning question, menu identity, base revision,
exact object versions, actor and displayed action mapping. A changed target,
revision or speaker invalidates the form; redisplay before accepting a new
selection. Restore and revalidate these bindings on resume before activation.
Opening, filtering, cancelling or invalidating a form creates no reasoning
revision or consultant call. Actions dispatch typed allowlisted intents, never
model-authored shell code. Unknown targets fail locally with a repair.

For an exact relation, Record position shows its complete formulation, decisive
conditions, scope and actor above separate fields:

```text
Recording for Priya (declared)                Relation: Jobs interrupted
                                             -> Orders finish late
Under: lost time cannot be recovered before promised dates.
Hypothesis; causal direction disputed. Historical wording is labeled if selected.

Wording:      [Accurate] [Inaccurate] [Unknown]   No change selected
Belief:       [Supported] [Disputed] [Unknown]   No change selected
Test reliance:[Choose exact test version]        No change selected
Note:         literal editor
              [Save position - local] [Cancel]
```

No substantive value is preselected. Saving only Wording cannot change Belief.
Saving Accurate and Disputed together is one atomic revision; reliance remains
unchanged. A test decision names its exact version even when resetting to
unknown. Notes are stored literally; new interpretation requires Send or an
explicit consultant action. Cancel/Esc retains the response draft and changes
nothing. Receipts name actor, exact formulation, changed dimensions, revision
and no consultant call. Events retain the initiating labeled action, form
identity, displayed formulation and explicit values. Selecting Inaccurate does
not invent replacement wording; offer Return to question to propose a correction.

### Waiting, failure and recovery

Retain raw input before a request. Show Input retained separately from Revision
saved. Keep inspection usable while waiting; completion announces Answer ready
without moving view, selection or focus. Return to question shows the committed
response. A failed request keeps its draft, provenance and live target and offers
Retry retained input, Inspect receipt, Copy response and Back as applicable.
An explicit consultant alternative needs no redundant second confirmation.

### Outer shell contract

```text
reason-commons --help
reason-commons --version
reason-commons new NAME --store PATH [--speaker NAME] [--accessible]
reason-commons resume PATH [--accessible] [--density compact|expanded]
reason-commons inspect CASE [--offline] [--json] [--no-color]
reason-commons history CASE [--json] [--no-color]
reason-commons export CASE --output PATH [--force]
reason-commons import BUNDLE --store PATH
```

`new` and `resume` open the persistent TUI. `--accessible` selects ordered text
without alternate-screen redrawing, using the same visible labeled actions and
literal editor; [accessibility.md](accessibility.md) defines that presentation.
`TERM=dumb` offers it. No alternate shell-session or REPL grammar defines user
work. `--no-color` preserves layout and all text/symbol statuses.
`inspect`, `history`, `export` and `import` are local utilities; CASE is a store
directory or `.reasoncase` archive. Inspection does not import implicitly.
Import creates a new store and refuses an existing destination.

Support `-h`/`--help` on every subcommand and global `--version` without opening
cases or contacting providers. Exit 0 on success, 2 for usage errors, 1 for
storage/validation/provider failures, 130 for interruption. Utility results go
to stdout; diagnostics to stderr. JSON stdout is one versioned object without
ANSI, headers or prompts. Honor `--no-color`, nonempty `NO_COLOR`, `TERM=dumb`
and non-TTY output. Never page or animate non-TTY output. `new`/`resume` require
interactive input; on non-TTY stdin give usage help pointing to offline utilities,
never silently submit piped lines. Paths with spaces work. Export refuses to
overwrite unless `--force` is supplied; the workspace Export form previews an
existing destination and requires the explicitly labeled Replace export action.

## 4. State, model invocation, and portability

### The authoritative case

The case store, rather than provider conversation memory, is authoritative.
From p0, a user-chosen writable filesystem directory is the external store:
external to the running process and the skill. Users can back it up or place it
on durable storage. A cloud backend is an adapter, not a prerequisite.

```text
forge-case/
  manifest.yaml                 schema/case identity and current revision
  revisions/000001.yaml          complete committed snapshot
  revisions/000002.yaml          next snapshot; never replaces 000001
  ...
  inputs/in001.yaml              preserved text, speaker/source, response target
  attempts/in001-01.yaml         provider request/result receipt
  sources/                      referenced attachments when actually supplied
  cursor.yaml                   view/focus/menu, draft, speaker, density
  writer.lock                   one active writer in the first release
```

The cumulative p5 schema below is not the minimal v1 schema. V1 includes only
the records listed in section 0; later fields arrive with their phases.

Every successful reasoning transaction creates a complete YAML snapshot with
schema version, case ID, revision ID, parent ID, timestamp and timezone, sources,
goal, measurements, propositions, relationships, WIP, hypotheses, stances,
interventions/options, tests/predictions/outcomes, and consequential events. A human
structured decision can therefore create a revision without a new consultant
intervention. A navigation operation does neither. A semantic response may create a
intervention with no graph change. Revision and intervention numbers are independent.
Snapshots also record applied request IDs and consultant-method/adapter
versions so recovery and later evaluation do not depend on a receipt alone.
IDs are allocated monotonically within a case and never reused. Restoring old
reasoning does not rewind the allocation ledger, applied-request ledger,
source archive, or audit history.

An intervention may carry a typed, preauthored continuation for an explicit decision,
such as showing the saved action and review prompt after Record decision on P1@1.
Stored presentation metadata includes the next cognitive operation, decision
purpose, focal object versions, decisive conditions, excerpt boundaries, and
any competing paths. Local renderers can expand, compare, or show text from
these records without inventing new reasoning. View, menu, and details changes
checkpoint the cursor only. Presentation preferences never change support.
Reasoning > Compare H1 and H2 works only when a stored comparison references both
accounts in this scope; otherwise display a local notice and a labeled option
to ask the consultant to author one. It never invents discriminating predictions.
Schema validation checks all declared presentation references and relation
types. Whether an authored view omitted an important condition requires the
semantic-quality and participant checks, not a claim of deterministic detection.

The renderer selects that phase from the recorded decision; it neither edits
the original intervention text nor invents a new consulting judgment. On resumption,
the same phase remains selected. Model views likewise use the intervention's stored
preferred-representation reference rather than asking the model what to show.

Ordinary YAML files are immutable **by application policy**: the app does not
overwrite them. Content hashes detect mismatches; they do not make owner-edited
files tamper-proof. The mutable manifest points to the last complete revision.
Snapshots plus events are exported together. The portable `.reasoncase` format
is a ZIP container with the manifest, complete revision ancestry, inputs,
receipts, referenced sources, and cursor. Credentials and provider secrets are
not part of a case. Import verifies schema, references, and hashes before use.

### Commit protocol

1. Preserve raw input, attribution, response target, and request ID before
   starting a semantic call. If that write fails, retain the editor text and do
   not start the call.
2. Send committed state, relevant source records, active question, coaching
   preference, input, and base revision to the consultant adapter. Large cases
   use an explicit context index with local read access for referenced records;
   an omitted item is not evidence that it does not exist.
3. Receive a structured proposal. Validate schema, references, object versions,
   allowed update types, and unchanged base revision. Evidence/support cannot
   be upgraded without cited input; the model cannot fabricate participant
   stances. Normalize IDs locally and validate the complete result.
4. Write and flush a complete new snapshot; atomically publish the manifest
   pointer after the snapshot is complete. Record a completed receipt keyed by
   request ID. Treat a request as applied at most once. Display "saved" only
   after this commit succeeds.
5. On restart, recover the last complete published revision. Incomplete or
   orphaned writes are not silently treated as applied. A response received
   but not committed can be retried as a commit after validation; no duplicate
   consultant call is needed just to recover a completed response.

A writer lock rejects a second editing process. Base-revision checks also
reject a stale response. A later collaboration backend would need an explicit
concurrency/merge contract; filesystem synchronization alone does not provide it.

### Example response envelope

This is a p3 shape illustration, not the v1 or complete schema. Temporary references
are resolved to stable IDs by the app. The app owns counters and timestamps.

```json
{
  "schema_version": "1",
  "delivery_profile": "p3",
  "request_id": "in005",
  "base_revision": 4,
  "intervention": {
    "kind": "question",
    "primary_prompt": "What evidence would distinguish interruption from the reverse explanation?",
    "purpose": "test_causal_direction",
    "related_objects": ["L3"],
    "rationale": "Both explanations fit the report so far; event order could change the next test.",
    "presentation": {
      "operation": "compare_causal_directions",
      "decision": "choose_the_next_observation",
      "focal_object_refs": ["L3@1"],
      "required_condition_refs": ["L3@1"],
      "scope": "partial; event order and capacity unresolved",
      "alternative_refs": ["alt1"]
    },
    "diagram": {"type": "partial_crt", "object_refs": ["N1", "N2", "N3", "N4", "L2", "L3"]},
    "options": [
      {"id": "O1", "label": "Inspect evidence", "action": {"type": "view", "target": "evidence:L3"}},
      {"id": "O2", "label": "Inspect assumptions", "action": {"type": "view", "target": "assumptions"}},
      {"id": "O3", "label": "Try a different question", "action": {"type": "consult", "intent": "reframe_current_question"}}
    ]
  },
  "proposed_updates": [
    {"operation": "record_alternative", "temporary_id": "alt1", "statement": "Priority changes may follow threatened dates", "source_refs": ["in005"], "support": "hypothesis", "origin": "participant"}
  ]
}
```

The v1 adapter uses a smaller envelope and allowed-update registry. It needs
no graph, relation, stance, or tree presentation fields. The following example
assumes G1@1 and its protected conditions are already committed:

```json
{
  "schema_version": "1",
  "delivery_profile": "p2",
  "request_id": "in003",
  "base_revision": 2,
  "intervention": {
    "kind": "question",
    "goal_ref": "G1@1",
    "purpose": "observe_preparation_result",
    "decision": "whether_the_pilot_can_start",
    "primary_prompt": "What does the rehearsal show before you start?",
    "rationale": "Naming a role does not establish understanding of the rule.",
    "required_context_refs": ["G1@1", "P1@1"],
    "options": [
      {"id": "O1", "label": "Inspect original test", "action": {"type": "view", "target": "test:P1@1"}},
      {"id": "O2", "label": "Ask for help observing", "action": {"type": "consult", "intent": "explain_observation"}}
    ]
  },
  "proposed_updates": [
    {"operation": "record_action_execution", "test_ref": "P1@1", "execution": "completed", "source_refs": ["in003"], "basis": "participant_report", "expected_state_attainment": "unknown"}
  ]
}
```

Schema/profile validation, explicit-input authority, unchanged base revision,
and durable commit still apply. The v1 update registry permits goal/note/intervention,
test/action, observation/review, and explicit goal-relevance review records.
It does not permit an adapter to bypass the boundary by placing executable
later structures inside a generic note. Ordinary prose remains literal data.

Automatically storing an interpretation as a draft or hypothesis is different
from recording a human consequential commitment. Let people correct ordinary
interpretations without approving every node. Only explicit input or a
structured human action establishes assent, reliance, or ownership. Do not
manufacture a confirmation loop after a commitment was already supplied.

## 5. Gherkin and traceability

The eleven `.feature` files below are acceptance specifications, with examples
expanding some outlines into multiple cases. Counts are in the bundle README.
They are not implemented tests. Step definitions and provider adapters remain
to be built. Deterministic scenarios should run against a fake consultant with
an observable call counter. Semantic fixtures should assert invariants and be
reviewed for professional quality; they should not assert exact wording.

Screen references below are the `SCREEN` labels in the three TUI specimens;
scenario IDs are the `@Snn` tags. A specimen illustrates selected behavior, not
all failure branches. Every scenario still needs its own fixture and release gate.

| Jobs | Feature | Scenarios | TUI specimens | Behavior |
|---|---|---|---|---|
| J01–J04 | 01 goals and guidance | S01–S06 | M01–M03; S01–S04 | Orientation, goal, one next move and direct help |
| J05–J06, J16 | 02 navigation and routing | S07–S13 | S05A–S05B; M02 | Visible local controls, explanation, return to draft |
| J07–J08, J10 | 03 model and WIP | S14–S23 | S04–S08; R01–R02 | Conditions, evidence, corrections and retained reports |
| J09, J11 | 04 group and conflict | S24–S29 | S07; S09 | Independent position fields and both legitimate needs |
| J10–J13 | 05 experiments and review | S30–S38 | M03–M07; S10–S22 | Prospective forecast, preparation, breach and follow-up |
| J14–J15 | 06 persistence and recovery | S39–S48 | M04 resume; S18 | Saved target/draft, portable case and exact retry |
| J03, J15–J16 | 07 accessibility and evaluation | S49–S53 | M01–M07; S23–S24 | Reflow, equivalent relations and deliberate submission |
| J02, J05–J06, J09, J14–J16 | 08 human interface | S54–S73 | S05A–S07; S18 | Focused menus, explicit targets and actor-bound forms |
| J03, J07, J10–J13, J16 | 09 visual reasoning | S74–S89 | S05–S05B; S09–S17 | Complete typed logic and decision-sized canvas |
| J05–J06, J16 | 02 later local views | S90–S90 | S05A–S05B | Stored model, unlinked reports and assumptions |
| J01–J03, J06–J07, J09, J11–J16 | 10 goal progress and delivery | S91–S113 | M03–M07; R01–R04 | Goal connection, execution/attainment and dependent review |
| J02–J03, J05–J07, J09, J12–J16 | 11 TUI workspace | S114–S127 | M01–M07; S01–S24; R01–R04 | Canonical interaction, async focus and complete diagrams |

## 6. Build sequence

Use the scenario tags and gates in [delivery-phases.md](delivery-phases.md).
Build p0, then p1, then p2; release v1 only after the complete loop works with
one semantic adapter and real first-time participants. A fake adapter isolates
storage and interaction behavior but cannot establish consulting quality.

Develop p3 only after v1 users show that explicit causal relationships help the
next decision. Add p4 when facilitated use needs exact structured positions;
add p5 as particular cross-tool tasks justify it. Each later release passes
its own new scenarios plus cumulative earlier regressions. A later feature
cannot become a dependency of an earlier fixture or background.

Scenario tags select requirements; they do not install step definitions, enforce
runtime capabilities, or declare features implemented. Profile-specific schemas,
action registries, and option validation enforce the runtime boundary. Keep
CI subsets and enabled capabilities aligned with the phase manifest.

Authenticated simultaneous collaboration, notifications, remote synchronization,
and automatic organizational execution remain outside these
phases. A review date is a stored intention, not a scheduled reminder.

## Design sources and evidence limits

- The supplied *TOC TUI Implementation Guide*, especially its worked gates,
  Cloud, adverse futures, prerequisites, transition steps and reflow contract.
  The new session adapts those logical distinctions to Payments and gives
  nodes, joints and opposing branches substantially more character-cell room.
- Monospace Design TUI [agent guidance](https://coreyt.github.io/monospace-design-tui/agents/),
  [standard](https://coreyt.github.io/monospace-design-tui/standard/) and
  [patterns](https://coreyt.github.io/monospace-design-tui/patterns/) inform the
  persistent workspace, focus, visible controls and optional inspection.
  Project-specific adaptations live in TUI-DESIGN.md; no full compliance claim
  or measured usability result is implied by these authored examples.
- The supplied *Reasoning with TOC Thinking Processes in Text Interfaces*
  (1 October 2026), especially sections 3–6 on typed logic and connected models,
  7–9 on interaction and purposeful wording, and 10 on separate outcome measures.
  Its six-tool examples are conceptual proposals.
- The supplied *Visual reasoning in TOC consulting*, especially questions
  1–8 (external memory and supported generation), 9–10 (scrutiny and visual
  authority), 13–21 (breadth, attention, notation, accessibility), 22–32
  (correction, dissent, understanding), and 33–46 (prediction, comparison,
  evaluation, and choosing the next move). The per-tree adaptations in section
  6a are design judgments; no universal optimal node count or guaranteed
  improvement in trust, implementation, or organizational outcomes is claimed.
- The two supplied CLI evaluations motivate contextual local decisions,
  numeric-answer routing, IDs as optional addresses, compact status, and a
  separate shell interface. Their numeric ratings are informal judgments,
  not validated usability results. The proposed interface still requires tests.
- [Command Line Interface Guidelines](https://clig.dev/) informs concise help,
  requested detail, repair suggestions, and predictable shell behavior.
- [Nielsen Norman Group usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
  informs visible actions, user control, and the balance of status and economy.
- [Cucumber Gherkin reference](https://cucumber.io/docs/gherkin/reference/)
  identifies the feature/scenario/outline conventions used in this bundle.

The GNU and TAOUP references in the supplied evaluation are useful background;
the proposed contracts here stand on their stated behavior and the accessible
primary CLI/UX guidance above. No book quotation in the inputs is asserted as
independently verified. Sources guide requirements; they do not demonstrate
that Reason Commons has achieved a 9/10 or 10/10 score.

## 6a. Visual reasoning and first-hour interaction

### Choosing the next representation

Before composing an intervention, the consultant states a public purpose: which act of
reasoning will help which decision? The adapter stores this purpose, focal
formulations, and the required premises. The renderer displays the premises;
it does not generate an inference to fill an empty arrow. The consultant choose
among a question, written distinction, local fragment, paired comparison,
timeline, or broader model. This is not a fixed progression through trees.

Ask when the premises are available and the useful missing work is a mechanism,
condition, observation, prediction, or judgment the participant can attempt.
Preserve a local fragment when reconstruction, ambiguous reference, or notation
interferes. Expand when interacting branches, rival routes, feedback, or harms
must be considered together. If breadth exceeds the terminal, use aligned
fragments and a comparison table rather than shrink labels or hide a decisive
qualification. A question can include two written premises with their relation
left open. A missing fact remains a question, not an inferred connection.

The consultant can respond to a reported difficulty by proposing a repair and
one small check of its usefulness. Hesitation, repetition, and disagreement do
not diagnose overload. First ask what is unclear, omitted, or contested. If
the premises are understood but knowledge is missing, explain with an example.
If the goal, authority, social consequence, or fatigue is the problem, address
that issue. Direct mode offers advice promptly. Neither mode makes participants
perform a discovery ritual to reach the consultant's preferred conclusion.

### Shared notation and inspectability

Give each view one visual query, such as "trace this mechanism" or "compare
these predictions". Use proposition labels with one principal meaning. Place
decisive conditions adjacent to the relation; do not consign them to a legend
or an off-screen register. Maintain predictable reading direction within a
view. Lines may join only at explicit junctions. Crossings have no implied
connection. Geometry conveys neither evidence strength, blame, importance,
organizational rank, elapsed time, nor constraint status.

A small legend explains only conventions used in the current view. In a causal
view `--?-->` means a proposed influence under stated conditions. In a necessity
view write `requires` or `needs`; never reuse the causal connector with a new
unstated meaning. `[AND]` means all listed inputs are required for that proposed
inference; completeness remains open to challenge. Independent routes are
separate and labeled; neither OR nor AND is inferred from mere convergence.
`FOCUS` marks attention, while `hypothesis`, `reported`, `disputed`, and `unknown`
mark epistemic status in words. Selection must never look like endorsement.

Node evidence and link evidence are independent. Two measured nodes do not
establish an arrow. The live view shows origin/support, consequential dissent,
and relevant scope. The object register holds exact wording/version, mechanism,
units/period/cohort, source method/date, limitations, alternatives, and decision
implication. Unknown fields remain unknown. A relation has visible Evidence and Position controls.  A source said to exist but not attached
is a participant report, not an inspected measurement.

The default model uses readable labels. Stable IDs appear in Details, history, ambiguous labels and audit/export. Versioned stance receipts
keep the exact address available. A multi-object model offers a branch list or a labeled inspect picker.
Selecting an item opens its detail locally; typing a number in Response never
selects an object. IDs remain stable across focus changes and expansions.

Partial views name their boundary: which mechanism is shown, which related
branches or alternatives are outside it, and the local action to inspect them.
Collapse is an authored summary referencing its members, not an unqualified
replacement proposition. Do not hide dissent, an AND input, a delay, or a
negative branch needed for the current judgment. Local expansion reconstructs
stored relationships only. A novel account or comparison requiring judgment
is an explicitly labeled consultant request.

Equal presentation of rivals means consistent vocabulary, scope, orientation,
and readable labels. It does not imply equal support. Show different evidence
levels beside each. Neutral labels describe policies and behavior rather than
blaming a person or making one legitimate need the villain. Record an objection
where it changes the exact proposition or support; acknowledging it in prose
while leaving a falsely certain diagram is insufficient.

### Goal and intermediate objectives

The task is to decide what must hold for the system goal, within its horizon
and protected conditions. Show the goal with its measure and scope, then the
necessary intermediate objectives relevant now. Say explicitly that achieving
one requirement does not establish the goal. An unknown necessity relation is
an assumption; a requirement supplied by one person does not become group
agreement. Keep the difference between a condition and an action visible.

For Forge, dependable October delivery may require an executable order plan
and available materials. Neither alone is sufficient. A focused question can ask
whether a dependable plan is necessary in the stated scope; a broader map is
needed when someone tries to optimize one requirement at the expense of the
other or a protected condition. Unconnected goals remain distinct proposals
until participants explain their relationship.

Inspection asks: can the goal occur without this proposed requirement? Could
all displayed requirements hold while the goal still fails? A credible instance
of the former challenges necessity; the latter exposes insufficiency of the
set without necessarily refuting a single requirement. The useful next output
is a missing condition or measurement, not merely another box. Learning can be
checked by distinguishing "necessary" from "enough" on a different objective.

### Current Reality Tree

The task is to examine what sustains recurring unwanted effects and what could
change the next intervention. Show a reported effect, the proposed mechanism,
and decisive enabling conditions. For Forge, priority changes AND high
unfinished work may interrupt jobs; interruption contributes to lateness only
under the recovery condition. Maintain Priya's alternative that threatened
dates induce changes, and the unintegrated supplier report, without inventing
links. Visually central nodes and large queues are not diagnoses of a constraint.

Use a local view to test the conjunction, a paired view for direction or rival
causes, and a time-labeled view when earlier lateness may trigger later changes.
A feedback loop needs episodes or an explicit delay. It is not circular proof,
and its layout cannot provide a growth rate or effect size. A broader tree is
justified when several routes jointly affect goal performance. State its scope
and which links are unresolved.

Inspect meaning, existence, mechanism, omitted conditions, other causes,
predicted effects, possible reversal, and tautology. These are accessible
prompts in Explain this and Help > Reasoning, not a required vocabulary lesson. Ask what would
happen for an otherwise similar job with recovery capacity available, or what
records distinguish changing priorities first from threatened dates first.
Removing one sufficient route does not imply the unwanted effect disappears;
other routes may remain. Record a prospective discriminating observation when
the evidence cannot settle the account. A participant who qualifies or rejects
a weak link has made progress even if confidence falls.

### Evaporating Cloud

The task is to examine why two legitimate needs appear to require incompatible
actions. Display the shared objective, both needs, both actions, the exact
scope/time of incompatibility, and the necessity assumptions. Give the needs
comparable treatment. `requires?` is a questioned necessity claim, not a causal
prediction or a moral judgment. Preserve whether the account is direct or
reported; Sam's report cannot count as Sales' or Production's endorsement.

For Forge, responding to urgent needs is claimed to require immediate plan
change; dependable execution is claimed to require keeping the plan unchanged.
Keep the shared objective in view while testing whether acknowledgement plus
a later reliable answer can meet responsiveness, and whether reserved slots
can protect execution. A local fragment may focus on one necessity assumption,
but it signals the other need and action. Both sides must be visible when
judging whether a proposed alternative actually meets both needs.

Ask for an instance where the need was met without the proposed action, then
what legitimate need would be lost by the new arrangement. An experiment can
resolve an assumption; some conflicts remain real resource or priority
tradeoffs requiring a named decision owner. Do not force an evaporating answer
or turn willingness to test an alternative into endorsement of the Cloud.
Check understanding by asking participants to explain the other need fairly
and distinguish questioning necessity from rejecting that need.

### Future Reality Tree

The task is to predict how a proposed change reaches desired effects while
protecting the system. Distinguish the proposed change, existing conditions,
intermediate predicted effects, desired result, and any harmful route. All new
effects are predictions until outcomes arrive. A reported starting state does
not lend observational status to the future links attached to it.

For Forge, frozen commitments plus urgent slots and daily triage may reduce
interruptions and improve delivery. Available material and adequate execution
capacity remain conditions. Display the responsiveness harm alongside delivery
when the decision is whether to run or expand the pilot. Use a local branch to
check a mechanism; expand to interacting outcomes for the intervention choice.
Do not convert removal of interruptions into a promise that all lateness ends.

Ask for the first observable intermediate change, what might stay unchanged,
and what the rival explanation predicts. Specify cohort, units, measurement,
dose, horizon, and comparability before collecting outcomes. Separate testing
a learning prediction against an already authored branch from obtaining new
evidence for the model. The saved forecast remains intact during review.
Understanding is shown by a qualified new-case prediction, not assent to the
proposed remedy. A package that succeeds may remain causally non-unique.

### Negative branch

The task is to trace a credible adverse mechanism and decide whether prevention,
detection, stopping, or an accepted tradeoff makes the change defensible. Show
the proposed change, triggering condition, adverse effect, threatened protection,
and candidate prevention or stop rule. Keep the beneficial and harmful paths
available together; a cheerful forecast with harms accessible only several
screens away is inadequate for a go/no-go decision.

For Forge, frozen commitments with insufficient urgent capacity may make urgent
work wait and miss a legitimate need. Acknowledgement and actual fulfilment are
different measures. A 95% within-24-hour acknowledgement guardrail is measurable
but does not alone prove that all urgent needs are met. Record that remaining
limitation. A prevention that can itself cause harm receives examination.

Ask what observation would reveal the mechanism early enough to act, who has
authority to stop, and whether the safeguard covers the threatened need. Do
not draw a safety valve as effective merely because it is planned. During review,
promote breaches visibly even if delivery succeeds; retain the original bound
and prevent success language from implying permission to expand. The next move
may be redesign or an explicit owned tradeoff. Check transfer by asking which
protection fails in a changed condition and what should happen next.

### Prerequisite Tree

The task is to convert a real implementation obstacle into a necessary state
and a feasible route to attain it. Show the obstacle, why it blocks the named
objective, the corresponding intermediate objective, and relevant dependency.
An obstacle is an existing reported condition; an intermediate objective is a
state that must become true. Neither is an executable task by itself.

For Forge, "no one owns urgent-request triage" blocks the pilot rule. "Every
urgent request has an accountable triage owner" is a proposed necessary state.
"Priya assigns a daily owner before the pilot starts" is a candidate action,
with authority and timing still requiring explicit input. A local pair helps
clarify obstacle versus desired state; a broader dependency view is needed
when material availability or another prerequisite also blocks the start.

Ask whether the stated objective could be reached despite this obstacle, and
whether removing it actually supplies the required state. A dependency diagram
must not imply that every prerequisite lies in a strict chronological chain:
some can be achieved in parallel, while others remain unknown. Store support
for the necessity/dependency and any unresolved ability to act. The useful next
move is resolving the blocking condition or naming an action, not completing
all possible obstacles. Check understanding with a new obstacle and a properly
scoped intermediate objective rather than a memorized task list.

### Transition Tree and action view

The task is to say what action, in which starting condition, should produce
which next state, and why. Show condition + action -> expected effect, with
owner, timing, observation, and a relevant stop/escalation rule. These are
sufficient-cause proposals for an execution step, not mere checklist order.
An action ticked complete does not establish that its expected effect occurred.

For Forge, an urgent request has arrived, a daily owner is assigned, and that
owner acknowledges receipt with a stated time for the final answer. The expected
state is timely acknowledgement without an immediate commitment to a final
date. Show supplier uncertainty if it affects the step: it may delay a final
answer but need not prevent acknowledging receipt. Unknown owners or authority
remain unknown; the consultant cannot create real-world assignments by drawing
an action node.

Use one step when selecting the immediate action; show adjacent steps or a
timeline if order, waiting, handoff, or contingency changes the inference. Ask
what would prevent the expected effect even if the action is performed, and
what to do if that occurs. During review record action fidelity separately
from outcome. A review date is a stored intention; no notification or external
execution is implied. Understanding is demonstrated by choosing the appropriate
next step in a changed starting condition and explaining its expected effect.

### First-hour usability evaluation

The following full structured-position tasks apply from p4, and the all-tool
reasoning tasks from p5. The smaller v1 tasks and gates are in
[delivery-phases.md](delivery-phases.md); v1 does not require stance menus or
all seven representations.

Use a runnable prototype with fixture state, a fake consultant, and an observable
call counter. Recruit at least five first-time participants spanning facilitation,
domain, and terminal experience, including an accessible text workflow. Start
from S02 in the full TUI specimen without a manual or command lesson. Ask them to inspect why, find evidence
for a disputed relation, record accurate representation with disputed belief,
return to the live question, enter the literal answer 5, distinguish local from
consultant options, quit, and resume. Repeat target selection from a multi-object
view and inspect an archived question without accidentally changing the response target.

Predeclare proposed release gates: at least four of five complete the core tasks
within 15 minutes without moderator commands; everyone predicts the provider
boundary correctly before selecting an action; no accidental provider call,
wrong-version stance, lost draft, or belief inferred from reliance occurs. Any
such consequential error blocks release regardless of task averages. Report raw
task completion, time, repairs, incorrect routes, and help use, with individual
results. These small-sample gates are design targets, not population estimates
or a validated rating scale. Test fixes with new participants.

Separately test reasoning quality on all seven representations: trace the relation,
state its decisive condition, challenge an unsupported claim, and predict or plan
for a new case. Score mechanism, condition, alternatives, and decision implication,
accepting legitimate corrections. Test aided use separately from unaided retrieval
or delayed transfer. Record displayed scope, supplied versus generated content,
repairs, and meaningful revisions. Compare matched fragments or views on distinct
cases with order counterbalanced where practical; do not compare four presentations
of the same case as independent learning trials.

Measure goal attainment, implementation fidelity, and guardrail results separately
from learning, confidence, and satisfaction. Reduced reference-recovery effort is
useful only if scrutiny and decision quality remain adequate. Agreement, speed,
completed trees, reply count, and an empty WIP list cannot substitute for these
outcomes. Stop adding representations when resolving the remaining detail would
not change the next decision; preserve scope, unresolved questions, and the test.

## 6b. Goal progress and connected reasoning

The supplied text-interface paper informs these contracts. Section references
below refer to that paper. Delivery tags decide when the structured behavior
is implemented; the principles guide plain-language v1 questions as well.

### Decision purpose and open questions from p2

The current question states its decision purpose beside its primary prompt and stores
the goal formulation it serves. Its rationale explains the goal connection.
A provisional decision remains provisional. Open questions and drafts survive
local inspection, pause, export, and resume. Asking whether an unresolved detail
would change the next action can justify stopping with a recorded uncertainty.
No complete tree or vocabulary lesson is required. (Paper sections 1, 4, 8–9.)

### Independent statuses from p2 through p5

Basis identifies report, observation, hypothesis, or prediction. Review identifies
proposed, supported in scope, disputed, or review needed. Model membership is
separate and arrives in p3. State attainment identifies whether an expected
state is unknown, unmet, or met according to cited evidence. Action execution
identifies not started, in progress, completed, or interrupted. Participant
representation, belief, and reliance arrive in p4 as separate dimensions.
Neither a saved claim nor a completed action establishes an observed effect.
Status labels name their objects and retain source limitations. (Sections 4–5.)

### Immediate actions and observation from p2

A test's immediate action identifies reality, unmet need, action, starting
conditions, expected effect, owner, authority, timing, observation criterion,
and contingency. Unknowns remain visible; drafting an assignment cannot grant
real authority. This compact record is sufficient for v1 within its persistent TUI; the
formal Transition Tree renderer arrives in p5. Record action completion separately from observation
of the result. A failed effect reopens the conditions and mechanism.

Preserve the original forecast, scope, denominator, comparison basis, dose,
window, safeguards, stop authority, and review date. Evaluate execution,
intermediate effects, goal performance, and harms separately. A pilot reaching
80 percent does not achieve a 90 percent goal. For Forge, acknowledgement and
fulfillment of an urgent need require separate scrutiny; participants determine
any missing fulfillment measure or bound. Never invent it. (Sections 5.4–5.6.)

### Typed goal connections from p3 and full integration from p5

From p3, selected-object Goal connections opens stored typed traceability,
and Changes opens a version/review comparison. Without a selected object, show
a local picker with readable labels. Exact-ID search is optional. Unknown
addresses and unavailable stored comparisons get a local repair; a new comparison
is explicitly labeled asks consultant. These controls appear only in delivered
profiles and never intercept Response text.

An overview locates branches; focus supports one judgment; comparison exposes
differences; revision shows changed claims and review consequences. All read
from shared versioned records. Explicit traceability types include `violates`,
`addresses`, `implements`, and `assesses`. They are not causal arrows. Causal,
necessity, conflict, temporal, and traceability meanings remain distinguishable.
Missing links are unknown, not inferred by the renderer.

The p3 goal-connection view links the goal, unwanted effect, and available
explanation/test records. P5 extends it to the Cloud candidate, predicted future,
implementation objective, prerequisite states, action, and observation. Different
objectives keep their own scope. Present observations and future predictions
are distinct records even when the wording resembles each other. Relevant WIP,
unresolved unwanted effects, and threatened protections stay visible.
(Sections 3–6.)

### Revision and review from p3

A correction receipt shows earlier wording, new wording, supplied reason,
source, unchanged observations, and known dependent formulations requiring
review. Explicit exact-version dependency references can generate local flags.
Newly suspected semantic consequences require human or consultant judgment.
A review record contains its triggering revision, target formulation, changed
premise references, question, resolution or open status, and cited decision.
Old support is labeled as applying to the old premises. It is not automatically
transferred or reversed. P4 preserves each participant's old stance; p5 extends
review across tools. Review needs surface at the next related decision, including
resume and expansion. A bounded decision may retain explicit uncertainty.
(Sections 4 and 6.)

### Requirements and implementation from p5

A Goal Tree distinguishes goal, critical success factors, and necessary
conditions; a shared condition uses one identity with cross-references.
Attainment is separate from the necessity warrant. An IO has an observable
attainment criterion. Parallel prerequisites stay parallel unless a warranted
dependency is supplied. `Prerequisites met` does not assert execution readiness:
resources, authority, or sufficient action steps may still be missing. A
Transition Tree retains unmet need, causal rationale, effect criteria, and
failure contingencies as well as action order. (Sections 5.1 and 5.5–5.6.)

### Wording and evaluation across delivered phases

Titles name a task; prompts ask for one manageable contribution; receipts name
what was saved; errors support recovery. No generic `Accept` control combines
save, endorse, rely, execute, and observe. Use context-specific prompts such as
`What else must be true?` and `Could the goal occur without this?`. Contribution
routes are stored options with a visible local or consultant consequence; the
route does not supply the contribution or infer a stance. Consequential wording
is available for correction without making every update a confirmation ritual.
Learning probes are optional when learning is an explicit goal and required in
appropriate evaluation; operational work can use external records.

At narrow widths retain full decisive qualifications. If ordered records cannot
support a judgment requiring simultaneous comparison, offer a wider read-only
export or another medium. Do not count repeated paging as an equivalent
experience without testing it. In comparative studies use distinct comparable
cases, prepared rubrics, similar prompts/evidence, counterbalanced order, and
recorded rescue views. Report access, reasoning, transfer, implementation, and
goal attainment separately. A small usability round cannot establish causal
effects of the interface on organizational results. (Sections 7–10.)

The following sections embed the canonical feature files, wireframes, and worked
session. Run `python3 reason-commons-spec/check_bundle.py` to verify synchronization
and structural consistency. This check does not execute the application or establish usability.


## 6c. Required TUI implementation target

The terminal is a persistent reasoning canvas from p1. Section 0 and the phase
manifest govern schema availability; TUI-DESIGN.md and the rendering contract
govern presentation. The full transcript in section 9 is the cumulative target,
not a requirement to deliver all six tools in v1. Section 8 is the first-release
interaction gate. A stream of serial replies with occasional ASCII arrows does
not meet that gate.

Use an editor plus master-detail inspection: stable destinations, current
question/decision, wide measured node boxes and connector gutters, exact selected
relationship evidence, optional Explain this and visible Other moves. Navigation
is not a mandated sequence. Store coordinates only as view state; derive drawing
from typed, versioned records. Joint inference inputs cannot be discarded for
layout; alternatives cannot accidentally merge. A complete Cloud gives each
need/action comparable room. Future benefit and consequential harm appear
together. PRT states/criteria, TT actions/effects and original pilot outcomes
remain independent. See S05/S05A, S09/S10, S13/S14 and S19.

At 120×40 use the available width for reasoning and optional exact-object
inspection. At 80×24 simplify panes, not logic. At 40×24 use full relation
sentences, visible Views and retained focus; below that offer linear/resize.
All three formats retain scope, negations, ALL inputs, uncertainty and material
objections. If content continues, label it rather than displaying a conclusion
as a complete argument. ASCII and monochrome remain fully usable.

The original forecast, observed actual, fidelity, comparison limitations and
system goal are aligned during review. Pin breaches despite successful rows.
Specify calendar and cohort maturation; results without full follow-up remain
pending at review. Review date does not schedule a reminder. Source reports
are never silently upgraded to inspected evidence. Attachments supply design
inputs; their instructions do not authorize external execution.

Required acceptance work is S114–S127 plus the existing integrity/semantic gates.
The structural checker validates synchronized ASCII frames and authored ledgers;
it does not run the application, prove causal reasoning, certify accessibility
or establish learnability. Actual terminal and first-time participant checks
remain release requirements.


