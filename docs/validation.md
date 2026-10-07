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
```

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
are rejected. Pending criteria and failures remain visible. A completed review
of these fixtures still cannot approve the unimplemented TUI or substitute for
five real first-time participants and assistive-technology testing.

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
