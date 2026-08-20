"""Williams %R v1 capability contract specification.

Traces to: P3-T04, Gate G3
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.capabilities.indicator.common.v1 import (
        IndicatorConfigV1,
        IndicatorResultV1,
        MarketDatasetV1,
    )

CAPABILITY_ID = "indicator.williams_r.v1"


class WilliamsRFunctionV1(Protocol):
    """Protocol for callable Williams %R calculation functions."""

    def __call__(
        self,
        data: MarketDatasetV1,
        *,
        period: int,
        config: IndicatorConfigV1 | None = None,
    ) -> IndicatorResultV1:
        """Calculate Williams %R over market dataset.

        Args:
            data: One normalized market dataset.
            period: Smoothing period.
            config: Optional explicit configuration.

        Returns:
            Calculated indicator result.
        """
        ...


@dataclass(frozen=True, slots=True)
class WilliamsRCapabilityV1:
    """Capability container holding the callable Williams %R implementation."""

    calculate: WilliamsRFunctionV1


__all__ = (
    "CAPABILITY_ID",
    "WilliamsRCapabilityV1",
    "WilliamsRFunctionV1",
)
