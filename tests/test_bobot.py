"""Tests for bobot.py — local dev psybot (RAG + ReAct loop on DeepSeek).

The agent loop is exercised against the mock client (DEEPSEEK_MOCK=1) so the
tests run without a real DEEPSEEK_API_KEY.
"""

from __future__ import annotations

import os
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Force the mock before any import that may load llm / make_client.
os.environ["DEEPSEEK_MOCK"] = "1"
os.environ["DEEPSEEK_API_KEY"] = "test-key-not-used"

from bobot import (  # noqa: E402  (import after env setup)
    _EMERGENCY_MESSAGE,
    _run_agent,
    app,
    tool_detect_emergency,
    tool_search_knowledge,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tools (unit)
# ---------------------------------------------------------------------------

def test_detect_emergency_matches():
    r = tool_detect_emergency("je n'en peux plus, je veux mourir")
    assert r["emergency"] is True
    assert r["message"]


def test_detect_emergency_no_match():
    r = tool_detect_emergency("C'est quoi l'EMDR ?")
    assert r["emergency"] is False


def test_search_knowledge_returns_hits():
    r = tool_search_knowledge("C'est quoi l'EMDR ?")
    assert "hits" in r
    assert len(r["hits"]) > 0
    top = r["hits"][0]
    assert "emdr" in (top["title"] + top["snippet"]).lower()


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

def test_health_ok(client: TestClient):
    r = client.get("/api/health/psybot")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm_mock"] is True
    assert body["max_iters"] >= 1


# ---------------------------------------------------------------------------
# /api/psybot/chat — contract
# ---------------------------------------------------------------------------

def test_chat_validation_empty_message(client: TestClient):
    r = client.post("/api/psybot/chat", json={"message": ""})
    assert r.status_code == 422  # Pydantic rejects empty (min_length=1)


def test_chat_validation_missing_field(client: TestClient):
    r = client.post("/api/psybot/chat", json={})
    assert r.status_code == 422


def test_chat_emergency_shortcut(client: TestClient):
    r = client.post("/api/psybot/chat", json={"message": "je veux mourir"})
    assert r.status_code == 200
    body = r.json()
    assert body["emergency"] is True
    assert "3114" in body["answer"]
    # Emergency short-circuits before the LLM — trajectory is minimal.
    assert any("emergency" in t["action"] for t in body["trajectory"])


def test_chat_normal_message(client: TestClient):
    r = client.post("/api/psybot/chat", json={"message": "C'est quoi l'EMDR ?"})
    assert r.status_code == 200
    body = r.json()
    # Contract fields
    assert "answer" in body and isinstance(body["answer"], str) and body["answer"]
    assert "sources" in body and isinstance(body["sources"], list)
    assert body["emergency"] is False
    assert "trajectory" in body and isinstance(body["trajectory"], list)
    # With the mock, sources may be empty (mock doesn't call RAG), but the
    # trajectory must show the agent loop ran.
    assert any(t["action"] == "finish" for t in body["trajectory"])


def test_chat_message_too_long(client: TestClient):
    r = client.post("/api/psybot/chat", json={"message": "a" * 1501})
    assert r.status_code == 400


def test_chat_with_history(client: TestClient):
    r = client.post(
        "/api/psybot/chat",
        json={
            "message": "Merci",
            "history": [
                {"role": "user", "content": "Bonjour"},
                {"role": "assistant", "content": "Bonjour, comment puis-je vous aider ?"},
            ],
        },
    )
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Agent loop — invariant: never hangs, always returns a string
# ---------------------------------------------------------------------------

def test_run_agent_returns_contract():
    from bobot import make_client

    client = make_client()
    out: dict[str, Any] = _run_agent(client, "C'est quoi l'EMDR ?")
    assert isinstance(out["answer"], str) and out["answer"]
    assert isinstance(out["sources"], list)
    assert isinstance(out["emergency"], bool)
    assert isinstance(out["trajectory"], list)
    assert out["trajectory"], "trajectory should not be empty (agent must act at least once)"


def test_run_agent_emergency_shortcircuits():
    """The agent's `detect_emergency` tool, if invoked by a smart LLM, returns
    the safety message verbatim. Here we exercise the tool directly (the route
    has its own fast-path short-circuit tested in test_chat_emergency_shortcut).
    """
    r = tool_detect_emergency("je veux en finir")
    assert r["emergency"] is True
    assert "3114" in r["message"]


# ---------------------------------------------------------------------------
# Anti-regression: the ReAct few-shots must stay in the decision prompt.
# Without them, deepseek-chat falls back to detect_emergency → finish without
# ever searching the KB (verified live on 2026-10-02).
# ---------------------------------------------------------------------------

def test_decision_prompt_has_fewshots():
    from bobot import _DECISION_PROMPT

    assert "search_knowledge" in _DECISION_PROMPT
    assert "EMDR Shapiro" in _DECISION_PROMPT, "few-shot EMDR example missing"
    assert "attachement" in _DECISION_PROMPT.lower()
    # No str.format placeholders left (regression on 2026-10-02 — format() raised
    # ValueError because the JSON examples contain single '{').
    assert "{trajectory}" not in _DECISION_PROMPT
    assert "{0}" not in _DECISION_PROMPT


def test_decision_prompt_replaces_trajectory_placeholder():
    from bobot import _DECISION_PROMPT

    out = _DECISION_PROMPT.replace("__TRAJECTORY__", "step 1: hello")
    assert "step 1: hello" in out
    assert "__TRAJECTORY__" not in out


def test_decision_prompt_injects_user_message():
    # Anti-regression: the user's question must reach the LLM at every iteration,
    # not just be a string we silently drop. Without this, the agent loop has no
    # way to ground tool calls in the actual question and answers the wrong one
    # (verified live on 2026-10-02 — Q2 'déroulé séance EMDR' was being answered
    # with the EMDR definition because the LLM only saw the trajectory, not the
    # original question).
    from bobot import _DECISION_PROMPT

    prompt = (
        _DECISION_PROMPT
        .replace("__USER_MESSAGE__", "Comment se déroule une séance d'EMDR ?")
        .replace("__TRAJECTORY__", "(vide)")
    )
    assert "Comment se déroule une séance d'EMDR ?" in prompt
    assert "__USER_MESSAGE__" not in prompt
    assert "__TRAJECTORY__" not in prompt


def test_agent_decide_signature_takes_user_message():
    # The signature must include user_message; calling without it is a programming
    # error and should fail loudly.
    import inspect
    from bobot import _agent_decide

    sig = inspect.signature(_agent_decide)
    params = list(sig.parameters.keys())
    assert "user_message" in params
    assert "client" in params
    assert "trajectory" in params
