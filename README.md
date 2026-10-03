# Reason Commons

A persistent terminal workspace that helps people reason through shared goals,
problems, changes and results, one small loop at a time: **goal → test with an
original forecast → action → observation → review**.

## Status

| Part | State |
| --- | --- |
| p0 durable case engine | Implemented: revisions, YAML storage, export/import, retry, consultant ports, CLI, MCP |
| Terminal workspace (TUI) | First personal-use slice of p1: `reason-commons tui`, built with Textual |
| Built-in guide | Offline consultant (`guided`) that walks the loop without a model or key |
| Full p1 contract | Not yet delivered: `--accessible`, speaker switching, 80×24 specimens, usability evidence |
| p2 and later | Consulting-quality gates, review loop acceptance and typed graphs remain later work |

## Quick start (macOS)

```sh
git clone https://github.com/life-itself/reason-commons-tui.git
cd reason-commons-tui
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade pip   # macOS ships an old pip that cannot install this
python3 -m pip install -e '.[tui]'
reason-commons tui ~/ReasonCommons/my-first-goal
```

The folder is created on first run; the same command resumes it, including your
unsent draft. It works offline with the built-in guide. To use Claude, set
`ANTHROPIC_API_KEY` and add `--provider anthropic`; for a local model use
`--provider lm-studio`. You can also switch with Ctrl+P inside the app.
[Running the TUI](docs/tui.md) covers keys, consultants, data and limits.

## Developers

The [architecture](ARCHITECTURE.md) explains the domain/application/adapter
boundaries and how BDD and replaceable skills use the same application surface.
The [p0 implementation report](docs/p0-delivery.md) records the delivered slice.

```sh
python3 -m pip install -e '.[test]'
python3 scripts/check_p0.py
reason-commons new --store /tmp/payments-case --name Payments
reason-commons show /tmp/payments-case
reason-commons inspect /tmp/payments-case --json
reason-commons export /tmp/payments-case /tmp/payments.reasoncase
reason-commons import /tmp/payments.reasoncase --store /tmp/payments-handoff
```

Use a new destination for each case or export. Without installation, prefix
utilities with `PYTHONPATH=src python3 -m reason_commons`. Python 3.9+ and a local
POSIX filesystem are supported. The application API accepts an injected
consultant; the deterministic acceptance suite requires no provider or key.

The TUI adapter (`adapters/tui.py`) and the offline `GuidedConsultant`
(`adapters/guided.py`) use the same application boundary as every other
interface. `tests/test_tui.py` drives the workspace headlessly with Textual's
pilot; install `.[test,tui]` to run it. The full gate's desktop-launcher test
needs `/bin/zsh` and a `.venv` in the repository.

For a local model, see the [LM Studio setup](docs/lm-studio.md). The
`LMStudioConsultant` adapter plugs into the same application boundary and requests
structured proposals; application/domain validation stays authoritative.
The [validation guide](docs/validation.md) runs repeatable live-model, real-agent
and recovery evaluations, with retained evidence and an attributed review rubric.

The [skill usage guide](docs/skill-use.md) describes a continuing conversation in
Codex, with saved questions, local explanations/history/sources, recorded diagrams
and forecast comparisons. Offline `show` and deliberate `contribute`/`retry`
commands use the same workspace through the application boundary. The contribution procedure ships in the Python package and is discoverable
through the repository's `.agents/skills` symlink. MCP is optional (`.[mcp]`,
Python 3.10+); the durable engine and local invocation remain Python 3.9+.

Start with the [first-release TUI journey](reason-commons-spec/example-mvp-session.txt)
or the [full visual reasoning journey](reason-commons-spec/example-tui-session.txt).
Then read the [specification](reason-commons-spec/reason-commons-specification.md),
[terminal design contract](TUI-DESIGN.md) and [bundle guide](reason-commons-spec/README.md).

The product is **Reason Commons**. The proposed executable is `reason-commons`.
Ordinary work uses visible workspace controls and a literal response editor.
Questions, reports, relationships, goals, tests, actions and reviews are the
user-facing concepts. Shell commands launch/resume or operate offline utilities.
The accessible ordered presentation shares the same actions and submission rules.
