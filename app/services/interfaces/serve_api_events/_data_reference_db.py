"""Database-backed Data reference projections for the D-IFACE boundary.

Serves the workstation's Data tab, symbol discovery, and chart bar history
from the hydrated reference tables in data/database/haruquantai.db:

* ``data_series`` - market-data series reference catalogue.
* ``data_brokers`` - broker profiles with customized-instrument counts.
* ``instruments`` - instrument specifications.
* ``data_bars`` - genuine broker-fetched bar history per (symbol, timeframe).

Every value served here is read from persisted rows; nothing is generated,
interpolated, or invented. A symbol/timeframe pair with no stored history
raises :class:`BarsUnavailableError` so the boundary can answer with an honest
typed failure instead of synthesized bars.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

_DEFAULT_DB_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
)

_MAX_PAGE_SIZE: Final = 200
_SECONDS_PER_DAY: Final = 86_400

_DATA_CAPABILITIES: Final[tuple[tuple[str, str, str], ...]] = (
    ("FEAT-DATA-01", "Market Data", "symbols, snapshots, and historical retrieval"),
    ("FEAT-DATA-02", "Datasets", "preparation, import, catalog, and manifests"),
    ("FEAT-DATA-03", "Synthetic Data", "seeded synthetic evidence"),
    ("FEAT-DATA-04", "Transformation", "closed bars and deterministic resampling"),
    ("FEAT-DATA-05", "Alignment", "backward-only multi-series alignment"),
    ("FEAT-DATA-06", "Integrity", "quality inspection and anomaly evidence"),
    ("FEAT-DATA-07", "Time and Sessions", "venue and named-session evidence"),
    ("FEAT-DATA-08", "Economic Calendar", "point-in-time releases and revisions"),
    ("FEAT-DATA-09", "Sources", "source readiness, licensing, and provenance"),
    ("FEAT-DATA-10", "Market Events", "ordered streaming and feed status"),
    ("FEAT-DATA-11", "Data Jobs", "bounded update and backfill state"),
    ("FEAT-DATA-12", "Evidence", "market, account, FX, and audit evidence"),
    ("FEAT-DATA-13", "Runtime Stores", "namespaced durable runtime state"),
    ("FEAT-DATA-14", "Replay", "availability-gated replay packages"),
)


class BarsUnavailableError(Exception):
    """Raised when no stored bar history exists for a symbol/timeframe pair."""


class ReferenceNotFoundError(LookupError):
    """Raised when a referenced series or instrument row does not exist."""


def _utc_now_iso() -> str:
    """Return the current UTC instant as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a row-factory SQLite connection to the boundary database.

    Args:
        db_path: Optional explicit database path.

    Returns:
        Connection with ``sqlite3.Row`` row factory.
    """
    target = Path(db_path) if db_path is not None else _DEFAULT_DB_PATH
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def _optional_int(value: int | str | None) -> int | None:
    """Coerce one database value to int when not None.

    Returns:
        Integer value, or None when the cell is null.
    """
    return int(value) if value is not None else None


def _optional_float(value: float | str | None) -> float | None:
    """Coerce one database value to float when not None.

    Returns:
        Float value, or None when the cell is null.
    """
    return float(value) if value is not None else None


def _clamp_limit(limit: int | None) -> int:
    """Clamp one requested page size to the boundary ceiling.

    Returns:
        Page size between 1 and the boundary ceiling.
    """
    if limit is None or limit < 1:
        return 50
    return min(limit, _MAX_PAGE_SIZE)


def list_capabilities() -> dict[str, Any]:
    """Return the bounded Data feature surface.

    Returns:
        Payload carrying fourteen capability summaries.
    """
    return {
        "capabilities": [
            {
                "feature_id": feature_id,
                "name": name,
                "summary": summary,
                "availability": "available",
            }
            for feature_id, name, summary in _DATA_CAPABILITIES
        ]
    }


def list_market_series(
    limit: int | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Project the market-data series reference catalogue.

    Args:
        limit: Bounded maximum series rows.
        db_path: Optional explicit database path.

    Returns:
        Payload conforming to the MarketSeries contract.
    """
    conn = _get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT series_id, symbol, instrument, filename, broker_id, usymbol,
                   timeframe, timezone, date_from, date_to, row_count, decimals,
                   source, data_type, show, remove_weekends
            FROM data_series
            ORDER BY series_id
            LIMIT ?
            """,
            (_clamp_limit(limit),),
        ).fetchall()
        series: list[dict[str, Any]] = []
        for row in rows:
            date_from = _optional_int(row["date_from"])
            date_to = _optional_int(row["date_to"])
            total_days = (
                (date_to - date_from) // _SECONDS_PER_DAY
                if date_from is not None and date_to is not None
                else None
            )
            series.append(
                {
                    "series_id": int(row["series_id"]),
                    "symbol": str(row["symbol"]),
                    "instrument": row["instrument"],
                    "document": row["filename"],
                    "broker_id": _optional_int(row["broker_id"]),
                    "usymbol": row["usymbol"],
                    "timeframe": row["timeframe"],
                    "timezone": row["timezone"],
                    "date_from": date_from,
                    "date_to": date_to,
                    "total_days": total_days,
                    "row_count": _optional_int(row["row_count"]),
                    "decimals": _optional_int(row["decimals"]),
                    "source": _optional_int(row["source"]),
                    "bar_type": "start_of_bar",
                    "data_type": _optional_int(row["data_type"]),
                    "show": _optional_int(row["show"]),
                    "remove_weekends": _optional_int(row["remove_weekends"]),
                }
            )
        return {"series": series}
    finally:
        conn.close()


def _broker_name_by_id(conn: sqlite3.Connection) -> dict[int, str]:
    """Map broker ids to display names from the broker profile table.

    Returns:
        Mapping of broker id to profile display name.
    """
    return {
        int(row["broker_id"]): str(row["name"])
        for row in conn.execute(
            "SELECT broker_id, name FROM data_brokers WHERE broker_id IS NOT NULL"
        )
    }


def list_instruments(
    limit: int | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Project instrument specification rows.

    Args:
        limit: Bounded maximum instrument rows.
        db_path: Optional explicit database path.

    Returns:
        Payload conforming to the Instruments contract.
    """
    conn = _get_connection(db_path)
    try:
        names = _broker_name_by_id(conn)
        rows = conn.execute(
            """
            SELECT symbol_id, description, broker_id, point_value,
                   contract_size_decimal, tick_size, default_spread,
                   default_slippage, asset_class, order_size_multiplier,
                   order_size_step
            FROM instruments
            ORDER BY symbol_id
            LIMIT ?
            """,
            (_clamp_limit(limit),),
        ).fetchall()
        instruments: list[dict[str, Any]] = []
        for row in rows:
            broker_id = _optional_int(row["broker_id"])
            instruments.append(
                {
                    "instrument": str(row["symbol_id"]),
                    "description": row["description"],
                    "broker_profile": names.get(broker_id) if broker_id else None,
                    "point_value": _optional_float(row["point_value"]),
                    "contract_size": row["contract_size_decimal"],
                    "tick_size": _optional_float(row["tick_size"]),
                    "default_spread": _optional_float(row["default_spread"]),
                    "default_slippage": _optional_float(row["default_slippage"]),
                    "data_type": row["asset_class"],
                    "order_size_multiplier": _optional_float(
                        row["order_size_multiplier"]
                    ),
                    "order_size_step": _optional_float(row["order_size_step"]),
                }
            )
        return {"instruments": instruments}
    finally:
        conn.close()


def list_brokers(
    limit: int | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Project broker profile rows with customized-instrument counts.

    Args:
        limit: Bounded maximum broker rows.
        db_path: Optional explicit database path.

    Returns:
        Payload conforming to the Brokers contract.
    """
    conn = _get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT b.broker_id, b.name, b.description, b.postfix, b.mt_timezone,
                   (SELECT count(*) FROM instruments i
                    WHERE i.broker_id = b.broker_id) AS customized
            FROM data_brokers b
            ORDER BY b.broker_id
            LIMIT ?
            """,
            (_clamp_limit(limit),),
        ).fetchall()
        brokers: list[dict[str, Any]] = []
        for row in rows:
            brokers.append(
                {
                    "broker_id": _optional_int(row["broker_id"]),
                    "name": row["name"],
                    "description": row["description"],
                    "postfix": row["postfix"],
                    "timezone": row["mt_timezone"],
                    "customized_instruments": int(row["customized"]),
                }
            )
        return {"brokers": brokers}
    finally:
        conn.close()


def list_symbols(
    source_id: str = "mt5",
    query: str | None = None,
    cursor: str | None = None,
    limit: int | None = None,
    request_id: str = "req-symbols",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Serve bounded provider-native symbol discovery from instruments.

    Args:
        source_id: Provider identity echoed to the caller.
        query: Optional substring filter on the symbol.
        cursor: Opaque last-symbol cursor from the previous page.
        limit: Bounded page size.
        request_id: Identifier of the invoking request.
        db_path: Optional explicit database path.

    Returns:
        Payload conforming to the SymbolPage contract.
    """
    page_size = _clamp_limit(limit)
    conn = _get_connection(db_path)
    try:
        sql = "SELECT canonical_symbol FROM instruments"
        conditions: list[str] = []
        params: list[Any] = []
        if query and query.strip():
            conditions.append("canonical_symbol LIKE ?")
            params.append(f"%{query.strip()}%")
        if cursor and cursor.strip():
            conditions.append("canonical_symbol > ?")
            params.append(cursor.strip())
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY canonical_symbol LIMIT ?"
        params.append(page_size + 1)
        rows = conn.execute(sql, params).fetchall()
        has_more = len(rows) > page_size
        selected = rows[:page_size]
        return {
            "source_id": source_id,
            "items": [str(row["canonical_symbol"]) for row in selected],
            "limit": page_size,
            "next_cursor": (
                str(selected[-1]["canonical_symbol"]) if has_more and selected else None
            ),
            "revision": "reference-v1",
            "request_id": request_id,
        }
    finally:
        conn.close()


def list_quotes(
    symbols: list[str],
    source_id: str = "mt5",
    request_id: str = "req-quotes",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Serve instrument-reference rows for an explicit symbol list.

    Live quote fields are served null: without a connected broker this is a
    reference projection only, never a fabricated price.

    Args:
        symbols: Exact symbols to project.
        source_id: Provider identity echoed to the caller.
        request_id: Identifier of the invoking request.
        db_path: Optional explicit database path.

    Returns:
        Payload conforming to the MarketDirectory contract.
    """
    conn = _get_connection(db_path)
    try:
        rows: list[dict[str, Any]] = []
        for symbol in symbols:
            row = conn.execute(
                """
                SELECT canonical_symbol, description, asset_class, digits,
                       default_spread
                FROM instruments WHERE canonical_symbol = ?
                """,
                (symbol,),
            ).fetchone()
            if row is None:
                continue
            rows.append(
                {
                    "symbol": str(row["canonical_symbol"]),
                    "name": str(row["description"] or row["canonical_symbol"]),
                    "asset_class": str(row["asset_class"]),
                    "source_id": source_id,
                    "digits": _optional_int(row["digits"]),
                    "last": None,
                    "bid": None,
                    "ask": None,
                    "spread": _optional_float(row["default_spread"]),
                    "volume": None,
                    "open": None,
                    "high": None,
                    "low": None,
                    "close": None,
                    "change": None,
                    "change_percent": None,
                }
            )
        return {
            "source_id": source_id,
            "rows": rows,
            "limit": max(len(rows), 1),
            "next_cursor": None,
            "revision": "reference-v1",
            "generated_at": _utc_now_iso(),
            "request_id": request_id,
        }
    finally:
        conn.close()


def _record_number(value: object) -> float | None:
    """Convert one stored bar field to a number without inventing values.

    Returns:
        Parsed float, or None when the stored value is null or non-numeric.
    """
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except TypeError, ValueError:
        return None


def _record_time(value: object) -> str | None:
    """Convert one stored bar timestamp to its wire string.

    Returns:
        Timestamp string, or None when the stored value is null.
    """
    return str(value) if value is not None else None


def _bar_time(bar: Mapping[str, str | float | None]) -> str | None:
    """Read one projected bar's timestamp without inventing a value.

    Returns:
        Bar-open time string, or None when absent.
    """
    time_value = bar.get("time")
    return time_value if isinstance(time_value, str) else None


def _bar_time_at_or_after(bar: Mapping[str, str | float | None], bound: str) -> bool:
    """Report whether one bar opens at or after the inclusive window start.

    Returns:
        True when the bar's open time exists and is at or after the bound.
    """
    time_value = _bar_time(bar)
    return time_value is not None and time_value >= bound


def _bar_time_at_or_before(bar: Mapping[str, str | float | None], bound: str) -> bool:
    """Report whether one bar opens at or before the inclusive window end.

    Returns:
        True when the bar's open time exists and is at or before the bound.
    """
    time_value = _bar_time(bar)
    return time_value is not None and time_value <= bound


def get_bars(
    symbol: str,
    timeframe: str,
    limit: int = 500,
    start: str | None = None,
    end: str | None = None,
    request_id: str = "req-bars",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Serve one bounded bar history from the persisted reference store.

    Args:
        symbol: Broker-native symbol to read.
        timeframe: Canonical timeframe key.
        limit: Maximum number of most-recent bars.
        start: Optional inclusive ISO-8601 window start.
        end: Optional inclusive ISO-8601 window end.
        request_id: Identifier of the invoking request.
        db_path: Optional explicit database path.

    Returns:
        Payload conforming to the BarSeries contract.

    Raises:
        BarsUnavailableError: When no stored history exists for the pair or the
            window filters every stored bar away.
    """
    conn = _get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT records_json, start, end FROM data_bars
            WHERE symbol = ? AND timeframe = ?
            """,
            (symbol, timeframe),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        missing = f"No {timeframe} bar history is stored for {symbol}"
        raise BarsUnavailableError(missing)
    try:
        records = json.loads(str(row["records_json"]))
    except (TypeError, ValueError) as error:
        unreadable = f"Stored {timeframe} history for {symbol} is unreadable"
        raise BarsUnavailableError(unreadable) from error
    bars = [
        {
            "time": _record_time(record.get("timestamp")),
            "open": _record_number(record.get("open")),
            "high": _record_number(record.get("high")),
            "low": _record_number(record.get("low")),
            "close": _record_number(record.get("close")),
            "volume": _record_number(record.get("volume")),
        }
        for record in records
        if isinstance(record, dict)
    ]
    if start is not None:
        bars = [bar for bar in bars if _bar_time_at_or_after(bar, start)]
    if end is not None:
        bars = [bar for bar in bars if _bar_time_at_or_before(bar, end)]
    if not bars:
        empty = f"No {timeframe} bars are stored for {symbol} in the requested window"
        raise BarsUnavailableError(empty)
    bounded = bars[-limit:] if limit > 0 else bars
    return {
        "source_id": "mt5",
        "symbol": symbol,
        "timeframe": timeframe,
        "bars": bounded,
        "count": len(bounded),
        "start": bounded[0]["time"],
        "end": bounded[-1]["time"],
        "cache_status": "hit",
        "request_id": request_id,
    }


def sync_reference(db_path: Path | str | None = None) -> dict[str, Any]:
    """Report the persisted reference catalogue state honestly.

    The reference catalogue is hydrated at startup from the reference
    database; this operation reports what is persisted and that no live MT5
    terminal participated, rather than claiming a broker sync that did not
    happen.

    Args:
        db_path: Optional explicit database path.

    Returns:
        Payload conforming to the ReferenceSyncSummary contract.
    """
    conn = _get_connection(db_path)
    try:
        series_synced = int(
            conn.execute("SELECT count(*) FROM data_series").fetchone()[0]
        )
        brokers_synced = int(
            conn.execute("SELECT count(*) FROM data_brokers").fetchone()[0]
        )
        instruments_synced = int(
            conn.execute("SELECT count(*) FROM instruments").fetchone()[0]
        )
    finally:
        conn.close()
    return {
        "series_synced": series_synced,
        "brokers_synced": brokers_synced,
        "instruments_synced": instruments_synced,
        "instruments_failed": [],
        "mt5_available": False,
    }


_INSTRUMENT_COLUMNS: Final[tuple[str, ...]] = (
    "description",
    "point_value",
    "tick_size",
    "tick_step",
    "default_spread",
    "default_slippage",
    "min_distance",
    "order_size_multiplier",
    "order_size_step",
)


def _instrument_spec_row(conn: sqlite3.Connection, instrument: str) -> sqlite3.Row:
    """Read one instrument row or raise :class:`ReferenceNotFoundError`.

    Returns:
        The matched instrument row.

    Raises:
        ReferenceNotFoundError: When the instrument identity is unknown.
    """
    row: sqlite3.Row | None = conn.execute(
        """
        SELECT symbol_id, description, broker_id, point_value,
               contract_size_decimal, tick_size, tick_step, default_spread,
               default_slippage, data_type, order_size_multiplier,
               order_size_step, min_distance, swap
        FROM instruments WHERE symbol_id = ?
        """,
        (instrument,),
    ).fetchone()
    if row is None:
        missing = f"INSTRUMENT_NOT_FOUND: {instrument}"
        raise ReferenceNotFoundError(missing)
    return row


def _instrument_spec_projection(
    conn: sqlite3.Connection, row: sqlite3.Row
) -> dict[str, Any]:
    """Project one instrument row into the InstrumentSpec contract shape.

    Returns:
        Payload conforming to the InstrumentSpec contract.
    """
    names = _broker_name_by_id(conn)
    broker_id = _optional_int(row["broker_id"])
    return {
        "instrument": str(row["symbol_id"]),
        "description": row["description"],
        "broker_profile": names.get(broker_id) if broker_id else None,
        "point_value": _optional_float(row["point_value"]),
        "contract_size": row["contract_size_decimal"],
        "tick_size": _optional_float(row["tick_size"]),
        "tick_step": _optional_float(row["tick_step"]),
        "default_spread": _optional_float(row["default_spread"]),
        "default_slippage": _optional_float(row["default_slippage"]),
        "data_type": _optional_int(row["data_type"]),
        "order_size_multiplier": _optional_float(row["order_size_multiplier"]),
        "order_size_step": _optional_float(row["order_size_step"]),
        "min_distance": _optional_float(row["min_distance"]),
        "swap": row["swap"],
    }


def get_instrument_spec(
    instrument: str,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Read one full instrument specification.

    Args:
        instrument: Instrument identity (the Data ``symbol_id``).
        db_path: Optional explicit database path.

    Returns:
        Payload conforming to the InstrumentSpec contract.

    Raises:
        ReferenceNotFoundError: When the instrument is unknown.
    """
    conn = _get_connection(db_path)
    try:
        return _instrument_spec_projection(conn, _instrument_spec_row(conn, instrument))
    finally:
        conn.close()


def _parameterized_update(
    table: str, updates: dict[str, object], key_column: str, key: object
) -> tuple[str, tuple[object, ...]]:
    """Build one parameterized UPDATE statement from a column whitelist.

    Column names come exclusively from the static whitelists in this module,
    never from request data; request values are bound parameters.

    Args:
        table: Target table name.
        updates: Whitelisted column-to-value updates.
        key_column: Key column for the WHERE clause.
        key: Key value for the WHERE clause.

    Returns:
        SQL string and bound parameter tuple.
    """
    assignments = ", ".join(f"{column} = ?" for column in updates)
    # Table, column, and key names are module-owned compile-time constants;
    # every request-derived value binds through a parameter placeholder.
    sql = (
        f"UPDATE {table} SET {assignments}, updated_at = ? "  # noqa: S608
        f"WHERE {key_column} = ?"
    )
    return sql, (*updates.values(), _utc_now_iso(), key)


def _apply_instrument_fields(
    conn: sqlite3.Connection, instrument: str, body: Mapping[str, object]
) -> None:
    """Apply optional spec fields from one update body to an instrument row."""
    updates: dict[str, object] = {}
    for column in _INSTRUMENT_COLUMNS:
        if column in body and body[column] is not None:
            updates[column] = body[column]
    if updates:
        sql, params = _parameterized_update(
            "instruments", updates, "symbol_id", instrument
        )
        conn.execute(sql, params)


def update_market_series(
    series_id: int,
    body: Mapping[str, object],
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Apply one governed edit to a series row and its linked instrument.

    Args:
        series_id: Series identity to update.
        body: Series and instrument fields to apply.
        db_path: Optional explicit database path.

    Returns:
        Updated series summary conforming to the UpdatedSeries contract.

    Raises:
        ValueError: When the body lacks a non-empty symbol or instrument.
        ReferenceNotFoundError: When the series row does not exist.
    """
    symbol = str(body.get("symbol") or "").strip()
    instrument = str(body.get("instrument") or "").strip()
    if not symbol or not instrument:
        raise ValueError("SERIES_IDENTITY_REQUIRED")
    conn = _get_connection(db_path)
    try:
        with conn:
            existing = conn.execute(
                "SELECT 1 FROM data_series WHERE series_id = ?", (series_id,)
            ).fetchone()
            if existing is None:
                missing = f"SERIES_NOT_FOUND: {series_id}"
                raise ReferenceNotFoundError(missing)
            series_fields: dict[str, object] = {
                "broker_id": body.get("broker_id"),
                "timeframe": body.get("timeframe"),
                "timezone": body.get("timezone"),
                "date_from": body.get("date_from"),
                "date_to": body.get("date_to"),
                "data_type": body.get("data_type"),
                "decimals": body.get("decimals"),
                "source": body.get("source"),
                "row_count": body.get("row_count"),
                "remove_weekends": body.get("remove_weekends"),
                "show": body.get("show"),
                "symbol": symbol,
                "instrument": instrument,
            }
            updates = {
                column: value
                for column, value in series_fields.items()
                if value is not None
            }
            sql, params = _parameterized_update(
                "data_series", updates, "series_id", series_id
            )
            conn.execute(sql, params)
            description = body.get("description")
            if description is not None:
                conn.execute(
                    "UPDATE instruments SET description = ?, updated_at = ? "
                    "WHERE symbol_id = ?",
                    (description, _utc_now_iso(), instrument),
                )
            _apply_instrument_fields(conn, instrument, body)
    finally:
        conn.close()
    return {
        "series_id": series_id,
        "symbol": symbol,
        "instrument": instrument,
        "bar_type": "start_of_bar",
    }


def update_instrument_spec(
    instrument: str,
    body: Mapping[str, object],
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Apply one governed edit to an instrument specification.

    Args:
        instrument: Instrument identity to update.
        body: Optional spec fields to apply.
        db_path: Optional explicit database path.

    Returns:
        Updated InstrumentSpec payload.

    Raises:
        ReferenceNotFoundError: When the instrument is unknown.
    """
    conn = _get_connection(db_path)
    try:
        with conn:
            _instrument_spec_row(conn, instrument)
            _apply_instrument_fields(conn, instrument, body)
        return _instrument_spec_projection(conn, _instrument_spec_row(conn, instrument))
    finally:
        conn.close()
