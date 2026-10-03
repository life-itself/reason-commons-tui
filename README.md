# Reason Commons

A persistent terminal workspace that helps people reason through shared goals,
problems, changes and results. The **p0 durable case engine is implemented**.
A first personal-use slice of the p1 TUI is available; the complete
first-release goal–action–review loop is p2. Authored interface specimens
describe those subsequent increments.

**To open the workspace**, see [Running the TUI](docs/tui.md):

```sh
python3 -m pip install -e '.[tui]'
reason-commons tui ~/ReasonCommons/my-first-goal
```

It works offline with a built-in guide; Anthropic or LM Studio are optional.

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
