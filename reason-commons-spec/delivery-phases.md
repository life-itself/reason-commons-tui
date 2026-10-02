# Delivery phases and release gates

V1 proves a useful goal–action–review loop. Its user does not need graph controls,
formal participant stances, six trees, or TOC vocabulary. V1 already provides
a persistent full-screen workspace, literal response
editor, visible local controls and readable forecast/outcome review. Typed graph
schemas and formal tools arrive later; the TUI itself is not deferred.

Section 0 of the main specification defines the v1 boundary. The JSON manifest
locks the selected scenario IDs and artifact profiles. Changing that scope is
an explicit specification decision; tagging a later scenario `@v1` is not a
shortcut around it.

## Tag contract

Every scenario or outline has exactly one delivery tag `@p0` through `@p5`,
exactly one release tag `@v1` or `@later`, and exactly one evaluation tag:

- `@automated`: deterministic fixtures, validator/routing/state invariants,
  fake adapter, and observable call counter.
- `@semantic`: authored and real-adapter proposals assessed against invariants
  and a professional rubric. Passing a canned fake reply is insufficient.
- `@usability`: a participant protocol and individual results; it cannot pass
  from automated step execution alone.

`@Snn` preserves the scenario identity and `@Jnn` links jobs. Release, phase,
and evaluation tags are scenario-local; they are forbidden on Feature or
Examples blocks to avoid accidental inheritance. An outline has one delivery
scope for all rows. Mixed-scope outlines must be split, as S07 and S90 are.

Tags select sets. They do not order scenario execution or provide runtime
feature flags. Each scenario uses an isolated fixture; no scenario depends on
another having run. Phase dependencies belong to delivery milestones. Tags and
boolean filters follow the [official Cucumber reference](https://cucumber.io/docs/cucumber/api/#tags).

## Ordered increments

| Phase | Build and validate | Incremental exit gate |
|---|---|---|
| p0 Durable minimal case | Goal/note/intervention/test/action/observation schema; immutable ancestry; preserved inputs; atomic publication; idempotent retry; stale response rejection; one writer; portable export/import; profile validation | Restart and round-trip reproduce the supported records and original forecast offline. Failed writes and invalid/out-of-profile proposals commit nothing. No provider call follows failed input retention. |
| p1 Persistent TUI | Event loop; pinned case/goal/task/footer; literal multiline editor; keyboard controls; local inspection; async completion notices; focus/draft restoration; 80×24; linear alternative; profile-aware Actions | Default launch opens the workspace. Tab/arrows/Enter/Esc complete ordinary work without commands. Input is literal; navigation makes zero calls; pending output does not steal focus. Resize, resume and failure preserve draft and target. |
| p2 Complete v1 loop | Goal/baseline/protections; public decision purpose; attributed corrections; bounded forecast; immediate action and authority; effect observation; prospective review; next decision | The v1 session is reproducible with a fake adapter; a real adapter preserves semantic invariants; first-time users complete and explain the goal–action–review loop. |
| p3 Causal release | Typed partial CRT, WIP integration, assumptions, evidence detail, comparisons, feedback episodes, goal-connection and revision-review views; optional coaching/density settings and structured authoring forms | New causal scenarios and p0-p2 regressions pass. Users preserve joint premises, challenge a mechanism, distinguish alternatives, and notice changed-premise reviews. |
| p4 Facilitated group release | Exact-version representation/belief/reliance; declared speaker switching; scoped Cloud; reported versus direct attribution | New group scenarios and p0-p3 regressions pass. No silence, reported opinion, or willingness to test becomes invented belief or consensus. |
| p5 Full-tools release | Goal hierarchy, FRT and negative branches, PRT criteria/dependencies, TT rationale/contingencies, shared requirements, cross-tool traceability and review | New full-tool scenarios and p0-p4 regressions pass. Users trace the goal connection, review adverse paths, distinguish necessary states from sufficient action plans, and choose a changed-case action. |

All increments need their selected automated, semantic, and participant checks.
P0 fixtures exercise the case engine through a test driver; they do not require
the p1 TUI. Later phases can reuse those records without depending on another
scenario's execution. Shared Background steps use only capabilities available
by the earliest selected scenario in that feature.
Ship v1 after p2. Later releases require evidence that their additional structure
helps a recurring user decision; they do not delay v1 merely because their
specifications exist. Notifications, authenticated simultaneous users,
remote synchronization, and external execution have no delivery tags and remain
outside this roadmap.

## V1 participant gate

Use at least five first-time participants with varied terminal and domain
experience, including an accessible linear text workflow. Begin at the default
v1 TUI current
question without a manual at both 120×40 and 80×24. Repeat the linear workflow
with assistive technology users; an ASCII screenshot is not accessibility
evidence. Core navigation tasks use visible controls, not command prompts:
inspect purpose and stored
source, return to the question, type the literal answer `5`, choose local versus
consultant options, preserve a draft, quit, and resume. At least four of five
complete those tasks within 15 minutes without moderator commands. Everyone
predicts the provider boundary before selecting an action. Any accidental call,
wrong test/version, lost draft, focus theft, clipped premise or concealed breach blocks release.

Separately give them the complete loop: state success and protections, identify
the next action and authority, specify an observation and stop condition, resume,
and review an unchanged forecast. They must distinguish completed action,
observed effect, pilot target, and system goal. Record individual performance,
repairs, missing conditions, and reasoning. These are proposed gates and small
formative samples, not claims of measured usability or population effectiveness.
Test consequential fixes with new participants.

The existing all-tree and structured-position protocol in section 6a applies to
later releases. Comparative display studies in S112 need their own size and
prepared rubrics; a five-person navigation round does not establish their effects.

## Selection and regression

The structural checker can list scope before any step definitions exist:

```sh
python3 reason-commons-spec/check_bundle.py --select v1 --list
python3 reason-commons-spec/check_bundle.py --select p3 --list
python3 reason-commons-spec/check_bundle.py --select through-p4 --list
```

`p3` lists only the new increment; `through-p4` includes every earlier phase.
`v1` is exactly p0-p2. A later release must run cumulative regressions, not only
the incremental list.

Once a Cucumber runner and step definitions are implemented, use these tag
expressions with that runner's tag option:

```text
@v1 and @automated
@v1 and @semantic
@v1 and @usability
@p3 and @automated
(@p0 or @p1 or @p2 or @p3) and @automated
```

The last filter is the cumulative automated gate for p3. Run semantic and
usability protocols separately for the same cumulative release. Undefined or
pending steps are incomplete acceptance work; filtering them out does not meet
a release gate. Do not use an exclusion such as `not @later` as an alternative
to explicit scope, or use `@wip` to hide required failing scenarios. WIP in the
product means unconnected contributions and is unrelated to delivery status.

## Change discipline

1. Add a scenario to the smallest phase that can deliver it without later
   schemas, controls, views, or shared fixture setup.
2. Split an outline whose rows need different capabilities.
3. Review earlier fixtures and Background steps for later dependencies.
4. Update the manifest deliberately if v1 scope or an artifact profile changes.
5. Update view/scenario traceability and session ledgers, then run `--sync`.
6. Run structural validation and checker regression tests. Application behavior
   remains unverified until a runnable implementation and participant study exist.

Keep a short release report identifying the selected scenarios, their completed
checks, consequential failures, and the scope actually enabled by the runtime.
Do not treat a scenario tag or a passing document check as proof of implementation.

## Specification decision of 2 October 2026

P1 includes the persistent workspace; p2 completes the useful goal/action/review
loop. All three session specimens are full-screen interactions. Every human
acceptance scenario follows visible controls; the shell only launches or operates
offline utilities. The superseded CLI wireframes and shell transcript are removed.
The accessible ordered presentation shares the same actions, never a separate
command language. Product/executable/archive names are Reason Commons,
`reason-commons` and `.reasoncase`. Internal consultant contributions do not
become user-facing stationery objects. No graph/group requirement moves into v1.
