"""Williams percent-R calculator compatibility façade."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from app.composition.facade import lease_capability
from app.kernel.identifiers import CapabilityId

if TYPE_CHECKING:
    from app.capabilities.indicator.williams_r.v1 import WilliamsRCapabilityV1
    from app.services.indicators.core.contracts import (
        IndicatorConfig,
    )
    from app.services.indicators.core.contracts import (
        _MarketDataset as MarketDataset,
    )
    from app.services.indicators.core.results import IndicatorResult

_WILLIAMS_R_CAPABILITY_ID = CapabilityId.parse("indicator.williams_r.v1")


def williams_r(
    data: MarketDataset,
    *,
    period: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate Williams %R over the inclusive OHLC window.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required rolling period of at least two.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Williams %R ``IndicatorResult``.

    Raises:
        IndicatorError: On validation, a zero price range, or atomic
            calculation failure.
        CapabilityUnavailableError: If Williams %R capability is
            unavailable in active runtime.
    """
    lease = lease_capability(_WILLIAMS_R_CAPABILITY_ID)
    cap = cast("WilliamsRCapabilityV1", lease.instance)
    return cast(
        "IndicatorResult",
        cap.calculate(
            cast("Any", data),
            period=period,
            config=cast("Any", config),
        ),
    )


__all__ = ["williams_r"]
