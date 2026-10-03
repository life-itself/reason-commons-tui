# Reason Commons architecture

The refined conversation fits Reason Commons directly: the app must preserve
reasoning correctly even if a skill is removed or a consultant misbehaves.
The first completed increment is **p0**, as selected by the existing delivery
manifest: all nine durable-case scenarios. V1 still ships after p2.

```mermaid
flowchart TD
  CLI[Offline CLI] --> App[Application use cases]
  Invocation[One-shot contribution command] --> Skill
  MCP[Local MCP tools] --> App
  TUI[Textual TUI, first p1 slice] --> App
  Agent[Agent using procedure] --> Skill[Skill adapter]
  Skill --> App
  BDD[Original p0 Gherkin steps] --> App
  App --> Domain[Reasoning Case aggregate]
  App --> Ports[Storage / consultant / clock ports]
  Ports --> FS[POSIX YAML and ZIP adapter]
  Ports --> Provider[Replaceable consultant]
```

There is one bounded context, [Reasoning Case](src/reason_commons/domain/CONTEXT.md).
Storage and consulting are capabilities, not invented business contexts.
A context map with artificial edges would add ceremony without defining a real
boundary. Add another context and a published contract when independent domain
ownership actually emerges.

| Authority | Location | Responsibility |
|---|---|---|
| Product behavior | Existing `.feature` files and delivery manifest | What must be observable in each increment |
| Domain language and invariants | `domain/CONTEXT.md`, `domain/model.py` | Valid records, references, attribution and immutable history |
| Architecture/control | This file, `.workflow.json`, architecture tests | Inward dependencies, owned paths and required gates |
| Application contract | `application/ports.py`, `application/service.py` | Retention, consultation, retry, inspection, cursor and portability |
| Procedures | `skills/reason-commons-contribute/SKILL.md` | How an agent chooses and sequences capabilities |
| Adapters | `adapters/` | Storage, offline CLI and a replaceable procedure driver |
| Composition | `bootstrap.py` | Choose adapters; create/open/import a case |

The domain imports only the standard library. The application imports the domain
and defines outbound protocols; it never imports an adapter or skill. Interfaces
use application use cases. Filesystem code serializes validated records but does
not decide consulting meaning. `tests/test_architecture.py` checks inward imports.
The workflow manifest is review/control metadata; it is not an OS sandbox.

## Interface guarantees

**Semantic parity:** Any domain-significant operation offered by a local
interactive interface must be expressible through the skill capability surface.
Interface-only state such as focus, viewport, expansion and caret position is
exempt. Both surfaces use the same application use cases, validation, attribution,
exact targets and persistence outcomes. A particular skill may use a subset of
capabilities, but its host surface cannot omit an operation merely because a
human normally initiates it. Parity provides expressibility, not additional
authorization or an automatic action.

**Projection, not authority:** The TUI is a projection and interaction
accelerator over application state. It defines no reasoning invariants,
consulting semantics or persistence behavior unavailable through application
use cases. It may arrange views, retain editor state, expose shortcuts and show
receipts. An application use case must enforce the same rules when called by a
skill, a test or another interface; a TUI confirmation, menu restriction or
validation hint cannot be the sole enforcement of a consequential rule.

`CaseCapabilities` publishes all current semantic use cases, including source
attachment and portable export, plus their local reads. Cursor checkpointing
and session lifecycle are explicit exceptions. The architecture gate checks
coverage and argument parity against `CaseApplication`: a new public use case
cannot silently remain outside the skill surface. Future TUI actions must call
these use cases; domain effects and local-versus-consultant routing are tested
at that boundary, while focus/layout behavior belongs in adapter tests. No TUI
is implemented in p0, so its future action bindings still need p1 verification.

## Application surface

`create_case`, `open_case` and `import_case` return an application session that
is a context manager. Every use case accepts/returns plain serializable values.
Callers get copies of state, not mutable aggregate/repository handles.

- `inspect`, `workspace`, `history`, `sources`, `receipts`, `storage_help`: local reads.
- `checkpoint`: saves view, caret, draft and exact target without a revision.
- `retain_input`: saves literal text, declared speaker and exact target/base.
- `consult`: invokes an injected provider only for durably retained input.
- `submit`: combines retention and consultation for a deliberate submission.
- `retry`: uses the retained identity; an applied request never calls again.
- `add_source`, `export`: local attachment and portable handoff operations.

The `CaseCapabilities` protocol is the shared semantic surface for skills and
local interfaces; it receives no repository capability. The contribution
procedure uses inspect, retain, consult and explicit retry, while other skills
can use the remaining capabilities. P0 has synchronous use
cases; p1 can invoke them in a worker while retaining UI focus. No event bus,
generic command dispatcher, service container or framework is necessary yet.

Result statuses distinguish `input_retained`, `saved`, `not_saved`, `unavailable`,
`rejected` and `stale`. Recovery actions are machine-readable control identities
for a future interface, rather than a prose parser. `saved` means manifest
publication completed, not that an LLM said the work succeeded.

## Shared conversation projection

`application/presentation.py` derives a presentation-neutral workspace from one
captured published snapshot. `workspace` is a local application capability with
view, optional historical revision and exact selection. Its JSON contains the
question, goals, stored references, original forecasts and actual observations,
attribution, explicit unknowns and action routes. It makes no inference or write.
Next/explain show the intervention's explicit saved context (or records from its own input when no context is declared); full reasoning remains a separate local read. Historical views exclude later records/input and consultant moves. Tests preserve
original forecast bounds and separate work execution from expected attainment.

`adapters/rendering.py` renders that same value as terminal text, chat Markdown,
comparison tables and Mermaid. It draws only explicit record references, escapes
untrusted labels and supplies no causal or consensus semantics. The CLI `show`
and MCP `workspace` share these renderers. Contribution/retry entry points attach
the post-operation workspace to the authoritative result, independently of model
prose. The packaged skill uses the projection for a continuing conversation,
local explanation/inspection, ordinary replies and explicit consultant moves.
Replies remain bound to the last displayed live target; no silent retargeting.
The future TUI can reuse the projection and supply its own layout and controls.

## Durability and recovery

The mutable manifest indexes hashes of complete YAML revisions. Each update
appends a candidate snapshot, fsyncs it and its directory, then atomically replaces
and fsyncs the manifest. Previous revisions are never replaced. `flock` holds one
editing session; a killed process releases it automatically. Read-only inspection
can coexist with a writer because published snapshots never change.

Inputs, supplied sources and attempt receipts are independently hashed,
append-only YAML records. Provider exceptions retain a category rather than
potentially secret exception text. Provider credentials are not stored.
The entire case and sources are explicitly supplied to the provider; no hidden
conversation is needed. The received proposal and provider version are retained
before validation/publication, so interrupted commits retry without another call.
The snapshot's applied-request ledger remains authoritative if receipt writing
fails after publication. Retry of an invalid proposal starts a fresh attempt;
retry of a stale input requires a new, explicit evaluation against the new base.

`allocations.yaml` durably reserves revision and object IDs before writing a
candidate. Crashes may leave gaps. Orphan candidates are never current history;
their reservations survive portable handoff so identifiers are never reused.
Failed retention keeps the literal input in session memory. Export to another
writable destination carries that text as an explicitly unretained draft.

Portable `.reasoncase` ZIPs contain published ancestry, reservations, inputs,
receipts, supplied sources and cursor. Import validates hashes, schema,
references, ancestry and member paths before creating an exclusively reserved
destination. It refuses existing destinations, duplicate entries, symlinks,
path traversal and oversized archives. Inspecting a bundle uses a temporary
read-only view and creates neither an editable case nor a writer lock.

The adapter targets local POSIX filesystems, tested on macOS. It does not provide
multi-host locking, Windows support or synchronized-folder merge semantics.
Hashes detect damage, not deliberate owner modification with recomputed hashes.
An fsync failure after rename can leave a visible but unconfirmed publication;
the operation reports `not_saved`. This is an operating-system durability limit,
not permission to show success before fsync. Idempotent recovery confirms the
published files and directories are flushed before it reports `saved`; continued
flush failures remain `not_saved` and never trigger another consultant call.

## Testing and increment boundary

`python3 scripts/check_p0.py` runs document consistency, the pre-existing checker
regressions, domain/storage/application/skill tests and **the original nine p0
Gherkin scenarios** through Behave. The runner locates external step definitions;
it does not copy, rewrite or weaken the feature files. It also verifies the exact
selected scenario identities and rejects undefined, skipped or pending p0 cases.
Fixture setup uses application use cases. Byte-level persistence checks inspect
archives returned by the public export capability.

Application acceptance uses a deterministic consultant fixture, with no LLM.
Separate skill tests record capability calls, ordering, forbidden access,
retention failures and resulting case state. The deterministic workflow driver
is a baseline; `LMStudioSkillAgent` also executes the actual procedure with a
real tool-calling model. Its bounded host exposes only capabilities authorized
for that invocation and records blocked requests as well as successful calls.
It cannot touch a repository or turn generated prose into a saved revision.
The live evaluator isolates procedure behavior with an authored downstream
consultant, then evaluates real semantic consulting and recovery separately.

`invocation.py` binds that same host to a real, selected case and consultant for
the `contribute`/`retry` commands. It reports application results independently
of model prose or agent-loop completion. The default procedure runner uses the
existing fixed-sequence driver. An explicitly selected agent runner executes the
Markdown procedure; it never silently falls back. The single skill source is a
packaged resource, linked from `skills/` and `.agents/skills/` so evaluations,
wheels and Codex use the same file.

`mcp_server.py` uses the optional official SDK for stdio transport, exposing the
published case capabilities to a client such as Codex. The bridge opens one
application session per call under a configured case root; it adds no persistence
or consulting rules. Domain validation, exact bases/targets and writer exclusion
remain in the existing layers. Its `context` read projects the owning artifacts,
rather than copying domain truth into the procedure. See [skill usage](docs/skill-use.md).

`LMStudioConsultant` is a real local HTTP provider adapter. It uses the domain
registry's JSON Schema projection and packaged consulting procedure/context,
requests structured chat output, and translates it to the existing `Consultant`
port. Model/endpoint/token configuration stays outside case state. Malformed or
truncated output has a distinct rejected-response receipt; transport failures
retain the existing unavailable/retry behavior. Local HTTP fixtures test this
adapter separately from provider-free application BDD. See the
[LM Studio guide](docs/lm-studio.md) for configuration and an opt-in live smoke test.

The [validation harness](docs/validation.md) now retains repeated multi-turn
local-model proposals, capability traces, actual-server failures and attributed
review criteria. Machine success is separate from semantic approval. Prompt and
context resources are frozen/hashed for each consultant session. The provider
grammar distinguishes source identities, existing formulation refs and named
temporary updates; domain validation still decides publication.

P0 is complete; p1 TUI, p2 consulting quality and the useful human review loop,
complete semantic acceptance and participant studies remain later work. The p2 envelope
name denotes the v1 **data profile**, not completion of p2 delivery behavior.
The conversational skill projects current saved record links; later typed graph/group semantics remain unavailable. No shell REPL or synthetic TUI is advertised. The
existing TUI design remains the p1 contract.


The offline legacy LTP continuation converter is a source-bound deterministic
proposal adapter. It uses existing public application operations, retains the
exact source and literal importing request, and publishes one imported baseline.
Unsupported structures are clearly labeled archival prose, rather than new
executable fields or invented domain types. Explicit legacy supersession does
not supply enough history to reconstruct original application revisions; future
contributions append snapshots through the ordinary boundary.
