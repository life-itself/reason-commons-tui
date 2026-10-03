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
The workspace draws the loop under the pinned context (current step marked) and a
small workflow diagram on the welcome screen; record IDs stay out of the views. The
home screen offers a finished, fictional example built through `retain_input` and
`consult` with the built-in guide in a temporary folder that is removed afterwards.
The README now leads with screenshots rendered from the running workspace by
`scripts/render_screenshots.py`; developer material moved to `CONTRIBUTING.md`, and
`tests/test_docs.py` checks that README and docs links and images resolve.

