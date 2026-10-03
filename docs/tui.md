# Running the Reason Commons workspace (TUI)

The workspace is a terminal app for working on one goal with the Reason Commons
loop: **goal → test with a forecast → action → observation → review**. Everything
is saved in a case folder as you type, so you can quit and resume at any time.

This is a first, personal-use slice of p1. It is not the complete p1 contract
(see "What is not in this slice" below).

## Run it on a Mac

You need Python 3.9 or newer (`python3 --version`). In Terminal:

```sh
git clone https://github.com/life-itself/reason-commons-tui.git
cd reason-commons-tui
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip   # macOS ships an old pip that cannot install this
python3 -m pip install -e '.[tui]'

reason-commons tui ~/ReasonCommons/my-first-goal
```

The last command creates the case folder if it does not exist and opens the
workspace. Run the same command again later to resume exactly where you left
off, including your unsent draft. `reason-commons resume <folder>` does the same
but refuses to create a new case.

Next time, you only need:

```sh
cd reason-commons-tui && source .venv/bin/activate
reason-commons tui ~/ReasonCommons/my-first-goal
```

Options: `--speaker "David"` sets the name recorded with your answers (default:
your login name), `--name "Running"` names a new case (default: the folder name).

## Choosing a consultant

| Consultant | How to choose it | Needs |
| --- | --- | --- |
| Built-in guide (default) | nothing to do, or `--provider guided` | nothing; works offline |
| Anthropic Claude | `--provider anthropic` | `export ANTHROPIC_API_KEY=...` before starting |
| LM Studio | `--provider lm-studio` | a local LM Studio server, see [lm-studio.md](lm-studio.md) |

The **built-in guide** asks the loop's questions in a fixed order and records your
literal words. It cannot give advice or rephrase. An AI consultant adapts its
questions, notices what is missing and can give direct advice (Other moves).
You can switch at any time with **Ctrl+P → Consultant: ...**; the case keeps
going from where it is. `REASON_COMMONS_PROVIDER=anthropic` makes a choice the
default. Optional: `REASON_COMMONS_ANTHROPIC_MODEL` picks a different Claude model.

If a consultant cannot be reached, your answer is still saved. A **Retry** button
appears; it asks again with the saved answer (for example after switching to
another consultant).

## Using the workspace

- The top line shows the case, your name, the saved revision, the current step and
  the consultant. The line below pins your goal, safeguards and current test.
- The middle shows the current question and what it builds on. The left list
  (on wide terminals) or **Views** switches to Goal, Tests (original forecast next
  to the reported result), Actions, Everything, Your words and History.
  Browsing never calls the consultant.
- Type your answer in the box at the bottom. **Enter** adds a line; **Ctrl+S**, or
  Tab to **Send** and Enter, sends it. All typing is literal.
- **Explain this** shows why the question matters. **Other moves** offers local
  explanations and consultant requests (advice, a different question).
- **Ctrl+P** (Actions) has export, retry, consultant choice, help and quit.
  **F1** shows help. **Ctrl+Q** saves your draft and quits.

With the built-in guide, empty answers skip optional questions (measure,
safeguards, review date, stop condition).

## Your data

Each case is a plain folder of YAML files (`~/ReasonCommons/my-first-goal` above).
`reason-commons show <folder>` prints it without opening the workspace, and
Ctrl+P → Export case writes a portable `.reasoncase` file. Only one workspace
can edit a case at a time.

## What is not in this slice

Polished 80×24 layout specimens, the `--accessible` ordered-text mode, speaker
switching, source attachment from the TUI, the measured usability study, and the
p2 consulting-quality gates. Those remain as specified in
[TUI-DESIGN.md](../TUI-DESIGN.md) and the delivery manifest.
