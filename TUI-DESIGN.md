# Reason Commons terminal design contract

Reason Commons opens a persistent terminal workspace from its first usable release.
Read the [canonical session](reason-commons-spec/example-tui-session.txt),
[v1 session](reason-commons-spec/example-mvp-session.txt) and
[rendering contract](reason-commons-spec/tui-reasoning-design.md) before implementing
screens. These are required behavior, not optional future styling. A first
personal-use slice is implemented in `src/reason_commons/adapters/tui.py`
([run guide](docs/tui.md)); it does not yet meet this whole contract.

## Direction and references

The workflow combines consulting, inspect-and-challenge, bounded action and
review. The screen combines an editor with master-detail reasoning inspection;
it is not a wizard. Use the Monospace Design TUI
[agent guidance](https://coreyt.github.io/monospace-design-tui/agents/),
[standard](https://coreyt.github.io/monospace-design-tui/standard/) and
[patterns](https://coreyt.github.io/monospace-design-tui/patterns/) as references.
Reason Commons requirements control project-specific behavior. We do not claim full
Mono compliance. Reading these references requires no installation or external
action. Framework selection is open: require multiline input, reliable focus,
responsive layout, asynchronous workers and terminal cleanup.

Required patterns: Focused Surface, Footer Command Bar, Master-Detail,
Expand-to-Focus, Object-Local Actions, filtered Commands palette (the
specification calls it Actions; on screen it is **Commands**),
and selection grammar. Returning restores exact selection and draft. A model
completion notice never moves the user's view or focus without their action.

## Canvas and visual grammar

Target 120×40. Reserve 12–16 columns for destinations; give the reasoning region
the remaining width. A right inspector may use 28–36 columns when all decisive
premises still fit. Prefer full words and separate branches over counters.
Support 80×24 by stacking or expanding the task region; use 40×24 relation
sentences with visible Views. Below that, retain state and offer resize or linear
presentation. Reflow preserves logic, IDs, draft, target and focus.

Default named palette: Mono **Default**, with text/symbol statuses. Monochrome
and ASCII are fully functional alternatives. ASCII is the specimen baseline;
Unicode borders may improve continuity but cannot carry unique meaning.
Measure terminal display cells, not bytes or code points.

Draw measured node boxes with padding and reserved connector gutters. Connections
terminate at explicit ports. Joint causal inferences have an ALL enclosure or
gate, complete inputs and one labeled output. Independent routes never merge
implicitly. Necessity says requires; conflict states scope and incompatibility;
predictions are labeled; trace references say tests, addresses or implements.

## Hierarchy, names and focus

One screen is read in one order. Each rule below was a clarity defect before it became a rule
(see the evaluator's findings behind it in [TUI-UX-PLAN.md](TUI-UX-PLAN.md#navigation-and-hierarchy-revision)).

- **One spine.** The loop line is the only thing that says where you are in the loop. The Views list is
  secondary: it names what else can be read, with ▸ beside the open view. The view's name is in the
  list and the page's heading, never also in the header.
- **Heading, question, hint.** The heading is the strongest line, the question is plain type and an
  optional-answer hint is the quietest. A goal with nothing recorded says "Measure: not set" on the loop
  line, never "No goal yet" under the goal's own name.
- **The answer sits at the question.** The answer box follows what it answers, with an example fading in
  while it is empty. A long page scrolls above it, so the box never leaves the screen; the line about
  Enter and Send sits beside its buttons, or under them when they leave no room. On any other view the
  box's tag names the question it answers, and while it is empty and unfocused it folds to one line;
  Tab or a click opens it, and a draft keeps it open.
- **Focus is a frame.** Where the keyboard is has a heavy frame in the accent colour (a heavy bar at the
  edge for the page and the trees, a highlight for a button or a footer control). No label names it. The header says only the goal's name, who you are
  and whether it is saved.
- **The footer speaks for the focused pane.** It lists the keys that work there, then Commands, with Help
  on the right. Every key it names must be a real binding. Commands and Help are also controls: Tab
  reaches them and Enter presses them. On a narrow terminal the hints say less and then drop from the
  end, but Commands and Help always stay, and the footer never changes under a click.
- **One word, one meaning.** *Commands* is everything you can do (Ctrl+P). *Loop actions* is the view of
  the plan's actions. *Action* is a step of the loop.
- **No raw data.** Ids, engine revisions and ISO timestamps never show. A time is on the person's own
  clock ("Oct 3, 18:02"), and who wrote it appears only when more than one person has.
- **Home.** Ways to *Start*, then *Your goals* as aligned columns (name, stage, day last changed).
  Settings are behind F2, and the footer says what they are now.
- **The trees read as sentences.** A statement opens its line, led in by its relation word
  ("because:"); its role is a quiet trailing tag in its colour family and the assumption behind the
  link hangs under it after a dotted rule (┆). A statement whose only deeper branch is its last
  continues the spine at the same indent, so a chain never drifts right. Each tree's page gives its
  name, its question and which way to read it; the Views list names *All six* and the six trees
  under *Trees*. The trees open first on all six, folded at what each is for; Space folds and unfolds.
  The chosen statement is a tinted band; focus stays the frame. Its details lead with *Worth asking*,
  the tree's question from the visual-grammar table of the rendering contract.
- **Dim, don't hide.** In one tree, while the keyboard is on the drawing or the chosen statement's
  details, that statement, every statement it hangs under and those directly below it keep their
  colours; every other line takes one quiet tone (about a third of full contrast) in the same place.
  Nothing moves, folds or goes. Leaving the drawing brings the whole tree back evenly; *All six* and a
  boxed Cloud never dim. Folding stays an explicit choice (Space), never a way of reducing attention.
- **Where paths meet, say so.** A statement reached by several paths says, on its own line, how many
  of its tree's ends it leads to ("leads to 5 of 6 undesirable effects"; in the Future Reality Tree only
  a change we make, benefits and harms together). It is a count of recorded links, never a rank or a
  finding about the constraint. A tree's page also counts what it does not state yet: links with no
  assumption and statements with no basis. Each missing assumption is said where it is looked at
  ("no assumption stated yet"), not raised in a prompt.
- **A forecast in a tree is sealed.** A test under a statement reads as the test, then its *original
  forecast, saved before any result*, then the result. No verdict mark appears that no one recorded.
- **Show the proposal while the speaker still knows what they meant.** After a reply, Next step draws
  what it proposes under the new question, as the trees draw them, beside the words they came from,
  marked *proposed*, with **Accept all** and **Backlog**; a larger change is summed up in a line. To
  correct a wrong reading, reject it or say so in the answer. Accepting admits the reading into the
  model; it is not agreement, and a stance still waits for the position records of p4. Under automatic
  acceptance the same place says what entered the model with the reply and that History can undo it.
- **The model and the backlog never mix.** Trees, Goal and Tests show what has been accepted; a
  proposal appears only in Next step, the Backlog and its own details, always marked *proposed*. The
  Backlog lists proposals and review flags in decision order: what an entry cites first, then a new
  goal (marked *decide first*), the Goal Tree, Current Reality, Cloud, Future Reality, Prerequisite and
  Transition Trees, tests, actions, observations, reviews and notes. A row says what it waits for, and
  a flag names the change that raised it. An action that takes other records with it lists them
  before anything changes; Undo, in History, says it is final.
- **Pointing goes into the words.** *Answer about this* (a) puts the chosen statement's words, role and
  tree at the end of the draft as ordinary editable text, so the kept input says which statement "that
  one" was. It changes neither the live question nor the target; an exact subject reference waits for
  the structured authoring of p3.
- **Records in columns.** Goal, Loop actions and Reasoning use the aligned label column of Next step;
  Reasoning puts what is still open first. History is one row per step. Commands are one line each,
  each still marked local or consultant.

## Project adaptations to Mono

| Reference | Adaptation | Reason and observable check |
|---|---|---|
| §1.4/§2.3 footer commands | OVERRIDE: context-critical keys in persistent footer; remaining actions have visible controls and filtered Help/Commands. Commands and Help are footer controls that Tab reaches and Enter presses | No required action depends on recalled syntax or an invisible key |
| §2.2 keyboard scope | TIGHTEN: all printable keys, including `?`, `q`, numbers, `:` and `/`, are literal in Response and filters | Sending those strings cannot navigate, quit or record a position |
| §2.2 command activation | OVERRIDE: Ctrl+P opens Commands (the specification's Actions); inside it arrows select and printable keys filter. F10/action-bar keys optional; visible Commands required, in the footer | Complete the journey with Tab, arrows, Space, Enter and Esc |
| §1.6 reflow | TIGHTEN: reflow semantic relations first; use complete records when connectors become ambiguous | No lost negation, input, objection or breach |
| §8 state | TIGHTEN: save, evidence, freshness, execution, attainment and human positions independent | Selection/save/completion cannot imply truth or consensus |

Tab/Shift+Tab traverse controls; arrows operate within one control. Response
Enter adds a newline; Tab to Send then Enter submits once. Paste never submits.
Esc leaves editor focus for browsing while retaining text. Help is visible as
well as F1; Explain this teaches reasoning separately. In browsing Enter opens,
Space expands a branch, `/` filters and `?` opens help. Optional letter accelerators
cannot intercept text. Quit is available through Commands.

Navigation checkpoints the cursor. New input invokes the consultant only through
labeled Send or a consultant action. Explicit structured decisions share the
shared exact-target transaction validator. No stance/reliance choice is preselected. Switching
speakers retains drafts by actor and question and invalidates actor-bound decision forms.

The shell provides launch, resume and offline utilities. `new`/`resume` open
the workspace. Plain `reason-commons` in a terminal opens a goals home
list (open one, or start a new goal by name) before the workspace; it adds no
command language. `--accessible` selects ordered text with the same labeled
controls, literal editor, explicit submission and exact targets; see
[accessibility.md](reason-commons-spec/accessibility.md). There is no separate
interactive command language. `TERM=dumb` offers ordered text; non-TTY input
cannot start a hidden conversation.

The product name is Reason Commons and the executable is `reason-commons`.
Users work with questions, reports, relationships, tests, actions and reviews.
Internal intervention records never become a stationery metaphor, navigation
label or numbered object users must learn. Human titles identify the task.

## Delivery gate

P1 includes workspace, controls, multiline input, draft preservation, asynchronous
focus stability, recovery and 80×24. P2 adds original forecast/outcome review and
the Trees view: the six trees drawn as indented outlines from recorded claims and
single links (S128–S134), with a chosen statement's links, wording and origin
beside them (Master-Detail) or full screen (Expand-to-Focus). A complete Evaporating
Cloud, whose five places are fixed and need no routing, is drawn as its five boxes
now, so both sides are visible; joint premises, rival routes and the other boxed
canvases arrive in p3–p5; the TUI is not deferred. P2 also adds the Backlog, where the
operator accepts or rejects what replies propose and closes review flags, with Undo in
History (S135–S147). Use S114–S147 alongside earlier integrity and reasoning gates. Authored snapshots
and document checks do not prove a running TUI or measured usability.
