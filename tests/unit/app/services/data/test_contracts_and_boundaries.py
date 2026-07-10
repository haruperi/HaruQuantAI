"""Tests for Data public-boundary classification and broker read-only ports."""

from datetime import UTC, datetime
from pathlib import Path

import app.services.data as data_service
import pandas as pd
import pytest
from app.services.data.contracts import BrokerMarketDataPort, SourceAdapterPort
from app.services.data.sources import (
    ADAPTER_REGISTRY,
    BrokerBackedAdapter,
    SourceAdapterProtocol,
    get_circuit_breaker,
)
from app.utils.errors import ExternalServiceError


class FakeBrokerMarketDataClient:
    """Fake broker data client with mutation traps for read-only tests."""

    def __init__(self) -> None:
        """Initialize fake broker data client counters."""
        self.connected = False
        self.connect_calls = 0
        self.get_bars_calls = 0
        self.get_ticks_calls = 0
        self.mutation_calls = 0

    def is_connected(self) -> bool:
        """Return the fake connection state."""
        return self.connected

    def connect(self) -> None:
        """Mark the fake client connected."""
        self.connect_calls += 1
        self.connected = True

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        date_from: datetime,
        date_to: datetime,
    ) -> pd.DataFrame:
        """Return one fake OHLCV row."""
        _ = (symbol, timeframe, date_to)
        self.get_bars_calls += 1
        return pd.DataFrame(
            [
                {
                    "Timestamp": date_from,
                    "Open": 1.1,
                    "High": 1.2,
                    "Low": 1.0,
                    "Close": 1.15,
                    "Volume": 100.0,
                    "Spread": 2.0,
                }
            ]
        )

    def get_ticks(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        as_dataframe: bool = True,
    ) -> pd.DataFrame:
        """Return one fake tick row."""
        _ = (symbol, end, as_dataframe)
        self.get_ticks_calls += 1
        return pd.DataFrame(
            [
                {
                    "Timestamp": start,
                    "bid": 1.1,
                    "ask": 1.1002,
                    "last": 1.1001,
                    "volume": 10.0,
                    "spread": 0.0002,
                }
            ]
        )

    def trade(self) -> None:
        """Trap forbidden broker mutation calls."""
        self.mutation_calls += 1
        raise AssertionError("Data adapters must not call trade().")

    def order_send(self) -> None:
        """Trap forbidden broker order calls."""
        self.mutation_calls += 1
        raise AssertionError("Data adapters must not call order_send().")


class FailingConnectBrokerClient(FakeBrokerMarketDataClient):
    """Fake broker client that fails during lazy connection."""

    def connect(self) -> None:
        """Raise a timeout during broker connection."""
        self.connect_calls += 1
        raise TimeoutError("connection timeout")


class FailingReadBrokerClient(FakeBrokerMarketDataClient):
    """Fake broker client that fails during broker reads."""

    def __init__(self) -> None:
        """Initialize connected fake read-failure client."""
        super().__init__()
        self.connected = True

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        date_from: datetime,
        date_to: datetime,
    ) -> pd.DataFrame:
        """Raise a timeout during broker bar reads."""
        _ = (symbol, timeframe, date_from, date_to)
        raise TimeoutError("read timeout")


class InvalidShapeBrokerClient(FakeBrokerMarketDataClient):
    """Fake broker client that returns an unsupported broker payload."""

    def __init__(self) -> None:
        """Initialize connected fake invalid-shape client."""
        super().__init__()
        self.connected = True

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        date_from: datetime,
        date_to: datetime,
    ) -> pd.DataFrame:
        """Return an intentionally invalid broker payload."""
        _ = (symbol, timeframe, date_from, date_to)
        return []


def test_public_imports_remain_classified_and_callable() -> None:
    """Verify broad compatibility exports remain importable and classified."""
    assert set(data_service.__all__) < set(data_service.PUBLIC_API_CLASSIFICATION)
    assert {
        "get_data",
        "list_symbols",
        "get_market_hours",
        "get_feed_status",
    } == data_service.OFFICIAL_DATA_TOOL_NAMES
    assert {
        data_service.PUBLIC_API_CLASSIFICATION[name] for name in data_service.__all__
    } == {
        "official_tool",
        "public_support_api",
        "legacy_public_compatibility",
    }
    assert (
        data_service.PUBLIC_API_CLASSIFICATION[
            "app.services.data.contracts.BrokerMarketDataPort"
        ]
        == "internal_only"
    )
    for name in data_service.__all__:
        assert callable(getattr(data_service, name))


def test_source_registry_preserves_current_source_names() -> None:
    """Verify the brownfield source registry keeps current adapter names."""
    assert set(ADAPTER_REGISTRY) == {
        "csv",
        "parquet",
        "synthetic",
        "mt5",
        "ctrader",
        "dukascopy",
        "binance",
        "yahoo",
    }
    for adapter in ADAPTER_REGISTRY.values():
        assert isinstance(adapter, SourceAdapterPort)
        assert isinstance(adapter, SourceAdapterProtocol)


def test_broker_market_data_port_exposes_only_read_methods() -> None:
    """Verify the broker market data port omits mutation methods."""
    port_methods = {
        name for name, value in BrokerMarketDataPort.__dict__.items() if callable(value)
    }
    assert {"is_connected", "connect", "get_bars", "get_ticks"} <= port_methods
    forbidden_methods = {
        "trade",
        "order_send",
        "order_modify",
        "order_cancel",
        "position_close",
        "account_mutation",
    }
    assert port_methods.isdisjoint(forbidden_methods)


def test_broker_backed_adapter_uses_only_read_methods() -> None:
    """Verify broker-backed adapters do not call fake mutation methods."""
    fake_client = FakeBrokerMarketDataClient()
    assert isinstance(fake_client, BrokerMarketDataPort)

    adapter = BrokerBackedAdapter(
        source="fake",
        client_factory=lambda: fake_client,
        unavailable_message="fake broker unavailable",
        error_code="BROKER_UNAVAILABLE",
        symbols=["EURUSD"],
        metadata={"ready": True},
    )

    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    bars = adapter.get_market_data("EURUSD", "H1", start, end)
    ticks = adapter.get_tick_data("EURUSD", start, end)

    assert fake_client.connect_calls == 1
    assert fake_client.get_bars_calls == 1
    assert fake_client.get_ticks_calls == 1
    assert fake_client.mutation_calls == 0
    assert isinstance(bars, list)
    assert isinstance(ticks, list)
    assert not isinstance(bars, pd.DataFrame)
    assert not isinstance(ticks, pd.DataFrame)
    assert bars[0]["symbol"] == "EURUSD"
    assert ticks[0]["symbol"] == "EURUSD"


def test_broker_backed_adapter_classifies_read_timeout() -> None:
    """Verify broker read timeouts map to deterministic errors."""
    fake_client = FailingReadBrokerClient()
    adapter = BrokerBackedAdapter(
        source="fake_timeout_read",
        client_factory=lambda: fake_client,
        unavailable_message="fake broker unavailable",
        error_code="BROKER_UNAVAILABLE",
        symbols=["EURUSD"],
        metadata={"ready": True},
    )
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    with pytest.raises(ExternalServiceError) as exc_info:
        adapter.get_market_data("EURUSD", "H1", start, end)
    assert exc_info.value.code == "TIMEOUT"


def test_failed_broker_connection_records_circuit_breaker() -> None:
    """Verify repeated failed broker connections open circuit breaker state."""
    fake_client = FailingConnectBrokerClient()
    adapter = BrokerBackedAdapter(
        source="fake_timeout_connect",
        client_factory=lambda: fake_client,
        unavailable_message="fake broker unavailable",
        error_code="BROKER_UNAVAILABLE",
        symbols=["EURUSD"],
        metadata={"ready": True},
    )
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    for _ in range(5):
        with pytest.raises(ExternalServiceError) as exc_info:
            adapter.get_market_data("EURUSD", "H1", start, end)
        assert exc_info.value.code == "TIMEOUT"

    circuit_breaker = get_circuit_breaker("fake_timeout_connect")
    assert circuit_breaker["state"] == "open"
    assert circuit_breaker["failures_count"] >= 5


def test_unsupported_broker_result_shape_fails_safely() -> None:
    """Verify non-DataFrame broker payloads fail with schema drift."""
    fake_client = InvalidShapeBrokerClient()
    adapter = BrokerBackedAdapter(
        source="fake_invalid_shape",
        client_factory=lambda: fake_client,
        unavailable_message="fake broker unavailable",
        error_code="BROKER_UNAVAILABLE",
        symbols=["EURUSD"],
        metadata={"ready": True},
    )
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    with pytest.raises(ExternalServiceError) as exc_info:
        adapter.get_market_data("EURUSD", "H1", start, end)
    assert exc_info.value.code == "DATA_SCHEMA_DRIFT"


def test_data_sources_do_not_import_broker_sdks_directly() -> None:
    """Verify Data sources route through broker service modules."""
    source_text = Path("app/services/data/sources.py").read_text(encoding="utf-8")
    assert "import MetaTrader5" not in source_text
    assert "from MetaTrader5" not in source_text
    assert "app.services.brokers.mt5" in source_text
