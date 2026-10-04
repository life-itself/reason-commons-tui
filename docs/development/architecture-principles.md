# Architecture principles

These principles explain *why* the layers are where they are, so a new change can
be placed without guessing. `ARCHITECTURE.md` records the concrete boundaries,
guarantees and enforcement; this page gives the reasoning behind them.

## The layers

```
Human interfaces:  offline CLI   TUI (p1)   other UIs / API / scheduled job
Agent side:        agent (runtime)  ->  skill (procedure)
                          \               /
                   Application use cases and ports (CaseCapabilities)
                                  |
                           Domain model (Reasoning Case)
                                  |
              Outbound ports: storage, consultant, clock  ->  adapters
```

Humans and agents enter through the **same application surface**. That is the
central design choice: nothing a person can do is out of an agent's reach, and
nothing an agent does bypasses a rule a person is held to.

## Where a skill fits

A skill is a repeatable procedure for a type of task. In layered terms it is an
**intelligent application adapter**: it sequences application capabilities on
behalf of an agent. It is not the application layer itself, and it is not part of
the domain.

| Role | Analogy | In this repository |
|---|---|---|
| Interface (CLI, TUI) | Controller / view | `adapters/cli.py`, the future TUI |
| Skill | Use-case orchestrator for an agent | `adapters/contribution_skill/SKILL.md`, `adapters/skills.py` |
| Agent | Executor / interpreter | An external agent, or the experimental `adapters/skill_agent.py` |
| Application use case | Application service | `application/service.py`, published in `application/ports.py` |
| Domain | Business semantics | `domain/` |
| Infrastructure | Adapters behind ports | `adapters/filesystem.py`, `lm_studio.py`, `anthropic.py` |

Treat the agent as a runtime and the skill as the program it runs. Presentation
may depend on skills, skills on application capabilities, application on the
domain, and the domain on nothing but the standard library. The domain knows
nothing of the skill or the agent.

## The replaceability test

Before placing anything, ask whether you could replace the interface (TUI, web UI,
CLI, API, scheduled job), the skill, the model, or the provider **without
rewriting anything below it**. If not, something is in the wrong layer. The
shipped examples: the offline CLI and the MCP server drive the same use cases, the
procedure runner and the agent runner drive the same host, and LM Studio and
Anthropic implement the same consultant port.

## A rule lives where it can be enforced

If a rule is part of what a valid case means, the **domain** enforces it. It must
not live only in:

- `SKILL.md` ("remember to check consumers before changing published language"),
- a prompt or a model's good behavior,
- a TUI confirmation, disabled menu item or validation hint.

Those may *guide* a participant or an agent toward the right workflow, but the
application must make the invalid operation fail even when called directly. This
is why a skill can be removed, rewritten or run by a weaker model without risking
the case, and why tests for the domain need no skill or agent at all.

A useful check: delete the guidance and call the use case with a bad input. If
the bad input succeeds, the rule is not yet enforced.

## What belongs in a `SKILL.md`

A skill file often mixes concerns. Keep only the application workflow in it and
point to the owners for the rest.

| Content | Belongs in |
|---|---|
| Sequencing: inspect, retain, consult, report | `SKILL.md` |
| What a term means | `domain/CONTEXT.md`, referenced, not copied |
| What is valid or forbidden | `domain/` and the application use cases |
| How a tool or provider is reached | `adapters/` |
| How results are laid out for a person | `adapters/rendering.py` and `application/presentation.py` |
| Prompting detail for the consultant | `adapters/prompts/consultant.md` |

The packaged procedure already follows this: it reads the glossary and the
capability contract instead of restating them, and says it "supplies no consulting
semantics of its own".

## Interface guarantees

Two guarantees keep the interfaces honest (details in `ARCHITECTURE.md`):

- **Semantic parity.** Every domain-significant operation a local interface offers
  must be expressible through `CaseCapabilities`. Focus, viewport, expansion and
  caret state are exempt. `tests/test_architecture.py` fails when a public use
  case is missing from the capability surface or its signature differs.
- **Projection, not authority.** The TUI projects and accelerates application
  state. It defines no reasoning invariants, consulting semantics or persistence
  behavior. A consequential rule is enforced in the application even if the UI also
  offers a hint.

## Provider neutrality

The consultant is a replaceable choice made only at composition
(`bootstrap.py`). The application never names a provider: an adapter tags its own
failures with a safe category, and the application records that. See
[Choosing a consultant](../providers.md).

## Dependency direction, mechanically

`.workflow.json` declares the rules and `tests/test_architecture.py` checks them:
the domain imports only the standard library; the application imports the domain
and never an adapter or skill; adapters may import the application, the domain and
composition. Only `bootstrap.py` chooses concrete adapters. A change that needs an
outward import means a port is missing; add the port instead.

## One bounded context

There is a single context, Reasoning Case. Storage and consulting are capabilities,
not invented contexts. Add a context, with a published contract, only when
independent domain ownership genuinely emerges.
