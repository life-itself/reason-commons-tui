# P0 delivered slice

The first natural phase is the existing **Durable minimal case** increment,
selected by `@p0 and @automated`, not the full v1 release. Its complete slice runs
from an attributed contribution through retained input, a consultant port,
validated records and a durable published case, then through restart and portable
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
| S40 | Whole-snapshot publication appends ancestry, source references and an intervention atomically; prior revision bytes do not change. |
| S42 | A validated `.reasoncase` round trip retains stable IDs, ancestry, supplied sources and original forecasts offline. |
| S43 | Timeout receipts are separate from reasoning; explicit retry preserves the request and applies at most once. |
| S44 | Unknown references and unsupported ownership reject the complete proposal while retaining input and failure receipt. |
| S45 | Failed retention makes zero calls, reports not saved, preserves literal text and allows draft recovery to another export destination. |
| S46 | Both pre-call and post-call base checks reject stale work with explicit re-evaluation; no implicit merge. |
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

On 3 October, the [own-case skill entry point](skill-use.md) added one-shot
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
Gemma turns saved and reopened in a synthetic case; reference diagrams rendered
in a browser. See [usage](skill-use.md) and [validation evidence](validation.md).
This fixes the missing chat presentation and continuation for the implemented
case semantics; it does not declare the future TUI or graph profiles delivered.


The offline LTP continuation conversion adds a source-bound adapter and script
using existing application operations, with exact source retention, explicit
archival qualifications and portable ID mapping. It publishes an imported
baseline without fabricating original application history, graph edges,
formulation versions or participant commitments. A disposable copy of the actual
converted case continued at revision 2 with revision 1 unchanged. The full gate
now passes 159 implementation tests, 23 specification regressions, the original
nine p0 scenarios and seven conversation scenarios. Native formulation
supersession and later graph profiles remain separate domain capabilities.

## After p0: first TUI slice

A personal-use slice of p1 now ships as `reason-commons tui` (Textual,
now a core dependency), described in [tui.md](tui.md). It reads `workspace`/`inspect`
and changes the case only through `retain_input`, `consult`, `retry`, `export` and
`checkpoint`. A deterministic `GuidedConsultant` (provider `guided`) implements the
consultant port offline; the application validates its proposals like any other.
Adapter tests (`tests/test_tui.py`, `tests/test_guided.py`) cover sending, draft
restore, local browsing without calls, and retained-input retry. The p1 scenario
set (80×24 specimens, accessible mode, speaker switching, usability evidence) is
not yet delivered and no p1 scenario is claimed.

A goals home screen follows: plain `reason-commons` in a terminal lists the case
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
the focused control (S114). A reply that arrives while someone browses no longer
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
screen, and build the Forge case through use cases (eight consultant replies, two
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
