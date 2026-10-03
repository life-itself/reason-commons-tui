# Workspace reference

Facts to look up while you work. To learn the workspace step by step, follow the
[tutorial](tutorial.md); to install it, see the [README](../README.md#try-it).

## The screen

| Part | What it shows |
| --- | --- |
| Top line | The goal's name, your name, whether everything is saved, the current step and the consultant |
| Pinned line | Your goal, safeguards and current test with its forecast |
| Loop line | Goal → Test + forecast → Action → Observe → Review; ✓ marks finished steps and > the current one |
| Middle | The current question and what it builds on, or the view you chose |
| Views list | On terminals 100 columns or wider; otherwise use **Views** |
| Answer box | Your answer; all typing is literal, including `?`, `q` and numbers |

## Keys and controls

| Key or control | What it does |
| --- | --- |
| Enter | New line in your answer |
| Ctrl+S, or Tab to **Send** then Enter | Send your answer |
| Tab / Shift+Tab | Move between controls |
| Esc | Leave the answer box to browse; your text stays |
| **Explain this** | Why the current question matters (saved, no consultant call) |
| **Other moves** | Local explanations, or ask the consultant for advice or a different question |
| **Views** | Switch view (also the list on the left) |
| Ctrl+P (**Actions**) | Export, import or export trees, retry, change consultant, views, help, quit |
| F1 | Help |
| Ctrl+Q | Save your draft and quit |

On the goals list: arrows choose, Enter opens, F1 shows help, Ctrl+Q quits.

## Views

Browsing views never calls the consultant.

| View | Shows |
| --- | --- |
| Next step | The current question and what it builds on |
| Goal | Goal, measure and safeguards |
| Trees | The six thinking-process trees, drawn from what was recorded; each branch says how a statement relates to the one above it |
| Tests | Each test with its original forecast next to the reported result, and reviews |
| Actions | Planned actions |
| Everything | All saved records |
| Your words | Your answers, exactly as written |
| History | Every saved revision with its time |

With the built-in guide, an empty answer skips an optional question (measure,
safeguards, review date, stop condition).

## The trees

The Trees view shows the Goal, Current Reality, Evaporating Cloud, Future Reality,
Prerequisite and Transition Trees, one below the other. Each statement shows its
role (for example ROOT CAUSE or OBSTACLE) and, where recorded, whether it is a
hypothesis or a report. Branches read top down: "needs", "because", "overcomes",
"produced by". A statement reached twice is drawn once and then referred to.

Claude and LM Studio add to the trees when you tell them about causes, conflicts,
obstacles or plans, and reword or drop a statement when you ask. The built-in
guide does not add to them. Under Actions (Ctrl+P), **Import trees** brings in an
`.ltp.yaml` file and **Export trees** writes one; imported trees join the ones
already there, and anything the trees cannot draw (a joint cause, an assessment)
is kept as a note.

## Commands

| Command | What it does |
| --- | --- |
| `reason-commons` | Show your goals; open one, start one or look at a finished example |
| `reason-commons tui FOLDER` | Open a goal in that folder, creating it if needed |
| `reason-commons resume FOLDER` | Open an existing goal; never creates one |
| `reason-commons export FOLDER FILE` | Write a portable `.reasoncase` copy |
| `reason-commons import FILE --store FOLDER` | Continue from a copy in a new folder |
| `reason-commons show FOLDER_OR_FILE` | Print a goal without opening the workspace |
| `reason-commons trees FOLDER` | Draw the goal's trees; `--import FILE` brings trees in from an `.ltp.yaml` file, `--export FILE` writes them out |
| `reason-commons --version` | Show the version |

`tui` and `resume` also take `--speaker NAME` (the name recorded with your
answers; default: your login name), `--provider guided|anthropic|lm-studio`,
`--model` and `--base-url`. `tui` takes `--name` for a new goal's name. Commands
for scripts and AI agents are listed by `reason-commons --help`.

## Settings

Set these in your shell, for example in `~/.zshrc` on a Mac.

| Variable | Effect | Default |
| --- | --- | --- |
| `REASON_COMMONS_HOME` | Folder that holds your goals | `~/ReasonCommons` |
| `REASON_COMMONS_PROVIDER` | Consultant at start: `guided`, `anthropic` or `lm-studio` | `guided` |
| `REASON_COMMONS_SPEAKER` | Name recorded with your answers | your login name |
| `ANTHROPIC_API_KEY` | Key for Claude | none |
| `REASON_COMMONS_ANTHROPIC_MODEL` | Claude model ID | `claude-sonnet-5-5` |
| `REASON_COMMONS_LM_STUDIO_URL` | LM Studio server address | `http://127.0.0.1:1234/v1` |
| `REASON_COMMONS_LM_STUDIO_MODEL` | LM Studio model ID | the only loaded model |
| `LM_STUDIO_API_TOKEN` | LM Studio token, if your server needs one | none |

Keys and server addresses are never written into your goals or exports.

## The goal folder

Each goal is a folder of plain YAML files, saved as you type: revisions, your
inputs, consultant attempts and the workspace position (view and unsent draft). A
lock file lets only one workspace edit a goal at a time. Treat the folder as a
whole; use export and import rather than editing files by hand.

## Not in this version yet

An accessible plain-text mode (`--accessible`), switching between several people
in one goal, attaching sources from the workspace, and the trees' richer reasoning
checks (joint causes, rival explanations, boxed diagrams). They
are specified in [TUI-DESIGN.md](../TUI-DESIGN.md).
