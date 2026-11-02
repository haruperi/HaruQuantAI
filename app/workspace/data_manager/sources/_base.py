"""Authoritative registration and bounded historical source retrieval.

Description:
    Register historical datasets, fetch bounded broker observations and publish through
    host-owned storage. Preserve provider no-data diagnostics when all chunks are empty.
Purpose:
    FEAT-DATA-MANAGER-HISTORICAL-SOURCES: authoritative historical source operations.
Key Capabilities:
    - FR-DATA-SOURCES-EMPTY-RANGE: retain provider diagnostics without publishing empty
      history. Logging: WARNING records the symbol and requested range on empty jobs;
      regression tests verify this log explicitly.
Python API Usage:
    Sources(gateway).download(dataset_id, date_from, date_to)
CLI Usage:
    uv run pytest tests/workspace/data_manager/test_sources.py --no-cov
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast, override

import pandas as pd  # type: ignore[import-untyped]

from app.core.data.contracts import BridgeError
from app.core.data.market_storage import (
    price_columns,
    provider_storage_name,
    safe_component,
)
from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from app.workspace.data_manager.data.coverage import (
    missing_ranges,
    record_checked_ranges,
)
from app.workspace.data_manager.data.storage import (
    dataset_root,
    publish_frame,
    require_data,
)

from ._helpers import (
    _CONTROL_LIMIT,
    _MAX_DATASETS,
    _MAX_SYMBOL,
    CRYPTO,
    PROVIDERS,
    Checkpoints,
    _report_progress,
    capabilities,
    intervals,
    make_client,
    provider_id,
    resolve_result,
)
from .dukascopy import Dukascopy

__all__ = ["BaseSource", "Sources"]
logger = get_logger(__name__)


def _fetch_frame(
    client: Any, row: dict[str, Any], start: datetime, stop: datetime
) -> pd.DataFrame:
    try:
        value = (
            client.get_ticks(
                row["underlying"], date_from=start, date_to=stop, count=None
            )
            if row["timeframe"] == "TICK"
            else client.get_bars(
                row["underlying"],
                row["timeframe"],
                date_from=start,
                date_to=stop,
                count=None,
                limit=1000,
            )
        )
        frame = resolve_result(value, client)
    except BridgeError as error:
        if error.code != "NO_DATA":
            raise
        frame = pd.DataFrame()
        frame.attrs["provider_no_data"] = str(error)
        return frame
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("Provider did not return a market DataFrame")
    return frame


def _empty_range_error(
    row: dict[str, Any], lower: datetime, upper: datetime, details: list[str]
) -> ValueError:
    """Build and log a bounded diagnostic for a wholly empty request."""
    message = (
        f"No historical observations for '{row['symbol']}' "
        f"({row['source']}, {row['timeframe']}) from {lower.isoformat()} to "
        f"{upper.isoformat()}."
    )
    if details:
        message += " Provider details: " + " | ".join(details)
    logger.warning("FR-DATA-SOURCES-EMPTY-RANGE: %s", message)
    return ValueError(message)


class BaseSource:
    """Base implementation providing registration, bounding, and Parquet storage."""

    source_id: str = ""
    default_category: str = "Stocks"

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        market_root: Path | None = None,
        client_factory: Any = None,
    ) -> None:
        self.gateway = gateway if gateway is not None else HostPersistence()
        self.market_root = Path(market_root) if market_root else Path("data/market")
        self.client_factory = client_factory or make_client
        self.connection: dict[str, Any] | None = None

    def _get_client(self, source: str) -> Any:
        return (
            self.client_factory(source, self.connection)
            if self.connection
            else self.client_factory(source)
        )

    def record(self, dataset_id: str) -> dict[str, Any]:
        """Resolve a persisted identity instead of trusting browser target metadata."""
        rows = require_data(
            self.gateway.read_records(
                "datamgr_datasets", filters={"id": dataset_id}, limit=1
            )
        )["records"]
        if not rows or rows[0]["source"] not in (*PROVIDERS, "dukascopy"):
            raise ValueError("Choose a registered historical dataset")
        return cast("dict[str, Any]", rows[0])

    def add(
        self,
        provider_or_definitions: str | list[dict[str, Any]],
        definitions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Atomically register a batch without inventing data or record counts."""
        if isinstance(provider_or_definitions, str):
            source = provider_id(provider_or_definitions)
            defs = definitions or []
        else:
            source = self.source_id or "yahoo"
            defs = provider_or_definitions

        if not isinstance(defs, list) or not defs or len(defs) > _MAX_DATASETS:
            raise ValueError("Register between one and 1,000 datasets")
        require_data(self.gateway.ensure_datasets_schema())
        rows = [self._definition(source, definition) for definition in defs]
        if len({row["id"] for row in rows}) != len(rows):
            raise ValueError("Duplicate dataset in registration")
        with self.gateway.transaction() as tx:
            for row in rows:
                existing = require_data(
                    tx.read_records(
                        "datamgr_datasets", filters={"id": row["id"]}, limit=1
                    )
                )["records"]
                if existing:
                    raise ValueError(
                        f"Dataset already exists: {row['symbol']} {row['timeframe']}"
                    )
                require_data(tx.create_records("datamgr_datasets", row))
        return {"success": True, "data": {"records": rows}}

    def _definition(self, source: str, definition: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(definition, dict):
            raise TypeError("A dataset definition must be an object")
        symbol = safe_component(str(definition.get("symbol", "")).strip().upper())
        underlying = str(definition.get("underlying") or symbol).strip()
        if (
            not underlying
            or len(underlying) > _MAX_SYMBOL
            or any(ord(c) < _CONTROL_LIMIT for c in underlying)
        ):
            raise ValueError("Invalid provider symbol")
        timeframe = str(
            definition.get("timeframe") or capabilities(source)["default_timeframe"]
        ).upper()
        if timeframe not in capabilities(source)["timeframes"]:
            raise ValueError(f"{source} does not supply {timeframe} historical data")
        raw_step = definition.get("tick_size", 0.00000001)
        if isinstance(raw_step, bool):
            raise TypeError("Price unit must be a positive number")
        step = float(raw_step)
        if not math.isfinite(step) or step <= 0:
            raise ValueError("Price unit must be finite and positive")
        now = datetime.now(UTC).isoformat()
        category = str(
            definition.get("category")
            or (
                "Crypto"
                if source in CRYPTO
                else "Forex"
                if source in ("darwinex", "mt5")
                else "Stocks"
                if source != "sq_futures"
                else "Futures"
            )
        )
        return {
            "id": f"{source}:{symbol}:{timeframe}",
            "source": source,
            "symbol": symbol,
            "underlying": underlying,
            "timeframe": timeframe,
            "broker": str(definition.get("broker") or "SQ default"),
            "timezone": "UTC",
            "category": category,
            "date_from": "",
            "date_to": "",
            "bars": 0,
            "path": str(
                dataset_root(
                    self.market_root / provider_storage_name(source), symbol, timeframe
                )
            ),
            "data_kind": "ticks" if timeframe == "TICK" else "bars",
            "created_at": now,
            "updated_at": now,
            "schema_version": 2,
            "lineage_json": json.dumps(
                {
                    "tick_size": step,
                    "partitions": [],
                    "price_policy": "round-half-even-to-storage-unit",
                    "provider": source,
                    "connection_id": definition.get("connection_id"),
                }
            ),
        }

    def download(
        self,
        dataset_id: str,
        date_from: Any,
        date_to: Any,
        *,
        overwrite: bool = False,
        context: Any = None,
    ) -> dict[str, Any]:
        """Fetch complete bounded intervals and commit each independently."""
        row = self.record(dataset_id)
        lower = Dukascopy.parse_date_bound(date_from)
        upper = Dukascopy.parse_date_bound(date_to, is_end=True)
        if (
            lower is None
            or upper is None
            or lower > upper
            or not isinstance(overwrite, bool)
        ):
            raise ValueError("Choose a valid date range and overwrite option")
        source, timeframe = row["source"], row["timeframe"]
        if source == "dukascopy":
            result = Dukascopy(self.gateway).download(
                row["symbol"],
                timeframe=timeframe,
                underlying=row["underlying"],
                date_from=lower,
                date_to=upper,
                overwrite=overwrite,
                context=context,
            )
            require_data(result)
            return result
        missing = missing_ranges(row, lower, upper, overwrite=overwrite)
        if not missing:
            _report_progress(context, 100, "Requested history is already downloaded")
            return {
                "success": True,
                "data": {
                    "dataset_id": dataset_id,
                    "received_rows": 0,
                    "published_intervals": 0,
                    "already_downloaded": True,
                    "record": self.record(dataset_id),
                },
            }
        chunks = [
            interval
            for start, stop in missing
            for interval in intervals(source, timeframe, start, stop)
        ]
        client = self._get_client(source)
        published, received = 0, 0
        empty = []
        no_data_details: list[str] = []
        try:
            for index, (start, stop) in enumerate(chunks):
                if context is not None:
                    context.wait_if_paused()
                    context.raise_if_cancelled()
                frame = _fetch_frame(client, row, start, stop)
                detail = frame.attrs.get("provider_no_data")
                if isinstance(detail, str) and detail not in no_data_details:
                    no_data_details = [*no_data_details, detail][-2:]
                count = self._publish(
                    row, frame, start, stop, overwrite=overwrite, context=context
                )
                published += bool(count)
                received += count
                if not count:
                    empty.append((start, stop))
                _report_progress(
                    context,
                    100 * (index + 1) / len(chunks),
                    f"{row['symbol']}: {stop.isoformat()}",
                )
        finally:
            if source != "mt5":
                client.disconnect()
        if not published and missing == [(lower, upper)]:
            raise _empty_range_error(row, lower, upper, no_data_details)
        record_checked_ranges(self.gateway, dataset_id, empty)
        return {
            "success": True,
            "data": {
                "dataset_id": dataset_id,
                "received_rows": received,
                "published_intervals": published,
                "record": self.record(dataset_id),
            },
        }

    def _publish(
        self,
        row: dict[str, Any],
        frame: pd.DataFrame,
        start: datetime,
        stop: datetime,
        *,
        overwrite: bool,
        context: Any,
    ) -> int:
        if frame.empty:
            return 0
        frame = frame.copy()
        if "DateTime" in frame:
            frame = frame.set_index("DateTime")
        frame.index = pd.to_datetime(frame.index, utc=True)
        frame = frame.loc[(frame.index >= start) & (frame.index <= stop)]
        if frame.empty:
            return 0
        step = json.loads(row["lineage_json"])["tick_size"]
        digits = max(0, -int(Decimal(str(step)).as_tuple().exponent))
        for column in price_columns(row["timeframe"]):
            frame[column] = ((frame[column] / step).round() * step).round(digits)
        publish_frame(
            self.gateway,
            self.market_root / provider_storage_name(row["source"]),
            row,
            frame,
            step,
            overwrite=overwrite,
            date_from=start,
            date_to=stop,
            context=Checkpoints(context) if context is not None else None,
            coverage=(start, stop),
        )
        return len(frame)


class Sources(BaseSource):
    """Unified facade for registrations and downloads across historical sources."""

    @override
    def add(
        self,
        provider_or_definitions: str | list[dict[str, Any]],
        definitions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Atomically register a batch for any supported provider."""
        if isinstance(provider_or_definitions, str):
            provider = provider_id(provider_or_definitions)
            defs = definitions or []
        else:
            provider = "yahoo"
            defs = provider_or_definitions
        return super().add(provider, defs)
