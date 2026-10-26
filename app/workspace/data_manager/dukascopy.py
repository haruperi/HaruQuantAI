"""Dukascopy market data ingestion, partitioning, and catalog service.

Description:
    Manages Dukascopy Bank SA historical market data ingestion according to
    the HaruQuantAI canonical data architecture:
    - Storage: Partitioned Parquet with ZSTD level 6 compression.
    - Historical writer: PyArrow, batched immutable parts.
    - Research/backtest reader: Polars lazy scans.
    - SQL/ad-hoc analytical reader: DuckDB directly over Parquet.
    - Ingestion state & catalog: SQLite datamgr_datasets table.
    - Partitions:
        - Ticks: source / ticks / symbol / year / month (e.g. 04-apr.parquet)
        - M1: source / m1 / symbol / year (e.g. 2025.parquet)
    - On-disk schema: Integer tick units (int64) for prices, not float64.
"""

from __future__ import annotations

import calendar
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb  # type: ignore[import-untyped]
import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import polars as pl  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.include.enums import Timeframe
from app.workspace.brokers.base import BridgeError
from app.workspace.brokers.dukascopy import DukascopyClient
from app.workspace.data_manager.logs import Logs

logger = get_logger(__name__)

# Canonical Schemas: Integer tick units for on-disk prices
TICK_SCHEMA = pa.schema(
    [
        ("DateTime", pa.timestamp("us", tz="UTC")),
        ("Bid", pa.int64()),
        ("Ask", pa.int64()),
        ("Flags", pa.uint16()),
    ]
)

M1_SCHEMA = pa.schema(
    [
        ("DateTime", pa.timestamp("us", tz="UTC")),
        ("Open", pa.int64()),
        ("High", pa.int64()),
        ("Low", pa.int64()),
        ("Close", pa.int64()),
        ("Volume", pa.uint64()),
    ]
)

DEFAULT_STORAGE_ROOT = Path("data/market/dukascopy")
DEFAULT_CATALOG_PATH = DEFAULT_STORAGE_ROOT / "dukascopy.csv"
MIN_CATALOG_PARTS = 11

DISCLAIMER_PARAGRAPHS = [
    (
        "The Dukascopy Trading Tools include different financial information. "
        "Such data are a result of original and unique methods and technology of "
        "information gathering, compilation, analysis and statistical evaluation "
        "developed by Dukascopy Bank SA. Therefore, such data reflect the current "
        "fair value of the respective financial instruments as independently assessed "
        "by Dukascopy Bank SA and NOT the actual values at a given point in time. "
        "If you are looking to obtain actual quotes please contact the respective "
        "entities that provide this information."
    ),
    (
        "The Dukascopy Trading Tools data and/or any other data available as free "
        "product from Dukascopy Bank's website shall not constitute a forecast of "
        "the market value of any instruments at any future point either, and is "
        "not an investment advice or recommendation in any form."
    ),
    (
        "Anyone using and/or putting free web products including all or parts of the "
        "information taken from the Dukascopy Trading Tools and/or any other data "
        "available as free product from Dukascopy Bank's website shall put a clear "
        "note to the public that such data are not meant to indicate the actual value "
        "at any given point in time but represent a discretionary assessment by "
        "Dukascopy Bank SA only."
    ),
    (
        "The market data assessment system is in constant development and is provided "
        "'AS IS', 'AS AVAILABLE', 'WITH ALL ITS FAULTS' and is offered without any "
        "covenants or any express, implied or statutory warranties including "
        "(without limitation and qualification) any warranties as to accuracy, "
        "functionality, performance, merchantability, quiet enjoyment, system "
        "integration, data accuracy or fitness for any particular purpose and any "
        "warranties arising from trade usage, course of dealing or course of "
        "performance."
    ),
]


class Dukascopy:
    """Service managing Dukascopy dataset catalog and historical Parquet ingestion."""

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        storage_root: str | Path | None = None,
        catalog_path: str | Path | None = None,
    ) -> None:
        """Initialize Dukascopy service with gateway and storage paths."""
        self.gateway = gateway or HostPersistence()
        self.storage_root = Path(storage_root) if storage_root else DEFAULT_STORAGE_ROOT
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
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

    def _validate_add_parameters(
        self,
        symbols: str | list[str],
        data_type: str,
        postfix: str,
        disclaimer_confirmed: bool,
    ) -> tuple[list[str], str, str] | StandardResponse:
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
        validation = self._validate_add_parameters(
            symbols, data_type, postfix, disclaimer_confirmed
        )
        if isinstance(validation, dict) or not isinstance(validation, tuple):
            return validation

        symbol_list, norm_type, norm_postfix = validation
        catalog = self._ensure_catalog()
        for sym in symbol_list:
            if catalog and sym not in catalog:
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

        self.gateway.ensure_datasets_schema()

        # Check for existing datasets to prevent duplicate collision
        for sym in symbol_list:
            target_symbol = f"{sym}{norm_postfix}"
            dataset_id = f"dukascopy:{target_symbol}:{norm_type}"
            existing = self.gateway.read_records(
                "datamgr_datasets", filters={"id": dataset_id}, limit=1
            )
            if existing.get("success") and (existing.get("data") or {}).get("records"):
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
        b_name = "SQ default" if broker in ("-1", "default", "SQ default") else broker
        created_records: list[dict[str, Any]] = []

        for idx, sym in enumerate(symbol_list):
            target_symbol = f"{sym}{norm_postfix}"
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
                "instrument": sym_def,
                "timeframe": norm_type,
                "broker": broker,
                "broker_name": b_name,
                "timezone": "UTC",
                "category": category,
                "date_from": from_date,
                "date_to": "",
                "bars": 0,
                "created_at": now_iso,
                "updated_at": now_iso,
                "path": str(
                    self.storage_root / norm_type.lower() / target_symbol.lower()
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
            self.gateway.create_records("datamgr_datasets", record)
            created_records.append(record)

        return StandardResponse.success(
            message=f"Added {len(created_records)} Dukascopy dataset(s)",
            metadata=ResponseMetadata(
                operation="dukascopy.add",
                duration_ms=(time.perf_counter() - start) * 1000,
            ),
            data={"records": created_records, "count": len(created_records)},
        )

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
        client: Any | None = None,
    ) -> dict[str, Any]:
        """Download market data and save partitioned Parquet with ZSTD level 6."""
        start = time.perf_counter()
        del download_type
        clean_symbol = (underlying or symbol).strip().upper()
        norm_tf = timeframe.strip().upper()

        if norm_tf not in ("M1", "TICK"):
            return StandardResponse.failure(
                message=f"Timeframe '{timeframe}' not supported. Supported: M1, TICK",
                metadata=ResponseMetadata(
                    operation="dukascopy.download",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.VALIDATION,
                    message="Unsupported timeframe",
                ),
            )

        catalog = self._ensure_catalog()
        cat_info = catalog.get(clean_symbol)
        digits = cat_info.get("decimals", 5) if cat_info else 5
        tick_sz = cat_info.get("tick_size", 0.00001) if cat_info else 0.00001
        scale = 1.0 / tick_sz if tick_sz > 0 else float(10**digits)

        df: pd.DataFrame
        if data_frame is not None:
            df = data_frame.copy()
        else:
            duk_client = client or DukascopyClient(
                catalog_path=self.catalog_path, data_dir=self.storage_root
            )
            try:
                if norm_tf == "M1":
                    df = duk_client.get_bars(
                        clean_symbol,
                        Timeframe.PERIOD_M1,
                        date_from=date_from,
                        date_to=date_to,
                        count=count,
                    )
                else:
                    df = duk_client.get_ticks(
                        clean_symbol,
                        date_from=date_from,
                        date_to=date_to,
                        count=count,
                    )
            except (BridgeError, OSError, ValueError, RuntimeError) as exc:
                return StandardResponse.failure(
                    message=(
                        f"Failed to download Dukascopy data for {clean_symbol}: {exc}"
                    ),
                    metadata=ResponseMetadata(
                        operation="dukascopy.download",
                        duration_ms=(time.perf_counter() - start) * 1000,
                    ),
                    error=StandardError(
                        code=ErrorCode.INTERNAL,
                        message=str(exc),
                    ),
                )

        if df is None or len(df) == 0:
            return StandardResponse.failure(
                message=f"No {norm_tf} data available for {clean_symbol}",
                metadata=ResponseMetadata(
                    operation="dukascopy.download",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.NOT_FOUND,
                    message="Empty dataset returned",
                ),
            )

        # Standardize DateTime index / column
        if "DateTime" not in df.columns:
            df["DateTime"] = pd.to_datetime(df.index, utc=True)
        else:
            df["DateTime"] = pd.to_datetime(df["DateTime"], utc=True)

        df.sort_values("DateTime", inplace=True)
        written_files: list[Path] = []

        if norm_tf == "M1":
            written_files = self._write_m1_partitions(
                df, clean_symbol, scale, overwrite
            )
        else:
            written_files = self._write_tick_partitions(
                df, clean_symbol, scale, overwrite
            )

        # Re-compute total bars & range across all partitions
        total_bars, min_dt, max_dt, all_partitions = self._audit_partitions(
            clean_symbol, norm_tf
        )
        min_date_str = (
            min_dt.strftime("%Y-%m-%d")
            if min_dt
            else (str(date_from or "").split("T")[0])
        )
        max_date_str = (
            max_dt.strftime("%Y-%m-%d")
            if max_dt
            else (str(date_to or "").split("T")[0])
        )

        # Persist ingestion state in SQLite
        dataset_id = self._record_dataset_catalog(
            symbol=symbol,
            underlying=clean_symbol,
            timeframe=norm_tf,
            broker=broker,
            bars=total_bars,
            date_from=min_date_str,
            date_to=max_date_str,
            partitions=[str(p) for p in all_partitions],
            tick_size=tick_sz,
            digits=digits,
        )

        Logs().record_progress(
            task_id="dukascopy_download",
            progress=100.0,
            message=(
                f"Downloaded {len(df)} {norm_tf} records for {clean_symbol} "
                f"({total_bars} total)"
            ),
            level="info",
        )

        return StandardResponse.success(
            message=f"Downloaded and saved {len(df)} {norm_tf} records for {symbol}",
            metadata=ResponseMetadata(
                operation="dukascopy.download",
                duration_ms=(time.perf_counter() - start) * 1000,
            ),
            data={
                "symbol": symbol,
                "underlying": clean_symbol,
                "timeframe": norm_tf,
                "downloaded_bars": len(df),
                "total_bars": total_bars,
                "date_from": min_date_str,
                "date_to": max_date_str,
                "partitions_written": [str(p) for p in written_files],
                "dataset_id": dataset_id,
            },
        )

    def _write_m1_partitions(
        self,
        df: pd.DataFrame,
        symbol: str,
        scale: float,
        overwrite: bool,
    ) -> list[Path]:
        """Write M1 bars grouped by year as integer tick units."""
        target_dir = self.storage_root / "m1" / symbol.lower()
        target_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []

        # Convert prices to int64 tick units
        open_ints = (df["Open"] * scale).round().astype(np.int64)
        high_ints = (df["High"] * scale).round().astype(np.int64)
        low_ints = (df["Low"] * scale).round().astype(np.int64)
        close_ints = (df["Close"] * scale).round().astype(np.int64)
        vol_ints = (
            df["Volume"].fillna(0).astype(np.uint64)
            if "Volume" in df.columns
            else np.zeros(len(df), dtype=np.uint64)
        )

        transformed = pd.DataFrame(
            {
                "DateTime": df["DateTime"],
                "Open": open_ints,
                "High": high_ints,
                "Low": low_ints,
                "Close": close_ints,
                "Volume": vol_ints,
            }
        )

        for year, group in transformed.groupby(transformed["DateTime"].dt.year):
            file_path = target_dir / f"{year}.parquet"
            final_df = group
            if file_path.exists() and not overwrite:
                try:
                    existing = pq.read_table(file_path).to_pandas()
                    merged = pd.concat([existing, group], ignore_index=True)
                    merged.drop_duplicates(subset=["DateTime"], inplace=True)
                    merged.sort_values("DateTime", inplace=True)
                    final_df = merged
                except OSError, ValueError, pa.ArrowInvalid:
                    final_df = group

            table = pa.Table.from_pandas(
                final_df, schema=M1_SCHEMA, preserve_index=False
            )
            pq.write_table(table, file_path, compression="ZSTD", compression_level=6)
            written.append(file_path)

        return written

    def _write_tick_partitions(
        self,
        df: pd.DataFrame,
        symbol: str,
        scale: float,
        overwrite: bool,
    ) -> list[Path]:
        """Write ticks grouped by year and month as integer tick units."""
        sym_lower = symbol.lower()
        written: list[Path] = []

        bid_ints = (df["Bid"] * scale).round().astype(np.int64)
        ask_ints = (df["Ask"] * scale).round().astype(np.int64)
        flags = (
            df["Flags"].fillna(0).astype(np.uint16)
            if "Flags" in df.columns
            else np.zeros(len(df), dtype=np.uint16)
        )

        transformed = pd.DataFrame(
            {
                "DateTime": df["DateTime"],
                "Bid": bid_ints,
                "Ask": ask_ints,
                "Flags": flags,
            }
        )

        dt_series = transformed["DateTime"]
        groups = transformed.groupby([dt_series.dt.year, dt_series.dt.month])
        for (year, month), group in groups:
            month_abbr = calendar.month_abbr[month].lower()
            month_filename = f"{month:02d}-{month_abbr}.parquet"
            month_dir = self.storage_root / "ticks" / sym_lower / str(year)
            month_dir.mkdir(parents=True, exist_ok=True)
            file_path = month_dir / month_filename
            final_df = group

            if file_path.exists() and not overwrite:
                try:
                    existing = pq.read_table(file_path).to_pandas()
                    merged = pd.concat([existing, group], ignore_index=True)
                    merged.drop_duplicates(subset=["DateTime"], inplace=True)
                    merged.sort_values("DateTime", inplace=True)
                    final_df = merged
                except OSError, ValueError, pa.ArrowInvalid:
                    final_df = group

            table = pa.Table.from_pandas(
                final_df, schema=TICK_SCHEMA, preserve_index=False
            )
            pq.write_table(table, file_path, compression="ZSTD", compression_level=6)
            written.append(file_path)

        return written

    def _audit_partitions(
        self,
        symbol: str,
        timeframe: str,
    ) -> tuple[int, datetime | None, datetime | None, list[Path]]:
        """Inspect on-disk Parquet partitions and calculate total records and bounds."""
        sub_dir = "m1" if timeframe == "M1" else "ticks"
        root = self.storage_root / sub_dir / symbol.lower()
        if not root.exists():
            return 0, None, None, []

        parquet_files = sorted(root.rglob("*.parquet"))
        total_rows = 0
        min_dt: datetime | None = None
        max_dt: datetime | None = None

        for p in parquet_files:
            try:
                meta = pq.read_metadata(p)
                total_rows += meta.num_rows
                if meta.num_rows > 0:
                    tbl = pq.read_table(p, columns=["DateTime"])
                    col = tbl.column("DateTime")
                    p_min = col[0].as_py()
                    p_max = col[-1].as_py()
                    if min_dt is None or p_min < min_dt:
                        min_dt = p_min
                    if max_dt is None or p_max > max_dt:
                        max_dt = p_max
            except (OSError, ValueError, pa.ArrowInvalid) as audit_err:
                logger.debug("Partition inspect skipped %s: %s", p, audit_err)

        return total_rows, min_dt, max_dt, parquet_files

    def _record_dataset_catalog(
        self,
        *,
        symbol: str,
        underlying: str,
        timeframe: str,
        broker: str,
        bars: int,
        date_from: str,
        date_to: str,
        partitions: list[str],
        tick_size: float,
        digits: int,
    ) -> str:
        """Upsert ingestion state into datamgr_datasets table."""
        self.gateway.ensure_datasets_schema()
        dataset_id = f"dukascopy:{symbol}:{timeframe}"
        now_iso = datetime.now(UTC).isoformat()
        b_name = "SQ default" if broker in ("-1", "default", "SQ default") else broker
        catalog = self._ensure_catalog()
        cat_info = catalog.get(underlying, {})
        category = cat_info.get("category", "Forex")
        path_str = str(self.storage_root / timeframe.lower() / symbol.lower())

        lineage = json.dumps(
            {
                "tick_size": tick_size,
                "digits": digits,
                "partitions": partitions,
                "data_kind": "bars" if timeframe == "M1" else "ticks",
            }
        )

        existing = self.gateway.read_records(
            "datamgr_datasets", filters={"id": dataset_id}, limit=1
        )
        if existing.get("success") and (existing.get("data") or {}).get("records"):
            self.gateway.update_record(
                "datamgr_datasets",
                {
                    "bars": bars,
                    "date_from": date_from,
                    "date_to": date_to,
                    "path": path_str,
                    "updated_at": now_iso,
                    "lineage_json": lineage,
                },
                filters={"id": dataset_id},
            )
        else:
            self.gateway.create_records(
                "datamgr_datasets",
                {
                    "id": dataset_id,
                    "source": "dukascopy",
                    "symbol": symbol,
                    "underlying": underlying,
                    "instrument": symbol,
                    "timeframe": timeframe,
                    "broker": broker,
                    "broker_name": b_name,
                    "timezone": "UTC",
                    "category": category,
                    "date_from": date_from,
                    "date_to": date_to,
                    "bars": bars,
                    "path": path_str,
                    "data_kind": "bars" if timeframe == "M1" else "ticks",
                    "quality_score": 1.0,
                    "lineage_json": lineage,
                    "schema_version": 1,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
            )
        return dataset_id

    def scan_polars(self, symbol: str, timeframe: str = "M1") -> pl.LazyFrame:
        """Open lazy Polars scan over partitioned Parquet files for research."""
        sub_dir = "m1" if timeframe.upper() == "M1" else "ticks"
        target_path = self.storage_root / sub_dir / symbol.lower()
        glob_pattern = str(target_path / "**" / "*.parquet").replace("\\", "/")
        return pl.scan_parquet(glob_pattern)

    def query_duckdb(
        self, query: str, symbol: str | None = None, timeframe: str = "M1"
    ) -> duckdb.DuckDBPyRelation:
        """Run SQL directly over partitioned Parquet files using DuckDB."""
        if symbol:
            sub_dir = "m1" if timeframe.upper() == "M1" else "ticks"
            path_str = str(
                self.storage_root / sub_dir / symbol.lower() / "**" / "*.parquet"
            ).replace("\\", "/")
            query = query.replace("$PARQUET", f"'{path_str}'")
        return duckdb.query(query)
