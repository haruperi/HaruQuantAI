"""Data Manager datasets catalog and overview metrics."""

from __future__ import annotations

import json
import shutil
import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from app.core.data.contracts import DataInfo
from app.core.data.market_storage import catalog_paths, safe_component, scan_catalog
from app.core.host.persistence import HostPersistence, RecordFilter
from app.core.lib.responses import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

from ._helpers import (
    DATASETS_CATALOG_FR,
    OVERVIEW_FR,
    _chart_bounds,
    logger,
    persistence,
)
from .storage import require_data

__all__ = ["Data"]


class Data:
    """Service providing dataset catalog and overview metrics."""

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        active_providers_getter: Callable[[], int] | None = None,
    ) -> None:
        """Initialize data service with optional active providers callback."""
        self.gateway = gateway or persistence
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
        require_data(self.gateway.ensure_datasets_schema())
        rows: list[dict[str, Any]] = []
        offset: int | None = 0
        while offset is not None:
            response = self.gateway.read_records(
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
            counts = []
            for table in ("datamgr_symbols", "datamgr_sessions", "datamgr_stock_group"):
                offset, count = 0, 0
                while True:
                    response = self.gateway.read_records(
                        table, offset=offset, limit=1000
                    )
                    if (
                        not response["success"]
                        and response.get("message") == "Table does not exist"
                    ):
                        break
                    page = require_data(response)
                    count += len(page["records"])
                    offset = page["pagination"].get("next_offset")
                    if offset is None:
                        break
                counts.append(count)
            self.instruments_count, self.sessions_count, self.baskets_count = counts
            paths = {
                Path(path).resolve()
                for row in dataset_rows
                for path in catalog_paths(row)
            }
            present = [path for path in paths if path.is_file()]
            self.storage_bytes = sum(path.stat().st_size for path in present)
            self.parquet_files_count = len(present)
            self.active_providers_count = (
                self._providers_getter()
                if self._providers_getter is not None
                else len({r["source"] for r in dataset_rows if r.get("bars", 0) > 0})
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
                    "symbols_count": self.instruments_count,
                    "storage_missing_files": len(paths) - len(present),
                    "disk_free_bytes": shutil.disk_usage(Path.cwd()).free,
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

            specifications: dict[Any, str] = {}
            ids = list(
                {
                    row["symbol_definition_id"]
                    for row in rows
                    if row.get("symbol_definition_id") is not None
                }
            )
            for index in range(0, len(ids), 1000):
                records = require_data(
                    self.gateway.read_records(
                        "datamgr_symbols",
                        filters=[RecordFilter("id", "in", ids[index : index + 1000])],
                        limit=1000,
                    )
                )["records"]
                specifications.update({row["id"]: row["name"] for row in records})
            datasets: list[Any] = []
            for r in rows:
                symbol = str(r.get("symbol", ""))
                underlying = str(r.get("underlying") or r.get("symbol", ""))
                broker = str(r.get("broker", "default"))
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
                        d_from = datetime.fromisoformat(date_from)
                        d_to = datetime.fromisoformat(date_to)
                        total_days = max(0, (d_to - d_from).days)
                    except ValueError:
                        total_days = 0

                datasets.append(
                    DataInfo(
                        id=str(r.get("id", f"{source}:{symbol}")),
                        symbol=symbol,
                        instrument=specifications.get(
                            r.get("symbol_definition_id"), underlying
                        ),
                        broker=broker,
                        broker_name=broker,
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
                datasets[-1] = {
                    **asdict(datasets[-1]),
                    "symbol_definition_id": r.get("symbol_definition_id"),
                    "session_id": r.get("session_id"),
                }

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

    def edit(self, dataset_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Persist validated catalog links without relabelling stored timestamps."""
        allowed = {
            "symbol",
            "broker",
            "category",
            "symbol_definition_id",
            "session_id",
            "timezone",
        }
        values = {
            key: value
            for key, value in updates.items()
            if value is not None or key in {"symbol_definition_id", "session_id"}
        }
        if not values or values.keys() - allowed:
            raise ValueError("Supply editable dataset properties")
        require_data(self.gateway.ensure_datasets_schema())
        with self.gateway.transaction() as tx:
            rows = require_data(
                tx.read_records("datamgr_datasets", filters={"id": dataset_id}, limit=1)
            )["records"]
            if not rows:
                raise ValueError("Dataset not found")
            row = rows[0]
            if "symbol" in values:
                safe_component(values["symbol"])

            from ._helpers import resolve_dataset_links

            resolve_dataset_links(tx, values)
            values["updated_at"] = datetime.now(UTC).isoformat()
            renamed = values.get("symbol", row["symbol"]) != row["symbol"]
            if not renamed or not row["bars"]:
                if renamed:
                    from .storage import dataset_root

                    values["path"] = str(
                        dataset_root(
                            Path(row["path"]).parent.parent,
                            values["symbol"],
                            row["timeframe"],
                        )
                    )
                return cast(
                    "dict[str, Any]",
                    require_data(
                        tx.update_record(
                            "datamgr_datasets", values, filters={"id": dataset_id}
                        )
                    )["records"][0],
                )
        from .partition_files import dataset_lock
        from .review import DatasetReview
        from .storage import dataset_root, publish_frame

        root = Path(row["path"])
        destination = dataset_root(
            root.parent.parent, values["symbol"], row["timeframe"]
        )
        with dataset_lock(root), dataset_lock(destination):
            latest = DatasetReview(self.gateway, dataset_id)
            if latest.record["updated_at"] != row["updated_at"]:
                raise ValueError("Dataset changed; reload before renaming")
            conflict = require_data(
                self.gateway.read_records(
                    "datamgr_datasets",
                    filters={
                        "source": row["source"],
                        "symbol": values["symbol"],
                        "timeframe": row["timeframe"],
                    },
                    limit=1,
                )
            )["records"]
            if conflict:
                raise ValueError("Another dataset already uses this name")
            frame = latest.frame()
            publish_frame(
                self.gateway,
                root.parent.parent,
                {**latest.record, **values},
                frame,
                json.loads(row["lineage_json"])["tick_size"],
                replace_snapshot=True,
                locked=True,
                metadata_updates=values,
            )
        return cast(
            "dict[str, Any]",
            require_data(
                self.gateway.read_records(
                    "datamgr_datasets", filters={"id": dataset_id}, limit=1
                )
            )["records"][0],
        )

    def _remove_cached_files(self, row: dict[str, Any]) -> None:
        """Remove retired canonical files only when no catalog still references them."""
        from .partition_files import dataset_lock

        lineage = json.loads(row.get("lineage_json") or "{}")
        if lineage.get("storage") != "canonical-partitions-v1":
            return
        root = Path(row["path"]).resolve()
        with dataset_lock(root):
            active = require_data(self.gateway.read_records("datamgr_datasets"))[
                "records"
            ]
            referenced = {
                Path(path).resolve() for item in active for path in catalog_paths(item)
            }
            for value in lineage.get("partitions", []):
                path = Path(value).resolve()
                if (
                    path.is_relative_to(root)
                    and path != root
                    and path.suffix == ".parquet"
                    and path not in referenced
                ):
                    path.unlink(missing_ok=True)

    def clear(self, dataset_id: str) -> dict[str, Any]:
        """Clear recorded dataset observations while retaining catalog record."""
        start = time.perf_counter()
        try:
            resp = self.gateway.read_records(
                "datamgr_datasets", filters={"id": dataset_id}, limit=1
            )
            records = (resp.get("data") or {}).get("records") or []
            if not records:
                return StandardResponse.failure(
                    message=f"Dataset '{dataset_id}' not found",
                    metadata=ResponseMetadata(
                        operation="data.clear",
                        duration_ms=(time.perf_counter() - start) * 1000,
                    ),
                    error=StandardError(
                        code=ErrorCode.NOT_FOUND,
                        message="Dataset not found",
                    ),
                )
            row = records[0]
            # Commit catalog retirement before removing unreferenced canonical files.
            now_iso = datetime.now(UTC).isoformat()
            require_data(
                self.gateway.update_record(
                    "datamgr_datasets",
                    {
                        "bars": 0,
                        "lineage_json": json.dumps(
                            {
                                **json.loads(row.get("lineage_json") or "{}"),
                                "partitions": [],
                                "covered_ranges": [],
                            }
                        ),
                        "date_from": "",
                        "date_to": "",
                        "updated_at": now_iso,
                    },
                    filters={"id": dataset_id},
                )
            )
            self._remove_cached_files(row)
            return StandardResponse.success(
                message=f"Dataset '{dataset_id}' cleared successfully",
                metadata=ResponseMetadata(
                    operation="data.clear",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data={"id": dataset_id, "bars": 0},
            )
        except (RuntimeError, ValueError, OSError) as error:
            return StandardResponse.failure(
                message=str(error) or f"Failed to clear dataset {dataset_id}",
                metadata=ResponseMetadata(
                    operation="data.clear",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error),
                ),
            )

    def delete(self, dataset_id: str) -> dict[str, Any]:
        """Retire a catalog entry and remove its unreferenced canonical cache."""
        start = time.perf_counter()
        try:
            resp = self.gateway.read_records(
                "datamgr_datasets", filters={"id": dataset_id}, limit=1
            )
            records = (resp.get("data") or {}).get("records") or []
            if not records:
                return StandardResponse.failure(
                    message=f"Dataset '{dataset_id}' not found",
                    metadata=ResponseMetadata(
                        operation="data.delete",
                        duration_ms=(time.perf_counter() - start) * 1000,
                    ),
                    error=StandardError(
                        code=ErrorCode.NOT_FOUND,
                        message="Dataset not found",
                    ),
                )
            # Commit catalog retirement before removing unreferenced canonical files.
            require_data(
                self.gateway.delete_record(
                    "datamgr_datasets", filters={"id": dataset_id}
                )
            )
            self._remove_cached_files(records[0])
            return StandardResponse.success(
                message=f"Dataset '{dataset_id}' deleted successfully",
                metadata=ResponseMetadata(
                    operation="data.delete",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data={"id": dataset_id, "deleted": True},
            )
        except (RuntimeError, ValueError, OSError) as error:
            return StandardResponse.failure(
                message=str(error) or f"Failed to delete dataset {dataset_id}",
                metadata=ResponseMetadata(
                    operation="data.delete",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error),
                ),
            )

    def review_chart(
        self,
        dataset_id: str,
        limit: int = 500,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Read candlestick bars from Parquet partitions for UI chart inspection."""
        start = time.perf_counter()
        try:
            resp = self.gateway.read_records(
                "datamgr_datasets", filters={"id": dataset_id}, limit=1
            )
            records = (resp.get("data") or {}).get("records") or []
            if not records:
                return StandardResponse.failure(
                    message=f"Dataset '{dataset_id}' not found",
                    metadata=ResponseMetadata(
                        operation="data.review_chart",
                        duration_ms=(time.perf_counter() - start) * 1000,
                    ),
                    error=StandardError(
                        code=ErrorCode.NOT_FOUND,
                        message="Dataset not found",
                    ),
                )
            row = records[0]
            _chart_bounds(limit, offset)
            bars: list[dict[str, Any]] = []
            if row.get("bars"):
                frame = (
                    scan_catalog(row, decode=True)
                    .sort("DateTime")
                    .slice(offset, limit)
                    .collect()
                )
                for item in frame.iter_rows(named=True):
                    tick = row["timeframe"] == "TICK"
                    mid = (item["Bid"] + item["Ask"]) / 2 if tick else item["Close"]
                    bars.append(
                        {
                            "datetime": item["DateTime"].isoformat(),
                            "open": mid if tick else item["Open"],
                            "high": item["Ask"] if tick else item["High"],
                            "low": item["Bid"] if tick else item["Low"],
                            "close": mid,
                            "volume": 1 if tick else item["Volume"],
                        }
                    )

            return StandardResponse.success(
                message=f"Loaded {len(bars)} chart bars for {dataset_id}",
                metadata=ResponseMetadata(
                    operation="data.review_chart",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data={"bars": bars, "count": len(bars)},
            )
        except (RuntimeError, ValueError, OSError) as error:
            return StandardResponse.failure(
                message=str(error) or "Failed to load chart bars",
                metadata=ResponseMetadata(
                    operation="data.review_chart",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error),
                ),
            )
