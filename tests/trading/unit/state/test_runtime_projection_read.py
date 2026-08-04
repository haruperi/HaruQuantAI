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
