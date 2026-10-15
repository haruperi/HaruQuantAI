"""Data Manager dashboard metrics and saved datasets catalog.

Description:
    Provides high-level dashboard metrics for the Data Manager workspace,
    aggregating dataset counts, stored bar totals, catalog counts (instruments,
    sessions, stock groups/baskets), and active provider connections from the
    authoritative database. Exposes saved datasets catalog and summaries.
    Operates as a read-only database presentation service without physical
    storage auditing or data reconciliation.

Purpose:
    FEAT-DATAMGR-HOME: Data Manager dashboard overview and catalog presentation.

Key Capabilities:
    - FR-DATAMGR-HOME-OVERVIEW: Compute aggregate counts across database catalogs.
      Associated: `DataHomeService.get_overview()`
      Logging: Emits INFO on overview computation with summary numbers.
    - FR-DATAMGR-HOME-DATASETS-CATALOG: Retrieve saved datasets catalog for display.
      Associated: `DataHomeService.get_saved_datasets()`
      Logging: Emits DEBUG when listing saved dataset catalog entries.
    - FR-DATAMGR-HOME-SUMMARY: Structured representation of home overview metrics.
      Associated: `DataHomeSummary.to_dict()`
      Logging: Emits DEBUG when converting summary metric items.
    - FR-DATAMGR-HOME-DASHBOARD: Structured representation of saved dataset items.
      Associated: `DataHomeDashboard.to_dict()`
      Logging: Emits DEBUG when converting dataset dashboard items.
    - FR-DATAMGR-HOME-CLI: Headless CLI formatting and table rendering.
      Associated: `DataHomeCLI.format_dataset_table()`,
      `DataHomeCLI.format_home_dashboard()`
      Logging: Emits DEBUG when formatting dashboard or ASCII tables.

Python API Usage:
    ```python
    from app.workspace.data_manager.home import (
        DataHomeCLI,
        DataHomeService,
    )

    home_service = DataHomeService()
    overview = home_service.get_overview()
    datasets = home_service.get_saved_datasets()
    print(DataHomeCLI.format_home_dashboard(overview, datasets))
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.home
    ```
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.read import count_rows, read_rows, resolve_connection

__all__ = [
    "DataHomeCLI",
    "DataHomeDashboard",
    "DataHomeService",
    "DataHomeSummary",
]

logger = get_logger(__name__)

OVERVIEW_FR = "FR-DATAMGR-HOME-OVERVIEW"
DATASETS_CATALOG_FR = "FR-DATAMGR-HOME-DATASETS-CATALOG"
SUMMARY_FR = "FR-DATAMGR-HOME-SUMMARY"
DASHBOARD_FR = "FR-DATAMGR-HOME-DASHBOARD"
CLI_FR = "FR-DATAMGR-HOME-CLI"


@dataclass(frozen=True)
class DataHomeSummary:
    """Aggregated metrics across the Data Manager catalogs."""

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
        logger.debug(
            "%s: Serializing home summary metrics",
            SUMMARY_FR,
            extra={"fr_id": SUMMARY_FR},
        )
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
class DataHomeDashboard:
    """Summary item for a saved dataset catalog entry."""

    symbol: str
    instrument: str
    broker: str
    underlying: str
    timeframe: str
    timezone: str
    date_from: str
    date_to: str
    total_days: int
    total_records: int
    source: str
    data_type: str

    def to_dict(self) -> dict[str, Any]:
        """Convert dataset summary item to dictionary representation."""
        logger.debug(
            "%s: Serializing dataset summary for %s",
            DASHBOARD_FR,
            self.symbol,
            extra={"fr_id": DASHBOARD_FR, "symbol": self.symbol},
        )
        return {
            "symbol": self.symbol,
            "instrument": self.instrument,
            "broker": self.broker,
            "underlying": self.underlying,
            "timeframe": self.timeframe,
            "timezone": self.timezone,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "total_days": self.total_days,
            "total_records": self.total_records,
            "source": self.source,
            "data_type": self.data_type,
        }


class DataHomeService:
    """Service providing high-level overview metrics and dataset catalog."""

    def __init__(
        self,
        *,
        active_providers_getter: Callable[[], int] | None = None,
    ) -> None:
        """Initialize home service with optional active providers callback."""
        self._providers_getter = active_providers_getter

    def get_overview(self) -> DataHomeSummary:
        """Compute aggregate counts across database catalogs."""
        with resolve_connection() as conn:
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

        data = DataHomeSummary(
            datasets_count=datasets_count,
            instruments_count=instruments_count,
            sessions_count=sessions_count,
            baskets_count=baskets_count,
            active_providers_count=active_providers,
            total_bars=total_bars,
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

    def get_saved_datasets(self) -> list[DataHomeDashboard]:
        """Retrieve saved dataset catalog items from the datamgr_datasets table."""
        with resolve_connection() as conn:
            rows = read_rows(conn, "datamgr_datasets")

        datasets: list[DataHomeDashboard] = []
        for r in rows:
            symbol = str(r.get("symbol", ""))
            instrument = str(r.get("instrument", ""))
            broker = str(r.get("broker", "default"))
            underlying = str(r.get("underlying", ""))
            timeframe = str(r.get("timeframe", ""))
            timezone = str(r.get("timezone", "Exchange"))
            date_from = str(r.get("date_from", ""))
            date_to = str(r.get("date_to", ""))
            records = int(r.get("bars", 0))
            source = str(r.get("source", ""))
            data_type = str(r.get("category", ""))

            total_days = 0
            if date_from and date_to:
                try:
                    d_from = datetime.fromisoformat(date_from.replace(".", "-"))
                    d_to = datetime.fromisoformat(date_to.replace(".", "-"))
                    total_days = max(0, (d_to - d_from).days)
                except ValueError:
                    total_days = 0

            datasets.append(
                DataHomeDashboard(
                    symbol=symbol,
                    instrument=instrument,
                    broker=broker,
                    underlying=underlying,
                    timeframe=timeframe,
                    timezone=timezone,
                    date_from=date_from,
                    date_to=date_to,
                    total_days=total_days,
                    total_records=records,
                    source=source,
                    data_type=data_type,
                )
            )

        logger.debug(
            "%s: Retrieved %d saved dataset catalog items",
            DATASETS_CATALOG_FR,
            len(datasets),
            extra={"fr_id": DATASETS_CATALOG_FR, "count": len(datasets)},
        )
        return datasets


class DataHomeCLI:
    """Headless CLI formatter and table presentation for Data Manager home."""

    MAX_UNDERLYING_DISPLAY_LEN: int = 32
    TRUNCATE_LEN: int = 30

    @classmethod
    def format_dataset_table(
        cls,
        saved_datasets: Sequence[DataHomeDashboard],
    ) -> str:
        """Format ASCII table of saved dataset catalog entries."""
        logger.debug(
            "%s: formatting %d saved datasets as ASCII table",
            CLI_FR,
            len(saved_datasets),
            extra={"fr_id": CLI_FR, "count": len(saved_datasets)},
        )
        count = len(saved_datasets)
        lines: list[str] = [f"=== Saved Datasets Catalog ({count} items) ==="]
        header_fmt = (
            "| {sym:<14} | {inst:<15} | {brk:<12} | {und:<32} | {tf:<4} "
            "| {tz:<8} | {d_from:<10} | {d_to:<10} | {days:>6} | {recs:>10} "
            "| {src:<16} | {cat:<8} |"
        )
        divider = (
            "|-"
            + "-|-".join(
                [
                    "-" * 14,
                    "-" * 15,
                    "-" * 12,
                    "-" * 32,
                    "-" * 4,
                    "-" * 8,
                    "-" * 10,
                    "-" * 10,
                    "-" * 6,
                    "-" * 10,
                    "-" * 16,
                    "-" * 8,
                ]
            )
            + "-|"
        )
        lines.append(
            header_fmt.format(
                sym="Symbol Name",
                inst="Instrument",
                brk="Broker profile",
                und="Underlying Symbol",
                tf="TF",
                tz="Timezone",
                d_from="Date from",
                d_to="Date to",
                days="Days",
                recs="Records",
                src="Source",
                cat="Data type",
            )
        )
        lines.append(divider)
        for ds in saved_datasets:
            if len(ds.underlying) > cls.MAX_UNDERLYING_DISPLAY_LEN:
                und_preview = ds.underlying[: cls.TRUNCATE_LEN] + ".."
            else:
                und_preview = ds.underlying
            lines.append(
                header_fmt.format(
                    sym=ds.symbol,
                    inst=ds.instrument,
                    brk=ds.broker,
                    und=und_preview,
                    tf=ds.timeframe,
                    tz=ds.timezone,
                    d_from=ds.date_from or "-",
                    d_to=ds.date_to or "-",
                    days=ds.total_days,
                    recs=f"{ds.total_records:,}",
                    src=ds.source,
                    cat=ds.data_type,
                )
            )
        return "\n".join(lines)

    @classmethod
    def format_home_dashboard(
        cls,
        overview: DataHomeSummary,
        saved_datasets: Sequence[DataHomeDashboard],
    ) -> str:
        """Format complete human-readable dashboard output."""
        logger.debug(
            "%s: formatting home overview and dataset table",
            CLI_FR,
            extra={"fr_id": CLI_FR},
        )
        lines = [
            "=== Data Manager Home: Live Database Overview ===",
            f"Total Datasets:       {overview.datasets_count}",
            f"Historical Bars:      {overview.total_bars:,}",
            f"Instruments Catalog:  {overview.instruments_count}",
            f"Trading Sessions:     {overview.sessions_count}",
            f"Custom Baskets:       {overview.baskets_count}",
            f"Active Providers:     {overview.active_providers_count}",
            "",
            cls.format_dataset_table(saved_datasets),
        ]
        return "\n".join(lines)


def main() -> None:
    """Execute live database read-only demonstration of DataHomeService."""
    service = DataHomeService()
    overview = service.get_overview()
    saved_datasets = service.get_saved_datasets()
    print(DataHomeCLI.format_home_dashboard(overview, saved_datasets))


if __name__ == "__main__":
    main()
