"""Anthropic Messages API implementation of the existing Consultant port.

One proposal tool call is data, never permission to execute an app tool.
The application validates and publishes it. No retries or provider fallback.
Lossless slips in how a model passes the call's arguments are undone and reported
in last_repairs; nothing the consultant decides is changed or filled in.
"""

from hashlib import sha256
from http.client import HTTPException
from importlib.resources import files
import json
import math
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import ProxyHandler, Request, build_opener

from reason_commons.adapters.provider_support import NoRedirect, decode_json, request_schema
from reason_commons.application.ports import ConsultantResponseError
from reason_commons.domain.model import FIELDS, PROFILE, SCHEMA


MAX_REQUEST_BYTES = 4 * 1024 * 1024
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
# The lowest-cost model the consulting procedure is validated with (docs/validation.md); a saved or chosen
# model always wins over it.
DEFAULT_MODEL = "claude-haiku-5-5"
# Thinking shares the output budget with the proposal, so leave room for both.
DEFAULT_MAX_TOKENS = 16000
EFFORTS = ("low", "medium", "high", "xhigh", "max")
# Unset effort means "high" where the model reports support for it, and otherwise the model's own
# default; "default" never sends one. The consulting rules reward careful instruction following.
DEFAULT_EFFORT = "high"
USAGE_FIELDS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


def usage_tokens(usage):
    """A reply's token counts as the usage log keeps them; anything missing or malformed counts as none."""
    usage = usage if isinstance(usage, dict) else {}
    count = lambda value: value if type(value) is int and value >= 0 else 0
    written = count(usage.get("cache_creation_input_tokens"))
    detail = usage.get("cache_creation") if isinstance(usage.get("cache_creation"), dict) else {}
    hour = min(written, count(detail.get("ephemeral_1h_input_tokens")))
    return {"input": count(usage.get("input_tokens")), "output": count(usage.get("output_tokens")),
            "cache_write": written - hour, "cache_write_1h": hour, "cache_read": count(usage.get("cache_read_input_tokens"))}


def _label(value):
    """A provider enum value safe to show; anything else is reported as unknown."""
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,39}", value) else "unknown"


def _supported(node):
    return isinstance(node, dict) and node.get("supported") is True


def _decoded(text, kind):
    try:
        value = decode_json(text)
    except (ValueError, RecursionError):
        return None
    return value if isinstance(value, kind) else None


def undo_transport_slips(arguments, envelope):
    """The proposal a call's arguments carry, with what had to be undone to read it.

    Only lossless slips: the proposal wrapped in an object with a single field, the intervention
    or the updates sent as a string of JSON, schema_version or delivery_profile sent as a JSON string
    literal, and an envelope field left out that can have only one value for this call (``envelope``).
    Anything else, a wrong envelope value included, reaches domain validation exactly as it came."""
    repairs, value = [], arguments
    if len(value) == 1:
        (key, inner), = value.items()
        # A lone wrapper (seen as "input" and "args") says nothing; the proposal is what it holds.
        if isinstance(inner, dict) and {"intervention", "proposed_updates"} & set(inner):
            value = inner
            repairs.append("unwrapped the proposal from " + _label(key))
    value = dict(value)
    for field, kind in (("intervention", dict), ("proposed_updates", list)):
        if isinstance(value.get(field), str) and (decoded := _decoded(value[field], kind)) is not None:
            value[field] = decoded
            repairs.append(f"decoded {field} from a string of JSON")
    for field in ("schema_version", "delivery_profile"):
        text = value.get(field)
        if (isinstance(text, str) and len(text) > 1 and text[0] == text[-1] == '"'
                and (decoded := _decoded(text, str)) is not None):
            value[field] = decoded
            repairs.append(f"unquoted {field}")
    for field, only in envelope.items():
        if field not in value and {"intervention", "proposed_updates"} <= set(value):
            value[field] = only
            repairs.append(f"filled the missing {field}")
    return value, repairs


class AnthropicError(RuntimeError):
    """Safe provider diagnostics; never expose credentials or response bodies."""

    def __init__(self, message, category="configuration", http_status=None, sent=False):
        super().__init__(message)
        # sent: the request went out in full and no reply came back, so it may still have been billed.
        self.category, self.http_status, self.sent = category, http_status, sent


class AnthropicConsultant:
    def __init__(self, model=DEFAULT_MODEL, base_url="https://api.anthropic.com/v1",
                 api_key=None, timeout=120.0, max_tokens=DEFAULT_MAX_TOKENS, effort=None, usage=None):
        parts = urlsplit(base_url)
        local_http = parts.scheme == "http" and parts.hostname in {"127.0.0.1", "localhost", "::1"}
        if (not (parts.scheme == "https" or local_http) or not parts.hostname
                or parts.username or parts.password or parts.query or parts.fragment
                or parts.path.rstrip("/") not in {"", "/v1"}):
            raise ValueError("Use an HTTPS Anthropic server URL (HTTP is allowed only for loopback tests)")
        if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", model):
            raise ValueError("Use an explicit Anthropic model ID")
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Timeout must be a positive finite number of seconds")
        if type(max_tokens) is not int or max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")
        if effort is not None and effort not in EFFORTS + ("default",):
            raise ValueError("Effort must be one of " + ", ".join(EFFORTS + ("default",)))
        if api_key is not None and (not isinstance(api_key, str) or not api_key.strip()
                                    or "\n" in api_key or "\r" in api_key):
            raise ValueError("Invalid Anthropic API key")
        self.model, self.timeout, self.max_tokens, self.effort = model, timeout, max_tokens, effort
        self.base_url = urlunsplit((parts.scheme, parts.netloc, "/v1", "", ""))
        self._api_key, self._resolved_model, self._sent_effort = api_key, None, None
        # Token counts and transport repairs of the last reply, for evaluation evidence; never part of the case.
        self.last_usage, self.last_repairs = None, []
        # Told what each request cost, as it happens (the composition root's usage sink); never part of the case.
        # Calls can run in parallel on one consultant, so each is reported with its own values.
        self.usage = usage
        self._opener = build_opener(ProxyHandler({}), NoRedirect())
        self._context = files("reason_commons.domain").joinpath("CONTEXT.md").read_text(encoding="utf-8")
        self._procedure = files("reason_commons.adapters").joinpath("prompts/consultant.md").read_text(encoding="utf-8")
        self._procedure += (
            "\n\nANTHROPIC TRANSPORT\nReturn the complete proposal by calling submit_proposal exactly once, rather "
            "than writing JSON as plain text. The call's arguments are the proposal itself, not wrapped in another "
            "object: its top level has exactly six fields, schema_version, delivery_profile, request_id, "
            "base_revision, intervention and proposed_updates. schema_version and delivery_profile are the plain "
            "strings the schema names, with no quotation marks inside them. Everything about the next move (kind, "
            "purpose, primary_prompt, rationale, goal_ref, decision, options, required_context_refs) goes inside the "
            "intervention object, never beside it. Those eight are the intervention's only fields, and a record has "
            "only the fields its schema lists: never invent another field. Anything more you want to say about the "
            "move belongs in its rationale. An update's data has only the fields of its operation (one you have "
            "nothing for is null or left out): " + "; ".join(f"record_{kind}: {', '.join(sorted(fields))}"
                                                          for kind, fields in FIELDS.items()) + ". "
            "The move refers to the goal through goal_ref: the goal's ref, or its "
            "temporary_id when this proposal records it (such as \"goal\"), or null when there is none. The "
            "intervention's decision and options are optional: leave them out rather than send them empty or null. "
            "intervention is an "
            "object and proposed_updates an array of update objects, never strings holding JSON. The shape, with "
            "your own values in place of the angle brackets:\n"
            f"{{\"schema_version\": \"{SCHEMA}\", \"delivery_profile\": \"{PROFILE}\", \"request_id\": \"<input ID>\", "
            "\"base_revision\": <revision>, \"intervention\": {\"kind\": \"<question, recommendation or stop>\", "
            "\"purpose\": \"<why this move now>\", \"primary_prompt\": \"<the one question or recommendation>\", "
            "\"rationale\": \"<plain reasons>\", \"goal_ref\": \"<the goal's ref or temporary_id, or null>\", "
            "\"required_context_refs\": [<refs, or temporary_ids declared in this proposal, it relies on>]}, "
            "\"proposed_updates\": [<update objects, as the procedure describes>]}\n"
            "This is a data return channel, not an executable application capability.")

    @staticmethod
    def _output_settings(environ):
        """max_tokens and effort from the environment, with what is wrong with them."""
        problems, max_tokens = [], DEFAULT_MAX_TOKENS
        raw = (environ.get("REASON_COMMONS_ANTHROPIC_MAX_TOKENS") or "").strip()
        if raw:
            if re.fullmatch(r"[1-9][0-9]{0,6}", raw):
                max_tokens = int(raw)
            else:
                problems.append("REASON_COMMONS_ANTHROPIC_MAX_TOKENS must be a positive whole number")
        effort = (environ.get("REASON_COMMONS_ANTHROPIC_EFFORT") or "").strip().lower() or None
        if effort is not None and effort not in EFFORTS + ("default",):
            problems.append("REASON_COMMONS_ANTHROPIC_EFFORT must be one of " + ", ".join(EFFORTS + ("default",)))
            effort = None
        return max_tokens, effort, problems

    @classmethod
    def from_env(cls, model=None, base_url=None, usage=None):
        max_tokens, effort, problems = cls._output_settings(os.environ)
        if problems:
            raise ValueError(problems[0])
        return cls(model=model or os.environ.get("REASON_COMMONS_ANTHROPIC_MODEL") or DEFAULT_MODEL,
                   base_url=base_url or os.environ.get("REASON_COMMONS_ANTHROPIC_URL", "https://api.anthropic.com/v1"),
                   api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
                   timeout=float(os.environ.get("REASON_COMMONS_ANTHROPIC_TIMEOUT", "120")),
                   max_tokens=max_tokens, effort=effort, usage=usage)

    @staticmethod
    def describe_settings(model=None, base_url=None, environ=os.environ):
        """Resolved configuration for a readiness check; reads the environment only."""
        env_model = environ.get("REASON_COMMONS_ANTHROPIC_MODEL") or None
        env_url = environ.get("REASON_COMMONS_ANTHROPIC_URL") or None
        present = bool((environ.get("ANTHROPIC_API_KEY") or "").strip())
        max_tokens, effort, problems = AnthropicConsultant._output_settings(environ)
        if not present:
            problems.insert(0, "ANTHROPIC_API_KEY is not set; export it in the environment that starts reason-commons")
        return {"model": model or env_model or DEFAULT_MODEL,
                "model_source": "explicit" if model else "environment" if env_model else "default",
                "endpoint": base_url or env_url or "https://api.anthropic.com/v1",
                "credential": {"variable": "ANTHROPIC_API_KEY", "required": True, "present": present},
                "max_tokens": max_tokens,
                "effort": effort or f"{DEFAULT_EFFORT} where the model supports it",
                "problems": problems}

    @property
    def version(self):
        # Before the model is resolved, the effort is the configured one ("auto" when unset).
        effort = (self._sent_effort or "default") if self._resolved_model else (self.effort or "auto")
        return (f"anthropic/adapter=4/prompt=9/schema=3/model={self._resolved_model or self.model}"
                f"/max_tokens={self.max_tokens}/effort={effort}/proposal=tool-auto"
                f"/procedure={sha256(self._procedure.encode()).hexdigest()[:16]}"
                f"/context={sha256(self._context.encode()).hexdigest()[:16]}")

    def _request(self, path, payload=None):
        if not self._api_key:
            raise AnthropicError("Set ANTHROPIC_API_KEY before consulting")
        body = None if payload is None else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if body is not None and len(body) > MAX_REQUEST_BYTES:
            raise AnthropicError("Complete case exceeds request size limit; context was not truncated")
        request = Request(self.base_url + path, data=body, headers={
            "Content-Type": "application/json", "Accept": "application/json",
            "x-api-key": self._api_key, "anthropic-version": "2023-06-01"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                content = response.read(MAX_RESPONSE_BYTES + 1)
            if len(content) > MAX_RESPONSE_BYTES:
                raise ConsultantResponseError("Anthropic response exceeds size limit")
            return decode_json(content)
        except HTTPError as exc:
            raise AnthropicError(f"Anthropic HTTP request failed (status {exc.code})",
                                 category="http_error", http_status=exc.code) from None
        except (URLError, OSError, TimeoutError, HTTPException) as exc:
            category = "timeout" if isinstance(exc, TimeoutError) or isinstance(getattr(exc, "reason", None), TimeoutError) else "connection"
            # urllib wraps a failure to connect or send in URLError; anything else came while waiting for the reply.
            raise AnthropicError("Anthropic unavailable or request timed out", category=category,
                                 sent=not isinstance(exc, URLError)) from None
        except (ValueError, UnicodeError, RecursionError):
            raise ConsultantResponseError("Anthropic returned invalid JSON") from None

    def list_models(self):
        """Models this key may use, newest first, as (id, display name); also checks the key works."""
        value = self._request("/models?limit=100")
        if not isinstance(value, dict) or not isinstance(value.get("data"), list):
            raise AnthropicError("Anthropic returned an invalid models response")
        models = []
        for item in value["data"]:
            if (isinstance(item, dict) and isinstance(item.get("id"), str)
                    and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", item["id"])):
                name = item.get("display_name") if isinstance(item.get("display_name"), str) else item["id"]
                models.append((item["id"], name))
        return models

    def model_metadata(self):
        """Verify account access and resolve the exact requested model, without inference."""
        value = self._request("/models/" + self.model)
        if (not isinstance(value, dict) or not isinstance(value.get("id"), str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value["id"])):
            raise AnthropicError("Anthropic returned invalid model metadata")
        self._sent_effort = self._effort_for(value)
        self._resolved_model = value["id"]
        return value

    def _effort_for(self, metadata):
        """The effort to send, from the model's reported capabilities; None sends none."""
        if self.effort == "default":
            return None
        level = self.effort or DEFAULT_EFFORT
        capabilities = metadata.get("capabilities")
        reported = capabilities.get("effort") if isinstance(capabilities, dict) else None
        if not isinstance(reported, dict) or "supported" not in reported:
            # Unknown support: send only an effort someone chose; the API refuses one it cannot use.
            return self.effort
        if _supported(reported) and _supported(reported.get(level)):
            return level
        if self.effort is None:
            return None
        raise AnthropicError(f"Model {metadata['id']} does not support effort {level}; "
                             "choose another level or 'default' in REASON_COMMONS_ANTHROPIC_EFFORT")

    def _payload(self, request):
        if self._resolved_model is None:
            self.model_metadata()
        payload = {"model": self._resolved_model, "max_tokens": self.max_tokens,
                   "system": self._procedure + "\n\nDOMAIN CONTEXT\n" + self._context,
                   "messages": [{"role": "user", "content": json.dumps(request, ensure_ascii=False, allow_nan=False)}],
                   "stream": False,
                   "tools": [{"name": "submit_proposal", "description":
                       "Return the complete reasoning proposal using the supplied case and sources. "
                       "This tool returns data for validation; it does not save or execute anything.",
                       "input_schema": request_schema(request)}],
                   "tool_choice": {"type": "auto", "disable_parallel_tool_use": True}}
        if self._sent_effort:
            payload["output_config"] = {"effort": self._sent_effort}
        return payload

    def count_tokens(self, request):
        """Count the complete consulting prompt without inference or case writes."""
        payload = self._payload(request)
        for key in ("max_tokens", "stream", "output_config"):
            payload.pop(key, None)
        value = self._request("/messages/count_tokens", payload)
        if not isinstance(value, dict) or type(value.get("input_tokens")) is not int or value["input_tokens"] < 0:
            raise AnthropicError("Anthropic returned an invalid token count")
        return value["input_tokens"]

    def _report(self, request, outcome, usage=None, model=None):
        """Tell the usage sink what one request cost. A sink that fails never costs the reply."""
        if self.usage is None:
            return
        try:
            self.usage({"provider": "anthropic", "model": model or self._resolved_model or self.model,
                        "outcome": outcome, "tokens": usage_tokens(usage),
                        "case_id": (request.get("case") or {}).get("case_id"),
                        "request_id": (request.get("input") or {}).get("request_id")})
        except Exception:
            pass

    def propose(self, request):
        payload = self._payload(request)
        self.last_usage, self.last_repairs = None, []
        try:
            response = self._request("/messages", payload)
        except AnthropicError as exc:
            if exc.sent:  # no reply, but the request was made: it may still be billed
                self._report(request, "no_reply")
            raise
        except ConsultantResponseError:  # a reply that cannot be read, so its tokens are not known
            self._report(request, "no_reply")
            raise
        if not isinstance(response, dict):
            self._report(request, "no_reply")
            raise ConsultantResponseError("Anthropic returned a different or unidentified response model")
        usage = response.get("usage")
        if response.get("model") != self._resolved_model:
            served = response.get("model")
            # Billed all the same, at the price of the model that answered.
            self._report(request, "other_model", usage,
                         served if isinstance(served, str) and MODEL_ID.fullmatch(served) else "unknown")
            raise ConsultantResponseError("Anthropic returned a different or unidentified response model")
        if isinstance(usage, dict):
            self.last_usage = {key: usage[key] for key in USAGE_FIELDS
                               if type(usage.get(key)) is int and usage[key] >= 0}
        # Each reason names only the adapter's own words and provider enum values, never response text.
        stop, blocks = response.get("stop_reason"), response.get("content")
        if stop == "max_tokens":
            self._report(request, "max_tokens", usage)
            raise ConsultantResponseError(f"Anthropic stopped at max_tokens ({self.max_tokens}) before finishing "
                                          "the proposal")
        if stop == "refusal":
            self._report(request, "refusal", usage)
            details = response.get("stop_details")
            category = _label(details.get("category")) if isinstance(details, dict) else "unknown"
            raise ConsultantResponseError(f"Anthropic declined the request (refusal, category {category})")
        calls = [block for block in blocks if isinstance(block, dict)
                 and block.get("type") == "tool_use"] if isinstance(blocks, list) else []
        problem = None
        if stop != "tool_use":
            problem = f"Anthropic replied without a proposal (stop_reason {_label(stop)})"
        elif len(calls) != 1:
            problem = f"Anthropic returned {len(calls)} tool calls instead of one proposal"
        elif calls[0].get("name") != "submit_proposal":
            problem = "Anthropic called a tool other than submit_proposal"
        elif not isinstance(calls[0].get("input"), dict):
            problem = "Anthropic's proposal call carried no proposal object"
        if problem:
            self._report(request, "no_proposal", usage)
            raise ConsultantResponseError(problem)
        envelope = {"schema_version": SCHEMA, "delivery_profile": PROFILE,
                    "request_id": request["input"]["request_id"], "base_revision": request["input"]["base_revision"]}
        proposal, self.last_repairs = undo_transport_slips(calls[0]["input"], envelope)
        self._report(request, "proposal", usage)
        return proposal
