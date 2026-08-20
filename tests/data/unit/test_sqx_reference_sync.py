"""Unit tests for the QuantDataManager reference synchronisation."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.services.data._settings import DataSettings, data_settings_context
from app.services.data.contracts import DataError
from app.services.data.sqx_source.reference_sync import sync_quantdata_reference

_REQUEST_ID = "req-00000000-0000-4000-8000-000000000000"

_METADATA = SimpleNamespace(
    canonical_symbol="EURUSD",
    provider_symbol="EURUSD",
    asset_class="fx",
    base_currency="EUR",
    quote_currency="USD",
    digits=5,
    point=0.00001,
    trade_tick_size=0.00001,
    trade_tick_value=1.0,
    trade_contract_size=100000.0,
    spread=12,
    trade_stops_level=20,
    swap_long=-0.5,
    swap_short=0.3,
    swap_mode=1,
    swap_rollover3days=3,
    trade_calc_mode=0,
    margin_initial=0.0,
    volume_min=0.01,
    volume_max=100.0,
    volume_step=0.01,
    path="Forex\\EURUSD",
)


def _quantdata_workspace(tmp_path: Path) -> None:
    data_dir = tmp_path / "qdm" / "user" / "data"
    data_dir.mkdir(parents=True)
    with sqlite3.connect(data_dir / "data.db") as conn:
        conn.execute(
            "CREATE TABLE DATA (ID INTEGER, CONNECTION TEXT, SYMBOL TEXT, "
            "INSTRUMENT TEXT, TIMEFRAME TEXT, TIMEZONE TEXT, FILENAME TEXT, "
            "DATEFROM INTEGER, DATETO INTEGER, DATATYPE INTEGER, ROWS INTEGER, "
            "DECIMALS INTEGER, SOURCE INTEGER, SECONDS_RECORDS INTEGER, "
            "USYMBOL TEXT, USYMBOLNAME TEXT, REMOVE_WEEKENDS INTEGER, "
            "SHOW INTEGER, BASKET_ID INTEGER, BROKER_ID INTEGER)"
        )
        conn.execute(
            "INSERT INTO DATA VALUES (201, 'History', 'EURUSD', 'EURUSD', 'M1', "
            "'Etc/UCT', NULL, 1167609600000, 1785531599000, 0, 7314561, 5, 2, "
            "0, 'EURUSD', 'EURUSD', 0, 1, -1, -1)"
        )
        conn.execute(
            "CREATE TABLE BROKER (ID INTEGER, NAME TEXT, SYSTEM INTEGER, "
            '"DESC" TEXT, STOCKPICKER_USE INTEGER, MT_USE INTEGER, '
            "MT_TIMEZONE TEXT, POSTFIX TEXT)"
        )
        conn.execute(
            "INSERT INTO BROKER VALUES (2, 'RoboForex', 1, 'RoboForex', 0, 1, "
            "'EET', '_roboforex')"
        )


def _settings(tmp_path: Path) -> DataSettings:
    return DataSettings(
        database_url=None,
        data_dir=tmp_path,
        quantdata_manager_root=tmp_path / "qdm",
    )


def test_sync_upserts_all_three_catalogues(tmp_path: Path) -> None:
    """Series, brokers, and MT5-backed instruments are upserted together."""
    _quantdata_workspace(tmp_path)
    with (
        data_settings_context(_settings(tmp_path)),
        patch(
            "app.services.data.sqx_source.reference_sync.create_market_series_records"
        ) as series_upsert,
        patch(
            "app.services.data.sqx_source.reference_sync"
            ".create_broker_reference_records"
        ) as broker_upsert,
        patch(
            "app.services.data.sqx_source.reference_sync"
            ".create_instrument_reference_records"
        ) as instrument_upsert,
        patch(
            "app.services.data.sqx_source.reference_sync.get_symbol_metadata",
            return_value=SimpleNamespace(data=_METADATA),
        ) as metadata_read,
    ):
        summary = sync_quantdata_reference(request_id=_REQUEST_ID, source_id="mt5")

    assert summary["series_synced"] == 1
    assert summary["brokers_synced"] == 1
    assert summary["instruments_synced"] == 1
    assert summary["mt5_available"] is True

    series_parameters = series_upsert.call_args.args[0]
    assert series_parameters[0][2] == "EURUSD"
    assert series_parameters[0][4] == "M1"
    # Millisecond catalogue times become epoch seconds.
    assert series_parameters[0][7] == 1167609600
    assert series_parameters[0][10] == 7314561

    broker_parameters = broker_upsert.call_args.args[0]
    assert broker_parameters[0][0] == "quantdata-2"
    assert broker_parameters[0][6] == 2

    metadata_read.assert_called_with(
        source_id="mt5", symbol="EURUSD", request_id=_REQUEST_ID
    )
    instrument_parameters = instrument_upsert.call_args.args[0]
    binding = instrument_parameters[0]
    assert binding[0] == "EURUSD"
    assert binding[5] == 5  # digits
    assert binding[10] == "100000.0"  # contract size
    assert binding[18] == pytest.approx(0.00001)  # point value
    assert binding[19] == pytest.approx(0.00001)  # tick size
    assert binding[21] == 12.0  # spread points
    assert binding[26] == "FOREX"  # data type from path
    assert binding[27] == 1.0  # default slippage
    assert binding[32] == pytest.approx(20 * 0.00001)  # stops level in price


def test_sync_survives_mt5_unavailability(tmp_path: Path) -> None:
    """A missing MT5 connection still syncs series and brokers."""
    _quantdata_workspace(tmp_path)
    with (
        data_settings_context(_settings(tmp_path)),
        patch(
            "app.services.data.sqx_source.reference_sync.create_market_series_records"
        ),
        patch(
            "app.services.data.sqx_source.reference_sync"
            ".create_broker_reference_records"
        ),
        patch(
            "app.services.data.sqx_source.reference_sync"
            ".create_instrument_reference_records"
        ) as instrument_upsert,
        patch(
            "app.services.data.sqx_source.reference_sync.get_symbol_metadata",
            side_effect=RuntimeError("mt5 offline"),
        ),
    ):
        summary = sync_quantdata_reference(request_id=_REQUEST_ID)

    assert summary["series_synced"] == 1
    assert summary["brokers_synced"] == 1
    assert summary["instruments_synced"] == 0
    assert summary["mt5_available"] is False
    assert summary["instruments_failed"] == ("EURUSD",)
    instrument_upsert.assert_not_called()


def test_sync_fails_closed_without_a_catalogue(tmp_path: Path) -> None:
    """An absent QuantDataManager root raises the typed owner error."""
    with (
        data_settings_context(_settings(tmp_path)),
        pytest.raises(DataError, match="QUANTDATA_ROOT_MISSING"),
    ):
        sync_quantdata_reference(request_id=_REQUEST_ID)
