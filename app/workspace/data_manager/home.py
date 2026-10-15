"""Dashboard overview, storage health metrics, and documentation links.

Description:
    Provides high-level dashboard metrics for the Data Manager workspace,
    aggregating dataset counts, stored bar totals, catalog counts (instruments,
    sessions, stock groups/baskets), active provider connections, and storage
    health (Parquet footprint and file counts). Exposes curated documentation
    and quick-start workflow links matching StrategyQuant X.

Purpose:
    FEAT-DATAMGR-HOME: Data Manager dashboard overview and storage diagnostics.

Key Capabilities:
    - FR-DATAMGR-HOME-OVERVIEW: Compute aggregate counts across catalogs and storage.
      Associated: `DataManagerHomeService.get_overview()`
      Logging: Emits INFO on overview computation with summary numbers.
    - FR-DATAMGR-HOME-DOC-LINKS: Curate workflow guides and documentation links.
      Associated: `DataManagerHomeService.get_doc_links()`
      Logging: Emits DEBUG when retrieving documentation links.
    - FR-DATAMGR-HOME-STORAGE-AUDIT: Audit Parquet file storage on disk.
      Associated: `DataManagerHomeService.audit_storage()`
      Logging: Emits DEBUG on scanning storage files and calculating bytes.

Python API Usage:
    ```python
    from app.workspace.data_manager.home import DataManagerHomeService

    home_service = DataManagerHomeService()
    overview = home_service.get_overview()
    print(f"Total datasets: {overview.datasets_count}, bars: {overview.total_bars}")
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.home
    ```
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.create import create_schema
from app.host.persistence.read import count_rows, read_rows, resolve_connection

__all__ = [
    "DataManagerHomeService",
    "DocLinkItem",
    "HomeOverviewData",
]

logger = get_logger(__name__)

OVERVIEW_FR = "FR-DATAMGR-HOME-OVERVIEW"
DOC_LINKS_FR = "FR-DATAMGR-HOME-DOC-LINKS"
STORAGE_AUDIT_FR = "FR-DATAMGR-HOME-STORAGE-AUDIT"


@dataclass(frozen=True)
class HomeOverviewData:
    """Aggregated metrics across the Data Manager catalogs and storage."""

    datasets_count: int
    instruments_count: int
    sessions_count: int
    baskets_count: int
    active_providers_count: int
    total_bars: int
    storage_bytes: int = 0
    parquet_files_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary representation."""
        return {
            "datasets_count": self.datasets_count,
            "instruments_count": self.instruments_count,
            "sessions_count": self.sessions_count,
            "baskets_count": self.baskets_count,
            "active_providers_count": self.active_providers_count,
            "total_bars": self.total_bars,
            "storage_bytes": self.storage_bytes,
            "parquet_files_count": self.parquet_files_count,
        }


@dataclass(frozen=True)
class DocLinkItem:
    """Curated documentation or workflow link item."""

    id: str
    title: str
    description: str
    url: str
    category: str = "guide"

    def to_dict(self) -> dict[str, Any]:
        """Convert documentation link item to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "category": self.category,
        }


_DEFAULT_DOC_LINKS: tuple[DocLinkItem, ...] = (
    DocLinkItem(
        id="guide-importing-data",
        title="Importing Historical Data",
        description=(
            "Learn how to import CSV/text market data and configure column formats."
        ),
        url="https://strategyquant.com/doc/strategyquant/importing-data-into-strategyquant/",
        category="data",
    ),
    DocLinkItem(
        id="guide-simulation-modes",
        title="Tick vs M1 Simulation",
        description=(
            "Understanding precision, execution speed, and spread/slippage modeling."
        ),
        url="https://strategyquant.com/doc/strategyquant/tick-vs-m1-simulation/",
        category="simulation",
    ),
    DocLinkItem(
        id="guide-instruments-commissions",
        title="Instruments & Commissions",
        description=(
            "Configuring tick sizes, point values, swap rules, and margin rates."
        ),
        url="https://strategyquant.com/doc/strategyquant/custom-instrument-settings/",
        category="instruments",
    ),
    DocLinkItem(
        id="guide-trading-sessions",
        title="Trading Sessions & Holidays",
        description="Defining custom session schedules and exchange holiday calendars.",
        url="https://strategyquant.com/doc/strategyquant/trading-sessions/",
        category="sessions",
    ),
    DocLinkItem(
        id="guide-stock-groups",
        title="Survivorship-Bias-Free Stock Groups",
        description=(
            "Building dynamic multi-asset baskets with dated constituent memberships."
        ),
        url="https://strategyquant.com/doc/strategyquant/stock-groups/",
        category="baskets",
    ),
    DocLinkItem(
        id="guide-exporting-data",
        title="Exporting to MT4, MT5, and CSV",
        description="Exporting clean historical series to external trading platforms.",
        url="https://strategyquant.com/doc/strategyquant/exporting-data/",
        category="export",
    ),
)


class DataManagerHomeService:
    """Service providing high-level overview metrics and storage audits."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        data_dir: Path | str | None = None,
        active_providers_getter: Callable[[], int] | None = None,
    ) -> None:
        """Initialize home service with database and filesystem paths."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.data_dir = Path(data_dir) if data_dir is not None else Path("data")
        self._providers_getter = active_providers_getter

    def audit_storage(self) -> tuple[int, int]:
        """Audit physical Parquet files and total byte footprint."""
        logger.debug(
            "%s: Auditing historical storage at %s",
            STORAGE_AUDIT_FR,
            self.data_dir,
            extra={"fr_id": STORAGE_AUDIT_FR, "data_dir": str(self.data_dir)},
        )
        total_bytes = 0
        parquet_count = 0
        history_dir = self.data_dir / "history"
        if history_dir.is_dir():
            for p in history_dir.rglob("*.parquet"):
                if p.is_file():
                    try:
                        total_bytes += p.stat().st_size
                        parquet_count += 1
                    except OSError:
                        pass

        custom_dir = self.data_dir / "custom_data"
        if custom_dir.is_dir():
            for p in custom_dir.rglob("*.parquet"):
                if p.is_file():
                    try:
                        total_bytes += p.stat().st_size
                        parquet_count += 1
                    except OSError:
                        pass

        return total_bytes, parquet_count

    def get_overview(self) -> HomeOverviewData:
        """Compute aggregate counts across catalogs and storage."""
        with resolve_connection(self.db_path) as conn:
            datasets_count = count_rows(conn, "datamgr_datasets")
            instruments_count = count_rows(conn, "datamgr_instruments")
            sessions_count = count_rows(conn, "datamgr_sessions")
            baskets_count = count_rows(conn, "datamgr_stock_group")

            # Sum total bars across all datasets
            dataset_rows = read_rows(conn, "datamgr_datasets")
            total_bars = sum(int(r.get("bars", 0)) for r in dataset_rows)

        active_providers = (
            self._providers_getter() if self._providers_getter is not None else 0
        )
        storage_bytes, parquet_files_count = self.audit_storage()

        data = HomeOverviewData(
            datasets_count=datasets_count,
            instruments_count=instruments_count,
            sessions_count=sessions_count,
            baskets_count=baskets_count,
            active_providers_count=active_providers,
            total_bars=total_bars,
            storage_bytes=storage_bytes,
            parquet_files_count=parquet_files_count,
        )
        logger.info(
            "%s: Overview computed (datasets=%d, instruments=%d, bars=%d)",
            OVERVIEW_FR,
            data.datasets_count,
            data.instruments_count,
            data.total_bars,
            extra={
                "fr_id": OVERVIEW_FR,
                "datasets_count": data.datasets_count,
                "instruments_count": data.instruments_count,
                "total_bars": data.total_bars,
            },
        )
        return data

    def get_doc_links(self) -> list[DocLinkItem]:
        """Return curated documentation links for Data Manager."""
        logger.debug(
            "%s: Returning %d documentation links",
            DOC_LINKS_FR,
            len(_DEFAULT_DOC_LINKS),
            extra={"fr_id": DOC_LINKS_FR, "count": len(_DEFAULT_DOC_LINKS)},
        )
        return list(_DEFAULT_DOC_LINKS)


def main() -> None:
    """Execute real-usage demonstration of DataManagerHomeService."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_home.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        service = DataManagerHomeService(
            db_path=db_file,
            data_dir=temp_path / "data",
            active_providers_getter=lambda: 3,
        )
        overview = service.get_overview()
        print(f"Data Manager Overview: {overview.to_dict()}")

        links = service.get_doc_links()
        print(f"Retrieved {len(links)} doc links:")
        for link in links:
            print(f" - [{link.category}] {link.title} ({link.url})")


if __name__ == "__main__":
    main()
