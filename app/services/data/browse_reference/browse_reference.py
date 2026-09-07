"""Database-backed Market Reference Browser implementation.

Owns market-data reference tables (data, broker, instruments, data_bars)
and projects them into capabilities, market series, instruments, brokers,
symbols, quotes, historical bars, and market directory rows.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

from app.contracts.common.models import JsonObject, ProblemDetails
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    BrowseReferenceRequest,
    BrowseReferenceSuccess,
)
from app.services.data.browse_reference.config import BrowseReferenceConfig
from app.services.data.browse_reference.reference_repository import (
    MarketDataReferenceRepository,
)

logger = logging.getLogger(__name__)

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

_SUPPORTED_TIMEFRAMES: Final[frozenset[str]] = frozenset(
    {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"}
)


class BarsUnavailableError(Exception):
    """Raised when no stored bar history exists for a symbol/timeframe pair."""


class ReferenceNotFoundError(LookupError):
    """Raised when a referenced series or instrument row does not exist."""


def _utc_now_iso() -> str:
    """Return the current UTC instant as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()


def _optional_int(value: int | str | None) -> int | None:
    """Coerce one database value to int when not None."""
    return int(value) if value is not None else None


def _optional_float(value: float | str | None) -> float | None:
    """Coerce one database value to float when not None."""
    return float(value) if value is not None else None


def _clamp_limit(limit: int | None) -> int:
    """Clamp one requested page size to the boundary ceiling."""
    if limit is None or limit < 1:
        return 50
    return min(limit, _MAX_PAGE_SIZE)


def _record_number(value: object) -> float | None:
    """Safely convert a scalar cell to float."""
    if value is None:
        return None
    try:
        return float(str(value))
    except ValueError, TypeError:
        return None


def _record_time(value: object) -> str | None:
    """Normalize a record timestamp to an ISO-8601 string."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:
        return text if text.endswith("Z") else f"{text}Z"
    if " " in text:
        return f"{text.replace(' ', 'T')}Z"
    return text


def _bar_time(bar: Mapping[str, Any]) -> str | None:
    """Extract a normalized timestamp string from a bar dictionary."""
    candidate = bar.get("time") or bar.get("timestamp") or bar.get("date")
    return _record_time(candidate)


def _bar_time_at_or_after(bar: Mapping[str, Any], bound: str) -> bool:
    """Return True if bar timestamp is >= bound."""
    t = _bar_time(bar)
    return t is not None and t >= bound


def _bar_time_at_or_before(bar: Mapping[str, Any], bound: str) -> bool:
    """Return True if bar timestamp is <= bound."""
    t = _bar_time(bar)
    return t is not None and t <= bound


class BrowseReferenceService:
    """Service owning market reference data persistence and queries."""

    def __init__(self, config: BrowseReferenceConfig | None = None) -> None:
        """Initialize reference browsing service with configured SQLite path."""
        self._config = config or BrowseReferenceConfig()
        self._db_path = Path(self._config.database_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._repo = MarketDataReferenceRepository(db_path=self._db_path)
        self._closed = False
        self._init_db()

    @property
    def closed(self) -> bool:
        """Return True if the service connection has been closed."""
        return self._closed

    def close(self) -> None:
        """Close SQLite database connection."""
        if not self._closed:
            self._conn.close()
            self._closed = True

    def _init_db(self) -> None:
        """Initialize database tables and seed from dev database if available."""
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS broker (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                desc TEXT,
                timezone TEXT,
                customized INTEGER DEFAULT 0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS instruments (
                name VARCHAR(64) PRIMARY KEY,
                description VARCHAR(255),
                path VARCHAR(255),
                category VARCHAR(64),
                exchange VARCHAR(64),
                bank VARCHAR(64),
                isin VARCHAR(32),
                basis VARCHAR(64),
                formula VARCHAR(255),
                page VARCHAR(255),
                currency_base VARCHAR(16),
                currency_profit VARCHAR(16),
                currency_margin VARCHAR(16),
                custom BOOLEAN DEFAULT FALSE,
                chart_mode INTEGER,
                select_mode BOOLEAN,
                visible BOOLEAN,
                time BIGINT,
                digits INTEGER,
                point DOUBLE PRECISION,
                spread INTEGER,
                spread_float BOOLEAN,
                ticks_bookdepth INTEGER,
                bid DOUBLE PRECISION,
                bidhigh DOUBLE PRECISION,
                bidlow DOUBLE PRECISION,
                ask DOUBLE PRECISION,
                askhigh DOUBLE PRECISION,
                asklow DOUBLE PRECISION,
                last DOUBLE PRECISION,
                lasthigh DOUBLE PRECISION,
                lastlow DOUBLE PRECISION,
                volume BIGINT,
                volumehigh BIGINT,
                volumelow BIGINT,
                volume_real DOUBLE PRECISION,
                volumehigh_real DOUBLE PRECISION,
                volumelow_real DOUBLE PRECISION,
                trade_calc_mode INTEGER,
                trade_mode INTEGER,
                trade_exemode INTEGER,
                trade_stops_level INTEGER,
                trade_freeze_level INTEGER,
                trade_contract_size DOUBLE PRECISION,
                trade_tick_size DOUBLE PRECISION,
                trade_tick_value DOUBLE PRECISION,
                trade_tick_value_profit DOUBLE PRECISION,
                trade_tick_value_loss DOUBLE PRECISION,
                trade_accrued_interest DOUBLE PRECISION,
                trade_face_value DOUBLE PRECISION,
                trade_liquidity_rate DOUBLE PRECISION,
                volume_min DOUBLE PRECISION,
                volume_max DOUBLE PRECISION,
                volume_step DOUBLE PRECISION,
                volume_limit DOUBLE PRECISION,
                order_mode INTEGER,
                order_gtc_mode INTEGER,
                filling_mode INTEGER,
                expiration_mode INTEGER,
                start_time BIGINT,
                expiration_time BIGINT,
                swap_mode INTEGER,
                swap_rollover3days INTEGER,
                swap_long DOUBLE PRECISION,
                swap_short DOUBLE PRECISION,
                margin_initial DOUBLE PRECISION,
                margin_maintenance DOUBLE PRECISION,
                margin_hedged DOUBLE PRECISION,
                margin_hedged_use_leg BOOLEAN,
                session_deals INTEGER,
                session_buy_orders INTEGER,
                session_sell_orders INTEGER,
                session_volume DOUBLE PRECISION,
                session_turnover DOUBLE PRECISION,
                session_interest DOUBLE PRECISION,
                session_buy_orders_volume DOUBLE PRECISION,
                session_sell_orders_volume DOUBLE PRECISION,
                session_open DOUBLE PRECISION,
                session_close DOUBLE PRECISION,
                session_aw DOUBLE PRECISION,
                session_price_settlement DOUBLE PRECISION,
                session_price_limit_min DOUBLE PRECISION,
                session_price_limit_max DOUBLE PRECISION,
                option_mode INTEGER,
                option_right VARCHAR(16),
                option_strike DOUBLE PRECISION,
                price_change DOUBLE PRECISION,
                price_volatility DOUBLE PRECISION,
                price_theoretical DOUBLE PRECISION,
                price_sensitivity DOUBLE PRECISION,
                price_greeks_delta DOUBLE PRECISION,
                price_greeks_theta DOUBLE PRECISION,
                price_greeks_gamma DOUBLE PRECISION,
                price_greeks_vega DOUBLE PRECISION,
                price_greeks_rho DOUBLE PRECISION,
                price_greeks_omega DOUBLE PRECISION
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY,
                source_data_id INTEGER,
                connection TEXT,
                symbol TEXT NOT NULL,
                instrument TEXT,
                timeframe TEXT,
                timezone TEXT,
                filename TEXT,
                date_from INTEGER,
                date_to INTEGER,
                data_type INTEGER,
                row_count INTEGER,
                decimals INTEGER,
                source INTEGER,
                seconds_records INTEGER,
                usymbol TEXT,
                usymbol_name TEXT,
                remove_weekends INTEGER,
                show INTEGER,
                basket_id INTEGER,
                broker_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS data_bars (
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                records_json TEXT NOT NULL,
                start TEXT,
                end TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (symbol, timeframe)
            )
            """
        )
        self._conn.commit()

        # Seed from dev DB if empty and available
        dev_path = self._db_path.parent / "haruquant-dev.db"
        if dev_path.exists():
            self._seed_from_dev(dev_path)

    def _seed_instruments(self, cur: sqlite3.Cursor, dev_cur: sqlite3.Cursor) -> None:
        """Seed instruments table from dev DB."""
        cur.execute("SELECT count(*) FROM instruments")
        if cur.fetchone()[0] == 0:
            try:
                inst = dev_cur.execute("SELECT * FROM data_instruments").fetchall()
                if inst:
                    placeholders = ", ".join(["?"] * len(inst[0]))
                    cur.executemany(
                        f"INSERT OR IGNORE INTO instruments VALUES ({placeholders})",  # noqa: S608
                        inst,
                    )
            except sqlite3.OperationalError:
                pass

    def _seed_data_series(self, cur: sqlite3.Cursor, dev_cur: sqlite3.Cursor) -> None:
        """Seed data table from dev DB."""
        cur.execute("SELECT count(*) FROM data")
        if cur.fetchone()[0] == 0:
            try:
                series = dev_cur.execute(
                    """
                    SELECT
                        series_id, source_data_id, connection, symbol,
                        instrument, timeframe, timezone, filename,
                        date_from, date_to, data_type, row_count,
                        decimals, source, seconds_records, usymbol,
                        usymbol_name, remove_weekends, show, basket_id,
                        broker_id, created_at, updated_at
                    FROM data_market_series
                    """
                ).fetchall()
                if series:
                    placeholders = ", ".join(["?"] * len(series[0]))
                    cur.executemany(
                        f"INSERT OR IGNORE INTO data VALUES ({placeholders})",  # noqa: S608
                        series,
                    )
            except sqlite3.OperationalError:
                pass

    def _seed_data_bars(self, cur: sqlite3.Cursor, dev_cur: sqlite3.Cursor) -> None:
        """Seed data_bars table from dev DB cache."""
        cur.execute("SELECT count(*) FROM data_bars")
        if cur.fetchone()[0] != 0:
            return
        try:
            best: dict[tuple[str, str], dict[str, Any]] = {}
            for (payload,) in dev_cur.execute(
                "SELECT dataset_json FROM data_cache"
            ).fetchall():
                try:
                    dataset = json.loads(str(payload))
                except TypeError, ValueError:
                    continue
                if dataset.get("data_kind") != "bars":
                    continue
                records = dataset.get("records") or []
                if not records:
                    continue
                symbol = str(dataset.get("symbol") or "")
                timeframe = str(dataset.get("timeframe") or "")
                if not symbol or not timeframe:
                    continue
                end = str(dataset.get("end") or "")
                current = best.get((symbol, timeframe))
                if current is None or end > current["end"]:
                    best[(symbol, timeframe)] = {
                        "records": records,
                        "start": dataset.get("start"),
                        "end": end,
                    }
            for (symbol, timeframe), entry in sorted(best.items()):
                cur.execute(
                    """
                    INSERT OR IGNORE INTO data_bars (
                        symbol, timeframe, records_json,
                        start, end, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        symbol,
                        timeframe,
                        json.dumps(entry["records"]),
                        entry["start"],
                        entry["end"],
                        _utc_now_iso(),
                    ),
                )
        except sqlite3.OperationalError:
            pass

    def _seed_from_dev(self, dev_path: Path) -> None:
        """Seed empty tables from reference development database if available."""
        try:
            with sqlite3.connect(str(dev_path)) as dev_conn:
                dev_cur = dev_conn.cursor()
                cur = self._conn.cursor()
                self._seed_instruments(cur, dev_cur)
                self._seed_data_series(cur, dev_cur)
                self._seed_data_bars(cur, dev_cur)
                self._conn.commit()
        except sqlite3.Error as err:
            logger.debug("Optional seeding from dev DB skipped: %s", err)

    def list_capabilities(self) -> dict[str, Any]:
        """Return the bounded Data feature surface."""
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

    def list_market_series(self, limit: int | None = None) -> dict[str, Any]:
        """Project the market-data series reference catalogue."""
        rows = self._conn.execute(
            """
            SELECT id, symbol, instrument, filename, broker_id, usymbol,
                   timeframe, timezone, date_from, date_to, row_count, decimals,
                   source, data_type, show, remove_weekends
            FROM data
            ORDER BY id
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
                    "id": int(row["id"]),
                    "series_id": int(row["id"]),
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

    def _broker_name_by_id(self) -> dict[int, str]:
        """Fetch a mapping from broker ID to broker name."""
        mapping: dict[int, str] = {}
        try:
            for row in self._conn.execute("SELECT id, name FROM broker").fetchall():
                if row["id"] is not None and row["name"]:
                    mapping[int(row["id"])] = str(row["name"])
        except sqlite3.OperationalError:
            pass
        return mapping

    def list_instruments(self, limit: int | None = None) -> dict[str, Any]:
        """Project instrument specifications from the instruments table."""
        rows = self._conn.execute(
            """
            SELECT name, description, point,
                   trade_contract_size, trade_tick_size, spread,
                   path, volume_min, volume_step
            FROM instruments
            ORDER BY name
            LIMIT ?
            """,
            (_clamp_limit(limit),),
        ).fetchall()
        instruments: list[dict[str, Any]] = []
        for row in rows:
            instruments.append(
                {
                    "instrument": str(row["name"]),
                    "description": row["description"],
                    "broker_profile": None,
                    "point_value": _optional_float(row["point"]),
                    "contract_size": str(row["trade_contract_size"]),
                    "tick_size": _optional_float(row["trade_tick_size"]),
                    "default_spread": _optional_float(row["spread"]),
                    "default_slippage": 0.0,
                    "data_type": row["path"],
                    "order_size_multiplier": _optional_float(row["volume_min"]),
                    "order_size_step": _optional_float(row["volume_step"]),
                }
            )
        return {"instruments": instruments}

    def list_brokers(self, limit: int | None = None) -> dict[str, Any]:
        """Project broker profile rows with customized-instrument counts."""
        try:
            rows = self._conn.execute(
                """
                SELECT b.id AS broker_id, b.name,
                       COALESCE(b.desc, '') AS description,
                       COALESCE(b.timezone, 'UTC') AS timezone,
                       0 AS customized
                FROM broker b
                ORDER BY b.id
                LIMIT ?
                """,
                (_clamp_limit(limit),),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
        brokers: list[dict[str, Any]] = []
        for row in rows:
            brokers.append(
                {
                    "broker_id": _optional_int(row["broker_id"]),
                    "name": row["name"],
                    "description": row["description"],
                    "postfix": "",
                    "timezone": row["timezone"],
                    "customized_instruments": int(row["customized"]),
                }
            )
        return {"brokers": brokers}

    def list_symbols(
        self,
        source_id: str = "mt5",
        query: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Serve bounded provider-native symbol discovery from instruments."""
        page_size = _clamp_limit(limit)
        sql = "SELECT name AS canonical_symbol FROM instruments"
        conditions: list[str] = []
        params: list[Any] = []
        if query and query.strip():
            conditions.append("name LIKE ?")
            params.append(f"%{query.strip()}%")
        if cursor and cursor.strip():
            conditions.append("name > ?")
            params.append(cursor.strip())
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY name LIMIT ?"
        params.append(page_size + 1)
        rows = self._conn.execute(sql, params).fetchall()
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
            "request_id": request_id or "req-symbols",
        }

    def list_quotes(
        self,
        symbols: list[str] | tuple[str, ...],
        source_id: str = "mt5",
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Serve instrument-reference rows for an explicit symbol list."""
        rows: list[dict[str, Any]] = []
        for symbol in symbols:
            row = self._conn.execute(
                """
                SELECT name, description, path, digits, spread
                FROM instruments WHERE name = ?
                """,
                (symbol,),
            ).fetchone()
            if row is None:
                continue
            rows.append(
                {
                    "symbol": str(row["name"]),
                    "name": str(row["description"] or row["name"]),
                    "asset_class": str(row["path"] or "Forex"),
                    "source_id": source_id,
                    "digits": _optional_int(row["digits"]),
                    "last": None,
                    "bid": None,
                    "ask": None,
                    "spread": _optional_float(row["spread"]),
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
            "request_id": request_id or "req-quotes",
        }

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        start: str | None = None,
        end: str | None = None,
        _request_id: str | None = None,
    ) -> dict[str, Any]:
        """Read genuine broker-fetched bar history per (symbol, timeframe)."""
        if not symbol or not symbol.strip():
            raise ValueError("symbol is required")
        if timeframe not in _SUPPORTED_TIMEFRAMES:
            msg = f"timeframe unsupported: {timeframe}"
            raise ValueError(msg)
        if start and end and start > end:
            raise ValueError("Bar history start bound must not follow end bound.")

        row = self._conn.execute(
            """
            SELECT records_json, start, end
            FROM data_bars
            WHERE symbol = ? AND timeframe = ?
            """,
            (symbol, timeframe),
        ).fetchone()

        if row is None:
            msg = f"No stored bar history exists for {symbol} on {timeframe}."
            raise BarsUnavailableError(msg)

        try:
            records = json.loads(str(row["records_json"]))
        except json.JSONDecodeError, TypeError:
            records = []

        if start:
            records = [b for b in records if _bar_time_at_or_after(b, start)]
        if end:
            records = [b for b in records if _bar_time_at_or_before(b, end)]

        selected = records[-limit:] if len(records) > limit else records
        normalized_bars: list[dict[str, Any]] = []
        for b in selected:
            t = _bar_time(b)
            normalized_bars.append(
                {
                    "time": t,
                    "open": _record_number(b.get("open")),
                    "high": _record_number(b.get("high")),
                    "low": _record_number(b.get("low")),
                    "close": _record_number(b.get("close")),
                    "volume": _record_number(b.get("volume") or b.get("tick_volume")),
                }
            )

        bar_start = normalized_bars[0]["time"] if normalized_bars else row["start"]
        bar_end = normalized_bars[-1]["time"] if normalized_bars else row["end"]

        return {
            "source_id": "data.bars@1",
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(normalized_bars),
            "bars": normalized_bars,
            "cache_status": "hit",
            "start": bar_start,
            "end": bar_end,
        }

    def sync_reference(self) -> dict[str, Any]:
        """Project reference synchronisation report."""
        series_count = self._conn.execute("SELECT count(*) FROM data").fetchone()[0]
        try:
            brokers_count = self._conn.execute(
                "SELECT count(*) FROM broker"
            ).fetchone()[0]
        except sqlite3.OperationalError:
            brokers_count = 0
        instruments_count = self._conn.execute(
            "SELECT count(*) FROM instruments"
        ).fetchone()[0]

        return {
            "series_synced": int(series_count),
            "brokers_synced": int(brokers_count),
            "instruments_synced": int(instruments_count),
            "mt5_available": False,
            "instruments_failed": [],
        }

    def get_instrument_spec(self, instrument: str) -> dict[str, Any]:
        """Fetch specification for one instrument."""
        row = self._conn.execute(
            """
            SELECT name, description, point, trade_contract_size,
                   trade_tick_size, spread, path, volume_min, volume_step,
                   trade_stops_level, swap_mode, swap_rollover3days,
                   swap_long, swap_short, currency_base, currency_profit, digits
            FROM instruments WHERE name = ?
            """,
            (instrument,),
        ).fetchone()
        if row is None:
            msg = f"INSTRUMENT_NOT_FOUND: {instrument}"
            raise ReferenceNotFoundError(msg)
        return {
            "instrument": str(row["name"]),
            "description": row["description"] or str(row["name"]),
            "broker_profile": "SQ default",
            "point_value": _optional_float(row["point"]),
            "contract_size": _optional_float(row["trade_contract_size"]),
            "tick_size": _optional_float(row["trade_tick_size"]),
            "tick_step": _optional_float(row["trade_tick_size"]),
            "default_spread": _optional_float(row["spread"]),
            "default_slippage": 0.0,
            "data_type": row["path"] or "Forex",
            "order_size_multiplier": _optional_float(row["volume_min"]),
            "order_size_step": _optional_float(row["volume_step"]),
            "min_distance": _optional_float(row["trade_stops_level"]) or 0.0,
            "swap": str(row["swap_long"]) if row["swap_long"] is not None else None,
            "swap_mode": _optional_int(row["swap_mode"]) or 0,
            "swap_long": _optional_float(row["swap_long"]) or 0.0,
            "swap_short": _optional_float(row["swap_short"]) or 0.0,
            "swap_rollover3days": _optional_int(row["swap_rollover3days"]) or 3,
        }

    def update_instrument_spec(
        self,
        instrument: str,
        fields: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Update specification fields for one instrument."""
        existing = self._conn.execute(
            "SELECT 1 FROM instruments WHERE name = ?", (instrument,)
        ).fetchone()
        if existing is None:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO instruments ("
                    "name, description, point, trade_contract_size, "
                    "trade_tick_size, spread, path, volume_min, volume_step"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        instrument,
                        instrument,
                        0.0001,
                        100000.0,
                        0.0001,
                        0,
                        "Forex",
                        1.0,
                        0.0,
                    ),
                )
        updates: dict[str, object] = {}
        field_mapping = {
            "description": "description",
            "default_spread": "spread",
            "spread": "spread",
            "point_value": "point",
            "point": "point",
            "tick_size": "trade_tick_size",
            "trade_tick_size": "trade_tick_size",
            "contract_size": "trade_contract_size",
            "trade_contract_size": "trade_contract_size",
            "order_size_multiplier": "volume_min",
            "volume_min": "volume_min",
            "order_size_step": "volume_step",
            "volume_step": "volume_step",
            "min_distance": "trade_stops_level",
            "trade_stops_level": "trade_stops_level",
            "data_type": "path",
            "path": "path",
            "swap_mode": "swap_mode",
            "swap_long": "swap_long",
            "swap_short": "swap_short",
            "swap_rollover3days": "swap_rollover3days",
        }
        for field, col in field_mapping.items():
            if field in fields and fields[field] is not None:
                updates[col] = fields[field]
        if updates:
            assignments = ", ".join(f"{col} = ?" for col in updates)
            sql = f"UPDATE instruments SET {assignments} WHERE name = ?"  # noqa: S608
            with self._conn:
                self._conn.execute(sql, (*updates.values(), instrument))
        return self.get_instrument_spec(instrument)

    def update_market_series(
        self,
        series_id: int,
        fields: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Update market series row by series ID and linked instrument."""
        symbol = str(fields.get("symbol") or "").strip()
        instrument = str(fields.get("instrument") or "").strip()
        if not symbol or not instrument:
            raise ValueError("SERIES_IDENTITY_REQUIRED")
        existing = self._conn.execute(
            "SELECT 1 FROM data WHERE id = ?", (series_id,)
        ).fetchone()
        if existing is None:
            msg = f"SERIES_NOT_FOUND: {series_id}"
            raise ReferenceNotFoundError(msg)

        series_fields: dict[str, object] = {
            "broker_id": fields.get("broker_id"),
            "timeframe": fields.get("timeframe"),
            "timezone": fields.get("timezone"),
            "date_from": fields.get("date_from"),
            "date_to": fields.get("date_to"),
            "data_type": fields.get("data_type"),
            "decimals": fields.get("decimals"),
            "source": fields.get("source"),
            "row_count": fields.get("row_count"),
            "remove_weekends": fields.get("remove_weekends"),
            "show": fields.get("show"),
            "symbol": symbol,
            "instrument": instrument,
        }
        updates = {k: v for k, v in series_fields.items() if v is not None}
        assignments = ", ".join(f"{col} = ?" for col in updates)
        sql = f"UPDATE data SET {assignments}, updated_at = ? WHERE id = ?"  # noqa: S608
        with self._conn:
            self._conn.execute(sql, (*updates.values(), _utc_now_iso(), series_id))
            description = fields.get("description")
            if description is not None:
                self._conn.execute(
                    "UPDATE instruments SET description = ? WHERE name = ?",
                    (description, instrument),
                )
            self.update_instrument_spec(instrument, fields)
        return {
            "series_id": series_id,
            "symbol": symbol,
            "instrument": instrument,
            "bar_type": "start_of_bar",
        }

    def list_market_directory(
        self,
        query: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
        request_id: str = "req-markets",
    ) -> dict[str, Any]:
        """Read market directory rows from instruments table."""
        sql = """
            SELECT
                name AS symbol,
                coalesce(description, name) AS name,
                coalesce(nullif(category, ''), path, 'Forex') AS asset_class,
                digits,
                spread
            FROM instruments
        """
        params: list[Any] = []
        conditions: list[str] = []
        if query and query.strip():
            conditions.append("(name LIKE ? OR description LIKE ?)")
            q = f"%{query.strip()}%"
            params.extend([q, q])
        if cursor and cursor.strip():
            conditions.append("name > ?")
            params.append(cursor.strip())
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY name LIMIT ?"
        params.append(limit + 1)

        raw_rows = self._conn.execute(sql, params).fetchall()
        has_more = len(raw_rows) > limit
        selected_rows = raw_rows[:limit]
        next_cursor = (
            str(selected_rows[-1]["symbol"]) if (has_more and selected_rows) else None
        )

        rows: list[dict[str, Any]] = []
        for r in selected_rows:
            rows.append(
                {
                    "symbol": str(r["symbol"]),
                    "name": str(r["name"]),
                    "asset_class": str(r["asset_class"]),
                    "source_id": "mt5",
                    "digits": int(r["digits"]) if r["digits"] is not None else 5,
                    "last": None,
                    "bid": None,
                    "ask": None,
                    "spread": float(r["spread"]) if r["spread"] is not None else None,
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
            "source_id": "mt5",
            "rows": rows,
            "limit": limit,
            "next_cursor": next_cursor,
            "revision": "v1",
            "generated_at": _utc_now_iso(),
            "request_id": request_id,
        }

    def _dispatch_catalogue(
        self,
        request: BrowseReferenceRequest,
    ) -> BrowseReferenceSuccess | DataFailure | None:
        """Dispatch catalogue read operations."""
        op = request.operation
        data: dict[str, Any] | None = None
        if op == "LIST_CAPABILITIES":
            data = self.list_capabilities()
        elif op == "LIST_SERIES":
            data = self.list_market_series(limit=request.limit)
        elif op == "LIST_INSTRUMENTS":
            data = self.list_instruments(limit=request.limit)
        elif op == "LIST_BROKERS":
            data = self.list_brokers(limit=request.limit)
        elif op == "SYNC_REFERENCE":
            data = self.sync_reference()
        elif op == "READ_INSTRUMENT":
            try:
                data = self.get_instrument_spec(request.instrument or "")
            except ReferenceNotFoundError as e:
                return DataFailure(
                    request_id=request.request_id,
                    code="DATA_NOT_FOUND",
                    problem=ProblemDetails(
                        title="Instrument Not Found",
                        detail=str(e),
                        status=404,
                        code="INSTRUMENT_NOT_FOUND",
                    ),
                )
        else:
            return None

        return BrowseReferenceSuccess(request_id=request.request_id, data=data)

    def _dispatch_market(
        self,
        request: BrowseReferenceRequest,
    ) -> BrowseReferenceSuccess | DataFailure | None:
        """Dispatch market query and bar history operations."""
        op = request.operation
        if op == "DISCOVER_SYMBOLS":
            data = self.list_symbols(
                source_id=request.source_id or "mt5",
                query=request.query,
                cursor=request.cursor,
                limit=request.limit or 50,
                request_id=str(request.request_id),
            )
            return BrowseReferenceSuccess(request_id=request.request_id, data=data)
        if op == "READ_QUOTES":
            data = self.list_quotes(
                list(request.symbols),
                source_id=request.source_id or "mt5",
                request_id=str(request.request_id),
            )
            return BrowseReferenceSuccess(request_id=request.request_id, data=data)
        if op == "READ_BARS":
            return self._handle_read_bars(request)
        if op == "LIST_MARKET_DIRECTORY":
            data = self.list_market_directory(
                query=request.query,
                cursor=request.cursor,
                limit=request.limit or 50,
                request_id=str(request.request_id),
            )
            return BrowseReferenceSuccess(request_id=request.request_id, data=data)
        return None

    def _handle_read_bars(
        self,
        request: BrowseReferenceRequest,
    ) -> BrowseReferenceSuccess | DataFailure:
        """Handle READ_BARS query with mapped error envelopes."""
        try:
            data = self.get_bars(
                request.symbol or "",
                request.timeframe or "",
                limit=request.limit or 500,
                start=request.start,
                end=request.end,
                _request_id=str(request.request_id),
            )
            return BrowseReferenceSuccess(request_id=request.request_id, data=data)
        except BarsUnavailableError as e:
            if request.symbol:
                parquet_bars = self._repo.read_bars(
                    symbol=request.symbol,
                    timeframe=request.timeframe or "M1",
                    start=request.start,
                    end=request.end,
                    limit=request.limit or 500,
                )
                if parquet_bars:
                    start_str = (
                        datetime.fromtimestamp(
                            parquet_bars[0]["time"], tz=UTC
                        ).isoformat()
                        if parquet_bars
                        else None
                    )
                    end_str = (
                        datetime.fromtimestamp(
                            parquet_bars[-1]["time"], tz=UTC
                        ).isoformat()
                        if parquet_bars
                        else None
                    )
                    return BrowseReferenceSuccess(
                        request_id=request.request_id,
                        data=cast(
                            "JsonObject",
                            {
                                "source_id": "data.bars.parquet@1",
                                "symbol": request.symbol,
                                "timeframe": request.timeframe or "M1",
                                "count": len(parquet_bars),
                                "bars": parquet_bars,
                                "cache_status": "hit_parquet",
                                "start": start_str,
                                "end": end_str,
                            },
                        ),
                    )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_FEED_UNAVAILABLE",
                problem=ProblemDetails(
                    title="Bars Unavailable",
                    detail=str(e),
                    status=503,
                    code="UPSTREAM_UNAVAILABLE",
                ),
            )
        except ValueError as e:
            msg = str(e)
            code = (
                "BAR_WINDOW_INVALID"
                if "start bound must not follow end bound" in msg
                else "VALIDATION_FAILED"
            )
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    title="Validation Failed",
                    detail=msg,
                    status=422,
                    code=code,
                ),
            )

    def _dispatch_mutation(
        self,
        request: BrowseReferenceRequest,
    ) -> BrowseReferenceSuccess | DataFailure | None:
        """Dispatch instrument and series write operations."""
        op = request.operation
        if op == "UPDATE_INSTRUMENT":
            return self._handle_update_instrument(request)
        if op == "UPDATE_SERIES":
            return self._handle_update_series(request)
        return None

    def _handle_update_instrument(
        self,
        request: BrowseReferenceRequest,
    ) -> BrowseReferenceSuccess | DataFailure:
        """Handle instrument update mutation."""
        try:
            data = self.update_instrument_spec(
                request.instrument or "", request.payload
            )
            return BrowseReferenceSuccess(request_id=request.request_id, data=data)
        except ReferenceNotFoundError as e:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_NOT_FOUND",
                problem=ProblemDetails(
                    title="Instrument Not Found",
                    detail=str(e),
                    status=404,
                    code="INSTRUMENT_NOT_FOUND",
                ),
            )

    def _handle_update_series(
        self,
        request: BrowseReferenceRequest,
    ) -> BrowseReferenceSuccess | DataFailure:
        """Handle series update mutation."""
        if request.series_id is None:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    title="Validation Failed",
                    detail="series_id is required",
                    status=422,
                    code="VALIDATION_FAILED",
                ),
            )
        try:
            data = self.update_market_series(request.series_id, request.payload)
            return BrowseReferenceSuccess(request_id=request.request_id, data=data)
        except ReferenceNotFoundError as e:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_NOT_FOUND",
                problem=ProblemDetails(
                    title="Series Not Found",
                    detail=str(e),
                    status=404,
                    code="SERIES_NOT_FOUND",
                ),
            )
        except ValueError as e:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    title="Validation Failed",
                    detail=str(e),
                    status=422,
                    code="VALIDATION_FAILED",
                ),
            )

    async def browse_reference(
        self,
        request: BrowseReferenceRequest,
    ) -> BrowseReferenceSuccess | DataFailure:
        """Handle operation-discriminated reference browsing requests."""
        if self._closed:
            return DataFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    title="Service Closed",
                    detail="BrowseReferenceService has been closed.",
                    status=503,
                    code="CAPABILITY_UNAVAILABLE",
                ),
            )

        cat_res = self._dispatch_catalogue(request)
        if cat_res is not None:
            return cat_res

        mkt_res = self._dispatch_market(request)
        if mkt_res is not None:
            return mkt_res

        mut_res = self._dispatch_mutation(request)
        if mut_res is not None:
            return mut_res

        # Delegate QuantDataManager operations to MarketDataReferenceRepository
        return await self._repo.browse_reference(request)


if __name__ == "__main__":
    svc = BrowseReferenceService()
    caps = svc.list_capabilities()
    print(
        f"BrowseReferenceService operational: {len(caps['capabilities'])} capabilities"
    )
    svc.close()
