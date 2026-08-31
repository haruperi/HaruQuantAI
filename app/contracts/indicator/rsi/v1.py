"""RSI v1 capability contract specification.

Traces to: P3-T03, Gate G3
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.contracts.indicator.common.v1 import (
        IndicatorConfigV1,
        IndicatorResultV1,
        MarketDatasetV1,
    )

CAPABILITY_ID = "indicator.rsi.v1"


class RsiFunctionV1(Protocol):
    """Protocol for callable RSI calculation functions."""

    def __call__(
        self,
        data: MarketDatasetV1,
        *,
        period: int,
        source: str = "close",
        config: IndicatorConfigV1 | None = None,
    ) -> IndicatorResultV1:
        """Calculate Wilder Relative Strength Index over market dataset.

        Args:
            data: One normalized market dataset.
            period: Smoothing period.
            source: Price source column name.
            config: Optional explicit configuration.

        Returns:
            Calculated indicator result.
        """
        ...


@dataclass(frozen=True, slots=True)
class RsiCapabilityV1:
    """Capability container holding the callable RSI implementation."""

    calculate: RsiFunctionV1


__all__ = (
    "CAPABILITY_ID",
    "RsiCapabilityV1",
    "RsiFunctionV1",
)
