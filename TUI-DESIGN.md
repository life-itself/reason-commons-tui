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
Expand-to-Focus, Object-Local Actions, filtered Actions palette,
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

## Project adaptations to Mono

| Reference | Adaptation | Reason and observable check |
|---|---|---|
| §1.4/§2.3 footer commands | OVERRIDE: context-critical keys in persistent footer; remaining actions have visible controls and filtered Help/Actions | No required action depends on recalled syntax or an invisible key |
| §2.2 keyboard scope | TIGHTEN: all printable keys, including `?`, `q`, numbers, `:` and `/`, are literal in Response and filters | Sending those strings cannot navigate, quit or record a position |
| §2.2 command activation | OVERRIDE: Ctrl+P opens Actions; inside it arrows select and printable keys filter. F10/action-bar keys optional; visible Actions required | Complete the journey with Tab, arrows, Space, Enter and Esc |
| §1.6 reflow | TIGHTEN: reflow semantic relations first; use complete records when connectors become ambiguous | No lost negation, input, objection or breach |
| §8 state | TIGHTEN: save, evidence, freshness, execution, attainment and human positions independent | Selection/save/completion cannot imply truth or consensus |

Tab/Shift+Tab traverse controls; arrows operate within one control. Response
Enter adds a newline; Tab to Send then Enter submits once. Paste never submits.
Esc leaves editor focus for browsing while retaining text. Help is visible as
well as F1; Explain this teaches reasoning separately. In browsing Enter opens,
Space expands a branch, `/` filters and `?` opens help. Optional letter accelerators
cannot intercept text. Quit is available through Actions.

Navigation checkpoints the cursor. New input invokes the consultant only through
labeled Send or a consultant action. Explicit structured decisions share the
shared exact-target transaction validator. No stance/reliance choice is preselected. Switching
speakers retains drafts by actor and question and invalidates actor-bound decision forms.

The shell provides launch, resume and offline utilities. `new`/`resume` open
the workspace. `--accessible` selects ordered text with the same labeled
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
focus stability, recovery and 80×24. P2 adds original forecast/outcome review.
Typed graphs arrive in p3–p5 with their schemas; the TUI is not deferred. Use
S114–S127 alongside earlier integrity and reasoning gates. Authored snapshots
and document checks do not prove a running TUI or measured usability.
