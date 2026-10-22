"""Unit tests for historical market data reader, validators, and DataFrame converters.

Description:
    Validates functionality, boundary conditions, numerical integrity,
    date routing, request parameter validation, row boundary validation,
    and DataFrame conversions for bars and ticks in app.services.include.data.

Purpose:
    FEAT-DATAMGR-HISTORY: Unit tests for historical market data capabilities.

Key Capabilities:
    - FR-DATAMGR-HISTORY-BAR-COLUMNS: Verify canonical bar column tuple specification.
    - FR-DATAMGR-HISTORY-TICK-COLUMNS: Verify canonical tick column tuple specification.
    - FR-DATAMGR-HISTORY-BACKEND-PROTOCOL: Verify DataBackend protocol conformance.
    - FR-DATAMGR-HISTORY-BROKER-BACKEND: Verify DataBrokerBackend dispatch and default stubs.
    - FR-DATAMGR-HISTORY-BARS-TO-DATAFRAME: Verify bars_to_dataframe conversion.
    - FR-DATAMGR-HISTORY-BARS-TO-DF: Verify bars_to_df alias.
    - FR-DATAMGR-HISTORY-GET-HISTORICAL-BARS: Verify get_historical_bars retrieval.
    - FR-DATAMGR-HISTORY-GET-TICKS: Verify get_ticks retrieval.
    - FR-DATAMGR-HISTORY-TICKS-TO-DATAFRAME: Verify ticks_to_dataframe conversion.
    - FR-DATAMGR-HISTORY-TICKS-TO-DF: Verify ticks_to_df alias.
    - FR-DATAMGR-HISTORY-VALIDATE-REQUEST: Verify request validation bounds.
    - FR-DATAMGR-HISTORY-VALIDATE-ROWS: Verify row counts and boundary validation.

Python API Usage:
    ```bash
    uv run pytest tests/unit/workspace/data_manager/test_history.py --no-cov
    ```
"""

from __future__ import annotations

import asyncio
import importlib
from datetime import UTC, datetime
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from app.services.brokers.base import BridgeError, BrokerClient
from app.services.include.contracts import (
    MAX_RECORDS,
    MarketBar,
    MarketTick,
)
from app.services.include.data import (
    BAR_COLUMNS,
    TICK_COLUMNS,
    DataBackend,
    _bounds,
    _route,
    bars_to_dataframe,
    bars_to_df,
    get_historical_bars,
    get_ticks,
    ticks_to_dataframe,
    ticks_to_df,
    validate_request,
    validate_rows,
)
from app.services.include.data import (
    main as history_main,
)
from app.services.include.enums import Timeframe


class TestColumnsAndAliases:
    """Verify column definitions and alias equivalence."""

    def test_bar_columns(self) -> None:
        """Verify BAR_COLUMNS specification."""
        assert BAR_COLUMNS == ["Open", "High", "Low", "Close", "Volume", "Spread"]

    def test_tick_columns(self) -> None:
        """Verify TICK_COLUMNS specification."""
        assert TICK_COLUMNS == ["Bid", "Ask"]

    def test_alias_equivalence(self) -> None:
        """Verify bars_to_df and ticks_to_df function aliases."""
        assert bars_to_df is bars_to_dataframe
        assert ticks_to_df is ticks_to_dataframe


class TestDataBackendProtocol:
    """Verify protocol conformance and backend calls."""

    def test_protocol_implementation(self) -> None:
        """Verify class implementing call method satisfies DataBackend protocol."""

        class MockBackend:
            async def call(
                self,
                *,
                object_id: str,
                class_name: str,
                method_name: str,
                args: list[Any],
                requires_arm: bool = False,
                timeout: float | None = None,  # noqa: ASYNC109
            ) -> Any:
                return []

        backend = MockBackend()
        assert hasattr(backend, "call")
        assert callable(backend.call)
        assert hasattr(DataBackend, "call")


class TestBrokerClient:
    """Verify BrokerClient subclassing and default stubs."""

    def test_default_stub_raises(self) -> None:
        """Verify default get_bars and get_ticks raise BridgeError."""
        backend = BrokerClient("test_broker")
        assert backend.name == "test_broker"

        with pytest.raises(
            BridgeError, match="test_broker does not support historical bars"
        ):
            backend.get_bars("EURUSD")

        with pytest.raises(
            BridgeError, match="test_broker does not support tick history"
        ):
            backend.get_ticks("EURUSD")

    def test_custom_broker_client(self) -> None:
        """Verify custom BrokerClient subclass returns MarketBar and MarketTick."""

        class CustomDataBroker(BrokerClient):
            def get_bars(
                self,
                symbol: str,
                timeframe: Timeframe | str = Timeframe.PERIOD_M1,
                date_from: datetime | None = None,
                date_to: datetime | None = None,
                *,
                start_pos: int | None = None,
                count: int | None = None,
                limit: int = 1000,
            ) -> list[MarketBar]:
                return [
                    MarketBar(
                        time=100,
                        open=1.0,
                        high=1.2,
                        low=0.9,
                        close=1.1,
                        tick_volume=5,
                        spread=0,
                        real_volume=0,
                    )
                ]

            def get_ticks(
                self,
                symbol: str,
                date_from: datetime | None = None,
                date_to: datetime | None = None,
                *,
                count: int | None = None,
                limit: int = 1000,
            ) -> list[MarketTick]:
                return [
                    MarketTick(
                        time_msc=1000,
                        bid=1.1,
                        ask=1.2,
                        last=1.15,
                        volume=1,
                        flags=0,
                        volume_real=1.0,
                    )
                ]

        broker = CustomDataBroker("custom")
        bars_res = broker.get_bars("EURUSD", "M1")
        assert len(bars_res) == 1
        assert bars_res[0].open == 1.0

        ticks_res = broker.get_ticks("EURUSD")
        assert len(ticks_res) == 1
        assert ticks_res[0].bid == 1.1


class TestRequestValidation:
    """Verify validate_request parameter constraints."""

    def test_valid_request(self) -> None:
        """Verify valid bounds pass without error."""
        validate_request("EURUSD", 100, 200, 100, Timeframe.PERIOD_M1)
        validate_request("EURUSD", 100, 200, 100, None)

    def test_invalid_types_and_bounds(self) -> None:
        """Verify invalid bounds or parameter types raise BridgeError."""
        with pytest.raises(BridgeError, match="invalid history request"):
            validate_request("", 100, 200, 100)

        with pytest.raises(BridgeError, match="invalid history request"):
            validate_request("EURUSD", "bad", 200, 100)  # type: ignore[arg-type]

        with pytest.raises(BridgeError, match="invalid history bounds"):
            validate_request("EURUSD", -1, 100, 100)

        with pytest.raises(BridgeError, match="invalid history bounds"):
            validate_request("EURUSD", 200, 100, 100)

        with pytest.raises(BridgeError, match="invalid history bounds"):
            validate_request("EURUSD", 100, 200, 0)

        with pytest.raises(BridgeError, match="invalid history bounds"):
            validate_request("EURUSD", 100, 200, MAX_RECORDS + 1)

        with pytest.raises(BridgeError, match="tick start must be after the epoch"):
            validate_request("EURUSD", 0, 100, 100, None)

    def test_unsupported_timeframe_and_range_exceeded(self) -> None:
        """Verify invalid timeframe and narrow date range error."""
        with pytest.raises(BridgeError, match="explicit timeframe required"):
            validate_request(
                "EURUSD",
                100,
                200,
                100,
                "INVALID",  # type: ignore[arg-type]
            )

        with pytest.raises(BridgeError, match="narrow the bar date range"):
            validate_request("EURUSD", 0, 100000, 10, Timeframe.PERIOD_M1)


class TestRowValidation:
    """Verify validate_rows structure, chronological order, and values."""

    def test_valid_bars(self) -> None:
        """Verify valid bar payload converts to MarketBar list."""
        payload = [
            {
                "time": 100,
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "tick_volume": 10,
                "spread": 1,
                "real_volume": 0,
            },
            {
                "time": 160,
                "open": 1.15,
                "high": 1.25,
                "low": 1.10,
                "close": 1.20,
                "tick_volume": 15,
                "spread": 1,
                "real_volume": 0,
            },
        ]
        bars = validate_rows(payload, "bars", 50, 200, 10)
        assert len(bars) == 2
        assert isinstance(bars[0], MarketBar)
        assert bars[0].open == 1.1

    def test_valid_ticks(self) -> None:
        """Verify valid tick payload converts to MarketTick list."""
        payload = [
            {
                "time_msc": 1000,
                "bid": 1.1,
                "ask": 1.2,
                "last": 1.15,
                "volume": 10,
                "flags": 0,
                "volume_real": 0.0,
            }
        ]
        ticks = validate_rows(payload, "ticks", 500, 1500, 10)
        assert len(ticks) == 1
        assert isinstance(ticks[0], MarketTick)
        assert ticks[0].bid == 1.1

    def test_valid_bars_dataclass(self) -> None:
        """Verify already instantiated MarketBar objects pass validate_rows."""
        payload = [
            MarketBar(
                time=100,
                open=1.1,
                high=1.2,
                low=1.0,
                close=1.15,
                tick_volume=10,
                spread=1,
                real_volume=0,
            ),
            MarketBar(
                time=160,
                open=1.15,
                high=1.25,
                low=1.10,
                close=1.20,
                tick_volume=15,
                spread=1,
                real_volume=0,
            ),
        ]
        bars = validate_rows(payload, "bars", 50, 200, 10)
        assert len(bars) == 2
        assert bars[0] is payload[0]
        assert bars[1] is payload[1]

    def test_valid_ticks_dataclass(self) -> None:
        """Verify already instantiated MarketTick objects pass validate_rows."""
        payload = [
            MarketTick(
                time_msc=1000,
                bid=1.1,
                ask=1.2,
                last=1.15,
                volume=10,
                flags=0,
                volume_real=0.0,
            )
        ]
        ticks = validate_rows(payload, "ticks", 500, 1500, 10)
        assert len(ticks) == 1
        assert ticks[0] is payload[0]

    def test_invalid_payload_cases(self) -> None:
        """Verify invalid schema, numbers, chronology, and OHLC raise BridgeError."""
        with pytest.raises(BridgeError, match="invalid history payload"):
            validate_rows("not a list", "bars", 0, 100, 10)

        with pytest.raises(BridgeError, match="invalid history payload"):
            validate_rows([{"time": 100}], "bars", 0, 100, 0)

        with pytest.raises(BridgeError, match="invalid history row"):
            validate_rows(["not a dict"], "bars", 0, 100, 10)

        with pytest.raises(BridgeError, match="invalid history row"):
            validate_rows([{"missing": 1}], "bars", 0, 100, 10)

        # Invalid number: negative volume
        with pytest.raises(BridgeError, match="invalid history number"):
            validate_rows(
                [
                    {
                        "time": 100,
                        "open": 1.1,
                        "high": 1.2,
                        "low": 1.0,
                        "close": 1.15,
                        "tick_volume": -1,
                        "spread": 0,
                        "real_volume": 0,
                    }
                ],
                "bars",
                0,
                200,
                10,
            )

        # Invalid chronology
        with pytest.raises(BridgeError, match="invalid history chronology"):
            validate_rows(
                [
                    {
                        "time": 200,
                        "open": 1.1,
                        "high": 1.2,
                        "low": 1.0,
                        "close": 1.15,
                        "tick_volume": 1,
                        "spread": 0,
                        "real_volume": 0,
                    },
                    {
                        "time": 150,
                        "open": 1.1,
                        "high": 1.2,
                        "low": 1.0,
                        "close": 1.15,
                        "tick_volume": 1,
                        "spread": 0,
                        "real_volume": 0,
                    },
                ],
                "bars",
                0,
                300,
                10,
            )

        # Invalid OHLC (high lower than open)
        with pytest.raises(BridgeError, match="invalid OHLC values"):
            validate_rows(
                [
                    {
                        "time": 100,
                        "open": 1.5,
                        "high": 1.2,
                        "low": 1.0,
                        "close": 1.15,
                        "tick_volume": 1,
                        "spread": 0,
                        "real_volume": 0,
                    }
                ],
                "bars",
                0,
                200,
                10,
            )


class TestBoundsAndRouting:
    """Verify _bounds and _route helper logic."""

    def test_bounds(self) -> None:
        """Verify _bounds calculation for UTC aware dates."""
        start = datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC)
        end = datetime(2023, 1, 1, 1, 0, 0, tzinfo=UTC)
        first, last = _bounds(start, end, scale=1)
        assert first < last

    def test_bounds_naive_raises(self) -> None:
        """Verify naive datetimes raise BridgeError."""
        start = datetime(2023, 1, 1, 0, 0, 0)  # noqa: DTZ001 -- deliberately naive
        end = datetime(2023, 1, 1, 1, 0, 0)  # noqa: DTZ001 -- deliberately naive
        with pytest.raises(BridgeError, match="ordered aware dates required"):
            _bounds(start, end, scale=1)

    def test_route_conflicts(self) -> None:
        """Verify conflicting route parameters raise BridgeError."""
        dt = datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC)
        with pytest.raises(
            BridgeError, match="conflicting history selectors or invalid count"
        ):
            _route(None, dt, None, None, 100, scale=1)  # date_to without date_from

        with pytest.raises(
            BridgeError, match="conflicting history selectors or invalid count"
        ):
            _route(dt, None, 5, None, 100, scale=1)  # date_from and start_pos

        with pytest.raises(BridgeError, match="position range exceeds limit"):
            _route(None, None, 100, None, 50, scale=1)


class TestBarsAndTicksToDataframe:
    """Verify DataFrame conversion and parsing logic."""

    def test_empty_bars(self) -> None:
        """Verify empty bar list produces empty DataFrame with schema."""
        df = bars_to_dataframe([])
        assert len(df) == 0
        assert list(df.columns) == BAR_COLUMNS
        assert df.index.name == "DateTime"

    def test_market_bar_conversion(self) -> None:
        """Verify MarketBar objects convert cleanly."""
        bar = MarketBar(1700000000, 1.1, 1.2, 1.0, 1.15, 100, 2, 0)
        df = bars_to_dataframe([bar])
        assert len(df) == 1
        assert df["Open"].iloc[0] == 1.1
        assert df["Close"].iloc[0] == 1.15
        assert df["Volume"].iloc[0] == 100
        assert df["Spread"].iloc[0] == 2

    def test_dict_bar_conversion(self) -> None:
        """Verify dict bars with both naming conventions."""
        lower_bar = {
            "time": 1700000000,
            "open": 1.1,
            "high": 1.2,
            "low": 1.0,
            "close": 1.15,
            "tick_volume": 50,
            "spread": 1,
        }
        upper_bar = {
            "DateTime": 1700000060,
            "Open": 1.15,
            "High": 1.25,
            "Low": 1.10,
            "Close": 1.20,
            "Volume": 60,
            "Spread": 1,
        }
        df = bars_to_dataframe([lower_bar, upper_bar])
        assert len(df) == 2
        assert df["Open"].iloc[0] == 1.1
        assert df["Open"].iloc[1] == 1.15

    def test_duck_bar_conversion(self) -> None:
        """Verify duck typed bar conversion."""

        class DuckBar:
            time = datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC)
            open = 1.0
            high = 1.1
            low = 0.9
            close = 1.05
            volume = 10
            spread = 0

        df = bars_to_dataframe([DuckBar()])  # type: ignore[list-item]
        assert len(df) == 1
        assert df["Close"].iloc[0] == 1.05

    def test_empty_ticks(self) -> None:
        """Verify empty tick list produces empty DataFrame."""
        df = ticks_to_dataframe([])
        assert len(df) == 0
        assert list(df.columns) == TICK_COLUMNS

    def test_market_tick_conversion(self) -> None:
        """Verify MarketTick objects convert cleanly."""
        tick = MarketTick(1700000000500, 1.1000, 1.1002, 1.1001, 10, 0, 0.0)
        df = ticks_to_dataframe([tick])
        assert len(df) == 1
        assert df["Bid"].iloc[0] == 1.1000
        assert df["Ask"].iloc[0] == 1.1002

    def test_dict_ticks_conversion(self) -> None:
        """Verify dict ticks with time_msc and time."""
        ticks = [
            {"time_msc": 1700000000100, "bid": 1.05, "ask": 1.06},
            {"time": 1700000001, "bid": 1.07, "ask": 1.08},
        ]
        df = ticks_to_dataframe(ticks)
        assert len(df) == 2
        assert df["Bid"].iloc[0] == 1.05
        assert df["Ask"].iloc[1] == 1.08

    def test_duck_tick_conversion(self) -> None:
        """Verify duck typed tick conversion."""

        class DuckTick:
            time = datetime(2023, 1, 1, 0, 0, 0, 500000, tzinfo=UTC)
            bid = 1.20
            ask = 1.21

        df = ticks_to_dataframe([DuckTick()])
        assert len(df) == 1
        assert df["Bid"].iloc[0] == 1.20


class TestAsyncHistoricalRetrieval:
    """Verify get_historical_bars and get_ticks asynchronous retrieval."""

    def test_get_historical_bars_range(self) -> None:
        """Verify get_historical_bars with date range."""

        class MockBackend:
            async def get_bars(
                self,
                symbol: str,
                timeframe: Timeframe | str = Timeframe.PERIOD_M1,
                date_from: datetime | None = None,
                date_to: datetime | None = None,
                *,
                start_pos: int | None = None,
                count: int | None = None,
                limit: int = 1000,
            ) -> list[MarketBar]:
                return [
                    MarketBar(
                        time=1672531200,
                        open=1.1,
                        high=1.2,
                        low=1.0,
                        close=1.15,
                        tick_volume=10,
                        spread=1,
                        real_volume=0,
                    )
                ]

        backend = MockBackend()
        start = datetime(2023, 1, 1, 0, 0, 0, tzinfo=UTC)
        end = datetime(2023, 1, 1, 1, 0, 0, tzinfo=UTC)
        bars = asyncio.run(
            get_historical_bars(backend, "EURUSD", Timeframe.PERIOD_M1, start, end)
        )
        assert isinstance(bars, pd.DataFrame)
        assert len(bars) == 1
        assert bars.iloc[0]["Close"] == 1.15

    def test_get_ticks_latest(self) -> None:
        """Verify get_ticks with count limit."""

        class MockBackend:
            async def get_ticks(
                self,
                symbol: str,
                date_from: datetime | None = None,
                date_to: datetime | None = None,
                *,
                count: int | None = None,
                limit: int = 1000,
            ) -> list[MarketTick]:
                return [
                    MarketTick(
                        time_msc=1672531200100,
                        bid=1.100,
                        ask=1.102,
                        last=1.101,
                        volume=5,
                        flags=0,
                        volume_real=0.0,
                    )
                ]

        backend = MockBackend()
        ticks = asyncio.run(get_ticks(backend, "EURUSD", count=5))
        assert isinstance(ticks, pd.DataFrame)
        assert len(ticks) == 1
        assert ticks.iloc[0]["Bid"] == 1.100


class TestMainDemo:
    """Verify module main execution."""

    def test_main(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verify main() executes without error."""
        with caplog.at_level("INFO"):
            history_main()
        assert "Historical bars DataFrame shape:" in caplog.text
        assert "Validated rows: count=1" in caplog.text


class TestAntiShim:
    """Verify strict deletion of legacy app.workspace.data_manager.history path."""

    def test_legacy_history_raises_module_not_found(self) -> None:
        """Verify importing app.workspace.data_manager.history raises ModuleNotFoundError."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.workspace.data_manager.history")
