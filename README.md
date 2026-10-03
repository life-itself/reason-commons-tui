# Reason Commons

**Make real progress on a goal that matters, one small, honest experiment at a time.**

Reason Commons is a calm workspace in your terminal. It helps you say what you
want, try one small change, write down what you expect *before* it happens, and
then look at what really happened. It works offline, and it keeps your own words.

![A goal in progress: the loop line shows Goal, Test and Action done and Observe as the current step; the workspace asks what actually happened](docs/images/in-progress.png)

## How it works

![The loop: 1 Goal, 2 Test + forecast, 3 Action, 4 Observe, 5 Review, then again](docs/images/loop.svg)

1. **Goal.** What would count as better, how you will notice, and what must not get worse.
2. **Test with a forecast.** One small change you can make yourself, plus what you
   expect to happen. The forecast is saved before any result exists and never changes.
3. **Action.** The concrete next thing you will do, and when.
4. **Observe.** What actually happened, kept apart from what you hoped.
5. **Review.** The result next to your forecast. Keep the change, adjust it or drop
   it, then start the next loop from what you learned.

A built-in guide asks these questions one at a time. If you like, Claude or a local
model can take its place and give advice as well.

## Is this for you?

It suits any goal where you are not sure what will work, for example:

- **Personal:** "Be in bed by 23:00 four nights a week without losing evenings with my partner."
- **Work:** "Cut the time our changes wait for release, without more rollbacks."
- **Team or community:** "Get more neighbours to the monthly meeting without burning out the organisers."

After one loop you have a written goal and safeguards. You also have a test whose
forecast you can't quietly rewrite, an honest record of what happened, and a decision
you can explain. All of it is in a plain folder you own.

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

## What a session looks like

**Your goals.** `reason-commons` opens a list of your goals. You can pick one, start a
new one, or look around a finished example first.

![The home screen lists goals with their current step, plus Start a new goal and a finished example](docs/images/home.png)

**The first question.** A new goal opens with a short welcome and one question. You
answer in ordinary words. Enter adds a line and Ctrl+S sends.

![The welcome screen asks what you want to achieve and draws the loop](docs/images/welcome.png)

**Forecast next to result.** Under **Tests**, what you expected sits beside what
happened. This is where the learning is.

![The Tests view shows the original forecast, 4 of 7 nights, next to the reported result, 5 of 7 nights](docs/images/forecast-vs-result.png)

Everything is saved as you type, including an unsent draft. Quit with Ctrl+Q and
`reason-commons` takes you back to where you were.

## Where next

- [Using the workspace](docs/tui.md): keys, views, consultants, where your data lives.
- [Use a local model with LM Studio](docs/lm-studio.md).
- [Use Reason Commons from an AI agent](docs/skill-use.md).
- Questions or ideas: [open an issue](https://github.com/life-itself/reason-commons-tui/issues).

## Status

This is an early prototype for personal use. The loop above works end to end. Group
work, richer reasoning maps and an accessible plain-text mode are planned.

[Contributing](CONTRIBUTING.md) · [MIT License](LICENSE)
