# Running the Reason Commons workspace (TUI)

The workspace is a terminal app for working on one goal with the Reason Commons
loop: **goal → test with a forecast → action → observation → review**. Everything
is saved in a case folder as you type, so you can quit and resume at any time.

This is a first, personal-use slice of p1. It is not the complete p1 contract
(see "What is not in this slice" below).

## Run it on a Mac

Install [uv](https://docs.astral.sh/uv/) once (`curl -LsSf https://astral.sh/uv/install.sh | sh`
or `brew install uv`), open a new Terminal window, then:

```sh
uv tool install git+https://github.com/life-itself/reason-commons-tui
reason-commons
```

uv brings its own Python. If macOS offers to install the command line developer
tools (for git), accept. If `reason-commons` is not found, run `uv tool update-shell`
and open a new window. Update with `uv tool upgrade reason-commons`.

`reason-commons` opens your goals: pick one with the arrows and Enter, or choose
**Start a new goal** and give it a short name. To see a whole loop before starting your own,
choose **Look around a finished example first**: a fictional goal walked through
goal, test, action, observation and review. Nothing you do there is kept. Goals live in `~/ReasonCommons`, one
folder each (set `REASON_COMMONS_HOME` to keep them elsewhere). Everything is saved
as you type, including an unsent draft, so the next `reason-commons` takes you back
to where you left off.

To keep a goal in a folder of your own choosing, give the folder:
`reason-commons tui ~/Projects/payments-goal` creates or opens it, and
`reason-commons resume <folder>` opens it but never creates one.

Options: `--speaker "David"` sets the name recorded with your answers (default:
your login name), `--name "Running"` names a new goal created by `tui <folder>`
(default: the folder name).

To work on Reason Commons itself instead, clone the repository and install it
into a virtual environment with `python3 -m pip install -e '.[test]'` (upgrade pip
first on macOS); see the README's developer section.

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

- The top line shows the goal, your name, whether everything is saved, the current
  step and the consultant. The line below pins your goal, safeguards and current
  test. Under it, the loop (Goal, Test + forecast, Action, Observe, Review) marks
  finished steps with ✓ and the current one with >.
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
