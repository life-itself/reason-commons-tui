# Reasoning Case

This is the sole bounded context in the first increment. It owns the durable
record of a consultation, independently of a consultant's conversation memory.
The product contract in `reason-commons-spec/reason-commons-specification.md`
and its scenario-local delivery tags remain authoritative. This glossary maps
that contract onto executable code; it does not change acceptance scope.

| Term | Meaning and owner |
|---|---|
| Case | One named reasoning workspace and its complete history. The aggregate root. |
| Revision | A complete snapshot, published only after validation and durable writes. |
| Intervention | The consultant's stored next question, recommendation, or justified stop. An internal record, not a numbered user-facing document. |
| Response target | The exact intervention the participant is answering, together with its base revision. |
| Input | Literal participant text, declared speaker, target, intent and any explicit structured declarations. Retained before any provider call. |
| Source | A retained input or supplied attachment. Interpretation cites sources; it does not replace them. |
| Goal | A sourced statement of success, with scope, horizon, measure, baseline and protections. Missing values stay unknown. |
| Note | Sourced literal prose or a bounded interpretation, with its evidence basis. It cannot contain executable later-profile structures. |
| Test | A bounded change tied to an exact goal, with an original prospective forecast. |
| Action | Proposed work for an exact test. Ownership requires cited explicit input; completing work is distinct from attaining an expected state. |
| Observation | A sourced result for an exact test, retaining measure, scope, denominator and period where supplied. |
| Review | A bounded assessment referencing the original test and relevant observations. |
| Applied request | A retained request whose validated proposal was published exactly once. |
| Attempt | A provider/recovery receipt, separate from reasoning history. |
| Cursor | Presentation state and draft, separate from reasoning. Navigation cannot commit reasoning. |

`model.py` owns the closed v1 schema, exact-reference validation, explicit-input
authority, append-only records and unchanged-base rules. The application owns
identity/time allocation and the retain → consult → validate → publish protocol.
Storage owns how that protocol becomes durable. Skills own none of this truth.

Every published revision preserves prior records byte for byte at the file
level and unchanged at the model level. Original forecasts cannot be edited by
a later proposal. The current p0 update registry appends distinct records with
exact `@1` formulation references. Later goal-revision and relevance use cases
will add version transitions without replacing historical formulations.

Declared attribution is not authenticated identity. Structured declarations
represent explicit participant input; no text parser or consultant may infer
ownership from prose. Hypotheses, participant reports and explicitly supplied
observations remain distinct. No group agreement, causal graph or stance
capability is available in this slice.

## Consulting semantics

When no goal has been formulated, symptoms do not establish an agreed goal or
a causal explanation. A provisional qualitative goal can make the desired
direction visible while its measure, scope, horizon and baseline remain unknown.
The first consequential decision is what meaningful success would look like and
what must be protected. Ranking symptoms is not a substitute for that decision.
Attributed notes account for information that cannot yet become a stronger claim.

A pilot prediction and a system goal are different comparisons. Preserve the
original prospective test, cohort, denominators, period and stop condition.
Action completion says work happened; it does not establish the predicted
effect. A comparable, implemented test may support or contradict a prediction.
Nonimplementation is an implementation failure; missing comparability or an
unknown denominator makes an outcome inconclusive. Address protection breaches
before recommending expansion. Changed suppliers or order mix remain possible
alternative explanations. Meeting an acknowledgement proxy does not alone
establish that all critical needs were protected.

## Reference namespaces

`source_refs` cite retained inputs (`in…`) or supplied source identities. They
establish attribution. `goal_ref`, `test_ref`, `observation_refs` and intervention
`required_context_refs` cite exact **case record** formulations (`G1@1`, `P1@1`,
etc.), or a `temporary_id` declared by another update in the same proposal.
An input ID is never a required-context record. Use an empty list if there is no
relevant case record yet. Do not allocate stable IDs in a consultant proposal.
