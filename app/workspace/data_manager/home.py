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
      Associated: `Home.get_overview()`
      Logging: Emits INFO on overview computation with summary numbers.
    - FR-DATAMGR-HOME-DATASETS-CATALOG: Retrieve saved datasets catalog for display.
      Associated: `Home.get_saved_datasets()`
      Logging: Emits DEBUG when listing saved dataset catalog entries.

Python API Usage:
    ```python
    from app.workspace.data_manager.home import (
        Home,
        HomeCLI,
    )

    home_service = Home()
    overview = home_service.get_overview()
    datasets = home_service.get_saved_datasets()
    print(HomeCLI.format_home_dashboard(overview, datasets))
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.home
    ```
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.read import count_rows, read_rows, resolve_connection
from app.services.include.contracts import DataInfo

__all__ = [
    "Home",
    "HomeCLI",
]

logger = get_logger(__name__)

OVERVIEW_FR = "FR-DATAMGR-HOME-OVERVIEW"
DATASETS_CATALOG_FR = "FR-DATAMGR-HOME-DATASETS-CATALOG"


@dataclass(frozen=True)
class _Config:
    """Internal aggregated metrics and configuration for Data Manager home."""

    datasets_count: int = 0
    instruments_count: int = 0
    sessions_count: int = 0
    baskets_count: int = 0
    active_providers_count: int = 0
    total_bars: int = 0
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


class Home:
    """Service providing high-level overview metrics and dataset catalog."""

    def __init__(
        self,
        *,
        active_providers_getter: Callable[[], int] | None = None,
    ) -> None:
        """Initialize home service with optional active providers callback."""
        self._providers_getter = active_providers_getter

    def get_overview(self) -> dict[str, Any]:
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

        config = _Config(
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
            config.datasets_count,
            config.instruments_count,
            config.total_bars,
            extra={
                "fr_id": OVERVIEW_FR,
                "datasets_count": config.datasets_count,
                "instruments_count": config.instruments_count,
                "total_bars": config.total_bars,
            },
        )
        return config.to_dict()

    def get_saved_datasets(self) -> list[DataInfo]:
        """Retrieve saved dataset catalog items from the datamgr_datasets table."""
        with resolve_connection() as conn:
            rows = read_rows(conn, "datamgr_datasets")

        datasets: list[DataInfo] = []
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
                DataInfo(
                    id=str(r.get("id", f"{source}:{symbol}")),
                    symbol=symbol,
                    instrument=instrument,
                    broker=broker,
                    broker_name=str(r.get("broker_name", broker)),
                    underlying=underlying,
                    timeframe=timeframe,
                    timezone=timezone,
                    date_from=date_from,
                    date_to=date_to,
                    total_days=total_days,
                    total_records=records,
                    bars=records,
                    rows=records,
                    source=source,
                    connection=source,
                    data_type=data_type,
                    category=data_type,
                )
            )

        logger.debug(
            "%s: Retrieved %d saved dataset catalog items",
            DATASETS_CATALOG_FR,
            len(datasets),
            extra={"fr_id": DATASETS_CATALOG_FR, "count": len(datasets)},
        )
        return datasets


MAX_UNDERLYING_DISPLAY_LEN: int = 32
TRUNCATE_LEN: int = 30


def format_dataset_table(saved_datasets: Sequence[DataInfo]) -> str:
    """Format ASCII table of saved dataset catalog entries."""
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
        if len(ds.underlying) > MAX_UNDERLYING_DISPLAY_LEN:
            und_preview = ds.underlying[:TRUNCATE_LEN] + ".."
        else:
            und_preview = ds.underlying
        lines.append(
            header_fmt.format(
                sym=ds.symbol,
                inst=ds.instrument,
                brk=ds.broker,
                und=und_preview,
                tf=str(ds.timeframe),
                tz=ds.timezone,
                d_from=str(ds.date_from) or "-",
                d_to=str(ds.date_to) or "-",
                days=ds.total_days,
                recs=f"{ds.total_records:,}",
                src=str(ds.source),
                cat=ds.data_type,
            )
        )
    return "\n".join(lines)


def format_home_dashboard(
    overview: Mapping[str, Any] | Any,
    saved_datasets: Sequence[DataInfo],
) -> str:
    """Format complete human-readable dashboard output."""
    if isinstance(overview, Mapping):
        ds_count = overview.get("datasets_count", 0)
        total_bars = int(overview.get("total_bars", 0))
        inst_count = overview.get("instruments_count", 0)
        sess_count = overview.get("sessions_count", 0)
        bask_count = overview.get("baskets_count", 0)
        act_prov = overview.get("active_providers_count", 0)
    else:
        ds_count = getattr(overview, "datasets_count", 0)
        total_bars = int(getattr(overview, "total_bars", 0))
        inst_count = getattr(overview, "instruments_count", 0)
        sess_count = getattr(overview, "sessions_count", 0)
        bask_count = getattr(overview, "baskets_count", 0)
        act_prov = getattr(overview, "active_providers_count", 0)

    lines = [
        "=== Data Manager Home: Live Database Overview ===",
        f"Total Datasets:       {ds_count}",
        f"Historical Bars:      {total_bars:,}",
        f"Instruments Catalog:  {inst_count}",
        f"Trading Sessions:     {sess_count}",
        f"Custom Baskets:       {bask_count}",
        f"Active Providers:     {act_prov}",
        "",
        format_dataset_table(saved_datasets),
    ]
    return "\n".join(lines)


class HomeCLI:
    """Headless CLI formatter and table presentation for Data Manager home."""

    MAX_UNDERLYING_DISPLAY_LEN: int = MAX_UNDERLYING_DISPLAY_LEN
    TRUNCATE_LEN: int = TRUNCATE_LEN

    @classmethod
    def format_dataset_table(
        cls,
        saved_datasets: Sequence[DataInfo],
    ) -> str:
        """Format ASCII table of saved dataset catalog entries."""
        logger.debug(
            "Formatting %d saved datasets as ASCII table",
            len(saved_datasets),
        )
        return format_dataset_table(saved_datasets)

    @classmethod
    def format_home_dashboard(
        cls,
        overview: Mapping[str, Any] | _Config,
        saved_datasets: Sequence[DataInfo],
    ) -> str:
        """Format complete human-readable dashboard output."""
        logger.debug("Formatting home overview and dataset table")
        return format_home_dashboard(overview, saved_datasets)


if __name__ == "__main__":
    home = Home()
    overview = home.get_overview()
    saved_datasets = home.get_saved_datasets()
    print(HomeCLI.format_home_dashboard(overview, saved_datasets))
