"""Data Manager datasets catalog and overview metrics.

Description:
    Provides high-level dataset metrics for the Data Manager workspace,
    reading saved datasets catalog entries from the authoritative SQLite database
    (datamgr_datasets table). Exposes saved datasets catalog and summaries.
    Operates as a read-only database presentation service without physical
    storage auditing or data reconciliation.

Purpose:
    FEAT-DATAMGR-DATA: Data Manager dataset catalog presentation and overview.

Key Capabilities:
    - FR-DATAMGR-DATA-OVERVIEW: Datasets overview metrics (Data.overview -> INFO).
    - FR-DATAMGR-DATA-CATALOG: Datasets catalog (Data.list -> DEBUG).

Python API Usage:
    ```python
    from app.workspace.data_manager.data import Data

    data_service = Data()
    overview = data_service.overview()
    datasets = data_service.list()
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.data
    ```
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.include.contracts import DataInfo

__all__ = [
    "Data",
]

logger = get_logger(__name__)
persistence = HostPersistence()

OVERVIEW_FR = "FR-DATAMGR-DATA-OVERVIEW"
DATASETS_CATALOG_FR = "FR-DATAMGR-DATA-CATALOG"


class Data:
    """Service providing dataset catalog and overview metrics."""

    def __init__(
        self,
        *,
        active_providers_getter: Callable[[], int] | None = None,
    ) -> None:
        """Initialize data service with optional active providers callback."""
        self._providers_getter = active_providers_getter
        self.datasets_count: int = 0
        self.instruments_count: int = 0
        self.sessions_count: int = 0
        self.baskets_count: int = 0
        self.active_providers_count: int = 0
        self.total_bars: int = 0
        self.storage_bytes: int = 0
        self.parquet_files_count: int = 0

    def _read_datasets(self) -> list[dict[str, Any]]:
        """Read all dataset catalog items from the datamgr_datasets table."""
        rows: list[dict[str, Any]] = []
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_datasets", limit=1000, offset=offset
            )
            if not response["success"]:
                err = response.get("error") or {}
                msg = (
                    err.get("message")
                    or response.get("message")
                    or "Database read failure"
                )
                raise RuntimeError(msg)
            data = response.get("data") or {}
            rows.extend(data.get("records") or [])
            pagination = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return rows

    def overview(self) -> dict[str, Any]:
        """Compute aggregate counts for datamgr_datasets wrapped in StandardResponse."""
        start = time.perf_counter()
        try:
            dataset_rows = self._read_datasets()
            self.datasets_count = len(dataset_rows)
            self.total_bars = sum(int(r.get("bars", 0)) for r in dataset_rows)
            self.active_providers_count = (
                self._providers_getter() if self._providers_getter is not None else 0
            )

            logger.info(
                "%s: Overview computed (datasets=%d, bars=%d)",
                OVERVIEW_FR,
                self.datasets_count,
                self.total_bars,
                extra={
                    "fr_id": OVERVIEW_FR,
                    "datasets_count": self.datasets_count,
                    "instruments_count": self.instruments_count,
                    "total_bars": self.total_bars,
                },
            )
            return StandardResponse.success(
                message="Overview computed successfully",
                metadata=ResponseMetadata(
                    operation="data.overview",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data={
                    "datasets_count": self.datasets_count,
                    "instruments_count": self.instruments_count,
                    "sessions_count": self.sessions_count,
                    "baskets_count": self.baskets_count,
                    "active_providers_count": self.active_providers_count,
                    "total_bars": self.total_bars,
                    "storage_bytes": self.storage_bytes,
                    "parquet_files_count": self.parquet_files_count,
                },
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("%s: Failed to compute overview", OVERVIEW_FR)
            return StandardResponse.failure(
                message=str(error) or "Failed to compute overview",
                metadata=ResponseMetadata(
                    operation="data.overview",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error) or "Internal error computing overview",
                ),
            )

    def list(self) -> dict[str, Any]:
        """Retrieve saved dataset catalog items wrapped in StandardResponse."""
        start = time.perf_counter()
        try:
            rows = self._read_datasets()

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
                        path=str(r.get("path", "")),
                        bar_type=str(r.get("bar_type", "start")),
                    )
                )

            logger.debug(
                "%s: Retrieved %d saved dataset catalog items",
                DATASETS_CATALOG_FR,
                len(datasets),
                extra={"fr_id": DATASETS_CATALOG_FR, "count": len(datasets)},
            )
            return StandardResponse.success(
                message=f"Retrieved {len(datasets)} dataset catalog items",
                metadata=ResponseMetadata(
                    operation="data.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data=datasets,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("%s: Failed to list datasets", DATASETS_CATALOG_FR)
            return StandardResponse.failure(
                message=str(error) or "Failed to retrieve datasets",
                metadata=ResponseMetadata(
                    operation="data.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error) or "Internal error listing datasets",
                ),
            )


if __name__ == "__main__":
    from app.workspace.data_manager.cli import DataCLI

    data_svc = Data()
    overview = data_svc.overview()
    saved_datasets = data_svc.list()
    print(DataCLI.format_data_dashboard(overview, saved_datasets))
