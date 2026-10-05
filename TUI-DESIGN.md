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
  Enter and Send sits beside its buttons, or under them when they leave no room.
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
beside them (Master-Detail) or full screen (Expand-to-Focus). Joint premises, rival routes and boxed canvases arrive
in p3–p5; the TUI is not deferred. Use S114–S134 alongside earlier integrity and
reasoning gates. Authored snapshots
and document checks do not prove a running TUI or measured usability.
