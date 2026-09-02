"""Unit tests for legacy/v1 contract modules across data, indicator, and notification."""

from __future__ import annotations

from app.contracts.data.tick_stream.v1 import (
    TickStreamCapabilityV1,
    TickStreamEventV1,
    TickStreamRequestV1,
)
from app.contracts.indicator.common.v1 import (
    IndicatorConfigV1,
    IndicatorResultV1,
    MarketDatasetV1,
    OHLCVRecordV1,
)
from app.contracts.indicator.rsi.v1 import (
    CAPABILITY_ID as RSI_CAPABILITY_ID,
)
from app.contracts.indicator.rsi.v1 import (
    RsiCapabilityV1,
)
from app.contracts.indicator.williams_r.v1 import (
    CAPABILITY_ID as WILLIAMS_R_CAPABILITY_ID,
)
from app.contracts.indicator.williams_r.v1 import (
    WilliamsRCapabilityV1,
)
from app.contracts.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)


def test_tick_stream_contracts_v1() -> None:
    """Verify TickStreamRequestV1 and TickStreamEventV1 models and protocol."""
    req = TickStreamRequestV1(symbol="EURUSD", buffer_size=512)
    assert req.symbol == "EURUSD"
    assert req.buffer_size == 512

    evt = TickStreamEventV1(
        sequence=1,
        symbol="EURUSD",
        bid=1.0500,
        ask=1.0502,
        timestamp="2026-09-01T12:00:00Z",
        payload={"spread": 0.0002},
    )
    assert evt.sequence == 1
    assert evt.bid == 1.0500
    assert evt.ask == 1.0502
    assert evt.payload == {"spread": 0.0002}

    class DummyTickStreamProvider(TickStreamCapabilityV1):
        @property
        def generation_id(self) -> str:
            return "gen-1"

        async def start(self, request: TickStreamRequestV1) -> None:
            pass

        async def stop(self) -> None:
            pass

        async def events(self):
            yield evt

    provider = DummyTickStreamProvider()
    assert provider.generation_id == "gen-1"


def test_indicator_common_contracts_v1() -> None:
    """Verify IndicatorConfigV1 and IndicatorResultV1 models and protocols."""
    cfg = IndicatorConfigV1(period=14, source="close")
    assert cfg.period == 14
    assert cfg.source == "close"

    res = IndicatorResultV1(values=(10.5, 20.0, None), is_valid=True)
    assert res.values == (10.5, 20.0, None)
    assert res.is_valid is True

    class DummyOHLCV(OHLCVRecordV1):
        timestamp = "2026-09-01T12:00:00Z"
        open = 100.0
        high = 105.0
        low = 99.0
        close = 104.0
        volume = 1500.0

    class DummyMarketDataset(MarketDatasetV1):
        symbol = "AAPL"
        timeframe = "D1"
        records = (DummyOHLCV(),)

    dataset = DummyMarketDataset()
    assert dataset.symbol == "AAPL"
    assert len(dataset.records) == 1
    assert dataset.records[0].close == 104.0


def test_rsi_and_williams_r_contracts_v1() -> None:
    """Verify RSI and Williams %R v1 capability definitions."""
    assert RSI_CAPABILITY_ID == "indicator.rsi.v1"
    assert WILLIAMS_R_CAPABILITY_ID == "indicator.williams_r.v1"

    def mock_calc(*args, **kwargs):
        return (50.0, 60.0)

    rsi = RsiCapabilityV1(calculate=mock_calc)
    assert rsi.calculate() == (50.0, 60.0)

    williams = WilliamsRCapabilityV1(calculate=mock_calc)
    assert williams.calculate() == (50.0, 60.0)


def test_notification_delivery_contracts_v1() -> None:
    """Verify NotificationDeliveryResultV1 model and protocol."""
    result = NotificationDeliveryResultV1(
        channel="slack", status="SENT", recipient_count=2
    )
    assert result.channel == "slack"
    assert result.status == "SENT"
    assert result.recipient_count == 2

    class DummyNotificationProvider(NotificationDeliveryCapabilityV1):
        @property
        def channel(self) -> str:
            return "telegram"

        @property
        def active(self) -> bool:
            return True

        def send(self, title: str, text: str, html_body: str | None = None):
            _ = (title, text, html_body)
            return NotificationDeliveryResultV1(channel=self.channel, status="OK")

        def close(self) -> None:
            pass

    provider = DummyNotificationProvider()
    assert provider.channel == "telegram"
    assert provider.active is True
    res = provider.send("Alert", "Price crossed MA")
    assert res.status == "OK"
