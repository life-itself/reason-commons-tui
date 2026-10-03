"""Anthropic Messages API implementation of the existing Consultant port.

One proposal tool call is data, never permission to execute an app tool.
The application validates and publishes it. No retries or provider fallback.
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


MAX_REQUEST_BYTES = 4 * 1024 * 1024
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
DEFAULT_MODEL = "claude-sonnet-5-5"


class AnthropicError(RuntimeError):
    """Safe provider diagnostics; never expose credentials or response bodies."""

    def __init__(self, message, category="configuration", http_status=None):
        super().__init__(message)
        self.category, self.http_status = category, http_status


class AnthropicConsultant:
    def __init__(self, model=DEFAULT_MODEL, base_url="https://api.anthropic.com/v1",
                 api_key=None, timeout=120.0, max_tokens=4096):
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
        if api_key is not None and (not isinstance(api_key, str) or not api_key.strip()
                                    or "\n" in api_key or "\r" in api_key):
            raise ValueError("Invalid Anthropic API key")
        self.model, self.timeout, self.max_tokens = model, timeout, max_tokens
        self.base_url = urlunsplit((parts.scheme, parts.netloc, "/v1", "", ""))
        self._api_key, self._resolved_model = api_key, None
        self._opener = build_opener(ProxyHandler({}), NoRedirect())
        self._context = files("reason_commons.domain").joinpath("CONTEXT.md").read_text(encoding="utf-8")
        self._procedure = files("reason_commons.adapters").joinpath("prompts/consultant.md").read_text(encoding="utf-8")
        self._procedure += ("\n\nANTHROPIC TRANSPORT\nReturn the complete proposal by calling submit_proposal "
                            "exactly once. Supply the proposal as its input, rather than emitting JSON as plain text. "
                            "This is a data return channel, not an executable application capability.")

    @classmethod
    def from_env(cls, model=None, base_url=None):
        return cls(model=model or os.environ.get("REASON_COMMONS_ANTHROPIC_MODEL") or DEFAULT_MODEL,
                   base_url=base_url or os.environ.get("REASON_COMMONS_ANTHROPIC_URL", "https://api.anthropic.com/v1"),
                   api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
                   timeout=float(os.environ.get("REASON_COMMONS_ANTHROPIC_TIMEOUT", "120")))

    @property
    def version(self):
        return (f"anthropic/adapter=1/prompt=5/schema=1/model={self._resolved_model or self.model}"
                f"/max_tokens={self.max_tokens}/proposal=tool-auto"
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
            raise AnthropicError("Anthropic unavailable or request timed out", category=category) from None
        except (ValueError, UnicodeError, RecursionError):
            raise ConsultantResponseError("Anthropic returned invalid JSON") from None

    def model_metadata(self):
        """Verify account access and resolve the exact requested model, without inference."""
        value = self._request("/models/" + self.model)
        if (not isinstance(value, dict) or not isinstance(value.get("id"), str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value["id"])):
            raise AnthropicError("Anthropic returned invalid model metadata")
        self._resolved_model = value["id"]
        return value

    def _payload(self, request):
        if self._resolved_model is None:
            self.model_metadata()
        return {"model": self._resolved_model, "max_tokens": self.max_tokens,
                   "system": self._procedure + "\n\nDOMAIN CONTEXT\n" + self._context,
                   "messages": [{"role": "user", "content": json.dumps(request, ensure_ascii=False, allow_nan=False)}],
                   "stream": False,
                   "tools": [{"name": "submit_proposal", "description":
                       "Return the complete reasoning proposal using the supplied case and sources. "
                       "This tool returns data for validation; it does not save or execute anything.",
                       "input_schema": request_schema(request)}],
                   "tool_choice": {"type": "auto", "disable_parallel_tool_use": True}}

    def count_tokens(self, request):
        """Count the complete consulting prompt without inference or case writes."""
        payload = self._payload(request)
        for key in ("max_tokens", "stream"):
            payload.pop(key)
        value = self._request("/messages/count_tokens", payload)
        if not isinstance(value, dict) or type(value.get("input_tokens")) is not int or value["input_tokens"] < 0:
            raise AnthropicError("Anthropic returned an invalid token count")
        return value["input_tokens"]

    def propose(self, request):
        payload = self._payload(request)
        response = self._request("/messages", payload)
        if not isinstance(response, dict) or response.get("model") != self._resolved_model:
            raise ConsultantResponseError("Anthropic returned a different or unidentified response model")
        blocks = response.get("content")
        if response.get("stop_reason") != "tool_use" or not isinstance(blocks, list):
            raise ConsultantResponseError("Anthropic did not finish a complete proposal")
        calls = [block for block in blocks if isinstance(block, dict) and block.get("type") == "tool_use"]
        if (len(calls) != 1 or calls[0].get("name") != "submit_proposal"
                or not isinstance(calls[0].get("input"), dict)):
            raise ConsultantResponseError("Anthropic returned an invalid or incomplete proposal")
        return calls[0]["input"]
