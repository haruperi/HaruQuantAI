"""Unit evidence for manual-order eligibility preflight orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.risk.governor import manual_preflight as preflight

_NOW = datetime(2026, 8, 14, tzinfo=UTC)


def test_track_equity_seeds_inception_peak_and_day_start_on_first_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A brand-new account's first observation seeds every tracked value."""
    monkeypatch.setattr(
        preflight, "create_equity_history_record", lambda **_kwargs: True
    )

    inception, peak, day_start = preflight._track_equity(
        account_id="account-one",
        equity=Decimal(10000),
        request_id="req-one",
        correlation_id="cor-one",
    )

    assert (inception, peak, day_start) == (
        Decimal(10000),
        Decimal(10000),
        Decimal(10000),
    )


def test_track_equity_raises_the_peak_and_preserves_day_start_same_day(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A later same-day observation raises the peak but not day-start equity."""
    today = datetime.now(UTC).date().isoformat()
    monkeypatch.setattr(
        preflight, "create_equity_history_record", lambda **_kwargs: False
    )
    monkeypatch.setattr(
        preflight,
        "read_equity_history_record",
        lambda _account_id: {
            "inception_equity": "9000",
            "peak_equity": "10000",
            "day_start_equity": "9500",
            "day_start_date": today,
            "updated_at": "2026-08-14T00:00:00+00:00",
        },
    )
    updates: list[dict[str, object]] = []
    monkeypatch.setattr(
        preflight,
        "update_equity_history_record",
        lambda **kwargs: updates.append(kwargs),
    )

    inception, peak, day_start = preflight._track_equity(
        account_id="account-one",
        equity=Decimal(11000),
        request_id="req-two",
        correlation_id="cor-two",
    )

    assert (inception, peak, day_start) == (
        Decimal(9000),
        Decimal(11000),
        Decimal(9500),
    )
    assert len(updates) == 1
    assert updates[0]["peak_equity"] == "11000"
    assert updates[0]["day_start_equity"] == "9500"


def test_kill_switch_states_filters_by_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    """_kill_switch_states queries global, portfolio, strategy, and symbol levels."""
    recorded_calls: list[tuple[str, dict[str, str]]] = []

    def mock_get_kill_switch_state(level: str, scope: dict[str, str]) -> object | None:
        recorded_calls.append((level, scope))
        if level == "global":
            return {"active": False, "level": "global"}
        return None

    monkeypatch.setattr(preflight, "get_kill_switch_state", mock_get_kill_switch_state)

    states = preflight._kill_switch_states(
        portfolio_id="port-1",
        strategy_id="strat-1",
        symbol="EURUSD",
    )

    assert len(states) == 1
    assert states[0] == {"active": False, "level": "global"}
    assert len(recorded_calls) == 4


def test_closing_returns_empty_on_missing_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_closing_returns returns empty tuple when market data is unavailable."""
    monkeypatch.setattr(
        preflight,
        "get_market_data",
        lambda _req: SimpleNamespace(data=None),
    )

    returns = preflight._closing_returns("src-1", "EURUSD", request_id="req-1")
    assert returns == ()
