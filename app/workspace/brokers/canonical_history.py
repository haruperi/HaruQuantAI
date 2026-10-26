"""Shared canonical catalog reader and bounded provider interval traversal."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import polars as pl

from app.host.persistence import HostPersistence
from app.include.contracts import BridgeError
from app.include.market_storage import scan_catalog


def cached_frame(
    gateway: HostPersistence,
    root: Path | None,
    source: str,
    symbol: str,
    timeframe: str,
    start: datetime | None,
    end: datetime | None,
    count: int | None,
) -> pd.DataFrame | None:
    """Read only a registered active snapshot, decoding canonical prices once."""
    response = gateway.read_records(
        "datamgr_datasets", filters={"id": f"{source}:{symbol}:{timeframe}"}, limit=1
    )
    if not response["success"] or not response["data"]["records"]:
        return None
    row = response["data"]["records"][0]
    if not row["bars"] or (
        root is not None
        and not Path(row["path"]).resolve().is_relative_to(root.resolve())
    ):
        return None
    if start and start < _utc_bound(row["date_from"]):
        return None
    if end and end > _utc_bound(row["date_to"]):
        return None
    lazy = scan_catalog(row, decode=True)
    if start:
        lazy = lazy.filter(pl.col("DateTime") >= start)
    if end:
        lazy = lazy.filter(pl.col("DateTime") <= end)
    lazy = lazy.sort("DateTime")
    if count is not None:
        lazy = lazy.tail(count)
    return lazy.collect().to_pandas().set_index("DateTime")


def fetch_interval(
    client: Any,
    symbol: str,
    timeframe: str,
    start: datetime | None,
    end: datetime | None,
    count: int | None,
    digits: int,
) -> list[dict[str, Any]]:
    """Traverse every hour/day in a bounded range; only genuine no-data is skipped."""
    stop = end or datetime.now(UTC)
    begin = start or stop - timedelta(days=1)
    cursor = (
        begin.replace(minute=0, second=0, microsecond=0)
        if timeframe == "TICK"
        else begin.replace(hour=0, minute=0, second=0, microsecond=0)
    )
    step = timedelta(hours=1) if timeframe == "TICK" else timedelta(days=1)
    rows: list[dict[str, Any]] = []
    fetch = (
        client._fetch_datafeed_ticks
        if timeframe == "TICK"
        else client._fetch_datafeed_bars
    )
    while cursor <= stop:
        if client.context is not None:
            client.context.wait_if_paused()
        try:
            rows.extend(fetch(sym_clean=symbol, dt=cursor, decimals=digits, count=None))
        except BridgeError as error:
            if error.code != "NO_DATA":
                raise
        cursor += step
    key, multiplier = ("time_msc", 1000) if timeframe == "TICK" else ("time", 1)
    rows = [
        row
        for row in rows
        if begin.timestamp() * multiplier <= row[key] <= stop.timestamp() * multiplier
    ]
    rows.sort(key=lambda row: row[key])
    return rows[-count:] if count is not None else rows


def _utc_bound(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return (
        parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    )
