# Using LM Studio

LM Studio is one of two consultants; [Choosing a consultant](providers.md) covers
how to select between it and Anthropic, check the setup, and diagnose failures.
This page covers the local server itself. Select it with
`REASON_COMMONS_PROVIDER=lm-studio` or `--provider lm-studio`; it is also the
default when nothing is chosen.

`LMStudioConsultant` implements the existing `Consultant` port. It calls only the
configured LM Studio server, with no hosted fallback or implicit retries. All
application validation, retention, stale-target checks and durable commits apply
unchanged. In the workspace, start with `reason-commons tui <folder> --provider lm-studio`
or switch with Ctrl+P → Consultant: LM Studio (see [tui.md](tui.md)).

## Server and model

In LM Studio's Developer tab, start the local server and select a chat model.
The usual API address is `http://127.0.0.1:1234/v1`. The official
[server guide](https://lmstudio.ai/docs/developer/core/server) also documents
`lms server start`. Use the served model ID from `/v1/models`, rather than a
display label or a model file path. JIT loading may advertise downloaded models
that are not currently loaded. Choose a chat model rather than an embedding model.
Automatic selection requires exactly one advertised ID; ambiguous lists require
an explicit choice.

Explicit selections are also verified against `/v1/models` on the first request,
and every completion must identify that same model. This prevents a server from
silently answering with a loaded model when the requested name is unavailable.

This machine advertises `google/gemma-4-e4b` as its chat model. A separate
`text-embedding-nomic-embed-text-v1.5` model is for embeddings.

```sh
export REASON_COMMONS_LM_STUDIO_MODEL='google/gemma-4-e4b'
export REASON_COMMONS_LM_STUDIO_URL='http://127.0.0.1:1234/v1'
export REASON_COMMONS_LM_STUDIO_TIMEOUT='120'
```

If your server requires authentication, provide `LM_STUDIO_API_TOKEN` in the
process environment. The adapter sends a Bearer header. Tokens and server
addresses are not serialized into commons or exports. Do not put tokens in URLs.
[LM Studio authentication](https://lmstudio.ai/docs/developer/core/authentication)
is optional and controlled by your server settings.

## Application use

```python
from reason_commons.adapters.lm_studio import LMStudioConsultant
from reason_commons.bootstrap import open_case

consultant = LMStudioConsultant.from_env()
with open_case("payments-case", consultant=consultant) as app:
    current = app.inspect()["case"]
    result = app.submit(
        "Here is my observation", "Sam",
        base_revision=current["revision"],
        response_target=current["current_intervention"],
    )
```

You can instead construct `LMStudioConsultant(model="served-id", base_url=...,
timeout=..., max_tokens=..., temperature=...)` explicitly. Reopen the same commons
with a different adapter/model to switch models; committed records and forecasts
remain unchanged. Model, adapter/prompt/schema versions and generation settings
are recorded for each applied request.

A received-but-uncommitted proposal is recovered from the commons, even if you
reopen with another model. Its original adapter version is retained. To obtain
a new model's evaluation, submit a new contribution against the current target.
Do not treat changing models as permission to overwrite an original forecast.

## Output contract and recovery

LM Studio receives the complete `{input, case, sources}` request, domain context
and a consulting procedure. The adapter uses
[structured output](https://lmstudio.ai/docs/developer/openai-compat/structured-output)
on `/v1/chat/completions`, with a JSON Schema generated from the domain registry.
Request identity/base revision are constrained to the retained input. The model
still cannot bypass exact-reference, profile or explicit-input-authority checks.
Valid JSON alone does not establish sound consulting or factual truth.

Malformed JSON, duplicate keys, refusals and token-truncated output are rejected
without a reasoning commit; input and a failure receipt remain available.
Connection, timeout and HTTP errors produce an unavailable receipt. The adapter
does not silently strip formatting, repair output, truncate context, switch to
plain-text mode, fall back to another provider or repeat a generation. Explicit
retry uses the retained request identity.

For a model/server that cannot support the requested structured schema, the
request fails; choose a compatible model rather than weaken domain validation.
Cold loading can take longer than an already-loaded generation. Set a longer
timeout when appropriate. Requests/responses have size limits and large commons
may exceed a model's context window; no hidden truncation occurs.

## Developer verification

The one-shot smoke harness submits a synthetic situation into a new disposable
commons; it is a development check, not an alternative interactive shell workflow:

```sh
PYTHONPATH=src python3 examples/lm_studio_smoke.py \
  --store /tmp/reason-lm-check \
  --model google/gemma-4-e4b
```

Use a fresh store destination. A successful run prints the committed proposal
and provider version. On failure, inspect the retained commons and LM Studio's
developer logs. Offline inspect/history/export continue to work without a model.

`python3 scripts/check_p0.py` includes local HTTP fixture tests for payload/schema,
authentication, invalid/truncated output, HTTP failure/retry, redirects and model
switching. These tests bind temporary loopback sockets; a sandbox that prohibits
socket binding needs permission to run the suite. They require neither LM Studio
nor model downloads. The live smoke harness is separate and opt-in. A successful
live transaction verifies integration, not the p2 semantic or participant gates.

For repeated multi-turn and failure testing, use the
[validation harness](validation.md). It also runs the actual contribution skill
with a tool-calling agent and records effects independently of the agent's prose.
Current Gemma evaluations expose semantic omissions and invalid references;
this model/configuration has not passed the full v1 quality gate. The loaded
context window reported by LM Studio can be smaller than a model's advertised
maximum; the evidence records that distinction without truncating the commons.

Initially verified on 2 October 2026 against the local `google/gemma-4-e4b` model: a synthetic
situation produced a structured intervention, passed application/domain
validation and was committed as revision 1. The disposable commons is at
`/tmp/reason-commons-lmstudio.Es6zle/case`; it can be inspected offline. The full
gate passed 67 implementation tests, 23 specification regressions and all nine
p0 acceptance scenarios. The packaged prompt/context were verified after
installing a built wheel into an isolated environment.

The later regression gate passed 110 implementation tests, 23 specification
regressions and all nine original p0 scenarios. The live evaluation evidence
and remaining semantic failures are described in [validation](validation.md).
