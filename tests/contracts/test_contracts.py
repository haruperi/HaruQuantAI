"""Tests for neutral domain capability contracts and DTO structures."""

from datetime import UTC, datetime

import pytest

from app.contracts.broker.execution import (
    BROKER_EXECUTION,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderType,
)
from app.contracts.broker.market_data import (
    BROKER_MARKET_DATA,
    BrokerBarsRequest,
    BrokerRawBar,
)
from app.contracts.data.bar_cache import BAR_CACHE
from app.contracts.data.historical_bars import (
    HISTORICAL_BARS,
    Bar,
    HistoricalBarsRequest,
    HistoricalBarsUnavailableError,
)
from app.contracts.data.realtime_ticks import REALTIME_TICKS, Tick
from app.contracts.risk.approval import (
    RISK_APPROVAL,
    RiskDecision,
    RiskVerdict,
)
from app.contracts.system.clock import SYSTEM_CLOCK
from app.contracts.system.metrics import SYSTEM_METRICS
from app.contracts.system.storage import SYSTEM_STORAGE


def test_capability_keys_identity() -> None:
    """Test all capability keys have correct versioned identifiers."""
    assert SYSTEM_CLOCK.identifier == "system.clock@1"
    assert SYSTEM_METRICS.identifier == "system.metrics@1"
    assert SYSTEM_STORAGE.identifier == "system.storage@1"
    assert BROKER_MARKET_DATA.identifier == "broker.market-data@1"
    assert BROKER_EXECUTION.identifier == "broker.execution@1"
    assert HISTORICAL_BARS.identifier == "data.historical-bars@1"
    assert REALTIME_TICKS.identifier == "data.realtime-ticks@1"
    assert BAR_CACHE.identifier == "data.bar-cache@1"
    assert RISK_APPROVAL.identifier == "risk.approval@1"


def test_broker_contract_dtos() -> None:
    """Test broker request and raw bar DTO immutability."""
    now = datetime.now(UTC)
    request = BrokerBarsRequest(
        symbol="EURUSD",
        timeframe="M1",
        start=now,
        end=now,
    )
    assert request.symbol == "EURUSD"
    assert request.timeframe == "M1"

    bar = BrokerRawBar(
        timestamp=now,
        open_price=1.1000,
        high_price=1.1050,
        low_price=1.0990,
        close_price=1.1040,
        volume=100.0,
    )
    assert bar.open_price == 1.1000

    with pytest.raises(AttributeError):
        bar.open_price = 1.2000  # type: ignore[misc]


def test_order_execution_dtos() -> None:
    """Test order execution request and result DTOs."""
    now = datetime.now(UTC)
    order = OrderRequest(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=0.5,
        price=60000.0,
        client_order_id="cl-001",
    )
    assert order.side == OrderSide.BUY
    assert order.order_type == OrderType.LIMIT

    result = OrderResult(
        order_id="ord-123",
        client_order_id="cl-001",
        symbol="BTCUSDT",
        status="FILLED",
        filled_quantity=0.5,
        average_price=60000.0,
        timestamp=now,
    )
    assert result.status == "FILLED"


def test_data_contract_dtos() -> None:
    """Test data domain DTOs and errors."""
    now = datetime.now(UTC)
    req = HistoricalBarsRequest(
        symbol="GBPUSD",
        timeframe="H1",
        start=now,
        end=now,
    )
    bar = Bar(
        datetime=now,
        open=1.3000,
        high=1.3050,
        low=1.2990,
        close=1.3020,
        volume=500.0,
    )
    assert req.symbol == "GBPUSD"
    assert bar.close == 1.3020

    tick = Tick(
        symbol="GBPUSD",
        timestamp=now,
        bid=1.3019,
        ask=1.3021,
    )
    assert tick.ask == 1.3021

    err = HistoricalBarsUnavailableError("No provider")
    assert str(err) == "No provider"


def test_risk_contract_dtos() -> None:
    """Test risk evaluation decision DTO."""
    decision = RiskDecision(
        verdict=RiskVerdict.APPROVED,
        reason="Within max drawdown limits",
    )
    assert decision.verdict == RiskVerdict.APPROVED
