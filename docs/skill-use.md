# Reason Commons conversations

The skill is a conversational commons interface. A coding agent (Claude Code or
Codex) presents the saved question, context, uncertainty, forecast comparisons and
recorded diagrams, and accepts participant replies in ordinary language. The
application owns the reasoning, attribution, exact targets and persistence. The
chosen consultant (a local model, Anthropic, or the coding agent itself; see
[choosing a consultant](providers.md)) supplies semantic consultation only after an
explicit contribution or consultant move.

The skill and the TUI work on the same commons folders. Point the MCP server at
`~/ReasonCommons`, the folder the TUI's home screen lists, and a goal can be
continued in either.

## Use it in Claude Code without a key

With the host consultant, Claude Code itself drafts each consultant reply on your
subscription, and Reason Commons checks it as it checks any provider's.

The easiest way is the plugin in this repository. With
[uv](https://docs.astral.sh/uv/) installed:

```sh
claude plugin marketplace add life-itself/reason-commons-tui
claude plugin install reason-commons@reason-commons --scope user
```

The plugin brings the skill (shown as `reason-commons:reason-commons-contribute`)
and starts the server with `uvx` straight from this repository's main branch, with
`--provider host`. Its goals go to `REASON_COMMONS_HOME`, otherwise `~/ReasonCommons`,
the folder the workspace uses. The first start builds Reason Commons, about
20 seconds; if the tools are reported missing, `/mcp` reconnects. `claude plugin
update reason-commons@reason-commons` picks up a newer plugin. The plugin's tools are
named `mcp__plugin_reason-commons_reason-commons__…`.

Without the plugin, set it up by hand once:

1. Install Reason Commons with the MCP extra (it needs Python 3.10 or later, which
   uv provides):

   ```sh
   uv tool install 'reason-commons[mcp] @ git+https://github.com/life-itself/reason-commons-tui'
   ```

   In a clone, `.venv/bin/python -m pip install -e '.[mcp]'` does the same.

2. Register the server for your user, with the host consultant:

   ```sh
   mkdir -p ~/ReasonCommons
   claude mcp add --scope user reason-commons -- "$(command -v reason-commons)" mcp --commons-root ~/ReasonCommons --provider host
   ```

3. Make the skill discoverable. In this repository, `.claude/skills/reason-commons-contribute`
   already links it. To use it from any folder, link it for your user:

   ```sh
   git clone https://github.com/life-itself/reason-commons-tui ~/reason-commons-tui
   mkdir -p ~/.claude/skills
   ln -s ~/reason-commons-tui/skills/reason-commons-contribute ~/.claude/skills/reason-commons-contribute
   ```

   An older `reason-commons` skill that keeps a single `reason-commons.yaml` file
   is a different format. If you have both, name this one when you start:

> Use the reason-commons-contribute skill. I'm David. Open my-goal.

A consultation on a large commons is 150,000–200,000 characters. Claude Code saves
any MCP result over 50,000 characters to a file, so the server declares a larger
size for `consultation` (`anthropic/maxResultSizeChars`, 500,000) and it arrives
whole; no client setting is needed. Other large reads, such as a long backlog, may
still be saved to a file, which the agent reads from there.

`claude mcp list` shows whether the server is connected; `reason-commons providers
--provider host` confirms the host consultant needs no key. The server offers
`consultation` and `propose` instead of `consult`, `submit` and `retry`. For each
contribution you authorize, the skill retains your words, reads the consultation,
writes one proposal from that alone and hands it over with `propose`. What it
proposes waits for your decision like any consultant's, and the skill never
accepts on your behalf. The application records the consultant as the agent and
model the agent declared and cannot verify them; consulting quality with a host
model has not been evaluated, and every turn uses your subscription allowance (see
[the host consultant](providers.md#your-coding-agent-as-the-consultant-host)).

Bringing trees in from an `.ltp.yaml` file, or writing them out, goes through the
command line, because the MCP tools take no file paths. Ask for it and name the
file; the skill runs `reason-commons trees ~/ReasonCommons/my-goal --import FILE`
(the trees arrive as proposals waiting in the backlog) or `--export NEW_FILE`.

### What the skill reaches, and what it leaves to the TUI

Every TUI command and view that reads or changes a commons is reachable from the
skill: sending an answer and the other consultant moves (another question, direct
advice, explaining an observation, asking about open reviews), retry, explaining
the question, all ten views and any earlier revision, accepting (including "accept
all" and adopting an import), rejecting, undoing, "still holds", exporting the
commons, creating a goal, and importing or exporting trees through the command
line. Changing the acceptance setting stays behind the operator's
`--allow-acceptance-setting`.

Left out on purpose, because they change no reasoning: focus, folding, keyboard
navigation, display density, theme, help, the saved draft and caret, and "answer
about the chosen statement", which only fills in a draft. Choosing a consultant,
and deeper reasoning for one reply, are made when the server starts, not by the
agent. The cost screen reads the local usage log, which the host consultant does
not write to.

## Use it on this machine

Start a fresh Codex chat in this repository to load the updated MCP tool catalog.
If tools are missing, restart the app. Invoke:

> Use $reason-commons-contribute on commons my-case as David. Resume our conversation.

This reads the existing commons and presents its saved question. It does not resubmit
your earlier contribution. Answer the question in your own words. You can also ask:

- “Explain why you're asking that.” — shows the saved rationale locally.
- “Show the goal and safeguards.” — inspects saved formulations and unknowns.
- “Show our reasoning as a diagram.” — draws recorded connections, when present.
- “Compare the forecast with what happened.” — shows original forecasts alongside
  observations, their scope and basis, safeguards and saved reviews.
- “Show who said that.” or “Show the earlier version.” — reads sources or history.
- “Ask me another question” or “Give me direct advice about this.” — deliberately
  consults with the chosen intent and participant-supplied text.
- “What is waiting for me?” — shows the backlog: what replies proposed and what is
  flagged for review, in the order it is best decided.
- “Accept the cause and its link.” or “Reject that.” — records your own decision on
  exactly the proposals you name. When it would take more (what they need, what needs
  them), Codex shows the whole list and waits for you before confirming.

A reply's updates are proposals: they wait for your decision and are not in your
model until you accept them. The skill never accepts on your behalf and never turns
on automatic acceptance; the MCP server refuses that unless you start it with
`--allow-acceptance-setting`.

The skill remembers the active commons, declared participant and displayed question
through the chat. A reply keeps that exact target; if another contribution
advances the commons, the new question is shown before reconsidering the reply.
Reopening reads the durable commons rather than relying on hidden model memory.
Input is literal, attributed and retained before inference. It is never an
instruction to edit commons files. Failures display actual save status and retained
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
model connection and does not change commons state.

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
With Anthropic the default model is `claude-haiku-5-5`; `--model claude-sonnet-5-5` sends
that one contribution (or `retry`) to Sonnet for deeper reasoning, at about twelve times
the cost. Each call is counted in the local usage log, never in the commons;
`reason-commons usage` sums it, and once this month reaches 80% of a budget
(`REASON_COMMONS_MONTHLY_BUDGET_USD`) the command says so in one line on stderr, with its
output and exit code unchanged (see [what it costs](providers.md#what-it-costs)).

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
All commons tools take a direct folder name under the configured root; portable
exports go into its reserved `exports` directory.

Diagrams show **explicit saved record references**, such as a test's goal, an
action's test or a review's observations. Edge labels preserve those meanings.
Original wording and forecast/result details accompany them. The `trees` view
draws the six thinking-process trees from the accepted tree statements and links,
and a consultant proposes additions when a reply describes causes, conflicts,
obstacles or plans; the renderer never manufactures them from notes, and the
`backlog` view lists what waits. Joint causes and rival
explanations remain later work. The TUI is described in [tui.md](tui.md); the
semantic and participant evaluations are separate from v1 scope. The shared
capability surface covers application semantics even when the default sidebar
hides a supporting view; this contribution skill uses a deliberate subset.

## Installation and configuration

The repository's `.agents/skills/reason-commons-contribute` symlink discovers the
single packaged skill. This machine uses `.venv` with Python 3.12 and the existing
project `.codex/config.toml` connection `reason-commons`, configured for
`google/gemma-4-e4b`, a 300-second tool timeout and commons root:

`/Users/davidjoseph/github/reason-commons-cli/.reason-commons/cases`

For another machine, the engine and CLI need Python 3.9+; the optional official
MCP SDK needs Python 3.10+:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[test,mcp]'
mkdir -p .reason-commons/cases
.venv/bin/reason-commons new --store .reason-commons/cases/my-case --name 'My commons'
```

Register a connection to `/absolute/path/to/.venv/bin/python -m reason_commons mcp
--commons-root /absolute/path/to/commons --provider PROVIDER [--model YOUR_MODEL_ID]`.

The older `--case-root` option remains an alias. Existing tool arguments such as
`case` and saved `.reasoncase` files continue to identify the same commons.
Preserve existing connections for other projects. Provider, model, endpoint,
timeout and credentials are settings outside commons state, and the credential must
reach the server process (for Anthropic, add `ANTHROPIC_API_KEY` to `env_vars`).
See [choosing a consultant](providers.md) for a complete example and for
[LM Studio configuration](lm-studio.md). The tools take no model, so an agent cannot
choose a dearer one; with Anthropic, from 80% of a monthly budget the results of
`consult`, `submit` and `retry` carry a `usage_notice` for the person, and nothing is
blocked.

Codex registration follows the official [MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
and [skill discovery](https://learn.chatgpt.com/docs/build-skills) documentation.
The transport uses the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).
