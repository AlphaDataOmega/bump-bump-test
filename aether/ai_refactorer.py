"""LLM-assisted refactor suggestions for AETHER.

This module provides a minimal client for large language models so that
AETHER can request rewrite suggestions for functions flagged as risky.
Configuration is read from ``.aether/config.json`` and looks like::

    {
      "llm_backend": "openai:gpt-4",
      "max_calls_per_run": 5,
      "rewrite_threshold": 0.75
    }

``llm_backend`` is formatted as ``"<provider>:<model>"``.  Supported
providers are ``openai`` and ``ollama``.  All dependencies are optional;
:class:`LLMError` is raised when the backend cannot be used.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class LLMError(RuntimeError):
    """Raised when the LLM backend is misconfigured or unavailable."""


@dataclass
class FunctionContext:
    """Minimal context required to request a refactor suggestion.

    Attributes
    ----------
    name:
        Function name.
    source:
        Source code for the function.
    docstring:
        Existing docstring or empty string.
    calls:
        Names of functions called by ``source``.
    risk:
        Float between 0 and 1 representing risk score.
    """

    name: str
    source: str
    docstring: str
    calls: Iterable[str]
    risk: float


@dataclass
class RefactorSuggestion:
    """Refactor suggestion returned by the LLM."""

    outline: str
    new_name: Optional[str] = None
    docstring: Optional[str] = None


class AIRefactorer:
    """Thin LLM client used to fetch refactor suggestions."""

    def __init__(self, config_path: Path | str = Path(".aether/config.json")) -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config()
        backend = self.config.get("llm_backend")
        self.backend_type: Optional[str] = None
        self.model: Optional[str] = None
        if backend:
            self.backend_type, self.model = backend.split(":", 1)

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        with self.config_path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def _call_openai(self, prompt: str) -> str:
        try:
            import openai  # type: ignore
        except ImportError as exc:
            raise LLMError("openai package is not installed") from exc
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OPENAI_API_KEY environment variable not set")
        openai.api_key = api_key
        response = openai.ChatCompletion.create(  # type: ignore[attr-defined]
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response["choices"][0]["message"]["content"].strip()

    def _call_ollama(self, prompt: str) -> str:
        data = json.dumps({"model": self.model, "prompt": prompt}).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:  # pragma: no cover - network
            payload = json.loads(resp.read().decode("utf-8"))
        return payload.get("response", "")

    def _request(self, prompt: str) -> str:
        if self.backend_type == "openai":
            return self._call_openai(prompt)
        if self.backend_type == "ollama":
            return self._call_ollama(prompt)
        raise LLMError("No llm_backend configured")

    def suggest_refactor(self, ctx: FunctionContext) -> RefactorSuggestion:
        """Return a refactor suggestion for ``ctx``.

        The LLM is prompted to produce JSON containing optional ``outline``,
        ``name`` and ``docstring`` fields.  If the response cannot be parsed,
        the raw text is returned as the ``outline``.
        """

        prompt = (
            "This function has high churn and poor documentation.\n\n"
            f"Function:\n{ctx.source}\n\n"
            f"Docstring:\n{ctx.docstring or 'None'}\n\n"
            f"Call graph: {list(ctx.calls)}\n\n"
            "Suggest how this function could be refactored or renamed. "
            "Respond in JSON with keys 'outline', 'name', and 'docstring'."
        )
        text = self._request(prompt)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"outline": text}
        return RefactorSuggestion(
            outline=data.get("outline", ""),
            new_name=data.get("name"),
            docstring=data.get("docstring"),
        )


__all__ = [
    "AIRefactorer",
    "FunctionContext",
    "RefactorSuggestion",
    "LLMError",
]
