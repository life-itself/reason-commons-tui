# Contributing to Reason Commons

This page is for people working on Reason Commons itself. To use it, see the
[README](README.md).

Start with [AGENTS.md](AGENTS.md) for the working rules, then the
[architecture](ARCHITECTURE.md) and `src/reason_commons/domain/CONTEXT.md`.

## Set up

```sh
git clone https://github.com/life-itself/reason-commons-tui.git
cd reason-commons-tui
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade pip   # macOS ships an old pip that cannot install this
python3 -m pip install -e '.[test]'
python3 scripts/check_v1.py            # the full gate
```

The full gate's desktop-launcher test needs `/bin/zsh` and a `.venv` in the
repository.

## Accepted v1 and future work

The current simplified app is the v1 baseline. [The matrix](docs/v1-reconciliation.md)
inventories current capabilities and every scenario disposition; [the current
report](docs/v1-delivery.md) records checks and outstanding evidence. The manifest
orders p0–p4 as an editorial development progression culminating in v1; p5–p7
retain future richer causal, group-position and full-tool work. These labels do
not rename the compatible serialized profile `p2` or authenticate a historical story.

V1 includes the guided loop, adaptive-provider integration, six partial trees,
proposals/decisions/review flags/undo, literal sources, editable RC development
import, stage history, ordered accessible text, Settings, tour and a separate
editorial reading example. Tests, Loop actions, Reasoning and Commons context
remain under Commands/Views when absent from the small imported sidebar.
Semantic review, participant usability and assistive-technology evidence remain
separate from implementation and release membership.

## Screenshots

The README and docs pictures are rendered from the real workspace with the
built-in guide and fixed dates. After changing what the workspace shows, run
`python3 scripts/render_screenshots.py` (PNG copies need Chromium and Pillow) and
review the changed `docs/images/` files. Then run `python3 scripts/render_commons.py`
for the primary RC import. Each renderer owns distinct home/first-start filenames;
`docs/images/runtime-manifest.json` records fixtures and hashes.
`docs/images/loop.svg` and `docs/images/trees/` are illustrations, not UI captures.

The optional capture utility makes a picture per selected executed step, named
by feature, scenario and step. Its default is `@v1 and @automated`;
`--all-contract` documents available steps in the future/evaluation contract and
records undefined steps explicitly. This is a documentation utility, not a gate. Run
`python3 scripts/capture_steps.py` to regenerate `docs/screenshots/`; each run
replaces that folder. Its `MANIFEST.json` records where each picture came from (the
live workspace, a fresh workspace on a copy of the commons, or the accessible
presentation's text) and lists the steps that have no step definition yet. The folder
is git-ignored, since full-contract capture can exceed 100 MB; regenerate it rather
than commit it.

## Engine, utilities and agents

The [architecture](ARCHITECTURE.md) explains the domain/application/adapter
boundaries and how BDD and replaceable skills use the same application surface.
The [current v1 report](docs/v1-delivery.md) records scope and checks;
[the older report](docs/p0-delivery.md) retains dated evidence.

```sh
python3 -m pip install -e '.[test]'
python3 scripts/check_v1.py
reason-commons new --store /tmp/payments-case --name Payments
reason-commons show /tmp/payments-case
reason-commons inspect /tmp/payments-case --json
reason-commons export /tmp/payments-case /tmp/payments.reasoncase
reason-commons import /tmp/payments.reasoncase --store /tmp/payments-handoff
```

Use a new destination for each commons or export. Without installation, prefix
utilities with `PYTHONPATH=src python3 -m reason_commons`. Python 3.9+ and a local
POSIX filesystem are supported. The application API accepts an injected
consultant; the deterministic acceptance suite requires no provider or key.

The TUI adapter (`adapters/tui.py`) and the offline `GuidedConsultant`
(`adapters/guided.py`) use the same application boundary as every other
interface. `tests/test_tui.py` drives the workspace headlessly with Textual's
pilot; install `.[test]` to run it. The full gate's desktop-launcher test
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
or the [future visual reasoning illustration](reason-commons-spec/example-tui-session.txt).
Then read the [specification](reason-commons-spec/reason-commons-specification.md),
[terminal design contract](TUI-DESIGN.md) and [bundle guide](reason-commons-spec/README.md).

The product is **Reason Commons**. The executable is `reason-commons`.
Ordinary work uses visible workspace controls and a literal response editor.
Questions, reports, relationships, goals, tests, actions and reviews are the
user-facing concepts. Shell commands launch/resume or operate offline utilities.
The accessible ordered presentation shares the same actions and submission rules.
