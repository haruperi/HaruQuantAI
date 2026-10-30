"""Unit tests for AI Assistant core service and conversation engine."""

from __future__ import annotations

from app.workspace.ai.assistant import AIAssistantService
from app.workspace.ai.assistant_models import (
    ChatTurnRequest,
    CompletionRequest,
    MemoryConfig,
)


def test_assistant_default_session() -> None:
    """Test initial default session setup."""
    svc = AIAssistantService()
    sessions = svc.list_sessions()
    assert len(sessions) >= 1
    assert any(s.session_id == "session-1" for s in sessions)

    history = svc.get_session_history("session-1")
    assert len(history) >= 1
    assert history[0].role == "system"


def test_assistant_session_lifecycle() -> None:
    """Test creating, renaming, pinning, clearing history, and deleting sessions."""
    svc = AIAssistantService()

    # Create
    sess = svc.create_session(name="Forex Alpha", project="EURUSD")
    assert sess.name == "Forex Alpha"
    assert sess.project == "EURUSD"
    sid = sess.session_id

    # Rename
    assert svc.rename_session(sid, "Crypto Momentum")
    assert not svc.rename_session("non-existent", "Test")

    # Pin
    assert svc.pin_session(sid, True)
    assert not svc.pin_session("non-existent", True)

    # Add turn then clear history
    svc.run_turn(ChatTurnRequest(message="Hello", sessionId=sid))
    hist = svc.get_session_history(sid)
    assert len(hist) > 1

    assert svc.clear_history(sid)
    assert not svc.clear_history("non-existent")
    assert len(svc.get_session_history(sid)) == 1

    # Delete
    assert svc.delete_session(sid)
    assert not svc.delete_session(sid)


def test_assistant_chat_turn_tool_execution() -> None:
    """Test chat turn that triggers MCP tools."""
    svc = AIAssistantService()

    # "list projects"
    resp = svc.run_turn(
        ChatTurnRequest(message="Please list projects for me", sessionId="session-1")
    )
    assert not resp.stopped
    assert resp.tool_calls >= 1
    assert len(resp.steps) >= 2
    assert "Default Project" in resp.success

    # "databanks"
    resp_db = svc.run_turn(
        ChatTurnRequest(message="What databanks do we have?", sessionId="session-1")
    )
    assert resp_db.tool_calls >= 1
    assert "Results" in resp_db.success

    # "strategies"
    resp_strat = svc.run_turn(
        ChatTurnRequest(message="Show me candidate strategies", sessionId="session-1")
    )
    assert resp_strat.tool_calls >= 1
    assert "Strategy 1.01" in resp_strat.success


def test_assistant_chat_turn_general() -> None:
    """Test chat turn without tool invocation."""
    svc = AIAssistantService()
    resp = svc.run_turn(
        ChatTurnRequest(message="How does Monte Carlo work?", sessionId="session-1")
    )
    assert not resp.stopped
    assert resp.tool_calls == 0
    assert "HaruQuantAI" in resp.success or "strategy" in resp.success


def test_assistant_stop_turn() -> None:
    """Test stopping an active turn."""
    svc = AIAssistantService()
    # No turn running
    assert not svc.stop_turn("session-1")

    # Inspect status
    st = svc.get_turn_status("session-1")
    assert not st.running


def test_assistant_one_shot_completion() -> None:
    """Test fast completion."""
    svc = AIAssistantService()
    req = CompletionRequest(
        prompt="Summarize trend filter", system="You are an analyst."
    )
    res = svc.complete(req)
    assert "trend filter" in res.success
    assert res.elapsed_ms >= 0


def test_assistant_memory_configuration() -> None:
    """Test memory enabled/disabled toggle."""
    svc = AIAssistantService()
    cfg = svc.get_memory_config()
    assert cfg.enabled

    # Disable memory
    svc.set_memory_config(MemoryConfig(enabled=False, flushIntervalMinutes=5.0))
    assert not svc.get_memory_config().enabled

    # Chat without memory should not append to history
    sid = "session-no-mem"
    svc.create_session(session_id=sid)
    hist_before = len(svc.get_session_history(sid))
    svc.run_turn(ChatTurnRequest(message="Transient message", sessionId=sid))
    hist_after = len(svc.get_session_history(sid))
    assert hist_before == hist_after


def test_assistant_model_catalog() -> None:
    """Test model listing and selection."""
    svc = AIAssistantService()
    cat = svc.get_model_catalog()
    assert len(cat.models) >= 1
    assert cat.ready

    assert svc.select_model("claude-3-5-sonnet-20241022")
    cat2 = svc.get_model_catalog()
    assert cat2.current_model == "claude-3-5-sonnet-20241022"
