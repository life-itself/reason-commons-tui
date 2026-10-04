# Choosing a consultant

Reason Commons keeps your reasoning in a durable case. A **consultant** is the
language model that proposes the next question or recommendation from that case.
The consultant is a replaceable choice, made outside the case. Two are supported:

| | LM Studio (local) | Anthropic |
|---|---|---|
| Where it runs | A server on your machine or network | Anthropic's hosted API |
| What you need | LM Studio with a chat model loaded | An Anthropic API key |
| Cost | None beyond your hardware | Billed to your API key |
| Case content leaves your machine | No (unless you point it at a remote server) | Yes, to Anthropic |
| Provider name | `lm-studio` | `anthropic` |

Every consultation sends the **complete** case and its sources; nothing is
truncated or summarised on the way. Neither provider is a fallback for the other.
If the chosen consultant fails, your words are kept and nothing else is tried.

Reading, searching, history, export and import never need a consultant or a key.

## Quick start

Pick one. The `providers` command then confirms what will be used, without
sending anything.

**Anthropic**

```sh
export ANTHROPIC_API_KEY='...'          # from your Anthropic Console; keep it out of files and flags
export REASON_COMMONS_PROVIDER=anthropic
reason-commons providers
```

**LM Studio**

```sh
# In LM Studio: start the local server and load a chat model, then:
export REASON_COMMONS_PROVIDER=lm-studio   # optional: this is the default
export REASON_COMMONS_LM_STUDIO_MODEL='your-served-model-id'
reason-commons providers
```

Then contribute as usual:

```sh
reason-commons contribute /path/to/my-case --speaker David --text 'Our deliveries keep slipping.'
```

## How a provider is chosen

The first of these that is set wins:

1. **An explicit choice**: `--provider anthropic` or `--provider lm-studio` on
   `contribute`, `retry`, `mcp` or `providers`.
2. **The environment**: `REASON_COMMONS_PROVIDER`.
3. **The default**: `lm-studio`.

In the environment, the name is not case-sensitive and a blank value counts as not
set. The flag accepts only the exact names. An unknown name is rejected with the
valid choices. `--model` and `--base-url` follow the same
order over the provider's own environment variables and defaults.

## Settings

Settings live in the process environment of whatever starts `reason-commons`. They
are never written into a case or an export.

| Setting | Anthropic | LM Studio |
|---|---|---|
| Credential | `ANTHROPIC_API_KEY` (required) | `LM_STUDIO_API_TOKEN` (optional, only if your server requires one) |
| Model | `REASON_COMMONS_ANTHROPIC_MODEL`, default `claude-sonnet-5-5` | `REASON_COMMONS_LM_STUDIO_MODEL`; if unset, used automatically only when the server advertises exactly one model |
| Server URL | `REASON_COMMONS_ANTHROPIC_URL`, default `https://api.anthropic.com/v1` (HTTPS only; plain HTTP just for loopback testing) | `REASON_COMMONS_LM_STUDIO_URL`, default `http://127.0.0.1:1234/v1` |
| Timeout (seconds) | `REASON_COMMONS_ANTHROPIC_TIMEOUT`, default 120 | `REASON_COMMONS_LM_STUDIO_TIMEOUT`, default 120 |

Use a model ID the server actually serves. Both adapters check the model first,
and require each answer to come from that same model, so a server cannot quietly
answer with a different one. Details for the local server are in
[Using LM Studio](lm-studio.md).

## Check your setup

```sh
reason-commons providers                      # the provider the environment selects
reason-commons providers --provider anthropic # or inspect one explicitly
reason-commons providers --json
```

```
Provider: anthropic (chosen by REASON_COMMONS_PROVIDER)
Model: claude-sonnet-5-5 (default)
Endpoint: https://api.anthropic.com/v1
Credential: ANTHROPIC_API_KEY not set (required)
Status: not ready
  - ANTHROPIC_API_KEY is not set; export it in the environment that starts reason-commons
Other providers: lm-studio
```

This reads configuration only. It names the credential variable and never prints
its value. The exit status is 0 when ready and 1 when not, so scripts can rely on
it. "Ready" means the settings are complete; it does not prove the server is
reachable or the key is accepted. For that, use a live check:

```sh
python3 scripts/check_anthropic.py                     # confirms the key can see the model; no inference
python3 scripts/check_anthropic.py --case /path/to/my-case      # also counts the pending prompt's tokens; no inference
python3 scripts/check_anthropic.py --smoke             # one billed synthetic consultation in a throwaway case
python3 examples/lm_studio_smoke.py --store /tmp/reason-lm-check --model your-served-model-id
```

## Switching on an existing case

Reopen the same case with a different provider whenever you like. Committed
records, forecasts and history do not change. Each applied request records which
consultant produced it, so `inspect` shows, for example, `in000001` answered by
`anthropic/...` and `in000002` by `lm-studio/...`. A response that was received
but not yet committed is recovered from the case and keeps its original
consultant; to get a different consultant's view, submit a new contribution
against the current question rather than overwriting an earlier forecast.

## When a consultation fails

Your words are always saved first, so a failure never loses them. The result says
`unavailable` and carries a category, plus the HTTP status when there is one. The
provider's own message and response body are never stored or shown, because they
can contain secrets. Read the stored receipt with
`reason-commons receipts /path/to/my-case REQUEST_ID`.

| Category | Meaning | What to check |
|---|---|---|
| `configuration` | A setting is missing, such as no API key | Run `reason-commons providers` |
| `http_error` | The server answered with an error status | The credential and model access (401/403), the model ID (404), rate limits (429) |
| `timeout` | No answer within the timeout | Allow more time, or check provider load |
| `connection` | The server could not be reached | That it is running, and that the address and network are right |
| `unknown` | Any other failure | Run `reason-commons providers`, then the provider's own logs |

Retry only when you decide to: `reason-commons retry /path/to/my-case REQUEST_ID`. A response
the application rejects (malformed, out of profile) is reported as `rejected`,
not `unavailable`, and also never publishes anything.

## Using a provider from the skill (MCP)

The skill and MCP server read the same settings. Name the provider on the server
command or in the environment, and make sure the **key reaches that process**.
Apps launched from a desktop icon often do not inherit variables from your shell.

```toml
# .codex/config.toml
[mcp_servers.reason-commons]
command = "/absolute/path/to/.venv/bin/python"
args = ["-m", "reason_commons", "mcp", "--case-root", "/absolute/path/to/cases", "--provider", "anthropic"]
env_vars = ["ANTHROPIC_API_KEY"]
```

`scripts/run_mcp.zsh` is an alternative command: if `ANTHROPIC_API_KEY` is not
already set, it reads your `~/.zshrc` for it, so the key stays out of the config
file. After changing a provider, restart the client so it starts a new server.

## Limits

- The experimental `--runner agent` currently needs `lm-studio`. With Anthropic
  it is rejected before anything is retained; use the default `--runner procedure`,
  or the Codex skill.
- Automated tests exercise both adapters against local fake servers and the
  provider-free application scenarios. They show the integration behaves as
  designed. They do not establish the quality of any live model's consulting;
  see [validation](validation.md).
- A case larger than the provider accepts fails with a size or context error.
  Nothing is cut down to fit.
