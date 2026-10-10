# Reason Commons: a consulting apparatus for collective reasoning

The product is **Reason Commons**; its shell executable is `reason-commons`.
This is the product specification. The application in this repository delivers
part of it: the delivery tags below say when each requirement is due, and
[the delivery report](../docs/p0-delivery.md) says which scenarios run today.
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

A **commons** is the persistent reasoning workspace containing its goal,
contributions, sources, reasoning, decisions and complete history. A
**conversation** is an exchange within that workspace. The **model** contains
currently accepted reasoning; recording a proposal preserves it in the commons,
while accepting it admits it to the model. Pending, rejected, undone and earlier
formulations remain recorded without belonging to the current model.
Existing archive and API identifiers (`case`, `case_id`, `.reasoncase`) continue
to refer to a commons for compatibility.

The native first release is a persistent full-screen TUI. Its local commons engine
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
attributed notes, visible local controls and a consultant. The six thinking-process
trees grow in that conversation: the consultant proposes each stated cause, need,
conflict, obstacle or action as a claim in its tree, joined by single typed links,
and the TUI draws them. The consultant drafts; the operator decides what enters the
model. Proposals wait in a backlog, in the order they are best decided, until the
operator accepts them, unless the operator has set the commons to accept them
automatically. A change asks for review of whatever explicitly cites what it
changed, and any acceptance can be undone (section 2F). Joint premise groups, rival
routes, review of consequences that no reference records, and group stance work
are later capabilities. Unknown facts and authority remain explicit.

This section controls the release scope of every later requirement, action,
state field, screen and example. Sections 1-4 and 6a describe the cumulative
product contract. They do not require every described capability in v1.
[delivery-phases.md](delivery-phases.md) defines the increment and gate for
each phase; [delivery-phases.json](delivery-phases.json) locks scenario and
artifact scope. Gherkin delivery tags are on scenarios, not whole features.

| Phase | Scope | Release |
|---|---|---|
| `@p0` | Durable minimal commons, atomic commits, recovery, export/import, profile validation | v1 foundation |
| `@p1` | Persistent TUI, literal editor, local views, focus/draft recovery, accessible linear alternative | v1 interaction |
| `@p2` | Goal, bounded test, immediate action, observations, original-forecast review; trees grown in conversation with LTP 1.0 import/export; proposals decided in a backlog, review flags and undo | v1 complete loop |
| `@p3` | Joint premise groups and rival routes, WIP integration, comparisons, goal connections, correction receipts and review records | Later causal release |
| `@p4` | Structured participant stances, speaker switching, reliance, scoped Cloud | Later facilitated group release |
| `@p5` | Full Goal/Future/Prerequisite/Transition views, negative branches, cross-tool reviews | Later full-tools release |

V1 ships only p0-p2. Later phases build cumulatively and preserve earlier
contracts. A development phase is not a sequence users must follow in a commons.
The consultant may discuss causes, conflicts, or obstacles in plain language
in v1 and propose what the participant states for the trees. Recording is never a
prerequisite: an empty or partial tree is normal, and no tree gates a test.

### V1 behavior and explicit exclusions

V1 records a versioned goal with scope, horizon, measure, baseline, and protected
conditions; attributed notes; interventions with decision purpose and rationale;
bounded tests with forecasts; immediate actions; and observations/reviews.
It also records tree claims (tree, role, statement, basis), single typed links
with an optional assumption, retractions, and new versions that reword a claim
while keeping its links. A link belongs to one tree and may use a statement from
another, such as a Future Reality link from the Cloud's injection. The commons has
one goal, and it is the Goal Tree's top statement: there is no second copy of it
among the tree claims. A test may name the tree claim it carries out. The
vocabulary is LTP 1.0 from the reasoncommons guide, so trees import from and
export to `.ltp.yaml` files. Imports go through the ordinary retained-input path
and wait in the backlog like any proposal; a file's Goal Tree goal is proposed as
the commons' goal, or as a new version of it. What the trees cannot hold (joint
premises, assessments) is kept as labelled notes. It stores unknowns rather than
manufacturing completeness. It distinguishes completed work, observed effects,
supported predictions, and goal attainment. Every record the consultant proposes
waits for the operator's decision (section 2F); the decisions, the acceptance
setting, review flags and undo are recorded too. Explicit references let a change
flag whatever cites it for review without a general dependency engine that
guesses at consequences.

V1 controls are Send, Explain this, Other moves, Backlog, Goal, Trees, Tests,
Actions and History, plus source and current-test inspection. Accept and Reject
act on a selected proposal or on everything one reply proposed; Undo acts on an
accepted change; Still holds closes a review flag; Actions changes whether the
commons accepts proposals automatically. The visible Views/Actions
controls provide navigation, export, retry, Help and Save and quit. They are
keyboard reachable without command syntax. Display only capabilities enabled
by the commons profile. V1 uses one declared operator; structured speaker switching,
positions and the tree-specific reasoning checks arrive in their tagged phases.

The Actions list and Help contain only operations enabled by the commons profile.
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
| J02 | We return, change views, or hand over facilitation | See the few facts and statuses that change the current question | We need not reconstruct the commons from memory | Compact status on views; consequential context beside the question; full context on request |
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
| J14 | We must stop, resume, inspect history, or transfer the commons | Preserve a portable record independent of a provider conversation | Work survives interruption and can be inherited | A fresh offline process restores the commons, cursor, draft, sources, dissent, and forecasts |
| J15 | The provider, parser, or storage fails | Understand what was retained and recover without duplicate work | We can trust the apparatus | Failure receipts distinguish retained input, pending reasoning, and committed revisions |
| J16 | We use a narrow terminal, a screen reader, multiline notes, or unfamiliar commands | Understand the interface and control what is submitted | The interaction supports our thinking rather than consuming it | Visible local actions, numeric answers, text equivalents, wrapping, and draft preservation |
| J17 | The consultant interprets what we said | Decide what enters our model, in the order the decisions depend on each other, and undo what we later doubt | Our model holds only reasoning we admitted, and we see what a change puts in question | Proposals wait with their source unless we chose automatic acceptance; the backlog orders them; a change flags what cites it; every acceptance can be undone |

There are two outcome families to evaluate. Organizational outcomes are the
group's chosen goal measures and protected conditions. Capability outcomes are
whether participants can make a similar reasoning move later with less help,
including identifying a condition or counterexample on a new commons. Reply count,
agreement with the consultant, the number of accepted proposals, and an empty WIP
list or backlog are not success measures.

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

Each rendered view begins with commons, committed revision, save status, declared
speaker, and focus in one short line (wrapping when needed). Local receipts
need not reprint it. Never use a checkmark alone to communicate durability.
The view title identifies browsing; historical views also show their as-of
revision and the live response target. Pending work has a separate label.

The persistent workspace uses compact pinned context. Show the complete goal, horizon,
protected conditions, and active test boundaries on startup/resume, whenever
those fields change, and through the visible Goal and Commons context controls. The current
question must also repeat any condition, baseline, target, or uncertainty that materially changes its answer,
even if it was displayed earlier. A saved commons with an unknown goal displays
"goal provisional" or "goal unknown" until the goal is defined.

Unresolved breaches and storage/provider failures take precedence over routine
focus in every affected view: name the breached condition and current value,
or distinguish retained input from uncommitted reasoning. Commons context also
shows full model/WIP status, attribution, response target, pending inputs,
waiting proposals and open review flags.
Actions > Display > Expanded repeats this context; Compact is the default. Both are persisted cursor
preferences, with no reasoning revision or consultant call. Display density cannot hide an active breach.

Context is physically pinned in the default TUI: commons/save/actor/view/focus
header, a short goal/safeguard band, and footer controls. Expand the task region
for complete diagrams and inspection; auxiliary panes collapse before decisive
premises. Navigation restores draft, caret, selected object, semantic scroll
anchor and live target. Incoming output cannot steal inspection focus. The
accessible ordered presentation uses recoverable scrollback and ordered snapshots.
Machine output and shell inspection omit interactive furniture. All displayed
facts come from committed state, with draft/pending changes separated. A proposal is labelled proposed wherever it appears and is never drawn as part of the model. An archived question's original goal never replaces the current one.

### C. Model membership is separate from epistemic status

Use consistent visible terms: observation, claim, cause, assumption, conflict,
change we make, obstacle, WIP, proposal, supported, disputed, and unknown.
Explain TOC terms where useful: an undesirable effect is an unwanted condition;
an injection is a change we would make. *Proposal* and *proposed* keep one
meaning: something the consultant drafted that is not yet in the model. Do not
make users learn the vocabulary first.

Each proposition has a stable ID, wording/version, source, source date or
unknown, kind, membership, and support. Membership says whether it is part of
the working model. A consultant's proposal is *proposed*: it waits in the
backlog and changes nothing in the model until it is *accepted*; it may instead
be *rejected*, and an accepted one may later be *undone* (section 2F). Accepting
admits a statement into the working model. It does not make it true, record
anyone's belief, or authorize acting on it: a statement can be in the model and
still be a hypothesis or disputed. WIP (shown as Unlinked, p3) is a different
state inside the model: accepted material not yet integrated into a coherent
relationship, not false, unimportant, or forbidden to use as evidence. Promotion
into a graph preserves the original contribution. Similar wording does not
justify a silent merge. Retired links remain in history.

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
be a successful endpoint; every commons need not produce a complete suite of trees.

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

### F. The consultant drafts; the operator decides what enters the model

The commons keeps three things apart: what the operator said, what the consultant
proposes it means, and what the operator has admitted into their model. Raw input
is retained first and stays available with its source. The consultant then drafts
candidate reasoning from it: goal changes, notes, tests, actions, observations,
reviews, tree statements, links, new wordings and withdrawals. Each proposal cites
the words it came from and may carry the consultant's confidence that it represents
them faithfully. A proposal may cite only the answer it replies to, answers the
commons has already taken in, and sources the operator supplied; an answer that became
stale before its reply was published is not part of the commons, so the consultant is
not shown it and no later reply may cite it. The operator can send it again.
Drafting is automatic; entry into the model is a decision.

The goal, the six trees and the tests are one model, not separate concerns. The
commons has one goal; it is the Goal Tree's top statement, and every change to it is
a new version of that goal. A test carries out a tree statement and serves the
goal; a link may use a statement from another tree, which stays one statement in
both. The backlog therefore holds every proposed change to the model, whatever
part it touches, and one set of rules decides them.

**Acceptance setting.** Each commons says how proposals enter the model. *Hold
proposals for review* is the default: proposals wait in the backlog while the
conversation continues. *Accept proposals automatically* delegates acceptance to
the application: a reply's proposals that are ready (below) enter the model in the
same revision that publishes the next question, recorded as accepted under the
operator's setting. Both use the same validation, sources and history. Only the
operator changes the setting, as a recorded local decision; a consultant reply
cannot, and a skill can only where its host was explicitly granted that
capability. A change applies to later replies; proposals already waiting keep
waiting. V1 records any confidence the consultant gives but neither shows it nor
lets it decide. A later setting may accept automatically above a threshold, once
recorded decisions show how well that confidence predicts the operator's own.

**Accept and reject.** A proposal is *ready* when everything it cites is in the
model. Accepting one also accepts the waiting proposals it needs, and rejecting one
also rejects the waiting proposals that need it; in both commons the operator sees
the full list before confirming. Everything one reply proposed can be accepted in
one action, so admission never becomes a confirmation ritual; individual proposals
can still be inspected, rejected or left waiting. Acceptance is atomic: one local
revision, no consultant call, recording who decided, when, and whether explicitly
or under the setting. A rejection is final for that proposal; the consultant may
propose the same idea again as a new proposal. A proposal is checked again when it
is accepted, against the model as it then stands.

**Order.** The backlog lists entries in the order they are best decided. Logical
dependence is a rule: a proposal comes after anything it cites that is still
waiting, and says what it waits for. Methodological order is advice among the
rest: a new version of the goal first, then the Goal Tree, Current Reality Tree,
Evaporating Cloud, Future Reality Tree, Prerequisite Tree and Transition Tree,
then tests, actions, observations, reviews and notes; older entries before newer.
A proposed new goal is marked to be decided first, because the rest is judged
against it, but it blocks nothing: an observation or an independently supported
cause can be accepted while the goal is still open.

**Review flags and cascades.** When an accepted change gives a record a new
version, withdraws it, or undoes it, everything in the model that explicitly cites
it and stays in the model is flagged for review: the links that join a statement
given a new version (in any tree), a test that carries it out, a test that serves a
changed goal, an action or a result planned for an earlier version of a test. A flag names the change that raised it.
It changes nothing and claims nothing is false; observations and unaffected
branches stay usable. It closes when the flagged record gets a new version or
leaves the model, or when the operator says it still holds. Each change flags only
what cites it directly, so a consequence travels one explicit step at a time: if
reviewing a flagged Cloud link leads the operator to accept a new wording of the
injection it joins, the Future Reality links that use that injection are flagged
in turn. The consultant sees open flags and may propose amendments; the operator
can also ask it about them directly. Its amendments are proposals like any other:
they wait, or are accepted automatically under that setting. A consequence the
consultant only suspects stays a proposal or a question; it never gains blocking
authority on its own.

**Withdraw.** A withdrawal is a proposal like any other. Accepting it takes the
statement out of the model together with the links that join it, which cannot be
drawn without it; records that cite it in another way are flagged. Because that
takes more than the operator named, the operator sees the links before confirming,
and under automatic acceptance a withdrawal that would take links waits in the
backlog for the operator.

**Tests.** A test can be given a new version, like a statement or the goal, until a
result for it is in the model. From then on its original forecast is fixed: a
further version is rejected, and a changed plan is a new test. A result cites the
current version of its test.

**Undo.** Every acceptance, explicit or automatic, can be undone. Undo appends a
local revision that takes the accepted records out of the model, together with
whatever cannot stand without them (the links of an undone statement), and closes
waiting proposals that cite them; records that cite them in another way are
flagged. The operator sees all of this before confirming. Later, unrelated changes
stay. History keeps the original words, the proposal, its acceptance and the undo.
An undo is final: it cannot itself be undone, and undone proposals do not return
to the backlog. Undo reverses one change; Restore reasoning (p3, S41) brings back a
whole earlier state.

**Timing and earlier cases.** Accepting, rejecting, undoing or changing the setting
while the consultant is working does not make its reply stale; the reply's
proposals are checked against the model as it stands when they arrive. Only a
newer consultant question makes a pending reply stale. Commons recorded before this
contract open unchanged: everything already in them is in the model, and their
history reads as it did.

## 3. Workspace interaction and the consultant boundary

This section defines the only human interaction model. Every ordinary workflow
uses visible labeled controls in a persistent workspace. Shell utilities are
separate and noninteractive. The accessible presentation changes layout and
reading order, not the domain actions or submission model.

### Orientation and agency

At rest, the workspace answers six questions: where am I, what are we deciding,
what deserves attention, what is uncertain, what can I do next, and what is saved?
Pin commons, saved revision, declared operator, view and focus; show the current
goal and consequential safeguard context. Give the main task most of the canvas.
A current question has a human title, decision purpose and prominent prompt.
Stable internal intervention IDs belong in audit/details, not titles, counters,
response prompts or first-use instruction.

The first screen offers a literal Response editor, Send, How this works and Open
a saved commons. Explain this and Other moves remain reachable as work develops.
No walkthrough, assent, prescribed answer or TOC vocabulary lesson gates action.

| Visible path | What it does | Boundary |
|---|---|---|
| Response > Send | Retains the exact response and asks for the next useful move | Asks consultant; one request |
| Explain this | Opens stored rationale and a worked reading of the current fragment | Local; no call |
| Other moves | Shows alternatives with their consequences before activation | Each item says local or asks consultant |
| Goal / Tests / Actions / History | Opens saved records; selecting a row opens its detail | Local; no call |
| Backlog | Lists proposals and review flags in the order they are best decided | Local; no call |
| Selected proposal > Accept / Reject | Admits it with what it needs, or rejects it with what needs it; Accept all takes everything one reply proposed | Local reasoning update; no call |
| Selected review flag > Still holds | Closes the flag and records the operator's decision | Local reasoning update; no call |
| History > Undo this change | Takes an accepted change out of the model with what cannot stand without it | Local reasoning update; final; no call |
| Actions > Accept proposals automatically / Hold proposals for review | Changes how later replies' proposals enter the model | Local; recorded; no call |
| Backlog > Ask about open reviews | Asks the consultant to draft amendments for flagged records | Asks consultant; one request |
| Reasoning / Unlinked (p3+) | Explores stored relationships or original reports | Local; no call |
| Selected object > Evidence / Changes / Details | Inspects exact wording, version, sources and history | Local; no call |
| Selected relation > Record position (p4+) | Opens independent attributed position fields | Local; saves only explicit choices |
| Selected test > Record decision (p4+) | Records willingness to run that exact bounded version | Local; never inferred belief |
| Actions > Capture report / Add relationship (p3+) | Saves literal material or a fully specified human hypothesis | Local reasoning update |
| Actions > Ask for direct advice / Another question | Requests the displayed stored intent | Asks consultant; one request |
| Actions > Export / Save and quit / Retry retained input | Operates on the selected commons or retained request | Consequence labeled; retry asks consultant only if needed |

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
it while interpreting the response against current commons state. Restore reasoning
is a separately labeled action that previews its source revision and appends a
new revision; it cannot rewind allocation or audit history. Undo reverses one
accepted change (section 2F) and is a different action.

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
saved. Keep inspection, and decisions about waiting proposals, usable while waiting; completion announces Answer ready
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
reason-commons inspect COMMONS [--offline] [--json] [--no-color]
reason-commons history COMMONS [--json] [--no-color]
reason-commons export COMMONS --output PATH [--force]
reason-commons import BUNDLE --store PATH
```

`new` and `resume` open the persistent TUI. `--accessible` selects ordered text
without alternate-screen redrawing, using the same visible labeled actions and
literal editor; [accessibility.md](accessibility.md) defines that presentation.
`TERM=dumb` offers it. No alternate shell-session or REPL grammar defines user
work. `--no-color` preserves layout and all text/symbol statuses.
`inspect`, `history`, `export` and `import` are local utilities; COMMONS is a store
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

### The authoritative commons

The commons store, rather than provider conversation memory, is authoritative.
From p0, a user-chosen writable filesystem directory is the external store:
external to the running process and the skill. Users can back it up or place it
on durable storage. A cloud backend is an adapter, not a prerequisite.

```text
forge-case/
  manifest.yaml                 schema/commons identity and current revision
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
schema version, commons ID, revision ID, parent ID, timestamp and timezone, sources,
goal, measurements, propositions, relationships, WIP, hypotheses, stances,
interventions/options, tests/predictions/outcomes, proposals and the decisions on
them, review flags, the acceptance setting, and consequential events. A human
structured decision (accepting, rejecting, undoing, closing a flag, changing the
setting) therefore creates a revision without a consultant call or a new
intervention. A navigation operation does neither. A semantic response may create a
intervention with no graph change. Revision and intervention numbers are independent.
Snapshots also record applied request IDs and consultant-method/adapter
versions so recovery and later evaluation do not depend on a receipt alone.
IDs are allocated monotonically within a commons and never reused. Restoring old
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
not part of a commons. Import verifies schema, references, and hashes before use.

### Commit protocol

1. Preserve raw input, attribution, response target, and request ID before
   starting a semantic call. If that write fails, retain the editor text and do
   not start the call.
2. Send committed state, relevant source records, active question, coaching
   preference, input, and base revision to the consultant adapter. Large cases
   use an explicit context index with local read access for referenced records;
   an omitted item is not evidence that it does not exist.
3. Receive a structured proposal. Validate schema, references, object versions,
   allowed update types, and an unchanged response target (local decisions
   recorded since the input do not make it stale). Evidence/support cannot
   be upgraded without cited input; the model cannot fabricate participant
   stances. Normalize IDs locally and validate the complete result.
4. Write and flush a complete new snapshot holding the next intervention and
   the proposed updates as proposals; under automatic acceptance the same
   snapshot records the acceptance of those that are ready. Atomically publish
   the manifest pointer after the snapshot is complete. Record a completed
   receipt keyed by request ID. Treat a request as applied at most once.
   Display "saved" only after this commit succeeds.
5. On restart, recover the last complete published revision. Incomplete or
   orphaned writes are not silently treated as applied. A response received
   but not committed can be retried as a commit after validation; no duplicate
   consultant call is needed just to recover a completed response.
6. A local decision (accept, reject, undo, still holds, the acceptance setting)
   is validated against the current revision, including the readiness of what
   it accepts, and published the same way as a complete snapshot, with no
   consultant call.

A writer lock rejects a second editing process. Response-target checks also
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

The v1 adapter uses a smaller envelope and allowed-update registry. It needs no
stance, comparison or diagram presentation fields; tree claims and links use the
same `record_<kind>` updates as every other record. The following example assumes
G1@1, its protected conditions and test P1@1 are already in the model:

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
    {"operation": "record_action", "data": {"statement": "Name the triage owner and backup", "test_ref": "P1@1", "execution": "completed", "expected_state_attainment": "unknown"}, "source_refs": ["in003"], "confidence": 0.9}
  ]
}
```

Schema/profile validation, explicit-input authority, an unchanged response
target and durable commit still apply. The v1 update registry permits goal, note,
test, action, observation, review, tree claim, link and retraction records, plus
the intervention; each update may carry a `confidence` between 0 and 1. Every
update becomes a proposal: the operator's decision, not the envelope, puts it in
the model. It does not permit an adapter to bypass the boundary by placing executable
later structures inside a generic note. Ordinary prose remains literal data.

Drafting may be automatic; entry into the model is not. A proposal enters the
model only by the operator's acceptance or under the automatic-acceptance setting
the operator chose (section 2F). Acceptance is membership, not assent: only
explicit input or a structured human action establishes assent, reliance, or
ownership. Keep acceptance cheap: everything a reply proposed can be accepted in
one action, and nothing asks again for a commitment already supplied.

## 5. Gherkin and traceability

The thirteen `.feature` files below are acceptance specifications, with examples
expanding some outlines into multiple commons. Counts are in the bundle README.
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
| J14–J15 | 06 persistence and recovery | S39–S48 | M04 resume; S18 | Saved target/draft, portable commons and exact retry |
| J03, J15–J16 | 07 accessibility and evaluation | S49–S53 | M01–M07; S23–S24 | Reflow, equivalent relations and deliberate submission |
| J02, J05–J06, J09, J14–J16 | 08 human interface | S54–S73 | S05A–S07; S18 | Focused menus, explicit targets and actor-bound forms |
| J03, J07, J10–J13, J16 | 09 visual reasoning | S74–S89 | S05–S05B; S09–S17 | Complete typed logic and decision-sized canvas |
| J05–J06, J16 | 02 later local views | S90–S90 | S05A–S05B | Stored model, unlinked reports and assumptions |
| J01–J03, J06–J07, J09, J11–J16 | 10 goal progress and delivery | S91–S113 | M03–M07; R01–R04 | Goal connection, execution/attainment and dependent review |
| J02–J03, J05–J07, J09, J12–J16 | 11 TUI workspace | S114–S127 | M01–M07; S01–S24; R01–R04 | Canonical interaction, async focus and complete diagrams |
| J03, J07, J11–J12, J14 | 12 trees in conversation | S128–S134 | none yet | Claims and single links in six trees, rewording, LTP 1.0 import/export |
| J07–J08, J14, J17 | 13 proposals and review | S135–S150 | M02–M03 | Backlog, acceptance setting, order, review flags, undo and one goal |

## 6. Build sequence

Use the scenario tags and gates in [delivery-phases.md](delivery-phases.md).
Build p0, then p1, then p2; release v1 only after the complete loop works with
one semantic adapter and real first-time participants. A fake adapter isolates
storage and interaction behavior but cannot establish consulting quality.

Develop p3 only after v1 users show that the trees' explicit relationships help
the next decision and need joint premises, rival routes or review of consequences
that no reference records. Add p4 when facilitated use needs exact structured positions;
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
for a new commons. Score mechanism, condition, alternatives, and decision implication,
accepting legitimate corrections. Test aided use separately from unaided retrieval
or delayed transfer. Record displayed scope, supplied versus generated content,
repairs, and meaningful revisions. Compare matched fragments or views on distinct
cases with order counterbalanced where practical; do not compare four presentations
of the same commons as independent learning trials.

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
unreviewed, supported in scope, disputed, or review needed. Model membership
(proposed, in the model, rejected or undone) is separate and arrives in p2;
unlinked material inside the model arrives in p3. State attainment identifies whether an expected
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

P2 already flags whatever explicitly cites a changed record (section 2F). From
p3, a correction receipt shows earlier wording, new wording, supplied reason,
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
what was saved; errors support recovery. No control combines save, endorse,
rely, execute, and observe: Accept admits a proposal into the model and does
nothing else. Use context-specific prompts such as
`What else must be true?` and `Could the goal occur without this?`. Contribution
routes are stored options with a visible local or consultant consequence; the
route does not supply the contribution or infer a stance. Consequential wording
is available for correction, and a reply's proposals are accepted together, so
admission does not become a confirmation ritual.
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

The following sections embed the canonical feature files, full-screen specimens, and accessible
presentation. Run `python3 reason-commons-spec/check_bundle.py` to verify synchronization
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

## 7. Full Gherkin acceptance specifications

### 01_goals_and_guidance.feature

```gherkin
@J01 @J02 @J03 @J04
Feature: Help a group make its next reasoning move
  The group does the consequential thinking; the consultant supplies structure,
  feedback, and a useful next question or recommendation.

  Background:
    Given a writable commons store
    And an available consultant adapter

  @S01 @p2 @v1 @semantic
  Scenario: Begin with a situation rather than a TOC questionnaire
    Given a new commons with no agreed goal
    When Sam submits "Late deliveries, changing priorities, overtime, and falling morale"
    Then the input is preserved with Sam's declared attribution
    And one prominent question asks what meaningful progress would look like and what must be protected
    And the visible context labels the goal as provisional
    And the effects are proposed as attributed notes with no invented relationships

  @S02 @p2 @v1 @semantic
  Scenario: Record a goal without inventing agreement or measures
    Given Sam proposes "At least 90% of orders on time by October 30"
    When the consultant creates the next useful response
    Then the goal it proposes records Sam as its source
    And absent baseline, scope, and protected conditions are shown as unknown
    And no other participant is recorded as agreeing
    And the next prompt addresses the most consequential missing item

  @S03 @p2 @v1 @automated
  Scenario: Show one recommended move and keep other paths available
    Given a bounded test proposal whose observation criterion is unknown
    When its current question is rendered
    Then exactly one primary prompt is visually distinguished from its decision context
    And the prompt asks the operator to supply the observation criterion
    And alternatives are available through visible "Other moves" controls
    And the foreground does not include an unsolicited TOC lesson

  @S04 @p2 @v1 @automated
  Scenario: Keep the information that changes the answer beside the question
    Given the current question concerns a pilot that may increase overtime
    And the commons protects "Overtime at most 20 hours per week"
    When the pilot workspace is rendered
    Then the consequential goal and protected condition appear beside the question
    And compact status shows save status, the focused control is framed, and Commons context gives the revision
    And an estimate is not relabeled as a measurement
    And the pilot workspace shows the relevant baseline and period

  @S05 @p3 @later @semantic
  Scenario: Change coaching style without forcing a discovery exercise
    Given the group has a working causal hypothesis
    When Sam activates Actions > Coaching > Direct advice
    And submits "Give us two concrete ways to test this"
    Then the preference change makes no consultant call
    And the semantic request produces ranked, concrete tests with tradeoffs
    And the group is not required to answer another Socratic question first

  @S06 @p2 @v1 @semantic
  Scenario: Treat an unclear or uncomfortable question as useful input
    Given a current question asks why Sales "disrupts" production
    When Priya submits "That wording blames us and does not fit what happens"
    Then the consultant preserves the correction
    And the next question uses neutral language about the scheduling mechanism
    And no record treats the correction as assent or irrational resistance
```

### 02_navigation_and_routing.feature

```gherkin
@J05 @J06 @J16
Feature: Navigate without asking the consultant to think
  Retrieval is local. Explicit structured decisions may also be local.
  Focus determines whether a key edits, filters, selects or activates a control.
  Response text is literal and reaches the consultant only through Send.

  Background:
    Given the persistent TUI workspace is active
    And commons "forge" at revision 10 with current question "Choose a test"
    And History contains the earlier questions "Define success" and "Inspect the baseline"
    And the consultant call counter is 8

  @S07 @p1 @v1 @automated
  Scenario Outline: Open a stored view using its visible control
    When the participant activates "<control>" using Tab and Enter
    Then the view "<view>" is rendered from stored state
    And the consultant call counter remains 8
    And the reasoning revision remains 10

    Examples:
      | control                          | view                           |
      | Other moves                      | alternatives for this question |
      | History                          | questions and event history    |
      | Explain this                     | authored rationale             |
      | History > Define success         | archived Define success        |
      | History > Inspect the baseline   | archived Inspect the baseline  |
      | Help                             | control help                   |
      | Actions > Consultant calls       | adapter call count             |
      | Backlog                          | proposals waiting for decision |

  @S08 @p1 @v1 @automated
  Scenario: Send a numeric answer from the literal editor
    Given Response owns focus
    When the participant types "5" then activates Send
    Then exactly one consultant request contains the literal answer "5"
    And neither the alternatives nor a historical question opens

  @S09 @p1 @v1 @automated
  Scenario: Send text resembling a shortcut without an escape command
    Given Response owns focus
    When Sam types "q" then activates Send
    Then exactly one consultant request contains the literal answer "q"
    And the session does not quit

  @S10 @p1 @v1 @automated
  Scenario: Keep a misspelled action filter local
    Given Actions filter owns focus
    When Sam types "histroy"
    Then the interface shows no match with Clear filter and Back controls
    And no consultant call or reasoning revision is created
    And the filter and current response draft are retained

  @S11 @p1 @v1 @automated
  Scenario: Keep the current question stable while browsing
    When Sam opens History > Define success and presses Esc
    Then the previous view and draft are restored
    And the live response target remains "Choose a test"
    And quoting the historical question in Response does not change that target

  @S12 @p1 @v1 @automated
  Scenario: Distinguish a stored view from another consultant move
    Given Other moves contains Inspect rationale and Ask another question
    When Sam opens Other moves
    Then Inspect rationale says "local; opens saved explanation"
    And Ask another question says "asks consultant"
    When Sam selects Inspect rationale and presses Enter
    Then no consultant request is made
    When Sam returns and activates Ask another question
    Then one request contains the stored intent and current response target

  @S13 @p1 @v1 @automated
  Scenario: Explain the question through public supporting material
    Given the current question has stored rationale and evidence references
    When Sam activates Explain this
    Then the rationale and referenced reports are displayed
    And the view makes no claim to expose a private model thought trace
    And Esc restores the originating view and draft

  @S90 @p3 @later @automated
  Scenario Outline: Open a structured reasoning view locally after the causal release
    Given the causal delivery profile and stored records for "<control>"
    When the participant activates "<control>"
    Then the view "<view>" is rendered from stored state
    And the consultant call counter remains 8
    And the reasoning revision remains 10

    Examples:
      | control                        | view                  |
      | Reasoning                      | partial working model |
      | Unlinked                       | unlinked reports      |
      | Reasoning > Assumptions         | assumptions           |
```

### 03_model_and_wip.feature

```gherkin
@J07 @J08 @J10
Feature: Earn coherence without manufacturing certainty
  Model membership and support are separate attributes.
  Disconnected contributions stay visible in WIP.

  @S14 @p3 @later @semantic
  Scenario: Keep a relevant observation outside the graph until connected
    Given a partial model of priority changes and late orders
    When Sam submits "Suppliers are often late and new hires take weeks to become productive"
    Then both contributions receive stable WIP identifiers and source references
    And the existing causal graph is not given invented arrows
    And the receipt reports "2 reports retained in Unlinked"
    And one prominent question offers a useful move on the current focus

  @S15 @p3 @later @semantic
  Scenario: Promote a WIP item through an explicit causal formulation
    Given "W1" says "Orders finish late"
    And "W2" says "Priorities change during the week"
    When Sam submits "Changing priorities contributes to late orders when unfinished work is high because active jobs are interrupted"
    Then the model contains the reported propositions and hypothesized relationships
    And the joint causes are represented with an AND group
    And W1 and W2 remain retrievable through their original source records
    And the new relationships are not labeled empirically established

  @S16 @p3 @later @automated
  Scenario: Show a diagram only when it earns its space
    Given two conditions jointly lead to one reported effect
    When a question asks whether either condition alone is enough
    Then a diagram shows the two conditions, an AND junction, and the effect
    And uncertain links are marked and explained in text
    And the workspace includes only the mechanism needed for the question
    And no decisive condition is omitted to meet a node-count target

  @S17 @p2 @v1 @automated
  Scenario: Show no diagram for a question it would not clarify
    Given the next useful move is to name an experiment owner
    When the question is rendered
    Then it asks for the owner without a decorative causal diagram

  @S18 @p3 @later @semantic
  Scenario: Preserve contradictory claims instead of resolving them silently
    Given L3 claims that interrupted jobs contribute to late completion
    When Priya submits "Priority changes may follow threatened dates rather than cause them"
    Then the alternative is stored with Priya's attribution
    And L3 can remain in the working model while disputed
    And the next question requests evidence that could distinguish the directions
    And neither participant's claim is overwritten

  @S19 @p3 @later @automated
  Scenario: Capture literally without interpretation
    Given a current question and 2 WIP items
    When Sam activates Actions > Capture report, types "Morale feels worse after the second shift" and saves locally
    Then the exact text is added as an unclassified WIP item
    And the reasoning revision advances once
    And the consultant call count does not change
    And the current question remains the response target

  @S20 @p3 @later @automated
  Scenario: Connect known objects locally when the human supplies every relation field
    Given W1 and W2 are unconnected reported observations
    When Sam selects the two reports and activates Add relationship
    And supplies input Priorities change, output Orders finish late, condition "high WIP" and basis Hypothesis
    And activates Save relationship - local
    Then a human-authored conditional hypothesis is recorded
    And the items are included in the model through that relationship
    And the original wording, attribution, and earlier revision remain available
    And no consultant call or claim of validation is made

  @S21 @p3 @later @semantic
  Scenario: Do not infer a merge from similar wording
    Given W4 says "Morale is falling"
    When another participant captures "People seem discouraged"
    Then both source records are preserved
    And a possible duplicate may be suggested on the next semantic turn
    And merging requires an explicit decision about the intended meaning

  @S22 @p3 @later @semantic
  Scenario: Challenge a constraint hypothesis at the system level
    Given a large production queue and low on-time delivery
    When Sam submits "The largest queue must be our constraint"
    Then the consultant asks what improving that queue would change in the chosen goal and horizon
    And it requests evidence about effective capacity, load, and downstream absorption when relevant
    And a queue alone is not stored as a confirmed system constraint

  @S23 @p3 @later @semantic
  Scenario: Preserve units, periods, and denominators
    Given a baseline of 32 on-time orders out of 50 orders due in September
    When Sam reports "20 completed orders this week proves we improved"
    Then the receipt retains the new report with its period
    And the consultant asks for orders due and on-time completions for a comparable cohort
    And the old baseline is not replaced with an incomparable percentage
```

### 04_group_and_conflict.feature

```gherkin
@J09 @J11
Feature: Represent a group's positions and conflicts faithfully

  @S24 @p4 @later @automated
  Scenario: Distinguish a faithful representation from belief
    Given L3 version 1 is a disputed causal hypothesis
    When Priya selects L3 version 1, opens Record position, chooses only Wording Accurate and saves
    Then her representation stance is recorded for that exact formulation
    And her belief remains disputed
    And other participants' stances remain unknown

  @S25 @p4 @later @automated
  Scenario: Reliance on a test does not establish belief or consensus
    Given pilot P1 version 1 has a prospective prediction
    When Sam selects pilot P1 version 1, opens Record decision, chooses Will run this bounded test and saves
    Then Sam's willingness to run that bounded pilot is recorded
    And no group's unanimous assent is inferred
    And disputed causal claims remain disputed

  @S26 @p4 @later @semantic
  Scenario: Attribute reported positions without claiming direct assent
    When Sam submits "Priya thinks the model is wrong"
    Then the source is Sam's report of Priya's position
    And Priya is not marked as directly endorsing a stance

  @S27 @p4 @later @automated
  Scenario: Do not carry agreement onto a substantively changed formulation
    Given Priya marked L3 version 1 as an accurate representation
    When the condition and effect of L3 are substantively revised
    Then the new formulation has a new version
    And the old stance remains attached to version 1
    And Priya's stance on the new version is unknown

  @S28 @p4 @later @semantic
  Scenario: Represent a conflict as legitimate needs and incompatible actions
    Given Sales wants responsiveness and Production wants dependable execution
    When the group explains why Sales changes the committed plan and Production freezes it
    Then a partial Cloud shows their shared objective and both needs
    And the conflicting actions are "Change the committed plan now" and "Keep the committed plan unchanged"
    And the assumptions making those actions seem necessary are inspectable
    And neither need is described as the obstacle to be defeated

  @S29 @p4 @later @semantic
  Scenario: Respect a real incompatibility
    Given two obligations require the same exclusive resource at the same time
    And no workable alternate arrangement is known
    When the group asks to resolve the conflict
    Then the consultant can describe the unresolved tradeoff and decision owner
    And it does not assert that every conflict has an evaporating solution
```

### 05_experiments_and_review.feature

```gherkin
@J10 @J11 @J12 @J13
Feature: Turn a defensible next move into learning

  @S30 @p2 @v1 @semantic
  Scenario: Test before completing every Thinking Process tree
    Given two plausible explanations would lead to the same low-cost bounded test
    When the group asks what to do next
    Then the consultant may recommend that test with the uncertainty visible
    And completing a CRT, Cloud, FRT, PRT, and Transition Tree is not a prerequisite

  @S31 @p5 @later @semantic
  Scenario: Inspect a consequential adverse effect
    Given the group proposes freezing the plan while reserving urgent capacity
    When the consultant evaluates the proposal
    Then a partial future model marks its effects as predictions
    And the most consequential credible negative branch is shown
    And the next prompt asks for a prevention or stopping condition

  @S32 @p2 @v1 @automated
  Scenario: Record a prospective pilot with enough detail to review
    Given the group has supplied a baseline and a proposed bounded change
    When Sam commits to a pilot
    Then the pilot records the following review fields:
      | field                  |
      | owner and scope        |
      | intervention and dose  |
      | baseline and cohort    |
      | exact prediction       |
      | measurement method     |
      | observation window     |
      | protected conditions   |
      | stopping conditions    |
      | alternative explanation|
      | review date            |
    And unknown fields remain visibly unknown
    And the prediction is versioned before the outcome is supplied

  @S33 @p5 @later @semantic
  Scenario: Convert an implementation obstacle into a necessary intermediate objective
    Given the pilot cannot begin because no one owns urgent-request triage
    When the group examines the obstacle
    Then the workspace identifies "Every urgent request has an accountable triage owner" as a necessary condition
    And a next action names an owner and timing if supplied
    And "Solve triage" alone is not presented as an executable plan

  @S34 @p2 @v1 @semantic
  Scenario: Show the original prediction before interpreting a result
    Given pilot P1 predicted at least 80% on-time completion
    And its original responsiveness guardrail was at least 95% acknowledged within 24 hours
    When Sam reports 40 of 50 on time and 18 of 20 timely acknowledgements
    Then the review compares 80% with the unchanged delivery prediction
    And it compares 90% with the unchanged 95% responsiveness guardrail
    And the forecast is supported on delivery while the guardrail is breached
    And the next move addresses the breach before expansion

  @S35 @p2 @v1 @semantic
  Scenario: Improvement is not proof of a unique cause
    Given a pilot improved delivery while changing both release rules and urgent-request handling
    When the result is reviewed
    Then the result can support the bounded intervention
    And the causal explanation remains non-unique
    And supplier timing and order mix are checked as relevant alternatives

  @S36 @p2 @v1 @semantic
  Scenario Outline: Classify a review according to what actually happened
    Given a pilot with an unchanged prospective prediction
    And the review evidence is "<evidence>"
    When the group submits the outcome
    Then the affected prediction is classified as "<classification>"
    And the original forecast and source reports remain available

    Examples:
      | evidence                                          | classification         |
      | planned dose, comparable measures, target reached  | supported prediction   |
      | planned dose, comparable measures, target missed   | contradicted prediction|
      | the intervention never started                    | implementation failure |
      | the outcome denominator is unknown                | inconclusive           |

  @S37 @p2 @v1 @automated
  Scenario: A review date is not a scheduled automation
    Given a pilot has a review date of October 19
    When the pilot is saved
    Then the view says "Review October 19; no reminder scheduled"
    And no calendar event, message, background job, or external action is created

  @S38 @p3 @later @semantic
  Scenario: Recheck the constraint after improvement
    Given a bounded change improves delivery without proving the previous diagnosis
    When the group decides its next step
    Then the consultant asks what now limits the goal in the remaining horizon
    And it preserves useful practices while questioning any that no longer serve the goal
```

### 06_persistence_and_recovery.feature

```gherkin
@J14 @J15
Feature: Preserve the commons across sessions and failures
  Successful reasoning transactions produce complete immutable-by-policy YAML
  revisions. Navigation and drafts use a separate resumable cursor checkpoint.

  @S39 @p0 @v1 @automated
  Scenario: Resume without reconstructing the consultation
    Given a saved commons with a current question, attributed notes, a bounded test, and an answer draft
    When the participant quits and resumes the same commons in a new process
    Then the same reasoning revision, response target, view cursor, and draft are restored
    And the goal, notes, test, and last prediction are unchanged
    And resumption makes no consultant call

  @S40 @p0 @v1 @automated
  Scenario: Save every complete reasoning update without overwriting earlier revisions
    Given committed revision 13
    When a valid semantic response is committed
    Then a complete revision 14 is available with parent 13 and source input references
    And revision 13 remains byte-for-byte unchanged
    And the intervention and the goal, note, test or tree updates it proposes appear together
    And "saved" is shown only after the local commit succeeds

  @S41 @p3 @later @automated
  Scenario: Keep inspection read-only and rollback explicit
    Given revision 14 is current and revision 3 exists
    When Sam selects revision 3 in History and opens it
    Then revision 3 is displayed as historical and read-only
    And the commons remains at revision 14
    When Sam activates Restore reasoning, reviews source revision 3 and activates Append restored reasoning
    Then a new revision 15 reproduces revision 3's reasoning state
    And it records both revision 14 as parent and revision 3 as restored source
    And revision 14 is retained

  @S42 @p0 @v1 @automated
  Scenario: Export a portable handoff independent of provider conversation memory
    Given a saved commons containing interventions, sources, attributed notes, a goal, and a bounded test
    When Sam exports a ".reasoncase" bundle and imports it into a fresh process
    Then stable identifiers and revision ancestry are preserved
    And all referenced source records and the original prediction can be inspected offline
    And no hidden provider conversation is required
    And the imported commons opens without a consultant call

  @S43 @p0 @v1 @automated
  Scenario: Recover from a provider failure without losing or duplicating input
    Given Sam's input has been stored under request "in014"
    When the consultant adapter times out
    Then the current question and committed reasoning revision remain unchanged
    And "Input retained; consultant unavailable" is displayed with a visible Retry retained input control
    When Sam retries "in014" successfully
    Then the valid response creates exactly one committed intervention and one revision
    And the failed attempt is preserved separately from reasoning revisions

  @S44 @p0 @v1 @automated
  Scenario: Reject an invalid response without applying a partial update
    Given a stored semantic input and current revision 14
    When the adapter returns an unknown goal reference or an ownership claim without cited explicit input
    Then no intervention or commons update is committed
    And the input and failure receipt remain available
    And a local recovery message explains the next available action

  @S45 @p0 @v1 @automated
  Scenario: A save failure never looks like a saved commons
    Given the commons store cannot complete a durable write
    When the participant submits an answer
    Then "not saved" is visible
    And no consultant call begins if the raw input cannot first be retained
    And the text remains in the editor or memory while the process is open
    And the participant can copy it or choose a writable export destination

  @S46 @p0 @v1 @automated
  Scenario: Detect stale work instead of silently overwriting another update
    Given an adapter request was based on revision 14
    And a reply to another input has advanced the commons to revision 15 with a new question
    When that adapter response arrives
    Then it is not applied to revision 15
    And the receipt offers a re-evaluation against the current revision
    And no last-write-wins merge is performed

  @S47 @p1 @v1 @automated
  Scenario: Keep offline navigation useful
    Given a saved commons and an unavailable consultant adapter
    When Sam opens options, rationale, history, or the bounded test
    Then every stored view works without the adapter
    And semantic work is clearly pending until an adapter is available

  @S48 @p0 @v1 @automated
  Scenario: Ordinary dated files do not imply tamper-proof evidence
    Given the store uses YAML revisions and content hashes
    When Sam opens storage help
    Then it explains that the app never overwrites committed revisions
    And it does not claim protection from an owner editing files outside the app
```

### 07_accessibility_and_evaluation.feature

```gherkin
@J03 @J15 @J16
Feature: Make the interface legible and the consultant evaluable

  @S49 @p1 @v1 @automated
  Scenario: Retain critical context on a narrow terminal
    Given the accessible ordered text presentation in a terminal 40 columns wide and 16 rows high
    When a test review is rendered
    Then compact status shows save status and names the focused control
    And the question shows its consequential goal and protected condition
    And the Commons context control exposes complete current context locally
    And lines wrap without horizontal scrolling
    And additional content is explicitly paged
    And "NEXT", uncertainty, and control labels do not depend on color

  @S50 @p3 @later @automated
  Scenario: Explain a graph through equivalent prose
    Given an AND relationship from N1 and N4 to N3
    When Sam activates Reasoning > Read as text
    Then the output says both conditions must hold in the hypothesis
    And the same identifiers, conditions, and epistemic statuses remain available

  @S51 @p1 @v1 @automated
  Scenario: Preserve a multiline draft across navigation
    Given Sam is composing a multiline answer with an embedded command-looking line
    When Sam opens history and then returns to the editor
    Then the exact draft is retained
    And its embedded line has not been executed as a command
    And submission invokes the consultant only once

  @S52 @p2 @v1 @semantic
  Scenario Outline: Evaluate realistic semantic input by invariants rather than exact prose
    Given a documented commons fixture and a live question
    When the participant submits "<input>"
    Then all contributed information is accounted for in the receipt
    And no unsupported causal certainty, identity verification, or group assent is invented
    And exactly one next move or a justified stopping point is prominent
    And any proposed update retains source references

    Examples:
      | input                                             |
      | I don't know                                      |
      | We cannot possibly do that                        |
      | Here are twelve more problems                     |
      | Your question is wrong                            |
      | Sales is lazy and Production never listens         |
      | Five possible causes, two observations, one demand |

  @S53 @p3 @later @automated
  Scenario: Measure useful progress without rewarding agreement
    Given a group corrects two causal links and completes a pilot review
    When the commons progress view is opened
    Then it reports the corrections, evidence obtained, decisions, and reviewed predictions
    And it does not score agreement, reply count, or WIP depletion as success
    And learning measures require an actual reasoning task or later unaided performance
```

### 08_human_interface.feature

```gherkin
@J02 @J05 @J06 @J09 @J14 @J15 @J16
Feature: Make rigorous local work discoverable through workspace controls
  All human workflows use visible controls and exact stored targets.
  Menus use selection and activation; editors and filters keep text literal.
  No alternate interactive command grammar can satisfy these scenarios.

  @S54 @p1 @v1 @automated
  Scenario Outline: Send numeric answers without selecting a menu item
    Given Response owns focus on a current question
    When Sam types "<answer>" then activates Send
    Then exactly one consultant request preserves the literal answer "<answer>"
    And no historical question or alternatives view opens

    Examples:
      | answer |
      | 1      |
      | 5      |
      | 17     |

  @S55 @p1 @v1 @automated
  Scenario: Activate a selected local alternative from its stored mapping
    Given Other moves is focused for "Choose a test"
    And its selected Inspect evidence item binds to this question's saved sources
    When Sam presses Enter
    Then stored evidence is shown locally
    And the live question, revision and consultant call count are unchanged

  @S56 @p1 @v1 @automated
  Scenario: Request a labeled consultant alternative once
    Given Other moves shows Ask another question labeled "asks consultant"
    When Sam selects that item with arrows and presses Enter
    Then one consultant request contains the stored intent and response target
    And there is no second confirmation for the same explicit request

  @S57 @p1 @v1 @automated
  Scenario: Keep an unmatched menu filter local
    Given Other moves filter owns focus and none of its labels contains "5"
    When Sam types "5" and presses Enter
    Then no item is activated and No matches appears with Clear filter and Back
    And no consultant request, commons update or revision is created
    And the response draft is retained

  @S58 @p1 @v1 @automated
  Scenario: Leave alternatives and send a literal numeric answer
    Given Other moves is open for "Choose a test"
    When Sam presses Esc, focuses Response, types "5" and activates Send
    Then exactly one semantic request contains "5"
    And it answers "Choose a test" without recording a menu decision

  @S59 @p4 @later @automated
  Scenario: Record an exact position using independent visible fields
    Given Priya is the declared speaker and L3 version 1 is selected
    When Priya activates Record position
    Then the exact formulation, conditions, actor and independent fields are shown
    And no substantive value is preselected or recorded
    When Priya selects Wording Accurate and Belief Disputed then activates Save position
    Then one atomic revision records both values on L3 version 1
    And reliance, other actors and the live question are unchanged
    And the receipt says "no consultant call"

  @S60 @p4 @later @automated
  Scenario: A wording objection is distinct from rejecting causal truth
    Given L3 version 1 is selected and Sam's belief is unknown
    When Sam opens Record position, selects only Wording Inaccurate and saves
    Then only representation inaccurate is recorded
    And Return to question offers a literal response for replacement wording
    And the interface does not invent wording or change belief

  @S61 @p4 @later @automated
  Scenario: Cancel a position form without changing reasoning
    Given a position form and a retained response draft
    When Sam activates Cancel or presses Esc
    Then the prior view and exact draft are restored
    And no stance, revision or consultant call is created

  @S62 @p4 @later @automated
  Scenario: Ask for an explicit target from a multi-object view
    Given the reasoning view contains several links and none is selected
    When Sam activates Record position from Actions
    Then a local target picker shows readable relationship labels and scope
    And no link is selected from creation order or semantic similarity
    And no stance or consultant call occurs before explicit selection

  @S63 @p1 @v1 @automated
  Scenario: Reject a stale menu before applying a decision
    Given Other moves is bound to "Choose a test" at revision 10
    And the commons advances to revision 11 with a different current question
    When Sam activates the old selected item
    Then the old choice is not dispatched against either question
    And current choices are redisplayed with a stale-menu notice
    And selecting again is required before dispatch

  @S64 @p4 @later @automated
  Scenario: Invalidate an actor-bound position form on speaker change
    Given Sam has an open position form
    When the operator activates Actions > Change speaker > Priya
    Then the form is invalidated and redisplayed for Priya with no substantive preselection
    And no Sam decision or draft is attributed to Priya

  @S65 @p3 @later @automated
  Scenario: Object evidence remains local and exact
    Given an object detail view selects L3 version 1
    When Sam activates Evidence
    Then evidence for L3 version 1 is rendered from stored records
    And Details identifies the exact same version and source references
    And neither action creates a call or reasoning revision

  @S66 @p4 @later @automated
  Scenario: Keep a historical target distinct from the live one
    Given Sam is inspecting L3 version 1 and version 2 is current
    When Sam activates Record position
    Then the form labels version 1 as a historical formulation
    And a selected stance attaches only to version 1
    And Response still answers the current question

  @S67 @p1 @v1 @automated
  Scenario: Keep substantive prose literal even when it resembles an action
    Given Response owns focus
    When Sam types "I disagree because overtime worsens" then activates Send
    Then one semantic request preserves the entire statement
    And no local parser infers representation, belief or reliance

  @S68 @p1 @v1 @automated
  Scenario: Compress routine context and repeat consequential changes
    Given Compact display and an unchanged goal and protections
    When Sam opens Explain this and returns to the current question
    Then the pinned header shows commons, save status and speaker, and the focused control is framed
    And complete unchanged context is not duplicated inside each view
    And the goal and consequential safeguard band remain pinned
    When the goal changes or Sam activates Goal or Commons context
    Then complete goal, horizon, protections, test boundaries, response target and revision appear
    And requesting context makes no consultant call

  @S69 @p1 @v1 @automated
  Scenario: Keep a consequential breach visible while browsing
    Given urgent acknowledgement is 90 percent against a 95 percent guardrail
    When Sam opens History, test sources or Other moves in Compact display
    Then the unresolved breach and both values remain visible
    And a delivery success marker does not obscure the breach

  @S70 @p1 @v1 @automated
  Scenario: Revalidate a restored menu before activation
    Given a checkpoint contains Other moves, focus, display preference, operator and draft
    When a fresh process resumes the commons
    Then it restores and validates the menu bindings
    And it shows complete startup context and labeled choices before accepting activation
    And no reasoning revision or consultant call occurs

  @S71 @p4 @later @automated
  Scenario: Reveal precision without changing the domain model
    Given a readable reasoning view with IDs omitted by default
    When Sam activates Details
    Then exact IDs, versions, sources and view-scoped action IDs appear
    And propositions, support, selection and response target are unchanged
    And Search and Help use stored context without a provider call

  @S72 @p1 @v1 @automated
  Scenario Outline: Keep offline shell utilities free of interactive furniture
    Given a saved valid commons and unavailable provider
    When the shell command "<command>" is invoked
    Then it exits 0 without a provider call
    And stdout contains only "<output>"
    And diagnostics if any go to stderr

    Examples:
      | command                                       | output                    |
      | reason-commons --help                          | requested help            |
      | reason-commons --version                       | version                   |
      | reason-commons inspect case.reasoncase --json   | one versioned JSON object |
      | reason-commons history case.reasoncase --json   | one versioned JSON object |

  @S73 @p1 @v1 @usability
  Scenario: Evaluate first-hour use through visible controls
    Given five first-time participants and a fake-consultant fixture
    When they attempt the documented first-hour tasks without a manual
    Then individual completion, time, repair, help and routing errors are recorded
    And at least four complete core tasks within 15 minutes without moderator instructions
    And all predict the local or consultant consequence before selecting an action
    And any accidental call, wrong test version or lost draft fails the proposed release gate
    And no numerical usability rating is inferred from these results
```

### 09_visual_reasoning.feature

```gherkin
@J03 @J07 @J10 @J11 @J12 @J13 @J16
Feature: Support the next reasoning operation across every Thinking Process
  Readability and visual fluency do not establish truth or understanding.

  @S74 @p3 @later @semantic
  Scenario: Preserve premises while leaving the inference to participants
    Given two agreed premises and an unarticulated mechanism
    When the consultant composes a question with visible premises to reason from
    Then the needed premises are visible and the mechanism is asked for
    And the renderer does not invent an arrow to fill the gap
    And the workspace identifies the decision the reasoning serves

  @S75 @p5 @later @automated
  Scenario: Expand scope when the current question needs interacting branches
    Given a proposed change may improve delivery and harm responsiveness
    When the current question is whether to run the pilot
    Then both relevant paths and decisive conditions are available together
    And a node-count heuristic does not remove a protection or alternative
    And a narrow terminal uses an aligned comparison or ordered text

  @S76 @p3 @later @automated
  Scenario: Distinguish attention from support and node evidence from link evidence
    Given two measured propositions joined by a hypothetical causal relation
    When that relation is focused in the model
    Then selection indicates only attention
    And the relation remains explicitly hypothetical despite measured endpoints
    And its evidence and dissent are independently inspectable

  @S77 @p3 @later @automated
  Scenario: Preserve location and uncertainty when collapsing a partial model
    Given a branch has a decisive AND condition and participant dissent
    When the renderer produces a partial view
    Then the view labels its boundary and local expansion route
    And the decisive condition and dissent remain visible if needed for the question
    And a summary retains references to the original claims
    And expanding stored branches makes no consultant call

  @S78 @p5 @later @automated
  Scenario: Test necessity without implying sufficiency in a goal map
    Given the goal requires a dependable plan and available materials
    When the question examines the plan requirement
    Then the relation says "requires" rather than using a causal connector
    And it asks whether the goal can occur without this condition in the stated scope
    And the view states that this requirement alone does not establish the goal

  @S79 @p3 @later @semantic
  Scenario: Inspect a CRT conjunction with a meaningful counterexample
    Given priority changes and high unfinished work jointly predict interruptions
    And the lateness link requires inability to recover before promised dates
    When the participant challenges the interruption-to-lateness claim
    Then the recovery condition appears beside that relation
    And a test considers whether all stated conditions hold
    And removing one route does not imply all lateness disappears

  @S80 @p3 @later @automated
  Scenario: Separate feedback episodes from circular justification
    Given earlier lateness may trigger later requests and further interruptions
    When the feedback view is shown
    Then successive episodes or relevant delays are labeled
    And layout does not imply known duration, strength, or proof
    And a static tree is not presented as a quantitative simulation

  @S81 @p4 @later @semantic
  Scenario: Preserve legitimate needs while questioning Cloud assumptions
    Given Sam reports Sales and Production needs and incompatible actions
    When a Cloud asks whether responsiveness requires immediate plan change
    Then the shared objective and both needs remain accessible with equal visual treatment
    And the arrow says "requires?" with scope and time of incompatibility
    And reported positions are not upgraded to direct endorsement
    And questioning necessity does not mean rejecting the need

  @S82 @p5 @later @semantic
  Scenario: Treat FRT branches as conditional prospective predictions
    Given a proposal freezes commitments and reserves urgent slots
    When the future view predicts fewer interruptions and better delivery
    Then predicted effects are distinguished from reported starting conditions
    And available material and recovery capacity remain visible where decisive
    And a new-case prediction includes alternatives and measurement scope
    And no original forecast is rewritten when results arrive

  @S83 @p5 @later @semantic
  Scenario: Test a negative branch and the adequacy of its safeguard
    Given urgent capacity may be insufficient for actual urgent needs
    When the proposed safeguard measures acknowledgement within 24 hours
    Then the view distinguishes acknowledgement from fulfilment of the need
    And it names the triggering condition, threatened protection, and stop owner if known
    And the prevention remains a proposal until its effect is evidenced

  @S84 @p5 @later @semantic
  Scenario: Convert a PRT obstacle into a state before naming the action
    Given no one owns urgent-request triage and this blocks the pilot
    When a prerequisite view is composed
    Then the obstacle and necessary state are shown distinctly
    And "Every urgent request has an accountable triage owner" is not itself marked executable
    And owner, authority, and timing remain unknown until explicitly supplied
    And independent prerequisites are not forced into a serial chain

  @S85 @p5 @later @semantic
  Scenario: Explain a Transition Tree action through condition and expected effect
    Given an urgent request has arrived and a daily triage owner is assigned
    When the action is to acknowledge receipt and state when a final answer will arrive
    Then the starting conditions, action, and expected effect are visible
    And supplier uncertainty need not imply inability to acknowledge receipt
    And completed action fidelity is recorded separately from timely acknowledgement
    And the step identifies a contingency if the expected effect does not occur

  @S86 @p3 @later @automated
  Scenario: Compare rival accounts without making geometry an evidence score
    Given scheduling and supplier accounts can both lead to lateness
    When the stored comparison view is opened
    Then both use aligned outcome wording, scope, and readable labels
    And actual evidence differences are explicit beside each account
    And prospective discriminating observations are inspectable
    And equal layout implies neither equal support nor mutual exclusivity

  @S87 @p5 @later @automated
  Scenario Outline: Preserve each representation's logic in accessible text
    Given a stored "<representation>" view with consequential uncertainty
    When Sam selects its text equivalent on a 40-column terminal
    Then the output preserves "<relation>" plus scope, conditions, and dissent
    And the same exact formulations remain accessible through details
    And reading and paging make no consultant call

    Examples:
      | representation | relation                                    |
      | goal map       | necessity without individual sufficiency    |
      | CRT            | joint causes and recovery condition         |
      | Cloud          | needs, actions, and necessity assumptions   |
      | FRT            | intervention and predicted consequences     |
      | negative branch| trigger, harm, prevention, and stop rule     |
      | PRT            | obstacle and required intermediate state    |
      | Transition Tree| condition, action, and expected effect      |

  @S88 @p5 @later @usability
  Scenario: Measure understanding separately from recognition and agreement
    Given a participant fluently repeats a displayed model
    When its learning effect is evaluated
    Then a task asks for a mechanism, condition, rival prediction, or changed-case action
    And aided performance is distinguished from unaided or delayed transfer
    And a defensible correction can score higher than repeating the consultant
    And confidence, satisfaction, implementation, and goal outcomes are recorded separately

  @S89 @p3 @later @semantic
  Scenario: Change support or stop when more drawing would not help the decision
    Given repeated premise recovery suggests a possible reference problem
    When the consultant shows the needed fragment and checks the next operation
    Then the benefit is assessed from the participant's actual reasoning
    And hesitation alone is not recorded as overload
    And a failed repair can lead to explaining, seeking facts, pausing, or addressing a concern
    And unresolved detail is retained when it would not change the next decision
```

### 10_goal_progress_and_delivery.feature

```gherkin
@J01 @J02 @J03 @J06 @J07 @J09 @J11 @J12 @J13 @J14 @J15 @J16
Feature: Connect reasoning to goal progress within the delivered scope
  The selected delivery profile limits controls, fixtures, and adapter updates.
  Later models remain specified without becoming requirements for v1.

  @S91 @p5 @later @automated
  Scenario: Preserve every delivered reasoning type in a portable handoff
    Given a full-tools commons with traceability, reviews, stances, and all six models
    When the operator exports and imports the commons offline
    Then exact versions and every typed relationship remain inspectable
    And review needs, open questions, observation criteria, and cursor are retained
    And no provider conversation is required

  @S92 @p3 @later @automated
  Scenario: Keep structured causal navigation useful offline
    Given a causal-profile commons and an unavailable consultant
    When the operator opens the model, WIP, assumptions, or stored comparison
    Then each supported view is reconstructed from stored records
    And no inference or discriminating prediction is invented
    And no consultant call or reasoning revision is created

  @S93 @p2 @v1 @automated
  Scenario: Show the decision and goal served by the live question
    Given a stored intervention with purpose, decision, and goal version G1 version 1
    When the current question is rendered
    Then the decision purpose is readable beside its one primary prompt
    And the rationale links the task to that exact goal formulation
    And a provisional goal remains labeled provisional

  @S94 @p2 @v1 @automated
  Scenario: Leave a question open and return without reconstructing it
    Given a live question and an answer draft
    When the operator opens history and returns with Esc
    Then the open question, response target, and exact draft are restored
    And inspection creates no reasoning revision or consultant call

  @S95 @p2 @v1 @automated
  Scenario: Revisit test relevance when its referenced goal changes
    Given test P1 version 1 explicitly serves goal G1 version 1
    When goal G1 receives a substantively different version 2
    Then P1 retains its original prediction and goal reference
    And its relevance to the current goal is marked review needed
    And the next test decision shows that review need
    And neither the old result nor the participants' positions are rewritten

  @S96 @p3 @later @automated
  Scenario: Inspect a typed goal connection without inventing a mechanism
    Given a reported unwanted effect linked to a goal criterion by "violates"
    And its proposed causal explanation remains incomplete
    When the stored goal-connection view is opened
    Then "violates" is presented as traceability rather than a causal arrow
    And missing connections and unresolved effects are named
    And a new connection requiring judgment is a labeled consultant option
    And browsing makes no consultant call

  @S97 @p5 @later @automated
  Scenario: Trace a change through distinct reasoning and implementation roles
    Given stored links from a goal through a CRT, Cloud, FRT, PRT, and action
    When the goal-connection view is opened
    Then each link names its causal, necessity, conflict, or traceability meaning
    And operating, conflict, and implementation objectives remain distinguishable
    And a present observation and future prediction remain separate records
    And unresolved unwanted effects and safeguards remain visible

  @S98 @p3 @later @automated
  Scenario: A revised premise requests review of its known dependent reasoning
    Given L2's reviewed formulation references premise N1 version 1
    When N1 receives a substantively revised version 2
    Then the change view shows old wording, new wording, source, and reason
    And L2 retains its original wording with a review-needed record
    And prior support is shown as applying to the older premise
    And support or rejection does not propagate automatically
    And unrelated semantic consequences are not claimed to be discovered

  @S99 @p4 @later @automated
  Scenario: Resolve a review without transferring another participant's belief
    Given a revised relationship and Priya's stance on its earlier formulation
    When Sam explicitly records a bounded decision under the remaining uncertainty
    Then Sam's decision cites the current formulation and unresolved review
    And Priya's earlier stance stays attached to its original version
    And Priya's current belief is unknown until she supplies it

  @S100 @p5 @later @semantic
  Scenario: A same-setup counterexample changes the questions across tools
    Given a CRT explanation that every sequence insertion adds setup time
    And the Cloud, FRT, and PRT contain explicitly linked dependent proposals
    When a participant supplies a credible same-setup counterexample
    Then the proposed revision qualifies the relevant CRT relationship
    And the Cloud's unchanged-sequence assumption is requested for review
    And the admission rule and setup-information requirement are requested for review
    And the late-order observation is not erased
    And no operational improvement is inferred from the model correction

  @S101 @p2 @v1 @automated
  Scenario: Complete an action without claiming its expected effect occurred
    Given a test action with an expected intermediate state and observation criterion
    When the operator explicitly records that the action was completed
    Then execution is completed and expected-effect attainment remains unknown
    And the receipt says "Action completed; result awaiting observation"
    And neither the prediction nor the system goal is marked achieved

  @S102 @p2 @v1 @semantic
  Scenario: Turn a recommendation into an immediate action with an observation
    Given a proposed bounded change and unknown decision authority
    When the operator asks what to do next
    Then the recommendation identifies starting conditions, need, action, and expected effect
    And owner, authority, timing, observation criterion, and contingency are explicit or unknown
    And it asks for the most consequential missing item
    And a drawn or saved action does not create a real-world assignment

  @S103 @p5 @later @automated
  Scenario: Keep attained prerequisites distinct from executable readiness
    Given two independent intermediate objectives with attainment criteria
    And both are necessary before a supervised pilot
    When both states have cited observations satisfying their criteria
    Then the pilot is labeled "prerequisites met"
    And the objectives remain parallel rather than ordered by entry time
    And missing resources, authority, or sufficient action steps remain unknown
    And the pilot is not labeled ready solely from its dependency graph

  @S104 @p2 @v1 @semantic
  Scenario: Distinguish a supported pilot target from achievement of the goal
    Given the goal is 90 percent on-time delivery
    And a bounded pilot prospectively predicts 80 percent
    When comparable results show 40 of 50 orders on time
    Then the pilot target is supported and the 90 percent goal remains unmet
    And the review shows protected conditions and implementation fidelity separately
    And a next decision addresses remaining goal progress and relevant uncertainty

  @S105 @p2 @v1 @semantic
  Scenario: Check whether the measured safeguard covers the protected need
    Given urgent responsiveness matters and only acknowledgement is measured
    When the operator asks whether timely acknowledgements establish fulfillment
    Then acknowledgement and fulfillment are distinguished
    And a fulfillment measure, acceptable bound, method, and authority are requested as needed
    And missing values remain unknown rather than receiving invented defaults
    And no breach is hidden by delivery success

  @S106 @p5 @later @automated
  Scenario: Share a requirement without confusing necessity with attainment
    Given a necessary condition supports two critical success factors
    When the goal overview and focused requirement are opened
    Then both appearances reference the same versioned condition
    And the critical success factors and supporting requirements are distinguished
    And current attainment is separate from its necessity warrant
    And meeting the requirement does not establish sufficiency for the goal

  @S107 @p1 @v1 @automated
  Scenario Outline: Refuse a restored out-of-profile action locally
    Given the v1 delivery profile and a retained response draft
    And a stale cursor or action reference requests "<action>"
    When the workspace revalidates that action reference
    Then a local notice says the action belongs to a later delivery profile
    And Help, navigation and Actions omit it as an available operation
    And no consultant call, revision or draft loss occurs

    Examples:
      | action              |
      | Explore causal model|
      | Record position     |
      | Record test reliance|
      | Restore reasoning   |

  @S108 @p0 @v1 @automated
  Scenario: Reject an adapter update outside the delivered schema
    Given the v1 schema allows only goal, note, intervention, test, action, observation, bounded review, and typed tree claim, link and retraction records, and the operator's decisions about them
    When an adapter proposal includes an untyped relationship graph or structured stance update
    Then the entire proposal is rejected before commit
    And the raw input and failure receipt remain available
    And later fields are not silently stored or partially applied

  @S109 @p5 @later @usability
  Scenario: Change medium when narrow output cannot support the comparison
    Given a decision requires simultaneous review of interacting future branches
    When ordered 40-column records do not let a participant make the comparison
    Then a wider read-only export or another medium is offered
    And decisive qualifications are not shortened away
    And the failed narrow comparison and rescue are recorded in evaluation

  @S110 @p1 @v1 @automated
  Scenario: Do not advertise an out-of-profile option from an adapter
    Given a v1 semantic response contains an option opening a Cloud view
    When the response is validated
    Then the proposal is rejected with a local unsupported-action receipt
    And the input, live response target, and prior revision remain intact
    And no menu exposes the unavailable option

  @S111 @p2 @v1 @usability
  Scenario: Evaluate the complete goal action review loop without a tree lesson
    Given first-time participants and a v1 fixture with a fake consultant
    When they define success, inspect the purpose, record a test, resume, and review results
    Then they identify the next action, authority, observation, and stopping condition
    And they distinguish action execution, intermediate effect, pilot result, and goal attainment
    And completion, reference repairs, missed conditions, and reasoning are reported individually
    And no TOC vocabulary lesson or complete tree is required

  @S112 @p5 @later @usability
  Scenario: Evaluate design hypotheses without confusing navigation with improvement
    Given predeclared rubrics and distinct comparable cases
    When joint-premise, goal-connection, and revision-review displays are compared
    Then prompts and evidence access are held comparable for each design claim
    And order, experience, rescue views, and consequential failures are recorded
    And defensible alternative answers are accepted
    And access, reasoning, learning, implementation, and goal results are reported separately

  @S113 @p1 @v1 @automated
  Scenario: Cancel an options menu and retain the question and draft
    Given a displayed options menu and an answer draft
    When the operator activates Cancel or presses Esc
    Then the prior view, open question, and exact draft are restored
    And no revision or consultant call is created
```

### 11_tui_workspace.feature

```gherkin
@J02 @J03 @J05 @J06 @J07 @J09 @J12 @J13 @J14 @J15 @J16
Feature: Work in a persistent terminal workspace from the first usable release
  These are default TUI requirements, required in both standard and accessible presentations.
  Screen specimens specify visible behavior; a runtime and participant protocol
  are required to exercise them. Structural document checks cannot pass them.

  @S114 @p1 @v1 @automated
  Scenario: Launch the persistent workspace by default
    Given interactive terminal input and output at 120 columns by 40 rows
    When the operator launches a new commons without a presentation flag
    Then the full-screen workspace shows the question, response editor, destinations and footer
    And save status, declared operator and focused control remain visible
    And no tour or command syntax is required to answer or leave

  @S115 @p1 @v1 @automated
  Scenario: Treat all printable response text literally and submit deliberately
    Given the response editor is focused on current question "Choose a test"
    When the operator types or pastes "5 ? q / :options" and presses Enter
    Then those characters and the newline are retained in the draft
    And no navigation, quit, stance or consultant request occurs
    When the operator Tabs to Send and presses Enter
    Then exactly one request preserves the full literal draft for "Choose a test"

  @S116 @p1 @v1 @automated
  Scenario: Restore the question and exact draft after optional inspection
    Given a partially edited response with caret position and current question "Choose a test"
    When the operator opens Explain this and a stored source then returns with Esc
    Then the originating view, selection, semantic scroll anchor and draft caret are restored
    And the live response target remains "Choose a test"
    And no commons revision or consultant call is created

  @S117 @p1 @v1 @automated
  Scenario: Keep the first-release workspace usable at minimum terminal size
    Given a v1 goal and test with a material safeguard at 120 columns by 40 rows
    When the terminal resizes to 80 columns by 24 rows and back
    Then the question, safeguard, response and footer remain reachable and readable
    And hidden auxiliary panes have a visible Views destination
    And the draft, target, focus and selected exact record survive without restart

  @S118 @p1 @v1 @automated
  Scenario: Complete a consultant response without stealing inspection focus
    Given a durably retained submission and pending consultant request
    And the operator has selected a source in History
    When a valid next response completes
    Then an Answer ready notice is visible without changing the selected source or focus
    And returning to Next presents the committed next question
    And no second request or duplicate commit occurs

  @S119 @p1 @v1 @automated
  Scenario: Expose every required action without recalled commands
    Given the default TUI and focused response editor
    When the operator reaches Actions or Help using Tab and Enter
    Then the displayed controls identify valid actions and local or consultant consequences
    And stored explanation, sources, history, export and Save and quit have control paths
    And Help for controls is distinct from Explain this for reasoning

  @S120 @p1 @v1 @automated
  Scenario: Recover a failed request while retaining the workspace
    Given a retained response draft and provider failure after input retention
    When the operator opens the failure receipt and retries the retained input
    Then the receipt distinguishes input retained from uncommitted reasoning
    And retry uses the same request identity and applies at most once
    And view state, draft provenance and the correct live target remain recoverable

  @S121 @p2 @v1 @automated
  Scenario: Compare the original pilot forecast with outcomes inside the workspace
    Given an original pilot delivery forecast of 80 percent and acknowledgement bound of 95 percent
    And reported delivery is 80 percent and acknowledgement is 90 percent
    When the review screen is rendered
    Then original forecast and actual result are aligned by measure with scope and denominators
    And the acknowledgement breach remains visible despite delivery success
    And action execution, observed effects and the 90 percent system goal are distinct

  @S122 @p2 @v1 @semantic
  Scenario: Keep immature cohort outcomes pending at a review date
    Given a rolling October 1 through 30 cohort with a three-business-day outcome window
    When the operator reviews it on October 30 with final outcomes still immature
    Then the review retains the original forecast and labels those outcomes pending
    And it requests complete follow-up before claiming goal attainment
    And missing observations are not treated as failures or successes

  @S123 @p3 @later @automated
  Scenario: Render a joint causal inference with complete readable boundaries
    Given L3 has three joint premises including net unrecovered recheck time exceeding slack before release cutoff
    When the causal fragment is rendered
    Then all three premises are enclosed or joined by one explicit ALL operator
    And exactly one labeled hypothesis output terminates at its conclusion
    And independent alternative routes do not become extra members of that ALL

  @S124 @p3 @later @automated
  Scenario: Inspect one exact relation without losing the broader map
    Given a stored branch index and causal map at 120 columns by 40 rows
    When the operator selects L3 version 1
    Then the inspector shows its complete scope, inputs, output, warrant, sources and objections
    And occurrence evidence for nodes is not represented as proof of L3
    And selection is distinct from focus, support and endorsement

  @S125 @p3 @later @automated
  Scenario: Replace a narrow drawing with complete relation sentences
    Given L3 version 1 is disputed and has three joint premises
    When its view resizes through 120 by 40, 80 by 24 and 40 by 24
    Then the same exact premises, negations, conclusion, dispute and live target are retained
    And the narrow view says IF ALL and THEN instead of clipping node labels
    And no decisive premise remains collapsed while endorsement is requested

  @S126 @p4 @later @automated
  Scenario: Keep positions independent and drafts attributed when speakers change
    Given Maya has an unsent response and a position form for L3 version 1
    When the operator switches the declared speaker to Leo
    Then Maya's draft remains attributed to Maya and cannot be submitted as Leo's answer
    And the actor-bound position form is invalidated and redisplayed for Leo
    And wording, belief and exact-test reliance have independent controls with no substantive preselection
    And no assent, belief, reliance or consensus is inferred from the switch

  @S127 @p5 @later @automated
  Scenario: Display cross-tool consequences without converting trace references into causes
    Given a corrected claim has exact registered dependencies in Cloud, FRT and PRT records
    When the correction is inspected in the workspace
    Then before and after versions are aligned and each registered dependency says review needed
    And trace links name their dependency meaning and are excluded from causal traversal
    And historical positions, prior observations and action execution remain on their original records
    And the view does not claim the dependency list exhausts real-world consequences
```

### 12_trees_in_conversation.feature

```gherkin
@J03 @J07 @J11 @J12 @J14
Feature: Grow the six thinking-process trees in conversation
  The trees use the LTP 1.0 vocabulary of the reasoncommons guide: a claim is one
  sourced statement in one tree with a role; a link is one typed relation that
  belongs to one tree and may reach a statement of another. The commons' goal is the
  Goal Tree's top statement. What the consultant proposes for the trees waits in
  the backlog until the operator accepts it (feature 13). Joint premise groups and
  rival routes stay with the later causal and full-tools releases.

  @S128 @p2 @v1 @automated
  Scenario: Record a reported cause and its effect in the Current Reality Tree
    Given a commons whose goal is "A clear next step after open evenings"
    When the operator says "Newcomers do not know the next step, because we never offer one"
    And the consultant proposes a symptom, a cause and a causes link citing that input
    And the operator accepts them
    Then the Current Reality Tree holds both statements and the link
    And the literal input remains the source of all three
    And the Trees view draws the symptom above its cause, labelled "because"

  @S129 @p2 @v1 @automated
  Scenario Outline: Reject a tree record that breaks the tree grammar
    Given a commons whose goal is "A clear next step after open evenings"
    When the consultant proposes <record> with an ordinary note
    Then the entire proposal is rejected before commit
    And the raw input and failure receipt remain available

    Examples:
      | record                                              |
      | a goal role in the Current Reality Tree             |
      | a statement in the goal role, beside the commons goal  |
      | a link whose claims both belong to other trees      |
      | a link from a claim to itself                       |
      | a link to a claim proposed after the link           |
      | a link with a relation outside the LTP vocabulary   |

  @S130 @p2 @v1 @automated
  Scenario: Reword and withdraw without rewriting history
    Given a Current Reality Tree with a symptom, a cause and a causes link
    When the operator asks to word the cause more precisely and accepts the consultant's new wording
    Then the tree shows the new wording, still linked to the symptom
    And the link is flagged for review because it was stated for the earlier wording
    And the earlier wording stays in the commons history
    When the operator withdraws the cause and accepts the consultant's withdrawal with its reason
    Then the tree no longer shows the cause or its link
    And a later proposal linking the withdrawn cause is rejected before commit

  @S131 @p2 @v1 @automated
  Scenario: Connect a test to the tree action it carries out
    Given a commons set to accept proposals automatically
    And a Transition Tree action "Prototype one next step after open evenings"
    When the operator records a test with a forecast that carries out that action
    And reports an observation for the test
    Then the Trees view shows the test's original forecast and reported result under the action
    And the test's original forecast is unchanged

  @S132 @p2 @v1 @automated
  Scenario: Bring in trees from an LTP file without inferring anything
    Given a commons in the middle of the goal-action-review loop
    And an LTP 1.0 file with six statements, two single-premise links, one joint-premise link and one assessment
    When the operator brings in the file
    Then the file is retained as a source and every imported statement and link cites it
    And the joint-premise link and the assessment are kept as labelled notes
    And everything the file brings in waits in the backlog until the operator accepts it
    And the current question carries on from the same step
    And the consultant is not called

  @S133 @p2 @v1 @automated
  Scenario: Export the trees and bring them back unchanged
    Given a commons with imported trees
    When the operator exports the trees to a new LTP file and brings that file into a new commons
    And the operator accepts everything the file brings in
    Then both commons show the same statements, roles, links and assumptions
    And exporting to an existing file is refused

  @S134 @p2 @v1 @automated
  Scenario: Browse the trees locally
    Given a commons with imported trees
    When the operator opens the Trees view and then returns to the current question
    Then no consultant call and no revision occurs
```

### 13_proposals_and_review.feature

```gherkin
@J07 @J08 @J14 @J17
Feature: Decide what enters the model
  The consultant drafts what the operator's words could mean; the operator decides
  what enters the model. The goal, the six trees and the tests are one model, and
  every change the consultant proposes to any part of it waits in the backlog with
  its source until the operator accepts it, unless the operator has set the commons to
  accept proposals automatically. The backlog lists proposals in the order they are
  best decided. A change asks for review of whatever explicitly cites what it
  changed, and every acceptance can be undone. Accepting admits a statement into the
  working model; it does not make it true or record anyone's belief.

  @S135 @p2 @v1 @automated
  Scenario: Hold a reply's proposals in the backlog by default
    Given a commons whose goal is "A clear next step after open evenings"
    When the operator says "Newcomers do not know the next step, because we never offer one"
    And the consultant proposes a symptom, a cause and a causes link citing that input
    Then the consultant's next question becomes the live question
    And the symptom, the cause and the link wait in the backlog, each citing the operator's words
    And the Current Reality Tree is unchanged
    And a confidence the consultant gave is kept with each proposal without deciding anything

  @S136 @p2 @v1 @automated
  Scenario: Accept a reply's proposals together
    Given the backlog holds a symptom, a cause and a causes link proposed from one input
    When the operator accepts all three
    Then one new revision adds them to the Current Reality Tree without a consultant call
    And the revision records who accepted them, when, and that they were accepted explicitly
    And the cause keeps its basis, so an accepted hypothesis is still a hypothesis
    And the backlog is empty and the live question and draft are unchanged

  @S137 @p2 @v1 @automated
  Scenario: Reject a proposal together with what needs it
    Given the backlog holds a symptom, a cause and a causes link proposed from one input
    When the operator rejects the cause
    Then the operator is shown that the link, which needs the cause, is rejected with it
    When the operator confirms
    Then the cause and the link leave the backlog and the symptom still waits
    And the commons history keeps both rejected proposals with the operator's decision
    And neither can be accepted later

  @S138 @p2 @v1 @automated
  Scenario: List the backlog in the order it is best decided
    Given the backlog holds, from earlier replies, a Transition Tree action, a Current Reality cause, a causes link from that cause and a new version of the goal
    When the operator opens the backlog
    Then the new version of the goal comes first, marked to be decided first because the rest is judged against it
    And the cause comes before its link, which says it waits for the cause
    And the Current Reality proposals come before the Transition Tree action
    When the operator accepts the link
    Then the operator is shown that the cause is accepted with it
    And after confirming, both are in the Current Reality Tree while the new goal still waits

  @S139 @p2 @v1 @automated
  Scenario: Accept proposals automatically when the operator has chosen to
    Given a commons set to accept proposals automatically
    When the consultant proposes a symptom, a cause and a causes link citing the operator's words
    Then the revision that publishes the next question also adds all three to the Current Reality Tree
    And it records that they were accepted automatically under the operator's setting
    And the operator can undo that acceptance like an explicit one

  @S140 @p2 @v1 @automated
  Scenario: Only the operator changes how proposals are accepted
    Given a commons that holds proposals for review, with two proposals waiting
    When the operator sets the commons to accept proposals automatically
    Then a revision records the operator's choice without a consultant call
    And the two proposals already waiting still wait
    And a consultant reply that tries to change the setting is rejected before commit

  @S141 @p2 @v1 @automated
  Scenario: Undo an accepted change without rewriting history
    Given the Current Reality Tree holds an accepted cause with its causes link and a later accepted symptom that cites neither
    And a waiting proposal links another statement to the cause
    When the operator undoes the acceptance of the cause
    Then the operator is shown that the link leaves the tree with it and the waiting proposal is closed
    When the operator confirms
    Then a new revision removes the cause and its link from the tree and keeps the later symptom
    And the commons history keeps the operator's words, the proposals, their acceptance and the undo
    And the undo is final: it cannot be undone and the cause does not return to the backlog

  @S142 @p2 @v1 @automated
  Scenario: Ask for review of what cites a changed statement
    Given an accepted Conflict tree injection, a Future Reality link from that injection to a desired effect, and a test that carries out the injection
    When the operator accepts a new wording of the injection
    Then the link and the test are flagged for review, each naming the change that raised the flag
    And neither is changed, withdrawn or marked false
    And both flags wait in the backlog
    When the operator marks the test as still holding
    Then the test's flag closes with the operator's decision recorded and the link's flag stays open

  @S143 @p2 @v1 @automated
  Scenario: Let a change cascade one explicit step at a time
    Given an accepted Conflict tree requirement, an injection linked to it, and a Future Reality link from that injection to a desired effect
    When the operator accepts a new wording of the requirement
    Then the Conflict tree link between the injection and the requirement is flagged for review
    And the Future Reality link is not flagged, because nothing it cites has changed
    When the consultant proposes a new wording of the injection and the operator accepts it
    Then the Future Reality link is flagged for review in turn
    And the backlog names, for each flag, the change that raised it

  @S144 @p2 @v1 @automated
  Scenario: Keep one goal at the top of the Goal Tree
    Given a commons whose goal is "At least 90% of orders on time by October 30"
    When the consultant proposes a critical success factor that the goal requires and the operator accepts it
    Then the Goal Tree shows the commons' goal at its top with the factor beneath it
    And the Goal view and the Goal Tree show the same goal
    When the consultant proposes a second goal that is not a new version of the current one
    Then the proposal is rejected before commit because a commons has one goal

  @S145 @p2 @v1 @automated
  Scenario: Use a statement from another tree in a link
    Given an accepted Conflict tree injection
    When the consultant proposes a desired effect and a Future Reality link from that injection to it
    And the operator accepts both
    Then the Future Reality Tree draws the injection, marked as from the Conflict tree, leading to the desired effect
    And the injection stays one statement, so its new wording shows in both trees
    And a link whose two statements both belong to other trees than its own is rejected before commit

  @S146 @p2 @v1 @automated
  Scenario: Decide proposals while the consultant is working
    Given the operator has sent an answer and the consultant has not replied
    When the operator accepts a waiting proposal
    Then the consultant's reply is published when it arrives rather than treated as stale
    And its proposals are checked against the model as it stands after that acceptance

  @S147 @p2 @v1 @automated
  Scenario: Ask the consultant to draft amendments for open reviews
    Given two accepted statements flagged for review
    When the operator asks the consultant about the open reviews
    Then one consultant request carries the flagged statements and the changes that raised the flags
    And the amendments it proposes wait in the backlog like any other proposal

  @S148 @p2 @v1 @automated
  Scenario: Withdraw a statement together with the links that join it
    Given the Current Reality Tree holds an accepted cause with its causes link and a test that carries out the cause
    And the consultant proposes withdrawing the cause
    When the operator accepts the withdrawal
    Then the operator is shown that the link leaves the tree with the cause and the test is flagged for review
    And nothing changes until the operator confirms
    When the operator confirms
    Then a new revision removes the cause and its link from the tree and the test's flag waits in the backlog
    And in a commons set to accept proposals automatically, the same withdrawal waits for the operator

  @S149 @p2 @v1 @automated
  Scenario: Cite only words the commons has taken in
    Given an answer the operator sent became stale before the consultant replied to it
    When the operator sends another answer
    Then the consultant's request does not carry the stale answer
    And a reply whose proposal cites the stale answer is rejected before commit, leaving the commons unchanged
    And the stale answer stays retained with its source, so the operator can send it again

  @S150 @p2 @v1 @automated
  Scenario: Revise a test's forecast only before its first result
    Given an accepted test forecasting "6 of 30" and an accepted action that carries it out
    When the operator accepts a new version of the test forecasting "8 of 30"
    Then the Tests view shows one test with the new forecast, and the commons history keeps the earlier one
    And the action is flagged for review because it was planned for the earlier version
    When a result is reported for the test and accepted
    Then a further new version of the test is rejected before commit, so the forecast stays as it was before the result
    And a result citing the earlier version of the test is rejected before commit
```

## 8. V1 TUI goal action review session

```text
REASON COMMONS / FIRST-RELEASE TUI JOURNEY
Delivery profile: p2 cumulative v1; deterministic adapter acceptance specimen.
Fictional Forge commons; an authored specimen, not a recording of the
application. Frames are 80x24. V1 has no structured graph browser, participant
stance registry or formal tree authoring. Its persistent workspace, literal
response editor, visible local controls, proposals that wait for the operator
and forecast/result comparison ARE required from p1-p2. No typed commands are
needed inside this session.
$ reason-commons new forge --store ./forge-v1 --speaker Sam
EVENT start r0000

SCREEN M01 80x24
+------------------------------------------------------------------------------+
| forge | Sam | r0000 saved | Start | Focus: Response                          |
+------------------------------------------------------------------------------+
| Goal unknown | Safeguards unknown | No test                                  |
+------------------------------------------------------------------------------+
| Welcome to Reason Commons.                                                   |
| What is happening, and what would count as better?                           |
| You can begin in ordinary words. Unknown measures can stay open.             |
|                                                                              |
| [How this works]  [Open a commons]                                           |
| Send asks the consultant. Browsing and saved explanations stay local.        |
| Enter adds a line. Tab to Send, then Enter sends once.                       |
| All typing, including 5, ?, q and punctuation, is literal in Response.       |
|                                                                              |
|                                                                              |
|                                                                              |
+------------------------------------------------------------------------------+
| Response | Send asks consultant; Enter adds a line.                          |
| _                                                                            |
|                                                                              |
| [Send]  [Explain this]  [Other moves]  [Views]  [Actions]                    |
+------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions             |
+------------------------------------------------------------------------------+

ACTION: Sam enters: Goal: >=90% of October due orders on time, original
promised dates; review October 30. September 32/50 = 64%. Protect overtime
<=20h each week and defects <=2% of inspected units each week. These are my
reported records. Tab to Send, Enter.
EVENT semantic in001 r0001 question001

SCREEN M02 80x24
+------------------------------------------------------------------------------+
| forge | Sam | r0001 saved | Choose a test | Focus: Response                  |
+------------------------------------------------------------------------------+
| Goal proposed, waiting | Safeguards proposed | No test                       |
+------------------------------------------------------------------------------+
| PROPOSED from your words / waiting for you; not yet in the model             |
|   Goal: >=90% October due orders on original dates; review Oct 30            |
|   Baseline: September 32/50 = 64%, reported by Sam                           |
|   Protect: overtime <=20h EACH week; defects <=2% inspected units/week       |
| [Accept all]  [Backlog]   Accepting admits it; it does not prove it.         |
|                                                                              |
| DECISION / What change can you authorize and observe?                        |
| Choose a small trial with an original forecast we can review later.          |
| Other people's agreement and authority remain unknown.                       |
| [Goal]  [Reported sources]  [Explain this]  [Other moves]                    |
|                                                                              |
+------------------------------------------------------------------------------+
| Response | Send asks consultant; Enter adds a line.                          |
| _                                                                            |
|                                                                              |
| [Send]  [Explain this]  [Other moves]  [Views]  [Actions]                    |
+------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions             |
+------------------------------------------------------------------------------+

ACTION: Sam Tabs to Accept all and presses Enter. The goal with its baseline
and protections enters the model in one local revision; no consultant call.
The band now shows the accepted goal.
EVENT local r0002 target=G1@1 dimension=membership value=accepted actor=Sam
ACTION: Sam types a draft "5 requests?", then Tabs to Other moves and presses
Enter. This menu keeps the question and draft. No consultant call has been
made.

SCREEN M02A 80x24
+------------------------------------------------------------------------------+
| forge | Sam | r0002 saved | Other moves | Focus: Other moves                 |
+------------------------------------------------------------------------------+
| Goal >=90% October delivery | Protect overtime <=20h/wk; defects <=2%        |
+------------------------------------------------------------------------------+
| Choose a route. Nothing is sent until you activate an item.                  |
|                                                                              |
| > Understand why this question    LOCAL: saved explanation                   |
|   Inspect goal and safeguards     LOCAL: saved records                       |
|   Help plan an observation        ASKS CONSULTANT                            |
|   Give direct advice              ASKS CONSULTANT                            |
|   Ask a different question        ASKS CONSULTANT                            |
|   Leave this question open        LOCAL: retains draft                       |
|                                                                              |
| Arrows select; Enter activates. Esc returns without a choice.                |
| Your draft stays attributed to Sam and the current question.                 |
+------------------------------------------------------------------------------+
| Live: Choose a test | Draft retained                                         |
| 5 requests?                                                                  |
|                                                                              |
| [Return to question]  [Help]  [Views]  [Actions]                             |
+------------------------------------------------------------------------------+
| Tab controls  Arrows select  Enter open  Esc back  F1 Help  Ctrl+P Actions   |
+------------------------------------------------------------------------------+

ACTION: Sam activates the selected Understand why this question item. The
local Explain this view says: A bounded trial and prospective forecast let you
compare results later, while protecting overtime and defects. The question
asks for work you can authorize. Esc restores the same question, draft and
cursor; no call. Sam replaces the draft and sends:
I have authority to name a triage owner and backup before Oct 5. Rehearse two
requests; both roles must explain response and escalation before start. Pilot
daily triage Oct 5-16; review Oct 19. Predict delivery >=80%, urgent
acknowledgement >=95% within 24h. Retain overtime/defect bounds. Record
original dates, mix, suppliers and rule use. Stop expansion on any breach. If
either role cannot explain escalation, resolve that before start. Urgent
fulfillment is a separate unknown.
EVENT semantic in002 r0003 question002

SCREEN M03 80x24
+------------------------------------------------------------------------------+
| forge | Sam | r0003 saved | Prepare P1@1 | Focus: Response                   |
+------------------------------------------------------------------------------+
| Goal >=90% October delivery | Protect overtime <=20h/wk; defects <=2%        |
+------------------------------------------------------------------------------+
| PROPOSED / waiting for you: test P1@1 and its preparation action             |
| P1@1 forecast, saved before results / Oct 5-16; review Oct 19                |
| Forecast: delivery >=80%; urgent acknowledgement >=95% within 24h.           |
| Protect overtime <=20h EACH week; defects <=2% inspected units/week.         |
| Owner and stop authority: Sam declares both; no expansion on breach.         |
| ACTION: name owner/backup and rehearse two requests before Oct 5.            |
| EXPECTED STATE: both roles can explain response and escalation.              |
| Execution: NOT STARTED | expected state: UNKNOWN | no reminder scheduled     |
| Urgent-need fulfillment: UNKNOWN.                                            |
| [Accept all]  [Backlog]  [Original forecast]  [Sources]                      |
| DECISION / What happens when you perform this preparation?                   |
+------------------------------------------------------------------------------+
| Response | Send asks consultant; Enter adds a line.                          |
| _                                                                            |
|                                                                              |
| [Send]  [Explain this]  [Other moves]  [Views]  [Actions]                    |
+------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions             |
+------------------------------------------------------------------------------+

ACTION: Sam activates Accept all. P1@1 and its action enter the model; one
local revision, no call.
EVENT local r0004 target=P1@1,A1@1 dimension=membership value=accepted actor=Sam
ACTION: Sam opens Actions > Accept proposals automatically and confirms. From
now on a reply's ready proposals enter the model with the reply, recorded as
accepted under Sam's setting, and each can be undone from History. Proposals
already waiting would keep waiting; none are. No call.
EVENT local r0005 target=case dimension=acceptance value=automatic actor=Sam
ACTION: Sam answers: I named owner and backup today. Rehearsal has not
happened; I do not know whether they can explain the rule.
EVENT semantic in003 r0006 question003

SCREEN M04 80x24
+------------------------------------------------------------------------------+
| forge | Sam | r0006 saved | Observe the result | Focus: Response             |
+------------------------------------------------------------------------------+
| Goal >=90% October delivery | Protect overtime <=20h/wk; defects <=2%        |
+------------------------------------------------------------------------------+
| PREPARATION / reported by Sam; added under Sam's setting, can be undone      |
| +-- ACTION ---------------------+ +-- EXPECTED STATE --------------------+   |
| | Roles named: COMPLETED        | | Rule understood: UNKNOWN             |   |
| +-------------------------------+ +--------------------------------------+   |
| Action completed; result awaiting observation.                               |
| Naming roles does not establish understanding or better delivery.            |
| P1 original forecast and G1 goal are unchanged.                              |
| DECISION / Does rehearsal establish readiness before the pilot?              |
| What did both roles demonstrate?                                             |
| [P1 forecast]  [Reported sources]  [History]                                 |
|                                                                              |
+------------------------------------------------------------------------------+
| Response | Send asks consultant; Enter adds a line.                          |
| _                                                                            |
|                                                                              |
| [Send]  [Explain this]  [Other moves]  [Views]  [Actions]                    |
+------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions             |
+------------------------------------------------------------------------------+

ACTION: Actions > Export > ./forge-v1-before-review.reasoncase. Actions > Save
and quit. Local export and cursor save, no call.
$ reason-commons resume ./forge-v1
M04 is restored at r0006 with Observe the result as the current question.
Goal, safeguards and P1 remain pinned; preparation state still unobserved. No
consultant call.
ACTION: Sam submits: Both roles correctly explained response and escalation in
the two rehearsals. Pilot then ran as planned. Fifty due orders, 40 on time.
Overtime 18h then 19h; defects 1/50 then 0/50 inspected units. Urgent
acknowledgements 18/20 within 24h. Original dates unchanged; similar mix but
steadier suppliers. This does not isolate triage as cause.
EVENT semantic in004 r0007 question004

SCREEN M05 80x24
+------------------------------------------------------------------------------+
| forge | Sam | r0007 saved | Review P1 | Focus: Response                      |
+------------------------------------------------------------------------------+
| ! Acknowledgement BREACH 90% <95% | Goal >=90% remains unmet                 |
+------------------------------------------------------------------------------+
| ! Urgent acknowledgement BREACH: 18/20 = 90%, original bound >=95%           |
| MEASURE             ORIGINAL             REPORTED RESULT                     |
| Delivery            >=80%                40/50 = 80% supported               |
| Acknowledgement     >=95% within 24h     18/20 = 90% BREACH                  |
| Overtime EACH week  <=20h                 18h; 19h within bound              |
| Defects EACH week   <=2% inspected units  1/50 = 2%; 0/50 = 0%               |
| G1 goal >=90% remains unmet. Supplier changes limit attribution.             |
| Rehearsal state: met by report. Original P1 unchanged; do not expand.        |
| DECISION / What delayed the two acknowledgements?                            |
| [Original forecast]  [Source report]  [Other moves]                          |
|                                                                              |
+------------------------------------------------------------------------------+
| Response | Send asks consultant; Enter adds a line.                          |
| _                                                                            |
|                                                                              |
| [Send]  [Explain this]  [Other moves]  [Views]  [Actions]                    |
+------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions             |
+------------------------------------------------------------------------------+

ACTION: Sam answers: They waited for supplier dates. The owner thought the
first response must promise a final date. We can acknowledge receipt before
that date is known.
EVENT semantic in005 r0008 question005

SCREEN M06 80x24
+------------------------------------------------------------------------------+
| forge | Sam | r0008 saved | Adapt the trial | Focus: Response                |
+------------------------------------------------------------------------------+
| ! P1 acknowledgement breach retained | Follow-up proposed                    |
+------------------------------------------------------------------------------+
| RECOMMENDATION / separate receipt acknowledgement from date commitment       |
| Expected effect: supplier uncertainty no longer blocks acknowledgement.      |
| Need: respond promptly without inventing a delivery promise.                 |
| Keep the prior protections; measure urgent-need fulfillment separately.      |
| No numeric fulfillment bound has been agreed.                                |
| P1 breach remains; original forecast unchanged; no causal proof.             |
| DECISION / Name follow-up owner, forecast, window and stopping response.     |
| [Draft follow-up]  [Original P1]  [Ask a different question]                 |
|                                                                              |
|                                                                              |
|                                                                              |
+------------------------------------------------------------------------------+
| Response | Send asks consultant; Enter adds a line.                          |
| _                                                                            |
|                                                                              |
| [Send]  [Explain this]  [Other moves]  [Views]  [Actions]                    |
+------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions             |
+------------------------------------------------------------------------------+

ACTION: Sam answers: I will run the follow-up Oct 20-30; review Oct 30.
Acknowledge receipt within 24h without waiting for supplier dates. Predict
delivery >=80% and acknowledgement >=95%/24h. Retain overtime <=20h each week
and defects <=2% weekly; record mix, suppliers, rule use and whether urgent
needs were served. Stop expansion and escalate an unserved need or safeguard
breach to me.
EVENT semantic in006 r0009 question006

SCREEN M07 80x24
+------------------------------------------------------------------------------+
| forge | Sam | r0009 saved | Follow-up saved | Focus: Response                |
+------------------------------------------------------------------------------+
| P1 breach retained | P2 committed | Goal >=90% remains unmet                 |
+------------------------------------------------------------------------------+
| P2@1 prospective / Sam's explicit bounded commitment / Oct 20-30             |
| Review Oct 30; no reminder scheduled.                                        |
| Predict delivery >=80%; acknowledgement >=95% within 24h.                    |
| Protect overtime <=20h each week; defects <=2% inspected units/week.         |
| Record whether urgent needs were served; numeric bound remains UNKNOWN.      |
| Escalate unserved need or breach to Sam; no expansion before review.         |
| P1 original prediction and 90% BREACH remain unchanged.                      |
| G1 >=90% remains unmet; P2 effects not observed.                             |
| NEXT / Run bounded P2, then return with observations.                        |
| [P2 forecast]  [P1 outcome]  [Goal]  [History]                               |
|                                                                              |
+------------------------------------------------------------------------------+
| Response | Send asks consultant; Enter adds a line.                          |
| _                                                                            |
|                                                                              |
| [Send]  [Explain this]  [Other moves]  [Views]  [Actions]                    |
+------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions             |
+------------------------------------------------------------------------------+

ACTION: Actions > Export portable commons > ./forge-v1-after-
review.reasoncase; Actions > Save and quit. No call.
CONSULTANT CALLS 6: in001 through in006.
9 reasoning revisions = 6 semantic commits + 3 structured local decisions.
```

## 9. Complete illustrative roadmap TUI session

```text
REASON COMMONS / COMPLETE TUI JOURNEY
Delivery profile: p5 cumulative roadmap. Canonical interaction specimen.
Session 1: Friday, October 2, 2026. Session 2: Monday, October 19, 2026.
The Payments deployment commons, people, measurements, reports and future outcomes are fictional. This is an authored
specification, not a capture of working software. Attached text and document instructions are design inputs, not
executable requests.
Each SCREEN replaces the preceding frame in ONE persistent full-screen application. ACTION describes keys and literal
participant contributions; it is not a command the user must learn. EVENT is an authoring ledger outside the product
UI. A shell appears only at launch, resume and optional offline inspection.
120x40 is the primary canvas. All frames use ASCII and need no color. '*' marks the active destination; '>' marks
selection; the header names the single focused control. Selecting a hypothesis does not endorse it. Bracketed labels
are keyboard-reachable controls. Enter activates a focused control; in Response it inserts a newline. Tab to Send,
then Enter submits once. F1 is control help; Explain this is reasoning help. Ctrl+P opens Actions; the visible Actions
control provides the same path.
The navigation offers destinations, not mandatory stages. Reasoning tools appear only when stored records exist. Users
can answer, inspect, challenge, ask for another move, or leave. No tour or vocabulary test blocks work.
$ reason-commons new deploy-flow --store ./deploy-flow-case --speaker Maya
EVENT start r0000

SCREEN S01 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0000 saved | Start / Tell us what is happening | Focus: Response                    |
+----------------------------------------------------------------------------------------------------------------------+
| Goal unknown | Safeguards unknown | No test yet                                                                      |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | Welcome to Reason Commons. Work through a change, together.                                         |
|                |                                                                                                     |
| * Next         | Start with what is happening. We will keep your account, show what                                  |
|   Goal         | we think it means, and help you choose a useful next move.                                          |
|   Reasoning    |                                                                                                     |
|   Unlinked     | You can correct the account at any time.                                                            |
|   Tests        |                                                                                                     |
|   Actions      |      +-----------------------+     +-------------------------+                                      |
|   History      |      | Your reports          |     | A next useful question  |                                      |
|                |      | What you have seen    | --> | What would help decide? |                                      |
| [Views]        |      +-----------------------+     +-------------------------+                                      |
| [Actions]      |                   This shows the workflow, not causation.                                           |
|                |                                                                                                     |
| Saved locally  | Want to look around first? [How this works] [Open a saved commons]                                  |
|                | Navigation and saved explanations stay local. Send asks the consultant.                             |
|                | New commons: success, safeguards and authority are still unknown.                                   |
|                | There is no need to type commands or name a Thinking Process.                                       |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Start | Send asks consultant; Enter adds a line.                                                         |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: In Response, Maya types: Production changes sit in the release queue for days. Customer escalations cause
engineers to interrupt testing for hotfixes. Then standard changes need revalidation and miss their release window. We
also do too much release work after hours. Tab to Send, Enter.
EVENT semantic in001 r0001 question001

SCREEN S02 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0001 saved | Define success | Focus: Response                                       |
+----------------------------------------------------------------------------------------------------------------------+
| Goal provisional: shorter release lead time | Safeguards not yet specified                                           |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | WHAT WE HEARD / Maya's reports; records not inspected                                               |
|                |                                                                                                     |
| * Next         | +----------------------------+     +-----------------------------+                                  |
|   Goal         | | Changes wait in the queue  |     | Hotfixes interrupt testing  |                                  |
|   Reasoning    | +----------------------------+     +-----------------------------+                                  |
|   Unlinked     |                                                                                                     |
|   Tests        | +----------------------------+     +-----------------------------+                                  |
|   Actions      | | Standard work revalidated  |     | Release work after hours    |                                  |
|   History      | +----------------------------+     +-----------------------------+                                  |
|                | Kept as separate reports. Their connections are not established yet.                                |
| [Views]        |                                                                                                     |
| [Actions]      | DECISION / What would count as an improvement worth keeping?                                        |
|                | What progress do you want, by when, and what must not get worse?                                    |
| Saved locally  |                                                                                                     |
|                | You might give a measure, a date, and one or two safeguards.                                        |
|                | If a number is unknown, say so; we can keep it open.                                                |
|                | [See the reports]  [Help me define success - asks consultant]                                       |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Define success | Send asks consultant; Enter adds a line.                                                |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya enters a multiline response with Enter between lines, then Tab to Send and Enter:
Scope: standard production changes for Payments. For changes marked release-ready October 1-30, at least 80% reach
production within 3 business days. September: 12/30 within 3 business days; 3/30 rollbacks; about 11 after-hours
engineer-hours per week. Protect rollback <=5% of the deployed cohort and after-hours release work <=8 engineer-hours
in any week, outside 08:00-18:00. These are my reports of the dashboard and rota; I have not attached the records. Use
Monday-Friday 08:00-18:00 Europe/Berlin as business hours, with no excluded closures. Review October 30, with any
immature three-day outcomes marked pending rather than failures.
EVENT semantic in002 r0002 question002

SCREEN S03 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0002 saved | Connect the reports | Focus: Response                                  |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | SUCCESS / G1@1                                      BASELINE / September                            |
|                | +-----------------------------------------------+  +----------------------+                         |
| * Next         | | >=80% of Oct 1-30 release-ready Payments       |  | Within 3 days: 12/30 |                        |
|   Goal         | | changes reach production within 3 business    |  | = 40%                |                         |
|   Reasoning    | | days. Oct 30 review; immature outcomes pending.|  | Rollback: 3/30 = 10% |                        |
|   Unlinked     | +-----------------------------------------------+  | After-hours: ~11h/wk |                         |
|   Tests        |                                                    +----------------------+                         |
|   Actions      | Protect rollback <=5%; after-hours <=8 engineer-hours in EVERY week.                                |
|   History      | Calendar, timezone and cohort maturation are explicit fields in [Goal].                             |
|                | Source: Maya's reports. Other people's positions on G1 remain unknown.                              |
| [Views]        |                                                                                                     |
| [Actions]      | DECISION / Which explanation should we examine before choosing a change?                            |
|                | Which reported effect do you think causes another?                                                  |
| Saved locally  |                                                                                                     |
|                | [Goal and safeguards]  [Unlinked reports]  [Other moves]                                            |
|                | You can propose a connection or tell us this is the wrong next question.                            |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Connect the reports | Send asks consultant; Enter adds a line.                                           |
| Urgent customer escalations cause standard changes to miss the three-day target._                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya activates Send with the displayed draft.
EVENT semantic in003 r0003 question003

SCREEN S04 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0003 saved | Find the mechanism | Focus: Response                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | CURRENT REALITY / first proposed connection, not an established cause                               |
|                |                                                                                                     |
| * Next         | +-------------------------------+            +-------------------------------+                      |
|   Goal         | | Urgent customer escalations   |            | Standard changes miss the     |                      |
|   Reasoning    | | Maya reports these occur      |-- L1 ? --->| three-business-day target     |                      |
|   Unlinked     | +-------------------------------+ hypothesis +-------------------------------+                      |
|   Tests        |                                                                                                     |
|   Actions      | The arrow needs an explanation of what changes in the work.                                         |
|   History      | DECISION / Is this a useful mechanism to test?                                                      |
|                | How does an escalation make a standard change late?                                                 |
| [Views]        |                                                                                                     |
| [Actions]      | Tell us what happens between the two boxes and when it does not happen.                             |
|                | [Inspect connection]  [Explain this]  [Challenge the question]                                      |
| Saved locally  | No claim of an operational constraint follows from this diagram.                                    |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Find the mechanism | Send asks consultant; Enter adds a line.                                            |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya answers: Engineers stop validation to insert the hotfix, then restart checks. This misses the target only
when net unrecovered recheck time exceeds slack before release cutoff and no eligible later release occurs before the
three-day deadline. Spare capacity or another eligible release could prevent that.
EVENT semantic in004 r0004 question004

SCREEN S05 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0004 saved | Test the whole inference | Focus: Response                             |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | CURRENT REALITY / Payments standard changes / proposed, partial                                     |
|                | Read down: every premise inside ALL belongs to ONE inference.                                       |
| * Next         |                                                                                                     |
|   Goal         | +-- ALL / L3@1 ---------------------------------------------------------+                           |
|   Reasoning    | | +-------------------------------------------------------------------+ |                           |
|   Unlinked     | | | Validation is interrupted and must be repeated for this change.   | |                           |
|   Tests        | | +-------------------------------------------------------------------+ |                           |
|   Actions      | | +-------------------------------------------------------------------+ |                           |
|   History      | | | Net unrecovered recheck time exceeds slack before release cutoff. | |                           |
|                | | +-------------------------------------------------------------------+ |                           |
| [Views]        | | +-------------------------------------------------------------------+ |                           |
| [Actions]      | | | No eligible later release occurs before its three-day deadline.   | |                           |
|                | | +-------------------------------------------------------------------+ |                           |
| Saved locally  | +-----------------------------------+-----------------------------------+                           |
|                |                                     | L3: hypothesis                                                |
|                |                                     v                                                               |
|                |             +-----------------------+----------------------+                                        |
|                |             | This standard change misses the 3-day target |                                        |
|                |             +----------------------------------------------+                                        |
|                | Spare capacity could defeat premise 2; another timely release defeats premise 3.                    |
|                | Missing evidence: dated interruptions, rechecks, slack and release windows.                         |
|                | Could the threatened release date instead be causing the escalation?                                |
|                | [Expand reasoning]  [Compare directions]  [Explain ALL]                                             |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Test the whole inference | Send asks consultant; Enter adds a line.                                      |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya types the start of an answer, "Could delay already exist?", then Tabs to Expand reasoning and opens it.
Her draft is checkpointed. The larger map and its right-hand inspector use the same r0004, selected L3@1 and exact
premises. This is optional inspection, not another answer or consultant call.

SCREEN S05A 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0004 saved | Reasoning / Explore L3@1 | Focus: Branch list                          |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | BRANCHES / select a relation      CRT / arrows UP / partial     SELECTED L3@1                       |
|                | > L3 interruption + delay        +-------------------------+   Hypothesis, not proof                |
|   Next         |   L1 escalation to hotfix        | Standard change misses  |   Inputs: all 3 required               |
|   Goal         |   Other routes not mapped        | three-day target        |   Scope: this change                   |
| * Reasoning    |                                 +------------^------------+   before release window                 |
|   Unlinked     | SAME SAVED MODEL                             | L3 hypothesis                                        |
|   Tests        | Expand/collapse changes          +-----------+-------------+   MECHANISM                            |
|   Actions      | the view, never the claim.        | ALL                     |   Rechecks consume time;              |
|   History      |                                 | Interruption + rechecks  |   time unavailable before              |
|                | Unlinked reports retained:       | Net loss exceeds slack  |   release; delay crosses               |
| [Views]        |   After-hours work               | before release cutoff   |   three-day boundary.                  |
| [Actions]      |   Queue delays                   | No timely later release |                                        |
|                | Unknown links stay unknown.      +------------^------------+   EVIDENCE                             |
| Saved locally  |                                              |                Maya's report, in004.                 |
|                |                                 +------------+------------+   Dashboard not attached.               |
|                |                                 | Validation interrupted  |   Event sequence unknown.               |
|                |                                 +------------^------------+                                         |
|                |                                              | L1 hypothesis  CHALLENGE                             |
|                |                                 +------------+------------+   Can another release or                |
|                |                                 | Urgent escalation;      |   recovery route absorb                 |
|                |                                 | hotfix inserted         |   the lost time?                        |
|                |                                 +-------------------------+                                         |
|                | Sources support occurrence separately from inference. Node evidence is not link evidence.           |
|                | [Full L3 record]  [Evidence]  [Challenge this]  [Return to question]                                |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Live question: Test the whole inference | Draft retained. [Return to question]                                       |
| Retained response draft: Could delay already exist?                                                                  |
|                                                                                                                      |
| [Full relation]  [Evidence]  [Return to question]  [Actions]                                                         |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Arrows select  Enter open  Esc back  F1 Help  Ctrl+P Actions                                           |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Esc restores the question, its diagram, draft text and editor cursor. The draft remains unsent and attributed
to Maya.

OPTIONAL INSPECTION: Before switching, Maya opens Explain ALL from the question. This worked counterfactual was stored
with the question. Its numbers are illustrative assumptions, not measured Payments evidence, and add no revision or
call. It shows why missing a release depends on lost time versus slack, and why missing one release does not alone
prove the three-day target was missed.

SCREEN S05B 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0004 saved | Explain L3 / Test the boundary | Focus: Worked explanation             |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | AN ILLUSTRATION, NOT COMMONS EVIDENCE / same change and release availability                        |
|                | Minutes from one chosen origin; deployment occurs at an eligible release.                           |
|   Next         | +-- SHARED TIMING -------------------------------------------------------+                          |
|   Goal         | | Planned validation finish: 90 | release cutoff: 120 | deadline: 180    |                          |
| * Reasoning    | | Next eligible release if current one is missed: 240                   |                           |
|   Unlinked     | +-----------------------------------------------------------------------+                           |
|   Tests        |                                                                                                     |
|   Actions      | SAME FIELDS                      MORE NET RECHECKS     FEWER NET RECHECKS                           |
|   History      | Planned validation finish        90 min                90 min                                       |
|                | Added recheck time               60 min                20 min                                       |
| [Views]        | Recoverable time                  0 min                 0 min                                       |
| [Actions]      | Final validation finish         150 min               110 min                                       |
|                | Slack before cutoff              30 min                30 min                                       |
| Saved locally  | Release cutoff                  120 min               120 min                                       |
|                | Eligible deployment             240 min               120 min                                       |
|                | Three-day deadline              180 min               180 min                                       |
|                | Predicted target outcome        MISSED                MET                                           |
|                |                                                                                                     |
|                | Even with NO recovery, 20 min rechecks fit the 30 min slack.                                        |
|                | And if an eligible later release were at 160, the first example could meet 180.                     |
|                | Both conditions matter. The boxes help us test a claim, not certify it.                             |
|                | These calculations do not establish how often either situation occurs.                              |
|                | [Return to question]  [Show actual evidence - reports only]                                         |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Live question: Test the whole inference | Draft retained. [Return to question]                                       |
| Retained Maya draft for the question: Could delay already exist?                                                     |
|                                                                                                                      |
| [Return to question]  [Actual sources]  [Actions]                                                                    |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Arrows select  Enter open  Esc back  F1 Help  Ctrl+P Actions                                           |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Esc returns to the question and its retained draft. The following switch opens Leo's separate response to the
question; Maya's unsent text remains labeled for its original question and actor even after a new response arrives.

ACTION: Maya chooses Actions > Change speaker, enters Leo, then activates Use label. Cursor changes only. Leo answers
in Response: Threatened dates may cause escalation. Interruptions could amplify an existing delay rather than start
it. Your wording represents my objection, but I dispute the claim that interruptions are the main cause.
EVENT semantic in005 r0005 question005

SCREEN S06 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Leo (declared) | r0005 saved | Compare explanations | Focus: Response                                  |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | SAME OUTCOME / standard change misses 3 business days                                               |
|                | These accounts can coexist. Neither is established by an association.                               |
| * Next         |                                                                                                     |
|   Goal         | +-- H1 / interruption first -------------+ +-- H2 / delay first ----------------+                   |
|   Reasoning    | | Interruption + required rechecks      | | Existing queue or complexity       |                    |
|   Unlinked     | | AND net delay exceeds release slack        | | threatens the release date         |               |
|   Tests        | | AND no timely later release      | |                 |                  |                         |
|   Actions      | |                 | hypothesis          | |                 v hypothesis       |                    |
|   History      | |                 v                     | | Escalation follows threatened date |                    |
|                | | Three-day target missed               | | It may add more delay: not settled |                    |
| [Views]        | +---------------------------------------+ +------------------------------------+                    |
| [Actions]      |                                                                                                     |
|                | Distinguish with: event order, queue/load, recheck duration, release slack.                         |
| Saved locally  | Evidence so far: Maya's and Leo's reports. No event series inspected.                               |
|                | DECISION / What observation would change the pilot we choose?                                       |
|                | What happens in a similar low-queue period when a hotfix interrupts checks?                         |
|                | [Inspect L3]  [Sources]  [Record a position]  [Other moves]                                         |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Compare explanations | Send asks consultant; Enter adds a line.                                          |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Leo opens Inspect L3, then Record a position. This opens stored records locally. His earlier natural-language
objection is a reported objection; the structured fields below remain unrecorded until he explicitly saves them.

SCREEN S07 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Leo (declared) | r0005 saved | Position / L3@1 | Focus: Wording                                        |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | RECORD FOR / Leo (declared) / exact formulation L3@1                                                |
|                | Validation interruption + rechecks; net unrecovered time exceeds release slack;                     |
|   Next         | no eligible later release before three-day deadline -> standard change misses target.               |
|   Goal         |                                                                                                     |
| * Reasoning    | WORDING / Does this accurately represent the claim being discussed?                                 |
|   Unlinked     |   ( ) Accurate    ( ) Inaccurate    ( ) Unknown     Current: unrecorded                             |
|   Tests        |                                                                                                     |
|   Actions      | BELIEF / What is your position on that claim?                                                       |
|   History      |   ( ) Supported   ( ) Disputed      ( ) Unknown     Current: unrecorded                             |
|                |                                                                                                     |
| [Views]        | RELIANCE / Will you run a particular bounded test?                                                  |
| [Actions]      |   No test version selected. This is a separate decision.                                            |
|                |                                                                                                     |
| Saved locally  | Saving wording never changes belief. Saving belief never commits a test.                            |
|                | No substantive choice is preselected. Space selects a focused radio.                                |
|                | [Save position - local]  [Choose test - none yet]  [Cancel]                                         |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Live question: Compare explanations | Draft retained. [Return to question]                                           |
| _                                                                                                                    |
|                                                                                                                      |
| [Return to question]  [Help]  [Actions]                                                                              |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Arrows select  Enter open  Esc back  F1 Help  Ctrl+P Actions                                           |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Leo selects only Accurate in Wording and activates Save position.
EVENT local r0006 target=L3@1 dimension=representation value=accurate actor=Leo
ACTION: In the same panel he selects only Disputed in Belief and activates Save position.
EVENT local r0007 target=L3@1 dimension=belief value=disputed actor=Leo
Receipt: r0007 saved. Leo: wording accurate; belief disputed on L3@1. Reliance unrecorded. No consultant calls. Esc
returns to the question with the response draft intact.
ACTION: Actions > Change speaker > Maya. Maya answers: When the queue is small, interrupted testing often recovers
before the next release window. With a large queue, standard work waits longer. But hotfixes also tend to arrive when
the queue is already bad, so that comparison does not isolate the cause.
EVENT semantic in006 r0008 question006

SCREEN S08 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0008 saved | Keep the qualification visible | Focus: Response                       |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | REPORTED COMPARISON / Maya; no controlled comparison                                                |
|                |                    Lower queue                 Higher queue                                         |
| * Next         | Recovered time     Often before release        Often not recovered                                  |
|   Goal         | Target missed      Not necessarily             Reported more often                                  |
|   Reasoning    | Hotfix frequency   Unknown                     Reported higher                                      |
|   Unlinked     | Source             Maya's account              Maya's account                                       |
|   Tests        |                                                                                                     |
|   Actions      | L3@1 remains a conditional hypothesis. Leo's belief: DISPUTED.                                      |
|   History      | H2 remains plausible: queue/load may influence both escalation and delay.                           |
|                | [Event evidence]  [Compare directions]  [Inspect L3]                                                |
| [Views]        |                                                                                                     |
| [Actions]      | DECISION / Should we test interruption policy under these uncertainties?                            |
|                | What makes Support and Engineering choose different actions now?                                    |
| Saved locally  | You can describe both needs or ask for a different route.                                           |
|                | [Describe conflict]  [Give me direct help - asks consultant]                                        |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Keep the qualification visible | Send asks consultant; Enter adds a line.                                |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya answers: Support needs urgent customer issues addressed quickly and thinks that requires inserting
hotfixes immediately. Engineering needs standard releases validated reliably and thinks that requires freezing the
active release. Both want dependable Payments changes and customer service.
EVENT semantic in007 r0009 question007

SCREEN S09 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0009 saved | Examine a necessity assumption | Focus: Response                       |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | CONFLICT CLOUD / scoped necessity claims, all proposed                                              |
|                |                            +-----------------------------------------+                              |
| * Next         |                            | A  Dependable Payments service          |                              |
|   Goal         |                            +-------+-------------------------+-------+                              |
|   Reasoning    |                                    |                         |                                      |
|   Unlinked     |     requires?        +-------------+                         +--------+     requires?               |
|   Tests        |                      |                                                |                             |
|   Actions      | +--------------------+--------------------+      +--------------------+--------------------+        |
|   History      | | B  Serve urgent customer needs          |      | C  Validate standard changes            |        |
|                | | quickly enough                          |      | reliably                                |        |
| [Views]        | +--------------------+--------------------+      +--------------------+--------------------+        |
| [Actions]      |                      |                                                |                             |
|                |                      |  requires?                                     |  requires?                  |
| Saved locally  |                      |                                                |                             |
|                | +--------------------+--------------------+      +--------------------+--------------------+        |
|                | | D  Insert hotfix in active release      |      | D' Keep that active release frozen      |        |
|                | | immediately                             |      | during validation                       |        |
|                | +--------------------+--------------------+      +--------------------+--------------------+        |
|                |                      |                                                |                             |
|                |                      +------------------------------------------------+                             |
|                |                         cannot both hold in this active release window                              |
|                | FOCUS / B requires D? Assumption: quick service needs immediate insertion.                          |
|                | The need matters. Is this action the only way to meet it?                                           |
|                | Acknowledgement alone would not establish that the customer need was served.                        |
|                | [Inspect B requires D]  [Other side's assumptions]  [Explain Cloud]                                 |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Examine a necessity assumption | Send asks consultant; Enter adds a line.                                |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya answers: We could acknowledge within four business hours, triage severity, state when the deployment
decision will be made, freeze active validation and reserve one urgent slot in the next release. Keep the existing
emergency path for genuinely critical incidents.
EVENT semantic in008 r0010 question008

SCREEN S10 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0010 saved | See benefits AND possible harm | Focus: Response                       |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | FUTURE REALITY / I1@1 candidate change / predictions, not observations                              |
|                | +-- CHANGE -------------------------------------------------------------+                           |
| * Next         | | Freeze active validation; reserve one urgent slot in the next release. |                          |
|   Goal         | | Daily triage; timely acknowledgement; existing emergency path retained.|                          |
|   Reasoning    | +---------------------+----------------------------+--------------------+                           |
|   Unlinked     |                       |                            |                                                |
|   Tests        |              expected benefit                possible adverse path                                  |
|   Actions      |                       v                            v                                                |
|   History      | +--------------------------------------+ +--------------------------------------+                   |
|                | | Fewer interruptions / less rework    | | Urgent work waits for the next slot |                    |
| [Views]        | +------------------+-------------------+ +------------------+-------------------+                   |
| [Actions]      |                    | ALL                                | ALL                                       |
|                | +--------------------------------------+ +--------------------------------------+                   |
| Saved locally  | | Saved time usable before release;   | | Wait exceeds legitimate need;       |                     |
|                | | standard work ready; no other delay | | emergency path cannot serve it      |                     |
|                | +------------------+-------------------+ +------------------+-------------------+                   |
|                |                    v prediction                         v prediction                                |
|                | +--------------------------------------+ +--------------------------------------+                   |
|                | | More standard work within 3 days    | | An urgent customer need goes unmet  |                     |
|                | +--------------------------------------+ +--------------------------------------+                   |
|                | Harm remains open: capacity, severity and emergency-path feasibility unknown.                       |
|                | DECISION / What guardrail and response would make a bounded trial acceptable?                       |
|                | [Inspect benefit]  [Inspect harm]  [Trace to goal]  [Other moves]                                   |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to See benefits AND possible harm | Send asks consultant; Enter adds a line.                                |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya chooses Actions > Coaching > Direct help. Preference saved; no call or revision. In Response she types:
Give me a concrete bounded pilot. Queue size, incident mix and change complexity vary; do not claim this isolates a
cause.
EVENT semantic in009 r0011 question009

SCREEN S11 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0011 saved | Choose a bounded pilot | Focus: Response                               |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | RECOMMENDATION / a two-week operational trial, with several interacting changes                     |
|                | Trial the freeze + reserved urgent slot + 09:30 daily triage for Oct 5-16.                          |
| * Next         | Keep the existing critical-incident emergency path.                                                 |
|   Goal         |                                                                                                     |
|   Reasoning    | +-- FORECAST / propose before results ---+ +-- PROTECT ------------------------+                    |
|   Unlinked     | | >=70% standard pilot changes deploy   | | Rollback <=5% deployed pilot cohort |                   |
|   Tests        | | within 3 business days                | | After-hours <=8 engineer-hours/week |                   |
|   Actions      | +---------------------------------------+ | Urgent acknowledgement >=95%/4h     |                   |
|   History      |                                           +-------------------------------------+                   |
|                | Log release-ready/deployment times, queue size, change type, urgent requests,                       |
| [Views]        | interruptions, rechecks, emergency-path use and rule exceptions.                                    |
| [Actions]      | Escalate any breach to an agreed owner; do not expand before review.                                |
|                |                                                                                                     |
| Saved locally  | LIMIT / acknowledging a request does not establish that its need was met.                           |
|                | Historical September comparison will not isolate this policy's effect.                              |
|                | DECISION / Which version are you willing and authorized to run?                                     |
|                | Specify owner, dates, preparation, safeguards and stopping conditions.                              |
|                | [Use this as a draft]  [Change the proposed plan]  [Inspect the harm]                               |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Choose a bounded pilot | Send asks consultant; Enter adds a line.                                        |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya chooses Use this as a draft (local form). She fills Owner: Maya; pilot Oct 5-16; review Oct 19; scope
standard Payments changes release-ready during the window. She retains the 70% forecast, <=5% rollback, <=8h in EACH
week and >=95% urgent acknowledgement within four business hours. September 12/30 is a historical baseline. Escalate
breaches to Maya; pause expansion until review. Use emergency handling for a critical incident and log it. Record
urgent need served or unserved; numeric fulfillment bound unknown. Maya states authority to run this bounded trial and
pause expansion. Before Oct 5 name triage owner/backup and rehearse response, escalation and emergency handling. Roles
must demonstrate all three before start. She activates Save forecast - asks consultant to structure this input. Saving
a forecast is distinct from committing to run it.
EVENT semantic in010 r0012 question010

SCREEN S12 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0012 saved | Original pilot forecast saved | Focus: Response                        |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | P1@1 / saved prospectively Oct 2 / proposed, not yet committed to run                               |
|                | OWNER Maya | Oct 5-16 | Review Oct 19 | no reminder scheduled                                       |
| * Next         | Scope: standard Payments changes marked release-ready Oct 5-16.                                     |
|   Goal         | Forecast: >=70% within 3 business days. September baseline: 12/30 = 40%.                            |
|   Reasoning    | Cohort rule: follow every eligible change through its full 3-day window.                            |
|   Unlinked     | Rollback denominator: deployed eligible changes; no deployment = pending.                           |
|   Tests        | Acknowledgement denominator: urgent requests received during pilot.                                 |
|   Actions      | Protect: rollback <=5%; after-hours <=8h EACH week; acknowledgement >=95%/4h.                       |
|   History      | Calendar: Mon-Fri, 08:00-18:00, Europe/Berlin; excluded closures: none stated.                      |
|                | Oct 19 review flags immature outcomes pending and schedules their data check.                       |
| [Views]        | Escalate any breach to Maya; no expansion before review.                                            |
| [Actions]      | Emergency path allowed for critical incidents; record use, not automatic failure.                   |
|                | Urgent-need fulfillment is observed separately; numeric bound UNKNOWN.                              |
| Saved locally  |                                                                                                     |
|                | +-- READY TO RUN? ------------------------------------------------------+                           |
|                | | Roles named: not started | Roles demonstrate response: unknown         |                          |
|                | | Logging operational: unknown | Stop authority: Maya declares it        |                          |
|                | +-----------------------------------------------------------------------+                           |
|                | DECISION / Can this version be implemented before its trial window?                                 |
|                | [Preparation map]  [Immediate action]  [Original forecast]  [Record reliance]                       |
|                | [Correct the record]  Other participants' agreement remains unknown.                                |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Original pilot forecast saved | Send asks consultant; Enter adds a line.                                 |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya opens Preparation map locally. The prerequisite and transition fragments were authored with the question;
browsing them makes no consultant call.

SCREEN S13 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0012 saved | Preparation / Required states | Focus: Preparation map                 |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | PREREQUISITE TREE / P1@1 / states that must hold, not a task checklist                              |
|                | +-- Pilot operates as specified ----------------------------------------+                           |
|   Next         | | requires ALL the states below; sufficiency of this set is still open  |                           |
|   Goal         | +--------------+-----------------------+------------------+-------------+                           |
| * Reasoning    |                |                       |                  |                                         |
|   Unlinked     | +-------------------------+ +-----------------------+ +------------------------+                    |
|   Tests        | | IO1 Roles acknowledged  | | IO2 Logs operational  | | IO3 Roles demonstrate  |                    |
|   Actions      | | owner + backup          | | timestamps + scope    | | response + escalation  |                    |
|   History      | +-------------------------+ +-----------------------+ | + emergency handling   |                    |
|                | | Obstacle: no cover      | | Obstacle: missing     | +------------------------+                    |
| [Views]        | | Criterion: both roles   | | records               | | Obstacle: ambiguous    |                    |
| [Actions]      | | explain authority       | | Criterion: one sample | | operating rule         |                    |
|                | | Attainment: unknown     | | change + request      | | Criterion: demonstrate |                    |
| Saved locally  | +-------------------------+ | correctly logged      | | all 3 cases correctly  |                    |
|                |                             | Attainment: unknown   | | Attainment: unknown    |                    |
|                |                             +-----------------------+ +------------------------+                    |
|                |                                                                                                     |
|                | IO3 requires IO1; IO1 and IO2 can be prepared in parallel.                                          |
|                | The connector above means requires, not causes. Unknown is not a green check.                       |
|                | Completing a meeting does not establish that either role understands the rule.                      |
|                | [Inspect IO1]  [Inspect IO2]  [Inspect IO3]  [Actions that may create these states]                 |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Live question: Original pilot forecast saved | Draft retained. [Return to question]                                  |
| _                                                                                                                    |
|                                                                                                                      |
| [Return to question]  [Help]  [Actions]                                                                              |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Arrows select  Enter open  Esc back  F1 Help  Ctrl+P Actions                                           |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya selects IO1 and opens Actions that may create these states. Same revision, local.

SCREEN S14 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0012 saved | Immediate action / Why it should work | Focus: Immediate action        |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | TRANSITION TREE / T1@1 expected to create IO1 / a proposed causal step                              |
|                | NEED: a legitimate, understood response and escalation rule before the pilot.                       |
|   Next         | +-- ALL ----------------------------------------------------------------+                           |
|   Goal         | | REALITY: triage response and cover are not yet assigned.               |                          |
|   Reasoning    | | ACTION: Maya names owner + backup, reads back rule and rehearses it.   |                          |
|   Unlinked     | | CONDITIONS: Maya has stated authority; both roles participate;         |                          |
|   Tests        | | wording resolves their authority and response questions.              |                           |
| * Actions      | +----------------------------------+------------------------------------+                           |
|   History      |                                    | LT1: predicted effect                                          |
|                |                                    v                                                                |
| [Views]        |             +-------------------------------------------------+                                     |
| [Actions]      |             | IO1 Roles acknowledge who responds/escalates    |                                     |
|                |             +-------------------------------------------------+                                     |
| Saved locally  | OBSERVE / ask both roles to explain responsibility and backup cover.                                |
|                | FAILURE / if either is unclear, revise and rehearse before starting.                                |
|                |                                                                                                     |
|                | Action execution: NOT STARTED      Expected state: UNKNOWN                                          |
|                | Separate records. A completed action cannot set attainment automatically.                           |
|                | DECISION / What happened when you tried the preparation?                                            |
|                | [Record completed action - asks consultant]  [Record observation separately]                        |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Live question: Original pilot forecast saved | Draft retained. [Return to question]                                  |
| _                                                                                                                    |
|                                                                                                                      |
| [Return to question]  [Help]  [Actions]                                                                              |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Arrows select  Enter open  Esc back  F1 Help  Ctrl+P Actions                                           |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Esc to the question. Maya answers: I have named the triage owner and backup and walked them through the draft.
The rehearsal has not happened, and I have not checked the logs yet.
EVENT semantic in011 r0013 question011

SCREEN S15 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0013 saved | Observe readiness | Focus: Response                                    |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | PREPARATION RECEIPT / Maya's report; no organizational action executed here                         |
|                |                                                                                                     |
| * Next         | +-- ACTION ----------------------------+  +-- EXPECTED STATE -------------------+                   |
|   Goal         | | Owner/backup named; rule read back   |  | Roles can explain and apply rule    |                   |
|   Reasoning    | | Execution: COMPLETED as reported    |  | Attainment: UNKNOWN                 |                    |
|   Unlinked     | +-------------------------------------+  +-------------------------------------+                    |
|   Tests        |         completed action  =/=  observed effect  =/=  pilot improvement                              |
|   Actions      |                                                                                                     |
|   History      | Original P1@1 forecast and dates are unchanged.                                                     |
|                | IO2 logging operational: unknown. IO3 demonstration: unknown.                                       |
| [Views]        | DECISION / Are the required states attained before Oct 5?                                           |
| [Actions]      | What does the rehearsal and sample log check actually show?                                         |
|                |                                                                                                     |
| Saved locally  | [Original forecast]  [Preparation]  [Observation fields]                                            |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Observe readiness | Send asks consultant; Enter adds a line.                                             |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya answers on Oct 2: Both roles correctly explained who responds and when to escalate. They demonstrated
acknowledgement with no deployment estimate, a request needing backup cover and a critical incident requiring the
existing emergency path. All three cases were correct after a wording clarification, which we read back. One sample
change and one sample request were correctly logged with timestamps and scope. This is a rehearsal report, not a pilot
result.
EVENT semantic in012 r0014 question012

SCREEN S16 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0014 saved | Decide on this exact trial | Focus: Response                           |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | READY STATES / reported rehearsal, not proof of live performance                                    |
|                | IO1 owner/backup authority explained: MET according to Maya's report.                               |
| * Next         | IO2 sample change + request logged: MET according to Maya's report.                                 |
|   Goal         | IO3 all three response cases demonstrated: MET according to Maya's report.                          |
|   Reasoning    |                                                                                                     |
|   Unlinked     | +-- P1@1 / ORIGINAL FORECAST --------------------------------------------+                          |
|   Tests        | | Oct 5-16 | >=70% standard changes within 3 business days               |                          |
|   Actions      | | Rollback <=5% | after-hours <=8h EACH week | urgent ack >=95%/4h        |                         |
|   History      | | Escalate to Maya; no expansion before Oct 19 review                    |                          |
|                | +-----------------------------------------------------------------------+                           |
| [Views]        | Reliance: unrecorded. Authority: Maya's declaration; not independently verified.                    |
| [Actions]      | L3@1 remains provisional. Leo's belief remains DISPUTED.                                            |
|                | DECISION / Will you run this exact bounded version?                                                 |
| Saved locally  | [Record reliance on P1@1]  [Revise forecast - asks consultant]  [Leave undecided]                   |
|                | Record reliance is local; it records a decision, not execution or consensus.                        |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Decide on this exact trial | Send asks consultant; Enter adds a line.                                    |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya opens Record reliance on P1@1. The panel repeats the exact window, forecast, safeguards and actor, with
no substantive value preselected. She selects Will run this bounded test and activates Record reliance.
EVENT local r0015 target=P1@1 dimension=reliance value=will_run actor=Maya
Receipt: r0015 saved. Maya will run P1@1. Leo's dispute unchanged; no group agreement inferred. No consultant call.
Live the current question now uses its stored continuation: run P1 and return with observations on Oct 19.
ACTION: Maya opens Goal from the sidebar to check how this trial relates to the system goal.

SCREEN S17 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0015 saved | Goal / What success requires | Focus: Goal                             |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | GOAL TREE / partial requirements / current goal G1@1                                                |
|                | +-- G1 -----------------------------------------------------------------+                           |
|   Next         | | >=80% of Oct 1-30 release-ready Payments changes deploy within 3 days. |                          |
| * Goal         | | Protect rollback <=5%; after-hours <=8h in each week.                  |                          |
|   Reasoning    | +---------------------+----------------------+--------------------------+                           |
|   Unlinked     |                requires?                requires?                                                   |
|   Tests        | +------------------------------------+ +---------------------------------------+                    |
|   Actions      | | Adequate usable validation and     | | Feasible release access before each   |                    |
|   History      | | recovery time for the due changes  | | change's three-day deadline            |                   |
|                | +------------------------------------+ +---------------------------------------+                    |
| [Views]        | Warrant: these changes need completed validation and an eligible release.                           |
| [Actions]      | These requirements are proposed in this scope. Others are not yet mapped.                           |
|                | Freezing an active release is a method to test, not itself a necessary condition.                   |
| Saved locally  |                                                                                                     |
|                | TRACE / P1@1 tests I1@1; I1 addresses interruption/rework; that route threatens G1.                 |
|                | Typed trace references are not causal arrows between tools.                                         |
|                | PILOT >=70%  =/=  SYSTEM GOAL >=80%  |  neither is yet an observed result.                          |
|                | [Inspect requirement]  [Trace P1 to G1]  [Return to question]                                       |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Live question: Decide on this exact trial | Draft retained. [Return to question]                                     |
| _                                                                                                                    |
|                                                                                                                      |
| [Return to question]  [Help]  [Actions]                                                                              |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Arrows select  Enter open  Esc back  F1 Help  Ctrl+P Actions                                           |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Actions > Export portable commons > path ./deploy-flow-before-pilot.reasoncase > Export. Local receipt:
exported r0015 with ancestry, source inputs, exact positions, P1 original forecast and cursor. Actions > Save and quit
returns to the shell and releases the writer lock.
$ reason-commons inspect ./deploy-flow-before-pilot.reasoncase --offline
Offline read-only inspection: r0015; original P1 forecast; Maya relies on P1@1; Leo disputes L3@1. Schema, references,
ancestry and content hashes pass. This command does not run the consultant.
Monday, October 19, 2026 - the following outcomes are simulated.
$ reason-commons resume ./deploy-flow-case

SCREEN S18 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0015 saved | Resume and review P1 | Focus: Response                                 |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week                                   |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | WELCOME BACK / saved state restored; no consultant call                                             |
|                | P1@1 original forecast stays pinned while you record results.                                       |
| * Next         | +-------------------------------+---------------------------------------+                           |
|   Goal         | | Delivery                      | >=70% within 3 business days          |                           |
|   Reasoning    | | Rollback                      | <=5% deployed eligible cohort         |                           |
|   Unlinked     | | After-hours                   | <=8 engineer-hours EACH week          |                           |
|   Tests        | | Urgent acknowledgement        | >=95% within 4 business hours         |                           |
|   Actions      | +-------------------------------+---------------------------------------+                           |
|   History      | Window Oct 5-16 | owner Maya | review Oct 19 | no reminder scheduled                                |
|                | Preparation: reported met. Pilot execution and effects: awaiting observations.                      |
| [Views]        | System goal: >=80% October cohort; end-of-month attainment not yet known.                           |
| [Actions]      | DECISION / Keep, change or stop this trial?                                                         |
|                | Supply outcomes, whether the rule was followed and comparison limitations.                          |
| Saved locally  | Do any eligible changes still lack their full three-day follow-up?                                  |
|                | [Original forecast]  [Outcome fields]  [Sources]  [Other moves]                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Resume and review P1 | Send asks consultant; Enter adds a line.                                          |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Maya enters: Pilot ran Oct 5-16. Freeze followed; 09:30 triage on all ten working days; urgent slot available
each release window; one Sev-1 used the emergency path. All 24 eligible standard changes have complete follow-up and
reached production; 18 within three business days (75%). One rolled back (1/24). After-hours 7h in week one and 8h in
week two. Ten urgent requests; nine acknowledged within four business hours (90%). The late one waited almost seven
hours for an engineer's deployment estimate. Queue smaller in week two; broadly similar mix but one fewer large
migration than September. We escalated the acknowledgement miss and did not expand. Urgent need fulfillment has not
been assessed consistently; retain it as unknown.
EVENT semantic in013 r0016 question013

SCREEN S19 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0016 saved | Review the unchanged forecast | Focus: Response                        |
+----------------------------------------------------------------------------------------------------------------------+
| ! P1 acknowledgement BREACH 90% <95% | Goal >=80% not demonstrated | No expansion                                    |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | ! BREACH / urgent acknowledgement 9/10 = 90%, below original 95% bound                              |
|                | Do not expand. Escalated to Maya according to her report.                                           |
| * Next         |                                                                                                     |
|   Goal         | MEASURE                  ORIGINAL P1@1                 REPORTED RESULT                              |
|   Reasoning    | -----------------------  ----------------------------  ---------------------------                  |
|   Unlinked     | Within 3 business days   >=70%; September 12/30 = 40%   18/24 = 75%   SUPPORTED                     |
|   Tests        | Rollback                 <=5% deployed pilot cohort    1/24 = 4.2%   WITHIN BOUND                   |
|   Actions      | After-hours EACH week    <=8 engineer-hours            7h; 8h        WITHIN BOUND                   |
|   History      | Urgent acknowledgement   >=95% within 4 business hours  9/10 = 90%    BREACH                        |
|                |                                                                                                     |
| [Views]        | P1 forecast saved Oct 2: unchanged. Scope/denominators above match the report.                      |
| [Actions]      | System G1 >=80% October cohort: NOT DEMONSTRATED; pilot target is different.                        |
|                | Fidelity: freeze + ten triages + urgent slot reported; emergency use logged.                        |
| Saved locally  | Lower queue, migration mix and simultaneous changes limit causal attribution.                       |
|                | Leo's L3@1 dispute remains. Customer need fulfillment remains UNKNOWN.                              |
|                |                                                                                                     |
|                | DECISION / What must change before another bounded trial?                                           |
|                | Why did the unacknowledged request wait?                                                            |
|                | [Inspect breach]  [Original P1]  [Evidence and limits]  [Compare H1/H2]                             |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Review the unchanged forecast | Send asks consultant; Enter adds a line.                                 |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Before answering, Maya opens Inspect breach. This selection does not erase the delivery result or change the
forecast.

SCREEN S20 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0016 saved | Breach / Follow the adverse path | Focus: Breach                       |
+----------------------------------------------------------------------------------------------------------------------+
| ! P1 acknowledgement BREACH 90% <95% | Original P1 preserved | No expansion                                          |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | NEGATIVE BRANCH / a reported acknowledgement failure, separate from need fulfillment                |
|                | +-- ALL / NB2@1 --------------------------------------------------------+                           |
|   Next         | | Support waits for a firm deployment estimate before acknowledging.    |                           |
|   Goal         | | Estimate remains unavailable beyond the four-business-hour bound.     |                           |
| * Reasoning    | +----------------------------------+------------------------------------+                           |
|   Unlinked     |                                    | proposed mechanism from report                                 |
|   Tests        |                                    v                                                                |
|   Actions      |                +-----------------------------------------+                                          |
|   History      |                | Acknowledgement sent almost 7h later    |                                          |
|                |                | This request misses the 4h protection   |                                          |
| [Views]        |                +-----------------------------------------+                                          |
| [Actions]      | P1 proposed >=95% timely acknowledgements. Reported result: 9/10 = 90%.                             |
|                | This mechanism does not settle whether the customer's urgent need was served.                       |
| Saved locally  | Earlier NB1 (urgent work waits) also remains: fulfillment data UNKNOWN.                             |
|                | Acknowledgement and fulfillment are separate branches and observations.                             |
|                | [Source input]  [NB1 urgent need]  [Return to question]                                             |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Live question: Review the unchanged forecast | Draft retained. [Return to question]                                  |
| _                                                                                                                    |
|                                                                                                                      |
| [Return to question]  [Help]  [Actions]                                                                              |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Arrows select  Enter open  Esc back  F1 Help  Ctrl+P Actions                                           |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Esc returns to the same question. Maya answers: Support believed a useful acknowledgement needed a firm fix
time. While Engineering investigated, nothing was sent. We can acknowledge receipt, name an owner and give the next-
update time without inventing a deployment promise.
EVENT semantic in014 r0017 question014

SCREEN S21 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Maya (declared) | r0017 saved | Change the assumption and test it | Focus: Response                    |
+----------------------------------------------------------------------------------------------------------------------+
| ! P1 historical breach retained | Follow-up proposed | No expansion                                                  |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | ASSUMPTION TO CHALLENGE / Useful acknowledgement requires a firm deployment estimate.               |
|                | Proposed communication change I2@1: acknowledge receipt; name owner;                                |
| * Next         | give next-update time while investigation and deployment decision continue.                         |
|   Goal         |                                                                                                     |
|   Reasoning    | +-- EXPECTED BENEFIT ------------------+  +-- STILL AT RISK --------------------+                   |
|   Unlinked     | | Estimate missing no longer blocks    |  | Timely acknowledgement can coexist |                    |
|   Tests        | | acknowledgement before 4h            |  | with an unserved urgent need        |                   |
|   Actions      | +--------------------------------------+  +-------------------------------------+                   |
|   History      | Retain freeze, urgent slot, triage, emergency path and existing protections.                        |
|                | Observe acknowledgement TIME and whether the agreed customer NEED was served.                       |
| [Views]        | A numeric acceptable fulfillment bound has not been agreed.                                         |
| [Actions]      |                                                                                                     |
|                | DECISION / Who will own a follow-up with what prediction and review window?                         |
| Saved locally  | [Draft follow-up]  [Inspect original breach]  [Ask a different question]                            |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Change the assumption and test it | Send asks consultant; Enter adds a line.                             |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Switch declared speaker to Leo. Leo enters: I will own and run P2 October 20-30, review October 30. Support
acknowledges within four business hours, names owner and next-update time without requiring a deployment estimate.
Keep all release-flow rules, emergency path, rollback <=5% and after-hours <=8h each week. Predict >=95% timely
acknowledgements and >=70% standard delivery within three business days. Record each agreed customer need and whether
it was served, plus exceptions. Numeric fulfillment bound remains unknown. Escalate an unserved urgent need or
existing guardrail breach to me; pause expansion until review. I have authority for this bounded follow-up. That does
not mean I agree with L3. At the October 30 review mark any immature delivery outcomes pending; review the complete
cohort after its three-day window closes.
EVENT semantic in015 r0018 question015

SCREEN S22 120x40
+----------------------------------------------------------------------------------------------------------------------+
| deploy-flow | Leo (declared) | r0018 saved | Follow-up saved; open issues remain | Focus: Response                   |
+----------------------------------------------------------------------------------------------------------------------+
| P1 breach retained | P2@1 committed by Leo | System goal not yet demonstrated                                        |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | P2@1 / prospective follow-up / Leo's explicit bounded commitment                                    |
|                | Oct 20-30 | review Oct 30; incomplete three-day windows pending, not failures                       |
| * Next         | Owner/stop authority: Leo declares both. No reminder scheduled.                                     |
|   Goal         | Acknowledge receipt + owner + next-update time; no final estimate required.                         |
|   Reasoning    | Retain freeze, reserved urgent slot, daily triage and existing emergency path.                      |
|   Unlinked     | Forecast: urgent acknowledgement >=95%/4h; standard delivery >=70%/3 days.                          |
|   Tests        | Protect: rollback <=5% deployed eligible cohort; after-hours <=8h EACH week.                        |
|   Actions      | Same calendar and cohort rules as P1; follow immature outcomes to completion.                       |
|   History      | Record agreed urgent customer need and whether it was served; bound UNKNOWN.                        |
|                | Escalate any unserved urgent need or guardrail breach; no expansion before review.                  |
| [Views]        |                                                                                                     |
| [Actions]      | +-- WHAT THIS DECISION DOES NOT SETTLE ----------------------------------+                          |
|                | | P1 acknowledgement breach remains recorded. Original forecast unchanged.|                         |
| Saved locally  | | Leo still DISPUTES L3@1. No causal conclusion or group agreement inferred.|                       |
|                | | System October goal is not yet demonstrated. P2 effects not observed.   |                         |
|                | +-----------------------------------------------------------------------+                           |
|                | NEXT / Run this bounded follow-up; return with comparable observations.                             |
|                | [Original P1 + outcome]  [P2 forecast]  [Open issues]  [History]                                    |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Follow-up saved; open issues remain | Send asks consultant; Enter adds a line.                           |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Leo opens History, selects r0016, then Return to question. The selected revision is historical; the live
response target stays Follow-up saved. Actions > Consultant calls shows 15 completed semantic calls. All inspection,
navigation, preference changes, export, quit and resume made zero calls. The three structured local decisions created
revisions without consultant responses.
The next two screens demonstrate resize of saved L3@1 at r0018, with the question and its draft retained. They are the
SAME inference as S05; the current breach/dispute remain visible. They are not new sessions or additional calls.

SCREEN S23 80x24
+------------------------------------------------------------------------------+
| deploy-flow | Leo | r0018 saved | L3@1 | Focus: L3                           |
+------------------------------------------------------------------------------+
| P1 breach retained | L3 disputed | Goal >=80% not demonstrated               |
+------------------------------------------------------------------------------+
| L3 hypothesis / Leo DISPUTES / H2 reversal also unresolved                   |
| +-- ALL / L3@1 ---------------------------------------------------------+    |
| | Validation is interrupted and must be repeated for this change.       |    |
| | Net unrecovered recheck time exceeds slack before release cutoff.     |    |
| | No eligible later release occurs before its three-day deadline.       |    |
| +-----------------------------------+-----------------------------------+    |
|                                     | L3: hypothesis                         |
|                                     v                                        |
|             +-----------------------+----------------------+                 |
|             | This standard change misses the 3-day target |                 |
|             +----------------------------------------------+                 |
+------------------------------------------------------------------------------+
| Live: Follow-up saved; open issues remain | Draft retained                   |
| _                                                                            |
|                                                                              |
| [Evidence]  [Compare H2]  [Return]                                           |
+------------------------------------------------------------------------------+
| Tab controls  Enter open  Esc back  F1 Help  Actions                         |
+------------------------------------------------------------------------------+

SCREEN S24 40x24
+--------------------------------------+
| r0018 saved | Leo | L3 | F:L3        |
+--------------------------------------+
| P1 breach retained; L3 disputed      |
+--------------------------------------+
| L3 hypothesis; Leo disputes it.      |
| IF ALL (3 premises):                 |
| 1 Validation interrupted;            |
|   rechecks needed for this change.   |
| 2 Net unrecovered recheck time       |
|   exceeds release-cutoff slack.      |
| 3 No eligible later release before   |
|   its three-business-day deadline.   |
| THEN standard change misses target.  |
| H2: delay may cause escalation.      |
| [Evidence] [Compare] [Explain]       |
+--------------------------------------+
| Live question | Draft retained       |
| _                                    |
|                                      |
| [Return] [Views] [Actions]           |
+--------------------------------------+
| Tab  Enter open  Esc back  Help      |
+--------------------------------------+

ACTION: Restoring 120x40 restores the same selected L3 version, semantic scroll anchor, response draft and focus. No
commons change. Actions > Export portable commons > ./deploy-flow-after-review.reasoncase > Export; Actions > Save and
quit.
$ reason-commons inspect ./deploy-flow-after-review.reasoncase --offline
Offline inspection: r0018. P1 delivery 18/24 = 75% supports its original >=70% forecast; P1 acknowledgement 9/10 = 90%
breaches its original >=95% bound. Full October goal remains unestablished. P2@1 prospective; owner Leo; Oct 20-30.
Fulfillment bound unknown; Leo disputes L3@1; causal attribution provisional. Forecasts, observations, ancestry,
references and hashes preserved.
CONSULTANT CALLS 15: in001 through in015; all completed in this specimen.
18 reasoning revisions = 15 semantic commits + 3 structured local decisions.
No deployment, notification, assignment or reminder was executed by the application.
```

## 10. TUI cross-tool correction and action review

```text
ILLUSTRATIVE CROSS-TOOL TUI CORRECTION AND ACTION REVIEW
Delivery profile: p5 cumulative roadmap; independent fictional fixture.
The r0000 fixture contains goal G1, CRT L1@1, Cloud A4@1, FRT I1@1, prerequisite IO2@1 and action T1@1. Dependencies
are stored exact references, not discovered by a renderer. Frames are 120x40; keyboard and focus follow the main TUI
specimen.
$ reason-commons resume ./setup-review-fixture
EVENT start r0000

SCREEN R01 120x40
+----------------------------------------------------------------------------------------------------------------------+
| setup | Sam (declared) | r0000 saved | Start / Challenge the setup route | Focus: Response                           |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: timely delivery + agreed throughput floor | Reviews and uncertainty remain visible                             |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | CURRENT CLAIM / L1@1: every urgent insertion adds setup time (hypothesis).                          |
|                | DECISION / What counterexample would change this explanation or admission rule?                     |
| * Next         | [Inspect L1]  [Sources]  [Cross-tool references]                                                    |
|   Goal         |                                                                                                     |
|   Reasoning    | Stored future I1@1: check setup/delivery consequences before admission.                             |
|   Unlinked     | Stored Cloud A4@1: every sequence change jeopardizes due work (proposed).                           |
|   Tests        | IO2@1 setup information adequate: UNKNOWN. T1@1 authority meeting: NOT STARTED.                     |
|   Actions      | These exact formulations can be inspected; none is established by its placement.                    |
|   History      |                                                                                                     |
|                |                                                                                                     |
| [Views]        |                                                                                                     |
| [Actions]      |                                                                                                     |
|                |                                                                                                     |
| Saved locally  |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Start | Send asks consultant; Enter adds a line.                                                         |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Sam submits: A same-setup insertion added no setup time. Qualify the causal route to insertions adding setup
changes. We still have late orders. Review whether the admission rule can allow setup-neutral jobs.
EVENT semantic in001 r0001 question001

SCREEN R02 120x40
+----------------------------------------------------------------------------------------------------------------------+
| setup | Sam (declared) | r0001 saved | Correction and dependent review | Focus: Response                             |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: timely delivery + agreed throughput floor | Reviews and uncertainty remain visible                             |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | CHANGE / source in001, Sam's report / late-order report UNCHANGED                                   |
|                | +-- BEFORE / L1@1 ----------------------+ +-- AFTER / L1@2 -----------------------+                 |
| * Next         | | Every urgent insertion adds setup time| | Only insertions adding setup changes |                  |
|   Goal         | | Hypothesis                            | | use this setup-loss route.            |                 |
|   Reasoning    | +---------------------------------------+ +---------------------------------------+                 |
|   Unlinked     | A setup-neutral insertion can still consume PROCESSING time: separate route.                        |
|   Tests        |                                                                                                     |
|   Actions      | +-- REGISTERED CONSEQUENCES / current r0001 -----------------------------+                          |
|   History      | | L1@2  ---- used by ---- Cloud A4@1: REVIEW NEEDED                      |                          |
|                | |       ---- used by ---- FRT I1@1:   REVIEW NEEDED                      |                          |
| [Views]        | |       ---- used by ---- PRT IO2@1:  REVIEW NEEDED                      |                          |
| [Actions]      | +-----------------------------------------------------------------------+                           |
|                | Trace labels are dependencies, not causal arrows. List is not exhaustive reality.                   |
| Saved locally  | Past reviews remain on OLD versions. No belief, assent or test reliance transfers.                  |
|                | T1 execution unchanged; pilot effects UNOBSERVED; no delivery gain established.                     |
|                | DECISION / Can admission distinguish setup-neutral work AND its processing load?                    |
|                | What information and accuracy would support that decision?                                          |
|                | [Compare versions]  [Review Cloud]  [Review future]  [Review prerequisite]                          |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Correction and dependent review | Send asks consultant; Enter adds a line.                               |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Sam opens Compare versions, then Esc. Same question, draft and scroll restored; no call. He submits: Sponsor
held the authority meeting and named owner/backup. Record T1 completed. We have not checked that roles understand
escalation or can apply the admission rule.
EVENT semantic in002 r0002 question002

SCREEN R03 120x40
+----------------------------------------------------------------------------------------------------------------------+
| setup | Sam (declared) | r0002 saved | Observe what the action achieved | Focus: Response                            |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: timely delivery + agreed throughput floor | Reviews and uncertainty remain visible                             |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | ACTION T1@1 / reported by Sam                                                                       |
|                | +------------------------------------+  +---------------------------------------+                   |
| * Next         | | Meeting and naming: COMPLETED     |  | Roles acknowledge authority: UNKNOWN |                     |
|   Goal         | +------------------------------------+  +---------------------------------------+                   |
|   Reasoning    | Completion cannot set the expected state automatically.                                             |
|   Unlinked     | Observe: both roles explain response, escalation and backup cover.                                  |
|   Tests        | If either fails: clarify authority and rehearse; retain the failure record.                         |
|   Actions      |                                                                                                     |
|   History      | Setup-information adequacy remains UNKNOWN. Registered reviews remain open.                         |
|                | DECISION / What did the roles demonstrate rather than merely attend?                                |
| [Views]        | [Observation fields]  [Action rationale]  [Open dependent reviews]                                  |
| [Actions]      |                                                                                                     |
|                |                                                                                                     |
| Saved locally  |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Observe what the action achieved | Send asks consultant; Enter adds a line.                              |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Sam submits: Both roles explained escalation correctly in rehearsal. I will run a small supervised test under
my stated authority while setup accuracy remains uncertain. Retain that uncertainty and admission-rule review; do not
expand on this rehearsal alone.
EVENT semantic in003 r0003 question003

SCREEN R04 120x40
+----------------------------------------------------------------------------------------------------------------------+
| setup | Sam (declared) | r0003 saved | Bounded decision under uncertainty | Focus: Response                          |
+----------------------------------------------------------------------------------------------------------------------+
| Goal: timely delivery + agreed throughput floor | Reviews and uncertainty remain visible                             |
+----------------------------------------------------------------------------------------------------------------------+
| Reason Commons | Authority state: MET according to reported rehearsal; real pilot UNOBSERVED.                        |
|                | Sam's explicit bounded intention recorded; authority is his declaration.                            |
| * Next         | Setup accuracy: UNKNOWN. Admission-rule and dependent reviews: OPEN.                                |
|   Goal         | Original claims, observations and positions remain attached to their versions.                      |
|   Reasoning    | No belief or consensus inferred from the willingness to test.                                       |
|   Unlinked     |                                                                                                     |
|   Tests        | DECISION / Is the accuracy criterion adequate for this supervised trial?                            |
|   Actions      | Specify accuracy criterion, scope and stopping observation before operation.                        |
|   History      | A willingness to test has not filled these missing conditions.                                      |
|                | [Unresolved reviews]  [Original forecast]  [Exact versions]                                         |
| [Views]        |                                                                                                     |
| [Actions]      |                                                                                                     |
|                |                                                                                                     |
| Saved locally  |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
|                |                                                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Response to Bounded decision under uncertainty | Send asks consultant; Enter adds a line.                            |
| _                                                                                                                    |
|                                                                                                                      |
| [Send]  [Explain this]  [Other moves]  [Actions]                                                                     |
+----------------------------------------------------------------------------------------------------------------------+
| Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions                                                     |
+----------------------------------------------------------------------------------------------------------------------+

ACTION: Actions > Consultant calls, then Save and quit. Local.
CONSULTANT CALLS 3: in001 through in003.
3 reasoning revisions = 3 semantic commits + 0 structured local decisions.
```

## 11. Accessible ordered presentation

# Accessible ordered presentation

Reason Commons has one set of human actions. The default is the spatial TUI;
`reason-commons new` or `resume` with `--accessible` selects ordered text for a
reader that cannot use alternate-screen redrawing. This is a presentation of
the same workspace, with the same records, explicit submission, attribution,
version validation and recovery. It has no command prompt or phrase parser.

Use a stable reading order: commons/save/actor/view/focus, urgent status, decision,
complete question and relevant context, what the last reply proposes (each
record with its source, under "Proposed, not yet in the model"), reasoning as
relation sentences or an aligned table, local evidence/actions, Response, Send,
other destinations. The Backlog reads as an ordered list in which each entry says
what it waits for, and its Accept, Reject, Still holds and Undo controls are the
same labeled controls as in the spatial TUI.
Describe each control by label, role, consequence and current focus. Announce
focus changes and important new status once. Never announce each animation or
reprint the entire commons on every keystroke. Append an explicit replacement section
on meaningful view changes; identify superseded sections so scrollback is not
mistaken for current state. An optional Repeat current view control is local.

For example, the same pilot review can read in this order:

```text
Reason Commons | forge | Sam (declared) | r0004 saved
Review P1 | Focus: Review results
Attention: urgent acknowledgement 90% against original >=95%: BREACH.
Decision: adapt the trial; expansion remains stopped.
Delivery: original >=80%; reported 40/50 = 80%. Pilot target supported.
System goal: >=90%; remains unmet.
Evidence: participant report; supplier comparability uncertain.
Controls: Inspect sources (local), Explain this (local), Return to question.
Response editor: retained draft; Enter adds a line.
Send (asks consultant), Other moves, Views, Actions, Help.
```

Tab/Shift+Tab moves to labeled controls, arrows select list entries, Enter/Space
activates them, and Esc returns while retaining the draft. Printable keys edit
Response or an explicitly focused filter. Enter in Response adds a newline;
only activating Send submits. Focus announcements must distinguish the editor
from Send. Multiline text needs no escape syntax. Selecting a list item and
activating it remains distinct from typing a number as an answer. This keyboard
model also works without color, cursor-addressed panels or Unicode borders.

Read graphs as exact typed relations: all joint premises, output, conditions,
scope, warrant, support, disagreement and alternative routes. A relation sentence
may occupy several sections; explicitly mark continuation and keep premises
reachable before judgment. Historical wording and current response target remain
distinct. Compare original forecasts with results using labeled rows when aligned
columns are unsuitable. Never reduce an adverse path to a success-only summary.

At less than 40x24 retain state and offer resize or this ordered presentation.
S49 covers narrow ordered context; S50 equivalent relation text; S51 drafts;
S54-S71 focus/selection/target behavior; S115-S120 deliberate submission, restoration
and recovery; S135-S150 decisions about proposals. The participant gates in delivery-phases.md include assistive
technology users. These requirements need implementation and actual reader tests;
a text specimen or passing document check is not evidence of accessibility.
