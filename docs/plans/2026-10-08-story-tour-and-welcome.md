# Plan: "A winter at Harrowfield": a story tour, and a welcome for every new goal

> Status: done on `claude/optimistic-hypatia-eutcgx` (stages 1 to 5), written and approved 2026-10-08.
> Line numbers below are as of the start of that branch and will drift; search for the named functions.
>
> **As built, where it differs from the plan below:**
> - *Part 1* opens on *Three months later* (the autumn's work, the board's decision to try a pilot), then
>   How this works, then the workspace; the monastery is introduced on its own short page before the
>   first koan. The prologue's first page offers Begin, Contents and Not now.
> - The *measure* is the wait for a bed after the decision to admit and discharges before noon, both
>   better by next winter; the guide copies it into the test's forecast.
> - *The two decisions* are each a statement and the link that joins it to its tree, so four entries wait
>   in Backlog. Joy's correction is a new root cause in the Current Reality Tree with its link (the
>   application asks to accept the two together when the link is chosen first), not a reword.
> - *The Prerequisite Tree's beat* points at the county's objection, so every beat that waits for a choice
>   names its statement and has a *Show me* button.
> - *The strip* names the part in its frame and has *◀ Back*, the step's own button, *Next ▶* (also F3,
>   named in the footer), *Contents* and *Leave tour*. A beat's button hides once what it opens is on
>   screen; in the loop, when the person is on another view, the button is *Back to the question*.
> - *Day three* gets its Monday ready while its opening page is read, in the workspace (a worker, with the
>   answers dated Monday), so a jump to it from Contents shows a page at once.
> - *Story pages* keep their choices right under their words; the top line reads *Reason Commons · guided
>   tour* with the part on the right. Every page fits 80 by 24 without scrolling except How this works.
> - *Deciding the last waiting proposal* used to leave the keyboard nowhere (the emptied list went with
>   it); it now stays on the page. This is the one change outside the tour and the welcome.

## Context

The guided tour today ("Practice: your first loop") is the ordinary workspace on an empty
practice goal with a coaching strip and Mira's example answers. A newcomer lands on
"Clarify the goal / What would count as better?" and asks *what goal? I thought this was a
tour.* It looks like starting a goal, has no situation to reason about, and assumes what only
the builders know. Reading the code, it is also out of step with today's proposals contract
(not yet confirmed by running it): the coaching never mentions **Accept all**, and views show
only accepted records, so the forecast-vs-result comparison it promises would not render;
*Finish tour* doesn't start a goal; Ctrl+Q quits the program; the consultant can be switched
mid-tour (`onboarding.py:334-379`, `tui.py` tour wiring). Ordinary new goals get no
orientation at all: TUI-UX-PLAN Step 3 deliberately removed it.

David's *Thinking Processes as Koans* supplies what the tour lacks: a real-feeling case
(Harrowfield General, always full, about to spend £9.4m on 24 beds), the six trees worked
through it, and 24 koans from an infirmary on a mountain pass that distil each move.

Outcome: a tour that is unmistakably a story — story pages that narrate, a role (**you are
Ruth Okonjo**, new Director of Patient Flow, 90 days), a lived-in goal whose six trees hold
the words of the people who work there — in which the user makes two real decisions and
runs one real loop whose forecast fails on day three. Plus a quiet, dismissable welcome on
every new goal's first screen. Decisions already taken with David: Ruth as the role; all
six trees plus one loop (~15 min, nine parts, skippable); a **non-blocking** welcome panel
(the spec forbids gating: spec §Orientation 415-417, tui-reasoning-design 21-22, S114);
one koan closes each part.

## Design principles (from the design docs and spec)

- **Opt-in, never gating.** The tour is offered, never required; the welcome never blocks
  typing, Send, browsing, help or leaving (S114, spec §Orientation). Nothing auto-advances
  or moves focus/view without a keypress (TUI-DESIGN "never moves the user's view").
- **The tour adds; it doesn't hijack.** The loop line keeps its one meaning (One spine).
  The tour speaks only in story pages and its own bottom strip.
- **Story first, then the tree, then the koan** — the koan document's own order.
- **Each tree is a plain question** the user already understands ("Why are we not there yet?")
  before it gets a name — the same question its page shows in the app (`trees.py:28`
  `TREE_TITLES`), and read the way the app draws it (*down*, `READING`), not the document's
  upward diagrams; roles in the app's words ("root cause · likely constraint", "change we
  make", "what we expect to see"). No acronyms on screen (no CSF/NC/UDE/CRT/FRT/PRT/INJ/NB/
  TOC/LTP).
- **Plain, short, unassuming.** Second person for Ruth, first person for choices, no
  exclamation marks, no blame ("every cause is a policy, not a person" — also spec 897-898).
  Never "card", "deck", "stack" (`check_bundle.py` rejects "card(s)" in spec-checked files):
  the narrative screens are **story pages**.
- **Never trapped.** Every workspace beat has *Next ▶*; every page has Back, Contents, Leave.
  Every question has *Example answer* with Ruth's words.
- **Projection, not authority.** Story pages are presentation (exempt from semantic parity).
  Everything written to a case goes through existing use cases; no domain or application
  change, no new `CaseCapabilities` method.

## The story in nine parts

Prologue pages → each part: an **opening page** (what happened, in story) → **the real
workspace** with the tour strip narrating 2–5 beats → a **closing page** (one koan, a one-line
key, the next part's question). Frame: it's week seven at Harrowfield; the trees are drawn;
two decisions are still open; the pilot starts Monday. Ruth walks back through what the team
found, one question at a time, then runs the first loop.

| # | Part (question) | Workspace moment | You do | Koan |
|---|---|---|---|---|
| — | **Prologue**: tour intro · *Harrowfield General* (Mr Pryce's 31 hours, 340 beds always full, £9.4m, 90 days) · *Everyone knows why* (five sincere, partly right voices; three faded campaigns) | — | Begin / Contents / Not now | — |
| 1 | **Ruth's workspace** — where do things stand? (opening page *Six weeks later*, then *How this works*) | Next step: pinned goal and safeguards, measure (the wait and before-noon discharges, not occupancy), loop line ✓ Goal ● Test, Views, History | Open History (who said what, when) | 1 Full Mats (+ one-time intro of the monastery) |
| 2 | **What must be true for us to reach the goal?** | Goal Tree; "No one occupies a bed they no longer need" holds up two branches; NC7's earlier wording "round on the sickest first" | **Reject** Graham's pending "Keep occupancy at 95% or more" in Backlog (necessity: paid per patient treated, not per bed filled) | 2 Must |
| 3 | **Why are we not there yet?** | Current Reality Tree; the core problem *leads to all 10 undesirable effects* | **Accept** Joy's pending correction (pharmacy) from the read-aloud; choose the core problem | 7 Ten Complaints |
| 4 | **What conflict keeps us stuck?** (three faded campaigns) | Cloud as five boxes; under them, the numbered assumption that holds the conflict together, "only the morning round can trigger a discharge" (false) | Choose the two action boxes in turn (a boxed Cloud can be chosen, never dims); read assumption (3) | 12 Yesterday |
| 5 | **If we change this, will it work, and what could go wrong?** | Future Reality Tree; the negative branch "freed beds harvested as savings" and its trim | Choose it | 15 Empty at Noon |
| 6 | **What stands in the way, and what comes first?** | Prerequisite Tree as a ladder; objections in the words of pharmacy, the county, junior doctors… | Read from the bottom | 18 A Map |
| 7 | **What exactly do we do next?** (Ward 7, on Monday) | Transition Tree, Ward 7; step 7 and what it expects to see | Choose step 7 | 22 What I Will See |
| 8 | **Monday: your first loop** | The guide's real questions: change, forecast, review date, stop → **Accept all**; action → **Accept all** | Answer as Ruth (or Example answer); the forecast is sealed | 17 By Thursday |
| 9 | **Day three** (story page: 4 of 11 kits ready; nobody wrote the take-home prescriptions; "pharmacy is slow") | Observe → Accept all; Review shows the **original forecast beside the result** → Accept all; Tests view | Report, compare, decide **adjust** (add step 7a) | 23 The Herbalist |
| — | **Twelve weeks later** (11%→38% before noon, 9h→3.5h; the week-10 bed closure stopped; the constraint moves to the county) | — | Start my own goal / Explore a real commons / Back to start | 24 Down the Mountain |

Example answers (Ruth's, adapted from the document): change = step 7 ("At 15:00 the registrar
confirms tomorrow's likely discharges; the list goes to pharmacy and transport by 16:00;
families are told"); forecast = "full kit ready by 08:00 for at least 8 in 10 of next-day
discharges, from the first week"; review = "Thursday, day three, at the 08:30 board round";
stop = "if any patient leaves without their medicines checked"; observation = "list at
pharmacy by 16:00 all three days, but only 4 of 11 kits ready at 08:00: no take-home
prescriptions written; no readmissions"; review = "Adjust. I forecast 8 in 10 and got 4 in 11;
safeguards held. Pharmacy wasn't slow: the step was missing a cause. Add 7a: the registrar
writes the take-home prescriptions at 15:00."

Tone samples (final copy lives in the tour script; David reviews it):

> **Harrowfield General** — Last January, Alwyn Pryce, 84, came in with pneumonia. Once
> doctors decided to admit him, he waited 31 hours on a trolley in a corridor. On the second
> night he became confused, and fell. Harrowfield has 340 beds, and every one is always full.
> The board is about to spend £9.4 million on 24 more. **You are Ruth Okonjo.** You started
> today as Director of Patient Flow. The board wants your answer in 90 days: are more beds the
> right call?

> **Everyone knows why** — … Each of them is sincere, and each is partly right. That is why
> none of it has led anywhere. You won't pick a side. You'll put their reasons where everyone
> can read them and argue with them. That is what Reason Commons is for.

## Screens (visual grammar: first-start's heading/lead/option rows; story strip's quiet band)

Story page (full screen; accent heading; plain body; koans as left-bar quotes like story
moments; option rows = bold label + dim detail; footer keys; right side "Part 3 of 9"):

```
 A winter at Harrowfield                                        Part 3 of 9
 Why are we not there yet?
 Weeks two and three. You spent them where things go wrong: the emergency
 department at night, the bed meetings, the wards at noon. You wrote down ten
 things that go wrong and asked of each one: what causes this? …
 ▸ Continue          open the tree
   Back · Contents · Leave the tour (it remembers where you were)
 ⏎ Choose   esc Back   f1 Help
```

Closing page: `At the pass` · ┃ koan ┃ · dim key ("Many complaints, one cause. A Current
Reality Tree is drawn to find it.") · "Next: if the cause is that plain, why has nobody fixed
it?" · Continue / Back / Contents.

Workspace during the tour: header `Harrowfield General … Ruth Okonjo · Tour` (Tour where
Saved would be); answer tag `Answer as Ruth Okonjo`; *Example answer* kept; *Finish tour*
gone; a bottom **tour strip** in the story strip's place and grammar:

```
 Tour · Part 3 of 9 · Why are we not there yet? (muted; first part bold, as in
                                                    the moment strip, tui.py:2699)
 On Ward 7, Joy Mensah stopped you: "You've missed pharmacy." Her correction
 waits in Backlog, marked proposed. Open it and accept it (a).
 ◀ Back   Open Backlog   Next ▶   Contents   Leave tour
```
A beat's action button (Open the Goal Tree, Open Backlog) moves the view only when pressed;
beats that wait for an event (reply, accept/reject, tree opened, statement chosen) advance on
it, and Next ▶ always works. Footer in the tour: `^q Leave tour` (back to the start screen,
not quit); consultant switching is hidden.

Welcome on every new goal (non-blocking), in the empty space **under** the answer box so
"the answer sits at the question" still holds; focus stays in the editor:

```
 ┌ Answer as David ───────────────────────────────────────────────┐
 │ e.g. I read for pleasure again, most evenings                  │
 │ Send ^s   Explain this   Other moves     Enter: new line · …   │
 └────────────────────────────────────────────────────────────────┘
 NEW HERE
 1  The guide asks one question at a time, here.
 2  You answer in your own words. Enter starts a new line; Ctrl+S sends.
 3  What it records comes back marked proposed, and enters your goal only
    when you accept it. History can undo it.
 4  The line at the top shows where you are: goal, test with a forecast,
    action, what happened, review. Views, on the left, show what's recorded.
 How this works   Hide this
```
It goes once the goal's first answer is sent; *Hide this* stops it for good (settings);
it shrinks to one line ("New here? How this works · Hide this") when the screen is short.
**How this works** is one shared page: a labelled sketch of the workspace (header, loop line,
Views, question, answer box, footer) with five numbered explanations; reachable from the
panel, Help (F1), Commands, and shown in the tour's Part 1. This realises the spec's own
first-screen control (M01/S01 `[How this works]`).

Start screens: first start lists **Take the tour** first and highlighted ("A short story at a
hospital that is always full. You play the person asked to fix it. About 15 minutes; leave
any time."), then Start my first goal, Choose who asks the questions first, Explore a real
commons; once the tour is finished, *Start my first goal* takes the highlight; the welcome
sentence loses its arrow-chain jargon. Help's "The screen" section (`tui.py:129`) points to
*How this works* instead of growing. Home's START becomes `+ New goal`,
`Take the tour · a story, about 15 minutes` (or `Continue the tour · Part 4 of 9`), then
`Explore a real commons: the Second Renaissance` (ids `new`, `tour`, `sample`).

## The Harrowfield goal (a lived-in case, packaged)

A prebuilt `src/reason_commons/adapters/stories/harrowfield.reasoncase`, built offline from
`stories/harrowfield.yaml` by the story builder (`adapters/story.py`), exactly as the Second
Renaissance story is, so History, Your words and Trees read as a goal that grew this way and
the engine validates every step. The YAML's header comment says it is a composite case from
*Thinking Processes as Koans*, numbers invented but typical (so no consent question, unlike the
real commons).

1. **Ruth's goal stage through the built-in guide** (goal, measure, safeguards → one goal
   record), as `sample.build_sample` does for Mira, so the guide can carry on later. Goal:
   "The people Harrowfield serves get timely, safe, effective hospital care, this winter and
   for the next ten." Measure, deliberately *not* occupancy, and covering what step 7 moves
   (the guide copies the goal's measure into every test's forecast, `guided.py:183`, and the
   review prints it above forecast-vs-result): "The wait for a bed after the decision to admit
   (median 7.5 hours now) and discharges before noon (11% now); 35% before noon on the pilot
   wards within eight weeks." Safeguards: 7-day readmissions within last year's range; nurses
   keep choosing to stay.
2. **Chapters by Harrowfield's people** (Ruth, Dr Haddad, Joy Mensah, Dr Marsh, Graham Teller,
   the Director of Nursing, pharmacy, the county, transport…) adding the six trees under that
   goal, each statement attributed to its speaker with their words from the document.
   Shapes the renderer needs: the Cloud is exactly five claims and five links (objective, two
   needs, two actions, `conflicts_with`) with the assumptions on the links, so it draws as five
   boxes (`trees.py:492` `cloud_lines`); the injections live in the Future Reality Tree as
   "change we make"; in the Current Reality Tree only the ten effects take
   `undesirable_effect` (intermediates are `intermediate_cause`) and the core problem is a
   `critical_root_cause` linked so it "leads to all 10 undesirable effects" (`trees.py:278`);
   joint conditions ("with the midday admission peak") become link assumptions; NC7 carries
   its earlier wording "round on the sickest first" (a reword). Avoid withdrawing linked
   statements (S148 makes such withdrawals wait even under automatic acceptance).
3. **Switch to review acceptance, then two pending chapters**: Graham's "Keep occupancy at 95%
   or more" (Goal Tree, under Viability) and Joy's pharmacy correction (Current Reality Tree).
   Accept all only takes the last reply's proposals (`tui.py:2405`), so these wait in Backlog
   for an individual a/r decision. Graham's is a claim plus its link to Viability, so
   rejecting it takes the link too: the use case answers `confirm` and the existing "Reject 2
   together?" dialog appears (the strip says so beforehand). Joy's is a reword of the
   pharmacy-blind root condition, so accepting it marks the statement REWORDED with her words.
4. **Handover**: a final intervention identical to the guide's *Choose a test* question
   (`purpose: guided:test_change`, prompt/decision/rationale from `guided.STEPS`). Without it
   the guide infers its step and turns the first answer into a note (`guided.py:127-132`).

Builder changes (adapter + script only): story name parameter in `load_story`,
`scripts/build_story.py <name>` and the archive path; optional guided seeding before chapters
with `StoryState.goal` taken from the case; a chapter flag that switches to review acceptance;
an optional handover step. All are opt-in: a fresh build of the Second Renaissance story must
still match its packaged archive (`tests/test_story.py:37-43`).

## Implementation

No domain, application or `CaseCapabilities` change; no `.feature` text change (the tour has
no scenarios today and is presentation; the welcome is non-gating, so S114/S117 still hold).
New code goes in new modules to keep `tui.py` (4178 lines) from growing.

| Where | What |
|---|---|
| `adapters/tour.py` (new) | Load and validate a tour script; a pure `Tour` state machine (position = part + beat; `observe(event)`, `next()`, `back()`, `goto(part)`); `prepare(case, script, part)` that fast-forwards a fresh copy to a part's starting state with existing use cases only — `submit` each earlier example answer through the guide, `accept` what the saved reply reports as `proposed` (`service.py:243`), and `reject`/`accept` the two pending records found in the Backlog by statement (repeating with `confirmed=True` after a `confirm`) — forward-only and idempotent; progress read/write in `$XDG_STATE_HOME/reason-commons/tour.yaml` (state, not a preference, so taking the tour before setup never retires the first-start screen; extract the state-folder rule inline in `usage.log_path` (`usage.py:45-47`) into a shared `state_folder()`; tests point `XDG_STATE_HOME` at a temp folder); the Textual pieces: `StoryPage` and `ContentsPage` screens and the `TourStrip` widget. |
| `adapters/tours/harrowfield.yaml` (new) | All tour copy: prologue pages, parts (title, question, opening page(s), beats `{say, button?, until?}`, closing `{koan, key, next}`), epilogue, Ruth's example answers keyed by guided step, the two decisions (record matched by statement), speaker, archive name. |
| `adapters/welcome.py` (new) | The `NEW HERE` panel widget and `HowItWorksScreen` (shared by the welcome, Help, Commands and the tour). The panel mounts in `#column` after `#response`; `fit_reading()` (`tui.py:1527`) counts its height in what the box takes, and folds it to one line, then hides it, when the reading area would drop below the question's height. |
| `adapters/story.py`, `scripts/build_story.py` | Generalise as above; add `stories/harrowfield.yaml` + built `.reasoncase` (package data already covers `stories/`). |
| `adapters/tui.py` | `ReasonCommonsApp(tour=<Tour>)` replaces the boolean: mount the strip where `#coach` was, header state "Tour" where "Saved" would be (`tui.py:1631`; Asking…/Answer ready unchanged), hooks that call `tour.observe` after a reply is applied, after `perform()` decisions, on view/tree change and statement choice (never moving focus); `#fill` (`fill_pressed`, `tui.py:2945`) reads the script's answer for the current guided step; remove `#coach`, `#finish`, coaching code; Ctrl+Q in the tour → leave to the start screen; hide consultant switching in Commands. Mount the welcome panel under `#response` on an empty case's first question when not hidden (not in tour/story); add *How this works* to Help and Commands. `GoalsApp`: first-start options (tour first, highlighted; new copy), START row "Take the tour" / "Continue the tour · Part N of 9". `run_tour()` imports the package into a temp folder (as `run_story` does), resumes at the saved part via `prepare`, returns `TOUR_HOME`, `TOUR_OWN_GOAL` or `TOUR_COMMONS`; `run_home` dispatches them. |
| `adapters/onboarding.py` | Delete `TOUR_PURPOSES`, `EXAMPLE_ANSWERS`, `TOUR_STAGE`, `COACH`, `tour_state`, `coach_text`; setup's final first-run choices name the new tour. `sample.ANSWERS` stays (screenshots, demo, tests). |
| `adapters/settings.py` | No structural change; new key `welcome: hidden`, set by *Hide this* exactly as `keep_theme` (`tui.py:1211`) does: in memory at once, written only once the settings file exists, so it never retires the first-start screen. |
| `adapters/accessible.py` | The welcome's four lines and *How this works* text on an empty case's first view. (A text-presentation tour is a follow-up; home and the current tour have none today.) |

**Moving through the tour.** *Next ▶/◀ Back* only move between pages and beats; they never
change the case. A beat that waits on the case (a reply, a decision) checks the case on entry,
so going back to a beat already done shows it done instead of waiting. *Contents* and *Continue
the tour* always start the chosen part on a **fresh copy** prepared to that part with Ruth's
answers ("Jumping starts that part fresh, with Ruth's answers for everything before it"):
`run_tour` loops — import the package into a temp folder, `prepare(...)` with a short-lived
session, open the workspace at that part — until the workspace returns an outcome. So the
user's own words are never kept across jumps or sessions; only the part reached is. Hooks:
`_submitted()` (`tui.py:3407`) after a reply, `perform()` (`tui.py:2338`) after a saved
decision, the view/tree switch and statement choice; none moves focus. A beat's button calls
the navigation that already exists — `show_view()` (`tui.py:2903`) and `show_tree()`
(`tui.py:3162`), as Commands and `scripts/render_screenshots.py` do — so it moves the view only
because it was pressed. The tour's copy runs on a story clock (Monday of week seven for
Part 8, Thursday for Part 9; `open_case(..., clock=)` already takes one, `bootstrap.py:82`) so
History reads as the story does.

### Stages (one commit each on `claude/optimistic-hypatia-eutcgx`, gate green after each; push at the end)

1. **Welcome + How this works.** Panel, screen, settings key, Help/Commands entries,
   first-start copy. Tests (`tests/test_welcome.py`): panel on an empty case's first question at 120×40 and 80×24
   (collapses to one line when short), editor keeps focus, typing/Send work immediately,
   gone after the first Send, *Hide this* persists and survives restart, *How this works*
   returns with draft and caret intact (as S116), never shown in tour/story; S114/S117
   acceptance still green.
2. **Story builder generalisation + the Harrowfield goal.** Tests (pure, like
   `tests/test_story.py`): package matches its YAML; the Second Renaissance fresh-build
   comparison still passes; tree counts per tree; the Cloud draws as five boxes; the core problem leads to
   all 10 undesirable effects; exactly two proposals wait (Graham's, Joy's); the live
   question is `guided:test_change`; every statement attributed to a named speaker.
3. **Tour engine.** Pure tests in `tests/test_tour.py`: script validation (every part has opening, beats and closing; every
   guided step reached has an example answer; every `until` names a known event; page length
   fits 80×24 when wrapped; banned on screen: card(s)/deck/stack and the acronyms CSF, NC,
   UDE, CRT, FRT, PRT, TT, INJ, NB, IO, TOC, LTP); `Tour` transitions; `prepare` reaches each
   part's precondition from a fresh copy and is idempotent; progress file round-trip.
4. **Tour UI + removal of the old tour.** Pilot tests (style of `tests/test_onboarding.py`):
   walk the whole tour with Example answer/Accept all/a/r and assert page and strip text,
   that the review shows the original forecast beside the result, the Tests view after
   Part 9, Leave → start screen with "Continue the tour · Part N of 9", Contents jump to
   Part 8, Ctrl+Q leaves rather than quits, no consultant switching, `run_home` dispatch of
   the three outcomes, strip and pages readable at 80×24. Update `tests/test_onboarding.py`
   (option ids, delete coaching tests), `tests/test_home.py` (START rows), `tests/test_tui.py`.
   Prove new tests fail by breaking a scratch copy (testing-strategy.md).
5. **Docs, design records, pictures.** README (first start, tour), `docs/tui.md` (first start,
   tour, welcome), `docs/tutorial.md` ("Prefer to learn inside the app?"), Help text
   (`tui.py` ~235), TUI-DESIGN.md (a *First use* bullet: welcome panel, story pages, tour
   strip grammar), TUI-UX-PLAN.md (dated note: on 8 October David reversed part of Step 3 —
   a non-blocking first-screen welcome and a story tour; still no steps before the first
   answer, symptom 13), this plan committed as `docs/plans/2026-10-08-story-tour-and-welcome.md`
   (the convention of `docs/plans/2026-10-08-haiku-default-boost-usage.md`) and linked from a
   dated `docs/p0-delivery.md` section ("Outside the specification's scenarios, following the
   plan: no feature file changed, nor the application layer or `CaseCapabilities`"),
   CONTRIBUTING (rebuild a story by name). `scripts/render_screenshots.py`: replace `tour`
   with tour-start, a story page, a closing page, the workspace with the strip, Day three's
   review, and add `welcome` and `how-this-works`; regenerate `docs/images/`.

## Verification

- Install once with `python3 -m pip install -e '.[test,mcp]'` (or prefix with
  `PYTHONPATH=src:.`). `python3 scripts/check_p0.py` after each stage (bundle check incl. the
  banned "card" word, pytest, behave p0/p1/p2 delivered scenarios incl. S114/S117,
  conversation features); while iterating, `python3 -m pytest tests/test_tour.py
  tests/test_welcome.py tests/test_story.py tests/test_onboarding.py tests/test_home.py
  tests/test_tui.py`.
- `python3 scripts/build_story.py harrowfield` builds the new archive. Do **not** rebuild
  `second-renaissance.reasoncase`: `tests/test_story.py` already builds it fresh and compares it
  with the packaged one, which proves the builder changes are opt-in (a rebuild would likely
  also leave its seven withdrawals waiting under the later S148 rule — unverified, and out of
  scope here).
- Run it for real (the `run` skill / a tmux session): first start → *Take the tour* → every
  part with Example answers at 120×40, then again at 80×24, in a light and a dark theme; check
  nothing moves focus on its own, Leave/Continue resumes at the right part, Contents → Part 8
  works from a fresh start, the Day-three review shows forecast vs result, the epilogue's
  *Start my own goal* opens the name dialog and the new goal shows the welcome panel; *Hide
  this* and restart; F1 → How this works.
- Look at every regenerated screenshot; read all tour copy aloud once for jargon and length.

## Risks and follow-ups

- **Content is the bulk of the work**: about 120 statements across the six trees (Goal ~17,
  Current Reality ~25, Cloud 5, Future Reality ~25, Prerequisite ~21, Transition ~31) in ~25
  chapters, plus ~40 pages and beats. Fallback if
  per-speaker chapters prove too heavy: author the trees as one `harrowfield.ltp.yaml`
  imported by a single chapter (attribution to Ruth only), keep the two pending chapters
  per-speaker. David reviews the copy before the screenshots are final.
- **Maintenance** (the cost TUI-UX-PLAN cited against onboarding): an engine plus a long
  script to keep in step with the UI. The validator ties the script to the code — every view
  and tree a beat names must exist (`VIEW_LABELS`, `TREE_TITLES`), each tree part's question
  is its page's question verbatim (`TREE_TITLES`), every guided step reached has an example answer — so
  a rename fails a test instead of silently breaking the tour.
- **80×24 budget**: the strip is capped at four rows (status, two narration lines, buttons);
  beats' narration has a length limit enforced by the script validator. Opening a past step
  from History shows the existing moment strip (`tui.py:1433`); meanwhile the tour strip folds
  to its status line so two bands never stack.
- **Not in scope**: a text-presentation (accessible) tour; renaming opaque Views (Reasoning,
  Case context) — *How this works* explains them instead; using the tour for S73 evidence
  (it is optional, so first-hour testing still runs without it).
