# Reason Commons

**See a hard problem whole, as connected trees, then change it one honest test at a time.**

Reason Commons is a calm workspace for reasoning about change: what you are aiming
for, what is really in the way, which conflict keeps you stuck and what to try next.
It is built on the **Logical Thinking Process** from the Theory of Constraints, a
method that lays out that reasoning as six connected trees instead of long prose.
Today it runs in your terminal, offline, and keeps your own words.

Throughout this page we use one real case: the **Second Renaissance**, a movement
that wants to help bring about a wiser, more regenerative culture. Its own documents
were analysed tree by tree in the
[Reason Commons guide](https://github.com/life-itself/reasoncommons/tree/main/ltp);
the pictures below are drawn from that analysis.

## Six questions, six trees

Every real change has to answer six questions. Each tree answers one, and each
connects to the next.

| Question | Tree |
| --- | --- |
| What must be true for us to reach the goal? | [Goal Tree](#goal-tree) |
| Why are we not there yet? | [Current Reality Tree](#current-reality-tree) |
| What conflict keeps us stuck? | [Evaporating Cloud](#evaporating-cloud) |
| If we change this, will it work, and what could go wrong? | [Future Reality Tree](#future-reality-tree) |
| What stands in the way, and what comes first? | [Prerequisite Tree](#prerequisite-tree) |
| What exactly do we do next? | [Transition Tree](#transition-tree) |

The first three are a **tree of change**: where we want to be, and why we are not
there. The last three are a **tree of action**: what to do about it, in order.

### Goal Tree

The movement's goal is vast. The Goal Tree breaks it into three critical success
factors and six necessary conditions, so any small step can be checked against the
whole.

![Goal Tree: the goal, a wiser, weller, regenerative civilisation, rests on three critical success factors (durable embodiment, learning and revision, transmissible pockets), each resting on two necessary conditions](docs/images/trees/goal-tree.svg)

### Current Reality Tree

Many people resonate with the Second Renaissance, yet few enter sustained practice.
Following the symptoms down from effect to cause leads to one likely constraint:
there is no reliable path from interest to practice.

![Current Reality Tree: the root cause "no reliable path from interest to practice" leads to newcomers not knowing the next step, few sustained practitioners, organiser overload, fragile pockets and weak replication; three more root causes feed the top symptom, a busy group with low lasting adoption](docs/images/trees/current-reality-tree.svg)

### Evaporating Cloud

The group feels pulled two ways: act like a movement to be visible, or like a
monastery to be embodied. Both needs are real. The cloud brings out the hidden
assumption that both draw on the same scarce organisers, and questioning it opens
a way out.

![Evaporating Cloud: "act like a movement now" serves the need to be visible and "act like a monastery or lab now" serves the need to be embodied; both needs serve durable cultural transformation, but the two actions conflict; the change that dissolves the conflict is a broad public invitation built around deep, protected practice pockets](docs/images/trees/evaporating-cloud.svg)

### Future Reality Tree

Before committing, check that the proposed changes really lead to the goal, and
what they might break. Two risks show up, reductive metrics and a manipulative
funnel, and each gets a trim.

![Future Reality Tree: seven changes lead through five desired effects to verified lasting adoption and the goal; two negative branches, counting replacing real change and people feeling funnelled, hang off two of the changes](docs/images/trees/future-reality-tree.svg)

### Prerequisite Tree

Seven obstacles stand between today and scaling through depth. Each is overcome by
an intermediate objective, in order. The first is to agree how the model itself
gets checked.

![Prerequisite Tree: seven obstacles, each overcome by an intermediate objective, stacked in order from "a stewarded model, accepted for provisional use" up to "a maturity-rated, adaptable practice library", which leads to scaling through depth](docs/images/trees/prerequisite-tree.svg)

### Transition Tree

Concrete actions, each with what you expect to see when it works. The first is one
time-boxed review of the whole model.

![Transition Tree: four actions, each with what we expect to see and the objective it achieves; the first, marked do this first, is one time-boxed, stewarded review of the goal, the symptoms and the likely constraint](docs/images/trees/transition-tree.svg)

More on how to read each tree: [the six trees, explained](docs/the-trees.md).

## In the app: trees that grow as you talk

The app's **Trees** view draws all six trees. They grow from the conversation: tell
the consultant what causes a problem, which conflict keeps you stuck, what stands
in the way or what you plan to do, and it records each statement in its tree,
linked to the others, in your own words. Ask it to reword or drop something and the
tree changes, while the earlier wording stays in the history. Trees you already
have come in from an `.ltp.yaml` file (the format the Reason Commons guide uses),
and go out the same way.

![The Trees view: the Goal Tree drawn as an outline, the goal at the top and each critical success factor and necessary condition below it, with "needs" written on every branch](docs/images/trees-view.png)

## From tree to test

Trees say what might work. The loop finds out: you take **one action**, write down
what you expect **before** it happens, do it, and review what happened against that
forecast.

![The loop: 1 Goal, 2 Test + forecast, 3 Action, 4 Observe, 5 Review, then again](docs/images/loop.svg)

Here is the Transition Tree's third action, *prototype one clear next step from an
open evening to a first practice*, as an organiser would run it. The goal and its
safeguards stay pinned at the top, and the line under them shows where you are.

![The workspace mid-loop: the goal of a clear, no-pressure next step after open evenings is pinned, with its safeguards; the loop line shows Goal, Test and Action done and Observe current; the guide asks what actually happened](docs/images/in-progress.png)

Three weeks later the forecast sits next to the result. The forecast was 6 of 30
newcomers; the result was 9 of 31, with both safeguards intact. This is where the
learning is. A test can name the tree action it carries out, and its forecast and
result then show under that action in the Trees view.

![The Tests view: the original forecast, 6 of 30 newcomers at a first practice within 3 weeks, next to the reported result, 9 of 31](docs/images/forecast-vs-result.png)

| | In the app today |
| --- | --- |
| The loop: goal, test with forecast, action, observation, review | **Works now**, offline, with a built-in guide or an AI consultant |
| All six trees | **Drawn now**. Claude or a local model adds to them as you talk; any consultant can work with trees you import |
| Joint causes (AND), rival explanations, flags on tests when a cause changes | Planned |
| Group work: several people's positions on one tree | Planned |

The order follows the [delivery plan](reason-commons-spec/delivery-phases.md).

## Is this for you?

It suits any change where you are not sure what will work, for example:

- **A movement:** "Turn people who resonate with our ideas into people who practise them."
- **A community group:** "Get more neighbours to the monthly meeting without burning out the organisers."
- **A team:** "Cut the time our changes wait for release, without more rollbacks."

After one loop you have a written goal and safeguards, a forecast you can't quietly
rewrite, an honest record of what happened and a decision you can explain. It is
all in a plain folder you own.

## Try it

On a Mac, install [uv](https://docs.astral.sh/uv/) once, then open a new Terminal window:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install Reason Commons and start it:

```sh
uv tool install git+https://github.com/life-itself/reason-commons-tui
reason-commons
```

That is all; there is no Python setup to manage. To update later, run
`uv tool upgrade reason-commons`.

`reason-commons` opens a list of your goals. Start a new one, or look around the
finished open-evening example first. A new goal opens with a short welcome and one
question; you answer in ordinary words, Enter adds a line and Ctrl+S sends.

![The home screen lists goals with their current step, plus Start a new goal and a finished example](docs/images/home.png)

Everything is saved as you type, including an unsent draft. Quit with Ctrl+Q and
`reason-commons` takes you back to where you were.

## Where next

- [Tutorial: your first loop](docs/tutorial.md), step by step with pictures.
- [The six trees, explained](docs/the-trees.md) and [the loop, explained](docs/the-loop.md).
- [Use Claude or a local model](docs/use-a-model.md) and [back up, share and move goals](docs/back-up-and-share.md).
- [Workspace reference](docs/tui.md): keys, views, commands and settings.
- [All documentation](docs/README.md), including using Reason Commons from an AI agent.
- Questions or ideas: [open an issue](https://github.com/life-itself/reason-commons-tui/issues).

## Status

This is an early prototype for personal use. The loop works end to end, and the
six trees grow in the conversation. Joint causes, group work and an accessible
plain-text mode are planned.

[Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)
