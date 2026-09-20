"""Transactional SQLite persistence feature for the Data domain.

Feature:
    FEAT-PERSISTENCE-DATA

Purpose:
    Provides durable storage, parameterized SQL execution, and transactional
    invariants for instrument specifications, broker aliases, session profiles,
    immutable dataset manifests, dynamic asset baskets, and quality reports
    under namespace `data.v1`.

Invariants:
    * All database interactions are strictly parameterized and transaction-safe.
    * Datasets are immutable; manifests cannot be silently overwritten.
    * Dates and timestamps are stored as ISO-8601 UTC strings.
    * Default sessions and standard instruments are deterministically pre-seeded.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, override

from app.contracts.data import (
    DATA_PERSISTENCE,
    BasketConstituent,
    BrokerAlias,
    DatasetImmutableError,
    DatasetManifest,
    InstrumentDefinition,
    QualityAnomaly,
    QualityAnomalyType,
    QualityReport,
    SessionDefinition,
    SessionWindow,
    UniverseBasket,
)
from app.contracts.data import (
    DataPersistenceService as IDataPersistenceService,
)
from app.contracts.persistence import (
    DATABASE_SERVICE,
    DatabaseService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Pre-seeded Default Data Profiles
# ---------------------------------------------------------------------------

PRESEEDED_INSTRUMENTS: tuple[dict[str, Any], ...] = (
    {
        "symbol": "EURUSD",
        "description": "Euro / US Dollar",
        "tick_size": 0.00001,
        "tick_step": 0.00001,
        "tick_value_in_money": 10.0,
        "point_value": 100000.0,
        "decimals": 5,
        "default_spread": 0.0001,
        "data_type": "Forex",
    },
    {
        "symbol": "GBPUSD",
        "description": "British Pound / US Dollar",
        "tick_size": 0.00001,
        "tick_step": 0.00001,
        "tick_value_in_money": 10.0,
        "point_value": 100000.0,
        "decimals": 5,
        "default_spread": 0.00015,
        "data_type": "Forex",
    },
    {
        "symbol": "USDJPY",
        "description": "US Dollar / Japanese Yen",
        "tick_size": 0.001,
        "tick_step": 0.001,
        "tick_value_in_money": 9.1,
        "point_value": 100000.0,
        "decimals": 3,
        "default_spread": 0.015,
        "data_type": "Forex",
    },
    {
        "symbol": "BTCUSD",
        "description": "Bitcoin / US Dollar",
        "tick_size": 0.01,
        "tick_step": 0.01,
        "tick_value_in_money": 1.0,
        "point_value": 1.0,
        "decimals": 2,
        "default_spread": 5.0,
        "data_type": "Crypto",
    },
    {
        "symbol": "SP500",
        "description": "S&P 500 Index CFD",
        "tick_size": 0.1,
        "tick_step": 0.1,
        "tick_value_in_money": 1.0,
        "point_value": 1.0,
        "decimals": 1,
        "default_spread": 0.4,
        "data_type": "CFD",
    },
)

DATA_SCHEMA_SQL: str = """
CREATE TABLE IF NOT EXISTS data_instruments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    connection TEXT DEFAULT '',
    broker_id INTEGER DEFAULT 0,
    description TEXT DEFAULT '',
    tick_size REAL NOT NULL DEFAULT 0.00001,
    tick_step REAL NOT NULL DEFAULT 0.00001,
    tick_value_in_money REAL NOT NULL DEFAULT 10.0,
    point_value REAL NOT NULL DEFAULT 100000.0,
    decimals INTEGER NOT NULL DEFAULT 5,
    default_spread REAL NOT NULL DEFAULT 0.0001,
    default_slippage REAL NOT NULL DEFAULT 0.0,
    min_volume REAL NOT NULL DEFAULT 0.01,
    max_volume REAL NOT NULL DEFAULT 100.0,
    lot_step REAL NOT NULL DEFAULT 0.01,
    margin_rate REAL NOT NULL DEFAULT 0.05,
    swap_long REAL NOT NULL DEFAULT 0.0,
    swap_short REAL NOT NULL DEFAULT 0.0,
    swap_3day_day INTEGER NOT NULL DEFAULT 3,
    commissions TEXT DEFAULT '0.0',
    data_type TEXT DEFAULT 'Forex',
    alias TEXT DEFAULT '',
    exchange TEXT DEFAULT '',
    country TEXT DEFAULT '',
    sector TEXT DEFAULT '',
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_instrument_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_symbol TEXT NOT NULL,
    alias_symbol TEXT NOT NULL UNIQUE,
    broker_id INTEGER DEFAULT 0,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS data_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    timezone TEXT NOT NULL DEFAULT 'UTC',
    windows_json TEXT NOT NULL DEFAULT '[]',
    holidays_json TEXT NOT NULL DEFAULT '[]',
    is_default INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS data_datasets (
    dataset_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    data_kind TEXT NOT NULL,
    source_id TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    parquet_path TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    quality_score REAL NOT NULL DEFAULT 1.0,
    lineage_json TEXT NOT NULL DEFAULT '{}',
    created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_baskets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    is_system INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS data_basket_constituents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    basket_id INTEGER NOT NULL REFERENCES data_baskets(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    date_from TEXT,
    date_to TEXT
);

CREATE TABLE IF NOT EXISTS data_quality_reports (
    report_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    quality_score REAL NOT NULL,
    total_records INTEGER NOT NULL,
    anomalies_json TEXT NOT NULL DEFAULT '[]',
    anomaly_counts_json TEXT NOT NULL DEFAULT '{}',
    evaluated_at_utc TEXT NOT NULL
);
"""

_SCHEMA_SQL: str = DATA_SCHEMA_SQL


@dataclass(slots=True)
class DataPersistenceConfig:
    """Configuration for data persistence service."""

    preseed_defaults: bool = True


class DataPersistenceServiceImpl(IDataPersistenceService):
    """SQLite implementation of Data domain persistence."""

    def __init__(
        self,
        db: DatabaseService,
        config: DataPersistenceConfig | None = None,
    ) -> None:
        """Initialize data persistence service.

        Args:
            db: Transactional database service.
            config: Optional configuration.
        """
        self._db = db
        self._config = config or DataPersistenceConfig()

    @override
    async def initialize_schema(self) -> None:
        """Create and migrate database tables for the data domain."""
        self._db.execute_script(_SCHEMA_SQL)
        if self._config.preseed_defaults:
            await self._preseed()

    async def _preseed(self) -> None:
        """Deterministically seed default instruments and sessions."""
        now_iso = datetime.now(UTC).isoformat()
        for inst in PRESEEDED_INSTRUMENTS:
            self._db.execute_mutation(
                """
                INSERT OR IGNORE INTO data_instruments (
                    symbol, description, tick_size, tick_step, tick_value_in_money,
                    point_value, decimals, default_spread, data_type,
                    created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inst["symbol"],
                    inst["description"],
                    inst["tick_size"],
                    inst["tick_step"],
                    inst["tick_value_in_money"],
                    inst["point_value"],
                    inst["decimals"],
                    inst["default_spread"],
                    inst["data_type"],
                    now_iso,
                    now_iso,
                ),
            )

        # Default Sessions: 24/5 Forex, US Equities, 24/7 Crypto
        forex_windows = [
            {"day_of_week": i, "open_time": "00:00:00", "close_time": "23:59:59"}
            for i in range(5)
        ]
        self._db.execute_mutation(
            """
            INSERT OR IGNORE INTO data_sessions (
                name, description, timezone, windows_json, holidays_json, is_default
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "24/5 Forex",
                "Standard 24/5 Foreign Exchange trading hours",
                "UTC",
                json.dumps(forex_windows),
                json.dumps([]),
                1,
            ),
        )

        us_windows = [
            {"day_of_week": i, "open_time": "09:30:00", "close_time": "16:00:00"}
            for i in range(5)
        ]
        self._db.execute_mutation(
            """
            INSERT OR IGNORE INTO data_sessions (
                name, description, timezone, windows_json, holidays_json, is_default
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "US Equities",
                "US Regular Trading Hours (NYSE/NASDAQ)",
                "America/New_York",
                json.dumps(us_windows),
                json.dumps([]),
                0,
            ),
        )

        crypto_windows = [
            {"day_of_week": i, "open_time": "00:00:00", "close_time": "23:59:59"}
            for i in range(7)
        ]
        self._db.execute_mutation(
            """
            INSERT OR IGNORE INTO data_sessions (
                name, description, timezone, windows_json, holidays_json, is_default
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "24/7 Crypto",
                "Continuous 24/7 Cryptocurrency trading hours",
                "UTC",
                json.dumps(crypto_windows),
                json.dumps([]),
                0,
            ),
        )

    # -----------------------------------------------------------------------
    # Instruments
    # -----------------------------------------------------------------------

    def _row_to_instrument(self, row: dict[str, Any]) -> InstrumentDefinition:
        """Map a database row to an InstrumentDefinition DTO."""
        return InstrumentDefinition(
            id=int(row["id"]),
            symbol=str(row["symbol"]),
            connection=str(row["connection"] or ""),
            broker_id=int(row["broker_id"] or 0),
            description=str(row["description"] or ""),
            tick_size=float(row["tick_size"]),
            tick_step=float(row["tick_step"]),
            tick_value_in_money=float(row["tick_value_in_money"]),
            point_value=float(row["point_value"]),
            decimals=int(row["decimals"]),
            default_spread=float(row["default_spread"]),
            default_slippage=float(row["default_slippage"]),
            min_volume=float(row["min_volume"]),
            max_volume=float(row["max_volume"]),
            lot_step=float(row["lot_step"]),
            margin_rate=float(row["margin_rate"]),
            swap_long=float(row["swap_long"]),
            swap_short=float(row["swap_short"]),
            swap_3day_day=int(row["swap_3day_day"]),
            commissions=str(row["commissions"] or "0.0"),
            data_type=str(row["data_type"] or "Forex"),
            alias=str(row["alias"] or ""),
            exchange=str(row["exchange"] or ""),
            country=str(row["country"] or ""),
            sector=str(row["sector"] or ""),
            created_at=datetime.fromisoformat(str(row["created_at_utc"])),
            updated_at=datetime.fromisoformat(str(row["updated_at_utc"])),
        )

    @override
    async def get_instrument(self, symbol: str) -> InstrumentDefinition | None:
        """Retrieve instrument definition by symbol."""
        rows = self._db.execute_query(
            "SELECT * FROM data_instruments WHERE symbol = ?",
            (symbol.upper(),),
        )
        if not rows:
            return None
        return self._row_to_instrument(rows[0])

    @override
    async def list_instruments(
        self, data_type: str | None = None
    ) -> list[InstrumentDefinition]:
        """List all instruments, optionally filtered by type."""
        if data_type:
            rows = self._db.execute_query(
                "SELECT * FROM data_instruments "
                "WHERE data_type = ? ORDER BY symbol ASC",
                (data_type,),
            )
        else:
            rows = self._db.execute_query(
                "SELECT * FROM data_instruments ORDER BY symbol ASC"
            )
        return [self._row_to_instrument(r) for r in rows]

    @override
    async def save_instrument(
        self, instrument: InstrumentDefinition
    ) -> InstrumentDefinition:
        """Save or update an instrument definition."""
        now_iso = datetime.now(UTC).isoformat()
        self._db.execute_mutation(
            """
            INSERT INTO data_instruments (
                symbol, connection, broker_id, description, tick_size, tick_step,
                tick_value_in_money, point_value, decimals, default_spread,
                default_slippage, min_volume, max_volume, lot_step, margin_rate,
                swap_long, swap_short, swap_3day_day, commissions, data_type,
                alias, exchange, country, sector, created_at_utc, updated_at_utc
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(symbol) DO UPDATE SET
                connection = excluded.connection,
                broker_id = excluded.broker_id,
                description = excluded.description,
                tick_size = excluded.tick_size,
                tick_step = excluded.tick_step,
                tick_value_in_money = excluded.tick_value_in_money,
                point_value = excluded.point_value,
                decimals = excluded.decimals,
                default_spread = excluded.default_spread,
                default_slippage = excluded.default_slippage,
                min_volume = excluded.min_volume,
                max_volume = excluded.max_volume,
                lot_step = excluded.lot_step,
                margin_rate = excluded.margin_rate,
                swap_long = excluded.swap_long,
                swap_short = excluded.swap_short,
                swap_3day_day = excluded.swap_3day_day,
                commissions = excluded.commissions,
                data_type = excluded.data_type,
                alias = excluded.alias,
                exchange = excluded.exchange,
                country = excluded.country,
                sector = excluded.sector,
                updated_at_utc = excluded.updated_at_utc
            """,
            (
                instrument.symbol.upper(),
                instrument.connection,
                instrument.broker_id,
                instrument.description,
                instrument.tick_size,
                instrument.tick_step,
                instrument.tick_value_in_money,
                instrument.point_value,
                instrument.decimals,
                instrument.default_spread,
                instrument.default_slippage,
                instrument.min_volume,
                instrument.max_volume,
                instrument.lot_step,
                instrument.margin_rate,
                instrument.swap_long,
                instrument.swap_short,
                instrument.swap_3day_day,
                instrument.commissions,
                instrument.data_type,
                instrument.alias,
                instrument.exchange,
                instrument.country,
                instrument.sector,
                now_iso,
                now_iso,
            ),
        )
        saved = await self.get_instrument(instrument.symbol.upper())
        if saved is None:
            msg = f"Instrument {instrument.symbol} could not be retrieved after save"
            raise RuntimeError(msg)
        return saved

    @override
    async def delete_instrument(self, symbol: str) -> bool:
        """Delete an instrument definition by symbol."""
        affected = self._db.execute_mutation(
            "DELETE FROM data_instruments WHERE symbol = ?",
            (symbol.upper(),),
        )
        return affected > 0

    # -----------------------------------------------------------------------
    # Broker Aliases
    # -----------------------------------------------------------------------

    @override
    async def get_alias(
        self, alias_symbol: str, broker_id: int | None = None
    ) -> str | None:
        """Resolve alias symbol to canonical symbol."""
        if broker_id is not None:
            rows = self._db.execute_query(
                """
                SELECT canonical_symbol FROM data_instrument_aliases
                WHERE alias_symbol = ? AND broker_id = ?
                """,
                (alias_symbol, broker_id),
            )
            if rows:
                return str(rows[0]["canonical_symbol"])

        rows = self._db.execute_query(
            "SELECT canonical_symbol FROM data_instrument_aliases "
            "WHERE alias_symbol = ?",
            (alias_symbol,),
        )
        if not rows:
            return None
        return str(rows[0]["canonical_symbol"])

    @override
    async def save_alias(self, alias: BrokerAlias) -> BrokerAlias:
        """Save or update a broker alias mapping."""
        self._db.execute_mutation(
            """
            INSERT INTO data_instrument_aliases (
                canonical_symbol, alias_symbol, broker_id, notes
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(alias_symbol) DO UPDATE SET
                canonical_symbol = excluded.canonical_symbol,
                broker_id = excluded.broker_id,
                notes = excluded.notes
            """,
            (
                alias.canonical_symbol.upper(),
                alias.alias_symbol,
                alias.broker_id,
                alias.notes,
            ),
        )
        return alias

    @override
    async def list_aliases(self, symbol: str | None = None) -> list[BrokerAlias]:
        """List registered broker aliases."""
        if symbol:
            rows = self._db.execute_query(
                """
                SELECT * FROM data_instrument_aliases
                WHERE canonical_symbol = ? ORDER BY alias_symbol ASC
                """,
                (symbol.upper(),),
            )
        else:
            rows = self._db.execute_query(
                "SELECT * FROM data_instrument_aliases ORDER BY canonical_symbol ASC"
            )
        return [
            BrokerAlias(
                id=int(r["id"]),
                canonical_symbol=str(r["canonical_symbol"]),
                alias_symbol=str(r["alias_symbol"]),
                broker_id=int(r["broker_id"]),
                notes=str(r["notes"] or ""),
            )
            for r in rows
        ]

    # -----------------------------------------------------------------------
    # Trading Sessions
    # -----------------------------------------------------------------------

    def _row_to_session(self, row: dict[str, Any]) -> SessionDefinition:
        """Map database row to SessionDefinition DTO."""
        windows_data = json.loads(str(row["windows_json"]))
        windows = [
            SessionWindow(
                day_of_week=w["day_of_week"],
                open_time=w["open_time"],
                close_time=w["close_time"],
            )
            for w in windows_data
        ]
        holidays_data = json.loads(str(row["holidays_json"]))
        return SessionDefinition(
            id=int(row["id"]),
            name=str(row["name"]),
            description=str(row["description"] or ""),
            timezone=str(row["timezone"]),
            windows=windows,
            holidays=list(holidays_data),
            is_default=bool(row["is_default"]),
        )

    @override
    async def get_session(self, name: str) -> SessionDefinition | None:
        """Retrieve trading session definition by name."""
        rows = self._db.execute_query(
            "SELECT * FROM data_sessions WHERE name = ?",
            (name,),
        )
        if not rows:
            return None
        return self._row_to_session(rows[0])

    @override
    async def list_sessions(self) -> list[SessionDefinition]:
        """List all configured trading sessions."""
        rows = self._db.execute_query(
            "SELECT * FROM data_sessions ORDER BY is_default DESC, name ASC"
        )
        return [self._row_to_session(r) for r in rows]

    @override
    async def save_session(self, session: SessionDefinition) -> SessionDefinition:
        """Save or update a trading session definition."""
        windows_json = json.dumps(
            [
                {
                    "day_of_week": w.day_of_week,
                    "open_time": w.open_time,
                    "close_time": w.close_time,
                }
                for w in session.windows
            ]
        )
        holidays_json = json.dumps(session.holidays)

        self._db.execute_mutation(
            """
            INSERT INTO data_sessions (
                name, description, timezone, windows_json, holidays_json, is_default
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                description = excluded.description,
                timezone = excluded.timezone,
                windows_json = excluded.windows_json,
                holidays_json = excluded.holidays_json,
                is_default = excluded.is_default
            """,
            (
                session.name,
                session.description,
                session.timezone,
                windows_json,
                holidays_json,
                1 if session.is_default else 0,
            ),
        )
        saved = await self.get_session(session.name)
        if saved is None:
            msg = f"Session {session.name} could not be retrieved after save"
            raise RuntimeError(msg)
        return saved

    # -----------------------------------------------------------------------
    # Datasets
    # -----------------------------------------------------------------------

    def _row_to_manifest(self, row: dict[str, Any]) -> DatasetManifest:
        """Map database row to DatasetManifest DTO."""
        return DatasetManifest(
            dataset_id=str(row["dataset_id"]),
            symbol=str(row["symbol"]),
            timeframe=str(row["timeframe"]),
            data_kind=str(row["data_kind"]),
            source_id=str(row["source_id"]),
            start_time=datetime.fromisoformat(str(row["start_time"])),
            end_time=datetime.fromisoformat(str(row["end_time"])),
            row_count=int(row["row_count"]),
            parquet_path=str(row["parquet_path"]),
            sha256_hash=str(row["sha256_hash"]),
            schema_version=int(row["schema_version"]),
            quality_score=float(row["quality_score"]),
            lineage=json.loads(str(row["lineage_json"])),
            created_at=datetime.fromisoformat(str(row["created_at_utc"])),
        )

    @override
    async def get_dataset_manifest(self, dataset_id: str) -> DatasetManifest | None:
        """Retrieve dataset manifest by ID."""
        rows = self._db.execute_query(
            "SELECT * FROM data_datasets WHERE dataset_id = ?",
            (dataset_id,),
        )
        if not rows:
            return None
        return self._row_to_manifest(rows[0])

    @override
    async def list_dataset_manifests(
        self, symbol: str | None = None, timeframe: str | None = None
    ) -> list[DatasetManifest]:
        """List dataset manifests matching filters."""
        query = "SELECT * FROM data_datasets WHERE 1=1"
        params: list[Any] = []
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol.upper())
        if timeframe:
            query += " AND timeframe = ?"
            params.append(timeframe)
        query += " ORDER BY created_at_utc DESC"

        rows = self._db.execute_query(query, tuple(params))
        return [self._row_to_manifest(r) for r in rows]

    @override
    async def save_dataset_manifest(self, manifest: DatasetManifest) -> DatasetManifest:
        """Save an immutable dataset manifest.

        Re-saving identical manifest is idempotent.
        """
        existing = await self.get_dataset_manifest(manifest.dataset_id)
        if existing is not None:
            if (
                existing.sha256_hash != manifest.sha256_hash
                or existing.row_count != manifest.row_count
                or existing.start_time != manifest.start_time
                or existing.end_time != manifest.end_time
                or existing.parquet_path != manifest.parquet_path
                or existing.quality_score != manifest.quality_score
            ):
                msg = (
                    f"Cannot alter immutable dataset manifest {manifest.dataset_id}: "
                    "semantic fields differ from existing record."
                )
                raise DatasetImmutableError(msg)
            return existing

        now_iso = datetime.now(UTC).isoformat()
        self._db.execute_mutation(
            """
            INSERT INTO data_datasets (
                dataset_id, symbol, timeframe, data_kind, source_id, start_time,
                end_time, row_count, parquet_path, sha256_hash, schema_version,
                quality_score, lineage_json, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                manifest.dataset_id,
                manifest.symbol.upper(),
                manifest.timeframe,
                manifest.data_kind,
                manifest.source_id,
                manifest.start_time.isoformat(),
                manifest.end_time.isoformat(),
                manifest.row_count,
                manifest.parquet_path,
                manifest.sha256_hash,
                manifest.schema_version,
                manifest.quality_score,
                json.dumps(manifest.lineage),
                now_iso,
            ),
        )
        return manifest

    # -----------------------------------------------------------------------
    # Universes & Baskets
    # -----------------------------------------------------------------------

    @override
    async def get_basket(self, name_or_id: str | int) -> UniverseBasket | None:
        """Retrieve asset basket by name or ID."""
        if isinstance(name_or_id, int):
            rows = self._db.execute_query(
                "SELECT * FROM data_baskets WHERE id = ?",
                (name_or_id,),
            )
        else:
            rows = self._db.execute_query(
                "SELECT * FROM data_baskets WHERE name = ?",
                (name_or_id,),
            )
        if not rows:
            return None

        basket_row = rows[0]
        basket_id = int(basket_row["id"])
        c_rows = self._db.execute_query(
            "SELECT * FROM data_basket_constituents "
            "WHERE basket_id = ? ORDER BY symbol ASC",
            (basket_id,),
        )
        constituents = [
            BasketConstituent(
                id=int(c["id"]),
                basket_id=basket_id,
                symbol=str(c["symbol"]),
                date_from=datetime.fromisoformat(str(c["date_from"]))
                if c["date_from"]
                else None,
                date_to=datetime.fromisoformat(str(c["date_to"]))
                if c["date_to"]
                else None,
            )
            for c in c_rows
        ]
        return UniverseBasket(
            id=basket_id,
            name=str(basket_row["name"]),
            description=str(basket_row["description"] or ""),
            is_system=bool(basket_row["is_system"]),
            constituents=constituents,
        )

    @override
    async def list_baskets(self) -> list[UniverseBasket]:
        """List all asset baskets."""
        rows = self._db.execute_query("SELECT id FROM data_baskets ORDER BY name ASC")
        result: list[UniverseBasket] = []
        for r in rows:
            b = await self.get_basket(int(r["id"]))
            if b:
                result.append(b)
        return result

    @override
    async def save_basket(self, basket: UniverseBasket) -> UniverseBasket:
        """Save or update an asset basket."""
        self._db.execute_mutation(
            """
            INSERT INTO data_baskets (name, description, is_system)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                description = excluded.description,
                is_system = excluded.is_system
            """,
            (basket.name, basket.description, 1 if basket.is_system else 0),
        )
        saved = await self.get_basket(basket.name)
        if saved is None:
            msg = f"Basket {basket.name} could not be retrieved after save"
            raise RuntimeError(msg)

        # Sync constituents
        self._db.execute_mutation(
            "DELETE FROM data_basket_constituents WHERE basket_id = ?",
            (saved.id,),
        )
        for c in basket.constituents:
            self._db.execute_mutation(
                """
                INSERT INTO data_basket_constituents (
                    basket_id, symbol, date_from, date_to
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    saved.id,
                    c.symbol.upper(),
                    c.date_from.isoformat() if c.date_from else None,
                    c.date_to.isoformat() if c.date_to else None,
                ),
            )
        refreshed = await self.get_basket(saved.id)
        return refreshed or saved

    @override
    async def delete_basket(self, basket_id: int) -> bool:
        """Delete an asset basket by ID."""
        affected = self._db.execute_mutation(
            "DELETE FROM data_baskets WHERE id = ?",
            (basket_id,),
        )
        return affected > 0

    # -----------------------------------------------------------------------
    # Quality Reports
    # -----------------------------------------------------------------------

    @override
    async def save_quality_report(self, report: QualityReport) -> QualityReport:
        """Save a quality evaluation report."""
        anomalies_data = [
            {
                "anomaly_type": str(a.anomaly_type),
                "timestamp": a.timestamp.isoformat(),
                "description": a.description,
                "severity": a.severity,
                "observed_value": a.observed_value,
                "expected_range": a.expected_range,
            }
            for a in report.anomalies
        ]
        self._db.execute_mutation(
            """
            INSERT INTO data_quality_reports (
                report_id, dataset_id, quality_score, total_records,
                anomalies_json, anomaly_counts_json, evaluated_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_id) DO UPDATE SET
                quality_score = excluded.quality_score,
                total_records = excluded.total_records,
                anomalies_json = excluded.anomalies_json,
                anomaly_counts_json = excluded.anomaly_counts_json,
                evaluated_at_utc = excluded.evaluated_at_utc
            """,
            (
                report.report_id,
                report.dataset_id,
                report.quality_score,
                report.total_records,
                json.dumps(anomalies_data),
                json.dumps(report.anomaly_counts),
                report.evaluated_at.isoformat(),
            ),
        )
        return report

    @override
    async def get_quality_report(self, report_id: str) -> QualityReport | None:
        """Retrieve a quality evaluation report by ID."""
        rows = self._db.execute_query(
            "SELECT * FROM data_quality_reports WHERE report_id = ?",
            (report_id,),
        )
        if not rows:
            return None
        r = rows[0]
        anomalies_raw = json.loads(str(r["anomalies_json"]))
        anomalies = [
            QualityAnomaly(
                anomaly_type=QualityAnomalyType(a["anomaly_type"]),
                timestamp=datetime.fromisoformat(a["timestamp"]),
                description=a["description"],
                severity=a["severity"],
                observed_value=float(a["observed_value"]),
                expected_range=tuple(a["expected_range"])
                if a.get("expected_range")
                else None,
            )
            for a in anomalies_raw
        ]
        counts = json.loads(str(r["anomaly_counts_json"]))
        return QualityReport(
            report_id=str(r["report_id"]),
            dataset_id=str(r["dataset_id"]),
            quality_score=float(r["quality_score"]),
            total_records=int(r["total_records"]),
            anomalies=anomalies,
            anomaly_counts=counts,
            evaluated_at=datetime.fromisoformat(str(r["evaluated_at_utc"])),
        )


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.data",
    provides=frozenset({DATA_PERSISTENCE}),
    requires=frozenset({DATABASE_SERVICE}),
    optional=frozenset(),
    description="Transactional SQLite persistence for Data domain under data.v1.",
)


class DataPersistenceFeature:
    """Wire data persistence service into kernel composition lifecycle."""

    def __init__(self, config: DataPersistenceConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional data persistence configuration.
        """
        self._config = config or DataPersistenceConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Initialize schema and publish data persistence service.

        Args:
            context: Lifecycle feature context.
        """
        db = context.require(DATABASE_SERVICE)
        service = DataPersistenceServiceImpl(db, self._config)
        await service.initialize_schema()
        context.provide(DATA_PERSISTENCE, service)
        logger.info("persistence_data_feature_started")


def feature() -> DataPersistenceFeature:
    """Return an unmounted DataPersistenceFeature instance.

    Returns:
        New DataPersistenceFeature instance.
    """
    return DataPersistenceFeature()


__all__ = [
    "DATA_SCHEMA_SQL",
    "PRESEEDED_INSTRUMENTS",
    "SPEC",
    "DataPersistenceConfig",
    "DataPersistenceFeature",
    "DataPersistenceServiceImpl",
    "feature",
]
