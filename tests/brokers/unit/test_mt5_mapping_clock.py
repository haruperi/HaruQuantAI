"""Fixed-clock coverage for every MT5 observation-owned mapping timestamp."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone

import pytest
from app.services.brokers.metatrader.mapping import (
    _map_account,
    _map_balance,
    _map_deal,
    _map_order,
    _map_order_result,
    _map_permissions,
    _map_position,
    _map_quote,
    _map_tick,
    _map_transaction,
)

PROVIDER_TIME = datetime(2026, 1, 1, tzinfo=UTC).timestamp()
FIXED = datetime(2026, 8, 15, 12, 30, tzinfo=UTC)


def _cases() -> tuple[tuple[str, Callable[[Callable[[], datetime]], object], str], ...]:
    """Build all ten mapping-site invocations.

    Returns:
        Mapper name, invocation, and observation-owned timestamp field tuples.
    """
    account = {
        "login": 1,
        "currency": "USD",
        "balance": 100,
        "equity": 100,
        "margin": 0,
        "margin_free": 100,
    }
    return (
        (
            "quote",
            lambda clock: _map_quote(
                {"bid": 1.1, "ask": 1.2, "last": 1.15, "time": PROVIDER_TIME},
                "EURUSD",
                clock=clock,
            ),
            "retrieved_at",
        ),
        (
            "tick",
            lambda clock: _map_tick(
                {"bid": 1.1, "ask": 1.2, "last": 1.15, "time": PROVIDER_TIME},
                "EURUSD",
                clock=clock,
            ),
            "provider_receipt_timestamp",
        ),
        ("account", lambda clock: _map_account(account, clock=clock), "retrieved_at"),
        (
            "position",
            lambda clock: _map_position(
                {
                    "ticket": 1,
                    "symbol": "EURUSD",
                    "type": 0,
                    "volume": 1,
                    "price_open": 1.1,
                    "price_current": 1.2,
                    "profit": 10,
                    "time_update": PROVIDER_TIME,
                },
                clock=clock,
            ),
            "retrieved_at",
        ),
        (
            "permissions",
            lambda clock: _map_permissions(
                {"trade_allowed": True},
                {"trade_allowed": True, "connected": True},
                clock=clock,
            ),
            "observed_at",
        ),
        ("balance", lambda clock: _map_balance(account, clock=clock), "retrieved_at"),
        (
            "order",
            lambda clock: _map_order(
                {
                    "ticket": 1,
                    "symbol": "EURUSD",
                    "type": 0,
                    "state": 1,
                    "volume_initial": 1,
                    "volume_current": 1,
                    "time_setup": PROVIDER_TIME,
                },
                clock=clock,
            ),
            "retrieved_at",
        ),
        (
            "deal",
            lambda clock: _map_deal(
                {
                    "ticket": 1,
                    "order": 1,
                    "position_id": 1,
                    "symbol": "EURUSD",
                    "type": 0,
                    "volume": 1,
                    "price": 1.1,
                    "time": PROVIDER_TIME,
                },
                clock=clock,
            ),
            "retrieved_at",
        ),
        (
            "transaction",
            lambda clock: _map_transaction(
                {
                    "ticket": 1,
                    "type": 2,
                    "profit": 10,
                    "commission": 0,
                    "swap": 0,
                    "fee": 0,
                    "time": PROVIDER_TIME,
                },
                "USD",
                clock=clock,
            ),
            "retrieved_at",
        ),
        (
            "order_result",
            lambda clock: _map_order_result(
                {"retcode": 10009, "order": 1, "deal": 1, "volume": 1},
                clock=clock,
            ),
            "retrieved_at",
        ),
    )


@pytest.mark.parametrize(("name", "invoke", "field"), _cases())
def test_each_mapping_site_uses_injected_clock_once(
    name: str,
    invoke: Callable[[Callable[[], datetime]], object],
    field: str,
) -> None:
    """Each provider payload captures one exact fixed observation time.

    Args:
        name: Mapping-site label.
        invoke: Mapper invocation accepting a clock.
        field: Observation-owned result timestamp.
    """
    calls = 0

    def clock() -> datetime:
        nonlocal calls
        calls += 1
        return FIXED

    result = invoke(clock)
    assert getattr(result, field) == FIXED, name
    assert calls == 1


@pytest.mark.parametrize(
    "invalid",
    [
        datetime(2026, 8, 15),  # noqa: DTZ001 - intentional invalid clock.
        datetime(2026, 8, 15, tzinfo=timezone(timedelta(hours=1))),
    ],
)
def test_mapping_clock_rejects_naive_or_non_utc(invalid: datetime) -> None:
    """Invalid clock domains fail before a canonical result is emitted.

    Args:
        invalid: Naive or non-zero-offset datetime.
    """
    with pytest.raises(ValueError, match="aware UTC"):
        _cases()[0][1](lambda: invalid)


def test_mapping_clock_rejects_non_datetime() -> None:
    """A non-datetime clock value fails explicitly."""
    with pytest.raises(TypeError, match="datetime"):
        _cases()[0][1](lambda: "not-time")  # type: ignore[return-value]
