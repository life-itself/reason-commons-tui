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

### Why look at the trees while you work

- **See the whole while you work on one part.** A question about a single test
  sits inside a goal, a cause and a plan. The trees keep that context one key away,
  so a small step never loses its reason.
- **Find the weak spot.** Every arrow shows the assumption it rests on, in grey
  under the statement. That is where to push back: "is that really why?"
- **Notice what is missing.** An obstacle with no objective, a cause nobody has
  explained, a tree with nothing in it: each is the next good question to ask.
- **Keep the reasoning, not just the chat.** Each statement keeps who said it and
  its earlier wordings, so the thinking builds up instead of scrolling away.

### How to see them

1. Run `reason-commons` and open a goal. To explore first, choose **Explore a real
   commons**: it carries the Second Renaissance analysis above, and how it grew.
2. Press **Ctrl+T**. The Trees view opens; the line at the top lists the six trees
   and how many statements each holds.
3. Press **Ctrl+N** to step to the next tree. After the sixth it shows all six
   together, then starts again.
4. Read each tree top down: a coloured label says what a statement is (ROOT CAUSE,
   OBSTACLE, ACTION), and the branch says how it relates to the one above
   ("because", "needs", "overcomes", "produced by").
5. Press **Ctrl+T** again to go back to the question you were answering.

![The Trees view showing the Current Reality Tree of the example: the symptom "the group is busy while durable-adoption throughput remains low" at the top, with root causes and further symptoms branching below it as "because" and "partly because", each with its assumption in grey](docs/images/trees-current-reality.png)

The trees grow from the conversation. With Claude or a local model as consultant,
tell it what causes a problem, which conflict keeps you stuck, what stands in the
way or what you plan to do. It records each statement in its tree, linked to the
others, in your own words. Ask it to reword or drop something and the tree changes,
while the earlier wording stays in the history. The built-in guide does not add to
the trees.

Trees you already have come in from an `.ltp.yaml` file, the format the Reason
Commons guide uses, and go out the same way: press **Ctrl+P** and choose **Import
trees** or **Export trees**. From the terminal, `reason-commons trees FOLDER` draws
them without opening the workspace. Add `--tree current_reality` to draw just one.

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

The first time, `reason-commons` offers to start your first goal straight away
with the offline guide. You can instead choose who asks the questions first, take
the guided tour or explore a real commons.

![The first screen offers four ways to start: start my first goal with the offline guide, choose who asks the questions first, take the guided tour, or explore a real commons](docs/images/first-start.png)

Choosing who asks takes about a minute: your name, then the offline guide, Claude
or a local model in LM Studio. For Claude you paste an API key; it
is checked and you choose from the models your key can use. Change any of it later
under **Settings** on the home screen. The guided tour walks one whole loop on a
practice goal, with example answers one button away; nothing from it is kept.

Contributors and agents: start with [how we develop](docs/development/README.md).
The [architecture](ARCHITECTURE.md) explains the domain/application/adapter
boundaries and how BDD and replaceable skills use the same application surface.
The [p0 implementation report](docs/p0-delivery.md) records the delivered slice.

**Explore a real commons** opens the Second Renaissance's shared reasoning
read-only, on the one action it says comes next. Step back with ← through every
saved step of how it grew since June 2026: who said what, when, in their own words,
and what changed in the trees. Ctrl+T shows all six trees.

![The real commons opens on its next action, with a strip for stepping back through how it got here](docs/images/story-now.png)

After that, `reason-commons` opens a list of your goals. Start a new one, or come
back to the real commons or the tour. A new goal opens with one question; you answer in
ordinary words, Enter adds a line and Ctrl+S sends. **Explain this** shows why the
question matters and how one loop works.

![The home screen lists goals with their current step, plus Start a new goal, the real commons and the guided tour](docs/images/home.png)

**Choosing a consultant.** Reading, history, export and import need no model. The
TUI starts with the offline built-in guide. To have a model propose questions,
choose a provider: a local model through LM Studio, or Anthropic. Either plugs
into the same application boundary and requests
structured proposals; application/domain validation stays authoritative.
[Choosing a consultant](docs/providers.md) explains how to set up each, how to
check the setup offline with `reason-commons providers`, and what to do when a
consultation fails. See also the [LM Studio setup](docs/lm-studio.md).
The [validation guide](docs/validation.md) runs repeatable live-model, real-agent
and recovery evaluations, with retained evidence and an attributed review rubric.

Everything is saved as you type, including an unsent draft. Quit with Ctrl+Q and
`reason-commons` takes you back to where you were.

## Where next

- [Tutorial: your first loop](docs/tutorial.md), step by step with pictures.
- [The six trees, explained](docs/the-trees.md) and [the loop, explained](docs/the-loop.md).
- [Use Claude or a local model](docs/use-a-model.md) to grow the trees as you talk, and [back up, share and move goals and trees](docs/back-up-and-share.md).
- [Workspace reference](docs/tui.md): keys, views, commands and settings.
- [All documentation](docs/README.md), including using Reason Commons from an AI agent.
- Questions or ideas: [open an issue](https://github.com/life-itself/reason-commons-tui/issues).

## Status

This is an early prototype for personal use. The loop works end to end, and the
six trees grow in the conversation. Joint causes, group work and an accessible
plain-text mode are planned.

[Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)
