"""Relative Strength Index calculator compatibility façade."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from app.composition.facade import lease_capability
from app.kernel.identifiers import CapabilityId

if TYPE_CHECKING:
    from app.contracts.indicator.rsi.v1 import RsiCapabilityV1
    from app.services.indicators.core.contracts import (
        IndicatorConfig,
    )
    from app.services.indicators.core.contracts import (
        _MarketDataset as MarketDataset,
    )
    from app.services.indicators.core.results import IndicatorResult

_RSI_CAPABILITY_ID = CapabilityId.parse("indicator.rsi.v1")


def rsi(
    data: MarketDataset,
    *,
    period: int,
    source: str = "close",
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate Wilder Relative Strength Index.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required smoothing period of at least two.
        source: Selected OHLC source.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic RSI ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
        CapabilityUnavailableError: If RSI capability is unavailable in active runtime.
    """
    lease = lease_capability(_RSI_CAPABILITY_ID)
    cap = cast("RsiCapabilityV1", lease.instance)
    return cast(
        "IndicatorResult",
        cap.calculate(
            cast("Any", data),
            period=period,
            source=source,
            config=cast("Any", config),
        ),
    )


__all__ = ["rsi"]
