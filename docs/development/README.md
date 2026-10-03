# How we develop Reason Commons

Start here, whether you are a person or an agent. These documents say how work
proceeds in this repository: where a change belongs, what to write first, how to
prove it, and when to stop and ask. `AGENTS.md` is the short entry point; this set
holds the reasoning and the procedures.

## The method in one paragraph

Behavior is **specified in Gherkin**, **enforced by the domain and application**,
**performed by replaceable skills and agents**, and **reached through replaceable
interfaces**. Specification comes first. A rule lives in the narrowest layer that
can enforce it, and never only in a prompt or a screen. Skills are tested for their
effects and decisions, not their prose. The application stays correct if the skill,
the model, or the TUI is removed.

> The TUI expresses intent. The skill orchestrates the use case. The domain decides
> what is valid. The agent executes the orchestration. Infrastructure makes the
> outside world accessible.

## Who owns what

Each question has exactly one authoritative place. Change the owner, not a copy.

| Question | Owner | Where |
|---|---|---|
| What must be observable? | `.feature` files | `reason-commons-spec/features/` (product scope; authoritative) and `tests/conversation/features/` (conversation and provider behavior we own) |
| What do the words mean? | Domain glossary | `src/reason_commons/domain/CONTEXT.md` |
| What states and rules are valid? | Domain model | `src/reason_commons/domain/model.py`, `contract.py` |
| How is behavior invoked? | Application use cases | `src/reason_commons/application/ports.py` (`CaseCapabilities`), `service.py` |
| How does an agent carry out the work? | Skill procedure | `src/reason_commons/adapters/contribution_skill/SKILL.md` (linked from `skills/` and `.agents/skills/`) |
| How does a human initiate and control it? | Interface | The offline CLI today; the TUI (p1) is specified in `TUI-DESIGN.md` and is not built |
| Which dependencies and gates apply? | Control files | `ARCHITECTURE.md`, `.workflow.json`, `tests/test_architecture.py` |

If two owners appear to disagree, do not pick one silently. The specification and
its delivery tags define scope; the glossary maps them onto code. Report the
conflict and ask.

## Documents in this set

| Read | When |
|---|---|
| [Architecture principles](architecture-principles.md) | Deciding where a change belongs; placing a rule; touching a skill |
| [Testing strategy](testing-strategy.md) | Choosing what kind of test to write and what it may assert |
| [Workflow](workflow.md) | Doing any change, start to finish, and knowing when it is done |
| [Recipes](recipes.md) | Adding a rule, a use case, a provider, an interface action, or changing a skill |

## Reading order by task

Every task starts with `AGENTS.md`, this page, `ARCHITECTURE.md` and
`src/reason_commons/domain/CONTEXT.md`. Then:

| Task | Also read |
|---|---|
| Change case behavior | The relevant spec features, [workflow](workflow.md), [testing strategy](testing-strategy.md) |
| Provider or adapter work | [Choosing a consultant](../providers.md), [LM Studio](../lm-studio.md) |
| Skill or procedure work | [Skill usage](../skill-use.md), the packaged `SKILL.md`, [validation](../validation.md) |
| TUI or interface work | `TUI-DESIGN.md`, `reason-commons-spec/tui-reasoning-design.md`, `reason-commons-spec/accessibility.md` |
| Scope or delivery questions | `reason-commons-spec/delivery-phases.md`, [P0 delivery](../p0-delivery.md) |

## Where this came from

The layering, the BDD boundary and the skill-testing approach follow a design
discussion about agentic domain-driven design with Gherkin. The documents here
restate those conclusions against this repository's real files and gates, and
`tests/test_development_docs.py` keeps the paths they cite from rotting.
