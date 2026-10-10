# Reasoning Commons

This is the sole bounded context in the first increment. It owns the durable
record of a consultation, independently of a consultant's conversation memory.
The product contract in `reason-commons-spec/reason-commons-specification.md`
and its scenario-local delivery tags remain authoritative. This glossary maps
that contract onto executable code; it does not change acceptance scope.

| Term | Meaning and owner |
|---|---|
| Commons | One named reasoning workspace containing its goal, contributions, sources, reasoning, decisions and complete history. It persists across conversations. The aggregate root. |
| Conversation | An exchange of participant contributions and consulting replies within a commons. It develops the commons; it is not the whole workspace or its model. |
| Revision | A complete snapshot, published only after validation and durable writes. A consulting revision applies one reply: its next question and its proposals. A decision revision records one decision of the operator's and nothing else. |
| Intervention | The consultant's stored next question, recommendation, or justified stop. An internal record, not a numbered user-facing document. |
| Response target | The exact intervention the participant is answering, together with its base revision. |
| Input | Literal participant text, declared speaker, target, intent and any explicit structured declarations. Retained before any provider call. |
| Source | A retained input or supplied attachment. Interpretation cites sources; it does not replace them. A reply cites only the input it answers, inputs already applied and supplied attachments; an input that went stale before its reply was published is not part of the commons, and the consultant is not shown it. |
| Goal | A sourced statement of success, with scope, horizon, measure, baseline and protections. Missing values stay unknown. A commons has one goal; it is the Goal Tree's top statement, and a different or reworded goal is a new version of it (`G1@2` replaces `G1@1`). |
| Note | Sourced literal prose or a bounded interpretation, with its evidence basis. It cannot contain executable later-profile structures. |
| Test | A bounded change tied to an exact goal, with an original prospective forecast. It may name the tree claim it carries out (`claim_ref`). Until a result for it is in the model it can be given a new version (`P1@2` replaces `P1@1`); from then on its forecast is fixed, and a changed plan is a new test. It may record the pilot's own baseline, its dose and an alternative explanation; its review reads ten fields (owner and scope, intervention and dose, baseline and cohort, exact prediction, measurement method, observation window, protected conditions, stopping conditions, alternative explanation, review date), each unknown until someone records it. A review date is a date, never a reminder. |
| Action | Proposed work for an exact test, with the state it should bring about (`expected_state`). Ownership requires cited explicit input. Recording that it was done is a new version (`A1@2`) with execution completed; its expected state cannot be marked met or not met until a result for its test is in the model. |
| Observation | A sourced result for an exact test, retaining measure, scope, denominator and period where supplied. It cites the test's current version. |
| Review | A bounded assessment referencing the original test and relevant observations. |
| Breach | A reported result outside a bound recorded with the test's forecast for the same measure ("at least 95%" against "18 of 20"). It is judged only when both are plain numbers in the same unit; otherwise nothing is said. It stays pinned in every view, whatever the display density. |
| Provisional goal | A goal with no measure yet. It is labelled provisional wherever it is pinned, until a measure is recorded. |
| Tree | One of the six thinking-process trees (goal, current reality, conflict, future reality, prerequisite, transition), in the LTP 1.0 vocabulary. A tree is the current state of its claims and links; it is derived, never stored as a whole. |
| Claim | One sourced statement placed in one tree with a role that belongs to that tree (any role but goal), and an optional evidence basis. Rewording records a new version of the same statement (`C3@2` replaces `C3@1`); its links follow it. |
| Link | One explicit, typed relation between two statements, with an optional stated assumption. It belongs to one tree, and at least one of its statements is in that tree; the other may come from another tree and stays one statement in both. It records what someone asserted; it does not prove causality or necessity. |
| Retraction | Withdraws a claim or link from its tree with a reason. Accepting the withdrawal of a statement also takes the links that join it out of the trees; the operator sees them before confirming, and automatic acceptance leaves such a withdrawal waiting. The withdrawn record stays in history. |
| Proposal | A record a reply (or an import) added that waits for the operator's decision. It cites its source and may carry the consultant's confidence, which decides nothing. |
| Membership | Whether a record is in the model: proposed, accepted (in the model), rejected, undone or closed. Accepting admits a record into the working model; it does not make it true, record a belief or authorize an action. |
| Model | The accepted records that are current: not replaced by an accepted newer version and not withdrawn. Pending and rejected proposals, undone acceptances and earlier formulations remain in the commons' history without belonging to its current model. Records published before the commons kept decisions are in the model by definition. |
| Decision | One choice of the operator's, recorded with who and when: accept (with the waiting proposals the chosen ones need, and for a withdrawal the links that join the statement), reject (with the waiting proposals that need them), undo (with whatever cannot stand without it), still holds, or the acceptance setting. Rejections and undos are final. |
| Acceptance setting | How a commons admits proposals: held for review (the default) or accepted automatically, recorded as the operator's decision. Automatic acceptances are recorded as such, with the reply they came with. |
| Backlog | The waiting proposals and open review flags, in the order they are best decided: what an entry cites first, then a new goal, the six trees in method order, tests, actions, observations, reviews and notes, older first. |
| Review flag | A record in the model that cites a record which has since been given a new version, withdrawn or undone. Derived from explicit references; it changes nothing, and it closes when the flagged record changes or leaves the model, or the operator says it still holds. |
| Applied request | A retained request whose validated reply was published exactly once. |
| Attempt | A provider/recovery receipt, separate from reasoning history. |
| Cursor | Presentation state and draft, separate from reasoning. Navigation cannot commit reasoning. |

`model.py` owns the closed v1 schema, exact-reference validation, explicit-input
authority, append-only records and decisions, and the response-target rule.
`membership.py` derives what is in the model, what waits, readiness, the
backlog's order, review flags and what a decision takes with it. The application
owns identity/time allocation, the retain → consult → validate → publish protocol
and the decision use cases. Storage owns how both become durable. Skills own none
of this truth.

Existing API and archive identifiers use `case`, `case_id`, `CaseApplication`,
`CaseCapabilities` and `.reasoncase` for compatibility. They refer to a commons,
not a different domain concept. Participant-facing language uses **commons**.

Every published revision preserves prior records and decisions byte for byte at
the file level and unchanged at the model level. Original forecasts cannot be
edited by a later proposal: a test can have new versions only until a result for
it is in the model. Records are appended with exact formulation
references (`C3@1`); a new version keeps the identity and raises the version
(`C3@2`), and the older formulation stays in history. A test that serves an older
version of the goal is flagged for review when the goal changes.

## What enters the model

A reply's updates are proposals. They change nothing in the model until the
operator accepts them, unless the operator set the commons to accept proposals
automatically; only the operator changes that setting, and a reply cannot. A
proposal is ready when everything it cites is in the model. Accepting takes the
waiting proposals it needs; rejecting takes the waiting proposals that need it.
A proposal that can never be accepted (it cites something rejected or undone, or
an earlier version that was already replaced) is closed by the decision that made
it so. Undo appends a decision that takes the accepted records out of the model
with whatever cannot stand without them (the links of an undone statement, a
test's work); records that only rely on them are flagged. Accepting a withdrawal
likewise takes the links that join the withdrawn statement, and the operator sees
them before confirming; under automatic acceptance such a withdrawal waits. A reply
may cite only the input it answers, inputs already applied and supplied
attachments. Decisions recorded while
the consultant works do not make its reply stale; only a newer question does.

A change flags only what explicitly cites the changed record, so consequences
travel one reviewed step at a time. A consultant may draft amendments for open
reviews; they are proposals like any other. Suspected consequences that no
reference records stay questions or proposals.

Declared attribution is not authenticated identity. Structured declarations
represent explicit participant input; no text parser or consultant may infer
ownership from prose. Hypotheses, participant reports and explicitly supplied
observations remain distinct. No group agreement or stance capability is
available in this slice.

Trees record what participants said about causes, needs, conflicts, obstacles and
actions, one claim and one link at a time. Each link joins exactly one claim to
another, so a joint premise group (AND) cannot be expressed yet; it stays in a
note. A link, a tree's shape or a completed tree is not evidence, consensus or a
diagnosis of the constraint. Tree records cite only earlier, current claims, so
the history of a tree reads in order. A test that names the claim it carries out
connects the loop to the trees; its forecast and results remain the test's own.

## Consulting semantics

When no goal has been formulated, symptoms do not establish an agreed goal or
a causal explanation. A provisional qualitative goal can make the desired
direction visible while its measure, scope, horizon and baseline remain unknown.
The first consequential decision is what meaningful success would look like and
what must be protected. Ranking symptoms is not a substitute for that decision.
Attributed notes account for information that cannot yet become a stronger claim.
A participant's correction of a question's premise comes before that decision:
the next move investigates the mechanism they describe, in neutral terms, and
framing success waits for a later move. A next move asks for one thing.

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
establish attribution. `goal_ref`, `test_ref`, `claim_ref`, `from_ref`, `to_ref`,
`replaces`, `target_ref`, `observation_refs` and intervention
`required_context_refs` cite exact **commons record** formulations (`G1@1`, `P1@1`,
`C1@1`, etc.), or a `temporary_id` declared by another update in the same proposal.
They may cite records in the model or still waiting, never records that were
rejected or undone. `from_ref` and `to_ref` may cite the goal.
An input ID is never a required-context record. Use an empty list if there is no
relevant commons record yet. Do not allocate stable IDs in a consultant proposal.
