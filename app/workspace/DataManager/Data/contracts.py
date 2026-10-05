"""Immutable records shared by historical dataset requirements.

Description:
    Defines caller-owned metadata, UTC millisecond records and catalog invariants.
    Requirement modules receive these records and return explicit changes without
    storage, network access or hidden mutable state. Bad OHLC may be represented
    for quality analysis; non-finite values and decreasing timestamps may not.
Purpose:
    FEAT-DATASET-MANAGEMENT: Shared types for the Data workspace.
Key Capabilities:
    Support only: immutable records and reference validation for the registered
    dataset requirements. Constructors emit DEBUG validation events with feature
    and bounded counts; no independent behavioral FR is introduced.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import Catalog, Dataset

    catalog = Catalog((Dataset("fx", "EURUSD", "EURUSD"),))
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_contracts.py --no-cov
    ```
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.host.logging import get_logger

logger = get_logger(__name__).bind(feature="FEAT-DATASET-MANAGEMENT")

MIN_TIME_MS = -62_135_596_800_000
MAX_TIME_MS = 253_402_300_799_999


class BarConvention(StrEnum):
    """Meaning of a stored bar's timestamp."""

    START = "start"
    END = "end"


@dataclass(frozen=True, slots=True)
class TickRecord:
    """One quote at an integer UTC millisecond timestamp."""

    time_ms: int
    bid: float
    ask: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        """Validate immutable construction before exposing the record."""
        logger.debug("Validating tick record")
        if (
            type(self.time_ms) is not int
            or not MIN_TIME_MS <= self.time_ms <= MAX_TIME_MS
        ):
            raise ValueError(
                "Timestamp must be UTC milliseconds within datetime bounds."
            )
        if not all(isfinite(value) for value in (self.bid, self.ask, self.volume)):
            raise ValueError("Record values must be finite.")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative.")


@dataclass(frozen=True, slots=True)
class BarRecord:
    """One stored OHLC bar; finite bad OHLC remains inspectable."""

    time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        """Validate immutable construction before exposing the record."""
        logger.debug("Validating bar record")
        if (
            type(self.time_ms) is not int
            or not MIN_TIME_MS <= self.time_ms <= MAX_TIME_MS
        ):
            raise ValueError(
                "Timestamp must be UTC milliseconds within datetime bounds."
            )
        values = (self.open, self.high, self.low, self.close, self.volume)
        if not all(isfinite(value) for value in values):
            raise ValueError("Record values must be finite.")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative.")


type Record = TickRecord | BarRecord


@dataclass(frozen=True, slots=True)
class Dataset:
    """Metadata and a bounded immutable series supplied by the caller."""

    id: str
    symbol: str
    instrument: str
    timeframe: str = "M1"
    timezone: str = "UTC"
    bar_convention: BarConvention = BarConvention.START
    broker_id: str | None = None
    source_id: str | None = None
    asset_type: str = "forex"
    groups: tuple[str, ...] = ()
    visible: bool = True
    parent_id: str | None = None
    restricted: bool = False
    records: tuple[Record, ...] = ()

    def __post_init__(self) -> None:
        """Validate immutable construction before exposing the record."""
        logger.debug("Validating dataset", extra={"count": len(self.records)})
        if not self.id or not self.instrument:
            raise ValueError("Dataset ID and instrument are required.")
        if not re.fullmatch(r"[a-zA-Z0-9_@.:$]+", self.symbol):
            raise ValueError("Invalid dataset symbol.")
        if self.timeframe not in {
            "TICK",
            "M1",
            "M5",
            "M15",
            "M30",
            "H1",
            "H4",
            "D1",
            "W1",
            "MN1",
        }:
            raise ValueError("Unsupported stored timeframe.")
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Unsupported timezone.") from exc
        if not isinstance(self.bar_convention, BarConvention):
            raise TypeError("Invalid bar convention.")
        if type(self.visible) is not bool or type(self.restricted) is not bool:
            raise ValueError("Visibility and restrictions must be boolean.")
        if not isinstance(self.records, tuple) or not isinstance(self.groups, tuple):
            raise TypeError("Records and groups must be immutable tuples.")
        self._validate_records()
        if self.parent_id == self.id:
            raise ValueError("Dataset cannot be its own parent.")

    def _validate_records(self) -> None:
        record_type = TickRecord if self.timeframe == "TICK" else BarRecord
        if any(not isinstance(record, record_type) for record in self.records):
            raise ValueError("Record kind does not match stored timeframe.")
        if any(
            a.time_ms > b.time_ms
            for a, b in zip(self.records, self.records[1:], strict=False)
        ):
            raise ValueError("Records must be ordered by timestamp.")

    @property
    def row_count(self) -> int:
        """Derive the number of historical observations."""
        return len(self.records)

    @property
    def date_from_ms(self) -> int | None:
        """Derive the first timestamp; empty data has no coverage."""
        return self.records[0].time_ms if self.records else None

    @property
    def date_to_ms(self) -> int | None:
        """Derive the last timestamp; equal timestamps are retained."""
        return self.records[-1].time_ms if self.records else None


@dataclass(frozen=True, slots=True)
class Catalog:
    """Complete supplied catalog with unique identities and resolved parents."""

    datasets: tuple[Dataset, ...]

    def __post_init__(self) -> None:
        """Validate immutable construction before exposing the record."""
        logger.debug("Validating catalog", extra={"count": len(self.datasets)})
        if not isinstance(self.datasets, tuple):
            raise TypeError("Catalog must be an immutable tuple.")
        by_id = {item.id: item for item in self.datasets}
        if len(by_id) != len(self.datasets):
            raise ValueError("Dataset IDs must be unique.")
        if len({item.symbol for item in self.datasets}) != len(self.datasets):
            raise ValueError("Dataset symbols must be unique.")
        for item in self.datasets:
            if item.parent_id is not None:
                parent = by_id.get(item.parent_id)
                if parent is None or parent.parent_id is not None:
                    raise ValueError(
                        "Clone parent must resolve to an original dataset."
                    )
