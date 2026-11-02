"""Dukascopy market data ingestion, partitioning, and catalog service.

Description:
    Register symbols and publish bounded market history using host-owned storage.
    Adopted datasets retain validated native decimal precision on subsequent updates.
Purpose:
    FEAT-DUKASCOPY-INGESTION: reusable canonical Dukascopy historical datasets.
Key Capabilities:
    - FR-DUKASCOPY-adopted-storage-unit: preserve verified legacy storage precision.
      Logging: INFO records adopted units; tests verify emitted logs and exact prices.
Python API Usage:
    Dukascopy(gateway).download("EURUSD", timeframe="M1", date_from=start, date_to=end)
CLI Usage:
    uv run pytest tests/workspace/data_manager/test_dukascopy.py --no-cov
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import duckdb
import pandas as pd  # type: ignore[import-untyped]
import polars as pl

from app.core.data.market_storage import (
    catalog_paths,
    safe_component,
    scan_catalog,
)
from app.core.enums import Timeframe
from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from app.core.lib.responses import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.workspace.brokers.base import BridgeError
from app.workspace.brokers.dukascopy import DukascopyClient
from app.workspace.data_manager.data.coverage import (
    RangeProgress,
    missing_ranges,
    record_checked_ranges,
)
from app.workspace.data_manager.data.storage import (
    dataset_root,
    publish_frame,
    require_data,
)
from app.workspace.data_manager.logs import Logs

from ._helpers import (
    DEFAULT_CATALOG_PATH,
    DEFAULT_STORAGE_ROOT,
    DISCLAIMER_PARAGRAPHS,
    MIN_CATALOG_PARTS,
    _valid_add_inputs,
)

logger = get_logger(__name__)

__all__ = ["Dukascopy"]


def _get_dukascopy_client() -> Any:
    mod = sys.modules.get("app.workspace.data_manager.sources")
    if mod and hasattr(mod, "DukascopyClient"):
        return mod.DukascopyClient
    return DukascopyClient


class Dukascopy:
    """Service managing Dukascopy dataset catalog and historical Parquet ingestion."""

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        storage_root: str | Path | None = None,
        catalog_path: str | Path | None = None,
        logs: Logs | None = None,
    ) -> None:
        """Initialize Dukascopy service with gateway and storage paths."""
        self.gateway = gateway or HostPersistence()
        self.storage_root = Path(storage_root) if storage_root else DEFAULT_STORAGE_ROOT
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self.logs = logs
        self._catalog_cache: dict[str, dict[str, Any]] | None = None

    def _ensure_catalog(self) -> dict[str, dict[str, Any]]:
        """Parse and cache symbol definitions from dukascopy.csv."""
        if self._catalog_cache is not None:
            return self._catalog_cache

        catalog: dict[str, dict[str, Any]] = {}
        if not self.catalog_path.exists():
            self._catalog_cache = catalog
            return catalog

        with self.catalog_path.open(encoding="latin1") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                parts = line_str.split(";")
                if len(parts) < MIN_CATALOG_PARTS:
                    continue
                sym = parts[0].strip().upper()
                name = parts[1].strip()
                category = parts[2].strip()
                subcategory = parts[3].strip()
                date_from_m1 = parts[4].strip()
                date_from_tick = parts[5].strip()
                decimals = int(parts[6].strip())
                contract_sz = float(parts[7].strip())
                spread = float(parts[8].strip())
                pip_sz = float(parts[9].strip())
                tick_sz = float(parts[10].strip())
                sym_type = (
                    int(parts[11].strip()) if len(parts) > MIN_CATALOG_PARTS else 0
                )

                catalog[sym] = {
                    "symbol": sym,
                    "name": name,
                    "category": category,
                    "subcategory": subcategory,
                    "full_category": f"{category} - {subcategory}",
                    "date_from_m1": date_from_m1,
                    "date_from_tick": date_from_tick,
                    "decimals": decimals,
                    "contract_size": contract_sz,
                    "spread": spread,
                    "pip_size": pip_sz,
                    "tick_size": tick_sz,
                    "symbol_type": sym_type,
                }
        self._catalog_cache = catalog
        return catalog

    def get_catalog(
        self,
        category: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """Return available Dukascopy symbols and categories from catalog."""
        start = time.perf_counter()
        catalog = self._ensure_catalog()
        items = list(catalog.values())

        if category:
            cat_norm = category.strip().lower()
            items = [
                it
                for it in items
                if cat_norm in it["full_category"].lower()
                or cat_norm == it["category"].lower()
            ]

        if search:
            query = search.strip().lower()
            items = [
                it
                for it in items
                if query in it["symbol"].lower() or query in it["name"].lower()
            ]

        categories: list[dict[str, str]] = [{"value": "", "name": "All"}]
        seen_cats = set()
        for it in catalog.values():
            if it["category"] not in seen_cats:
                seen_cats.add(it["category"])
                categories.append(
                    {"value": it["category"], "name": f"{it['category']} - All"}
                )
            if it["full_category"] not in seen_cats:
                seen_cats.add(it["full_category"])
                categories.append(
                    {"value": it["full_category"], "name": it["full_category"]}
                )

        return StandardResponse.success(
            message=f"Retrieved {len(items)} Dukascopy symbols",
            metadata=ResponseMetadata(
                operation="dukascopy.catalog",
                duration_ms=(time.perf_counter() - start) * 1000,
            ),
            data={"symbols": items, "categories": categories, "count": len(items)},
        )

    def disclaimer(self) -> dict[str, Any]:
        """Retrieve Dukascopy data disclaimer, terms, and CDN notices."""
        start = time.perf_counter()
        return StandardResponse.success(
            message="Dukascopy data disclaimer retrieved",
            metadata=ResponseMetadata(
                operation="dukascopy.disclaimer",
                duration_ms=(time.perf_counter() - start) * 1000,
            ),
            data={
                "title": "Dukascopy data disclaimer",
                "paragraphs": DISCLAIMER_PARAGRAPHS,
                "requires_confirmation": True,
                "cdn_disclaimer": (
                    "Historical market data is retrieved and cached using "
                    "StrategyQuant CDN for high availability and throughput."
                ),
            },
        )

    def resolve_broker_name(self, broker_val: Any) -> str:
        """Resolve a broker identifier, alias, or profile name to real text name."""
        if broker_val is None:
            return "SQ default"
        raw = str(broker_val).strip()
        if not raw or raw in ("-1", "default", "SQ default", "Default"):
            return "SQ default"
        if raw.startswith("[[") and raw.endswith("]]"):
            return raw[2:-2].strip()
        return self._lookup_broker_name(raw)

    def _lookup_broker_name(self, raw: str) -> str:
        """Look up raw identifier or bracketed name from datamgr_broker table."""
        filters = {"id": int(raw)} if raw.isdigit() else {"name": f"[[{raw}]]"}
        try:
            res = self.gateway.read_records("datamgr_broker", filters=filters, limit=1)
            records = (res.get("data") or {}).get("records") or []
            if records:
                name = str(records[0].get("name", "")).strip()
                if name.startswith("[[") and name.endswith("]]"):
                    return name[2:-2].strip()
                return name
        except KeyError, ValueError, RuntimeError:
            pass
        return raw

    @staticmethod
    def parse_date_bound(
        val: str | datetime | None, is_end: bool = False
    ) -> datetime | None:
        """Parse string or datetime boundary into UTC datetime."""
        if val is None:
            return None
        if isinstance(val, datetime):
            res = val if val.tzinfo is not None else val.replace(tzinfo=UTC)
            if is_end and res.hour == 0 and res.minute == 0 and res.second == 0:
                res = res.replace(hour=23, minute=59, second=59, microsecond=999999)
            return res.astimezone(UTC)
        if isinstance(val, str) and val.strip():
            try:
                dt = datetime.fromisoformat(val.strip())
                res = dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
                if is_end and "T" not in val and " " not in val:
                    res = res.replace(hour=23, minute=59, second=59, microsecond=999999)
                return res.astimezone(UTC)
            except ValueError:
                return None
        return None

    def _validate_add_parameters(
        self,
        symbols: str | list[str],
        data_type: str,
        postfix: str,
        disclaimer_confirmed: bool,
    ) -> tuple[list[str], str, str] | dict[str, Any]:
        """Validate input parameters before creating dataset records."""
        if not disclaimer_confirmed:
            return StandardResponse.failure(
                message=(
                    "Dukascopy data disclaimer must be confirmed before adding symbols"
                ),
                metadata=ResponseMetadata(operation="dukascopy.add", duration_ms=0.0),
                error=StandardError(
                    code=ErrorCode.VALIDATION,
                    message="Disclaimer confirmation required",
                ),
            )

        norm_type = data_type.strip().upper()
        if norm_type not in ("M1", "TICK"):
            return StandardResponse.failure(
                message=f"Invalid data type '{data_type}'. Must be 'M1' or 'TICK'",
                metadata=ResponseMetadata(operation="dukascopy.add", duration_ms=0.0),
                error=StandardError(
                    code=ErrorCode.VALIDATION,
                    message="Invalid data type",
                ),
            )

        norm_postfix = postfix.strip().upper()
        if norm_postfix and not re.match(r"^[A-Z0-9_.-]*$", norm_postfix):
            return StandardResponse.failure(
                message="Use a safe alphanumeric postfix",
                metadata=ResponseMetadata(operation="dukascopy.add", duration_ms=0.0),
                error=StandardError(
                    code=ErrorCode.VALIDATION,
                    message="Invalid postfix",
                ),
            )

        symbol_list = (
            [s.strip().upper() for s in symbols.split(",") if s.strip()]
            if isinstance(symbols, str)
            else [s.strip().upper() for s in symbols if s.strip()]
        )
        if not symbol_list:
            return StandardResponse.failure(
                message="No symbols selected",
                metadata=ResponseMetadata(operation="dukascopy.add", duration_ms=0.0),
                error=StandardError(
                    code=ErrorCode.VALIDATION,
                    message="Empty symbols list",
                ),
            )

        return symbol_list, norm_type, norm_postfix

    def add(
        self,
        symbols: str | list[str],
        *,
        data_type: str = "M1",
        broker: str = "default",
        postfix: str = "",
        symbol_definitions: list[str] | None = None,
        disclaimer_confirmed: bool = True,
    ) -> dict[str, Any]:
        """Add Dukascopy symbols to datamgr_datasets catalog."""
        start = time.perf_counter()
        if not _valid_add_inputs(symbols, data_type, postfix, disclaimer_confirmed):
            return self._failure("add", ValueError("Invalid add parameters"), start)
        validation = self._validate_add_parameters(
            symbols, data_type, postfix, disclaimer_confirmed
        )
        if isinstance(validation, dict) or not isinstance(validation, tuple):
            return validation

        symbol_list, norm_type, norm_postfix = validation
        catalog = self._ensure_catalog()
        for sym in symbol_list:
            if sym not in catalog:
                return StandardResponse.failure(
                    message=f"Unknown catalogue symbol '{sym}'",
                    metadata=ResponseMetadata(
                        operation="dukascopy.add",
                        duration_ms=(time.perf_counter() - start) * 1000,
                    ),
                    error=StandardError(
                        code=ErrorCode.NOT_FOUND,
                        message=f"Symbol '{sym}' not found in Dukascopy catalog",
                    ),
                )

        try:
            require_data(self.gateway.ensure_datasets_schema())
            with self.gateway.transaction() as tx:
                # Check for existing datasets to prevent duplicate collision
                for sym in symbol_list:
                    target_symbol = safe_component(f"{sym}{norm_postfix}")
                    dataset_id = f"dukascopy:{target_symbol}:{norm_type}"
                    existing = tx.read_records(
                        "datamgr_datasets", filters={"id": dataset_id}, limit=1
                    )
                    require_data(existing)
                    if existing.get("success") and (existing.get("data") or {}).get(
                        "records"
                    ):
                        return StandardResponse.failure(
                            message=(
                                f"Data symbol {target_symbol} already exists. "
                                "Choose a different postfix."
                            ),
                            metadata=ResponseMetadata(
                                operation="dukascopy.add",
                                duration_ms=(time.perf_counter() - start) * 1000,
                            ),
                            error=StandardError(
                                code=ErrorCode.CONFLICT,
                                message=f"Dataset {dataset_id} already exists",
                            ),
                        )

                now_iso = datetime.now(UTC).isoformat()
                real_broker = self.resolve_broker_name(broker)
                created_records: list[dict[str, Any]] = []

                for idx, sym in enumerate(symbol_list):
                    target_symbol = safe_component(f"{sym}{norm_postfix}")
                    dataset_id = f"dukascopy:{target_symbol}:{norm_type}"
                    sym_def = (
                        symbol_definitions[idx]
                        if symbol_definitions and idx < len(symbol_definitions)
                        else "-1"
                    )
                    cat_entry = catalog.get(sym, {})
                    tick_sz = cat_entry.get("tick_size", 0.00001)
                    digits = cat_entry.get("decimals", 5)
                    category = cat_entry.get("category", "Forex")
                    from_date = (
                        cat_entry.get("date_from_m1", "")
                        if norm_type == "M1"
                        else cat_entry.get("date_from_tick", "")
                    )

                    record = {
                        "id": dataset_id,
                        "source": "dukascopy",
                        "symbol": target_symbol,
                        "underlying": sym,
                        "timeframe": norm_type,
                        "broker": real_broker,
                        "timezone": "UTC",
                        "category": category,
                        "date_from": from_date,
                        "date_to": "",
                        "bars": 0,
                        "created_at": now_iso,
                        "updated_at": now_iso,
                        "path": str(
                            dataset_root(self.storage_root, target_symbol, norm_type)
                        ),
                        "data_kind": "bars" if norm_type == "M1" else "ticks",
                        "quality_score": 1.0,
                        "lineage_json": json.dumps(
                            {
                                "tick_size": tick_sz,
                                "digits": digits,
                                "symbol_definition": sym_def,
                                "partitions": [],
                            }
                        ),
                        "schema_version": 1,
                    }
                    require_data(tx.create_records("datamgr_datasets", record))
                    created_records.append(record)
        except (RuntimeError, ValueError, TypeError, OSError) as error:
            return self._failure("add", error, start)

        return StandardResponse.success(
            message=f"Added {len(created_records)} Dukascopy dataset(s)",
            metadata=ResponseMetadata(
                operation="dukascopy.add",
                duration_ms=(time.perf_counter() - start) * 1000,
            ),
            data={"records": created_records, "count": len(created_records)},
        )

    def _prepare_download(
        self,
        symbol: str,
        *,
        underlying: str | None,
        timeframe: str,
        download_type: str,
        date_from: Any,
        date_to: Any,
        overwrite: bool,
        count: int | None,
    ) -> Any:
        target = safe_component(symbol.strip().upper())
        clean = safe_component((underlying or target).strip().upper())
        resolution = timeframe.upper()
        if resolution not in ("M1", "TICK") or download_type not in (
            "standard",
            "cdn",
        ):
            raise ValueError("Unsupported resolution or download mode")
        if not isinstance(overwrite, bool) or (
            count is not None
            and (isinstance(count, bool) or not isinstance(count, int) or count < 1)
        ):
            raise ValueError("Invalid overwrite or count")
        lower = self.parse_date_bound(date_from)
        upper = self.parse_date_bound(date_to, is_end=True)
        if (
            (date_from is not None and lower is None)
            or (date_to is not None and upper is None)
            or (lower and upper and lower > upper)
        ):
            raise ValueError("Choose a valid UTC date range")
        info = self._ensure_catalog().get(clean)
        if info is None:
            raise ValueError(f"Unknown Dukascopy catalog symbol: {clean}")
        return target, clean, resolution, lower, upper, info

    @staticmethod
    def _failure(operation: str, error: Exception, started: float) -> dict[str, Any]:
        code = (
            ErrorCode.UNAVAILABLE
            if isinstance(error, (RuntimeError, OSError))
            else ErrorCode.VALIDATION
        )
        if isinstance(error, BridgeError):
            code = (
                ErrorCode.NOT_FOUND
                if error.code == "NO_DATA"
                else ErrorCode.UNAVAILABLE
            )
        return StandardResponse.failure(
            message=str(error)[:1000] or "Download failed",
            metadata=ResponseMetadata(
                operation=f"dukascopy.{operation}",
                duration_ms=(time.perf_counter() - started) * 1000,
            ),
            error=StandardError(
                code=code, message=str(error)[:1000] or "Download failed"
            ),
        )

    def _publication_unit(
        self, target: str, resolution: str, info: dict[str, Any]
    ) -> float:
        """Keep adopted prices in their catalogue-validated native decimal unit."""
        rows = require_data(
            self.gateway.read_records(
                "datamgr_datasets",
                filters={"id": f"dukascopy:{target}:{resolution}"},
                limit=1,
            )
        )["records"]
        default = float(info["tick_size"])
        if not rows:
            return default
        lineage = json.loads(rows[0]["lineage_json"])
        if lineage.get("provenance") != "owner-supplied-legacy-history":
            return default
        expected = min(Decimal(str(default)), Decimal(1).scaleb(-int(info["decimals"])))
        stored = Decimal(str(lineage.get("tick_size")))
        if not stored.is_finite() or stored <= 0 or stored != expected:
            raise ValueError(
                "Adopted storage unit does not match catalogue precision; "
                "explicit migration required"
            )
        logger.info(
            "FR-DUKASCOPY-adopted-storage-unit: %s %s unit=%s",
            target,
            resolution,
            stored,
        )
        return float(stored)

    def download(
        self,
        symbol: str,
        *,
        timeframe: str = "M1",
        date_from: str | datetime | None = None,
        date_to: str | datetime | None = None,
        underlying: str | None = None,
        broker: str = "default",
        overwrite: bool = False,
        download_type: str = "cdn",
        data_frame: pd.DataFrame | None = None,
        count: int | None = None,
        client: Any = None,
        context: Any = None,
    ) -> dict[str, Any]:
        """Fetch prices and publish canonical yearly/monthly Parquet files."""
        started = time.perf_counter()
        owned = None
        try:
            target, clean, resolution, lower, upper, info = self._prepare_download(
                symbol,
                underlying=underlying,
                timeframe=timeframe,
                download_type=download_type,
                date_from=date_from,
                date_to=date_to,
                overwrite=overwrite,
                count=count,
            )
            require_data(self.gateway.ensure_datasets_schema())
            if context is not None:
                context.wait_if_paused()
            if (
                data_frame is None
                and lower is not None
                and upper is not None
                and count is None
                and not overwrite
            ):
                cached = self._download_missing(
                    target,
                    resolution,
                    lower,
                    upper,
                    {
                        "underlying": clean,
                        "broker": broker,
                        "download_type": download_type,
                        "client": client,
                        "context": context,
                    },
                )
                if cached is not None:
                    return cached
            if data_frame is None:
                if client is None:
                    owned = _get_dukascopy_client()(
                        catalog_path=self.catalog_path,
                        data_dir=self.storage_root,
                        use_cache=False,
                        download_mode=download_type,
                        gateway=self.gateway,
                        context=context,
                    )
                    client = owned
                if resolution == "M1":
                    frame = client.get_bars(
                        clean,
                        Timeframe.PERIOD_M1,
                        date_from=lower,
                        date_to=upper,
                        count=count,
                    )
                else:
                    frame = client.get_ticks(
                        clean, date_from=lower, date_to=upper, count=count
                    )
            else:
                frame = data_frame
            self._require_frame(frame)
            now = datetime.now(UTC).isoformat()
            record = {
                "id": f"dukascopy:{target}:{resolution}",
                "source": "dukascopy",
                "symbol": target,
                "underlying": clean,
                "timeframe": resolution,
                "broker": self.resolve_broker_name(broker),
                "timezone": "UTC",
                "category": info["category"],
                "data_kind": "bars" if resolution == "M1" else "ticks",
                "created_at": now,
            }
            result = publish_frame(
                self.gateway,
                self.storage_root,
                record,
                frame,
                self._publication_unit(target, resolution, info),
                overwrite=overwrite,
                date_from=lower,
                date_to=upper,
                context=context,
                coverage=(lower, upper)
                if data_frame is None
                and count is None
                and lower is not None
                and upper is not None
                else None,
            )
            return StandardResponse.success(
                message=f"Published {resolution} history for {target}",
                metadata=ResponseMetadata(
                    operation="dukascopy.download",
                    duration_ms=(time.perf_counter() - started) * 1000,
                ),
                data={
                    "symbol": target,
                    "underlying": clean,
                    "timeframe": resolution,
                    "downloaded_bars": len(frame),
                    **result,
                },
            )
        except (
            BridgeError,
            RuntimeError,
            OSError,
            ValueError,
            TypeError,
            KeyError,
        ) as error:
            return self._failure("download", error, started)
        finally:
            if owned is not None:
                owned.disconnect()

    @staticmethod
    def _require_frame(frame: Any) -> None:
        if frame is None or frame.empty:
            raise BridgeError(
                "No observations returned for the requested range", code="NO_DATA"
            )

    def _download_missing(
        self,
        target: str,
        timeframe: str,
        lower: datetime,
        upper: datetime,
        options: dict[str, Any],
    ) -> dict[str, Any] | None:
        started = time.perf_counter()
        rows = require_data(
            self.gateway.read_records(
                "datamgr_datasets",
                filters={"id": f"dukascopy:{target}:{timeframe}"},
                limit=1,
            )
        )["records"]
        row = rows[0] if rows else None
        gaps = missing_ranges(row, lower, upper)
        if gaps == [(lower, upper)]:
            return None

        downloaded, written = 0, []
        empty = []
        for index, (start, stop) in enumerate(gaps):
            result = self.download(
                target,
                timeframe=timeframe,
                date_from=start,
                date_to=stop,
                **{
                    **options,
                    "context": RangeProgress(options.get("context"), index, len(gaps)),
                },
            )
            if result["success"]:
                downloaded += result["data"]["downloaded_bars"]
                written.extend(result["data"]["partitions_written"])
            elif result.get("error", {}).get("code") != "not_found":
                require_data(result)
            else:
                empty.append((start, stop))
        row = self.catalog_record(target, timeframe)
        context = options.get("context")
        if context is not None:
            context.raise_if_cancelled()
        record_checked_ranges(self.gateway, row["id"], empty)
        if context is not None:
            context.report_progress(100, "Missing-data download complete")
        return StandardResponse.success(
            message="Requested history is already downloaded"
            if not gaps
            else "Missing history downloaded",
            metadata=ResponseMetadata(
                operation="dukascopy.download",
                duration_ms=(time.perf_counter() - started) * 1000,
            ),
            data={
                "symbol": target,
                "underlying": row["underlying"],
                "timeframe": timeframe,
                "downloaded_bars": downloaded,
                "total_bars": row["bars"],
                "dataset_id": row["id"],
                "date_from": row["date_from"],
                "date_to": row["date_to"],
                "partitions": catalog_paths(row),
                "partitions_written": written,
                "already_downloaded": not gaps,
            },
        )

    def catalog_record(self, symbol: str, timeframe: str) -> dict[str, Any]:
        """Resolve a registered dataset by its stable public identity."""
        rows = require_data(
            self.gateway.read_records(
                "datamgr_datasets",
                filters={"id": f"dukascopy:{symbol.upper()}:{timeframe.upper()}"},
                limit=1,
            )
        )["records"]
        if not rows:
            raise ValueError("Dataset is not registered")
        return cast("dict[str, Any]", rows[0])

    def scan_polars(self, symbol: str, timeframe: str = "M1") -> pl.LazyFrame:
        """Lazily scan catalog partitions, preserving on-disk integer units."""
        return scan_catalog(self.catalog_record(symbol, timeframe))

    def query_duckdb(
        self, query: str, symbol: str | None = None, timeframe: str = "M1"
    ) -> duckdb.DuckDBPyRelation:
        """Query an active snapshot using $PARQUET as the registered relation name."""
        if symbol is None:
            return duckdb.query(query)
        from app.core.data.market_storage import catalog_paths

        connection = duckdb.connect()
        connection.read_parquet(
            catalog_paths(self.catalog_record(symbol, timeframe))
        ).create_view("history")
        return connection.sql(query.replace("$PARQUET", "history"))
