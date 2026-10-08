# Workspace reference

Facts to look up while you work. To learn the workspace step by step, follow the
[tutorial](tutorial.md); to install it, see the [README](../README.md#quick-start).

## The screen

| Part | What it shows |
| --- | --- |
| Top line | The goal's name on the left; on the right, your name and whether everything is saved (or *Asking …* while the consultant works, *Asking Claude (Sonnet 5.5)…* for a reply with deeper reasoning, *Answer ready* when its reply waits on **Next step**, *Read-only* while you look back) |
| Pinned lines | Your goal and safeguards, and the open **Action**, once a goal is in your model; a goal still waiting in **Backlog** shows as *proposed, not yet accepted*, and one with no measure yet as *provisional*. A long goal ends in … and **Goal** shows all of it. At review the safeguards move down, next to the result. A **Breach** (a reported result outside a bound recorded with its forecast) stays pinned here in every view. Commands, **Display: Expanded** repeats the goal's measure, baseline, horizon and scope, each safeguard and each test's boundaries here; **Display: Compact** (the default) turns it back. The choice is saved with your draft and changes nothing else |
| Loop line | The spine of the screen: Goal ─ Test + forecast ─ Action ─ Observe ─ Review, with ✓ finished, ● current and ○ still to come. On its right, the goal's **Measure**, or *not set* while there is none. On a narrow terminal the line drops its joins, and below about 56 columns shows only where you are ("● Review · step 5 of 5") |
| Views list | **VIEWS**, with ▸ beside the open one; **Backlog** says how many entries wait ("Backlog · 3"). While **Trees** is open and has statements, **All six** and the six trees are listed under it, with ▸ beside the one on screen. On terminals 100 columns or wider; narrower, the **Views** button takes its place |
| The page | A heading, then the question in plain type, then, for a question you may skip, a quiet hint ("Leave empty if you don't know yet."). Below it, what the last reply proposes, marked *proposed* (see [deciding what enters your model](#deciding-what-enters-your-model)), then what the question builds on (at review: the original forecast beside the result) |
| Answer box | Right under the page, so you answer next to the question. All typing is literal, including `?`, `q` and numbers. Its tag says who you answer as, with the built-in guide an example of the answer shows faintly while it is empty, and the line beside the buttons says what **Send** will bring back (with Claude, from which model: "Send: get Claude's reply (Haiku 5.5)"). It grows as you write, and when the page is long the page scrolls above it, so the box never leaves the screen. On any view other than **Next step** its tag also names the question it answers ("Answer as Mira · Choose a test"), and while it is empty it folds to one line so the view has the room; Tab or a click opens it, and a draft keeps it open |
| Footer | The keys that work where the keyboard is, then **Commands**, then **Help** on the right. On a narrow terminal the hints say less, then the last ones go; **Commands** and **Help** always stay. With Claude, the space before **Help** estimates what this session and this month cost ("Haiku 5.5 · session ≈ $0.02 · month ≈ $1.40 of $5", or "…, over $5" past a budget); it says less as room runs out and is the first thing to go. With LM Studio it says *no charge*; with the built-in guide it says nothing until something was spent this month |

You can always see where the keyboard is: a heavy frame in the accent colour round the answer
box or the Views list, a bar down the left edge of the page or the trees, or a highlighted
button or footer control. There is no label for it; the footer says what the keys do there.
In the trees, the chosen statement lies on a band of the same colour's tint: that marks
what is chosen, not where the keyboard is. Tab goes from the Views list to the open
page's own list (Backlog, History or Trees) if it has one, and back to the answer otherwise.

On a small terminal (80×24) the views list gives way to the **Views** button, and
the forecast and the result stack one above the other:

![The review question at 80 by 24: the original forecast, 6 of 30 newcomers, directly above the reported result, 9 of 31, under a one-line goal that ends in an ellipsis](images/review-80x24.png)

## Keys and controls

| Key or control | What it does |
| --- | --- |
| Enter | New line in your answer |
| Ctrl+S, or Tab to **Send** then Enter | Send your answer |
| Tab / Shift+Tab | Move between controls: the answer box and its buttons, then **Commands**, **Help** and the Views list |
| Esc | Leave the answer box to browse, your text kept; anywhere else, go back to where you were before you started looking around (view, scroll, draft and caret) |
| Ctrl+T | Open the trees, with the keys on the drawing; press again to go back to the question and your draft |
| ← / → | Step back or forward through saved steps, when the answer box is not in use |
| Ctrl+N | In the Trees view: the next tree, one at a time, then all six again |
| ↑ / ↓ | In the Trees view: choose a statement |
| Space | In the Trees view: fold the chosen statement's branches away, or unfold them |
| Enter | In the Trees view: the chosen statement's details in full, and Esc returns; in **All six**, the chosen statement's own tree |
| a | In the Trees view, or its details: begin an answer about the chosen statement (its words go into your answer; nothing is sent) |
| **Accept all** | Beside **Send** while the last reply's proposals wait: admits them all to your model, with anything they need (you see that list first) |
| Enter, a, r, h | In **Backlog**: the choices for the chosen entry; accept it; reject it; say a flagged record still holds |
| u | In **History**: undo what the chosen step accepted; what leaves with it is shown first, and an undo is final |
| **Explain this** | Why the current question matters (saved, no consultant call) |
| **Other moves** | Local explanations and evidence, or ask the consultant for advice or a different question; each item says which. Type to filter; **Back** or Esc leaves without choosing |
| **Views** | Switch view, when the list on the left does not fit |
| Ctrl+P, or **Commands** in the footer | Every command, one to a line: send with deeper reasoning (with Claude), accept all the last reply proposed, accept proposals automatically (or hold them for review), ask about the open reviews, export, import or export trees, retry (and retry with Sonnet), consultant calls and cost, change consultant, views, trees, help, quit; each says whether it is local or asks the consultant |
| F1, or **Help** in the footer | Keys and controls |
| Ctrl+Q | Save your draft and quit (in the tour: leave it, for the start screen) |

On the goals list: arrows choose, Enter opens, F1 shows help, F2 opens Settings, Ctrl+Q quits.

## First start, settings and the tour

The first time, `reason-commons` offers four ways to start: take the tour (first,
until you have finished it), start a first goal straight away (the offline guide,
with your login name), choose who asks the questions first, or explore a real
commons. Choosing first asks for your name (recorded with your answers), the
consultant and, for Claude or LM Studio, checks the connection and lets you choose a
model. Esc goes back a step; leaving setup changes nothing. F2 **Settings** on the
home screen, then **You**, runs it again.

A new goal's first screen has a short note under the answer box: who asks, how to
answer and send, that each reply proposes and you decide, and where the loop line and
Views are. It gates nothing (the answer box keeps the keys) and goes once the first
answer is sent. **How this works** draws the workspace with each part numbered and says
what each is for; it is also in Commands. **Hide this** puts the note away on every
new goal. When the screen is short, the note folds to one line, then goes.

**The tour**, *A winter at Harrowfield*, is a story in nine parts. You are Ruth
Okonjo, the new Director of Patient Flow at a hospital that is always full and about to
spend £9.4 million on 24 more beds. Story pages tell what happened; then the workspace
opens on her goal, whose six trees hold the words of the people who work there, and a
strip under it narrates a few steps: open this tree, choose that statement, decide the
proposal waiting in Backlog. A step's button moves the view only when you press it, and
**Next ▶** (or F3) always goes on. Each part asks one of the six questions and ends with
a short koan from a monastery on a mountain pass. Parts 8 and 9 are a real loop with the
built-in guide: you choose a test, write its forecast before anything happens, and three
days later compare it with what happened. **Example answer** puts in Ruth's words.
**Contents** starts any part fresh, with Ruth's answers for everything before it;
**Leave tour** (Ctrl+Q) returns to the start screen, which then offers **Continue the
tour** at the part you reached. Nothing you write in the tour is kept.

## Screens

A picture of each part of the workspace, drawn from Mira's example goal, a goal in
progress or the real commons. `scripts/render_screenshots.py` regenerates them.

### First start

| | |
| --- | --- |
| ![The first screen: take the tour, start a first goal, choose who asks, or the real commons](images/first-start.png) | The ways to start, shown once |
| ![Choosing who asks the questions](images/setup-consultant.png) | Setup: who asks the questions |
| ![Choosing a Claude model](images/setup-model.png) | Setup: the models your key can use |
| ![The tour's first page: A winter at Harrowfield, a story in nine parts, with Begin, Contents and Not now](images/tour-start.png) | The tour's first page |
| ![A story page: Harrowfield General, where Alwyn Pryce waited 31 hours, and You are Ruth Okonjo](images/tour-story.png) | A story page |
| ![The workspace during the tour: the Goal Tree with a condition chosen, and the tour's strip beneath](images/tour-strip.png) | The workspace and the tour's strip |
| ![A part's closing page: the koan Ten Complaints, its key, and what comes next](images/tour-koan.png) | A part's closing koan |
| ![Day three: the review question with the original forecast, 8 in 10, beside the reported result, 4 of 11](images/tour-day-three.png) | Day three: the forecast beside what happened |
| ![A new goal's first screen with the note under the answer box](images/welcome.png) | A new goal's first screen, with its note |
| ![How this works: the workspace drawn with five numbered parts and what each is for](images/how-this-works.png) | How this works |

### The goals list

The list has two sections: **Start** (**New goal**, the tour, the real commons) and
**Your goals**, a table of each goal's name, the stage it has reached and the day it last
changed, with ▸ beside the highlighted row. The footer lists the keys and, on the right,
what is set now: your name, who asks the questions and the theme. Settings are behind F2.

![The goals list](images/home.png)

| | |
| --- | --- |
| ![The Settings dialog: theme, light or dark, You and Budget](images/home-settings.png) | F2 Settings: the voice and light or dark change as you press ← and →; **You** asks your name and consultant again; **Budget** sets a monthly budget for Claude's replies |
| ![Naming a new goal](images/new-goal.png) | Naming a new goal |
| ![Help on the goals list](images/home-help.png) | F1: how the loop works |

### The workspace

![The workspace on a narrow terminal, with the views behind Views](images/workspace-narrow.png)

On a narrow terminal the views list is hidden; **Views** opens it.

![The Views menu](images/views-menu.png)

![A draft answer in the answer box](images/answer-draft.png)

**Explain this** shows why the question matters, saved and without a consultant call.

![Explain this](images/explain-question.png)

**Other moves** offers local explanations and the question's evidence (the saved words and files it rests on), or asks the consultant for advice, a different question or help planning an observation. Each item says which ("local; opens saved explanation", "asks consultant"). Typing filters the list; with nothing matching, Enter does nothing and the menu offers **Clear filter** and **Back**. **Back** or Esc leaves with nothing sent.

A menu belongs to the question it was opened for. If a reply moves the goal on while a menu is open, choosing from it does nothing: the menu says the question changed and shows the current choices. An open menu is kept with your draft; when you come back, it reopens only for the same question, and a choice from a later version of Reason Commons is refused with a note.

![Other moves](images/other-moves.png)

If the consultant cannot be reached, your words are kept and **Retry** appears. With Claude, on a
terminal 100 columns or wider, **Retry with Sonnet** sits beside it: the same retry, answered once
by Claude Sonnet (see below). Narrower, it is in Commands, and the notice says so.

![The consultant could not be reached; Retry and Retry with Sonnet are offered](images/consultant-unavailable.png)

**Help** (in the footer, or F1) shows the keys and controls; **Explain this** is for the reasoning.

![Help](images/help.png)

### Views

| View | Screenshot |
| --- | --- |
| Backlog | ![Backlog: a proposed new goal marked decide first, a proposed cause and the link that waits for it, a Transition Tree action, and beside the list the chosen entry in full](images/backlog.png) |
| Goal | ![Goal view](images/view-goal.png) |
| Tests | ![Tests view](images/forecast-vs-result.png) |
| Loop actions | ![Loop actions view](images/view-actions.png) |
| Reasoning | ![Reasoning view](images/view-reasoning.png) |
| Your words | ![Your words view](images/view-sources.png) |
| History | ![History view: every saved step with who, when and what changed](images/view-history.png) |

### Looking back and the real commons

Enter on a History step opens that moment, read-only: the question it answered, the
words, what entered the model, what was proposed or decided, and what was asked next.
← and → step through.

![An earlier step of Mira's goal, read-only](images/history-moment.png)

**Explore a real commons** opens on the decision the Second Renaissance story waits
on and its one open action; each step back shows the editor's narration, the quoted
words, the source and what changed.

| | |
| --- | --- |
| ![The real commons now: the decision and the open action](images/story-now.png) | Now |
| ![Step 6 of the real commons](images/story-moment.png) | One step back |

### The trees

Before anything is recorded, the Trees view lists the six questions the trees answer
and the ways to start them.

![The Trees view with nothing recorded yet: the six trees and their questions, and how they grow](images/trees-empty.png)

The trees open first on **All six**, each tree folded at what it is for. Choose one
under **Trees** in the Views list, open the chosen statement's tree with Enter, or
step through them with Ctrl+N:

| Tree | Screenshot |
| --- | --- |
| All six | ![All six trees, each folded at what it is for, with how many statements lie below](images/tree-all-six.png) |
| Goal | ![Goal Tree](images/tree-goal.png) |
| Current Reality | ![Current Reality Tree](images/trees-current-reality.png) |
| Evaporating Cloud | ![Evaporating Cloud](images/tree-evaporating-cloud.png) |
| Future Reality | ![Future Reality Tree](images/tree-future-reality.png) |
| Prerequisite | ![Prerequisite Tree](images/tree-prerequisite.png) |
| Transition | ![Transition Tree](images/tutorial-trees.png) |

↑ and ↓ choose a statement, and the rest of the tree goes quiet around it; on a wide
terminal its details sit beside the trees, and Enter shows them full screen at any size.

| Size | Screenshot |
| --- | --- |
| 120 by 40 | ![A chosen cause in the Current Reality Tree on a tinted band; the symptom it causes and the cause beneath it keep their colours while the rest of the tree is drawn in a quiet tone, and the question worth asking of it, its links, the assumption behind them and where it came from sit in a panel beside the tree](images/trees-statement.png) |
| 80 by 24, after Enter | ![The same statement's details full screen at 80 by 24](images/trees-statement-80x24.png) |

After a reply that proposes a few statements, the next question shows them, marked
proposed, beside the words they came from, with **Accept all** beside **Send**:

![Under the next question, "Choose a test": proposed from your answer, not yet in your model, the Current Reality Tree's new symptom, newcomers do not come back after their first open evening, and the root cause beneath it, we never offer a next step, with the assumption behind the link, both marked NEW; then the answer they came from, and that Accept all admits them without making them true](images/trees-heard.png)

### Commands (Ctrl+P)

![The Commands palette](images/actions-palette.png)

Each command takes one line and says whether it stays local or asks the consultant. Ctrl+P and **Commands** in the footer
open the same menu as Other moves, with the same filter, **Clear filter** and **Back**.
Type to filter the list.

**Send with deeper reasoning (Sonnet 5.5)**, offered with Claude Haiku, sends your answer
to Claude Sonnet 5.5 for this one reply: it reasons more deeply and costs more (the command
says about how much, "≈ $0.05, about 12× a Haiku reply"). The status says *Asking Claude
(Sonnet 5.5)…*, the reply's notice says what it cost, and the next Send goes to Haiku again.
**Retry with Sonnet 5.5** does the same for a retry, and appears only when Retry would ask
the consultant again rather than apply a reply already received. Nothing switches model on
its own: you ask, one reply at a time.

**Consultant calls and cost** shows how often the consultant has been asked in this goal,
counted from the saved attempt receipts (imports, which ask no consultant, are counted
apart), and, with a usage log, what Claude's replies cost: this goal, the last reply's tokens
and cost, this session, today and this month by model against your budget, requests that
got no reply (they may still have been billed), the model in use and where it was chosen.
The amounts are estimates at Anthropic's list prices; your bill is in the Anthropic Console.
They come from the usage log kept outside every goal, never from the goal itself (see
[what it costs](providers.md#what-it-costs)).

![Consultant calls and cost: the calls in this goal; Claude's replies this goal, the last reply's tokens and cost, this session, today and this month by model against a $5 budget, the model in use, and where the estimates come from](images/usage-and-cost.png)

A reply's notice ends with what it cost ("Reply ≈ $0.0042 (Haiku 5.5)."), and the footer keeps the running total:

![After a reply from Claude Haiku: the footer's right end estimates this session, ≈ $0.0042, and this month, ≈ $0.31 of a $5 budget](images/footer-meter.png)

With a **monthly budget** (F2 Settings, **Budget**), you are told once when this month's
replies reach 80% of it and once when they reach it. Past it, each Send, and each Retry
that would ask again, first asks: **Send this one** or **Not now**. Nothing is blocked, and
**Not now** sends nothing and leaves your answer in the box. Local actions never ask.

![Filtering the Commands palette](images/actions-palette-search.png)

| Command | Screenshot |
| --- | --- |
| Export case | ![Export case](images/export-case.png) |
| Export trees | ![Export trees](images/export-trees.png) |
| Import trees | ![Import trees](images/import-trees.png) |

## Views

Browsing views never calls the consultant.

| View | Shows |
| --- | --- |
| Next step | The current question, what the last reply proposes, and what the question builds on |
| Backlog | Everything waiting for your decision, in the order it is best decided, and records flagged for review; the chosen entry in full beside the list on a wide terminal. Deciding here calls no consultant |
| Goal | The goal, its measure and each safeguard, in full |
| Trees | The six thinking-process trees, drawn from what is in your model: first all six, folded, then one at a time. The goal is the Goal Tree's top statement, and a statement another tree's link uses is drawn there too, marked with its own tree. Each statement says how it relates to the one above it, and where paths meet, how many of the tree's ends it leads to. Choose a statement for the question worth asking of it, its links, wording and origin; the rest of the tree goes quiet around it |
| Tests | Each test with its original forecast next to the reported result, a breach of a recorded bound marked where it happens, the action's status and the goal kept apart from the pilot, the review date (never a reminder), what is not recorded yet, and reviews |
| Loop actions | Each test and the action that carries it out, with its status |
| Reasoning | What is still open first, then the loop's records, then how many statements each tree holds |
| Your words | Your answers, exactly as written, each with when you wrote it on your own clock (and who, when more than one person has written) |
| History | Every saved step, oldest first, one row each: when, the question it answered or the decision taken, and what entered the model (and who, once more than one person has written); Enter opens that moment, **u** undoes what it accepted |
| Case context | Everything the current question rests on, in full: the revision it is saved at, the whole goal with each safeguard, each test's scope, period, stop condition and review date, what you are answering, and what waits (proposals, reviews, unanswered answers). Local; nothing is sent |

With the built-in guide, an empty answer skips an optional question (measure,
safeguards, review date, stop condition).

## Looking back

Every goal keeps each saved step. **History** lists them oldest first, one row each:
the day (written once, where it changes) and time, who answered or decided when more
than one person has, the question they answered or the decision they took ("Accepted
3 proposals", "Undid 2 changes"), and what entered the model (statements added,
reworded or withdrawn, links, tests). A reply whose proposals still wait says how many
it proposed; a step that changed nothing in the model is quiet. Tab to the list;
Enter opens that moment: the goal exactly as it was, the question, the words that
answered it, what entered the model, what was proposed, rejected or undone, and what
was asked next. **u** on a step undoes what it accepted that is still in your model:
the list of what leaves (with whatever cannot stand without it), the waiting proposals
that close and the records that will be flagged comes first, and nothing changes until
you confirm. An undo is final: it cannot be undone, and what leaves does not return to
the Backlog, though the consultant may propose it again. The Trees view then marks that step's statements NEW or REWORDED.
**← / →** (or **◀ Earlier**, **Later ▶**, shown in the footer while you look back)
step through; **Back to now** returns. The top line says *Read-only*; nothing can be
changed while looking back, and your unsent draft waits.

An **Action** line under the goal shows the open action (planned, its test not yet
observed) and its owner, except where the screen already shows that action.

**Explore a real commons** on the home screen opens the Second Renaissance's shared
reasoning this way, read-only. It leads with the decision the story is waiting on,
then the action's owner, what it carries out, what to expect and when to stop. Each
step back shows the editor's narration in italics above the quoted words; the words
are real and dated, the tree changes are an editor's reading, and approximate dates
are marked ≈. **Start my own goal** and **Back to start** leave it; nothing there is
kept.

## The trees

Ctrl+T opens the Trees view. The first time, it opens on **All six**: the six trees in
the method's order, Goal, Current Reality, Evaporating Cloud, Future Reality,
Prerequisite and Transition, each with its question and folded at what it is for
("▸ 9 below"). A short branch, or one the last reply added to, is shown whole. Space
unfolds a branch in place; Enter opens the chosen statement's tree. The Views list
names the overview and the six trees under **Trees**, so you can open any of them
there; Ctrl+N steps through them, then back to all six. The app remembers the tree
you last looked at.

A tree's page names it, asks its question and says which way to read it ("Read the
ladder from the bottom: what is lowest comes first."). Each statement opens its line,
led in by how it relates to the one above ("needs:", "because:", "overcomes:",
"made possible by:"), so a branch reads as a sentence. Its role follows as a quiet tag
in its colour ("· root cause", "· obstacle"), with "· hypothesis" or "· reported" where
that was recorded, and the assumption behind the link hangs under it after a dotted
rule (┆). When a statement's only branch with more below it is its last, that branch
continues down the same spine, marked ●, instead of stepping to the right: a
Prerequisite Tree reads as a ladder and a long chain of causes keeps its width. A
statement reached twice is drawn once and then referred to ("↑ … (shown above)"). A
Future Reality Tree shows its desired effects first and what could go wrong after.
Space folds any branch away and shows how many statements it holds.

Where paths meet, a statement says so on its own line, counted from the recorded
links: in the Current Reality Tree a cause that "leads to 5 of 6 undesirable effects",
in the Goal Tree a condition "needed for both critical success factors", and in the
Future Reality Tree each change we make, with what could go wrong beside what it is
for ("leads to all 7 desired effects and 1 of 2 undesirable effects"). It is a count
of links someone recorded, not a finding about the constraint. Under its question, a
tree's page says what it holds and what it does not say yet: "10 statements · 9 links
· 6 links state no assumption · 10 statements state no basis".

A test that carries out a statement hangs under it as a sealed prediction: the test,
then its *original forecast, saved before any result*, then the result, or *not
observed yet*.

A complete Evaporating Cloud (a shared objective, two needs, the action each need
seems to require, and the conflict between the actions) is drawn as its five boxes:
the objective on top, each need with its action below it, side by side, and the
conflict between the two actions. Each link's assumption is numbered on the drawing
and written out underneath, and a link with no assumption recorded says so. A cloud
that is not complete yet is drawn as an outline.

Ctrl+T puts the keys on the drawing, with a statement chosen; a tinted band marks it.
↑ and ↓ choose another. In a single tree, while the keys are on the drawing or the
details, the chosen statement, the statements it hangs under and those directly below
it keep their colours, and the rest of the tree goes quiet in place: nothing moves or
is hidden, and Tab away brings the whole tree back evenly. **All six** never goes
quiet, since it is for seeing the whole. Its details say what it is and in which tree, its wording and
whether its basis is recorded, then **Worth asking**: the question to put to it in
this tree ("When would this route fail to produce the effect?"). Then every link read
from its side, grouped ("Causes", "Partly because", "Required by"), with the
assumption behind each, or *no assumption stated yet*; the ends of the tree it leads
to, where there are several; the tests that carry it out; its earlier wordings; and where
it came from: who wrote the words it cites, when, and the words themselves, or the
file it was brought in from. At 120 columns or wider they sit beside the trees and
follow your choice; Enter shows them full screen at any size, and Esc returns to the
same statement. Ctrl+T again takes you back to the question, with your draft as you
left it. The app remembers the statement you chose. Choosing, folding and reading
never call the consultant.

To say something about the chosen statement, press **a** (or Commands, **Answer about
the chosen statement**). Its words, role and tree go at the end of your answer
("About “Throughput is not yet operationally defined and accepted” (root cause,
Current Reality Tree): "), and the keyboard goes there, so what you write next says
which statement you mean, and the words that are kept say it too. It is ordinary text:
change or delete it before you send. Your answer still answers the current question,
and nothing is sent until you press Send.

After a reply, **Next step** draws what it proposes under the new question: the
statements and links, marked NEW or REWORDED, as the trees draw them, then the words
they came from ("You wrote, Oct 6, 18:02: “…”"). This is the moment you still know what
you meant, so check the reading there. Nothing in it is in your trees yet: **Accept
all** admits it, **Backlog** decides it one entry at a time, and if it is wrong you can
reject it or say so in your answer. A larger change, such as an import, is summed up in
a line. Once accepted, the Trees page says what changed ("The last step: 68 statements
added · 61 links, in 6 trees"), and the drawing marks those statements NEW or
REWORDED; a folded branch says how many of its statements changed.

Claude and LM Studio propose additions to the trees when you tell them about causes,
conflicts, obstacles or plans, and a new wording or a withdrawal when you ask. The
built-in guide proposes the loop's records, not tree statements. Under Commands
(Ctrl+P), **Import trees** brings in an `.ltp.yaml` file and **Export trees** writes
one; what a file brings in waits in Backlog (the file's goal is proposed as your goal,
or as a new version of it), and anything the trees cannot draw (a joint cause, an
assessment) is kept as a note.

## Deciding what enters your model

The consultant drafts what your words could mean; you decide what becomes part of
your model. What a reply proposes waits in **Backlog**, with the words it came from,
until you accept or reject it. Accepting admits a statement to your model; it does not
make it true, record that you agree, or commit you to act on it.

**Order.** Backlog lists entries in the order they are best decided. An entry comes
after anything it needs that is still waiting, and says so ("waits for 2"). Among the
rest, a new goal comes first, marked *Decide first*, because everything else is judged
against the goal; then the Goal Tree, Current Reality Tree, Evaporating Cloud, Future
Reality Tree, Prerequisite Tree and Transition Tree; then tests, actions, results,
reviews and notes; older entries first. A goal waiting to be decided blocks nothing.

**Deciding.** Choose an entry with ↑ and ↓; on a wide terminal it is shown in full
beside the list. Enter offers its choices; **a** accepts and **r** rejects. Accepting also
takes the waiting entries it needs, and rejecting the waiting entries that need it;
when that is more than you chose, the whole list comes first and nothing changes until
you confirm. Accepting a withdrawal also takes the links that join the statement out
of your trees, and those links are listed first in the same way. A rejection is final
for that proposal; the consultant may propose the idea again. **Accept all**, beside Send, takes everything the last reply proposed.
Deciding never calls the consultant, and you can decide while it is working on your
next answer.

**Reviews.** When you accept a change to something (a new wording, a withdrawal, an
undo), whatever cites it is flagged for review in Backlog, with the change that raised
the flag: a link joined to a reworded statement, a test that carries out a withdrawn
action, a test that served the goal before its new version, an action planned for an
earlier version of a test. A test can be given a new version (a changed forecast, say)
until a result for it is in your model; after that its forecast stays as written, and a
changed plan is a new test. A flag changes nothing and
claims nothing is false. **h** says the record still holds; accepting a new version or
withdrawal of it also closes the flag. Each change flags only what cites it directly,
so a consequence reaches one step further each time you accept a change. **Ask about
the open reviews** (Commands) asks the consultant whether the flagged records still
hold; what it proposes waits like anything else.

**Undo.** In **History**, **u** undoes a step's acceptance (see [looking back](#looking-back)).

**Automatic acceptance.** Commands, **Accept proposals automatically** lets later
replies' proposals enter your model as they arrive, recorded as accepted under your
setting, and Next step says what was added; each can still be undone from History.
A withdrawal that would take links with it still waits for you, so you see them first.
**Hold proposals for review** turns it back. Proposals already waiting keep waiting
either way, and only you change the setting: a consultant cannot, and an agent can
only where you started its server with `--allow-acceptance-setting`.

## Commands

| Command | What it does |
| --- | --- |
| `reason-commons` | The first time, the ways to start; then your goals: open one, start one, the tour or the real commons; F2 opens Settings |
| `reason-commons tui FOLDER` | Open a goal in that folder, creating it if needed |
| `reason-commons resume FOLDER` | Open an existing goal; never creates one |
| `reason-commons export FOLDER FILE` | Write a portable `.reasoncase` copy |
| `reason-commons import FILE --store FOLDER` | Continue from a copy in a new folder |
| `reason-commons show FOLDER_OR_FILE` | Print a goal without opening the workspace |
| `reason-commons trees FOLDER` | Draw the goal's trees; `--import FILE` brings trees in from an `.ltp.yaml` file (they wait in the backlog), `--export FILE` writes them out; `--tree current_reality` draws just one |
| `reason-commons usage` | What Claude's replies cost this month, estimated from the usage log, by model and against your budget; `--month 2026-09`, `--all`, `--goal FOLDER`, `--json`. Sends nothing |
| `reason-commons decide FOLDER accept REF...` | Accept, reject or undo proposals by their refs (`show FOLDER --view backlog` lists them), `still-holds REF`, or `acceptance review\|automatic`; without `--confirm` a decision that takes more than you named lists it and changes nothing |
| `reason-commons --version` | Show the version |

`tui` and `resume` also take `--speaker NAME` (the name recorded with your
answers; default: your login name), `--provider guided|anthropic|lm-studio`,
`--model` and `--base-url`. `tui` takes `--name` for a new goal's name. Every
way of opening the workspace takes `--theme` (see [Themes](#themes)). Commands
for scripts and AI agents are listed by `reason-commons --help`.

### The accessible ordered presentation

`reason-commons tui FOLDER --accessible` (and `resume --accessible`) opens the same
goal as ordered text that is appended, never redrawn, for a screen reader or a
terminal that cannot redraw; it is also used when `TERM=dumb`. Each view begins with
the case, who is answering and whether it is saved, then the view and the control
with focus; then any breach, the decision and question with the goal and its
safeguards, what is uncertain, the test review, what the last reply proposes, your
draft, and the controls, each with its role and consequence. Tab and Shift+Tab move
between controls and say which has focus; Enter or Space activates one; in Response
every key is typed literally, Enter adds a line, and only **Send** asks the
consultant. Page Down and Page Up page a long view ("Page 1 of 3"); Esc returns with
your draft kept. **Case context**, **Explain this**, **Views**, **Backlog** (Accept,
Reject and Still holds, with a decision that takes more listed first) and **Help**
are local. A new view is announced as replacing the one above, so scrollback is not
mistaken for what is current. Nothing depends on colour. With Claude, each reply's cost
is said once after it ("Cost: about $0.0042, Haiku 5.5, estimated."), and so is reaching
80% or all of a monthly budget; past the budget, Send says what the month and the reply
cost and asks to be activated again, and Tab leaves it with nothing sent.

## Settings

Setup saves your name, consultant, model, Claude key and LM Studio address, and Settings
your theme and monthly budget, in
`~/.config/reason-commons/settings.yaml` (or `$XDG_CONFIG_HOME/reason-commons/`;
`REASON_COMMONS_CONFIG` names another file), readable only by you. Command-line
options win over environment variables, which win over that file. To set them in
your shell instead, for example in `~/.zshrc` on a Mac:

| Variable | Effect | Default |
| --- | --- | --- |
| `REASON_COMMONS_HOME` | Folder that holds your goals | `~/ReasonCommons` |
| `REASON_COMMONS_CONFIG` | Personal settings file written by setup | `~/.config/reason-commons/settings.yaml` |
| `REASON_COMMONS_PROVIDER` | Consultant at start: `guided`, `anthropic` or `lm-studio` | `guided` |
| `REASON_COMMONS_SPEAKER` | Name recorded with your answers | the name from setup, else your login name |
| `ANTHROPIC_API_KEY` | Key for Claude | none |
| `REASON_COMMONS_ANTHROPIC_MODEL` | Claude model ID | `claude-haiku-5-5` |
| `REASON_COMMONS_ANTHROPIC_BOOST_MODEL` | The model for one reply with deeper reasoning; `none` turns the offer off | `claude-sonnet-5-5` |
| `REASON_COMMONS_MONTHLY_BUDGET_USD` | A soft monthly budget for Claude's replies, in dollars; `none` or `0` for none | none |
| `REASON_COMMONS_USAGE_LOG` | Where the usage log is kept, or `off` | `~/.local/state/reason-commons/usage.jsonl` |
| `REASON_COMMONS_ANTHROPIC_MAX_TOKENS` | Claude's output budget, thinking included | `16000` |
| `REASON_COMMONS_ANTHROPIC_EFFORT` | Claude's effort: `low` to `max`, or `default` to send none | `high` where the model supports it |
| `REASON_COMMONS_LM_STUDIO_URL` | LM Studio server address | `http://127.0.0.1:1234/v1` |
| `REASON_COMMONS_LM_STUDIO_MODEL` | LM Studio model ID | the only loaded model |
| `LM_STUDIO_API_TOKEN` | LM Studio token, if your server needs one | none |
| `REASON_COMMONS_THEME` | Colour theme (see [Themes](#themes)) | `yoruba-dark` |

Keys and server addresses are never written into your goals or exports.

## Themes

The workspace speaks in the same twelve voices as the Reason Commons web app, each
in a light form (the web palette) and a dark form (the same hues for a dark
terminal). Choose one in the app, and it is kept:

- **In the app:** **Settings** (F2, or Ctrl+P, **Settings**): Left and Right change the
  voice or light/dark on the highlighted row and apply at once. Or Ctrl+P, **Theme**, in a goal:
  moving through the list previews each voice with its description; Left and Right switch
  between light and dark; Enter keeps it and Esc puts back the one you had.
- **In your settings file:** `theme: tanizaki-dark`. The app writes this line when
  you choose in the app.
- **For one run:** `reason-commons --theme "Shadows dark"`, or
  `REASON_COMMONS_THEME=goethe` in your shell, which wins over the settings file.

A theme is named by its id or its label, in any case, with `dark` or `light`
after it if you like:

| Id | Label | Reads its colours from |
| --- | --- | --- |
| `commons` | Commons | the public voice |
| `organic` | Organic | cream and earth |
| `schopenhauer` | Schopenhauer | graphite ink and one judgment colour |
| `goethe` | Goethe | the polarity of yellow and blue |
| `steiner` | Steiner | image and lustre |
| `al-haytham` | Optics | Ibn al-Haytham: the instrument plane |
| `tanizaki` | Shadows | Jun'ichirō Tanizaki: smoked parchment, no white anywhere |
| `suhrawardi` | Illumination | Suhrawardi: presence through degrees of light |
| `wittgenstein` | Grammar | Ludwig Wittgenstein: four hues that exclude one another |
| `yoruba` | Chromatics | Yorùbá chromatics, the default (dark); the mapping is ours, not the tradition's |
| `wuxing` | Five Phases | Wǔsè / Wǔxíng; the four assignments are ours |
| `khipu` | Channels | Inka khipu; the theme that leans least on hue |

Every theme keeps the web app's four colour families apart: the **hand** (yours to
act on: Send, focus, the frame around what you are editing), **proposed** (not yet
in the record), **stood behind** (relied upon) and **disagreed** (reality pushed
back, or something going wrong). In the Trees view, what you want is drawn in
stood behind, what is wrong in disagreed, what you do in the hand and what you
think you must do in proposed. Every coloured word clears WCAG AA contrast on its
background. Fonts are your terminal's; rounded frames stand in for the web's soft
corners, and square frames for its hard-edged voices.

## The goal folder

Each goal is a folder of plain YAML files, saved as you type: revisions, your
inputs, consultant attempts and the workspace position (view and unsent draft). A
lock file lets only one workspace edit a goal at a time. Treat the folder as a
whole; use export and import rather than editing files by hand.

## Not in this version yet

Switching between several people
in one goal, attaching sources from the workspace, the trees' richer reasoning
checks (joint causes, rival explanations, and boxed diagrams for the trees other than
the Evaporating Cloud), review of consequences that no reference records, editing a
proposal's wording yourself before accepting it, and automatic acceptance above a
confidence you choose. They
are specified in [TUI-DESIGN.md](../TUI-DESIGN.md).
