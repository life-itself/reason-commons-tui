# Reasoning and acceptance in one feature

New development proposals keep their complete argument in the owning `.feature`
file. The first worked precedent is
[contribution feedback](../../reason-commons-spec/features/15_contribution_feedback.feature).
Reading that file should explain the reported problem, proposed change, reasoning,
implementation conditions, behavior checks and outstanding evaluations without
needing a chat transcript or a second rationale table.

The proposal is authored reasoning, not recovered history. The readable argument
retains literal source words and declared speakers separately from the
editor's interpretation. Its updates remain proposed. Test success neither adopts
the argument nor authenticates its causes, benefit or historical approvals.

## The correspondence

There are two different relationships:

1. **One authored update ↔ one proposed RC record.** Each claim and link has one
   stable `temporary_id`, one native `operation`, exact `data` and explicit
   `source_refs`. No importer may infer extra claims or links from scenario prose.
   Application allocation returns a concrete record reference for each authored
   identity. Preserve that binding when retaining an imported proposal.
2. **Scenario ↔ explicit argument references.** A scenario can check several
   necessary conditions; a condition can need several checks. These links are
   explicit rather than forced into an artificial one-scenario/one-claim rule.

The fixture tree updates in a scenario are distinct from the development argument
about why that scenario is worth implementing. S189 submits two authored fixture
claims to test update markers; it does not silently add its own development
argument to a participant's commons.

## Writing the argument

**Write for a person reading the proposal.** Begin with the reported problem and
candidate change. Use named Rules for the tree concerns and sentence examples for
the reasoning. The reader should understand what follows from what, under which
assumption, without knowing the application record schema. Keep sources at the end
of the argument and the acceptance scenarios after it. Do not put a storage payload
in front of the reader or make a second prose account that can drift from it.

Enclose the argument in `# RC-ARGUMENT-BEGIN` and `# RC-ARGUMENT-END`; each line is
a Gherkin comment. Inside it, use the following readable notation:

```gherkin
# rc-argument: schema 1 | proposal contribution-feedback | status proposed
#   @future_reality @argument
#   Rule: Future reality - what we expect the change to do
#     This is a prediction; participant evidence is outstanding.
#
#     @frt_benefit_route @produces
#     Example: A truthful receipt helps participants understand the outcome
#       When we show a truthful contribution receipt [injection frt_injection]
#       And assuming the receipt is readable and understood
#       Then we predict that participants understand what happened [DE frt_benefit]
#       But this prediction still needs usability evidence
```

These are explanatory argument examples, not executable acceptance scenarios.
Commenting them keeps them out of Behave's scenario inventory; the argument checker
parses and validates them separately. All acceptance identities and required steps
remain executable under their existing scope and evidence tags.

Each Rule has `@argument` and one tree tag. Its description supplies the context,
including an explicit absence where appropriate. Each Example has two ordered
tags: a stable link identity and its relation. Two annotated claims are its ends;
`And assuming` declares the assumption. A Background can declare unlinked claims.
Repeated claim identities must retain exactly the same sentence, role and source.
The checker collects each claim once, then its links; authors need not arrange the
argument in storage allocation order.

The compact annotations declare roles and identities. NC is a Goal necessary
condition; UDE and cause belong to the CRT; injection, DE and NBR to the FRT;
objective, obstacle and IO to the PRT; reality, need, action and effect to the TT.
A shared claim retains its own tree when referenced from another tree's Rule.
`David reports that` cites `user_report`; `Codex found that` and `Claude found that`
cite `editor` as a reported finding; other claims are hypotheses from `editor`. Fixed lead-ins such
as `we predict that` are presentation wording; the checker does not infer roles,
attribution or extra claims from free prose.

The Sources Rule contains literal doc strings and declared speakers. Preserve the
original text, including whitespace; do not silently reconstruct source bytes by
joining display lines. The parser retains support for the superseded YAML comment
representation, but new proposals use the readable form.

Use the domain's tree roles and relationship vocabulary. A participant report
stays a report; causal explanations and predicted effects stay hypotheses.
Do not invent observations, agreement, a constraint diagnosis, a complete Cloud
or a successful trial. A possible negative branch is not by itself a conflict.
An inherited goal can be explained as context without proposing its replacement.
Completing all six trees is never an entry requirement.

## Linking scenarios

Add scenario-local tags naming identities in the same argument:

| Tag | Meaning |
|---|---|
| `@addresses_crt_ude` | This scenario addresses the named reported problem; passing does not establish its cause or eliminate it for participants |
| `@implements_tt_receipt` | This scenario specifies the named Transition Tree action's delivered behavior; it does not record the action as executed |
| `@verifies_prt_outcomes` | This scenario checks the named implementation condition within its stated fixture scope |
| `@verifies_frt_benefit` | This evaluation tests the predicted benefit, using the evidence mode declared in the argument |

Gherkin is not inherently a PRT or TT. `Given` states context, `When` a trigger,
and `Then` an observable expectation. A contract can specify a Goal Tree condition,
test a CRT explanation or evaluate an FRT prediction. In this precedent, S188–S190
mainly cover PRT conditions and TT effects. S191 evaluates the FRT benefit and
negative branch; its participant evidence remains outstanding.

Do not promote a participant prediction to `@automated` merely because its receipt
or marker exists. Keep release tags and evidence modes separate. Every scenario
needs its existing identity, increment, release and evaluation tags too.

## Checking and eventual import

The full gate checks arguments through the bundle checker. Focused checks are:

```sh
.venv/bin/python -m pytest -q tests/test_feature_arguments.py
.venv/bin/python reason-commons-spec/check_bundle.py --select v1
```

The tooling in [feature_arguments.py](../../scripts/feature_arguments.py) reads
explicit records and binds symbolic citations to actual source IDs supplied by a
caller. A disposable application test retains those sources with `add_source`,
submits an explicitly authored proposal, and verifies exactly one pending record
per identity, including resolved link ends and source attribution. It makes no
live consultant call and changes no participant commons.

This establishes an executable correspondence, not a production Gherkin importer
or coding harness. A future interface must retain the complete original feature,
record the identity-to-reference binding, and submit through `CaseCapabilities`.
Membership decisions, revisions, retry and provenance still belong to the
application. Accepting the reasoning does not authorize code execution. Later
wording changes must use new record versions and retain the earlier source bytes;
rerunning tests must not duplicate an already imported proposal.

Legacy features remain valid without argument blocks; do not fabricate motivations
or historical tree records for the older specifications. Every new change that is
not upkeep needs an argument, and [tree updates](tree-updates.md) says when an
agent proposes one. A change to the development method, tooling or repository
practice has no owning product feature; its argument goes in an argument-only file
under `docs/development/arguments/`, which the full gate validates the same way.
