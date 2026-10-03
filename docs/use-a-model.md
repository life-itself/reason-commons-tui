# Use Claude or a local model

The built-in guide asks the loop's questions in a fixed order and keeps your exact
words. It works offline and never gives advice. An AI consultant adapts its
questions, notices what is missing and can give direct advice through **Other
moves**. Your case keeps going from where it is when you switch.

## Use Claude

1. Get an API key from the [Anthropic Console](https://console.anthropic.com/).
2. Make it available to Reason Commons. On a Mac, add this line to `~/.zshrc` and
   open a new Terminal window:

   ```sh
   export ANTHROPIC_API_KEY='sk-ant-...'
   ```

3. Start `reason-commons`, open a goal, press **Ctrl+P** and choose
   **Consultant: Anthropic Claude**.

To make Claude the default, also add `export REASON_COMMONS_PROVIDER=anthropic`.
To use a different Claude model, set `REASON_COMMONS_ANTHROPIC_MODEL`.

When Claude is selected and you press **Send** (or choose a move marked "asks
consultant"), your answer and the goal's saved records are sent to Anthropic.
Browsing views, **Explain this** and help never send anything.

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
should lead to, what stands in the way or what you plan to do. It records each
statement in the right tree, in your words, and links it to what is already
there. Ask it to reword or drop a statement and the tree changes; the earlier
wording stays in **History**.

Press **Ctrl+T** to see the trees and **Ctrl+N** to step through them. The
[workspace reference](tui.md#the-trees) explains how to read them. The built-in
guide does not add to the trees; it only walks the loop.

## When the consultant can't be reached

Your answer is saved anyway. A **Retry** button appears; press it once the
consultant is reachable again, or after switching to another one with **Ctrl+P**.
