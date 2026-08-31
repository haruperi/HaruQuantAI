"""Provider-neutral structural protocols for indicator capability specifications.

Traces to: P3-T02, Gate G3
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class OHLCVRecordV1(Protocol):
    """Protocol for single-bar price records."""

    @property
    def timestamp(self) -> datetime:
        """UTC bar start timestamp."""
        ...

    @property
    def open(self) -> Decimal | float:
        """Bar open price."""
        ...

    @property
    def high(self) -> Decimal | float:
        """Bar high price."""
        ...

    @property
    def low(self) -> Decimal | float:
        """Bar low price."""
        ...

    @property
    def close(self) -> Decimal | float:
        """Bar close price."""
        ...

    @property
    def volume(self) -> Decimal | float:
        """Bar traded volume."""
        ...

    @property
    def available_at(self) -> datetime:
        """UTC timestamp when bar became available for processing."""
        ...


@runtime_checkable
class MarketDatasetV1(Protocol):
    """Protocol for market price dataset inputs."""

    @property
    def symbol(self) -> str:
        """Market instrument symbol."""
        ...

    @property
    def timeframe(self) -> str:
        """Market bar timeframe string."""
        ...

    @property
    def records(self) -> Sequence[OHLCVRecordV1]:
        """Ordered sequence of OHLCV bar records."""
        ...


@runtime_checkable
class IndicatorConfigV1(Protocol):
    """Protocol for indicator calculation parameters."""

    @property
    def indicator_id(self) -> str:
        """Identifier of the indicator."""
        ...

    @property
    def parameters(self) -> tuple[tuple[str, Any], ...]:
        """Key-value tuple of calculation parameters."""
        ...

    @property
    def source(self) -> str:
        """Selected input price source column."""
        ...

    @property
    def formula_version(self) -> str:
        """Mathematical formula version."""
        ...

    @property
    def output_mode(self) -> str:
        """Output delivery mode string."""
        ...

    @property
    def column_conflict_policy(self) -> str:
        """Policy for column name collisions."""
        ...


@runtime_checkable
class IndicatorResultV1(Protocol):
    """Protocol for calculation result objects."""

    @property
    def data(self) -> MarketDatasetV1:
        """Original input dataset."""
        ...

    @property
    def config(self) -> IndicatorConfigV1:
        """Configuration used during calculation."""
        ...

    @property
    def indicator_version(self) -> str:
        """Version string of the calculating indicator."""
        ...

    @property
    def output_columns(self) -> tuple[str, ...]:
        """Names of generated output columns."""
        ...

    @property
    def output_values(self) -> pd.DataFrame:
        """Calculated indicator series DataFrame."""
        ...

    @property
    def available_at(self) -> pd.Series:
        """Timestamp series when each value became available."""
        ...

    @property
    def computed_from_start(self) -> pd.Series:
        """Timestamp series for starting calculation bar."""
        ...

    @property
    def computed_from_end(self) -> pd.Series:
        """Timestamp series for ending calculation bar."""
        ...

    @property
    def unavailable_reason(self) -> pd.Series:
        """Reason series for uncomputed or warmup rows."""
        ...


__all__ = (
    "IndicatorConfigV1",
    "IndicatorResultV1",
    "MarketDatasetV1",
    "OHLCVRecordV1",
)
