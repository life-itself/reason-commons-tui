"""LM Studio's local HTTP API implements the replaceable Consultant port.

No hosted fallback, implicit provider retries, credentials in case state, or
provider-specific behavior in the application/domain.
"""

from importlib.resources import files
from hashlib import sha256
from http.client import HTTPException
import json
import math
import os
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import ProxyHandler, Request, build_opener

from reason_commons.application.ports import ConsultantResponseError
from reason_commons.adapters.provider_support import NoRedirect, decode_json, request_schema


MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_REQUEST_BYTES = 4 * 1024 * 1024


class LMStudioError(RuntimeError):
    """Sanitized connection/configuration failure; never includes token or body."""

    def __init__(self, message, category="configuration", http_status=None):
        super().__init__(message)
        self.category = category
        self.http_status = http_status


class LMStudioConsultant:
    def __init__(self, model: Optional[str] = None, base_url="http://127.0.0.1:1234/v1",
                 api_key: Optional[str] = None, timeout=120.0, max_tokens=4096, temperature=0.2):
        parts = urlsplit(base_url)
        if (parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password
                or parts.query or parts.fragment or parts.path.rstrip("/") not in {"", "/v1"}):
            raise ValueError("Use a server URL with an optional /v1 path and no embedded credentials")
        self.base_url = urlunsplit((parts.scheme, parts.netloc, "/v1", "", ""))
        if model is not None and (not isinstance(model, str) or not model.strip()):
            raise ValueError("Model must be a nonempty served model ID")
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Timeout must be a positive finite number of seconds")
        if type(max_tokens) is not int or max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")
        if not isinstance(temperature, (int, float)) or not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        if api_key is not None and (not isinstance(api_key, str) or "\n" in api_key or "\r" in api_key):
            raise ValueError("Invalid API token")
        self.model = model
        self._verified_model = None
        self.timeout, self.max_tokens, self.temperature = timeout, max_tokens, temperature
        self._api_key = api_key
        self._opener = build_opener(ProxyHandler({}), NoRedirect())
        # Freeze procedure/context for this adapter session. Editing files while
        # a run is active must not silently change its consulting policy.
        self._context = files("reason_commons.domain").joinpath("CONTEXT.md").read_text(encoding="utf-8")
        self._procedure = files("reason_commons.adapters").joinpath("prompts/consultant.md").read_text(encoding="utf-8")

    @classmethod
    def from_env(cls, model: Optional[str] = None, base_url: Optional[str] = None):
        """Runtime configuration only; tokens and endpoints never enter case files."""
        return cls(model=model if model is not None else os.environ.get("REASON_COMMONS_LM_STUDIO_MODEL") or None,
                   base_url=base_url if base_url is not None else os.environ.get("REASON_COMMONS_LM_STUDIO_URL", "http://127.0.0.1:1234/v1"),
                   api_key=os.environ.get("LM_STUDIO_API_TOKEN") or None,
                   timeout=float(os.environ.get("REASON_COMMONS_LM_STUDIO_TIMEOUT", "120")))

    @staticmethod
    def describe_settings(model=None, base_url=None, environ=os.environ):
        """Resolved configuration for a readiness check; reads the environment only."""
        env_model = environ.get("REASON_COMMONS_LM_STUDIO_MODEL") or None
        env_url = environ.get("REASON_COMMONS_LM_STUDIO_URL") or None
        return {"model": model or env_model or "the single chat model the server advertises",
                "model_source": "explicit" if model else "environment" if env_model else "auto",
                "endpoint": base_url or env_url or "http://127.0.0.1:1234/v1",
                "credential": {"variable": "LM_STUDIO_API_TOKEN", "required": False,
                               "present": bool((environ.get("LM_STUDIO_API_TOKEN") or "").strip())},
                "problems": []}

    @property
    def version(self):
        return (f"lm-studio/adapter=5/prompt=8/schema=3/model={self.model or 'unresolved'}"
                f"/temperature={self.temperature}/max_tokens={self.max_tokens}"
                f"/procedure={sha256(self._procedure.encode()).hexdigest()[:16]}"
                f"/context={sha256(self._context.encode()).hexdigest()[:16]}")

    def _request(self, path, payload=None, native=False):
        content = None if payload is None else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if content is not None and len(content) > MAX_REQUEST_BYTES:
            raise LMStudioError("Complete case exceeds request size limit; context was not truncated")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = "Bearer " + self._api_key
        base = self.base_url[:-3] + "/api/v1" if native else self.base_url
        request = Request(base + path, data=content, headers=headers)
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ConsultantResponseError("LM Studio response exceeds size limit")
            return decode_json(body)
        except HTTPError as exc:
            raise LMStudioError(f"LM Studio HTTP request failed (status {exc.code})",
                                category="http_error", http_status=exc.code) from None
        except (URLError, OSError, TimeoutError, HTTPException) as exc:
            category = "timeout" if isinstance(exc, TimeoutError) or isinstance(getattr(exc, "reason", None), TimeoutError) else "connection"
            raise LMStudioError("LM Studio unavailable or request timed out", category=category) from None
        except (ValueError, UnicodeError, RecursionError):
            raise ConsultantResponseError("LM Studio returned invalid JSON") from None

    def list_models(self):
        response = self._request("/models")
        if not isinstance(response, dict) or not isinstance(response.get("data"), list):
            raise LMStudioError("LM Studio returned an invalid models response")
        models = []
        for item in response["data"]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
                raise LMStudioError("LM Studio returned an invalid model identifier")
            if item["id"] not in models:
                models.append(item["id"])
        return models

    def chat_completion(self, payload):
        """HTTP capability shared with the separate skill agent adapter.

        This does not apply a case proposal or expose persistence. Each consumer
        validates its own response contract; no automatic generation retry.
        """
        self._resolve_model()
        if payload.get("model") != self.model:
            raise LMStudioError("Chat payload must use the configured verified model")
        response = self._request("/chat/completions", payload)
        if not isinstance(response, dict) or response.get("model") != self.model:
            raise ConsultantResponseError("LM Studio returned a different or unidentified response model")
        return response

    def _resolve_model(self):
        if self.model is not None and self._verified_model == self.model:
            return
        available = self.list_models()
        if self.model is None:
            if len(available) != 1:
                raise LMStudioError("Choose a model explicitly: server must advertise exactly one model for automatic selection")
            self.model = available[0]
        elif self.model not in available:
            raise LMStudioError("Configured model is not advertised by LM Studio; generation did not start",
                                category="model_unavailable")
        self._verified_model = self.model

    def model_metadata(self):
        """Read native model/configuration metadata for opt-in reproducibility."""
        return self._request("/models", native=True)

    def propose(self, request):
        self._resolve_model()
        schema = request_schema(request)
        payload = {"model": self.model, "messages": [
            {"role": "system", "content": self._procedure + "\n\nDOMAIN CONTEXT\n" + self._context},
            {"role": "user", "content": json.dumps(request, ensure_ascii=False, allow_nan=False)}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "reason_commons_proposal", "strict": True, "schema": schema}},
            "stream": False, "temperature": self.temperature, "max_tokens": self.max_tokens}
        response = self.chat_completion(payload)
        try:
            choice = response["choices"][0]
            if choice.get("finish_reason") != "stop" or choice["message"].get("refusal"):
                raise ConsultantResponseError("LM Studio did not finish a complete proposal")
            content = choice["message"]["content"]
            if not isinstance(content, str):
                raise ConsultantResponseError("LM Studio returned no proposal text")
            proposal = decode_json(content)
            if not isinstance(proposal, dict):
                raise ConsultantResponseError("LM Studio proposal must be an object")
            return proposal
        except (KeyError, IndexError, TypeError, ValueError, AttributeError, RecursionError):
            raise ConsultantResponseError("LM Studio returned an invalid or incomplete proposal") from None
