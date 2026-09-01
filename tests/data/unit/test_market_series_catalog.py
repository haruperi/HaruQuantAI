"""Unit tests for the market series catalogue operation."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from app.kernel.identity import generate_id
from app.services.data.contracts import DataError
from app.services.data.datasets.catalog import (
    get_instrument_spec,
    list_brokers,
    list_instruments,
    list_market_series,
    update_instrument_spec,
    update_market_series,
)


class _Result:
    """Minimal read result double carrying plain rows."""

    def __init__(self, rows: tuple[dict[str, Any], ...]) -> None:
        self.rows = rows


def test_list_market_series_maps_owner_rows_with_the_bar_type_constant() -> None:
    """Series rows pass through owner columns plus the invariant bar type."""
    row = {
        "symbol": "EURJPY_M1",
        "filename": "EURJPY_M1.csv",
        "broker_id": 1,
        "usymbol": None,
        "timeframe": "M1",
        "timezone": "UTC",
        "date_from": 1609459200,
        "date_to": 1640908800,
        "total_days": 364,
        "row_count": 250000,
        "source": 2,
        "data_type": 1,
        "show": 1,
    }
    with patch(
        "app.services.data.datasets.catalog.read_market_series_records",
        return_value=_Result((row,)),
    ):
        result = list_market_series(request_id=generate_id("req"))

    assert len(result) == 1
    assert result[0]["symbol"] == "EURJPY_M1"
    assert result[0]["document"] == "EURJPY_M1.csv"
    assert result[0]["total_days"] == 364
    assert result[0]["bar_type"] == "start_of_bar"


def test_list_instruments_and_brokers_map_owner_rows() -> None:
    """Instrument and broker summaries pass owner columns through."""
    instrument_row = {
        "instrument": "EURJPY",
        "description": "Euro vs Japanese Yen",
        "broker_id": 1,
        "point_value": 1,
        "tick_size": 0.001,
        "tick_step": 0.001,
        "default_spread": 0.002,
        "default_slippage": 0,
        "data_type": 1,
        "order_size_multiplier": 1,
        "order_size_step": 0,
    }
    broker_row = {
        "broker_id": 1,
        "name": "MetaTrader 5",
        "description": "Default MT5 broker",
        "postfix": "_r",
        "mt_timezone": "EET",
        "customized_instruments": 30,
    }
    with (
        patch(
            "app.services.data.datasets.catalog.read_instrument_records",
            return_value=_Result((instrument_row,)),
        ),
        patch(
            "app.services.data.datasets.catalog.read_broker_records",
            return_value=_Result((broker_row,)),
        ),
    ):
        instruments = list_instruments(request_id=generate_id("req"))
        brokers = list_brokers(request_id=generate_id("req"))

    assert instruments[0]["instrument"] == "EURJPY"
    assert instruments[0]["tick_size"] == 0.001
    assert brokers[0]["timezone"] == "EET"
    assert brokers[0]["customized_instruments"] == 30


def test_update_market_series_applies_both_statements_atomically() -> None:
    """The governed edit updates the series row and instrument spec together."""
    with (
        patch(
            "app.services.data.datasets.catalog.read_market_series_exists",
            return_value=_Result(({"series_id": 7},)),
        ),
        patch(
            "app.services.data.datasets.catalog.update_market_series_records"
        ) as update,
        patch(
            "app.services.data.datasets.catalog.get_instrument_spec",
            return_value={"instrument": "EURJPY", "tick_size": 0.002},
        ) as spec,
    ):
        result = update_market_series(
            7,
            symbol="EDITED_M1",
            instrument="EURJPY",
            broker_id=1,
            timeframe="M1",
            timezone="UTC",
            date_from=1609459200,
            date_to=1640908800,
            data_type=1,
            decimals=3,
            source=2,
            row_count=250000,
            remove_weekends=1,
            show=0,
            instrument_description="Euro vs Japanese Yen",
            point_value=1,
            tick_size=0.002,
            tick_step=0.001,
            default_spread=0.002,
            default_slippage=0,
            min_distance=0,
            order_size_multiplier=1,
            order_size_step=0,
            request_id=generate_id("req"),
        )

    assert update.call_count == 1
    series_parameters, instrument_parameters = update.call_args.args
    assert series_parameters[0] == "EDITED_M1"
    assert series_parameters[-1] == 7
    assert instrument_parameters[2] == 0.002
    assert instrument_parameters[-1] == "EURJPY"
    assert result["symbol"] == "EDITED_M1"
    assert result["total_days"] == 364
    assert result["instrument_spec"] == spec.return_value


def test_update_market_series_fails_closed_for_unknown_identity() -> None:
    """An unknown series identity never reaches the update transaction."""
    with (
        patch(
            "app.services.data.datasets.catalog.read_market_series_exists",
            return_value=_Result(()),
        ),
        patch(
            "app.services.data.datasets.catalog.update_market_series_records"
        ) as update,
        pytest.raises(DataError) as excinfo,
    ):
        update_market_series(
            999,
            symbol="X",
            instrument="Y",
            broker_id=None,
            timeframe=None,
            timezone=None,
            date_from=None,
            date_to=None,
            data_type=None,
            decimals=None,
            source=None,
            row_count=None,
            remove_weekends=0,
            show=1,
            instrument_description=None,
            point_value=None,
            tick_size=None,
            tick_step=None,
            default_spread=None,
            default_slippage=None,
            min_distance=None,
            order_size_multiplier=None,
            order_size_step=None,
            request_id=generate_id("req"),
        )
    assert excinfo.value.code == "SERIES_NOT_FOUND"
    update.assert_not_called()


def test_update_market_series_rejects_an_inverted_range() -> None:
    """An inverted date range fails closed before any statement executes."""
    with pytest.raises(DataError) as excinfo:
        update_market_series(
            7,
            symbol="X",
            instrument="Y",
            broker_id=None,
            timeframe=None,
            timezone=None,
            date_from=200,
            date_to=100,
            data_type=None,
            decimals=None,
            source=None,
            row_count=None,
            remove_weekends=0,
            show=1,
            instrument_description=None,
            point_value=None,
            tick_size=None,
            tick_step=None,
            default_spread=None,
            default_slippage=None,
            min_distance=None,
            order_size_multiplier=None,
            order_size_step=None,
            request_id=generate_id("req"),
        )
    assert excinfo.value.code == "DATE_RANGE_INVALID"


def test_get_instrument_spec_requires_a_known_identity() -> None:
    """A blank or unknown instrument identity fails closed."""
    with pytest.raises(DataError):
        get_instrument_spec("", request_id=generate_id("req"))
    with (
        patch(
            "app.services.data.datasets.catalog.read_instrument_spec_record",
            return_value=_Result(()),
        ),
        pytest.raises(DataError) as excinfo,
    ):
        get_instrument_spec("UNKNOWN", request_id=generate_id("req"))
    assert excinfo.value.code == "INSTRUMENT_NOT_FOUND"


def test_update_instrument_spec_applies_and_returns_the_spec() -> None:
    """The instrument edit executes one statement and re-reads the result."""
    spec = {"instrument": "EURJPY", "tick_size": 0.005}
    with (
        patch(
            "app.services.data.datasets.catalog.update_instrument_spec_record"
        ) as update,
        patch(
            "app.services.data.datasets.catalog.get_instrument_spec",
            return_value=spec,
        ),
    ):
        result = update_instrument_spec(
            "EURJPY",
            description="Edited",
            point_value=1,
            tick_size=0.005,
            tick_step=0.001,
            default_spread=0.002,
            default_slippage=0,
            min_distance=0,
            order_size_multiplier=1,
            order_size_step=0,
            request_id=generate_id("req"),
        )

    update.assert_called_once()
    parameters = update.call_args.args[0]
    assert parameters[0] == "Edited"
    assert parameters[2] == 0.005
    assert parameters[-1] == "EURJPY"
    assert result == spec


def test_list_market_series_rejects_an_invalid_bound() -> None:
    """Zero and above-bound limits fail closed before any read executes."""
    for limit in (0, 1001):
        with pytest.raises(DataError) as excinfo:
            list_market_series(request_id=generate_id("req"), limit=limit)
        assert excinfo.value.code == "LIMIT_EXCEEDED"
