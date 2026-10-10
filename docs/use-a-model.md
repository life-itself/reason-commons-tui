# Use Claude or a local model

The built-in guide asks the loop's questions in a fixed order and keeps your exact
words. It works offline and never gives advice. An AI consultant adapts its
questions, notices what is missing and can give direct advice through **Other
moves**. Your commons keeps going from where it is when you switch.

## The easy way: setup

On the first start, choose **Choose who asks the questions first**; later, choose
**Settings** on the home screen. Pick Claude or LM Studio:

- **Claude**: paste your API key from the
  [Anthropic Console](https://console.anthropic.com/). Reason Commons checks it and
  lists the models your key can use. Haiku 5.5 is marked as recommended: it costs
  least and suits most replies. Sonnet reasons more deeply and costs more per reply.
- **LM Studio**: the usual address is filled in. Reason Commons finds the server
  and lists the loaded models. If nothing answers, it says what to do in LM Studio.

![Choosing a Claude model: Opus, Sonnet, Haiku 5.5 (recommended) and Haiku 4.5, each with its trade-off](images/setup-model.png)

Your choices are saved in `~/.config/reason-commons/settings.yaml`, readable only
by you, and never in a goal or an export. Environment variables, described below,
still take precedence, so an existing shell setup keeps working.

## Use Claude with environment variables

1. Get an API key from the [Anthropic Console](https://console.anthropic.com/).
2. Make it available to Reason Commons. On a Mac, add this line to `~/.zshrc` and
   open a new Terminal window:

   ```sh
   export ANTHROPIC_API_KEY='sk-ant-...'
   ```

3. Start `reason-commons`, open a goal, press **Ctrl+P** and choose
   **Consultant: Anthropic Claude**.

To make Claude the default, also add `export REASON_COMMONS_PROVIDER=anthropic`.
Claude Haiku 5.5 answers unless you chose another model; to use a different one,
set `REASON_COMMONS_ANTHROPIC_MODEL`.

When Claude is selected and you press **Send** (or choose a move marked "asks
consultant"), your answer and the goal's saved records are sent to Anthropic.
Browsing views, **Explain this** and help never send anything.

## What Claude costs

Claude is paid per reply: about $0.004 with Haiku 5.5. For a question that needs more,
**Ctrl+P**, **Send with deeper reasoning (Sonnet 5.5)** sends that one answer to Claude
Sonnet, which reasons more deeply for about $0.05; the next Send goes to Haiku again.
The footer estimates what this session and this month cost, each reply's notice says
what it cost, and **Ctrl+P**, **Consultant calls and cost** has the details. F2
**Settings**, **Budget** sets a soft monthly budget: you are told at 80% and 100%, and
past it each send asks first. Nothing is ever blocked. The amounts are estimates at list
prices; your bill is in the [Anthropic Console](https://console.anthropic.com/).
`reason-commons usage` prints the same from the command line. More in
[what it costs](providers.md#what-it-costs).

## Use a local model with LM Studio

Nothing leaves your computer with a local model.

1. In [LM Studio](https://lmstudio.ai/), load a chat model and start the local
   server (Developer tab). The usual address is `http://127.0.0.1:1234/v1`.
2. If more than one model is loaded, name the one to use:
   `export REASON_COMMONS_LM_STUDIO_MODEL='<model id>'`.
3. In Reason Commons, press **Ctrl+P** and choose **Consultant: LM Studio (local)**.

The [LM Studio notes](lm-studio.md) cover other addresses, tokens and how model
choice is verified.

## Grow the trees as you talk

With Claude or LM Studio as consultant, the six trees grow from the conversation.
Tell it what causes a problem, which conflict keeps you stuck, what a change
should lead to, what stands in the way or what you plan to do. It proposes each
statement for the right tree, in your words, linked to what is already there. Ask it
to reword or drop a statement and it proposes that; once you accept, the tree
changes and the earlier wording stays in **History**.

After each reply, the next question draws what it proposes, marked NEW, beside the
words it came from. Check it there, while you still know what you meant. **Accept all**
puts it in your trees; **Backlog** decides one entry at a time; if the reading is wrong,
reject it or say so in your answer. When you accept a new wording, the links and tests
that cite the old one are flagged for review in Backlog, and **Ask about the open
reviews** (Ctrl+P) asks the consultant whether they still hold. The
[workspace reference](tui.md#deciding-what-enters-your-model) explains deciding, undo and
automatic acceptance. Press **Ctrl+T** to see the whole tree, **Ctrl+N** to step through
the trees, **↑**/**↓** to choose a statement and check the words it came from, and
**a** to begin an answer about the chosen statement. The
[workspace reference](tui.md#the-trees) explains how to read them. The built-in
guide does not propose tree statements; it only walks the loop.

## When the consultant can't be reached

Your answer is saved anyway. A **Retry** button appears; press it once the
consultant is reachable again, or after switching to another one with **Ctrl+P**.
