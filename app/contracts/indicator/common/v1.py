"""Indicator common capability v1 contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class IndicatorConfigV1:
    """Standard indicator configuration."""

    period: int
    source: str = "close"


@dataclass(frozen=True, slots=True)
class IndicatorResultV1:
    """Standard indicator output."""

    values: tuple[float | None, ...]
    is_valid: bool = True


class OHLCVRecordV1(Protocol):
    """OHLCV record interface."""

    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketDatasetV1(Protocol):
    """Market dataset interface."""

    symbol: str
    timeframe: str
    records: tuple[OHLCVRecordV1, ...]


__all__ = (
    "IndicatorConfigV1",
    "IndicatorResultV1",
    "MarketDatasetV1",
    "OHLCVRecordV1",
)
