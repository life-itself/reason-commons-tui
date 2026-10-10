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
python3 scripts/check_p0.py            # the full gate
```

The full gate's desktop-launcher test needs `/bin/zsh` and a `.venv` in the
repository.

## Status by delivery phase

| Part | State |
| --- | --- |
| p0 durable case engine | Implemented: revisions, YAML storage, export/import, retry, consultant ports, CLI, MCP |
| Terminal workspace (TUI) | First personal-use slice of p1: `reason-commons tui`, built with Textual |
| Built-in guide | Offline consultant (`guided`) that walks the loop without a model or key |
| Real commons | The Second Renaissance story (`adapters/stories/second-renaissance.yaml`), built one revision per chapter by `scripts/build_story.py` into the packaged `.reasoncase`; History becomes a steppable timeline for every goal |
| First start | Ways to begin, setup (name, consultant, checked key and model), Settings and the in-app guided tour (`adapters/onboarding.py`, `adapters/settings.py`) |
| Six trees | Tree statements, links (which may reach another tree), new versions and withdrawals, with the goal at the Goal Tree's top (p2, S128–S134); Trees view, `trees` command, `.ltp.yaml` import/export |
| Deciding what enters the model | Proposals, the acceptance setting, the ordered Backlog, review flags and undo (p2, S135–S150; `domain/membership.py`); Backlog view, Accept all, Undo in History, `decide` command, MCP decision tools |
| Full p1 contract | Not yet delivered: `--accessible`, speaker switching, 80×24 specimens, usability evidence |
| p2 and later | Consulting-quality gates, review loop acceptance, joint causes and rival routes remain later work |

## Screenshots

The README and docs pictures are rendered from the real workspace with the
built-in guide and fixed dates. After changing what the workspace shows, run
`python3 scripts/render_screenshots.py` (PNG copies need Chromium and Pillow) and
commit `docs/images/`. `docs/images/loop.svg` is drawn by hand.

Every executed step of the specification and conversation features also has a
picture, one per step, named by feature, scenario and step. Run
`python3 scripts/capture_steps.py` to regenerate `docs/screenshots/`; each run
replaces that folder. Its `MANIFEST.json` records where each picture came from (the
live workspace, a fresh workspace on a copy of the case, or the accessible
presentation's text) and lists the steps that have no step definition yet. The folder
is git-ignored, since it is about 100 MB of generated pictures; regenerate it rather
than commit it.

## Engine, utilities and agents

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
or the [full visual reasoning journey](reason-commons-spec/example-tui-session.txt).
Then read the [specification](reason-commons-spec/reason-commons-specification.md),
[terminal design contract](TUI-DESIGN.md) and [bundle guide](reason-commons-spec/README.md).

The product is **Reason Commons**. The proposed executable is `reason-commons`.
Ordinary work uses visible workspace controls and a literal response editor.
Questions, reports, relationships, goals, tests, actions and reviews are the
user-facing concepts. Shell commands launch/resume or operate offline utilities.
The accessible ordered presentation shares the same actions and submission rules.
