# Reason Commons conversations

The skill is a conversational case interface. Codex presents the saved question,
context, uncertainty, forecast comparisons and recorded diagrams, and accepts
participant replies in ordinary language. The application owns the reasoning,
attribution, exact targets and persistence. The chosen consultant, a local model
or Anthropic (see [choosing a consultant](providers.md)), supplies semantic
consultation only after an explicit contribution or consultant move.

## Use it on this machine

Start a fresh Codex chat in this repository to load the updated MCP tool catalog.
If tools are missing, restart the app. Invoke:

> Use $reason-commons-contribute on case my-case as David. Resume our conversation.

This reads the existing case and presents its saved question. It does not resubmit
your earlier contribution. Answer the question in your own words. You can also ask:

- “Explain why you're asking that.” — shows the saved rationale locally.
- “Show the goal and safeguards.” — inspects saved formulations and unknowns.
- “Show our reasoning as a diagram.” — draws recorded connections, when present.
- “Compare the forecast with what happened.” — shows original forecasts alongside
  observations, their scope and basis, safeguards and saved reviews.
- “Show who said that.” or “Show the earlier version.” — reads sources or history.
- “Ask me another question” or “Give me direct advice about this.” — deliberately
  consults with the chosen intent and participant-supplied text.

The skill remembers the active case, declared participant and displayed question
through the chat. A reply keeps that exact target; if another contribution
advances the case, the new question is shown before reconsidering the reply.
Reopening reads the durable case rather than relying on hidden model memory.
Input is literal, attributed and retained before inference. It is never an
instruction to edit case files. Failures display actual save status and retained
input; retry needs an explicit request and preserves the original identity.

Your existing `my-case` has revision 1, your contribution and the saved question
about measurable delivery reliability and protected conditions. It currently
has a reported note and a question, with no formal goal or recorded connections.
The diagram view therefore explains that there is nothing connected to draw yet.

## Local CLI

The same workspace is available offline:

```sh
.venv/bin/reason-commons show .reason-commons/cases/my-case
.venv/bin/reason-commons show .reason-commons/cases/my-case --view explain
.venv/bin/reason-commons show .reason-commons/cases/my-case --view reasoning --format markdown
.venv/bin/reason-commons show .reason-commons/cases/my-case --view sources
.venv/bin/reason-commons show .reason-commons/cases/my-case --view history
```

Views are `next`, `explain`, `goal`, `trees`, `reasoning`, `tests`, `actions`,
`history` and `sources`. `--revision N` freezes an earlier published revision. `--select REF`
opens an exact saved item and its referenced context. `--format json` returns
presentation data and text/Markdown/Mermaid renderings. Inspection requires no
model connection and does not change case state.

For a deliberate contribution, name the provider (or set `REASON_COMMONS_PROVIDER`):

```sh
# Anthropic, with ANTHROPIC_API_KEY exported
.venv/bin/reason-commons contribute .reason-commons/cases/my-case \
  --speaker David --provider anthropic \
  --text-file /absolute/path/to/my-reply.txt

# A local model through LM Studio
.venv/bin/reason-commons contribute .reason-commons/cases/my-case \
  --speaker David --provider lm-studio --model google/gemma-4-e4b \
  --text-file /absolute/path/to/my-reply.txt
```

Run `reason-commons providers` first to confirm the settings without sending anything.

Use `--text-file -` for standard input. Default output presents the saved question
and workspace; `--format markdown` includes diagrams and tables. `--json` exposes
the authoritative result, procedure completion, agent reply and capability trace.
Exit zero requires a completed procedure and a saved application result.

For a reply to a question displayed earlier, supply both `--base-revision N` and
`--response-target REF` from that workspace's `target` (`none` when absent).
`--intent direct_advice`, `another_question` or `explain_observation` deliberately
selects a consultant alternative. `--ownership NAME` and `--observed` express
actual participant declarations, never guesses from prose.

The default `--runner procedure` executes the bounded inspect → retain → consult
sequence with either provider. `--runner agent` lets the configured model execute
the packaged skill through the same host. It is experimental and currently needs
`lm-studio` (it is rejected before anything is retained with Anthropic); a model
changing literal input or the bound target is rejected. There is no automatic fallback or semantic retry.

```sh
.venv/bin/reason-commons receipts .reason-commons/cases/my-case REQUEST_ID
.venv/bin/reason-commons retry .reason-commons/cases/my-case REQUEST_ID \
  --provider lm-studio --model google/gemma-4-e4b
```

Use the actual retained identity. Retry with the provider you want to consult; it
need not be the one that failed. Already applied requests return the saved state
without consulting again. An unavailable model, invalid proposal or unconfirmed
save remains a failure. A stale reply requires deliberate re-evaluation against
current context.

## Shared presentation boundary

`CaseCapabilities.workspace(view, revision, selection)` captures a published
snapshot once and derives question, context, exact references, unknowns, original
forecast comparisons, attribution and available actions. Local and consultant
routes are explicit. Historical views expose only local moves and a return to
live state. Layout and Markdown/Mermaid formatting live in adapters.

The MCP `workspace` tool and CLI `show` use identical renderings. `consult`,
`submit` and `retry` return a receipt plus the newly read workspace, so clients
can present the next turn without inventing a question or interpreting an agent's
success claim. Each MCP call closes its session; idle clients hold no writer lock.
All case tools take a direct folder name under the configured root; portable
exports go into its reserved `exports` directory.

Diagrams show **explicit saved record references**, such as a test's goal, an
action's test or a review's observations. Edge labels preserve those meanings.
Original wording and forecast/result details accompany them. The `trees` view
draws the six thinking-process trees from recorded tree statements and links, and
a consultant adds to them when a reply describes causes, conflicts, obstacles or
plans; the renderer never manufactures them from notes. Joint causes and rival
explanations remain later work. The TUI is described in [tui.md](tui.md); the
remaining p1/p2 release gates are separate work. This
change delivers the conversation interface for the implemented case semantics.

## Installation and configuration

The repository's `.agents/skills/reason-commons-contribute` symlink discovers the
single packaged skill. This machine uses `.venv` with Python 3.12 and the existing
project `.codex/config.toml` connection `reason-commons`, configured for
`google/gemma-4-e4b`, a 300-second tool timeout and case root:

`/Users/davidjoseph/github/reason-commons-cli/.reason-commons/cases`

For another machine, the engine and CLI need Python 3.9+; the optional official
MCP SDK needs Python 3.10+:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[test,mcp]'
mkdir -p .reason-commons/cases
.venv/bin/reason-commons new --store .reason-commons/cases/my-case --name 'My case'
```

Register a connection to `/absolute/path/to/.venv/bin/python -m reason_commons mcp
--case-root /absolute/path/to/cases --provider PROVIDER [--model YOUR_MODEL_ID]`.
Preserve existing connections for other projects. Provider, model, endpoint,
timeout and credentials are settings outside case state, and the credential must
reach the server process (for Anthropic, add `ANTHROPIC_API_KEY` to `env_vars`).
See [choosing a consultant](providers.md) for a complete example and for
[LM Studio configuration](lm-studio.md).

Codex registration follows the official [MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
and [skill discovery](https://learn.chatgpt.com/docs/build-skills) documentation.
The transport uses the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).
