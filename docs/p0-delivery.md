# P0 delivered slice

The first natural phase is the existing **Durable minimal commons** increment,
selected by `@p0 and @automated`, not the full v1 release. Its complete slice runs
from an attributed contribution through retained input, a consultant port,
validated records and a durable published commons, then through restart and portable
handoff. Offline utilities and a skill capability adapter enter the application.

The [architecture](../ARCHITECTURE.md) applies the expert's refined distinction:
skills provide procedures; the application/domain enforces validity without them.
The architecture also guarantees semantic parity for domain-significant local
operations and treats the TUI as a projection over application state. The shared
skill protocol includes source attachment, export and local inspection alongside
contribution/retry. A coverage/signature gate prevents new public semantic use
cases from becoming interface-only; parity tests compare application outcomes
and exercise portable handoff through the skill surface. P1 must additionally
verify the actual TUI action bindings.

| Existing scenario | Implemented behavior |
|---|---|
| S39 | Fresh-process resume preserves complete reasoning, current target and draft/cursor without consulting. |
| S40 | Whole-snapshot publication appends ancestry, source references, the next intervention and the reply's proposals atomically; prior revision bytes do not change. |
| S42 | A validated `.reasoncase` round trip retains stable IDs, ancestry, supplied sources and original forecasts offline. |
| S43 | Timeout receipts are separate from reasoning; explicit retry preserves the request and applies at most once. |
| S44 | Unknown references and unsupported ownership reject the complete proposal while retaining input and failure receipt. |
| S45 | Failed retention makes zero calls, reports not saved, preserves literal text and allows draft recovery to another export destination. |
| S46 | Both pre-call and post-call response-target checks reject a reply once another reply has published a new question, with explicit re-evaluation; no implicit merge. Decisions recorded meanwhile do not make a reply stale (S146). |
| S48 | Storage help describes immutable application policy and the limits of ordinary files/content hashes. |
| S108 | The closed v1 registry rejects graph/stance records and out-of-profile fields/options before publication. |

Run `python3 scripts/check_p0.py` for the complete gate. It runs the unchanged
feature files in place and checks every selected scenario actually passes.
Additional tests cover domain invariants, inward dependencies, dead-writer lock
release, provider/commit recovery, crash after publication, allocation gaps across
handoff, hash corruption, archive traversal/duplicates, read-only archive access
and skill capability traces. Existing document-checker regressions also run.

Initial validation on 2 October 2026: all nine p0 scenarios (50 steps), 67 implementation
tests and 23 specification-checker regressions passed. The authored demo retained
all seven record kinds at revision 4 and reproduced identical state after
restart/import. A built wheel installed into an isolated environment passed
version, creation, export and read-only archive inspection. The procedure passed
the skill validator. The implementation suite includes 22 LM Studio HTTP adapter
tests. A live synthetic call to `google/gemma-4-e4b` returned a valid proposal and
committed revision 1. The updated wheel includes both the domain context and
consulting prompt. No existing feature text was changed.

The subsequent validation work expanded the gate to **110 implementation tests**;
all 23 specification regressions and nine original p0 scenarios still pass.
This includes the bounded agent host, evidence/report/review checks, schema
namespace isolation and frozen resource provenance.

Application BDD uses a deterministic consultant fixture. The subsequent
[LM Studio integration](lm-studio.md) adds a real provider adapter and separate
HTTP protocol tests. The [validation harness](validation.md) now records real
tool-calling skill execution, repeated semantic proposals and real-server
recovery evidence. Formal semantic approval and participant studies remain
incomplete; live runs expose consequential quality failures rather than
establishing v1 readiness.

**Provider-neutral consulting.** The consultant is now an explicit choice between
LM Studio and Anthropic ([choosing a consultant](providers.md)). The change added
14 conversation scenarios (21 in all) in `tests/conversation/features/providers.feature`,
an offline `reason-commons providers` readiness check, and a retained safe failure
category. The original p0 features were not changed.

P0 has only automated-tagged scenarios. P1/p2 and the v1 release gates remain
explicitly incomplete. A synchronous application boundary is ready for a future
TUI worker, but the persistent TUI does not ship here. The conversational skill described below is now available.

On 3 October, the [own-commons skill entry point](skill-use.md) added one-shot
contribution/retry commands, offline receipts and an optional stdio MCP bridge
for Codex. The complete gate now passes 129 implementation tests with the SDK,
23 specification regressions and the same nine p0 scenarios. Real LM Studio
consultations were saved through both local skill execution and MCP, then reopened
and retried idempotently. Explicit unavailable-model recovery saved the original
identity in a fresh process. The recorded negative agent/proposal cases still
demonstrate model limitations; these adapters do not imply p1/p2 completion.

## Using the public boundary

```python
from reason_commons.bootstrap import create_case

# Supply a Consultant with version: str and propose(request: dict) -> dict.
with create_case("payments-case", name="Payments", consultant=consultant) as app:
    current = app.inspect()["case"]
    result = app.submit(
        "Late deliveries and changing priorities", "Sam",
        base_revision=current["revision"],
        response_target=current["current_intervention"],
    )
    # Use result["status"] and recovery_actions to update the interface.
    # An unavailable provider leaves a retained request for explicit retry.
```

The provider receives `{input, case, sources}` with the complete committed state.
The proposal envelope is the v1 example from specification section 4, using
`schema_version: "1"`, `delivery_profile: "p2"`, `request_id`, `base_revision`,
`intervention` and `proposed_updates`. P0 supports `record_goal`, `record_note`,
`record_test`, `record_action`, `record_observation` and `record_review`, each
carrying `{operation, data, source_refs}` and an optional `temporary_id`.
The application resolves temporary references and allocates stable IDs locally.
Interventions are added by the application from the envelope, not a separate
update operation. [The domain registry](../src/reason_commons/domain/model.py)
defines exact fields; future adapters cannot bypass it.

Declaration fields are an explicit structured participant channel:
`{"ownership": ["Sam"]}` permits a cited action owner and
`{"evidence": ["observed"]}` permits a cited observed basis. A skill/provider
must not manufacture those declarations. Ordinary text stays literal.

The executable demo, `PYTHONPATH=src python3 examples/p0_slice.py --directory
/tmp/reason-demo`, shows retained inputs, all minimal record kinds, restart and
handoff using authored proposals. It is a storage/application demonstration,
not evidence of live consulting quality or a completed p2 human workflow.


On 3 October the conversational skill interface added a shared frozen
`CaseCapabilities.workspace` projection, local explanation/history/source views,
Markdown/Mermaid renderers, forecast comparison tables, explicit local/consultant
actions and replies bound to the displayed target. CLI `show` reads the same
workspace offline; contribution/retry now present it after the result. The complete
gate passes 147 implementation tests, the 23 specification regressions, the
original nine p0 scenarios and seven added conversation scenarios. Two actual
Gemma turns saved and reopened in a synthetic commons; reference diagrams rendered
in a browser. See [usage](skill-use.md) and [validation evidence](validation.md).
This fixes the missing chat presentation and continuation for the implemented
commons semantics; it does not declare the future TUI or graph profiles delivered.


The offline LTP continuation conversion adds a source-bound adapter and script
using existing application operations, with exact source retention, explicit
archival qualifications and portable ID mapping. It publishes an imported
baseline without fabricating original application history, graph edges,
formulation versions or participant commitments. A disposable copy of the actual
converted commons continued at revision 2 with revision 1 unchanged. The full gate
now passes 159 implementation tests, 23 specification regressions, the original
nine p0 scenarios and seven conversation scenarios. Native formulation
supersession and later graph profiles remain separate domain capabilities.

## After p0: first TUI slice

A personal-use slice of p1 now ships as `reason-commons tui` (Textual,
now a core dependency), described in [tui.md](tui.md). It reads `workspace`/`inspect`
and changes the commons only through `retain_input`, `consult`, `retry`, `export` and
`checkpoint`. A deterministic `GuidedConsultant` (provider `guided`) implements the
consultant port offline; the application validates its proposals like any other.
Adapter tests (`tests/test_tui.py`, `tests/test_guided.py`) cover sending, draft
restore, local browsing without calls, and retained-input retry. The p1 scenario
set (80×24 specimens, accessible mode, speaker switching, usability evidence) is
not yet delivered and no p1 scenario is claimed.

A goals home screen follows: plain `reason-commons` in a terminal lists the commons
folders under `~/ReasonCommons` (or `REASON_COMMONS_HOME`) and starts new ones with
`create_case`, reading each through read-only `open_case`/`inspect`. Without a
terminal it still prints help. The header shows "Saved"; revisions stay in History.
The workspace draws the loop under the pinned context (✓ done, ● current, ○ to come);
the welcome screen asks one question, with the workflow diagram behind Explain this.
Record IDs stay out of the views. The
home screen offers a finished, fictional example built through `retain_input` and
`consult` with the built-in guide in a temporary folder that is removed afterwards.
The README now leads with screenshots rendered from the running workspace by
`scripts/render_screenshots.py`; developer material moved to `CONTRIBUTING.md`, and
`tests/test_docs.py` checks that README and docs links and images resolve.
User docs follow the four Diataxis kinds from `docs/README.md`: a tutorial with
step screenshots (`tutorial.md`), how-to guides (`use-a-model.md`,
`back-up-and-share.md`, `skill-use.md`), a reference (`tui.md`) and an explanation
(`the-loop.md`). They describe shipped behaviour only; no new scenario is claimed.

A UX pass ([TUI-UX-PLAN.md](../TUI-UX-PLAN.md)) moves the workspace towards the
p1/p2 contract, in the adapters only. At review, Next step puts each original
forecast beside the reported results, matched by measure name alone and with no
verdicts, followed by the goal's safeguards (towards S121). The guide quotes the
change while it is being forecast (S04). The goal band never clips silently, and
the context under a question leaves out what the band shows (S68). The header names
the focused control (S114; since replaced by a focus frame, see
[Navigation and hierarchy](#navigation-and-hierarchy-redesign-5-october-2026)). A reply that arrives while someone browses no longer
changes their view (S118). The first start leads with starting a goal. Adapter
tests cover each of these; the scenario steps and participant checks are still
outstanding, so no p1 or p2 scenario is claimed.

The README and docs now illustrate the six LTP trees with the Second Renaissance
analysis from the reasoncommons guide (`docs/the-trees.md`, pictures drawn by
`scripts/draw_trees.py`), and the finished example is one of its Transition Tree
actions. The pictures are labelled as illustrations.

## Trees in conversation (p2 scenarios S128–S134)

On 3 October 2026 David approved a specification change: the six trees enter v1
and grow in the conversation. The domain gains three record kinds in the LTP 1.0
vocabulary: `claim` (tree, role, statement, basis, optional `replaces`), `link`
(one typed relation between two earlier, current claims of the same tree, with an
optional assumption) and `retraction`. Tests may name the claim they carry out
(`claim_ref`). Validation keeps the trees append-only and ordered: a role must
belong to its tree, links stay inside one tree, and nothing cites a replaced or
withdrawn claim. S108 now names these typed records in its allowed schema; it
still rejects untyped graphs and stances.

`workspace` returns the current trees (`project_trees`); the TUI's Trees view, the
`trees` command and `show --view trees` draw them with `adapters/trees.py`. The
TUI shows one tree at a time (Ctrl+T opens the view, Ctrl+N steps to the next tree
or all six); which tree is shown is presentation state, kept in the cursor's
`display` field like the view, and `trees --tree NAME` gives the same choice.
`adapters/ltp_trees.py` brings LTP files in through `add_source` and `submit` with
a deterministic one-use proposal adapter (no model call), keeps what the trees
cannot hold as notes, and writes the trees back out. The consultant prompt and
domain context explain the tree records; LLM output with them is not yet checked
against a live model. The finished example carries the reasoncommons Second
Renaissance analysis, mapped by `scripts/build_sample_trees.py`.

`scripts/check_p0.py` now also runs every scenario in
`12_trees_in_conversation.feature` (S128–S134, 11 cases) and fails unless all
pass. Joint premise groups, rival routes, dependent review and boxed canvases
remain p3–p5 work. The remaining p1/p2 scenarios are not yet delivered.

Since 7 October 2026 (below) the trees work differently in three ways this section
predates: a link may use a statement from another tree, the commons' goal is the Goal
Tree's top statement instead of a second copy among the claims, and rewording records
a new version of the same statement (`C3@2`). S128–S133 were amended to say that what
the consultant proposes waits for the operator.

The user docs now cover the trees: the tutorial ends in the example's Transition
Tree (`tutorial-trees.png`), `use-a-model.md` explains growing trees in
conversation, `back-up-and-share.md` covers `.ltp.yaml` import/export and the
`trees` command, and `skill-use.md` lists the `trees` view.
The README and `the-trees.md` also explain why to open the Trees view and how
(Ctrl+T, Ctrl+N, import/export), with a Current Reality Tree screenshot
(`trees-current-reality.png`).

## Trees you can read (5 October 2026)

The Trees view became something to work with rather than only look at. All of it
is in the adapters (`trees.py`, `timeline.py`, `tui.py`), over the existing
`workspace`, `history` and `sources` reads; no specification, domain or application
change was needed and no new scenario is claimed.

- **Nothing recorded is hidden.** The outline dropped the assumption behind aside
  links (the Evaporating Cloud's conflict, "comes before", "refines") and behind a
  second link into a statement already drawn. In the shipped sample 4 of 22
  assumptions never reached the screen, among them the one the Cloud exists to
  question. Every assumption is now drawn under its link.
- **The empty view tells the truth.** With the built-in guide it says the guide does
  not add to the trees and points to Claude or a local model, or to importing.
- **A reply's tree changes are named.** After a reply or import saved in the open
  workspace, the question says what it changed, tree by tree; the tree names mark
  which trees changed; and the drawing marks those statements NEW or REWORDED. A
  reply that arrives while the trees are open leaves them open (S118's rule).
  Opening the goal later starts unmarked; History still shows each step's changes.
- **Choose a statement and inspect it.** Ctrl+T puts the keys on the drawing with
  a statement chosen; ↑↓ choose another, marked by a bar separate from focus. Its
  details read every link from its side with the assumption behind it, the tests
  that carry it out, earlier wordings, and where it came from (who wrote the words
  it cites, when, and the words, or the imported file). They sit beside the trees
  from 120 columns (Master-Detail) and open full screen with Enter at any size
  (Expand-to-Focus); Esc returns to the same statement. Ctrl+T goes back to the
  question with the draft and caret as they were. The choice is kept in the
  cursor's `selection`. Choosing and reading make no consultant call and no
  revision.

Adapter tests in `tests/test_trees.py`, `tests/test_tui.py` and
`tests/test_story.py` cover each of these, including a reply that grows and
rewords a tree through the TUI with a scripted consultant, 80×24, and restart;
each new test was shown to fail first and to catch a deliberate break. The
screenshots were regenerated; they had predated the theme change. Still
outstanding: the p1 scenarios' steps through the TUI, a live-model check that a
real consultant records tree statements well, and the p3–p5 tree structures.

## Seeing the part without losing the whole (6 October 2026)

An outside expert's review of the TUI against Norman, Ware and *The Unarchivable
Reason* was checked against the specification; [TUI-UX-PLAN.md](../TUI-UX-PLAN.md#conflicts-revision)
records each recommendation and why it was adopted, adapted or left for a later
phase. What was built is in the adapters (`trees.py`, `timeline.py`, `tui.py`) over
the existing reads; no specification, domain or application change was needed and
no new scenario is claimed.

- **Dim, don't hide.** In one tree, while the keyboard is on the drawing or the
  details, the chosen statement, what it hangs under and what hangs under it keep
  their colours and the rest of the tree takes a quiet tone in place.
- **Where paths meet, say so.** A statement reached by several paths says how many
  of its tree's ends it leads to ("leads to 5 of 6 undesirable effects"), counted
  from recorded links; in the Future Reality Tree, each change we make says what it
  leads to, harms beside benefits. Each tree's page counts the links that state no
  assumption and the statements that state no basis, and a statement's details say
  "no assumption stated yet" on such a link.
- **A forecast in a tree reads as sealed.** A test under a statement shows its
  original forecast, saved before any result, then its result, on lines of their own.
- **The reading, while the speaker still knows what they meant.** After a reply that
  added a few statements, Next step draws them under the new question beside the
  words they came from, with how to correct a wrong reading. No stance is recorded.
- **Pointing kept in the words.** In the trees, **a** puts the chosen statement's
  words, role and tree at the end of the draft as editable text.

Adapter tests in `tests/test_trees.py` and `tests/test_tui.py` cover each, and each
was shown to catch a deliberate break. The S131 step reads the test's new lines.
Not built, because they need records the v1 schema does not have: recording a
speaker's *Wording: Accurate* on what the consultant recorded (S24, S59, S60, p4),
an exact subject reference on an input (p3 structured authoring), a consultant
move that raises one reservation at a time (a new intent), and dependent review
after a missed forecast (p5).

## P1 workspace scenarios through the TUI (5 October 2026)

22 of the 32 p1 scenarios now run through the real workspace and pass: S07 (all
seven controls), S08, S09, S11, S12, S13, S47, S51, S54 (all three answers), S56,
S58, S67, S72 (all four commands), S110, S113, S114, S115, S116, S117, S118, S119
and S120. `scripts/check_p0.py` runs them by identity, fails unless each runs and
passes, and prints the ten that are not delivered: S10 and S57 (a menu filter's "No
matches" with Clear filter and Back), S49 (the accessible ordered presentation),
S55 (an Inspect evidence alternative), S63 and S70 (menus checkpointed and
revalidated), S68 and S69 (Compact display and a pinned breach), S73 (the
first-hour participant study, which automation cannot pass) and S107 (refusing a
restored out-of-profile action).

The steps are interface acceptance: they drive the Textual app headlessly by keys
(`tests/acceptance/workspace.py`), read outcomes at the application boundary and on
screen, and build the Forge commons through use cases (eight consultant replies, two
tree imports). See the [testing strategy](development/testing-strategy.md#interface-acceptance-p1).
No specification text changed.

Writing them found and fixed what the workspace lacked:

- **A live resize was laid out for the old size.** Textual calls `App.on_resize`
  before it updates `size`, so shrinking a terminal from 120 to 80 columns kept the
  destinations list and hid the Views control. The workspace now lays out from the
  event's size, and drawings are redrawn for their new width (S117).
- **Esc returns from an inspection.** Opening Explain this, a view, or a past
  moment remembers where you were; Esc goes back there with the view, scroll
  position, draft and caret as they were. In the answer box Esc still means
  "browse" (S11, S13, S116).
- **Help is a visible control** and opens on the keys and controls, apart from
  Explain this (S07, S119).
- **Consultant calls** in Actions counts the consultant's attempts from the saved
  receipts, with imports counted apart (S07).
- **Every action says its consequence.** Actions entries say "Local" or "asks the
  consultant"; Other moves items read "Inspect rationale · local; opens saved
  explanation" and "Ask another question · asks consultant" (S12, S56, S119).
- **Menus have a Cancel control** as well as Esc (S113).

Each new behavior was shown to be caught by its scenario when broken in a scratch
copy.

### Menus (S10, S55, S57, S63, S70, S107)

Six more p1 scenarios followed, bringing p1 to 28 of 32. Other moves, Actions
(Ctrl+P) and Views now share one menu, which replaces Textual's command palette:

- **Filtered by typing, with an honest dead end.** The filter has focus; with
  nothing matching, Enter activates nothing and the menu says "No matches" with
  **Clear filter** and **Back** (S10, S57).
- **Inspect evidence** in Other moves shows the saved words and files the current
  question rests on, locally (S55).
- **A menu belongs to its question.** It is bound to the question and revision it
  opened on. If a reply moves the commons on while it is open, choosing does nothing:
  the menu shows a notice and the current choices, and a new choice is needed (S63).
  Other moves therefore stays available while a reply is pending; its local items
  work, and a move that asks the consultant is refused until the reply is in.
- **Menus survive a restart.** The open menu (filter, choice and binding) is kept in
  the cursor's `menu` field. On resume it reopens with the question it belongs to,
  only if that question and revision are still current (S70). A kept choice from a
  later delivery profile, such as "Record position", is refused locally with a note;
  nothing is sent and the draft stays (S107).

Still outstanding in p1: S49 (the accessible ordered presentation), S68 (Compact
display and a Commons context control), S69 (a breach kept visible while browsing) and
S73 (the participant study).

## Navigation and hierarchy redesign (5 October 2026)

An outside evaluator's findings on three screens, and a revised mock-up, were built in the
workspace ([TUI-UX-PLAN.md](../TUI-UX-PLAN.md#navigation-and-hierarchy-revision) lists each
finding and its change; the rules that remain are in [TUI-DESIGN.md](../TUI-DESIGN.md#hierarchy-names-and-focus)).
Adapters, docs and screenshots only; no domain, application or specification change, and no
scenario's text changed. The same 28 of 32 p1 scenarios run through the workspace and pass.

What the scenarios now check differently, because the screen changed:

- **S114** asks that the focused control stay visible. The step now checks that the answer
  box is the focused control and that its frame is drawn heavy, where it read a "Focus:
  Answer" label that the header no longer carries.
- **S07 and S119** call the list of every action **Actions**. On screen it is **Commands**,
  in the footer, and **Help** is a footer control too; both are reached with Tab and Enter, as
  the buttons were. The steps map the specification's name onto the control that carries it.
- **S68** (not yet delivered) says the pinned header shows "focus". The design shows focus as
  a frame, so that scenario needs a decision before it is delivered.

Found while building it: Tab from the views list must go on to the History timeline (S07's
`History > …` examples caught that a shortcut straight to the answer box skipped it), a column
width floor that clipped the day at 40 columns, and a one-frame jump of the answer box when its
hint moved under the buttons. An independent review then found and had fixed: a footer that
overflowed at 80 columns and lost Help (hints now shorten, then drop, and Commands and Help stay),
a click on Commands or Help that rearranged the footer under the pointer and fired another hint, a
loop line clipped at 58–61 columns, goal names and measures containing `[` read as markup, and a
Textual floor that was too low (`textual>=6.2`: older versions lack `OptionList.highlighted_option`
or leave Commands and Help out of the Tab order).

Not built: renaming and deleting a goal, shown in the mock-up's home footer. They need new
application use cases and scenarios first; see the UX plan.

## Deciding what enters the model (p2 scenarios S135–S147, 7 October 2026)

David set a contract change: the consultant drafts, and the operator decides what
enters the model. The specification change came first and was reviewed (main
specification section 2F, `13_proposals_and_review.feature`, amendments to S01, S02,
S07, S40, S43, S46, S52, S108 and S128–S133, and the dated decision in
`reason-commons-spec/delivery-phases.md`). Then:

- **Domain.** A reply's updates become records whose membership is *proposed*;
  snapshots carry `membership` (where proposals begin, and the acceptance setting) and
  an append-only `decisions` list. `domain/membership.py` derives what is in the
  model, readiness, the backlog's order, what a decision takes with it and review
  flags. `Snapshot.decide` records accept, reject, undo, still holds and the setting as
  revisions of their own; ancestry validation accepts exactly one explicit decision in
  such a revision, and a reply may carry only its own automatic acceptance. A commons has
  one goal (a new one is `G1@2`), a claim may not take the goal role, a link belongs to
  the tree of at least one of its statements, and a new wording keeps the statement's
  identity. Only a newer question makes a pending reply stale.
- **Application.** New use cases on `CaseApplication` and `CaseCapabilities`:
  `accept`, `reject`, `undo`, `still_holds`, `set_acceptance`. A decision that takes
  more than was named (and every undo) returns `confirm` with the full list and changes
  nothing until it is repeated with `confirmed=True`. `workspace` returns the backlog,
  each record's membership, the last reply's records and the setting; trees, goals
  and comparisons show the model only. Consultants receive a `model` summary with
  open reviews, and a `review_flags` consult intent asks about them.
- **Adapters.** The built-in guide, the LTP importer (the file's goal is proposed as
  the commons' goal or its new version; links across trees are kept), the story builder
  (created with automatic acceptance by its editor, so each chapter is still one
  revision) and the finished example (its organiser accepts each reply, and rejects
  the trees file's goal to keep her own) were brought under the new rules. The
  provider schema accepts a per-update `confidence`, recorded and not used. The MCP
  bridge has the decision tools and refuses `set_acceptance` unless started with
  `--allow-acceptance-setting`; the CLI has `decide`. The contribution skill reports
  proposals and leaves decisions to the participant.
- **TUI.** Next step draws what the last reply proposes with **Accept all**; a
  **Backlog** view lists entries in decision order (Enter for choices, `a`, `r`, `h`);
  History rows name decisions and `u` undoes a step's acceptance; Commands switch the
  setting and ask about open reviews; the band shows a goal that is only proposed.

`scripts/check_p0.py` runs every scenario of `13_proposals_and_review.feature`
(S135–S150) and fails unless all pass. `tests/test_membership.py` covers the domain's
negative cases, forged decisions, ancestry and a commons recorded by the previous release
(`tests/fixtures/recorded-before-proposals.reasoncase`), which opens with everything
in the model. Three deliberate breaks (no prerequisites on accept, flags never
closing, no automatic acceptance) each failed feature 13. Tests that are about
drawing or reading rather than deciding create their commons with automatic acceptance,
which is a recorded choice; the Forge fixture of the p1 navigation scenarios does the
same, so its Background still holds.

Not delivered: a confidence threshold for automatic acceptance, editing a proposal's
wording in the workspace before accepting, review of consequences that no reference
records, and Restore reasoning (S41, p3). Live-model behaviour with proposals (does a
real consultant use `replaces`, cite waiting proposals and answer `review_flags`
well?) is not yet evaluated.

## Withdrawals, citations and test versions (p2 scenarios S148–S150, 7 October 2026)

A live acceptance run against Claude found three gaps, and David chose the fixes
(withdrawal confirmed like undo; the rest as recommended). The specification came
first: section 2F (*Withdraw*, *Tests*, what a proposal may cite, which flags a
change raises) and scenarios S148–S150 in `13_proposals_and_review.feature`.

- **Withdrawal (S148).** Accepting the withdrawal of a statement used to remove the
  links that join it without saying so. `Membership.leaves_after` names the links a
  decision takes out of the trees; the decision use cases return them as `leaves`
  and ask for confirmation when there are any, and automatic acceptance leaves such
  a withdrawal waiting. The TUI dialog lists them under "Leaves your trees with it".
- **Citations (S149).** A later reply could cite an answer that went stale and was
  never applied, bringing its words into the commons through another request. A reply
  may now cite only the answer it replies to, answers already applied and supplied
  sources (`Snapshot.apply`), and the consultant is no longer sent stale answers.
  The rule governs new replies only, so commons that already hold such a citation
  open unchanged.
- **Test versions (S150).** A test can be given a new version (`P1@2` replaces
  `P1@1`) until a result for it is in the model; from then on a further version is
  refused, and a waiting one is closed when the result is accepted. A result, an
  action or a review cites the test's current version. The Tests view compares the
  current version; earlier ones stay in history. The consultant prompt says so.

Not changed, by choice: a result reported before its test's stated start is not
refused, because test periods and result dates are the participant's free text,
and refusing would drop their report. `tests/test_membership.py` adds the negative
cases, `tests/test_tui.py` the withdrawal dialog, and six deliberate breaks (one per
rule above) each failed the scenario written for it. A live check with
`claude-sonnet-5-5` passed all three rules; `claude-haiku-4-5-20251001` could not
produce valid proposals reliably (see [validation](validation.md)).

## The loop's records (p2 scenarios S32, S37, S95, S101, 7 October 2026)

Toward finishing v1, the commons engine scenarios of the goal-action-review loop:

- **A pilot reviewable later (S32).** A test may record the pilot's own `baseline`, its
  `dose` and an `alternative_explanation`. The workspace's comparisons carry ten
  `review_fields` (owner and scope, intervention and dose, baseline and cohort, exact
  prediction, measurement method, observation window, protected conditions, stopping
  conditions, alternative explanation, review date), drawn from the test, its
  forecast, its current action's owner and its goal's safeguards; a field nobody
  recorded is `None`, shown as "unknown" in text and listed under "Not recorded yet"
  in the Tests view.
- **A review date is a date (S37).** It reads "Review October 19; no reminder
  scheduled", and nothing is scheduled, sent or written outside the commons.
- **A test's goal changed (S95).** The existing review flag is also projected as
  `test_reviews`, shown at the next test decision ("Review needed: …").
- **Completing an action (S101).** An action may take new versions (`A1@2`) and
  record its `expected_state`. Marking that state met or not met is refused until a
  result for its test is in the model. A completed action without a result shows
  "Action completed; result awaiting observation." The provider schema is now
  `schema=3`, and the consultant prompt describes the new fields.

`scripts/check_p0.py` now also runs the p2 scenarios delivered outside features 12
and 13 (`DELIVERED_P2`) and names the rest of p2 as outstanding, as it does for p1.
Five deliberate breaks, one per rule above, each failed the scenario written for it.

## How the question is presented (p2 scenarios S03, S04, S17, S93, S121, 7 October 2026)

- **One move, other paths visible (S03, S17).** These already held: one heading and one
  prompt, Other moves visible, no unsolicited lesson, and no tree drawn for a question
  it would not clarify. A test's context rows now give each forecast's measure ("not
  stated yet" while unknown) and period, and the pilot's own baseline.
- **What changes the answer beside the question (S04).** The band keeps the goal and
  each safeguard; the question's context gives the pilot's baseline and period; an
  estimate stays worded as one. The status line keeps its redesign (see the dated note
  in `reason-commons-spec/delivery-phases.md`): the focused pane is framed, and the new
  **Commons context** view (last in Views) gives the revision with the complete goal, the
  tests' boundaries, the response target and what waits. It is a workspace view
  (`context`), local, with no consultant call.
- **The decision and the goal it serves (S93).** A question's purpose shows under its
  heading when it is written for people (a coded purpose is not shown); Explain this
  names the exact goal formulation the question serves, and says when the goal has a
  newer version. A goal with no measure is pinned as provisional.
- **Forecast beside outcome, breach visible (S121).** The workspace now projects
  `breaches`: a reported result outside a bound recorded with the test's forecast for
  the same measure, judged only when both are plain numbers in the same unit. A breach
  is pinned in the band in every view and marked on the review; the review also lists
  the action's execution and the system goal ("judged by its own measure, not by this
  pilot") on their own lines.

Seven deliberate breaks each failed a scenario, two after their steps were tightened
(the revision and the period were also matched by other text on screen).

## Compact context, a pinned breach, leaving and returning (p1 S68, S69; p2 S94, 7 October 2026)

- **Compact and Expanded (S68).** Display density is a presentation preference
  (`display.density` in the cursor, `compact` by default), switched in Commands with
  **Display: Expanded** or **Display: Compact**; it records no reasoning and calls no
  consultant. Expanded repeats the goal's measure, baseline, horizon and scope, each
  safeguard and each test's boundaries in the band (its label column widened so
  "Baseline" is not cut). In Compact the page does not repeat what the band shows, and
  the review's "System goal" line appears only once a result exists, so a routine
  Tests view does not repeat the goal. Commons context gives the complete context.
- **A breach while browsing (S69).** The pinned breach stays visible in History, Your
  words and behind Other moves, at either density.
- **Leave and return (S94).** Already held: History and Esc bring back the question,
  the response target, the exact draft and the focus, with no revision or call.

A TUI test covers Expanded and its being saved with the draft. Seven deliberate breaks
each failed a scenario (an eighth missed because it broke the restore-on-open path,
which S94 does not exercise; two breaks of the Esc path were caught instead).

## The accessible ordered presentation (p1 scenario S49, 7 October 2026)

`reason-commons tui FOLDER --accessible` (or `TERM=dumb`) opens
`adapters/accessible.py`: the same commons through the same application use cases, as
ordered text appended to the terminal without redrawing, as
`reason-commons-spec/accessibility.md` describes. Each view starts with the commons,
the declared speaker and save state, then the view and the focused control in
words (the redesign's frame cannot be seen in text); then any breach, the decision
and question with the goal and safeguards, what is uncertain (grouped by record),
the test review, what the last reply proposes, the draft and the labelled
controls. Lines wrap to the terminal's width, a long view is paged ("Page 1 of 6.
Page Down: more."), a new view says it replaces the one above, and no colour or
cursor code is written. Tab and Shift+Tab announce each control's label, role and
consequence; Response is literal and only Send submits; Esc returns with the draft
kept; Commons context, Explain this, Views, Backlog (Accept, Reject, Still holds, with
a decision that takes more listed and confirmed by activating it again), Help and
Save and quit are local, and the draft is checkpointed like the TUI's.

S49 runs at 40 by 16; `tests/test_accessible.py` covers literal input and single
submission, local navigation with Esc, backlog decisions through the use cases, plain
wrapped output and the draft kept across sessions. Five deliberate breaks (no
wrapping, no paging, focus not named, the revision missing from Commons context, colour
codes) each failed S49. Not done: assistive-technology users have not tried it; the
participant gate in `reason-commons-spec/delivery-phases.md` asks for that.

## Haiku by default, one reply with deeper reasoning, and what it costs (8 October 2026)

Outside the specification's scenarios, following the
[plan](plans/2026-10-08-haiku-default-boost-usage.md): no feature file of the
specification changed, nor the application layer or `CaseCapabilities`.

- **Haiku 5.5 is the default Claude model.** Setup recommends it; a saved or chosen
  model stays. Conversation scenario: "Claude Haiku 5.5 consults when no Claude model is
  chosen".
- **What it costs.** A local usage log outside every goal, fed by a sink the composition
  root injects into the Anthropic adapter, counts each billed request from every entry
  point; costs are list-price estimates, and the Anthropic Console is the authority.
  The workspace says it in the footer, in each reply's notice and in Commands ›
  Consultant calls and cost; `reason-commons usage` prints it. A soft monthly budget is
  said at 80% and 100%, and past it each workspace send asks once; nothing is blocked.
  Conversation scenario: "Count what a Claude reply cost outside the commons" (no tokens
  or cost in the commons or its export, no words or key in the log).
- **One reply with deeper reasoning.** On request only, one answer goes to Sonnet 5.5
  and the next Send to Haiku again; never automatically, and not through MCP.

That makes 23 conversation scenarios. Adapter tests cover the prices, the log (modes,
torn lines, four writers at once, local days and months), the adapter's reports, the
workspace meter, budget and boost, the accessible presentation, the command and the
notices. They establish the integration with fake servers; the live smoke in
[validation](validation.md) checks it once against Anthropic. Whether the meter helps
people spend as they intend is not established.

## Dogfood restoration

The reconstructed RC development and simplified home/navigation are implemented
in `adapters/commons.py` and the TUI. Five additional conversational scenarios
cover honest import, free-form continuation, readable stage ordering, a pending
review import, and changing future acceptance policy. Adapter checks cover
literal attribution, collision-safe resume, portable round trips, F2 acceptance
settings and adopting the import through the UI. The adopted demonstration retains
59 claims, 56 links and ten development stages; its Backlog is empty because all
119 proposed records were adopted. No historical participant approvals, dates or
measured trial results are invented.

This changes no scenario-local delivery tags or product-specification scenarios.
It does not establish live consultant quality or participant usability. See
[the working import](restoration/working-import.md) for sources and commands.

The final restoration gate passed 476 pytest tests and all 28 conversational
scenarios, alongside every required delivered specification case.

## Commons terminology and review clarity

The persistent workspace is now called a **commons** in the TUI, ordered
presentation, CLI help, consulting guidance, domain glossary, specifications and
user guides. A **conversation** is an exchange within it. Its **model** contains
accepted current reasoning; pending, rejected, undone and earlier reasoning
remains recorded in the commons without belonging to its current model.

The evaluation review page introduces these separately and explains older
replies' use of “case” without rewriting the recorded reply. It retains PR #38's
plain questions, attribution, turn-specific facts and answer polarity handling.
The MCP launcher accepts `--commons-root`; `--case-root` remains an alias, and
existing API keys, tool names and `.reasoncase` archives remain compatible.
Scenario identities, delivery tags and acceptance behavior are unchanged.

The complete gate passed 476 pytest tests, all required delivered specification
scenarios and all 28 conversational scenarios. The 150 product scenario
identities, delivery tags and 186 expanded cases were compared with the prior
version. The reconstructed import, attributed source files and portable archive
were verified unchanged byte for byte. Screenshots were refreshed in disposable
commons, and the export and view-picker labels were visually checked.
