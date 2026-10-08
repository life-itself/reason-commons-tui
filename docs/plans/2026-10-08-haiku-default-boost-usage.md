# Plan: Haiku 5.5 by default, a one-reply Sonnet boost, and a usage/cost meter with a soft budget

> Status: in progress on `claude/haiku-default-sonnet-boost-15ad85`: steps 1–5 done; 6–7 planned. Written 2026-10-08 on `claude/relaxed-rubin-9mij55` after the Haiku 5.5
> evaluation recorded in `docs/validation.md` ("Claude Haiku 5.5 as the consultant"). Line numbers are as of that
> branch and will drift; search for the named functions.


## Context

Today's billed runs (branch `claude/relaxed-rubin-9mij55`, recorded in `docs/validation.md`) showed that the Anthropic
adapter (adapter 4: 16K tokens, effort high, transport repairs) makes Haiku 5.5 a workable consultant:
- **Validity:** 70 of 72 semantic replies and 42 of 42 procedure replies saved first time.
- **Cost and speed:** ≈ $0.004 a reply against Sonnet's ≈ $0.05, but ≈ 22 s against 11 s.
- **Quality (blind AI pre-screen):** Haiku 150 pass / 8 fail / 4 can't judge; Sonnet 70 / 2 / 9.
- **Haiku's weak spots:** classifying review outcomes, and the Evaporating Cloud layout.

The user wants:
1. Haiku 5.5 as the default.
2. A way to boost one reply to Sonnet 5.5.
3. An in-app meter, following best practices, so people see what their use costs.

Decided with the user:
- **Boost:** one reply, then back to Haiku. Manual only; no automatic escalation, since `docs/providers.md` says no provider is a fallback.
- **Budget:** a soft monthly budget. Warn at 80% and 100%. Past 100%, each send asks once. Never block, and always keep the participant's words.
- **Coverage:** meter every entry point (workspace, accessible, CLI `contribute`/`retry`, MCP) into one local log, and add a `reason-commons usage` command.

**Constraints**
- **Nothing in the case.** Usage and cost must never enter a case: everything in `attempts/` is exported in `.reasoncase` (`filesystem.py:393-421`).
- **Application untouched.** The application layer and `CaseCapabilities` don't change; the parity test stays green.
- **Type checks kept.** `configured_consultant()` must keep returning the bare adapter types (`test_anthropic.py:197`, `provider_steps.py:84,102`, `cli.py:235`).
- **Product spec unchanged.** No edits to the `.feature` files in `reason-commons-spec/`. New scenarios go in `tests/conversation/features/providers.feature`, which we own.
- **Header unchanged.** TUI-DESIGN.md limits the header to name, who you are and saved state, so the meter lives in the footer summary slot, the reply toast and a screen.

## Steps (one commit each; gate after each)

### 1. Record the Haiku pre-screen — done (2026-10-08)
The blind AI pre-screen of `semantic-haiku55-adapter4` (150 pass, 8 fail, 4 can't judge) is recorded in
`docs/validation.md`, with its failure patterns (review classification, the Cloud layout, the fixtures' dates).

### 2. Haiku 5.5 is the default — done (2026-10-08)
- **Default model.** `adapters/anthropic.py:27` `DEFAULT_MODEL = "claude-haiku-5-5"`.
- **Onboarding.**
  - `adapters/onboarding.py:260`: recommend `DEFAULT_MODEL` if listed, else Sonnet, else the first model. Never "any haiku": Haiku 4.5 is unvalidated and costs $1 / $5.
  - Text at `:266-267`: "Haiku 5.5 costs least and suits most replies; in a goal you can send any one question to Sonnet for deeper reasoning."
- **Hints.** `adapters/settings.py:132-143` `model_hint`:
  - Haiku: "lowest cost; quick, lighter reasoning".
  - Sonnet: "deeper reasoning; costs more per reply".
- **Existing users.** A saved `anthropic.model` such as Sonnet is an explicit choice and stays (`Settings.apply`). The usage screen mentions the new default once.
- **Docs.** `docs/providers.md:85,112`, `docs/tui.md:447`, `docs/use-a-model.md:15,19`, `evaluations/live-claude-test-prompt.md:41`.
- **Screenshots.** In `scripts/render_screenshots.py:322-323`, add Haiku 5.5 to the fake model list and re-render `setup-model`.
- **Tests.**
  - `tests/test_onboarding.py:66-69,128-144`: Haiku 5.5 highlighted; with only Haiku 4.5 listed, Sonnet is highlighted.
  - `test_anthropic.py`: the default is pinned by literal.
  - New `providers.feature` scenario: "Claude Haiku 5.5 consults when no Claude model is chosen".

### 3. Pricing, usage log, adapter sink, wiring (no UI) — done (2026-10-08)
**`adapters/pricing.py`** (new, pure, `Decimal`)
- An as-of date and source URL.
- Prices per MTok, as (input, output, 5-min cache write, 1-h cache write, cache read):

  | Model | Prompt length | Prices |
  |---|---|---|
  | `claude-haiku-5-5` | up to 100K tokens | 0.10, 0.50, 0.125, 0.20, 0.01 |
  | `claude-haiku-5-5` | over 100K tokens | 0.50, 2.50, 0.625, 1.00, 0.05 |
  | `claude-sonnet-5-5` | any | 2, 10, 2.50, 4, 0.10 |

  Checked against the live pricing page on 2026-10-08: it gives Sonnet 5.5's cache reads as $0.10 (0.05× input),
  not the $0.20 first written here; every other figure matched. The table also prices Opus 5.5 and Haiku 4.5,
  which setup lists.

- The rate card is chosen by prompt size: input plus cache tokens. It prices the whole request.
- Functions: `cost(model, tokens, overrides) -> Decimal|None` (None for an unknown model), `label()` ("Haiku 5.5"), `money()`, and `ratio()` for the boost's cost wording.
- Overrides come from settings `usage.prices.<model>`.
- Verify the prices against the live Anthropic pricing page (WebFetch) before committing.

**`adapters/usage.py`** (new) — `UsageLog`
- **Location.** `$REASON_COMMONS_USAGE_LOG` (a path, or `off`), else `$XDG_STATE_HOME/reason-commons/usage.jsonl`, else `~/.local/state/reason-commons/usage.jsonl`.
- **Permissions.** Folder 0700, file 0600.
- **Writes.** Append-only JSON lines: one `flock` and one `O_APPEND` write per line, so the workspace, CLI and MCP processes never interleave.
- **Entry fields.** `v, at (UTC), entry, session, case_id, request_id, provider, model, outcome (proposal|max_tokens|refusal|no_proposal|other_model|no_reply), tokens{input,output,cache_write,cache_write_1h,cache_read}, usd, prices`.
- **Never stored.** Prompts, case text, the case name, paths or keys.
- **Reading.** Skips and counts corrupt lines and a partial last line. Read on open and after each reply, cached by file size and modification time.
- **Session.** `UsageLog.session(entry)` gives `record(event)` (the sink: prices, appends, keeps a copy under a lock, never raises; a write error is kept), `last_for(request_id)`, and `summary(now, case_id)`: this reply, this session, this goal, today and this month by model.
- **Calendar.** Day and month use local time. `now()` is injectable for tests and screenshots.
- **Budget.** `budget_usd()`: `REASON_COMMONS_MONTHLY_BUDGET_USD`, else settings `usage.monthly_budget_usd`. Blank, `none` or `0` means no budget. `crossed(before, after, budget) -> 80|100|None`.

**`adapters/anthropic.py`**
- `usage=None` in `__init__` and `from_env`.
- `_report()` calls the sink inside try/except, so a broken log never loses a paid reply.
- In `propose()`, report the usage read from each reply, with the outcome classified from `stop_reason` and the tool calls:
  - a model mismatch is still recorded (it was billed);
  - a timeout or connection failure after sending is recorded as `no_reply`;
  - HTTP error statuses, `count_tokens` and `/models` are not recorded.
- Pass values to the sink directly: MCP runs calls in parallel on one consultant, so reading `last_usage` back would race. Keep `last_usage` for the evaluation harness.

**Composition**
- `bootstrap.configured_consultant(..., usage=None)` passes the sink to Anthropic only.
- New `bootstrap.usage_session(entry)` reads the environment and the `usage.*` settings. It does not call `apply()`, so the CLI still ignores the saved provider and model.

**Entry points**
- `tui.run()` (`tui.py:3707-3722`), `accessible.run()` (`:477`), `cli.py:234` (`contribute`/`retry`) and `mcp_server.serve()` (`:178-180`) each pass a session sink.
- `scripts/check_anthropic.py` logs as entry `check`, adds `usage` and `estimated_cost_usd` to the smoke report, and gains `--model`.
- The evaluation scripts stay unlogged, as they keep their own token records.

**Test isolation**
- New `tests/conftest.py`: an autouse fixture setting `REASON_COMMONS_USAGE_LOG` to a tmp path and clearing the budget.
- The same in `tests/conversation/environment.py` and `tests/acceptance/environment.py`, and temporary logs in `scripts/check_p0.py` and `scripts/render_screenshots.py`.

**Tests**
- New `tests/test_pricing.py`: the 100,000 / 100,001 boundary, cache rates, exact decimals (the fake server's 12,000 in / 900 out is $0.00165 on Haiku and $0.033 on Sonnet), unknown models, overrides.
- New `tests/test_usage.py`: path precedence and `off`; file modes; corrupt and partial lines; 4 processes × 200 writes; local-midnight and month-end summaries; `crossed()` firing once; a read-only folder never raising; only allowed keys, with no contribution text or key.
- `tests/test_anthropic.py`: sink calls for each outcome; nothing logged for 4xx/5xx; a raising sink still returns the proposal.
- New `providers.feature` scenario: "Count what a Claude reply cost outside the case". The case and its export have no tokens or cost, and the log has no words or key.

### 4. Workspace meter, usage screen, soft budget — done (2026-10-08)
**Wiring**
- `ReasonCommonsApp(..., usage=None)`; `run()` passes `usage_session("workspace")`. Tests, the story and the tour pass none, so the meter is hidden there.
- The summary is cached in `self._meter`, refreshed on mount, in `_submitted` and on opening the screen. It is never read inside `refresh_hints`.

**Footer** (`refresh_hints`, `tui.py:2850`)
- Pass `summary=` alternatives, longest first (HintBar already drops the summary before any hint):
  1. `Haiku 5.5 · session ≈ $0.02 · month ≈ $1.40 of $5`
  2. `Haiku · session ≈ $0.02 · month ≈ $1.40 of $5`
  3. `session ≈ $0.02 · month ≈ $1.40 of $5`
  4. `month ≈ $1.40 of $5`
- Past budget: `month ≈ $5.20, over $5`. No colour is used for any of it; `$warning` already means "proposed".
- With a local consultant: `local model · no charge · month ≈ …`.
- The guide with no spend shows nothing, so the existing footer and screenshots are unchanged.

**Reply toast** (`_submitted`, `tui.py:3108`)
- Append " ≈ $0.0049 (Haiku 5.5)." Nothing when a retry reapplied a saved reply.
- Budget thresholds: a separate `severity="information"` toast, once per crossing, plus once on open if already over. "Each send will ask first; nothing is blocked."

**Usage screen**
- Extend `CallsScreen` (`tui.py:771-786`) and keep the class name and the exact line "Consultant calls in this goal: N", which S07 checks.
- Title and command "Consultant calls and cost". The detail starts "Local:" (S119).
- Contents:
  - Claude replies for this goal.
  - The last reply: model, tokens in and out, cost.
  - This session.
  - Today and this month by model, against the budget.
  - Timed-out requests ("may still have been billed").
  - The current model and where it is set, plus one line for saved-Sonnet users about the new default.
  - "LM Studio and the guide: no charge".
- Note: "Estimates at Anthropic's list prices of <date>, from each reply's token counts; your bill is in the Anthropic Console." Then the log path and the number of skipped lines.
- No model ids and no ISO times.

**Settings screen** (`tui.py:862-924`)
- A Budget row: "$5 a month · ≈ $1.40 so far · Enter changes", or "none set".
- An input accepts 5, $5, 5.50; blank, none or 0 clears it.
- Saving is like `keep_theme` (`Settings.load().set().save()`) and also updates `os.environ`.
- If the shell sets the variable, the row says so.
- Row order: home `voice, mode, setup, budget` (so the existing keys still reach setup); workspace `voice, mode, budget`.
- Settings gains `("usage","monthly_budget_usd")` in `ENVIRONMENT`, and `_get` accepts numbers.

**Confirmation past 100%**
- `spend_check()` wraps `action_send` and `action_retry`, only when the provider is Anthropic and the month is at or over budget.
- It shows a `ChoiceScreen`: "This month ≈ $5.20 of your $5 budget (estimate). This reply ≈ $0.004." Choices: "Send this one" / "Not now".
- "Not now" retains nothing; the draft stays in the editor and is checkpointed.
- It asks once per send. Local actions never ask.

**Accessible presentation** (`accessible.py:337-354`)
- Announce the reply cost and threshold crossings once.
- Past budget, reuse its "activate again to confirm" pattern.

**Docs.** One TUI-DESIGN.md bullet: a paid consultant's cost is said where it is spent (footer right, dropped first; reply toast; Commands › Consultant calls and cost), and past budget each send asks once with nothing blocked. Also `HELP` "Consultants" (`tui.py:207-212`).

**Tests** (`tests/test_tui.py` run_test)
- Footer meter present at 120 columns and absent at 80 and 40; `footer_fits` holds, and Commands and Help stay.
- Toast cost; screen contents including the S07 line and "no charge" for the guide.
- Budget row save and environment update; the row lists in `test_onboarding.py:279,307,322`.
- "Not now" leaves revision, pending requests and draft unchanged; "Send this one" sends; the guide never asks; Retry asks.
- Accessible equivalents in `tests/test_accessible.py`.
- An S119-style check with provider `anthropic`.

### 5. One-reply Sonnet boost — done (2026-10-08)
**Configuration**
- Settings `("anthropic","boost_model")` maps to `REASON_COMMONS_ANTHROPIC_BOOST_MODEL`.
- `anthropic.DEFAULT_BOOST_MODEL = "claude-sonnet-5-5"`, reported by `describe_settings`.
- `render_provider_settings` (`rendering.py:284`) prints "Deeper reasoning on request: claude-sonnet-5-5".

**Mechanism: a TUI-owned stand-in, not a reopen**

```python
class ChosenConsultant:   # adapters/tui.py
    """The workspace's consultant, with an optional stand-in for exactly one consultation. The application
    reads ``version`` after ``propose`` returns, so the stand-in stays until consult() has returned."""
    def __init__(self, consultant): self.default, self.once = consultant, None
    current = property(lambda self: self.once or self.default)
    version = property(lambda self: self.current.version)
    def propose(self, request): return self.current.propose(request)
```

- The case opens with `self.chosen`. `switch_provider` replaces `chosen`.
- `action_import_trees` (`tui.py:3302`) reopens with the same instance instead of calling the factory again.
- The `run()` factory becomes `lambda chosen, model=None: configured_consultant(..., model=model or cli_model, usage=session.record)`. Existing one-argument test lambdas still work.

**When the boost is offered**
- Only when the provider is Anthropic, a boost model is set, it differs from the current model, and its list price is higher.
- So it's hidden for the guide, LM Studio, and Sonnet or Opus users.

**Flow**
1. `action_send(..., deeper=False)` and `action_retry(deeper=False)` refuse while busy.
2. The cached Sonnet stand-in is built on the main thread, then goes through `spend_check`.
3. Set `chosen.once`, run the worker, and reset `once = None` in the worker's `finally` after `consult()` returns, success or failure.
4. Status: "Asking Claude (Sonnet 5.5)…". The Send hint names the model: "Send: get Claude's reply (Haiku 5.5)".
5. Toast: "Sonnet 5.5 answered (≈ $0.05). Send goes to Haiku 5.5 again."

**Commands**
- "Send with deeper reasoning (Sonnet 5.5)", with detail "Asks the consultant: Sonnet 5.5 answers this one, then Haiku again; ≈ $0.05, about 12× a Haiku reply".
  - The figure comes from log averages when each model has at least 3 replies in 90 days, otherwise from a typical
    reply of each at list price (the token shapes measured in `docs/validation.md`; the bare list-price ratio, 20×,
    would overstate it, since Haiku thinks at greater length).
  - The detail must not contain "consultant calls" (S07 filter).
- "Retry with Sonnet 5.5" only when Retry would ask the consultant again, not when it would reapply a received reply (check `case.receipts()`).
- A `#retry-deeper` button beside Retry from 100 columns up. Narrower, it lives in Commands and the failure toast says so.

**CLI and MCP**
- Document `reason-commons retry CASE REQUEST --provider anthropic --model claude-sonnet-5-5` (and `contribute`).
- No model parameter on MCP tools, so an agent cannot escalate spend.

**Tests**
- `tests/servers.py`: per-model metadata (`server.models`).
- `test_tui.py`:
  - A boosted send's receipt says `model=claude-sonnet-5-5`, and the next send's says Haiku.
  - A boost that fails (404) still returns to Haiku.
  - Refused while busy; hidden for the guide or a Sonnet default.
  - "Retry with Sonnet" only when Retry would ask again.
  - Import keeps the consultant.
  - The log has both models.
- `test_tui.py:115-131` still passes.

### 6. `reason-commons usage`; CLI and MCP notices
- **`cli.py` `usage [--month YYYY-MM | --all] [--goal FOLDER] [--json]`.** Reads only the log, sends nothing, exits 0. It shows:
  - each model's replies, tokens and estimated cost;
  - the total against the budget;
  - today;
  - totals by entry point;
  - timed-out requests and skipped lines;
  - the Console note and the log path.
- **CLI notices.** `contribute`/`retry` print one stderr line at 80% and at 100% ("nothing was blocked"). stdout, JSON output and exit codes don't change.
- **MCP notices.** A `usage_notice` field in `consult`/`submit`/`retry` results at 80% or more. Nothing goes to stdout, which is the transport.
- **Tests.** `tests/test_invocation.py` or a new `tests/test_cli_usage.py`; `tests/test_mcp_bridge.py`.

### 7. Docs and screenshots
**Docs**
- `docs/providers.md`: the default; "Deeper reasoning for one reply"; a "What it costs" section (log location, privacy, `off`, budget, `usage`); the note that Haiku replies take longer.
- `docs/tui.md`: commands, footer, budget row, and the new environment variables.
- `docs/use-a-model.md`, `docs/skill-use.md`, and a "What it costs" row in the README consultant table.
- `ARCHITECTURE.md`: usage stays outside the case through an injected sink; the one-reply stand-in; the budget is an interface notice, not a case rule.
- `evaluations/live-claude-test-prompt.md`: set `REASON_COMMONS_USAGE_LOG`, and check that `reason-commons usage` counts the run.

**Screenshots** (`scripts/render_screenshots.py`, with a temporary log and a fixed `usage.now`)
- Re-render `setup-model`, `home-settings`, `actions-palette` and `consultant-unavailable`.
- Add `usage-and-cost` and `footer-meter`.

## Critical files
- `src/reason_commons/adapters/anthropic.py`, `tui.py`, `settings.py`, `onboarding.py`, `cli.py`, `mcp_server.py`,
  `accessible.py`, `rendering.py`; new `adapters/pricing.py`, `adapters/usage.py`
- `src/reason_commons/bootstrap.py` (the composition root)
- `tests/servers.py`, `tests/conftest.py` (new), `tests/conversation/features/providers.feature` and its steps
- `scripts/render_screenshots.py`, `scripts/check_anthropic.py`, `docs/*`, `TUI-DESIGN.md`, `ARCHITECTURE.md`

**Reused rather than rebuilt**
- `CallsScreen` / `call_counts()` (`tui.py:771,3248`); `HintBar.update_hints` summary alternatives (`tui.py:967-1038`).
- `ChoiceScreen` / `PathScreen` for the confirmation and the budget input; the `keep_theme` save pattern (`tui.py:1109`).
- `Settings` / `ENVIRONMENT` (`settings.py`); `timeline.day()` for dates.
- `switch_provider` (`tui.py:3325`); `action_retry` / `retryable()`.
- The fake-server `transform`/`metadata` hooks (`tests/servers.py`); `evaluations/report.consultation_summary` as a model for summaries.

## Verification
- **After each step.**
  - `TZ=UTC .venv/bin/python -m pytest -q` on the touched test files.
  - The conversation runner: `.venv/bin/python -m behave --runner tests.conversation.runner:ConversationRunner tests/conversation/features`.
  - `TZ=UTC .venv/bin/python scripts/check_p0.py`: exit 0, with S07 and S114–S120 still passing.
- **Docs.** `pytest -q tests/test_docs.py tests/test_development_docs.py`, then `python3 scripts/render_screenshots.py`.
- **Live smoke** (billed, about $0.12), with `REASON_COMMONS_USAGE_LOG` in a throwaway folder:
  1. `scripts/check_anthropic.py --smoke` on Haiku, then on `--model claude-sonnet-5-5`.
  2. `reason-commons usage`: 2 replies, Haiku and Sonnet.
  3. `REASON_COMMONS_MONTHLY_BUDGET_USD=0.02 reason-commons tui <case> --provider anthropic`, then:
     - Send once and check the toast and footer.
     - Ctrl+P → Send with deeper reasoning: check "Asking Claude (Sonnet 5.5)…".
     - The next Send asks to confirm; choose "Not now" and check the draft is kept.
     - Open "Consultant calls and cost".
  4. `inspect --json` shows Haiku, Sonnet, Haiku versions in order.
  5. Record the results in `docs/validation.md`. A day later, compare the log with the Anthropic Console.
- **Ship.** Commit and push each step to `claude/relaxed-rubin-9mij55`.
