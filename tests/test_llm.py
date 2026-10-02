"""Tests for server/llm.py — DeepSeek client (live API).

The real DeepSeek client is exercised against the configured endpoint. Tests
skip gracefully when ``DEEPSEEK_API_KEY`` is missing or the network is
unreachable, so ``pytest`` stays green in sandboxes / CI without secrets.

Set ``DEEPSEEK_MOCK=1`` to run these tests against the mock client explicitly.
"""

from __future__ import annotations

import os
import socket

import pytest

from llm import DeepSeekClient, DeepSeekError, _DeepSeekMockClient, make_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_api_key() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())


def _endpoint_reachable(url: str, timeout: float = 2.0) -> bool:
    """Best-effort TCP probe of the API host. Returns False on any failure."""
    try:
        host = url.split("://", 1)[1].split("/", 1)[0]
        if ":" in host:
            host, port = host.rsplit(":", 1)
            port = int(port)
        else:
            port = 443
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


@pytest.fixture
def real_client() -> DeepSeekClient:
    """Build a real DeepSeekClient; skip the test if the key is missing."""
    if not _has_api_key():
        pytest.skip("DEEPSEEK_API_KEY not set — live API tests skipped")
    return DeepSeekClient()


# ---------------------------------------------------------------------------
# Construction & config
# ---------------------------------------------------------------------------

def test_constructor_requires_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(DeepSeekError, match="DEEPSEEK_API_KEY"):
        DeepSeekClient()


def test_constructor_accepts_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-xyz")
    c = DeepSeekClient()
    assert c.api_key == "test-key-xyz"
    assert c.mock is False
    assert c.model == "deepseek-chat"
    assert c.api_url.startswith("https://")


def test_constructor_respects_overrides(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    monkeypatch.setenv("DEEPSEEK_API_URL", "https://example.com/v1")
    c = DeepSeekClient()
    assert c.model == "deepseek-reasoner"
    assert c.api_url == "https://example.com/v1"


# ---------------------------------------------------------------------------
# Mock factory (opt-in)
# ---------------------------------------------------------------------------

def test_make_client_returns_real_when_no_mock(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_MOCK", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")
    c = make_client()
    assert isinstance(c, DeepSeekClient)
    assert c.mock is False


def test_make_client_returns_mock_when_flag_set(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_MOCK", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")
    c = make_client()
    assert isinstance(c, _DeepSeekMockClient)
    assert c.mock is True


def test_mock_client_emdr():
    c = _DeepSeekMockClient()
    out = c.chat([{"role": "user", "content": "C'est quoi l'EMDR ?"}])
    assert "EMDR" in out
    assert "Shapiro" in out


def test_mock_client_intelligence_relationnelle():
    c = _DeepSeekMockClient()
    out = c.chat([{"role": "user", "content": "Parlez-moi de l'intelligence relationnelle"}])
    assert "Intelligence Relationnelle" in out or "Le Doze" in out


# ---------------------------------------------------------------------------
# Payload extraction (pure, no network)
# ---------------------------------------------------------------------------

def test_extract_returns_content():
    payload = {"choices": [{"message": {"role": "assistant", "content": "Bonjour"}}]}
    assert DeepSeekClient._extract(payload) == "Bonjour"


def test_extract_handles_malformed_payload():
    with pytest.raises(DeepSeekError, match="unexpected payload shape"):
        DeepSeekClient._extract({})


def test_extract_handles_non_dict_message():
    with pytest.raises(DeepSeekError):
        DeepSeekClient._extract({"choices": [{"message": "not a dict"}]})


# ---------------------------------------------------------------------------
# Live API (skip cleanly when key absent or network unreachable)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _has_api_key(), reason="DEEPSEEK_API_KEY not set")
def test_live_ping(real_client: DeepSeekClient):
    """One-shot ping to the configured DeepSeek endpoint."""
    if not _endpoint_reachable(real_client.api_url):
        pytest.skip("DeepSeek endpoint unreachable from this host")
    out = real_client.chat(
        [{"role": "user", "content": "Réponds uniquement: OK"}],
        max_tokens=10,
    )
    assert isinstance(out, str)
    assert len(out.strip()) > 0


@pytest.mark.skipif(not _has_api_key(), reason="DEEPSEEK_API_KEY not set")
def test_live_system_prompt_is_passed_through(real_client: DeepSeekClient):
    if not _endpoint_reachable(real_client.api_url):
        pytest.skip("DeepSeek endpoint unreachable from this host")
    out = real_client.chat(
        [{"role": "user", "content": "Dissociation"}],
        system="Tu es un psy informatif.",
        max_tokens=50,
    )
    assert isinstance(out, str)
    assert len(out.strip()) > 0


@pytest.mark.skipif(not _has_api_key(), reason="DEEPSEEK_API_KEY not set")
def test_live_unreachable_raises_deepseek_error(monkeypatch):
    """Force an unreachable host and confirm we get DeepSeekError, not a raw URLError."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")
    monkeypatch.setenv("DEEPSEEK_API_URL", "https://does-not-exist.invalid/v1")
    c = DeepSeekClient()
    with pytest.raises(DeepSeekError):
        c.chat([{"role": "user", "content": "ping"}], max_tokens=5)