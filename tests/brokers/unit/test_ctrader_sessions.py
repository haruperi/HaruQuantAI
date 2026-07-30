"""Tests for broker-authored cTrader session and holiday mapping."""

from datetime import UTC, date, datetime

import pytest
from app.services.brokers.ctrader_market_data.sessions import _map_trading_sessions


def test_ctrader_schedule_subtracts_partial_broker_holiday() -> None:
    holiday_day = date(2026, 7, 20)
    epoch_days = (holiday_day - date(1970, 1, 1)).days
    spec = {
        "tradingMode": 0,
        "scheduleTimeZone": "UTC",
        "schedule": [
            {
                "startSecond": 86_400 + 9 * 3_600,
                "endSecond": 86_400 + 17 * 3_600,
            }
        ],
        "holiday": [
            {
                "holidayDate": epoch_days,
                "isRecurring": False,
                "scheduleTimeZone": "UTC",
                "startSecond": 12 * 3_600,
                "endSecond": 13 * 3_600,
            }
        ],
    }

    sessions = _map_trading_sessions(
        spec,
        symbol="EURUSD",
        start=datetime(2026, 7, 20, tzinfo=UTC),
        end=datetime(2026, 7, 21, tzinfo=UTC),
    )

    assert [(item.opens_at.hour, item.closes_at.hour) for item in sessions] == [
        (9, 12),
        (13, 17),
    ]
    assert all(item.provider_timezone == "UTC" for item in sessions)


def test_ctrader_disabled_trading_mode_fails_closed() -> None:
    sessions = _map_trading_sessions(
        {
            "tradingMode": 3,
            "scheduleTimeZone": "UTC",
            "schedule": [{"startSecond": 0, "endSecond": 86_400}],
            "holiday": [],
        },
        symbol="EURUSD",
        start=datetime(2026, 7, 20, tzinfo=UTC),
        end=datetime(2026, 7, 21, tzinfo=UTC),
    )

    assert sessions == ()


def test_ctrader_zero_boundaries_close_the_full_holiday_day() -> None:
    """Treat the provider's explicit zero/zero holiday as a full-day closure."""
    holiday_day = date(2026, 7, 20)
    epoch_days = (holiday_day - date(1970, 1, 1)).days
    sessions = _map_trading_sessions(
        {
            "tradingMode": 0,
            "scheduleTimeZone": "UTC",
            "schedule": [
                {
                    "startSecond": 86_400 + 9 * 3_600,
                    "endSecond": 86_400 + 17 * 3_600,
                }
            ],
            "holiday": [
                {
                    "holidayDate": epoch_days,
                    "isRecurring": False,
                    "scheduleTimeZone": "UTC",
                    "startSecond": 0,
                    "endSecond": 0,
                }
            ],
        },
        symbol="EURUSD",
        start=datetime(2026, 7, 20, tzinfo=UTC),
        end=datetime(2026, 7, 21, tzinfo=UTC),
    )

    assert sessions == ()


@pytest.mark.parametrize(
    ("spec", "message"),
    [
        (
            {
                "tradingMode": 0,
                "scheduleTimeZone": "Missing/Timezone",
                "schedule": [{"startSecond": 0, "endSecond": 1}],
                "holiday": [],
            },
            "timezone",
        ),
        (
            {
                "tradingMode": 0,
                "scheduleTimeZone": "UTC",
                "schedule": [],
                "holiday": [],
            },
            "schedule is absent",
        ),
    ],
)
def test_ctrader_schedule_rejects_missing_provider_evidence(
    spec: dict[str, object],
    message: str,
) -> None:
    """Invalid provider timezone or absent intervals fail closed."""
    with pytest.raises(ValueError, match=message):
        _map_trading_sessions(
            spec,
            symbol="EURUSD",
            start=datetime(2026, 7, 20, tzinfo=UTC),
            end=datetime(2026, 7, 21, tzinfo=UTC),
        )


def test_ctrader_schedule_rejects_unordered_bounds() -> None:
    """An empty requested range is never treated as provider evidence."""
    instant = datetime(2026, 7, 20, tzinfo=UTC)
    with pytest.raises(ValueError, match="ordered"):
        _map_trading_sessions(
            {},
            symbol="EURUSD",
            start=instant,
            end=instant,
        )
