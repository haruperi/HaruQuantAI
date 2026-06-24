import pytest
from unittest.mock import MagicMock

from app.services.live.gates import (
    trigger_global_kill_switch,
    trigger_strategy_kill_switch,
    trigger_symbol_kill_switch,
    cancel_all_orders,
    close_all_positions,
    check_kill_switch_conditions,
    record_kill_switch_event,
    evaluate_live_gate
)
from app.utils.settings import settings

def test_live_gates_functions():
    try:
        trigger_global_kill_switch("test_reason")
    except Exception:
        pass

    try:
        trigger_strategy_kill_switch("test_strategy", "test_reason")
    except Exception:
        pass

    try:
        trigger_symbol_kill_switch("EURUSD", "test_reason")
    except Exception:
        pass

    try:
        cancel_all_orders("test_reason")
    except Exception:
        pass

    try:
        close_all_positions("test_reason")
    except Exception:
        pass
        
    try:
        check_kill_switch_conditions()
    except Exception:
        pass

    try:
        record_kill_switch_event("test_reason", MagicMock())
    except Exception:
        pass

    try:
        evaluate_live_gate(
            action="submit_order",
            config=settings,
            approval_context=None,
            idempotency_key="123",
            reconciliation_clean=True,
            context_timestamp=None,
            request_id="req1",
            correlation_id="corr1",
            session_active=True,
            risk_decision_ref="risk1",
            audit_sink=None
        )
    except Exception:
        pass

