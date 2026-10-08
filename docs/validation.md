# Validation of the implemented slice

The p0 application/DDD boundary has a deterministic acceptance gate. A local
model and an agent are separate replaceable adapters with separate evaluations.
None of these evaluations constitutes the p1/p2 or first-time participant gate.
The existing [delivery contract](../reason-commons-spec/delivery-phases.md)
defines those additional requirements.

## Repeatable checks

```sh
python3 scripts/check_p0.py
python3 scripts/evaluate_lm_studio.py \
  --model google/gemma-4-e4b --suite all --repeat 2 \
  --output .evaluation-runs/my-model-check
# The semantic fixtures with any configured consultant, Claude included (billed):
python3 scripts/evaluate_semantic.py --provider anthropic --repeat 2 \
  --output .evaluation-runs/my-claude-check
# The live procedure's consultant steps, replayed in review mode (billed):
python3 scripts/evaluate_procedure.py --provider anthropic --repeat 2 \
  --output .evaluation-runs/my-procedure-check
```

The model and its output settings come from the environment, as in use
(`REASON_COMMONS_ANTHROPIC_MODEL`, `REASON_COMMONS_ANTHROPIC_MAX_TOKENS`,
`REASON_COMMONS_ANTHROPIC_EFFORT`; `--model` overrides the first). Each report ends
with a `consultations` summary: how the attempted turns ended (each is attempted
once, so the share saved is first-attempt validity), the reason each other turn
was not saved, the transport slips the adapter undid, and tokens and seconds.

`evaluate_semantic.py` runs every fixture in `evaluations/fixtures.py` (or `--case
NAME`, repeatable) once per repetition, each generation attempted once. The
fixtures cover the twelve `@semantic` p2 scenarios (S01, S02, S06, S30, S34, S35,
S36 with one case per outline row, S52, S102, S104, S105, S122); authored setups
are seeded through the application. Two more carry the live procedure's
open-evenings conversation, which asks for the largest replies: its trees (a cause
and an Evaporating Cloud, S128) and its test-result loop (S131, S34, S36). Each case is created with automatic acceptance,
recorded as Sam's setting, so a turn builds on the last; every proposal and its
membership stays in the evidence.

Use a new output path. The live harness uses synthetic contributions, creates
disposable durable cases, and leaves the server running. It makes no downloads
and sends nothing to a hosted fallback. It reads the optional API token from
the environment; tokens are not written into evidence. `--suite semantic`,
`agent` or `recovery` runs one part, and `--case` selects a semantic fixture.
Each generation is attempted once; a failure remains evidence. The recovery
suite deliberately performs explicitly identified retries.

Reports contain configuration, native loaded-model/context metadata where
available, versioned and hashed frozen consulting/context resources, inputs,
receipts, resulting records, restart checks, and exported `.reasoncase` files.
JSON evidence and readable Markdown are checkpointed after each semantic turn.
Interrupted or aborted runs remain incomplete. The large disposable evidence
directory is ignored by Git; reviewed conclusions belong in this document.

| Evaluation | What it establishes | What remains separate |
|---|---|---|
| Original p0 Gherkin | Retention, validation, durability, retry and portability through application use cases | Model quality and human interface behavior |
| HTTP protocol fixtures | Structured payloads, namespaces, malformed/truncated replies, credentials, redirects and model replacement | Real-server implementation and model behavior |
| Live semantic fixtures | Actual multi-turn proposals and saved/rejected results against authored situations | Attributed assessment of the complete professional rubric |
| Live skill agent | A real model executes the actual Markdown skill through bounded capability tools | The authored downstream consultant isolates procedure from consulting quality |
| Real-server recovery | Timeout, unavailable model, token truncation, oversized context, restart/retry, client-process interruption | Server shutdown/unload and concurrent external users |

The semantic fixtures cover a situation → goal → prospective pilot → action →
outcome sequence, attributed correction/uncertainty, a guardrail review, and an
unimplemented/inconclusive review. They link to original scenario identities;
they do **not** cover every p2 scenario or outline row. Required record kinds,
immutable history, exact source/target retention, provider outcomes and restart
are mechanically checked. Judging neutrality, causal restraint, decision
usefulness, and whether the protection breach is properly addressed requires
reviewing the recorded proposals. A keyword count or the same model grading its
own response cannot pass that gate.

The live agent is offered only the capabilities authorized by this procedure,
not storage, shell or file tools. Every requested call, including blocked calls,
is recorded. Evaluation checks inspect → retain → consult, literal multiline
text and declared speaker, failed-retention stopping, no automatic retry,
explicit retry identity and published effects. Host permissions protect the
case, but a blocked request remains a failed agent evaluation. Finishing a chat
or claiming success cannot publish a case revision.

Recovery probes use real local HTTP responses. One additional test injects a
storage commit fault *after* a real received proposal; restart must apply that
same proposal with zero further inferences. Another kills only a disposable
client while it is entering the real provider call, then reopens and retries
the retained request. It does not kill LM Studio. The harness does not unload
a model or stop a server that might be serving another application.

## Attributed semantic review

```sh
python3 scripts/review_evaluation.py .evaluation-runs/my-model-check/report.json \
  --output .evaluation-runs/my-model-check/review.json
# Fill reviewer, role, date and each decision with cited run/turn evidence.
python3 scripts/review_evaluation.py .evaluation-runs/my-model-check/report.json \
  --review .evaluation-runs/my-model-check/review.json \
  --output .evaluation-runs/my-model-check/reviewed.json
```

Reviews are bound to the SHA-256 of the completed evidence report. Changed
reports, rewritten criteria, missing decisions or unsupported pass/fail entries
are rejected. A criterion whose evidence does not exist (its reply was rejected
before commit) is marked `unjudgeable` with the reason; such a review reports
`incomplete`, never `pass`. Each run keeps its authored setup (`setup_text`,
`setup_records`) and the turns whose reply was not committed, and every machine
check says what a failure would be evidence of: the consultant's reply, the
application, or only the consequence of an uncommitted reply. Pending criteria and failures remain visible. A completed review
of these fixtures still cannot approve the unimplemented TUI or substitute for
five real first-time participants and assistive-technology testing.

### Reviewing replies with people who have no background

Reviewers judge each case from the assistant's replies, in plain words, with the
workspace's own screens beside them, on a page they open by link:

```sh
python3 scripts/review_screens.py .evaluation-runs/my-model-check/report.json
```

Then ask Claude Code to "publish the review package in
.evaluation-runs/my-model-check/review-package" (the `publish-review` skill in
`.claude/skills/` does it), and share the link from the page's Share menu with
each reviewer as a Contributor. `--case NAME` builds a shorter package from some
fixtures only.

The page is written for a reviewer with no background. It opens with a short
brief: what the app is, who Sam and the assistant are, that the reviewer judges
the assistant's replies (not Sam, and not the plan), what each answer means, and
a worked example. Each case then gives what was going on, the facts with the
arithmetic done, and each turn as what the person wrote and what the assistant
replied, in plain words: the question it asked and each item it saved, with
whose words it came from (`evaluations/plain_reply.py`). Under each reply are
yes/no questions about it (`evaluations/review_questions.py`): each rubric
criterion becomes one or more questions, one idea each, tied to the turn they
are about, in plain words, with one name for each thing (the 95% rule is always
"the 95% urgent-request line"). Answers are Yes, No, Can't tell and "I don't
understand the question", with a few words on why. A criterion's decision comes
from its questions: every question Yes is a pass, any No a fail, otherwise it
cannot be judged, and a question the reviewer did not understand leaves it
undecided. A question about a reply the application rejected, or a turn never
sent, is answered for the reviewer. The workspace's own screens are folded under
each reply, named by what they show.

Reviewers' answers save as they go, under their own account; only the reviewer
and the page's owner can read them. As the owner, you see everyone's progress on
the page and save each reviewer's `review.json` from it, or collect them all
with `--collect` (see the skill), then check each with `review_evaluation.py
--review`. Opened as a file, `index.html` also works offline.

The review never calls a model. It shows the replies the evaluation run
recorded, so it reviews whichever model that run used; with `--provider
anthropic`, `evaluate_semantic.py` uses Claude Haiku 5.5 unless `--model` says
otherwise.

`evaluations/screens.py` replays every run through the real workspace. It
rebuilds the case from the run's own inputs and the replies recorded in the
report. Each evaluated turn's words are put in the answer box and sent as a
person sends them: Send, or the Other moves entry for a turn that asked for
advice or an observation. A turn by another participant is sent from a workspace
opened as them, and every step carries its recorded time. The screens are
exported as each reply lands: Next step at 120×40 and 80×24, Case context, and
Trees or Backlog when they hold anything. The first turn also shows the question
with the answer typed in. The replay refuses to produce screens unless it
reproduces the recorded inputs, replies and revisions exactly.

The page carries no machine check, earlier review, scenario ID or score. Every
`review.json` it saves is the template's format, which `review_evaluation.py
--review` checks against the unchanged report as before.

Two fixture turns cannot be typed into the workspace as written. The workspace
has no control for declaring an owner or observed evidence, so the ownership
turns of `goal_action_review` and `evenings_loop` are sent the way the command
line sends them, and the page says the person formally stated being in charge. The evaluation cases accept proposals automatically,
so their screens show that setting, not the default of holding proposals in the
Backlog.

## Findings on 2 October 2026

The final provider-free gate passes **110 implementation tests**, **23 specification
regressions** and **all nine original p0 scenarios (50 steps)**. The verified-model
real-server recovery suite passes **37/37 checks**, covering timeout, nonexistent
model selection, truncation, context overflow, cached-response recovery and a
killed client. No feature text was changed.

Evidence is retained in these workspace directories:

| Evidence | Result |
|---|---|
| `.evaluation-runs/2026-10-02-semantic/` | Four semantic fixtures repeated twice; failures and an attributed developer review retained |
| `.evaluation-runs/2026-10-02-agent/` | Original skill repeated twice; incomplete submission and malformed tool/final responses exposed |
| `.evaluation-runs/2026-10-02-refined/` | Six correction/uncertainty turns saved; both normal agent submissions completed; one empty agent final response flagged |
| `.evaluation-runs/2026-10-02-recovery-verified/` | 37/37 real recovery checks pass after model-identity repair |
| `.evaluation-runs/2026-10-02-final-loop/` | Full loop repeated with the model/skill repairs; missing pilot/action/review records still block approval |
| `.evaluation-runs/2026-10-02-final-review/` | Final adapter publishes exact-test-linked observations; a missing review still fails the authored expectation |

The refined skill's eight cases complete the required capability traces and
effects; seven also finish with a valid final explanation. The other run ends
with an empty model reply after correctly stopping on failed retention. This is
recorded as a failed agent response, not a saved case or a silently repeated
consultation.

The initial measured run reproduced the earlier semantic gap and additionally
used an input identity as a case-context formulation reference. The application
rejected the whole proposal, retaining input and the prior state. Subsequent
prompt changes ask about success and protections, explicitly account for
contributions as sourced records, and separate source/formulation namespaces.
The provider contract guides those namespaces and meaningful-input accounting;
the domain remains the validator. The adapter freezes and hashes its resources
so editing a prompt during a session cannot change its recorded policy silently.

Regression testing also caught shared mutable arrays in the schema projection:
refining source constraints could accidentally refine goal protections.
Independent array schemas and a specific regression test repair this defect.

Real recovery testing uncovered a server fallback: a request naming a
nonexistent model returned a completion whose `model` was
`google/gemma-4-e4b`. The adapter now verifies the configured model against the
[server's advertised model list](https://lmstudio.ai/docs/developer/openai-compat/models)
before generation and requires the response model to match. A nonexistent model
cannot publish a revision under false provenance. Response mismatch, missing
identity and later explicit recovery have dedicated HTTP regressions.

The final-loop replay exposed one domain defect: required test references
accepted null, so orphan observations could be published. Required goal/test
relationships now require nonempty exact references in both the domain validator
and its generated schema. The same correction rejects null defining statements,
note text, measurement/value and review assessment. Optional baseline, scope and other missing context can
remain unknown. A captured real negative proposal is checked through application
use cases, demonstrating all-or-nothing rejection while retaining the input.
The earlier synthetic trace preserves the defect as historical evidence; it is
not a valid current-format handoff. No production case was used in these tests.

Live Gemma results still vary. Some valid proposals omit a provisional goal,
prospective pilot, action or review, while describing those concepts in prose.
In a seeded review the model computed 80% delivery and 90% acknowledgement but
asked about expansion without prominently addressing the 95% protection breach.
Valid JSON and durable publication therefore remain insufficient for approval.
The complete v1 semantic gate is **not passed**.

P1's persistent workspace/action bindings and p2's complete loop, goal version
transitions, local action completion, complete acceptance coverage and participant
study remain implementation/release work. The current runtime is the p0 slice;
its data profile name `p2` does not imply that the later phase is delivered.

## Usable skill entry points — 3 October 2026

[Skill usage](skill-use.md) now covers real-case contribution/retry commands,
offline receipts, an optional bounded local model agent, and a project-scoped
Codex MCP connection. The single procedure resource ships in the wheel and is
discovered through repository symlinks; an isolated wheel installation verified
its references and server construction outside the checkout.

The latest complete gate passes **129 implementation tests** with the optional
MCP SDK on Python 3.12, **23 specification regressions**, and **all nine original
p0 BDD scenarios (50 steps)**. Python 3.9 passes 128 implementation tests with
the one optional-SDK transport test skipped, plus the same specification/BDD
checks. Both runs retain the original scenario selection and feature text.

The added adapter tests exercise actual command subprocesses and an official SDK
stdio client: exact multiline text and attribution, independent consultation,
restart, explicit retry, idempotency, failed retention, incomplete/false agent
claims, case-root boundaries, source/export operations and preserved consulting
intents. Model/schema fixtures prove integration behavior, not semantic quality.

Live evidence is retained in `.evaluation-runs/2026-10-03-skill-entry/`:

| Evidence | Outcome |
|---|---|
| `agent-simple.json` | Gemma executes inspect → retain → consult against a real consultant, publishes revision 1, and finishes the procedure |
| `reopened.json`, `already-applied.json` | A fresh process reads revision 1; retrying the applied identity makes no new consultation |
| `mcp-live.json` | Actual stdio MCP contribution calls the real model, saves revision 1, restarts and confirms idempotent retry |
| `procedure-failure.json`, `procedure-recovery.json` | Default procedure retains input before an unavailable model call; explicit retry with Gemma saves the same identity at revision 1 |
| `agent.json`, `agent-verified.json` | Gemma tries to shorten prefixed literal text; the host blocks the change, including with an exact-value tool schema |
| `failure.json`, `retry.json` | A second retained input survives provider failure and a subsequent invalid proposal; original published history remains unchanged |
| `check-p0.log`, `check-p0-python39.log` | Complete regression/BDD results on both supported environments |

Because the orchestration model can still change tool arguments, the normal
command defaults to the existing deterministic procedure driver. `--runner
agent` is an explicit experimental selection; no failure silently switches
runners or repeats semantic requests. Application publication status and agent
completion are reported independently. This delivers the own-case skill entry
point, not the unfinished TUI or a passed v1 semantic quality gate.


## Conversational interface verification on 3 October 2026

The complete gate passes **147 implementation tests**, **23 specification
regressions**, all **nine original p0 scenarios (50 steps)** and **seven new
conversation scenarios (30 steps)**. On Python 3.9 it passes 146 tests with the
optional MCP SDK transport test skipped; both Gherkin suites and the 23
specification checks still pass. Original feature text and phase membership are
unchanged. The gate now rejects skipped, undefined or missing conversation cases
as well as missing p0 coverage.

Conversation acceptance runs through application use cases: open without
inference, retain literal attributed replies against the displayed question,
resume/explain/inspect offline, reject stale replies, deliberately choose an
alternative consulting intent, compare original forecasts with observations and
safeguards, inspect historical state, and project only explicit record links.
Adapter tests compare CLI and MCP workspace data/renderings, use the official SDK
stdio transport, check numeric receipt ordering, preserve unknowns and escape
untrusted diagram labels. Model prose cannot change the renderer's save status.

Synthetic evidence is retained under
`.evaluation-runs/2026-10-03-conversation/`:

- `live-turn-1.json` and `live-turn-2.json`: two actual Gemma consultations save
  revisions 1 and 2 (14.3s and 17.6s), retain literal input and reopen identically.
  The second goal leaves scope/measure/horizon/protections as unstructured wording;
  the view correctly shows those structured fields as not recorded. This is
  interface/adapter evidence, not a passed semantic-quality review.
- `authored-workspace.json` and `.md`: a deterministic four-turn fixture shows
  the original 80%/95% forecast, reported 80%/90% outcomes, the recorded safeguard
  breach, work completed and expected attainment unknown.
- `authored-diagram.svg`, `.png` and `diagram-check.json`: generated reference
  graphs parse and render in a real Chromium browser with Mermaid 11.12.0.
  Quoted/markup-containing stored labels remain literal text with no added nodes
  or executable scripts. Graphs use the documented [Mermaid flowchart syntax](https://mermaid.js.org/syntax/flowchart.html).

The existing `my-case` was inspected read-only; its revision 1 was not resubmitted
or modified. It has a note and question without graph references, so no diagram
is invented. The packaged skill now presents a continuing conversation over the
shared workspace; a fresh Codex chat must load the updated MCP tool catalog.
The full p1 TUI contract (a first slice now ships), later typed causal/conflict graphs, full v1 consulting quality
and participant/assistive-technology release gates remain outstanding.


The updated wheel also built in an isolated build environment and passed an
installed-package check outside the checkout: the shared workspace, renderers,
MCP schemas and packaged conversational skill are available. The official-SDK
client read `my-case` through the actual stdio server and confirmed every case
file's SHA-256 remained unchanged (`own-case-read-check.json`).


## Legacy LTP continuation conversion

`adapters/ltp_conversion.py` and `scripts/convert_ltp_case.py` convert a validated
LTP 1.0 document offline through normal create/attach/submit/export capabilities.
The single designated root becomes a native goal; legacy entities, designations,
relationships, assumptions and assessments remain labeled source-report notes,
with original bytes and an ID mapping retained in the portable bundle. Ownership,
observed status, action completion, native graph semantics and historical
application revisions are not inferred. Duplicate keys/IDs, dangling references,
ambiguous goals, unsupported schemas/change logs and existing destinations are
rejected before publication.

The next/explain projection now uses the intervention's saved relevant context;
full reasoning remains available locally. This avoids presenting the entire
import archive as the next conversational turn. Twelve conversion tests exercise
source/provenance preservation, historical qualifications, unknowns, immutable
continuation, portability, focused reads and rejection boundaries. The actual
Rufus–David source produced a validated native baseline; a disposable portable
copy accepted a follow-up with an authored consultant, preserving revision 1.
Live consultation on the full imported case requires adequate model context: the
local Gemma was loaded at 8,192 tokens during conversion. No model inference or
model reconfiguration was used to convert it.


## Live trees check with Anthropic (2026-10-05)

A billed run of `claude-sonnet-5-5` through `reason_commons.bootstrap` in a temporary
case (not under `~/ReasonCommons`), seven provider calls in all. No key, request body
or provider response is recorded here; the case text below is the four synthetic
messages sent as "Sam".

**First smoke: `rejected`.** `scripts/check_anthropic.py --smoke` made a successful
HTTP call (no HTTP error) but the application refused the proposal: the model
returned `"schema_version": 1` (a number) where the domain requires the string
`"1"`. The tool schema said `{"const": "1"}` without a type; LM Studio's strict
grammar forces a string, but Anthropic tool input is not constrained. Replaying the
saved proposal offline through a stub consultant reproduced `InvalidCase: Proposal
belongs to an unsupported schema or delivery profile`, and the same proposal with
`"1"` saved. The receipt only says "invalid or out-of-profile response rejected",
so a participant cannot see this cause.

**Fix (authorized):** `domain/contract.py` types `schema_version` and
`delivery_profile` as `{"type": "string", "const": ...}`, the Anthropic transport
prompt names the string, and `tests/test_domain.py` fails without the contract
change. The domain check is unchanged. Full `check_p0.py` passed; the smoke then
returned `saved` at revision 1.

**Tree check, per message** (all four `saved`, revisions 1-4):

| # | Sam said | Recorded | Next question |
|---|---|---|---|
| 1 | "Our orders ship late because priorities change daily, so jobs get interrupted halfway." | Current reality: effect "Orders ship late."; causes "Jobs get interrupted halfway." and "Priorities change daily."; chain priorities → interrupted → late. Also a note and a *provisional* goal with no measure, horizon or protections. No assumptions. | What does success look like (how many on time, by when) and what must not suffer? |
| 2 | "Sales wants us to change the plan the moment a customer pushes; production needs a stable plan to finish anything." | Conflict: need "Production can finish jobs." requires "Keep a stable plan"; "Change the plan the moment a customer pushes" conflicts with it. Note. No assumptions. | What is Sales protecting by changing right away, and what if the change waited? |
| 3 | "To protect the plan we could freeze each day's schedule by 9:00 and keep two urgent slots open." | Future reality: one change "Freeze each day's schedule by 9:00 and keep two urgent slots open.", basis `hypothesis`. No effects or links. | How many urgent pushes on a typical day, and what happens to one after 9:00 or when both slots are taken? |
| 4 | "First step: next Monday I'll tell sales about the 9:00 freeze and the two urgent slots." | Transition: action "Tell sales about the 9:00 freeze and the two urgent slots (planned for next Monday)." No link to the change. | What do you expect to change in two weeks, and what would tell you it is hurting something? |

**Faithfulness.** Statements are close to Sam's words and marked `reported`, except
the 9:00 freeze, which Claude correctly marked `hypothesis` ("we could"). Small
liberties: "finish anything" became "finish jobs"; the cloud boxes gain
parenthetical "(what Sales wants)" / "(what production needs)"; the "because"
chain was split into three statements. Claude invented no numbers, owners,
assumptions or effects, and each next question asked for what Sam had not said.
The one inference is the provisional goal in message 1 ("orders ship on time, while
protecting important conditions not yet named"), labelled provisional by Claude but
never stated by Sam.

**Drawing** (`reason-commons trees <case> --width 100`):

```text
Goal Tree  What must be true for us to reach the goal?
Nothing in this tree yet.

Current Reality Tree  Why are we not there yet?
UNDESIRABLE EFFECT  reported
Orders ship late.
└─ because ─ CAUSE  reported
   Jobs get interrupted halfway.
   └─ because ─ CAUSE  reported
      Priorities change daily.

Evaporating Cloud  What conflict keeps us stuck?
NEED  reported
Production can finish jobs.
└─ requires ─ WHAT WE THINK WE MUST DO  reported
   Keep a stable plan (what production needs).
WHAT WE THINK WE MUST DO  reported
Change the plan the moment a customer pushes (what Sales wants).
⚡ conflicts with: Keep a stable plan (what production needs).

Future Reality Tree  If we change this, will it work, and what could go wrong?
CHANGE WE MAKE  hypothesis
Freeze each day's schedule by 9:00 and keep two urgent slots open.

Prerequisite Tree  What stands in the way, and what comes first?
Nothing in this tree yet.

Transition Tree  What exactly do we do next?
ACTION  reported
Tell sales about the 9:00 freeze and the two urgent slots (planned for next Monday).
```

**Judgement.** Honest and correctly placed, but only partly a useful picture. The
current-reality chain is right and readable. Nothing is invented or in the wrong
tree. What is missing: the cloud has two of its five boxes (no Sales need, no
shared objective) and its link has no assumption; the freeze has no link to "keep a
stable plan" even though Sam said it protects the plan, and no expected effects; the
Monday action is not linked to the freeze and has no owner or date field; the Goal
tree is empty although a provisional goal was recorded; the Prerequisite tree is
empty. The drawing therefore shows six disconnected fragments, not one argument,
and the freeze → stable plan → fewer interruptions chain Sam implied is not
drawn. One run of four short messages; this is not a measure of consulting quality
across cases, and a different run may record or link differently.

## Live check of withdrawals, citations and test versions (2026-10-07)

A billed run through the CLI and `reason_commons.bootstrap` in a temporary case
(`/tmp/rc-live3`, not under `~/ReasonCommons`), messages sent as "David". No key,
request body or provider response is recorded here. The symptom, cause and link were
brought in with a local LTP import (no provider call), so the calls went to the rules
under test (S148–S150).

**Model choice.** `claude-haiku-4-5-20251001` was tried first as the cheapest model.
One of its five replies was valid. The other four were rejected before commit:
updates sent as a string, a link to a note instead of a statement, and intervention
fields (`purpose`, `required_context_refs`) placed at the top level of the proposal.
It is not workable with this proposal contract today. `claude-sonnet-5-5` (the
default) then made nine calls, all `saved` on the first attempt.

| Rule | What happened | Result |
|---|---|---|
| Test versions (S150) | Asked to change the forecast before the start, Claude proposed `P1@2` replacing `P1@1`. After acceptance the Tests view showed one test (8 of 30), history kept 6 of 30, and the action was flagged (`new_version`). The reported result and its review cited `P1@2`. Asked to change the forecast after the result, Claude recorded only a note and said the forecast "has to stay as it was", offering a new test instead. | Pass (the domain refusal was not needed) |
| Withdrawal (S148) | Claude proposed `X1@1` withdrawing the cause. `decide accept X1@1` returned `confirm` with `leaves: [L1@1]` and changed nothing; with `--confirm` the cause and its link left the tree. Under automatic acceptance, a new cause and its link entered automatically; the withdrawal of that cause (`X2@1`) waited in the backlog while its note was accepted. | Pass |
| Citations (S149) | An answer was held, a different answer moved the case on, and the held answer came back `stale` with no call. The next request (asking for advice) was not sent the stale answer, no record cites it, and the advice did not use its wording. (In the run before the fix, the same sequence put the stale answer's words into the model.) | Pass |

## Semantic scenarios with Claude (2026-10-07)

A billed run of `scripts/evaluate_semantic.py --provider anthropic --model
claude-sonnet-5-5 --repeat 2` (`.evaluation-runs/2026-10-07-semantic-sonnet/`,
report SHA-256 beginning `cba484d0ddf398df`): 16 fixtures covering the twelve
`@semantic` p2 scenarios, twice, 32 cases and 44 provider calls, each attempted
once. No key, request body or provider response is recorded here.

Machine checks: 285 passed, 5 failed. Two failures are a harness error: the
guardrail case's pilot-review check was also applied to its second turn, which
asks a question and needs no new review (turn 1's review passes in both
repetitions); the check now applies only to the reporting turn. The other three
come from one reply: in `attributed_correction-2`, Claude's third reply put a
`decision` field at the top level of the proposal, and the application rejected
it before commit, so that turn has nothing to judge. Every other reply was saved.

A review page shows each case's turns, records and next move beside its
criteria; its decisions are turned into `review.json` and checked with
`scripts/review_evaluation.py`.

### Review (2026-10-07)

The 108 criteria were reviewed by Codex, recorded as "AI semantic reviewer": an
attributed review, but not the human review this record asked for. It was
validated against the unchanged report (`review.json` and `reviewed.json` in the
run directory): 92 pass, 15 fail, 1 can't judge (the rejected turn). The
semantic status is **fail**, so these scenarios are not passed.

| Pattern | Criteria failed |
|---|---|
| A move bundles separate asks instead of one prominent next move | goal_action_review c3 (both runs), realistic_blame c3 (both), realistic_mixed c3 (both) |
| The reply returns to the setup's pilot question instead of the new input | realistic_twelve c3 (both) |
| After Priya's correction, the move returns to framing success instead of investigating the mechanism Priya described | attributed_correction c2 (both) |
| Asked whether acknowledgement shows fulfilment, the reply asks how to check it but not for an acceptable bound or who decides | guardrail_review c5 (both) |
| The move does not ask who may authorise the pilot | immediate_action c3 (both) |
| At an immature review date, the move does not ask for the pending outcomes or when to look again | immature_cohort c2 (run 1) |

The reviewer also judged run 1's turn-3 advice to "count the first days as a
baseline" misleading, since those days already run under the new queue.

Some notes cite review-guide rules that the guide's revised version removed as
stricter than the criterion text: "simply repeating the setup question" (both
realistic_twelve failures) and requiring all four fulfilment items (both
guardrail_review c5 failures). Those four decisions may change under the revised
guide; the other eleven failures follow the criterion text either way. The v1
participant gate stays separate.

## Semantic scenarios with Claude, prompt 7 (2026-10-07)

After the review above, the consultant prompt (now version 7) asks for one thing
per next move, takes up corrections and new information before earlier
questions, asks who may decide before other gaps of an unowned test, and treats
outcomes still pending at a review date as pending. The domain context records
that a correction of a question's premise comes before framing success (S06
over S01). Two rubric lines no longer suggest an answer or a pronoun, and four
held-out fixtures test the same behaviour in other words.

The same billed command, now 20 fixtures twice
(`.evaluation-runs/2026-10-07-semantic-sonnet-prompt7/`, report SHA-256
beginning `556517ca34f50a18`): 40 cases, 52 turns, each attempted once. Machine
checks: 318 passed, 4 failed, all from one reply. In `goal_action_review-1`,
Claude's first reply put the next move's fields at the top level of the
proposal; the application rejected it before commit and the case stopped, so
its seven criteria have nothing to judge. Every other reply was saved.

A rough signal, not a judgement: under prompt 6, 16 of 45 next moves asked more
than one question (counting question marks in the prompt); under prompt 7, none
of 51 did, held-out cases included. The 138 rubric criteria wait for review on
their own page; until then these scenarios are not passed.

### AI pre-screen (2026-10-07)

The 138 criteria were pre-screened by Claude in a handoff session, recorded as
"AI semantic pre-screen". It is attributed, but it is not the human review this
record asks for, and a Claude session was grading a prompt change that another
Claude session wrote. It was validated against the unchanged report
(`review.json` and `reviewed.json` in the run directory): 128 pass, 3 fail and 7
can't judge (the seven criteria of `goal_action_review-1`, whose first reply was
rejected). The semantic status is **fail**, so these scenarios are not passed.
The judging was blind: the runs' machine checks, the first review and the
question-mark count were read only after every criterion was decided.

| Pattern | Criteria failed |
|---|---|
| The S102 recommendation leaves out one of its four parts: the need it serves, or its expected effect | immediate_action c1 (run 2: the 90% goal is not named), heldout_immediate_action c1 (run 1: the 85% forecast is not named) |
| A move bundles separate asks | goal_action_review c3 (run 2, turn 3: who may decide and which team would run it) |

Close calls passed, with the concern recorded in their notes:
`attributed_correction-2` c3 (after "I don't know", the move sets the mechanism
aside with a reason and returns to framing success, though Priya could still
answer) and `heldout_correction-2` c3 (links inferred from Priya's account,
with the inference stated as an assumption). Outside any criterion,
`goal_action_review-2` turn 4 records "Sam states he has authority", a pronoun
nobody gave.

Against the first run, fixture by fixture over the 16 shared fixtures (pass of
the criteria in both runs; the first review was Codex's under the earlier guide):

| Fixture | Prompt 6 | Prompt 7 |
|---|---|---|
| goal_action_review | 12 of 14 | 6 of 14 (7 can't judge) |
| attributed_correction | 3 of 6 (1 can't judge) | 6 of 6 |
| guardrail_review | 10 of 12 | 12 of 12 |
| inconclusive_review, classify_* (5 fixtures) | 20 of 20 | 20 of 20 |
| blaming_question | 6 of 6 | 6 of 6 |
| realistic_cannot | 8 of 8 | 8 of 8 |
| realistic_twelve | 6 of 8 | 8 of 8 |
| realistic_blame | 6 of 8 | 8 of 8 |
| realistic_mixed | 6 of 8 | 8 of 8 |
| two_explanations | 4 of 4 | 4 of 4 |
| immediate_action | 6 of 8 | 7 of 8 |
| immature_cohort | 5 of 6 | 6 of 6 |
| Total | 92 of 108 (15 fail) | 99 of 108 (2 fail) |

The four held-out fixtures: 29 of 30 pass (heldout_correction 8 of 8,
heldout_new_information 8 of 8, heldout_immediate_action 7 of 8,
heldout_immature_cohort 6 of 6). Of the first review's failure patterns, only
the bundled move fails again, once. The S102 omission is new: both
immediate_action runs passed c1 under prompt 6; under prompt 7, two of the four
S102 runs (one tuned, one held out) leave out a part while asking who may
decide. The rejected first reply is also new. Two guide
rules differ from the first review's (the reworded immediate_action c3, and
"as needed" for the S105 fulfilment items), so the comparison is not exact.

## Semantic scenarios with Claude, prompt 8 (2026-10-07)

The prompt 7 pre-screen found recommendations without the need they serve or
their expected effect, a record that gave Sam a pronoun nobody stated, and a
reply rejected for its shape. Prompt 8 asks a recommendation for its four
parts, refers to participants by name or as they, asks only who may decide
to start an unowned test, and the Anthropic transport names the proposal's six
top-level fields. Strict tool use was tried for the shape and dropped: the API
refuses this contract's 45 optional and 68 union-typed fields (limits 24 and
16).

The same billed command (`.evaluation-runs/2026-10-07-semantic-sonnet-prompt8/`,
report SHA-256 beginning `25a49052da1552eb`): 40 cases, each reply attempted
once. Machine checks: 332 passed, 6 failed, all from two rejected replies, each
the only evaluated reply of its case: in `attributed_correction-1` the next
move carried a field it does not have (`purpose_note`), and in
`blaming_question-1` the next move's fields were beside the intervention
object. Their six criteria have nothing to judge.

Mechanical signals, not judgements: no record or next move uses a gendered
pronoun, and no next move asks more than one question (48 ask one, 4 none).
The rejected replies did not fall: one in 44 under prompt 6, one in 52 under
prompt 7, two here. Each attempt is made once by design, so a rejected reply
costs its case; in use, the operator retries the retained input. The 138
rubric criteria wait for review on their own page.

## Claude Haiku 5.5 as the consultant (2026-10-08)

The question was whether `claude-haiku-5-5`, at $0.10 / $0.50 per million input and
output tokens for prompts up to 100K tokens (Sonnet 5.5: $2 / $10), can consult well
enough. Billed runs with the key read from the environment; no key, request body or
provider response is recorded here. All data is synthetic.

**Starting point.** An agent following `evaluations/live-claude-test-prompt.md` with
Haiku and adapter 1 (4096 output tokens, no effort sent, so Haiku's default
`medium`) saved 8 of 12 replies. Two rejections named an invented intervention
field (`kind_note`, `intervention_goal_placeholder`); two said only "invalid
structured response", because a reply the adapter refused carried no reason.

**What changed.** Adapter 2 allows 16000 output tokens, which the model's thinking
shares (`REASON_COMMONS_ANTHROPIC_MAX_TOKENS`), sends effort `high` where the
model reports support for it (`REASON_COMMONS_ANTHROPIC_EFFORT`), gives every
adapter rejection a reason (`max_tokens`, a refusal and its category, no proposal
call) and names the intervention's only fields. Adapter 3 lists each record kind's
fields from the domain registry, stops asking for "the string \"1\"", and undoes
lossless slips in how the call's arguments are passed; prompt 9 tells the model
when basis `observed` is allowed (a rule the domain enforced but never explained)
and which records take `replaces`. Adapter 4 fills an envelope field left out
(each has one valid value per consultation; a wrong one is still refused), unwraps
a lone wrapper of any name, and drops literal refs from the example shape. The
semantic harness gained two fixtures from the live procedure's open-evenings
conversation (`evenings_trees`, `evenings_loop`), and `scripts/evaluate_procedure.py`
replays that procedure's fourteen consultant steps in review mode.

| Run (`.evaluation-runs/2026-10-08-…`) | Model, adapter, settings | Replies saved first time | Cost per reply |
|---|---|---|---|
| `semantic-haiku55-4096-default` (`842caca2…`) | Haiku, 2, 4096 tokens, effort default | 45 of 64 | $0.0030 |
| `semantic-haiku55-high` (`45a6c883…`), repetition 1 | Haiku, 2, 16000, high | 26 of 33 | $0.0042 |
| `semantic-haiku55-adapter3` (`cf608d58…`) | Haiku, 3, 16000, high | 64 of 68 | $0.0042 |
| `semantic-haiku55-adapter4` (`c0b6dfb6…`) | Haiku, 4, 16000, high | **70 of 72** | $0.0042 |
| `semantic-sonnet55-adapter3` (`f276de5b…`) | Sonnet, 3, 16000, high | 36 of 36 | $0.051 |
| `semantic-sonnet55-adapter4` (`f5075876…`) | Sonnet, 4, 16000, high | 31 of 33 | $0.050 |
| `procedure-haiku55-adapter3` (`d0bfb3e6…`) | Haiku, 3 | 24 of 28 | $0.0056 |
| `procedure-haiku55-adapter4` (`f9446019…`), 3 repetitions | Haiku, 4 | **42 of 42** | $0.0058 |
| `procedure-sonnet55-adapter3` / `adapter4` (`5c01c759…`, `fa8216f2…`) | Sonnet, 3 and 4 | 14 of 14, 14 of 14 | $0.073 |

Each reply is attempted once, so the share saved is first-attempt validity. Costs are
from each run's recorded token usage at list prices, with no prompt caching (the
tool schema is rebuilt for each request, and tools come first in the cached
prefix). A partial Sonnet run on adapter 2 (13 of 13) was stopped to spend on the
final adapter.

- **The 4096-token cap explained the unexplained rejections.** Under it, 7 of 19
  rejections were `stopped at max_tokens (4096)`, among them the open-evenings
  conflict reply, the live procedure's step 5. At effort `high` Haiku's replies
  averaged about 5,000 output tokens and reached 9,500; Sonnet's averaged 1,600.
- **What Haiku still gets wrong is the record shape, not the reasoning.** On adapter 4
  both rejections added a field a review does not have (`review_date`, and
  `source_refs` inside the review's data). Earlier runs showed the same class
  (`scope`, `stop_condition` on reviews; `replaces` on a note), a reference to a
  record listed later in the same reply, and once updates sent as a string of JSON
  that was itself broken. All were refused before commit with the input kept.
  Sonnet's two rejections on adapter 4 are of the same class (`temp_orary_id`,
  `proposed_updates_note`). No transport repair was needed in any adapter 4 run;
  the wording changes stopped those slips, and the repairs remain a safety net.
- **Machine checks.** On adapter 4, Haiku passed 423 of 432 and Sonnet 194 of 201.
  Every failure but one follows from a rejected reply. The exception is Haiku's
  `classify_never_started-1`: the reply recorded the pilot's action as `blocked`
  but no review, so the pilot was not classified as untested. The procedure replays
  passed every check on both models, the prompt-injection guard included.
- **Time.** At effort `high` Haiku took about 22 seconds a reply in the semantic
  fixtures and 28 in the procedure replay; Sonnet took 11 and 15.

### AI pre-screen (2026-10-08)

The rubric criteria of the adapter 3 and 4 Sonnet runs and the adapter 4 Haiku run
were pre-screened blind by separate Claude subagents under the same written
instructions, recorded as "AI semantic pre-screen" in each run's `review.json` and
validated into `reviewed.json`. This is not the human review the gate requires,
and the agent that wrote the prompt changes chose the reviewers' instructions.

| Run | Pass | Fail | Can't judge (rejected reply) |
|---|---|---|---|
| Sonnet, adapter 3 | 77 | 4 | 0 |
| Sonnet, adapter 4 | 70 | 2 | 9 |
| Haiku, adapter 4 | 150 | 8 | 4 |

Haiku's failures: classifying a review's outcome, its weakest area (a 60%
result against an 80% forecast left without a verdict; a never-started pilot
called inconclusive rather than an implementation failure; an unknown denominator
called pending; 9 of 31 left "pending" twice), and the Evaporating Cloud (needs
merged with their actions, the injection placed in another tree, the unstated
objective neither recorded nor asked about). Its 4 can't-judge criteria are its
2 rejected replies. In both `evenings_loop` runs Haiku held back the review
because each input is dated today, 8 October, while the test starts on
16 October: a fixture artefact, since the inputs carry the real date, which
three of the four immature-cohort runs also noticed.

Sonnet's failures across both runs: after Sam's "I don't know" the move returns
to framing success instead of a feasible observation (`attributed_correction`,
both runs); the Cloud's unstated objective is neither recorded nor asked about,
and once the injection was placed in the Future Reality Tree only; one review did
not classify its result as supported; one direct-advice turn offered no options.
Both Sonnet reviewers noted a formulaic fall-back to "who may decide" as the next
move.

The prompt changes above were made while watching these fixtures; the four
held-out fixtures and the procedure replay check them elsewhere, but these numbers
are not independent of the tuning. Samples are small, the semantic status of every
run is `fail` or `incomplete`, and the participant gate is separate.

## Haiku by default, one Sonnet reply, and the cost meter: live smoke (2026-10-08)

The final smoke of the [plan](plans/2026-10-08-haiku-default-boost-usage.md), billed,
with the key passed by reference and a usage log of its own in a throwaway folder
(`REASON_COMMONS_USAGE_LOG`). No key, request body or provider response is recorded
here, and the key was found in none of the run's files. All data is synthetic.

1. **`scripts/check_anthropic.py --smoke`** saved revision 1 on `claude-haiku-5-5`
   (15,709 tokens in, 1,437 out, ≈ $0.0023) and, with `--model claude-sonnet-5-5`,
   on Sonnet (15,711 in, 592 out, ≈ $0.037). Each report gives its `usage` and
   `estimated_cost_usd`.
2. **`reason-commons usage`** counted the two replies, one each of Haiku and Sonnet,
   both under "provider check", ≈ $0.04 in all.
3. **The workspace**, opened by `tui.run()` itself (the same composition, settings,
   usage session and consultant factory as `reason-commons tui CASE --provider
   anthropic`) and driven headlessly by Textual's pilot at 120 by 40, since an agent
   cannot press keys in a live terminal. The budget was $0.06, not the plan's $0.02:
   the two smokes had already spent $0.04 this month, so $0.02 would have made the
   first Send ask, where the plan's order has the question come after the Sonnet
   reply; $0.06 keeps the plan's $0.02 of room.
   - On opening, the footer said "Haiku 5.5 · month ≈ $0.04 of $0.06".
   - **Send** (Haiku): the top line said "Asking Claude…", the notice "Saved. 3
     proposed; they wait in Backlog. Reply ≈ $0.0031 (Haiku 5.5).", the footer
     "session ≈ $0.0031 · month ≈ $0.04 of $0.06" (the model's name gives way when
     the bar is short), and the hint "Send: get Claude's reply (Haiku 5.5)".
   - **Commands › Send with deeper reasoning (Sonnet 5.5)**, whose line read "Asks the
     consultant: Sonnet 5.5 answers this one, then Haiku 5.5 again; ≈ $0.05, about 12×
     a Haiku reply": the top line said "Asking Claude (Sonnet 5.5)…"; the notice "Saved.
     2 proposed; they wait in Backlog. Sonnet 5.5 answered (≈ $0.05). Send goes to Haiku
     5.5 again.", and a second notice "This month's Claude replies ≈ $0.09, past your
     $0.06 budget (estimate). Each send will ask first; nothing is blocked." The
     stand-in was put away after the reply.
   - The next **Send** asked first: "This month ≈ $0.09 of your $0.06 budget
     (estimate). This reply ≈ $0.0042." **Not now** sent nothing, kept the draft in the
     box and the revision as it was, and said "Nothing was sent. Your answer is still
     in the box."
   - **Consultant calls and cost** showed 2 calls in this goal (the third had not been
     sent), the last reply as Sonnet 5.5 with 17,039 tokens in and 1,548 out
     (≈ $0.05), this session, today and this month (4 replies, ≈ $0.09, past the
     budget: Sonnet 2, ≈ $0.09; Haiku 2, ≈ $0.0054), "Haiku 5.5, the default", the
     list-price date, the Console as the authority and the log's place.
   - **Send** again, then **Send this one**: Haiku answered (≈ $0.0032).
4. **`inspect --json`** gave the applied requests in order: `in000001` Haiku,
   `in000002` Sonnet, `in000003` Haiku.
5. The log then held five billed requests, ≈ $0.096 (Haiku 3, ≈ $0.0086; Sonnet 2,
   ≈ $0.087; provider check 2, workspace 3), no unreadable line, and only its own
   keys; it held no words of the case or its name. Neither the case's files nor its
   `.reasoncase` export held a token count or a cost.

Not yet done: comparing the log with the Anthropic Console a day later, as the plan
asks; the Console is the authority on what was billed. The workspace was driven by
the pilot, not by a person at a terminal, and notices were read as the app raised
them (Textual's headless screenshots do not draw them).
