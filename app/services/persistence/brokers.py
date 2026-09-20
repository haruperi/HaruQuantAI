"""Transactional SQLite persistence feature for the Brokers domain.

Feature:
    FEAT-PERSISTENCE-BROKERS

Purpose:
    Provides durable storage, parameterized SQL execution, and transactional
    invariants for broker catalog profiles, symbol postfix mappings, server
    timezones, and connection configurations under namespace `brokers.v1`.
    Pre-seeds the 11 StrategyQuant X system broker definitions.

Invariants:
    * System broker profiles cannot be deleted.
    * Connection configurations reference secret keys, never plaintext passwords.
    * Database interactions are fully parameterized and transaction-safe.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, override

from app.contracts.brokers import (
    BROKER_PERSISTENCE,
    BrokerConnectionConfig,
    BrokerError,
    BrokerProfile,
)
from app.contracts.brokers import (
    BrokerPersistenceService as IBrokerPersistenceService,
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
# Pre-seeded StrategyQuant X System Brokers
# ---------------------------------------------------------------------------

PRESEEDED_BROKERS: tuple[dict[str, Any], ...] = (
    {
        "id": 1,
        "name": "XTB",
        "is_system": 1,
        "description": "XTB broker",
        "stockpicker_use": 1,
        "mt_use": 0,
        "server_timezone": "UTC",
        "postfix": "",
    },
    {
        "id": 2,
        "name": "RoboForex",
        "is_system": 1,
        "description": "RoboForex",
        "stockpicker_use": 0,
        "mt_use": 1,
        "server_timezone": "EET",
        "postfix": "_roboforex",
    },
    {
        "id": 3,
        "name": "Dukascopy",
        "is_system": 1,
        "description": "Dukascopy",
        "stockpicker_use": 0,
        "mt_use": 1,
        "server_timezone": "EETUS",
        "postfix": "_dukascopy",
    },
    {
        "id": 4,
        "name": "Darwinex",
        "is_system": 1,
        "description": "Darwinex CFDs",
        "stockpicker_use": 0,
        "mt_use": 1,
        "server_timezone": "EETUS",
        "postfix": "_darwinex",
    },
    {
        "id": 5,
        "name": "ICMarkets",
        "is_system": 1,
        "description": "ICMarkets",
        "stockpicker_use": 0,
        "mt_use": 1,
        "server_timezone": "EETUS",
        "postfix": "_icmarkets",
    },
    {
        "id": 6,
        "name": "Pepperstone",
        "is_system": 1,
        "description": "Pepperstone",
        "stockpicker_use": 0,
        "mt_use": 1,
        "server_timezone": "EETUS",
        "postfix": "_pepperstone",
    },
    {
        "id": 7,
        "name": "OANDA",
        "is_system": 1,
        "description": "OANDA",
        "stockpicker_use": 0,
        "mt_use": 1,
        "server_timezone": "EETUS",
        "postfix": "_oanda",
    },
    {
        "id": 8,
        "name": "FTMO",
        "is_system": 1,
        "description": "FTMO",
        "stockpicker_use": 0,
        "mt_use": 1,
        "server_timezone": "EETUS",
        "postfix": "_ftmo",
    },
    {
        "id": 9,
        "name": "The5ers",
        "is_system": 1,
        "description": "The5ers",
        "stockpicker_use": 0,
        "mt_use": 1,
        "server_timezone": "Asia/Jerusalem",
        "postfix": "_the5ers",
    },
    {
        "id": 10,
        "name": "Monevis",
        "is_system": 1,
        "description": "Monevis",
        "stockpicker_use": 0,
        "mt_use": 1,
        "server_timezone": "EETUS",
        "postfix": "_monevis",
    },
    {
        "id": 11,
        "name": "Darwinex Zero",
        "is_system": 1,
        "description": "Darwinex Zero",
        "stockpicker_use": 1,
        "mt_use": 0,
        "server_timezone": "UTC",
        "postfix": "",
    },
)

# ---------------------------------------------------------------------------
# SQLite Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL: str = """
CREATE TABLE IF NOT EXISTS broker_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_system INTEGER NOT NULL DEFAULT 0,
    description TEXT DEFAULT '',
    stockpicker_use INTEGER DEFAULT 0,
    mt_use INTEGER DEFAULT 0,
    server_timezone TEXT DEFAULT 'UTC',
    postfix TEXT DEFAULT '',
    enabled INTEGER DEFAULT 1,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS broker_connections (
    connection_id TEXT PRIMARY KEY,
    broker_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    environment TEXT NOT NULL DEFAULT 'demo',
    endpoint TEXT NOT NULL DEFAULT '',
    secret_key_ref TEXT NOT NULL DEFAULT '',
    timeout_s REAL NOT NULL DEFAULT 30.0,
    rate_limit_rps REAL NOT NULL DEFAULT 10.0,
    settings_json TEXT NOT NULL DEFAULT '{}',
    created_at_utc TEXT NOT NULL
);
"""


@dataclass(slots=True)
class BrokersPersistenceConfig:
    """Slotted immutable configuration for broker persistence."""

    schema_version: int = 1
    preseed_system_brokers: bool = True


class BrokersPersistenceService(IBrokerPersistenceService):
    """SQLite implementation of broker metadata persistence."""

    def __init__(
        self,
        db: DatabaseService,
        config: BrokersPersistenceConfig | None = None,
    ) -> None:
        self._db = db
        self._config = config or BrokersPersistenceConfig()
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Initialize tables and seed system profiles if missing."""
        self._db.execute_script(_SCHEMA_SQL)

        if self._config.preseed_system_brokers:
            now_iso = datetime.now(UTC).isoformat()
            for b in PRESEEDED_BROKERS:
                self._db.execute_mutation(
                    """
                    INSERT OR IGNORE INTO broker_profiles (
                        id, name, is_system, description, stockpicker_use,
                        mt_use, server_timezone, postfix, enabled,
                        created_at_utc, updated_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        b["id"],
                        b["name"],
                        b["is_system"],
                        b["description"],
                        b["stockpicker_use"],
                        b["mt_use"],
                        b["server_timezone"],
                        b["postfix"],
                        now_iso,
                        now_iso,
                    ),
                )

    def _row_to_profile(self, row: dict[str, Any]) -> BrokerProfile:
        return BrokerProfile(
            id=int(row["id"]),
            name=str(row["name"]),
            is_system=bool(row["is_system"]),
            description=str(row["description"] or ""),
            stockpicker_use=bool(row["stockpicker_use"]),
            mt_use=bool(row["mt_use"]),
            server_timezone=str(row["server_timezone"] or "UTC"),
            postfix=str(row["postfix"] or ""),
            enabled=bool(row["enabled"]),
        )

    @override
    async def list_profiles(self) -> list[BrokerProfile]:
        rows = self._db.execute_query("SELECT * FROM broker_profiles ORDER BY id ASC")
        return [self._row_to_profile(r) for r in rows]

    @override
    async def get_profile(self, broker_id: int) -> BrokerProfile | None:
        rows = self._db.execute_query(
            "SELECT * FROM broker_profiles WHERE id = ?", (broker_id,)
        )
        if not rows:
            return None
        return self._row_to_profile(rows[0])

    @override
    async def get_profile_by_name(self, name: str) -> BrokerProfile | None:
        rows = self._db.execute_query(
            "SELECT * FROM broker_profiles WHERE name = ?", (name,)
        )
        if not rows:
            return None
        return self._row_to_profile(rows[0])

    @override
    async def save_profile(self, profile: BrokerProfile) -> BrokerProfile:
        now_iso = datetime.now(UTC).isoformat()
        if profile.id > 0:
            existing = await self.get_profile(profile.id)
            if existing and existing.is_system and not profile.is_system:
                raise BrokerError("Cannot downgrade system broker profile.")

            self._db.execute_mutation(
                """
                INSERT INTO broker_profiles (
                    id, name, is_system, description, stockpicker_use,
                    mt_use, server_timezone, postfix, enabled,
                    created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    stockpicker_use=excluded.stockpicker_use,
                    mt_use=excluded.mt_use,
                    server_timezone=excluded.server_timezone,
                    postfix=excluded.postfix,
                    enabled=excluded.enabled,
                    updated_at_utc=excluded.updated_at_utc
                """,
                (
                    profile.id,
                    profile.name,
                    1 if profile.is_system else 0,
                    profile.description,
                    1 if profile.stockpicker_use else 0,
                    1 if profile.mt_use else 0,
                    profile.server_timezone,
                    profile.postfix,
                    1 if profile.enabled else 0,
                    now_iso,
                    now_iso,
                ),
            )
            saved = await self.get_profile(profile.id)
            if saved is None:
                raise BrokerError(f"Failed to retrieve saved profile {profile.id}")
            return saved

        # Auto-increment insertion
        self._db.execute_mutation(
            """
            INSERT INTO broker_profiles (
                name, is_system, description, stockpicker_use,
                mt_use, server_timezone, postfix, enabled,
                created_at_utc, updated_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile.name,
                1 if profile.is_system else 0,
                profile.description,
                1 if profile.stockpicker_use else 0,
                1 if profile.mt_use else 0,
                profile.server_timezone,
                profile.postfix,
                1 if profile.enabled else 0,
                now_iso,
                now_iso,
            ),
        )
        saved = await self.get_profile_by_name(profile.name)
        if saved is None:
            raise BrokerError(f"Failed to retrieve created profile {profile.name}")
        return saved

    @override
    async def delete_profile(self, broker_id: int) -> bool:
        profile = await self.get_profile(broker_id)
        if profile is None:
            return False
        if profile.is_system:
            logger.warning(
                "Attempted to delete system broker profile rejected",
                broker_id=broker_id,
                name=profile.name,
            )
            return False

        rows = self._db.execute_mutation(
            "DELETE FROM broker_profiles WHERE id = ?", (broker_id,)
        )
        return rows > 0

    @override
    async def save_connection_config(self, config: BrokerConnectionConfig) -> None:
        now_iso = datetime.now(UTC).isoformat()
        settings_str = json.dumps(dict(config.settings))
        self._db.execute_mutation(
            """
            INSERT INTO broker_connections (
                connection_id, broker_id, provider_name, environment,
                endpoint, secret_key_ref, timeout_s, rate_limit_rps,
                settings_json, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(connection_id) DO UPDATE SET
                broker_id=excluded.broker_id,
                provider_name=excluded.provider_name,
                environment=excluded.environment,
                endpoint=excluded.endpoint,
                secret_key_ref=excluded.secret_key_ref,
                timeout_s=excluded.timeout_s,
                rate_limit_rps=excluded.rate_limit_rps,
                settings_json=excluded.settings_json
            """,
            (
                config.connection_id,
                config.broker_id,
                config.provider_name,
                config.environment,
                config.endpoint,
                config.secret_key_ref,
                config.timeout_s,
                config.rate_limit_rps,
                settings_str,
                now_iso,
            ),
        )

    @override
    async def get_connection_config(
        self,
        connection_id: str,
    ) -> BrokerConnectionConfig | None:
        rows = self._db.execute_query(
            "SELECT * FROM broker_connections WHERE connection_id = ?",
            (connection_id,),
        )
        if not rows:
            return None
        r = rows[0]
        settings = json.loads(r["settings_json"]) if r["settings_json"] else {}
        return BrokerConnectionConfig(
            connection_id=str(r["connection_id"]),
            broker_id=int(r["broker_id"]),
            provider_name=str(r["provider_name"]),
            environment=str(r["environment"]),
            endpoint=str(r["endpoint"]),
            secret_key_ref=str(r["secret_key_ref"]),
            timeout_s=float(r["timeout_s"]),
            rate_limit_rps=float(r["rate_limit_rps"]),
            settings=settings,
        )


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.brokers",
    provides=frozenset({BROKER_PERSISTENCE}),
    requires=frozenset({DATABASE_SERVICE}),
    optional=frozenset(),
    description="Transactional SQLite persistence for namespace brokers.v1",
)


class BrokersPersistenceFeature:
    """Feature lifecycle wrapper for broker persistence."""

    def __init__(self, config: BrokersPersistenceConfig | None = None) -> None:
        self._config = config or BrokersPersistenceConfig()
        self._service: BrokersPersistenceService | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature specification."""
        return SPEC

    async def start(self, ctx: FeatureContext) -> None:
        """Start the feature and provide BrokersPersistenceService capability."""
        db = ctx.require(DATABASE_SERVICE)
        self._service = BrokersPersistenceService(db, self._config)
        ctx.provide(BROKER_PERSISTENCE, self._service)
        logger.info("brokers_persistence_started")

    async def stop(self, _ctx: FeatureContext) -> None:
        """Stop the feature and release resources."""
        self._service = None
        logger.info("brokers_persistence_stopped")


def feature(
    config: BrokersPersistenceConfig | None = None,
) -> BrokersPersistenceFeature:
    """Factory function creating the brokers persistence feature."""
    return BrokersPersistenceFeature(config)
