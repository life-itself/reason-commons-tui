# Reason Commons TUI and reasoning rendering contract

The first usable Reason Commons interface is a persistent terminal workspace. It
keeps the current decision, question and material context visible while people
inspect and challenge reasoning. This contract supersedes the earlier proposal
and command-driven default. The main spec, phases, manifest and acceptance features
now include that decision.

Read [the canonical Payments journey](example-tui-session.txt),
[the smaller v1 journey](example-mvp-session.txt) and
[the correction journey](example-review-session.txt). These are authored,
fictional examples, not recordings of software. [TUI-DESIGN.md](../TUI-DESIGN.md) declares project
archetypes, patterns, keyboard adaptations and visual direction.

## Information in front of the user

A settled screen MUST answer: where am I, what are we deciding, what should I
attend to, what is uncertain, what can I do next, and has my contribution been
saved? Show one recommended reasoning move with visible alternative routes.
Destinations are Next, Backlog, Goal, Reasoning, Unlinked, Tests, Actions and History.
They are not stages. No tour, expert mode, assent, vocabulary lesson or prescribed
answer can block browsing, correction, direct help or exit.

First use shows a response editor and enough instruction to send, inspect and
return. Explain an operator when it first appears. Explain this opens stored
public rationale and a worked reading of the CURRENT fragment; Help explains
controls. Neither silently requests a new explanation from the consultant.
A requested new explanation is labeled asks consultant before activation.

Pin save status, commons, declared actor, view and focused control in the header,
and a short goal/safeguard context band. Pin an active breach with bound and
actual value in affected views; retain it as historical when a follow-up begins.
Repeat scope, forecast, baseline and qualification beside the judgment they
affect. If they cannot fit, label the view an overview and provide the complete
relation before asking for endorsement. Do not pin all commons facts everywhere.

## Three depths over the same records

| Depth | Display | Action |
|---|---|---|
| Work now | Question, decision, complete local inference or comparison, uncertainty and response | Answer, correct, choose another move |
| Explain this | Why the question helps, how to read these premises, a useful challenge | Inspect locally; restore question and draft |
| Explore | Branch index, spatial map or aligned routes, selected-object inspector, sources, positions and changes | Select, inspect, challenge, trace dependencies |

All depths derive from one frozen revision and exact object versions. The
consultant authors task and presentation references; the local renderer resolves
them. Layout code cannot supply missing causes, warrants, discriminators,
favorable predictions or human agreement.

## The terminal is a canvas

120×40 is the primary target. Use 12–16 columns for destinations and the remaining
width for reasoning. A right inspector fits only when decisive labels remain
readable. S05A shows branch index, map and relationship evidence together; S05B works
through release slack and later-release availability without inventing commons evidence. A
Cloud needs both sides visible; future review needs benefits and material harms
together. Do not reduce these to inline chains with most of the terminal unused.

Allocate node interiors, independent branches and connector gutters deliberately.
Boxes identify propositions; an outer ALL boundary identifies a joint inference.
Route around text and finish at explicit ports. Avoid ambiguous crossings.
Geometry is not evidence, blame, rank, consensus, elapsed time or a diagnosis of
the system constraint. Shared nodes, multiple parents and temporal feedback
must be supported; a strict tree data structure is insufficient.

At 80×24 stack auxiliary panes and use complete local relations or comparison
tables. At 40×24 use sentence records with explicit IF ALL / THEN. S23 and S24
preserve the three premises, outcome and dispute from S05. Expand-to-Focus keeps
the same target; collapse restores layout/selection. Readable logic takes
priority over drawing boxes at small sizes.

Scrollable content shows position and continuation. A conclusion visible alone
MUST say its premises are above, rather than appear to be a complete argument.
A decisive input cannot remain collapsed during judgment. Below 40×24 retain the
draft and offer resize or linear presentation. Resize preserves semantic anchor,
selected object, editor caret and live target; it never restarts or consults.

## Typed visual grammar

| Tool and user-facing label | Required meaning | Useful question |
|---|---|---|
| Goal Tree — What success requires | Parent requires each child; warrant, unknown attainment, shared references and unmapped requirements explicit | Could success occur without this condition here? |
| CRT — Why this happens | Complete causes inside ALL, one labeled output, hypotheses, conditions and rival routes | When would this route fail to produce the effect? |
| Cloud — What makes this a conflict | Objective, equal treatment of needs/actions, requires links, scoped conflict and selected assumption | Is this action the only way to meet the legitimate need? |
| FRT — What the change may produce | Candidate change, conditional benefit and material negative branch together; predictions labeled | What could defeat the benefit or harm another need? |
| PRT — What must be achieved first | Obstacles, required states, criteria and justified dependencies; parallel preparation shown | Is this state demonstrated, or has an action merely finished? |
| TT — Why this action should work | Reality, need, performed action and conditions, expected state, observation and failure response | What would establish the expected effect? |

Negative branches are causal paths in future analysis, not a seventh mandatory
stage. Acknowledgement and customer-need fulfillment are distinct. Feedback
uses dated or lagged episodes. Cross-tool references say addresses, tests,
implements or depends on; they are excluded from causal traversal. Tracing to
the goal cannot prove attainment.

A joint inference is stored as one relation with all inputs and one output,
not several ordinary edges whose lines touch. Necessity and conflict have
separate types. Node evidence and relation warrant are independent. Report,
hypothesis, prediction, review freshness, execution and attainment are independent
fields. Membership is proposed, in the model, or out of it (rejected or undone),
never true/false; inside the model, Unlinked means not yet connected (legacy WIP
IDs remain valid).

## Inspect and correct the exact object

Select before acting. The inspector shows full wording/version, role, scope,
inputs/output or adjacent relationships, warrant/mechanism, evidence method/date/
denominators, limitations, objections, positions and history. Every appearance
references the same record. Search full wording and exact IDs; label historical
matches and retain the live question. No normal journey requires typing IDs.

Correction R02 shows before/after wording and registered dependent reviews.
Retain old reviews and positions on old formulations. Flag exact dependencies
mechanically; label other consequences as review suggestions. Do not claim to
find every real-world consequence. A correction changes reasoning, not an
already recorded observation or organizational outcome.

Positions use independent Wording, Belief and Test reliance controls with no
substantive choice preselected. Every save names actor and exact formulation or
test version; historical targets are explicit. Silence, inspection, typing access
or willingness to test cannot imply belief, authority or group agreement.
Speaker labels are declarations, not authentication.

## Proposals, the backlog and undo

A reply's proposals appear first where the speaker still knows what they meant:
Next step draws them under the new question, as the trees would draw them, beside
the words they came from, labelled proposed and not yet in the model, with Accept
all and Backlog. Under automatic acceptance the same place says what entered the
model with the reply and that History can undo it. A proposal is never drawn as
part of a tree; the Trees view shows the model and a count of what waits.

The Backlog view lists proposals and review flags in decision order (main
specification, section 2F). Each row reads as the record it would become, with its
tree or kind, the reply it came from and what it waits for. A proposed new goal is
marked decide first. A review flag names the change that raised it. Selecting a
row opens its details: the exact proposed record (a new version shows old and new
wording), its source words, what it cites, and how its tree would read with it,
the proposal set in place among accepted statements and marked proposed. Accept,
Reject and, on a flag, Still holds act on the selected row; Accept all acts on
everything one reply proposed. When an action takes other records with it, a
confirmation lists every one before anything changes; a single ready proposal
needs no confirmation. A rejection is final and says so.

History shows each decision as a step: who accepted, rejected or undid what, and
whether under the automatic setting. An accepted step offers Undo; its
confirmation lists what leaves the model with it, the waiting proposals it closes
and the records it flags, and says the undo is final. Restore reasoning (p3) is a
different, later action. Accepting is not agreement: no control combines admission
with endorsement, reliance or execution, and silence admits nothing.

## Interaction and asynchronous behavior

Exactly one control owns keyboard focus; name it and mark it visually. Selection
is a separate marker. Tab/Shift+Tab traverse controls; arrows stay within the
focused editor/list/map. All printable keys are literal in editors, including
numbers, question marks, q, slashes and command-looking text. Enter adds a newline in
Response; Tab to Send and Enter submits once. Paste cannot submit. Modified-Enter
is an optional accelerator, never required.

Esc leaves editor focus for browsing without losing text. Esc from inspection
restores view, selection, scroll, actor-and-question-bound draft and caret. Switching speakers
retains drafts with their original actor; another actor cannot submit them
accidentally. Preferences do not change reasoning. Actions is visible and
keyboard reachable; Ctrl+P accelerates it. Printable keys filter the palette;
arrows select. Every important action has a path without syntax.

Stored navigation/explanation/export says local. Send, a new explanation or
another consultant intervention says asks consultant. Explicit structured local
decisions can create revisions without consultant responses. Decisions about
proposals stay available while a reply is pending and do not make it stale. A
clearly requested consultant alternative needs no redundant second confirmation.

Retain input durably before requesting a response. Show input retained separately
from revision saved. Keep inspection usable while waiting. Completion shows
Answer ready without taking focus; returning offers the validated next question.
Failure retains input and draft, identifies retention/provider/commit failure
and offers the appropriate retry. At-most-once application and stale-version
checks apply to every presentation. Exit restores terminal cursor and shell.

## Forecasts and review

Show scope, calendar, units, denominators, observation window and review date
before saving. A review date does not schedule a reminder. Forecast correction
creates another version; it cannot rewrite the original after results arrive.
A rolling cohort's immature final outcomes are pending at review, with complete
follow-up required before claiming attainment. Missing results are not automatic
failures or successes.

Align ORIGINAL forecast with actual row for row, including every protection,
fidelity and comparison limitation. Pin a breach despite delivery improvement.
Distinguish pilot target from system goal and correlation from cause. Follow-up
retains the prior forecast and breach. P1's 75% meets 70% but does not demonstrate
the 80% October goal; 90% acknowledgements breaches 95%.

## Implementation and evidence boundary

P1 delivers the workspace, focus routing, local navigation, restoration, async notices,
linear alternative and 80×24. P2 adds goal/action/observation review, the Trees view and
the Backlog in that workspace.
P3–p5 add typed tool views with their schemas. S114–S127 make these part of
delivery selection. No full graph schema is a prerequisite for the initial TUI.

The builder/checker verify ASCII geometry, scope, ledgers and synchronized
appendices. They do not prove sound reasoning, accessibility or usability.
Test real terminals, resize, multiline entry, monochrome, failures and screen
readers. First-time participants must identify their task and uncertainty,
inspect a source, return to a draft, choose another route and recognize a breach.
Later tasks assess conjunction, necessity, alternatives and corrections on
unfamiliar cases. Agreement, speed and filled trees are not reasoning quality.

## Design inputs

The supplied [TOC implementation guide](/Users/davidjoseph/Downloads/TOC_TUI_Implementation_Guide.docx),
sections 6–18 and 19–25, motivates gates, rival routes, equal Cloud sides,
adverse predictions, separate action/attainment, reflow and dependent review.
Its embedded commands and prescriptions are reference material, not authorization.
The adaptation uses the Payments commons; the factory examples do not establish
measured outcomes for this product.

The [supplied shell session](</Users/davidjoseph/.codex/attachments/8cd3eedc-56e1-438b-acd0-e0fd10cfc4a1/Eingefügter Text.txt>)
provides the commons. The Monospace [agent guide](https://coreyt.github.io/monospace-design-tui/agents/),
[agent directive](https://coreyt.github.io/monospace-design-tui/agent-ref/),
[standard](https://coreyt.github.io/monospace-design-tui/standard/),
[patterns](https://coreyt.github.io/monospace-design-tui/patterns/) and
[examples](https://coreyt.github.io/monospace-design-tui/examples/) inform canvas,
focus, discoverability and inspection. They were read for this revision.
Project adaptations in TUI-DESIGN.md do not assert full Mono compliance or measured gains.

## Names and the single interaction model

Reason Commons is the product; `reason-commons` launches it. Visible tasks have
human titles. Questions, reports, relationships, goals, tests, actions and reviews
are the concepts users work with. Internal intervention identities belong only
in Details or audit/export. No numbered exchange, deck or stack appears in the UI.
The compact consulting unit keeps one next move prominent while the persistent
canvas supplies orientation, scrutiny and alternatives.

Every Gherkin human interaction uses these controls. The ordered presentation
in [accessibility.md](accessibility.md) changes layout and announcement policy,
not actions or literal-input routing. No linear REPL, colon-command grammar,
phrase router or command-entry field is part of this product.
