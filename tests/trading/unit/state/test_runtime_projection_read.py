"""Trading aggregate projection public read tests."""

# ruff: noqa: INP001 - mirrors the existing state-test namespace layout.

import pytest
from app.services.trading.state import runtime


def test_projection_read_uses_exact_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route, tenant, and authority are retained through owner delegation."""
    store = object()
    captured: list[tuple[object, str, object]] = []
    monkeypatch.setattr(runtime, "build_trading_state_store", lambda: store)

    def execute(value: object, operation: str, scope: object) -> None:
        captured.append((value, operation, scope))

    monkeypatch.setattr(runtime, "execute_trading_state_store_operation", execute)
    assert runtime.get_trading_projection("paper", "dev", "account-1") is None
    assert len(captured) == 1
    assert captured[0][0:2] == (store, "load_projection")
    assert tuple(str(item) for item in captured[0][2]) == (
        "paper",
        "dev",
        "account-1",
    )


@pytest.mark.parametrize(("tenant_id", "authority_id"), [("", "account"), ("dev", "")])
def test_projection_read_rejects_incomplete_scope(
    tenant_id: str, authority_id: str
) -> None:
    """No storage read occurs for incomplete authority scope."""
    with pytest.raises(ValueError, match="scope is incomplete"):
        runtime.get_trading_projection("paper", tenant_id, authority_id)


def test_state_operation_rejects_invalid_handle_and_operation() -> None:
    """The private adapter cannot be bypassed by arbitrary callers."""
    with pytest.raises(TypeError, match="invalid Trading state-store handle"):
        runtime.execute_trading_state_store_operation(object(), "load_projection")
    store = object.__new__(runtime._DurableTradingStateStore)
    with pytest.raises(ValueError, match="unsupported Trading state-store operation"):
        runtime.execute_trading_state_store_operation(store, "delete_everything")


def test_runtime_encoder_requires_validated_model() -> None:
    """Unvalidated persistence material is rejected."""
    with pytest.raises(TypeError, match="validated model"):
        runtime._encode({"invented": True})
