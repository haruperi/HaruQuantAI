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
        request_id="req-one",
        correlation_id="cor-one",
    )

    assert inception == Decimal(9000)
    assert peak == Decimal(11000)
    assert day_start == Decimal(9500)
    assert updates[0]["peak_equity"] == "11000"
    assert updates[0]["day_start_equity"] == "9500"


def test_track_equity_resets_day_start_on_a_new_calendar_day(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A new UTC calendar day resets the day-start reference to current equity."""
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
            "day_start_date": "2000-01-01",
            "updated_at": "2026-08-14T00:00:00+00:00",
        },
    )
    updates: list[dict[str, object]] = []
    monkeypatch.setattr(
        preflight,
        "update_equity_history_record",
        lambda **kwargs: updates.append(kwargs),
    )

    _inception, _peak, day_start = preflight._track_equity(
        account_id="account-one",
        equity=Decimal(9800),
        request_id="req-one",
        correlation_id="cor-one",
    )

    assert day_start == Decimal(9800)
    assert updates[0]["day_start_equity"] == "9800"


def test_correlation_requires_a_minimum_sample_size() -> None:
    """Too few paired observations never produce a fabricated correlation."""
    assert (
        preflight._correlation([Decimal(1), Decimal(2)], [Decimal(1), Decimal(2)])
        is None
    )


def test_correlation_computes_a_real_pearson_value() -> None:
    """A genuine linear relationship correlates to (near) 1."""
    left = [Decimal("0.01"), Decimal("0.02"), Decimal("0.03"), Decimal("0.04")]
    right = [Decimal("0.02"), Decimal("0.04"), Decimal("0.06"), Decimal("0.08")]

    value = preflight._correlation(left, right)

    assert value is not None
    assert value > Decimal("0.99")


def test_kill_switch_states_fetches_only_applicable_scopes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only global/portfolio/strategy/symbol scopes for this proposal are fetched."""
    seen: list[tuple[str, dict[str, str]]] = []

    def _fake_state(level: str, scope: dict[str, str]) -> object | None:
        seen.append((level, scope))
        return None if level == "portfolio" else SimpleNamespace(state="inactive")

    monkeypatch.setattr(preflight, "get_kill_switch_state", _fake_state)

    states = preflight._kill_switch_states(
        portfolio_id="portfolio-one", strategy_id="strategy-one", symbol="EURUSD"
    )

    assert ("global", {}) in seen
    assert ("portfolio", {"portfolio_id": "portfolio-one"}) in seen
    assert ("strategy", {"strategy_id": "strategy-one"}) in seen
    assert ("symbol", {"symbol": "EURUSD"}) in seen
    # The portfolio scope returned None (no recorded state) and is excluded.
    assert len(states) == 3


def test_kill_switch_states_omits_portfolio_scope_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No portfolio binding means no portfolio-scope lookup at all."""
    seen: list[str] = []
    monkeypatch.setattr(
        preflight,
        "get_kill_switch_state",
        lambda level, _scope: seen.append(level) or SimpleNamespace(state="inactive"),
    )

    preflight._kill_switch_states(
        portfolio_id=None, strategy_id="strategy-one", symbol="EURUSD"
    )

    assert "portfolio" not in seen


def test_authorization_verifier_requires_the_same_authenticated_principal() -> None:
    """An attestation attributed to a different principal is never authorized."""
    auth = SimpleNamespace(principal_id="operator-1", permissions=("trading:write",))
    verify = preflight._authorization_verifier(auth)
    attestation = SimpleNamespace(principal_id="someone-else", action="submit_order")

    assert verify(attestation) is False


def test_authorization_verifier_requires_the_expected_permission() -> None:
    """The same principal without trading:write is still not authorized."""
    auth = SimpleNamespace(principal_id="operator-1", permissions=("trading:read",))
    verify = preflight._authorization_verifier(auth)
    attestation = SimpleNamespace(principal_id="operator-1", action="submit_order")

    assert verify(attestation) is False


def test_authorization_verifier_authorizes_the_matching_principal_and_permission() -> (
    None
):
    """The same authenticated principal holding the right permission is authorized."""
    auth = SimpleNamespace(principal_id="operator-1", permissions=("trading:write",))
    verify = preflight._authorization_verifier(auth)
    attestation = SimpleNamespace(principal_id="operator-1", action="submit_order")

    assert verify(attestation) is True


def test_authorization_verifier_requires_trading_write_for_bulk_cancel() -> None:
    """A bulk cancel-all attestation also requires trading:write, not the read default."""
    auth = SimpleNamespace(principal_id="operator-1", permissions=("trading:read",))
    verify = preflight._authorization_verifier(auth)
    attestation = SimpleNamespace(principal_id="operator-1", action="cancel_all_orders")

    assert verify(attestation) is False


def test_authorization_verifier_authorizes_bulk_cancel_with_trading_write() -> None:
    """A bulk cancel-all attestation is authorized once trading:write is held."""
    auth = SimpleNamespace(principal_id="operator-1", permissions=("trading:write",))
    verify = preflight._authorization_verifier(auth)
    attestation = SimpleNamespace(principal_id="operator-1", action="cancel_all_orders")

    assert verify(attestation) is True
