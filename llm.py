"""Minimal DeepSeek chat completion client using the OpenAI SDK.

Reads the API key from the ``DEEPSEEK_API_KEY`` env var (or ``.env`` via python-dotenv).

Endpoint (DeepSeek, OpenAI-compatible):
    POST https://api.deepseek.com/v1/chat/completions
Auth: ``Authorization: Bearer <DEEPSEEK_API_KEY>``
Default model: ``deepseek-chat``
"""

from __future__ import annotations

import os
from typing import Any

# Load .env file if present (silently ignored if python-dotenv is absent).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from openai.types.chat import ChatCompletionMessageParam


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEEPSEEK_API_URL_DEFAULT = "https://api.deepseek.com/v1"
_DEEPSEEK_DEFAULT_MODEL_DEFAULT = "deepseek-chat"
_DEEPSEEK_TIMEOUT_SEC_DEFAULT = 30.0


class DeepSeekError(RuntimeError):
    """Raised on any failure calling DeepSeek."""


# ---------------------------------------------------------------------------
# Real client
# ---------------------------------------------------------------------------

class DeepSeekClient:
    """Calls the DeepSeek chat-completion endpoint using the OpenAI SDK.

    Raises ``DeepSeekError`` at construction time if ``DEEPSEEK_API_KEY`` is missing.
    """

    mock: bool = False

    def __init__(self) -> None:
        # Read env at construction time so tests can monkeypatch overrides.
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        self.api_url = os.environ.get("DEEPSEEK_API_URL", _DEEPSEEK_API_URL_DEFAULT).strip()
        self.model = os.environ.get("DEEPSEEK_MODEL", _DEEPSEEK_DEFAULT_MODEL_DEFAULT).strip()
        self.timeout = float(os.environ.get("DEEPSEEK_TIMEOUT", str(_DEEPSEEK_TIMEOUT_SEC_DEFAULT)))
        if not self.api_key:
            raise DeepSeekError("DEEPSEEK_API_KEY environment variable is not set")
        # DEBUG: Log key prefix (never log the full key)
        import logging
        logging.getLogger(__name__).debug(
            f"DeepSeekClient init: API_URL={self.api_url}, MODEL={self.model}, "
            f"KEY_PREFIX={self.api_key[:4]}... if len(self.api_key) > 4 else 'TOO_SHORT'"
        )

        # Initialize the OpenAI client with the custom base URL
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url,
            timeout=self.timeout,
        )

    def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> str:
        full_messages: list[ChatCompletionMessageParam] = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)  # type: ignore[arg-type]

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return self._extract(response.model_dump())
        except APITimeoutError as e:
            raise DeepSeekError(f"timeout after {self.timeout}s") from e
        except RateLimitError as e:
            raise DeepSeekError(f"rate limit exceeded: {e}") from e
        except APIError as e:
            raise DeepSeekError(f"API error: {e}") from e

    @staticmethod
    def _extract(payload: dict[str, Any]) -> str:
        """Pull ``choices[0].message.content`` from an OpenAI-style payload."""
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise DeepSeekError(f"unexpected payload shape: {payload}") from e


# ---------------------------------------------------------------------------
# Mock client — opt-in, for local dev / sandbox / offline testing
# ---------------------------------------------------------------------------

_DEFAULT_SYSTEM_MOCK = (
    "Tu es un assistant thérapeutique bienveillant et professionnel, "
    "spécialisé en EMDR, en théorie de l'attachement, en théorie polyvagale "
    "et en intelligence relationnelle. Réponds de manière concise, empathique "
    "et fondée sur ces approches."
)


class _DeepSeekMockClient:
    """No-network client that returns a pedagogical stub. ``DEEPSEEK_MOCK=1`` selects it."""

    mock: bool = True

    def __init__(self) -> None:
        self.api_key = "mock"
        self.api_url = "<mock>"
        self.model = "mock"
        self.timeout = 0.0
        self._system = _DEFAULT_SYSTEM_MOCK

    def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> str:
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = (m.get("content") or "").lower()
                break
        if "emdr" in user_msg:
            return (
                "[Mode mock — DeepSeek] L'EMDR (Eye Movement Desensitization and "
                "Reprocessing) est une approche thérapeutique développée par "
                "Francine Shapiro, utilisée pour traiter les traumatismes psychiques."
            )
        if "intelligence relationnelle" in user_msg or "le doze" in user_msg:
            return (
                "[Mode mock — DeepSeek] L'Intelligence Relationnelle, modélisée par "
                "le Dr François Le Doze, explore la manière dont le cerveau social "
                "influences nos liens aux autres."
            )
        return (
            "[Mode mock — DeepSeek] Merci pour votre message. "
            "Cela sera traité par le système DeepSeek une fois configuré."
        )


def make_client() -> DeepSeekClient | _DeepSeekMockClient:
    """Factory: return a mock client when ``DEEPSEEK_MOCK=1``, else a real ``DeepSeekClient``.

    The real client raises ``DeepSeekError`` if the key is missing; callers that
    want graceful fallback should catch it and call ``make_client`` again with
    ``DEEPSEEK_MOCK`` forced.
    """
    if os.environ.get("DEEPSEEK_MOCK", "").strip().lower() in ("1", "true", "yes"):
        return _DeepSeekMockClient()
    return DeepSeekClient()


# ---------------------------------------------------------------------------
# Backwards-compatibility aliases (deprecated, use make_client)
# ---------------------------------------------------------------------------

# Aliases for code that references MiMoClient/MiMoError
MiMoClient = DeepSeekClient
MiMoError = DeepSeekError
_MiMoMockClient = _DeepSeekMockClient


def MiMoClient_compat() -> DeepSeekClient | _DeepSeekMockClient:
    """Deprecated: use make_client() instead."""
    return make_client()
