"""Optional language model for C.6.1 Explanation Engine (ADR-0001: LM Studio, run locally).

LM Studio serves an OpenAI-compatible API on the investor's own machine, so
profile data never leave it. WealthPilot uses a model only when the
environment names one:

    WEALTHPILOT_LLM_MODEL     model identifier as LM Studio shows it (required to enable)
    WEALTHPILOT_LLM_BASE_URL  default http://localhost:1234/v1
    WEALTHPILOT_LLM_TIMEOUT   seconds, default 30

Without WEALTHPILOT_LLM_MODEL, F.6.1 uses its deterministic template. Every
failure here raises LanguageModelError, and F.6.1 then falls back to the
template (SPEC.md Model Response Contract).
"""

import json
import os
import urllib.error
import urllib.request
from typing import Protocol

DEFAULT_BASE_URL = "http://localhost:1234/v1"
DEFAULT_TIMEOUT = 30.0
MAX_TOKENS = 900


class LanguageModelError(Exception):
    """The model could not be reached, or did not return one JSON object."""


class LanguageModel(Protocol):
    name: str

    def complete_json(self, system: str, user: str, schema: dict) -> dict: ...


class LmStudioModel:
    """A model loaded in LM Studio, called through its OpenAI-compatible chat endpoint."""

    def __init__(self, model: str, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.name = f"{model} (LM Studio)"
        # LM Studio runs on this machine, so a system proxy must never be used.
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def complete_json(self, system: str, user: str, schema: dict) -> dict:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.2,
            "max_tokens": MAX_TOKENS,
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "investment_plan_explanation", "strict": True, "schema": schema},
            },
        }
        try:
            reply = self._post(body)
        except urllib.error.HTTPError as error:
            if error.code != 400:
                raise LanguageModelError(f"LM Studio answered HTTP {error.code}") from error
            # some models or server versions do not support structured output
            body.pop("response_format")
            try:
                reply = self._post(body)
            except urllib.error.HTTPError as retry_error:
                raise LanguageModelError(f"LM Studio answered HTTP {retry_error.code}") from retry_error
        try:
            text = reply["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise LanguageModelError("LM Studio's reply has no message content") from error
        return parse_json_object(text)

    def _post(self, body: dict) -> dict:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError:
            raise
        except (OSError, ValueError) as error:  # unreachable, timed out, or not JSON
            raise LanguageModelError(f"LM Studio could not be used: {error}") from error


def parse_json_object(text) -> dict:
    """The JSON object in a model reply, allowing a code fence or a sentence around it."""
    if not isinstance(text, str):
        raise LanguageModelError("the reply is not text")
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise LanguageModelError("the reply contains no JSON object")
    try:
        value = json.loads(text[start : end + 1])
    except ValueError as error:
        raise LanguageModelError(f"the reply is not valid JSON: {error}") from error
    if not isinstance(value, dict):
        raise LanguageModelError("the reply is not a JSON object")
    return value


def language_model_from_environment(environ=None) -> LmStudioModel | None:
    """The configured LM Studio model, or None to use the template."""
    environ = os.environ if environ is None else environ
    model = environ.get("WEALTHPILOT_LLM_MODEL", "").strip()
    if not model:
        return None
    try:
        timeout = float(environ.get("WEALTHPILOT_LLM_TIMEOUT", DEFAULT_TIMEOUT))
    except ValueError:
        timeout = DEFAULT_TIMEOUT
    return LmStudioModel(model, environ.get("WEALTHPILOT_LLM_BASE_URL", DEFAULT_BASE_URL), timeout)
