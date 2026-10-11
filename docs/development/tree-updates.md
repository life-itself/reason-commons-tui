# Every change is a proposed tree update

Reason Commons is developed with Reason Commons. A change to this repository is an
injection into the development commons, so it needs the same thing RC asks of any
participant: a reason in the trees. This page is the protocol a person or agent
follows before writing code. [Feature arguments](feature-arguments.md) defines the
notation; this page says when to use it, when to recommend against a request, and
how the participant accepts or rejects the proposal.

The participant decides. An agent proposes, recommends, and records the decision.
It never silently builds unargued work, and it never silently refuses either.

## 1. Classify the request before touching files

Every request falls into one of four kinds. Say which one in the first reply.

| Kind | Meaning | What happens next |
|---|---|---|
| **Argued** | It carries out a Transition Tree action in an existing argument | Name the proposal and the action, then follow the [workflow](workflow.md) |
| **New argument** | It changes behavior, scope or the development method, and no argument covers it | Reply with a proposed tree update and wait for the participant |
| **Upkeep** | No reasoning changes: a bug fix restoring specified behavior, a refactor without behavior change, dependency or tooling maintenance, wording, regenerated artifacts | State the upkeep reason and proceed |
| **Not explicable** | No recorded or reported problem, necessary condition or action makes it useful | Recommend against it (section 3) |

A feature request is never upkeep. When in doubt between upkeep and a new argument,
treat it as a new argument; a small argument costs less than an unexplained feature.

## 2. Find what is already argued

Look before proposing, so a new argument extends the existing trees instead of
duplicating them:

- argument blocks in the repository:
  `grep -rl RC-ARGUMENT-BEGIN reason-commons-spec/features tests/conversation/features docs/development/arguments`;
- the development commons, when it exists on this machine, read only:
  `reason-commons show ~/ReasonCommons/reason-commons-development --view trees`.
  Its Goal Tree holds the accepted necessary conditions, including *keep the
  interface minimal* and *keep unused models and hypotheses from overwhelming the
  work*. Never write to it without the participant's explicit go-ahead;
- the reconstructed development record in
  [working-import.md](../restoration/working-import.md).

## 3. Recommend against what the trees cannot explain

Recommend against a request, and do not start it, when any of these holds:

- it serves no necessary condition in the Goal Tree and removes no reported
  undesirable effect, and the participant cannot name one;
- it adds interface, options or reasoning inventory without an undesirable effect
  it removes, against the minimal-interface and inventory conditions;
- it builds future scope (p5–p7) or a speculative capability with no current
  report behind it;
- a smaller injection, or one already argued, addresses the same effect;
- its benefit depends on an assumption that recorded evidence already contradicts.

Say which test failed, name the smaller alternative or the missing report, and ask.
The participant may still proceed. Then the argument records their words as a
source and the agent's objection as a negative branch or an explicit assumption,
so the disagreement stays visible in the trees instead of disappearing into code.

## 4. Reply with the proposed tree update

For a new argument, the first reply contains no edits. It contains this, in plain
language, small enough to read in a minute:

```text
Proposed tree update: <proposal-id> (proposed; nothing built yet)

Serves     <the Goal Tree condition, existing or new>
Problem    <the undesirable effect, in the participant's quoted words> [UDE]
           because <suspected cause> [cause; hypothesis]
Conflict   <a real cloud, or "none established">
Change     <the injection> [injection]
           predicts <desired effect> [DE; needs evidence]
           risks <negative branch> [NBR]
First      <what must be true before it can work> [IO]
Build      <transition actions: what will be written> [action]
           observable as <effect a test can check> [effect]
Not argued <the trees deliberately left out, and why>

Accept, reject or edit?
```

Keep it proportionate. A small change can be one quoted report, one injection, one
action and stated absences for the other trees. Completing all six trees is never
required. Distinguish what the participant said from what the agent suspects, as
the [notation](feature-arguments.md) does.

## 5. After the participant answers

- **Accept:** write the argument block into the owning feature, or for a change to
  the development method, tooling or repository practice, into
  `docs/development/arguments/<proposal-id>.feature`. Link scenarios with
  `@addresses_`, `@implements_` and `@verifies_` tags. Then implement through the
  [workflow](workflow.md). Acceptance in conversation authorizes the work; it does
  not adopt the reasoning. The block stays `status proposed`: adoption is the
  participant's decision in the development commons Backlog, after the change is
  used.
- **Edit:** revise the proposal and ask again.
- **Reject:** build nothing. Say so in one line.

## 6. Name the tree update in every commit

Each commit that touches a guarded path ends with a trailer:

```text
Tree-update: contribution-feedback
Tree-update: upkeep - regenerate screenshots after the theme fix
```

The first names an argument present in the repository. The second declares upkeep
and its reason, which a reviewer can dispute. Guarded paths are the code, the
specification, the procedures, the scripts and the development method; the list is
`GUARDED` in [check_tree_updates.py](../../scripts/check_tree_updates.py).

Check a branch before opening a pull request:

```sh
python3 scripts/check_tree_updates.py --base main
```

To have Git reject an unargued commit as it is made, enable the repository's hooks
once per clone:

```sh
git config core.hooksPath .githooks
```

The full gate validates every argument file under `docs/development/arguments/`.
It does not read Git history, so the trailer check stays a separate step. Neither
check judges whether an argument is good; that remains the participant's review.
