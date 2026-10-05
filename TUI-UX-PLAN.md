# TUI UX plan: one constraint, four small PRs

Status: Steps 1–4 and the automated part of Step 6 are implemented, one commit
each, plus regenerated screenshots. Step 5 is deliberately deferred until
participants show the need, and the S73 participant check has not been run.
Scope: adapters, docs and screenshots only. No domain, application or
specification change was needed; every element below uses fields the `workspace`
projection already returns.

Where the build differs from the text below: the first question is labelled
"Clarify the goal" rather than repeating the goal's name, which the header
already shows; and `tui.py` grew by the comparison renderer, so the net deletion
is on screen and in the docs, not in lines of code.

## Navigation and hierarchy revision

An outside evaluator reviewed three screens (the goal question, Your words, and the home
list) and a revised mock-up answered each finding. Where it differs from the rows of Step 2
below (header, destinations, buttons, answer box) and the home list, this revision wins;
[TUI-DESIGN.md](TUI-DESIGN.md#hierarchy-names-and-focus) holds the rules that remain.

| Finding | Change |
| --- | --- |
| Five navigation systems compete: stepper, views list, buttons, footer keys and palette | The loop line is the spine. The views list is secondary (**VIEWS**, ▸ on the open view). The **Actions** and **Help** buttons are gone; **Commands** and **Help** are in the footer, and Tab reaches them |
| "Actions" meant a view, a button and a palette | The view is **Loop actions**, the palette is **Commands**, and the button is gone |
| The question sat far above the answer box | The box follows the page: right under a short question; under a long page the page scrolls above it, so the box stays on screen |
| Inverted hierarchy: a quiet heading over a bold question | Heading in the accent colour and bold, the question plain, an optional-answer hint quiet |
| The view's name appeared in the header, the list and the heading | The header is the goal's name on the left, and who you are and whether it is saved on the right |
| "No goal yet" under a goal that has a name | "Measure: not set" on the loop line (the measure itself once there is one); the goal band appears once a goal is recorded |
| Focus was hard to see and named in a "Focus:" label | A heavy accent frame round the focused pane; the label is gone. The footer says what the keys do there |
| A jargon hint on the answer box's bottom border | "Enter: new line · Send: get the guide's reply", beside the buttons (under them when there is no room), and an example fading in the empty box |
| Your words showed an internal id, a login name and an ISO timestamp | "Oct 3, 18:02" on the person's own clock; a name only when more than one person has written; no id |
| The home list mixed ways to start, settings and goals, with ragged columns | **Start**, then **Your goals** as aligned columns (name, stage, day); settings behind F2, and the footer says what they are now |

Not built: **rename** and **delete** for a goal, which the evaluator's mock-up lists in the
home footer. Neither exists in the application: a goal's name is stored in every saved step, so
renaming it is a new use case, and deleting one is a new, destructive one. The recipe for
[an interface action](docs/development/recipes.md#add-an-interface-action-for-example-a-tui-key)
says to map it to an existing capability or add the use case first, with its scenario, so the
footer lists only what works.

Where it meets the specification: S114 asks that the focused control stay visible, which the
frame does, but S68 (not yet delivered) says the pinned header shows "focus", which this design
puts in the frame instead; S07 and S119 call the list of every action **Actions**, which is now
**Commands** on screen, and their steps map one to the other. Neither scenario's text was changed.

## The short version

The specification already describes the quiet tool the design-retreat answer
asks for. Frames M01–M05 in
[example-mvp-session.txt](reason-commons-spec/example-mvp-session.txt) show a
one-line header, a short goal/safeguard band, one decision, the context that
changes the answer, and an aligned forecast/result table at review. The
implementation has drifted from those frames in a few places, all in
[tui.py](src/reason_commons/adapters/tui.py). This plan brings the code back to
its own contract.

The binding constraint is the participant's attention at the moment of
decision. It is worst at **Review**. That step turns work into learning, yet the
screen asks "How does what happened compare?" without showing what happened.
Every other surface (CLI `show`, MCP, the skill) already renders that
comparison through [rendering.py](src/reason_commons/adapters/rendering.py#L158).
Only the TUI does not.

## What the running code shows

These were checked by running the app headlessly against the sample case, not
taken from the screenshots alone.

| # | Symptom | Cause in code | Contract it misses |
|---|---|---|---|
| 1 | Review asks for a comparison, but the result is not on the review screen. At 80×24 the reading pane shows 8 of 34 rows, and the observation is the last record. | `render_next` prints every context record as prose ([L401](src/reason_commons/adapters/tui.py#L401)). The comparison appears only in the Tests view ([L471](src/reason_commons/adapters/tui.py#L471)). | S121 |
| 2 | The forecast question asks "what will happen if you make this change?", but the change appears nowhere on screen. | The guided consultant records the test only after the stop-condition question, so `_context` at `test_forecast` holds only the goal ([guided.py L228](src/reason_commons/adapters/guided.py#L228)). | S04 |
| 3 | The pinned band is clipped silently. At 120 columns the test's forecast, the part that matters when observing and reviewing, is never visible, and nothing marks the cut. | `pinned_text` joins three long statements; `#pinned` has `max-height: 3` ([L220](src/reason_commons/adapters/tui.py#L220), [L353](src/reason_commons/adapters/tui.py#L353)). | v1 gate: "clipped premise … blocks release" |
| 4 | Goal and safeguards appear twice on most screens. | Pinned band plus "What this step builds on". | S68 |
| 5 | The current step is named three times: status bar, loop line and heading. | [L329](src/reason_commons/adapters/tui.py#L329), [L333](src/reason_commons/adapters/tui.py#L333), [L378](src/reason_commons/adapters/tui.py#L378) | S03 |
| 6 | The most striking elements are furniture: a reverse-blue status bar, a decision heading drawn as blue underlined text (it looks like a link but isn't one), and an answer box with an orange border whether or not it has focus. | `#status` uses the `$primary` background; Textual's default `MarkdownH2` style; `#response` always has an `$accent` border ([L219](src/reason_commons/adapters/tui.py#L219), [L232](src/reason_commons/adapters/tui.py#L232)). | S03; TUI-DESIGN "exactly one control owns focus; name it and mark it" |
| 7 | The focused control is never named. | The status line has no focus field. | S114 |
| 8 | When a reply arrives, the app pulls you out of the view you were browsing. Reproduced by opening History while the guide is working; on completion the view becomes Next. | `_submitted` sets `view_name = "next"` whenever text was sent ([L663](src/reason_commons/adapters/tui.py#L663)). | S118; v1 gate: "focus theft … blocks release" |
| 9 | Four routes to the same eight views are visible at once: the side list, the Views button, the Actions palette and Ctrl+T. Ctrl+N "Next tree" is advertised on every screen. | `compose`, `BINDINGS` | Not required. S117 needs Views only when the list is hidden. |
| 10 | Furniture takes 14 of 24 rows at 80×24, leaving an 8-row reading area; at 120×40 it takes 17 of 40. | Fixed editor height (6, or 3 on short terminals), three borders, a label row, the controls margin | S117 |
| 11 | Internal vocabulary shows through, e.g. "(participant_report)". | `record_lines` ([L426](src/reason_commons/adapters/tui.py#L426)) | TUI-DESIGN, "Names" |
| 12 | In the Tests view table, the measure column wraps one word per line. | Markdown table auto-widths ([L477](src/reason_commons/adapters/tui.py#L477)) | S121 readability |
| 13 | A first run passes a 4-way chooser, up to 3 setup dialogs, a goal-name dialog and a welcome diagram before the first answer. The name dialog is followed at once by "What do you want to achieve?" | [onboarding.py](src/reason_commons/adapters/onboarding.py), `NewGoalScreen` ([L846](src/reason_commons/adapters/tui.py#L846)), `WELCOME_WIDE` ([L44](src/reason_commons/adapters/tui.py#L44)) | S114 ("no tour … required") |

## Theory of Constraints reading

**Goal and throughput.** Reason Commons exists so that people finish loops and
learn from them. Throughput is the number of loops that end in a review
comparing an unchanged forecast with a reported result. The spec's release
blockers act as necessary conditions: no lost draft, no accidental consultant
call, no focus theft, no clipped premise, no concealed breach. A change that
raises throughput but violates one of these is not an improvement.

**The constraint.** Screen space is not the constraint; most screens have empty
rows. Data is not the constraint either; the projection already returns
everything needed. The constraint is the participant's attention and working
memory at the decision point. It is a *policy* constraint, built into two habits
of the code:

1. Under every question, show every context record, the same way.
2. Show every route, everywhere, all the time.

Review is the drum. It is the only step that converts work into learning, and
it is the step the screen supports least.

**The conflict underneath.** This is the conflict that set Krug against
*Making Thinking Visible* in the retreat answer, drawn as an Evaporating Cloud:

```text
                              ┌─ B  Keep the next move effortless ── D   Show less
A  People make a good next ───┤
   reasoning move             └─ C  Keep reasoning inspectable ──── D'  Show more context
```

The conflict between D and D′ rests on one assumption: everything in view gets
equal weight, all the time. The injection is to weight content by its relevance
to the current decision, decided only from facts already recorded:

- a test with observations puts its comparison first;
- a goal with a measure puts that measure beside the forecast question;
- nothing already pinned is repeated;
- everything else stays one keystroke away in stable destinations.

That is the retreat's "progressive visibility", tied to data rather than
judgement.

**The maintainers' constraint.** Every visible element is mirrored in `HELP`
(in `tui.py`), [docs/tui.md](docs/tui.md), [docs/tutorial.md](docs/tutorial.md)
and the README screenshots. Each duplicate element removed is one less thing to
keep in sync. Every step below removes at least as much as it adds.

## The plan, as the five focusing steps

### Step 1: Exploit. Put what the decision asks about on screen (PR 1, size M)

**1a. The comparison goes on the review screen.**

- When the Next view's context includes a test that has observations, draw the
  forecast/result block first.
- Match rows with the rule `rendering.py` already uses: an observation's
  `measure` equals a forecast's `measure`. Show unmatched observations as
  "Additional result".
- Add one row per goal safeguard. Its result reads "no separate result
  recorded" unless an observation's measure names that safeguard.
- Show the stop condition and review date below the block.
- Use one helper for both Next and the Tests view; it replaces the Markdown
  table. Draw it as a Rich `Table` into the existing `#canvas` Static, the same
  pattern the trees use. Put forecast and result side by side at 100 columns or
  wider; stack them below that.
- Print no ✓, ✗ or BREACH marks. Results are free text, so the TUI has no basis
  for a verdict (ARCHITECTURE: "Projection, not authority"; S122). Verdict words
  appear only when someone records them; see Step 5.
- Optional: drop the forecast quote from the guided review prompt
  ([guided.py L249](src/reason_commons/adapters/guided.py#L249)), since every
  renderer now shows the forecast.

**1b. The change goes beside the forecast question.** When `GuidedConsultant`
proposes `test_forecast`, `test_review` or `test_stop`, it quotes the change the
person just wrote. The review prompt already does the same for the forecast.
This is an adapter-only change; no record shape changes.

**1c. Compact, de-duplicated context.**

- Keep showing all of the intervention's `required_context_refs`. The
  consultant chose that context, so the TUI must not filter it.
- Leave out goal text and safeguards that are already in the band.
- Draw the remaining records as aligned `Label  value` lines instead of
  paragraphs.
- Use plain words: "reported by Mira" rather than `participant_report`, and
  "not known yet" rather than `unknown`.

**1d. The band never clips silently.**

- At most two labelled lines: **Goal** and **Protect**. The test leaves the
  band; it now appears where it matters (1a, 1b).
- Truncation always ends in "…", and the Goal view always holds the full text.
- When the body is showing the safeguards (review), the band shows Goal only.
- An empty case shows one muted line: "No goal yet".

The mockups below use the sample case's real records and nothing else.

#### Forecast step at 80×24

```text
From open evening to first practice · Mira · Saved · Next step     Focus: Answer
Goal    Newcomers at our open evenings find a clear, no-pressure next step into…
Protect Nobody feels recruited or pressured · Organisers' hours stay as they are
✓ Goal  ● Test + forecast  ○ Action  ○ Observe  ○ Review

CHOOSE A TEST
Your change: "End each open evening with one clear invitation: the date of a
first practice, what it asks of you, and that no is a fine answer."
What do you predict will happen? Be concrete, with a number if you can.

Measure Newcomers at a first practice within 3 weeks (sign-up sheet): now 2 of
        30, aiming for 8 of 30 by 30 November.





╭ Answer as Mira ──────────────────────────────────────────────────────────────╮
│ ▏                                                                            │
│                                                                              │
│                                                                              │
│ [Send]  Explain this  Other moves  Views  Actions                            │
╰───────────────────────────── Enter adds a line · Send asks the offline guide ╯
 ^s Send  ^t Trees  F1 Help  ^q Save & quit                           ^p Actions
```

#### Review step at 80×24 (the same data as `tutorial-review.png`)

```text
From open evening to first practice · Mira · Saved · Next step     Focus: Answer
Goal    Newcomers at our open evenings find a clear, no-pressure next step into…
✓ Goal  ✓ Test + forecast  ✓ Action  ✓ Observe  ● Review
REVIEW AGAINST THE FORECAST
How does what happened compare? Check your safeguards first. Then decide:
keep, adjust or drop the change?
Measure: Newcomers at a first practice within 3 weeks (sign-up sheet): now 2
of 30, aiming for 8 of 30 by 30 November.
ORIGINAL FORECAST · saved before any result
6 of 30 newcomers come to a first practice within 3 weeks
REPORTED RESULT · Mira
9 of 31 newcomers came to a first practice within 3 weeks (sign-up sheet).
Nobody said they felt pushed; two said the card helped them decide. Organiser
hours were the same.
SAFEGUARDS · no separate result recorded: check each against the report
· Nobody feels recruited or pressured   · Organisers' hours stay as they are
STOP CONDITION  Stop if anyone tells us they felt pushed.
╭ Answer as Mira ──────────────────────────────────────────────────────────────╮
│ ▏                                                                            │
│                                                                              │
│                                                                              │
│ [Send]  Explain this  Other moves  Views  Actions                            │
╰───────────────────────────── Enter adds a line · Send asks the offline guide ╯
 ^s Send  ^t Trees  F1 Help  ^q Save & quit                           ^p Actions
```

#### Review step at 120×40 (the side list is visible, so there is no Views button)

```text
From open evening to first practice · Mira · Saved · Next step                                             Focus: Answer
Goal    Newcomers at our open evenings find a clear, no-pressure next step into a first practice session, so interest
        turns into sustained practice.
✓ Goal  ✓ Test + forecast  ✓ Action  ✓ Observe  ● Review

 ▌Next step      REVIEW AGAINST THE FORECAST
  Goal           How does what happened compare? Check your safeguards first. Then decide: keep, adjust or drop
  Trees          the change?
  Tests
  Actions        Measure: Newcomers at a first practice within 3 weeks (sign-up sheet): now 2 of 30, aiming for 8 of
  Reasoning      30 by 30 November.
  Your words     ORIGINAL FORECAST · saved before any result   REPORTED RESULT · Mira
  History        6 of 30 newcomers come to a first practice    9 of 31 newcomers came to a first practice within 3
                 within 3 weeks                                weeks (sign-up sheet). Nobody said they felt pushed; two
                                                               said the card helped them decide. Organiser hours were
                                                               the same.

                 SAFEGUARDS
                 Nobody feels recruited or pressured           no separate result recorded
                 Organisers' hours stay as they are            no separate result recorded

                 Stop condition  Stop if anyone tells us they felt pushed.
                 Review date     Sunday, 9 November









╭ Answer as Mira ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ▏                                                                                                                    │
│                                                                                                                      │
│                                                                                                                      │
│                                                                                                                      │
│ [Send]  Explain this  Other moves  Actions                                                                           │
╰───────────────────────────────────────────────────────────────────── Enter adds a line · Send asks the offline guide ╯
 ^s Send  ^t Trees  F1 Help  ^q Save & quit                                                                   ^p Actions
```

PR 1 already helps at 120×40 on its own. At 80×24, the review fits on the first
screen only once PR 2 frees the rows.

### Step 2: Subordinate everything else to the question (PR 2, size S–M; mostly CSS and `compose`, net deletion)

| Change | Detail | Contract |
|---|---|---|
| Header | One quiet line with no reverse video: case · speaker · save state · view, with **Focus: \<control\>** on the right. The consultant name moves to where its consequence is, the Send subtitle ("Send asks Claude"). While the consultant works, "Asking Claude…" replaces "Saved". | S114 |
| Loop line | ✓ done, ● current, ○ to come. The reverse block and arrows go. | S03 |
| Decision label | Small and muted, with no underline and no link colour (override `#content MarkdownH2`). The prompt becomes the only bold, high-contrast text. | S03 |
| Destinations | Keep the list at 100 columns and wider, without a border, 14 columns, muted, with the current view marked ▌. Hide the **Views** button while the list is visible; show it when the list is hidden. | S114, S117, TUI-DESIGN 12–16 cols |
| Buttons | Only Send is filled; the rest look like text. Names stay unchanged. | S12, S13, S119 |
| Answer box | Accent border only under `:focus-within`. "Answer as Mira" moves into the border title and the instruction into the subtitle, saving a row. The editor uses `height: auto` and grows from 3 to 10 rows (checked on Textual 8.2.8). | Spec: "one control owns focus" |
| Footer | Ctrl+N appears only in Trees, via `check_action`. | — |
| Reading pane | The border goes. The "Browsing is local and never asks the consultant" line leaves every view body; it stays in the Views menu title and on each Other moves item, where the choice is made. | S12 |
| Completion | A reply never changes the view. Show **Answer ready** in the header; returning to Next shows the new question. | S118 (release blocker) |
| Names | "Everything" becomes **Reasoning**, the spec's destination name; the view id is already `reasoning`. | tui-reasoning-design.md |

Row budget:

| Region | 80×24 now | 80×24 after | 120×40 now | 120×40 after |
|---|---:|---:|---:|---:|
| Header | 1 | 1 | 1 | 1 |
| Goal/safeguard band | 3 (clipped) | 1–2 | 3 (clipped) | 2–3 |
| Loop line | 1 | 1 | 1 | 1 |
| Reading area | 8 | 13–14 | 21 | 27–28 |
| Answer box | 8 | 6, grows when typing | 11 | 7, grows when typing |
| Footer | 1 | 1 | 1 | 1 |

### Step 3: Remove onboarding steps instead of adding teaching (PR 3, size S)

- **First run.** The highlighted default becomes "Start my first goal": the
  offline guide, the login name, then straight to naming the goal. This is
  today's "Skip setup" behaviour promoted. "Choose who asks the questions
  (Claude or a local model)" is the second option. The tour and the example stay
  as they are. The name is visible in the header and in "Answer as …", so a
  wrong default is easy to spot and change in Settings.
- **No repeated question.** The name dialog asks "Name this goal (a few
  words)". The first workspace question uses that name as its heading and asks
  "What would count as better? Describe it in your own words." The TUI draws
  this empty-case text itself ([L381](src/reason_commons/adapters/tui.py#L381)),
  so no consultant change is needed.
- **The diagram moves out of the work surface.** The three-box loop diagram
  moves into Explain this for the first question and into Help, as frame M01's
  "[How this works]" does. The welcome body becomes the question plus one line:
  "Your words are kept as written. Unknowns can stay open. Nothing is sent until
  you press Send." The loop line already shows the five steps.

### Step 4: Trees. Swap emphasis, don't redesign (PR 4, size XS)

- In `tree_lines`
  ([trees.py L116](src/reason_commons/adapters/trees.py#L116)), role labels
  drop bold and take a muted colour, so each statement becomes the brightest
  text. The text itself is unchanged, so `reason-commons trees`, `show`, and
  the S128 step assertion (`└─ because ─ ROOT CAUSE`) are unaffected. The
  labels still carry the meaning; colour only reinforces it, so monochrome
  terminals lose nothing.
- The Trees view header becomes one line: the tree's name and its question,
  plus the existing picker line. The inline key-help sentence goes, because the
  footer now shows Ctrl+N in context.

### Step 5: Elevate, only if Step 6 shows the need (size M each)

- **Results per measure and per safeguard.** The guided observe step would ask
  one short question per forecast measure and per safeguard, and record one
  observation for each with that `measure`. The schema already allows this, so
  only the adapter changes. The review table would then line up each safeguard
  with the person's own words. It costs extra questions per loop, so do it only
  if participants skip safeguards at review.
- **Interactive tree outline.** Textual's `Tree` widget gives Space to expand
  and Enter to open an inspector with the claim's wording, role, basis,
  assumption, earlier wording and linked tests: the spec's Master-Detail and
  Expand-to-Focus. It needs `tree_lines`' topology turned into a small node
  structure shared by the text renderer and the widget. Do it only if people get
  lost in large trees.

### Step 6: Verify, then find the next constraint

- **Adapter tests** (pilot at 120×40 and 80×24), for example:
  - review shows the forecast and the result inside the visible region;
  - the goal statement appears once per screen;
  - every "…" has a destination that shows the full text;
  - a reply arriving while History is open leaves the view and focus alone;
  - Ctrl+N is hidden outside Trees.
- **Screenshots.** Add 80×24 forecast and review shots to
  [render_screenshots.py](scripts/render_screenshots.py). Every docs screenshot
  today is 120×36, so the tightest size the spec names is never looked at.
- **Housekeeping.** Run `python3 scripts/check_p0.py`. Update `HELP`, the
  screen, keys and views tables in [docs/tui.md](docs/tui.md), and the README
  alt text. Regenerate the screenshots.
- **People.** Run the S73 first-hour protocol: five people, fake consultant, at
  120×40 and 80×24. Watch the review step: do they compare the result with the
  forecast and check each safeguard without prompting? If yes, the constraint
  has moved. The next candidates are consultant question quality (p2 semantic)
  or reading large trees. Choose Step 5 work from that evidence, not before.

## What I would deliberately not do, from the retreat answer

| Suggestion | Why not | Instead |
|---|---|---|
| Remove the destination list from the work surface; add an "Inspect…" menu | S114 and TUI-DESIGN require visible destinations at 120×40, and "Inspect…" would add a fifth way to navigate | Make the list quieter; show the Views button only when the list is hidden |
| Rename Explain this, Other moves and Views ("Why this?", "Inspect…") | S12, S13, S55, S116, S117 and S119 and the spec frames name these controls; renaming churns them with no evidence of confusion | Keep the names; test the vocabulary in S73 |
| ✓ and ! verdicts in the review table | Results are free text, so the TUI would be inventing judgements (Projection, not authority; S122) | Align both sides; show verdict words only when someone records them |
| A relation-focus tree view with IF ALL, objections and support counts | Joint premises, objections and positions are p3/p4 data; the v1 schema does not record them | Swap emphasis now; build the interactive outline only if needed |
| Progressive onboarding that introduces concepts as they arise | A new mechanism to maintain | Remove steps; put the diagram behind Explain this |
| Any domain or application change | Not needed | — |

## Cost to maintainers

- **Changed:** `adapters/tui.py` (most of it), `adapters/trees.py` (one style
  expression), `adapters/guided.py` (prompt wording), the first-run options in
  `GoalsApp`, `tests/test_tui.py`, `scripts/render_screenshots.py`,
  `docs/tui.md`, `docs/tutorial.md`, and the README alt text.
- **Unchanged:** `domain/`, `application/`, `bootstrap.py`, the feature files,
  the acceptance step definitions, and the CLI and MCP renderers.
- **Removed from the screen and the docs:**
  - the step name in the status bar;
  - the test in the band;
  - the duplicate Views button at wide sizes;
  - the per-view "Browsing is local" line;
  - the Markdown comparison table;
  - the welcome diagram on the work surface;
  - the "What this step builds on" heading.
- **Spec gaps closed:** S03, S04, S68, S114 (focus named), S118 (no view jump),
  S121 (comparison inside the workspace), and the v1 "clipped premise" gate.

Each PR ships on its own and regenerates the screenshots. Order: PR 1 → PR 2 →
PR 3 → PR 4.
