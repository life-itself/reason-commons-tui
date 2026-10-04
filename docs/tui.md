# Workspace reference

Facts to look up while you work. To learn the workspace step by step, follow the
[tutorial](tutorial.md); to install it, see the [README](../README.md#try-it).

## The screen

| Part | What it shows |
| --- | --- |
| Top line | The goal's name, your name, whether everything is saved (or *Asking …* while the consultant works, *Answer ready* when its reply waits on **Next step**), the view, and on the right which control has the keyboard |
| Pinned lines | Your goal and safeguards; a long goal ends in … and **Goal** shows all of it. At review the safeguards move down, next to the result |
| Loop line | Goal, Test + forecast, Action, Observe, Review: ✓ finished, ● current, ○ still to come |
| Middle | The current question and what it builds on (at review: the original forecast beside the result), or the view you chose |
| Views list | On terminals 100 columns or wider; narrower, the **Views** button takes its place |
| Answer box | Your answer; all typing is literal, including `?`, `q` and numbers. Its frame says who you answer as and who **Send** asks, and turns bright while you type. It grows as you write |

## Keys and controls

| Key or control | What it does |
| --- | --- |
| Enter | New line in your answer |
| Ctrl+S, or Tab to **Send** then Enter | Send your answer |
| Tab / Shift+Tab | Move between controls |
| Esc | Leave the answer box to browse; your text stays |
| Ctrl+T | Open the trees; press again to go back to the current question |
| Ctrl+N | In the Trees view: the next tree, one at a time, then all six together |
| **Explain this** | Why the current question matters (saved, no consultant call) |
| **Other moves** | Local explanations, or ask the consultant for advice or a different question |
| **Views** | Switch view, when the list on the left does not fit |
| Ctrl+P (**Actions**) | Export, import or export trees, retry, change consultant, views, help, quit |
| F1 | Help |
| Ctrl+Q | Save your draft and quit |

On the goals list: arrows choose, Enter opens, F1 shows help, Ctrl+Q quits.

## First start, settings and the tour

The first time, `reason-commons` offers four ways to start: start a first goal
straight away (the offline guide, with your login name), choose who asks the
questions first, take the guided tour, or look around a finished example. Choosing
first asks for your name (recorded with your answers), the consultant and, for
Claude or LM Studio, checks the connection and lets you choose a model. Esc goes
back a step; leaving setup changes nothing. **Settings** on the home screen runs
it again.

The guided tour opens a practice goal with the built-in guide. A coaching strip
explains each of the six steps; **Example answer** puts the tutorial's answer in
the box and **Finish tour** returns to the home screen. The practice goal is
deleted afterwards.

## Views

Browsing views never calls the consultant.

| View | Shows |
| --- | --- |
| Next step | The current question and what it builds on |
| Goal | Goal, measure and safeguards |
| Trees | The six thinking-process trees, drawn from what was recorded; each branch says how a statement relates to the one above it |
| Tests | Each test with its original forecast next to the reported result, and reviews |
| Actions | Planned actions |
| Reasoning | All saved records, and what is still open |
| Your words | Your answers, exactly as written |
| History | Every saved revision with its time |

With the built-in guide, an empty answer skips an optional question (measure,
safeguards, review date, stop condition).

## The trees

Ctrl+T opens the Trees view and shows one tree at a time: Goal, Current Reality,
Evaporating Cloud, Future Reality, Prerequisite or Transition. Ctrl+N moves to the
next one, and after the Transition Tree shows all six together; the line at the top
says which tree is on screen and how many statements each holds. The app remembers
the tree you last looked at. Ctrl+T again takes you back to the current question. Each statement shows its
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
| `reason-commons` | The first time, the ways to start; then your goals: open one, start one, the tour, the finished example or Settings |
| `reason-commons tui FOLDER` | Open a goal in that folder, creating it if needed |
| `reason-commons resume FOLDER` | Open an existing goal; never creates one |
| `reason-commons export FOLDER FILE` | Write a portable `.reasoncase` copy |
| `reason-commons import FILE --store FOLDER` | Continue from a copy in a new folder |
| `reason-commons show FOLDER_OR_FILE` | Print a goal without opening the workspace |
| `reason-commons trees FOLDER` | Draw the goal's trees; `--import FILE` brings trees in from an `.ltp.yaml` file, `--export FILE` writes them out; `--tree current_reality` draws just one |
| `reason-commons --version` | Show the version |

`tui` and `resume` also take `--speaker NAME` (the name recorded with your
answers; default: your login name), `--provider guided|anthropic|lm-studio`,
`--model` and `--base-url`. `tui` takes `--name` for a new goal's name. Commands
for scripts and AI agents are listed by `reason-commons --help`.

## Settings

Setup saves your name, consultant, model, Claude key and LM Studio address in
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
