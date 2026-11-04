"""Canonical market dataset catalog service and query contracts.

Description:
    Validates dataset references through shared timeframe semantics while
    preserving stored catalog keys, then coordinates bounded partition reads.
Purpose:
    FEAT-DATA-TIMEFRAMES: Validate timeframe references without changing identity.
Key Capabilities:
    - FR-data-catalog-timeframes: Shared owner logs DEBUG validation; isolated
      catalog tests verify unchanged keys and custom timeframe reads.
Python API Usage:
    DatasetRef(symbol="EURUSD", timeframe="H7")
CLI Usage:
    uv run pytest tests/core/data/test_catalog.py --no-cov
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import pandas as pd  # type: ignore[import-untyped]
import polars as pl
import pyarrow as pa

from app.core.data.contracts import DataInfo
from app.core.data.io import DataIO
from app.core.data.market_storage import catalog_paths, safe_component
from app.core.data.timeframes import timeframe_to_seconds
from app.core.enums import Timeframe
from app.core.lib.errors import DomainError

if TYPE_CHECKING:
    from app.core.data.charts import ChartDef
    from app.core.data.instruments import InstrumentInfo
    from app.core.host.persistence import HostPersistence

__all__ = ["DataBatch", "DataCatalog", "DatasetRef"]


def _normalize_bound(val: datetime | int | None) -> datetime | None:
    """Normalize datetime or integer epoch timestamps into a UTC-aware datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return (
            val.astimezone(UTC) if val.tzinfo is not None else val.replace(tzinfo=UTC)
        )
    if isinstance(val, int):
        if val > 10**14:  # Microseconds
            return datetime.fromtimestamp(val / 1_000_000, tz=UTC)
        if val > 10**11:  # Milliseconds
            return datetime.fromtimestamp(val / 1_000, tz=UTC)
        return datetime.fromtimestamp(val, tz=UTC)  # Seconds
    raise DomainError(
        code="INVALID_TIME_BOUND",
        message=f"Unsupported timestamp bound type: {type(val).__name__}",
    )


@dataclass(frozen=True, slots=True)
class DatasetRef:
    """Canonical immutable reference identifying a versioned market dataset."""

    symbol: str
    timeframe: str | Timeframe = "M1"
    source: str = "default"
    revision: str | int | None = None

    def __post_init__(self) -> None:
        """Validate components and normalize timeframe to uppercase string."""
        object.__setattr__(self, "symbol", safe_component(self.symbol))
        src = self.source or "default"
        object.__setattr__(self, "source", safe_component(src))
        tf_str = (
            self.timeframe.value
            if isinstance(self.timeframe, Timeframe)
            else str(self.timeframe).strip().upper()
        )
        timeframe_to_seconds(tf_str)
        object.__setattr__(self, "timeframe", tf_str)

    @property
    def dataset_id(self) -> str:
        """Deterministic dataset identifier in datamgr_datasets table."""
        return f"{self.source}:{self.symbol}:{self.timeframe}"


@dataclass(frozen=True, slots=True)
class DataBatch:
    """Immutable batch of market data observations returned by DataCatalog."""

    ref: DatasetRef
    frame: pl.DataFrame
    start: datetime | None
    end: datetime | None
    row_count: int
    tick_size: float
    decoded: bool = True

    @property
    def is_empty(self) -> bool:
        """True if the batch contains zero observations."""
        return self.row_count == 0

    def to_pandas(self) -> pd.DataFrame:
        """Convert Polars DataFrame to a pandas DataFrame indexed by DateTime."""
        if self.frame.is_empty():
            return pd.DataFrame()
        df = self.frame.to_pandas()
        if "DateTime" in df.columns:
            df = df.set_index("DateTime")
        return df

    def to_arrow(self) -> pa.Table:
        """Convert Polars DataFrame to a PyArrow Table."""
        return self.frame.to_arrow()


class DataCatalog:
    """Shared dataset catalog reader and reference resolver for research engines."""

    def __init__(self, persistence: HostPersistence) -> None:
        """Initialize catalog reader with persistence gateway."""
        self.persistence = persistence

    def get_dataset_info(self, ref: DatasetRef) -> DataInfo | None:
        """Retrieve catalog metadata for a dataset reference if registered."""
        result = self._find_record(ref)
        if result is None:
            return None
        row, _ = result
        return DataInfo.from_row(row)

    def create_chart(
        self,
        ref: DatasetRef,
        instrument_info: InstrumentInfo | None,
        *,
        session: str,
        timezone: str,
        bar_time_type: Literal[1, 2],
        mode: Literal["live", "backtest"] = "backtest",
        history_from: int = 0,
        history_to: int = 0,
        spread: float = 0.0,
        backload_type: int = 0,
        backload_number: int = 0,
    ) -> ChartDef:
        """Resolve donor constructor metadata once, then delegate chart semantics.

        Maps ChartDef's DataManager lookup. InstrumentManager's resolved value
        is explicit; this catalog does not introduce another instrument registry.
        """
        from app.core.data.charts import ChartDef

        info = self.get_dataset_info(ref)
        if info is None:
            raise DomainError(
                code="DATASET_NOT_FOUND", message="Chart data cannot be found"
            )
        if bar_time_type not in (1, 2):
            raise ValueError("Unknown donor bar time type")
        if info.symbol != ref.symbol or info.connection != ref.source:
            raise DomainError(
                code="DATASET_IDENTITY_MISMATCH",
                message="Chart metadata does not match the requested dataset",
            )
        # Existing host rows do not encode donor DATATYPE. Its resolved value
        # is explicit instead of inferred from bar timestamps or provider names.
        info.bar_time_type = bar_time_type
        if mode == "live":
            return ChartDef.for_live(
                info,
                instrument_info,
                timeframe=ref.timeframe,
                backload_type=backload_type,
                backload_number=backload_number,
                session=session,
            )
        if mode != "backtest":
            raise ValueError("Unknown chart initialization mode")
        return ChartDef.for_backtest(
            info,
            instrument_info,
            timeframe=ref.timeframe,
            history_from=history_from,
            history_to=history_to,
            spread=spread,
            session=session,
            timezone=timezone,
        )

    def _find_record(self, ref: DatasetRef) -> tuple[dict[str, Any], bool] | None:
        """Look up catalog record by exact ref or base M1 resample source."""
        # 1. Exact ID match
        response = self.persistence.read_records(
            "datamgr_datasets", filters={"id": ref.dataset_id}, limit=1
        )
        if response.get("success") and response.get("data", {}).get("records"):
            return response["data"]["records"][0], False

        # 2. Match by composite attributes
        response = self.persistence.read_records(
            "datamgr_datasets",
            filters={
                "source": ref.source,
                "symbol": ref.symbol,
                "timeframe": ref.timeframe,
            },
            limit=1,
        )
        if response.get("success") and response.get("data", {}).get("records"):
            return response["data"]["records"][0], False

        # 3. Base M1 fallback for resamplable bar timeframes
        if ref.timeframe not in ("M1", "TICK"):
            base_resp = self.persistence.read_records(
                "datamgr_datasets",
                filters={
                    "source": ref.source,
                    "symbol": ref.symbol,
                    "timeframe": "M1",
                },
                limit=1,
            )
            if base_resp.get("success") and base_resp.get("data", {}).get("records"):
                return base_resp["data"]["records"][0], True

        return None

    @staticmethod
    def _validate_range(dt_start: datetime | None, dt_end: datetime | None) -> None:
        """Ensure start bound does not exceed end bound."""
        if dt_start is not None and dt_end is not None and dt_start > dt_end:
            msg = (
                f"Start timestamp {dt_start.isoformat()} cannot be after "
                f"end timestamp {dt_end.isoformat()}"
            )
            raise DomainError(code="INVALID_TIME_RANGE", message=msg)

    @staticmethod
    def _validate_revision(ref: DatasetRef, row: dict[str, Any]) -> None:
        """Verify optimistic concurrency snapshot revision if requested."""
        if ref.revision is not None:
            current = row.get("updated_at") or str(row.get("schema_version", ""))
            if str(ref.revision) != str(current):
                msg = (
                    f"Dataset revision mismatch: requested '{ref.revision}', "
                    f"current '{current}'"
                )
                raise DomainError(code="STALE_CATALOG_REVISION", message=msg)

    @staticmethod
    def _resolve_partitions(row: dict[str, Any]) -> tuple[list[str], float]:
        """Extract committed isolated partitions and tick size from dataset row."""
        lineage = json.loads(row.get("lineage_json") or "{}")
        partitions = lineage.get("partitions")
        if partitions is None:
            partitions = catalog_paths(row)

        isolated = [
            p
            for p in partitions
            if not any(
                part.startswith((".", "tmp", "stage"))
                or part.endswith((".tmp", ".stage"))
                for part in Path(p).parts
            )
        ]
        tick_size = float(lineage.get("tick_size") or 0.0001)
        return isolated, tick_size

    def read(
        self,
        ref: DatasetRef,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        count: int | None = None,
        decode: bool = True,
        context: Any = None,
    ) -> DataBatch:
        """Read a bounded batch of market observations matching a DatasetRef."""
        dt_start = _normalize_bound(start)
        dt_end = _normalize_bound(end)
        self._validate_range(dt_start, dt_end)

        match_result = self._find_record(ref)
        if match_result is None:
            raise DomainError(
                code="DATASET_NOT_FOUND",
                message=f"Dataset '{ref.dataset_id}' not found in catalog",
            )

        row, needs_resampling = match_result
        self._validate_revision(ref, row)
        isolated_paths, tick_size = self._resolve_partitions(row)

        if context is not None and hasattr(context, "raise_if_cancelled"):
            context.raise_if_cancelled()

        if not isolated_paths or int(row.get("bars", 0)) == 0:
            return DataBatch(
                ref=ref,
                frame=DataIO.empty_frame(ref.timeframe, decode=decode),
                start=dt_start,
                end=dt_end,
                row_count=0,
                tick_size=tick_size,
                decoded=decode,
            )

        frame = DataIO.read_partitions(
            isolated_paths,
            start=dt_start,
            end=dt_end,
            decode=decode,
            tick_size=tick_size,
            timeframe=row.get("timeframe", "M1"),
        )

        if context is not None and hasattr(context, "raise_if_cancelled"):
            context.raise_if_cancelled()

        if needs_resampling:
            frame = DataIO.resample_bars(
                frame, target_timeframe=ref.timeframe, source_timeframe="M1"
            )
            if dt_start is not None and not frame.is_empty():
                frame = frame.filter(pl.col("DateTime") >= dt_start)
            if dt_end is not None and not frame.is_empty():
                frame = frame.filter(pl.col("DateTime") <= dt_end)

        if count is not None and count >= 0:
            frame = frame.tail(count)

        batch_start = (
            cast("datetime | None", frame["DateTime"].min())
            if not frame.is_empty()
            else dt_start
        )
        batch_end = (
            cast("datetime | None", frame["DateTime"].max())
            if not frame.is_empty()
            else dt_end
        )

        return DataBatch(
            ref=ref,
            frame=frame,
            start=batch_start,
            end=batch_end,
            row_count=len(frame),
            tick_size=tick_size,
            decoded=decode,
        )
