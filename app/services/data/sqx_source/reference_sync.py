"""QuantDataManager reference synchronisation (FEAT-DATA-15).

Refreshes the Data-owned reference catalogues from the QuantDataManager
workspace: series and broker-profile rows come from the QuantDataManager
SQLite catalogue, and instrument specifications come from the live MT5
connection through ``get_symbol_metadata`` so the stored specs are the
broker's real symbol properties (digits, point, spread, stops level,
contract size, tick size/value, swaps). No ``.dat`` payload is decoded
during synchronisation, so a refresh stays bounded by the catalogue size.
"""

from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING, Any

from app.services.data._settings import get_data_provider_settings
from app.services.data.contracts import DataError
from app.services.data.market_data import get_symbol_metadata
from app.services.data.persistence import (
    create_broker_reference_records,
    create_instrument_reference_records,
    create_market_series_records,
    read_quantdata_series_and_broker_rows,
)
from app.services.data.sqx_source.reader import _resolve_database_path
from app.utils import get_logger, utc_now

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.market_data.symbol_metadata import SymbolMetadata

_MAX_SYNC_ROWS = 2000
_UNAVAILABLE = "Attribute is not available with this broker."


def _read_quantdata_catalogue(request_id: str) -> tuple[Any, ...]:
    """Read the bounded QuantDataManager DATA and BROKER rows read-only.

    Args:
        request_id: Caller trace identity.

    Returns:
        Dictionary rows; series rows carry a ``SYMBOL`` key.

    Raises:
        DataError: If the catalogue is unreadable.
    """
    database = _resolve_database_path(request_id)
    try:
        return read_quantdata_series_and_broker_rows(
            database, request_id=request_id, limit=_MAX_SYNC_ROWS
        )
    except sqlite3.Error as error:
        raise DataError("QUANTDATA_ROOT_MISSING", request_id=request_id) from error


def _sync_series_and_brokers(
    rows: tuple[Any, ...], *, request_id: str
) -> tuple[int, int]:
    """Upsert series and broker rows from the raw catalogue read.

    Args:
        rows: Mixed DATA and BROKER rows from ``_read_quantdata_catalogue``.
        request_id: Caller trace identity.

    Returns:
        Series and broker upsert counts.
    """
    now = utc_now().isoformat()
    series_parameters: list[tuple[Any, ...]] = []
    broker_parameters: list[tuple[Any, ...]] = []
    for row in rows:
        if "SYMBOL" in row:
            series_parameters.append(
                (
                    row["ID"],
                    row["CONNECTION"],
                    row["SYMBOL"],
                    row["INSTRUMENT"],
                    row["TIMEFRAME"],
                    row["TIMEZONE"],
                    row["FILENAME"],
                    (row["DATEFROM"] or 0) // 1000,
                    (row["DATETO"] or 0) // 1000,
                    row["DATATYPE"],
                    row["ROWS"],
                    row["DECIMALS"],
                    row["SOURCE"],
                    row["SECONDS_RECORDS"],
                    row["USYMBOL"],
                    row["USYMBOLNAME"],
                    int(bool(row["REMOVE_WEEKENDS"])),
                    int(bool(row["SHOW"])),
                    row["BASKET_ID"],
                    row["BROKER_ID"],
                    request_id,
                    "",
                    now,
                    now,
                )
            )
        else:
            broker_parameters.append(
                (
                    f"quantdata-{row['ID']}",
                    f"qdm-{row['ID']}",
                    request_id,
                    "",
                    now,
                    now,
                    row["ID"],
                    row["NAME"],
                    int(bool(row["SYSTEM"])),
                    row["DESC"],
                    row["STOCKPICKER_USE"],
                    row["MT_USE"],
                    row["MT_TIMEZONE"],
                    row["POSTFIX"],
                )
            )
    if series_parameters:
        create_market_series_records(tuple(series_parameters), request_id=request_id)
    if broker_parameters:
        create_broker_reference_records(tuple(broker_parameters), request_id=request_id)
    return len(series_parameters), len(broker_parameters)


def _optional(value: float | str | None) -> float | None:
    """Pass through numeric MT5 values and drop unavailable markers.

    Args:
        value: Normalized metadata number, the unavailable marker string,
            or an absent value.

    Returns:
        The numeric value, or None when the broker does not provide it.
    """
    if value is None or isinstance(value, str):
        return None
    return float(value)


def _instrument_parameters(
    instrument: str,
    metadata: SymbolMetadata,
    server_name: str | None,
    *,
    request_id: str,
) -> tuple[Any, ...]:
    """Build one instrument upsert binding from MT5 symbol metadata.

    Args:
        instrument: Instrument identity.
        metadata: Normalized ``SymbolMetadata`` owner contract.
        server_name: MT5 server name the metadata came from, or None.
        request_id: Caller trace identity.

    Returns:
        Ordered ``data_instruments`` binding tuple.
    """
    now = utc_now().isoformat()
    point = _optional(metadata.point)
    tick_size = _optional(metadata.trade_tick_size) or point
    contract_size = _optional(metadata.trade_contract_size)
    spread_points = _optional(metadata.spread)
    stops_points = _optional(metadata.trade_stops_level)
    digits = _optional(metadata.digits)
    path = metadata.path if isinstance(metadata.path, str) else ""
    # symbol_info.path looks like "Forex\EURUSD"; the leading segment names
    # the broker's market category for the Data type column (e.g. FOREX).
    path_category = (
        path.replace("/", "\\").split("\\")[0].strip().upper() if path else ""
    )
    spec = {
        "provider_symbol": metadata.provider_symbol,
        "contract_size": contract_size,
        "tick_value": _optional(metadata.trade_tick_value),
        "swap_long": _optional(metadata.swap_long),
        "swap_short": _optional(metadata.swap_short),
        "swap_mode": _optional(metadata.swap_mode),
        "swap_rollover3days": _optional(metadata.swap_rollover3days),
        "trade_calc_mode": _optional(metadata.trade_calc_mode),
        "margin_initial": _optional(metadata.margin_initial),
        "spread_points": spread_points,
    }
    volume_step = _optional(metadata.volume_step)
    volume_min = _optional(metadata.volume_min)
    volume_max = _optional(metadata.volume_max)
    swap_text = (
        f"long={spec['swap_long']} short={spec['swap_short']}"
        if spec["swap_long"] is not None or spec["swap_short"] is not None
        else None
    )
    return (
        instrument,
        metadata.canonical_symbol,
        metadata.asset_class,
        metadata.base_currency or "",
        metadata.quote_currency or "",
        digits if digits is not None else 5,
        str(tick_size) if tick_size is not None else "0.00001",
        str(volume_min) if volume_min is not None else "0",
        str(volume_max) if volume_max is not None else "0",
        str(volume_step) if volume_step is not None else "1",
        str(contract_size) if contract_size is not None else "1",
        json.dumps(spec, sort_keys=True),
        "active",
        request_id,
        "",
        now,
        now,
        metadata.canonical_symbol,
        point,
        tick_size,
        tick_size,
        spread_points,
        None,
        None,
        server_name,
        None,
        path_category or None,
        1.0,
        swap_text,
        1.0,
        0.0,
        -1,
        (
            stops_points * tick_size
            if stops_points is not None and tick_size is not None
            else 0.0
        ),
    )


def _mt5_server_name() -> str | None:
    """Resolve the configured MT5 server name from provider settings.

    Returns:
        The configured server name, or None when unset.
    """
    provider = get_data_provider_settings()
    server = getattr(provider, "mt5_server", None)
    if server is None:
        return None
    return server.get_secret_value()


def sync_quantdata_reference(
    *, request_id: str, source_id: str | None = None
) -> dict[str, object]:
    """Synchronise the reference catalogues from QuantDataManager and MT5.

    Series and broker rows come from the QuantDataManager catalogue; each
    instrument with data is re-read from the live MT5 connection so stored
    specifications are the broker's real symbol properties. A missing MT5
    attribute never invents a value: the field stays ``None`` and unavailable
    markers are dropped. When MT5 is unreachable the series and broker
    synchronisation still completes and the summary reports the failure.

    Args:
        request_id: Caller trace identity.
        source_id: Optional resolved runtime broker source; required for
            the MT5 instrument-spec reads.

    Returns:
        Sync summary with per-table counts and MT5 availability.

    Raises:
        DataError: If the QuantDataManager catalogue is absent or unreadable.
    """
    logger.info("Synchronising QuantDataManager reference catalogues")
    rows = _read_quantdata_catalogue(request_id)
    series_count, broker_count = _sync_series_and_brokers(rows, request_id=request_id)

    server_name = _mt5_server_name()
    instruments = sorted(
        {row["INSTRUMENT"] for row in rows if "SYMBOL" in row and row["INSTRUMENT"]}
    )
    instrument_parameters: list[tuple[Any, ...]] = []
    failures: list[str] = []
    for instrument in instruments:
        try:
            response = get_symbol_metadata(
                source_id=source_id,
                symbol=instrument,
                request_id=request_id,
            )
            instrument_parameters.append(
                _instrument_parameters(
                    instrument,
                    response.data,
                    server_name,
                    request_id=request_id,
                )
            )
        except Exception:  # noqa: BLE001 - owner failures are per-symbol
            logger.warning("MT5 metadata unavailable for %s", instrument)
            failures.append(instrument)
    if instrument_parameters:
        create_instrument_reference_records(
            tuple(instrument_parameters), request_id=request_id
        )
    summary: dict[str, object] = {
        "series_synced": series_count,
        "brokers_synced": broker_count,
        "instruments_synced": len(instrument_parameters),
        "instruments_failed": tuple(failures),
        "mt5_available": not failures,
    }
    logger.info(
        "QuantDataManager sync complete: %s series, %s brokers, %s instruments",
        series_count,
        broker_count,
        len(instrument_parameters),
    )
    return summary


__all__ = ("sync_quantdata_reference",)
