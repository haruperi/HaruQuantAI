"""PyArrow Immutable Partitioned Parquet Writer Engine."""

from __future__ import annotations

import hashlib
import shutil
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from app.contracts.data.market_data_store import CatalogPartRecord, IngestionReceipt
from app.services.data.market_data_store.schema import (
    convert_bars_table_to_canonical,
    convert_ticks_table_to_canonical,
)

if TYPE_CHECKING:
    from app.services.data.market_data_store.catalog import MarketDataCatalog
    from app.services.data.market_data_store.config import MarketDataStoreConfig


class MarketDataWriter:
    """High-performance immutable Parquet dataset writer using PyArrow and Zstandard."""

    def __init__(
        self,
        config: MarketDataStoreConfig,
        catalog: MarketDataCatalog | None = None,
    ) -> None:
        """Initialize the writer.

        Args:
            config: Store configuration parameters.
            catalog: Manifest catalog for recording committed parts.
        """
        self._config = config
        self._catalog = catalog
        self._root = Path(config.storage_root).resolve()
        self._ticks_root = self._root / "ticks"
        self._bars_root = self._root / "bars"
        self._staging_root = self._root / config.staging_dir_name

        self._ticks_root.mkdir(parents=True, exist_ok=True)
        self._bars_root.mkdir(parents=True, exist_ok=True)
        self._staging_root.mkdir(parents=True, exist_ok=True)

    def append_ticks(
        self,
        table: pa.Table,
        *,
        source: str,
        symbol: str,
        tick_size: float | Decimal = 0.00001,
    ) -> IngestionReceipt:
        """Process, validate, stage, and atomically append an immutable batch of ticks.

        Args:
            table: Input PyArrow table with tick data.
            source: Origin broker or feed identifier (e.g. 'dukascopy').
            symbol: Instrument ticker (e.g. 'EURUSD').
            tick_size: Tick size for fixed-point integer scaling.

        Returns:
            IngestionReceipt with committed file paths, row counts, and checksums.
        """
        if table.num_rows == 0:
            now = datetime.now(UTC)
            return IngestionReceipt(
                part_paths=[],
                dataset="ticks",
                source=source,
                symbol=symbol,
                timeframe="TICK",
                minimum_datetime=now,
                maximum_datetime=now,
                row_count=0,
                schema_version=1,
                checksums=[],
                committed_at=now,
            )

        # 1. Transform to canonical schema (with fixed-point int64 ticks)
        canonical_table = convert_ticks_table_to_canonical(table, tick_size=tick_size)

        # 2. Add partitioning columns: source, symbol, year, month
        dt_array = canonical_table["datetime"]
        years = pc.strftime(dt_array, format="%Y")  # type: ignore[attr-defined]
        months = pc.strftime(dt_array, format="%m")  # type: ignore[attr-defined]

        source_col = pa.array([source] * len(canonical_table), type=pa.string())
        symbol_col = pa.array([symbol] * len(canonical_table), type=pa.string())

        full_table = canonical_table.append_column("source", source_col)
        full_table = full_table.append_column("symbol", symbol_col)
        full_table = full_table.append_column("year", years)
        full_table = full_table.append_column("month", months)

        # 3. Sort chronologically by datetime, sequence
        sort_indices = pc.sort_indices(  # type: ignore[attr-defined]
            full_table,
            sort_keys=[("datetime", "ascending"), ("sequence", "ascending")],
        )
        sorted_table = pc.take(full_table, sort_indices)

        # 4. Deduplicate on composite identity key (datetime, sequence)
        sorted_table = self._deduplicate_ticks(sorted_table)

        # 5. Write to staging, validate, and atomically promote
        partition_cols = ["source", "symbol", "year", "month"]
        return self._stage_validate_and_commit(
            table=sorted_table,
            dest_root=self._ticks_root,
            partition_cols=partition_cols,
            dataset="ticks",
            source=source,
            symbol=symbol,
            timeframe="TICK",
        )

    def append_bars(
        self,
        table: pa.Table,
        *,
        source: str,
        symbol: str,
        timeframe: str = "M1",
        tick_size: float | Decimal = 0.00001,
    ) -> IngestionReceipt:
        """Process, validate, stage, and atomically append an immutable batch of bars.

        Args:
            table: Input PyArrow table with bar data.
            source: Origin broker or feed identifier.
            symbol: Instrument ticker.
            timeframe: Timeframe code (e.g. 'M1').
            tick_size: Tick size for fixed-point integer scaling.

        Returns:
            IngestionReceipt with committed file paths, row counts, and checksums.
        """
        if table.num_rows == 0:
            now = datetime.now(UTC)
            return IngestionReceipt(
                part_paths=[],
                dataset="bars",
                source=source,
                symbol=symbol,
                timeframe=timeframe,
                minimum_datetime=now,
                maximum_datetime=now,
                row_count=0,
                schema_version=1,
                checksums=[],
                committed_at=now,
            )

        # 1. Transform to canonical schema
        canonical_table = convert_bars_table_to_canonical(table, tick_size=tick_size)

        # 2. Add partitioning columns: source, timeframe, symbol, year
        dt_array = canonical_table["datetime"]
        years = pc.strftime(dt_array, format="%Y")  # type: ignore[attr-defined]

        source_col = pa.array([source] * len(canonical_table), type=pa.string())
        tf_col = pa.array([timeframe] * len(canonical_table), type=pa.string())
        symbol_col = pa.array([symbol] * len(canonical_table), type=pa.string())

        full_table = canonical_table.append_column("source", source_col)
        full_table = full_table.append_column("timeframe", tf_col)
        full_table = full_table.append_column("symbol", symbol_col)
        full_table = full_table.append_column("year", years)

        # 3. Sort chronologically by datetime
        sort_indices = pc.sort_indices(  # type: ignore[attr-defined]
            full_table, sort_keys=[("datetime", "ascending")]
        )
        sorted_table = pc.take(full_table, sort_indices)

        # 4. Deduplicate bars on datetime
        sorted_table = self._deduplicate_bars(sorted_table)

        # 5. Write to staging, validate, and atomically promote
        partition_cols = ["source", "timeframe", "symbol", "year"]
        return self._stage_validate_and_commit(
            table=sorted_table,
            dest_root=self._bars_root,
            partition_cols=partition_cols,
            dataset="bars",
            source=source,
            symbol=symbol,
            timeframe=timeframe,
        )

    def _deduplicate_ticks(self, table: pa.Table) -> pa.Table:
        """Deduplicate ticks using exact (datetime, sequence) identity key."""
        dts = table["datetime"].to_numpy(zero_copy_only=False)
        seqs = table["sequence"].to_numpy(zero_copy_only=False)

        if len(dts) <= 1:
            return table

        is_dup = (dts[1:] == dts[:-1]) & (seqs[1:] == seqs[:-1])
        if not np.any(is_dup):
            return table

        keep_mask = np.ones(len(table), dtype=bool)
        keep_mask[1:][is_dup] = False
        return table.filter(pa.array(keep_mask))

    def _deduplicate_bars(self, table: pa.Table) -> pa.Table:
        """Deduplicate bars using exact datetime identity key."""
        dts = table["datetime"].to_numpy(zero_copy_only=False)
        if len(dts) <= 1:
            return table

        is_dup = dts[1:] == dts[:-1]
        if not np.any(is_dup):
            return table

        keep_mask = np.ones(len(table), dtype=bool)
        keep_mask[1:][is_dup] = False
        return table.filter(pa.array(keep_mask))

    def _stage_validate_and_commit(
        self,
        table: pa.Table,
        dest_root: Path,
        partition_cols: list[str],
        dataset: Literal["ticks", "bars"],
        source: str,
        symbol: str,
        timeframe: str,
    ) -> IngestionReceipt:
        """Stage, validate, promote to dest_root, and update catalog."""
        run_id = uuid4().hex
        stage_dir = self._staging_root / f"stage-{run_id}"
        stage_dir.mkdir(parents=True, exist_ok=True)

        basename = f"part-{run_id}-{{i}}.parquet"

        try:
            pq.write_to_dataset(
                table=table,
                root_path=stage_dir,
                partition_cols=partition_cols,
                basename_template=basename,
                existing_data_behavior="overwrite_or_ignore",
                compression=self._config.compression,
                compression_level=self._config.compression_level,
                version="2.6",
                use_dictionary=True,
                write_statistics=True,
                write_page_checksum=True,
                min_rows_per_group=self._config.min_rows_per_group,
                row_group_size=self._config.max_rows_per_group,
                max_rows_per_file=self._config.max_rows_per_file,
            )

            staged_files: list[Path] = list(stage_dir.glob("**/*.parquet"))
            if not staged_files:
                msg = (
                    f"No parquet part files produced in staging directory: {stage_dir}"
                )
                raise RuntimeError(msg)

            committed_paths: list[str] = []
            checksums: list[str] = []
            total_verified_rows = 0
            all_min_dts: list[datetime] = []
            all_max_dts: list[datetime] = []
            now = datetime.now(UTC)

            for staged_file in staged_files:
                meta = pq.read_metadata(staged_file)
                part_rows = meta.num_rows
                total_verified_rows += part_rows

                with Path(staged_file).open("rb") as f:
                    digest = hashlib.sha256(f.read()).hexdigest()
                checksums.append(digest)

                part_tab = pq.read_table(staged_file, columns=["datetime"])
                min_ts = pc.min(part_tab["datetime"]).as_py()  # type: ignore[attr-defined]
                max_ts = pc.max(part_tab["datetime"]).as_py()  # type: ignore[attr-defined]
                all_min_dts.append(min_ts)
                all_max_dts.append(max_ts)

                rel_path = staged_file.relative_to(stage_dir)
                target_file = dest_root / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)

                shutil.move(str(staged_file), str(target_file))
                committed_paths.append(str(target_file))

                if self._catalog is not None:
                    part_record = CatalogPartRecord(
                        file_path=str(target_file),
                        dataset=dataset,
                        source=source,
                        symbol=symbol,
                        timeframe=timeframe,
                        minimum_datetime=min_ts,
                        maximum_datetime=max_ts,
                        row_count=part_rows,
                        schema_version=1,
                        checksum=digest,
                        created_at=now,
                    )
                    self._catalog.register_part(part_record)

            min_dt = min(all_min_dts)
            max_dt = max(all_max_dts)

            return IngestionReceipt(
                part_paths=committed_paths,
                dataset=dataset,
                source=source,
                symbol=symbol,
                timeframe=timeframe,
                minimum_datetime=min_dt,
                maximum_datetime=max_dt,
                row_count=total_verified_rows,
                schema_version=1,
                checksums=checksums,
                committed_at=now,
            )
        finally:
            if stage_dir.exists():
                shutil.rmtree(stage_dir, ignore_errors=True)
