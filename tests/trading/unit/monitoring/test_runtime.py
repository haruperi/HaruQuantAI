"""Unit tests for the bounded Trading operational-event reader."""

from types import SimpleNamespace

import pytest
from app.services.trading.monitoring import runtime


@pytest.mark.parametrize("limit", [True, 0, 201])
def test_operational_event_limit_fails_closed(limit: object) -> None:
    """Invalid public bounds are rejected before storage access."""
    with pytest.raises(ValueError, match="between 1 and 200"):
        runtime.get_trading_operational_events(limit=limit)  # type: ignore[arg-type]


def test_operational_events_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    """The reader delegates once and returns an immutable bounded sequence."""
    store = SimpleNamespace()
    monkeypatch.setattr(runtime, "build_trading_state_store", lambda: store)

    def execute(*_args: object) -> list[str]:
        return ["first", "second"]

    monkeypatch.setattr(runtime, "execute_trading_state_store_operation", execute)
    assert runtime.get_trading_operational_events(limit=1) == ("first",)


def test_operational_events_reject_invalid_storage_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-sequence persistence result is rejected."""
    monkeypatch.setattr(runtime, "build_trading_state_store", object)

    def execute(*_args: object) -> int:
        return 1

    monkeypatch.setattr(runtime, "execute_trading_state_store_operation", execute)
    with pytest.raises(TypeError, match="invalid sequence"):
        runtime.get_trading_operational_events()
