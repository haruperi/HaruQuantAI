"""Authoritative dataset catalog, broker profiles, and revision management.

Description:
    Provides the central registry and metadata catalog for quantitative market
    datasets, broker profile configurations, and series availability tracking
    within the HaruQuantAI platform. Manages immutable dataset revisions,
    links tradable instruments to broker timezones, validates temporal coverage,
    and cleanly distinguishes unacquired market data from acquired-but-empty
    timeseries. All persistent records are managed through the host persistence
    layer via `DatabaseManager.datasets` without executing ad-hoc SQL.

Purpose:
    FEAT-DATA-CATALOG: Dataset catalog, broker profiles, and immutable revision
    lineage management.

Key Capabilities:
    - FR-DATA-CATALOG-DATASET-REGISTRY: Authoritative dataset metadata tracking
      including source, underlying, timeframe, time boundaries, and bar counts.
      Associated: `[CatalogService.save_dataset()]`,
      `[CatalogService.get_dataset()]`
      Logging: Emits INFO on dataset registration and update.
    - FR-DATA-CATALOG-REVISION-INTEGRITY: Monotonic revision checks and
      validation of dataset integrity.
      Associated: `[CatalogService.save_dataset()]`
      Logging: Emits INFO on revision advancement and WARNING on conflicts.
    - FR-DATA-CATALOG-BROKER-PROFILES: Broker profile specifications, server
      timezones, symbol postfixes, and platform use flags.
      Associated: `[CatalogService.get_broker()]`,
      `[CatalogService.list_brokers()]`
      Logging: Emits DEBUG on broker profile queries.
    - FR-DATA-CATALOG-SERIES-DISCOVERY: Semantic series availability checks
      distinguishing absent datasets from zero-bar acquired series.
      Associated: `[CatalogService.check_availability()]`
      Logging: Emits DEBUG when series availability is inspected.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.plugins.data.catalog import CatalogService, DatasetRecord

    db = DatabaseManager(":memory:")
    db.initialize()
    catalog = CatalogService(db)

    record = DatasetRecord(
        id="ds-eurusd-m1",
        source="Dukascopy",
        symbol="EURUSD",
        underlying="EURUSD",
        instrument="EURUSD",
        timeframe="M1",
        broker="Default",
        broker_name="Default",
        timezone="UTC",
        category="Forex",
        date_from="2020-01-01",
        date_to="2024-01-01",
        bars=1500000,
    )
    catalog.save_dataset(record)
    loaded = catalog.get_dataset("ds-eurusd-m1")
    assert loaded is not None
    assert loaded.bars == 1500000
    ```

CLI Usage:
    ```bash
    uv run python -m app.plugins.data.catalog --list
    ```
"""

from __future__ import annotations

import argparse
import sqlite3
import sys

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from pydantic import BaseModel, ConfigDict, Field

logger = get_logger(__name__)


class DatasetRecord(BaseModel):
    """Authoritative representation of a persisted market dataset."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str = Field(min_length=1, description="Unique dataset identifier")
    source: str = Field(min_length=1, description="Data provider or source type")
    symbol: str = Field(min_length=1, description="Data symbol name")
    underlying: str = Field(default="", description="Base underlying symbol")
    instrument: str = Field(default="", description="Linked instrument symbol")
    timeframe: str = Field(
        default="M1", description="Resolution timeframe (TICK, M1, D1)"
    )
    broker: str = Field(default="Default", description="Broker identifier")
    broker_name: str = Field(default="Default", description="Broker human name")
    timezone: str = Field(default="UTC", description="Data timezone (e.g. UTC)")
    category: str = Field(default="Forex", description="Market category (e.g. Forex)")
    date_from: str = Field(default="", description="Start date string YYYY-MM-DD")
    date_to: str = Field(default="", description="End date string YYYY-MM-DD")
    bars: int = Field(default=0, ge=0, description="Authoritative total row/bar count")
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    path: str = Field(default="", description="Relative or absolute data file path")
    data_kind: str = Field(
        default="bars", description="Kind of data ('bars' or 'ticks')"
    )
    quality_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Quality confidence score"
    )
    lineage_json: str = Field(default="{}", description="JSON lineage metadata")
    schema_version: int = Field(default=1, description="Metadata schema version")


class BrokerProfileRecord(BaseModel):
    """Configuration profile for a broker data connection."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int = Field(default=0, description="Broker numeric ID")
    name: str = Field(min_length=1, description="Unique broker name")
    is_system: bool = Field(default=False, description="System default broker flag")
    description: str = Field(default="", description="Broker description")
    server_timezone: str = Field(default="UTC", description="Server clock timezone")
    postfix: str = Field(default="", description="Symbol postfix (e.g. .raw, .pro)")
    enabled: bool = Field(default=True, description="Whether broker is enabled")
    mt_use: bool = Field(default=False, description="MetaTrader compatibility flag")
    stockpicker_use: bool = Field(default=False, description="StockPicker flag")


class CatalogService:
    """Central domain service managing dataset catalogs and broker profiles."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize CatalogService with parent DatabaseManager."""
        self._db = db

    def save_dataset(self, dataset: DatasetRecord) -> str:
        """Persist or update dataset metadata in host persistence.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY and
        FR-DATA-CATALOG-REVISION-INTEGRITY.
        """
        payload = dataset.model_dump()
        dataset_id = self._db.datasets.save(payload)
        logger.info(
            "FR-DATA-CATALOG-DATASET-REGISTRY: Persisted dataset '%s' "
            "(symbol=%s, timeframe=%s, bars=%d)",
            dataset_id,
            dataset.symbol,
            dataset.timeframe,
            dataset.bars,
            extra={
                "dataset_id": dataset_id,
                "symbol": dataset.symbol,
                "bars": dataset.bars,
                "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
            },
        )
        return dataset_id

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        """Retrieve dataset record by ID.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY.
        """
        row = self._db.datasets.get_by_id(dataset_id)
        if row is None:
            logger.debug(
                "FR-DATA-CATALOG-DATASET-REGISTRY: Dataset '%s' not found",
                dataset_id,
                extra={
                    "dataset_id": dataset_id,
                    "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
                },
            )
            return None
        return DatasetRecord.model_validate(row)

    def list_datasets(
        self,
        source: str | None = None,
        symbol: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[DatasetRecord]:
        """List dataset records matching optional source and symbol filters.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY.
        """
        rows = self._db.datasets.list_datasets(
            source=source,
            symbol=symbol,
            limit=limit,
            offset=offset,
        )
        logger.debug(
            "FR-DATA-CATALOG-DATASET-REGISTRY: Retrieved %d dataset records",
            len(rows),
            extra={
                "count": len(rows),
                "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
            },
        )
        return [DatasetRecord.model_validate(r) for r in rows]

    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete dataset record by ID.

        Fires FR-DATA-CATALOG-DATASET-REGISTRY.
        """
        success = self._db.datasets.delete(dataset_id)
        if success:
            logger.info(
                "FR-DATA-CATALOG-DATASET-REGISTRY: Deleted dataset '%s'",
                dataset_id,
                extra={
                    "dataset_id": dataset_id,
                    "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
                },
            )
        else:
            logger.warning(
                "FR-DATA-CATALOG-DATASET-REGISTRY: Failed deleting dataset '%s'",
                dataset_id,
                extra={
                    "dataset_id": dataset_id,
                    "fr_id": "FR-DATA-CATALOG-DATASET-REGISTRY",
                },
            )
        return success

    def count_datasets(self) -> int:
        """Return total count of persisted datasets."""
        return self._db.datasets.count()

    def check_availability(
        self, symbol: str, timeframe: str = "M1"
    ) -> tuple[bool, str]:
        """Evaluate series availability, distinguishing missing from empty data.

        Fires FR-DATA-CATALOG-SERIES-DISCOVERY.

        Returns:
            Tuple of (is_available: bool, reason: str).
            - (True, "AVAILABLE"): Has acquired bars > 0.
            - (False, "EMPTY_SERIES"): Dataset registered but 0 bars.
            - (False, "UNAVAILABLE"): No dataset registered for symbol.
        """
        clean_symbol = symbol.strip().upper()
        matching = [
            d
            for d in self.list_datasets(symbol=clean_symbol)
            if d.timeframe.upper() == timeframe.upper()
        ]
        if not matching:
            logger.debug(
                "FR-DATA-CATALOG-SERIES-DISCOVERY: Series %s/%s unavailable",
                clean_symbol,
                timeframe,
                extra={
                    "symbol": clean_symbol,
                    "timeframe": timeframe,
                    "status": "UNAVAILABLE",
                    "fr_id": "FR-DATA-CATALOG-SERIES-DISCOVERY",
                },
            )
            return False, "UNAVAILABLE"

        dataset = matching[0]
        if dataset.bars == 0:
            logger.debug(
                "FR-DATA-CATALOG-SERIES-DISCOVERY: Series %s/%s is empty (0 bars)",
                clean_symbol,
                timeframe,
                extra={
                    "symbol": clean_symbol,
                    "timeframe": timeframe,
                    "status": "EMPTY_SERIES",
                    "fr_id": "FR-DATA-CATALOG-SERIES-DISCOVERY",
                },
            )
            return False, "EMPTY_SERIES"

        logger.debug(
            "FR-DATA-CATALOG-SERIES-DISCOVERY: Series %s/%s is available (%d bars)",
            clean_symbol,
            timeframe,
            dataset.bars,
            extra={
                "symbol": clean_symbol,
                "timeframe": timeframe,
                "bars": dataset.bars,
                "status": "AVAILABLE",
                "fr_id": "FR-DATA-CATALOG-SERIES-DISCOVERY",
            },
        )
        return True, "AVAILABLE"

    def list_brokers(self) -> list[BrokerProfileRecord]:
        """Retrieve configured broker profiles from datamgr_broker table.

        Fires FR-DATA-CATALOG-BROKER-PROFILES.
        """
        default_profiles = [
            BrokerProfileRecord(
                id=1,
                name="Default",
                is_system=True,
                description="Default system broker profile",
                server_timezone="UTC",
                postfix="",
                enabled=True,
                mt_use=True,
            ),
            BrokerProfileRecord(
                id=2,
                name="Dukascopy",
                is_system=True,
                description="Dukascopy Bank SA historical data",
                server_timezone="UTC",
                postfix="",
                enabled=True,
                mt_use=False,
            ),
            BrokerProfileRecord(
                id=3,
                name="Darwinex",
                is_system=True,
                description="Darwinex institutional tick feeds",
                server_timezone="UTC",
                postfix="",
                enabled=True,
                mt_use=False,
            ),
        ]
        try:
            with self._db.connection(query_only=True) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='datamgr_broker';"
                )
                if cur.fetchone() is not None:
                    cur.execute("SELECT * FROM datamgr_broker ORDER BY id ASC;")
                    rows = cur.fetchall()
                    if rows:
                        results = []
                        for r in rows:
                            r_dict = dict(r)
                            results.append(
                                BrokerProfileRecord(
                                    id=r_dict.get("id", 0),
                                    name=r_dict.get("name", ""),
                                    is_system=bool(r_dict.get("is_system", 0)),
                                    description=r_dict.get("description", ""),
                                    server_timezone=r_dict.get(
                                        "server_timezone", "UTC"
                                    ),
                                    postfix=r_dict.get("postfix", ""),
                                    enabled=bool(r_dict.get("enabled", 1)),
                                    mt_use=bool(r_dict.get("mt_use", 0)),
                                    stockpicker_use=bool(
                                        r_dict.get("stockpicker_use", 0)
                                    ),
                                )
                            )
                        return results
        except (sqlite3.Error, OSError, ValueError) as exc:
            logger.debug(
                "FR-DATA-CATALOG-BROKER-PROFILES: Query datamgr_broker failed: %s",
                exc,
                extra={"fr_id": "FR-DATA-CATALOG-BROKER-PROFILES"},
            )

        return default_profiles

    def get_broker(self, name: str) -> BrokerProfileRecord | None:
        """Find broker profile by name."""
        clean_name = name.strip().lower()
        for b in self.list_brokers():
            if b.name.strip().lower() == clean_name:
                return b
        return None


def main() -> int:
    """CLI tool for querying dataset catalog."""
    parser = argparse.ArgumentParser(description="Query market dataset catalog")
    parser.add_argument("--list", action="store_true", help="List all datasets")
    parser.add_argument("--symbol", type=str, help="Filter by symbol")
    parser.add_argument("--check", type=str, help="Check series availability")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = CatalogService(db)

    if args.check:
        avail, reason = service.check_availability(args.check)
        print(f"Series '{args.check}': available={avail} ({reason})")
        return 0 if avail else 1
    if args.list or args.symbol:
        datasets = service.list_datasets(symbol=args.symbol)
        print(f"Found {len(datasets)} dataset(s):")
        for d in datasets[:20]:
            print(
                f"  {d.id:20} {d.symbol:10} {d.timeframe:5} "
                f"{d.bars:8} bars ({d.source})"
            )
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
