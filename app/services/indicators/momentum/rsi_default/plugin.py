"""Factory plugin for indicator.rsi.default provider."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

from app.contracts.indicator.rsi.v1 import RsiCapabilityV1, RsiFunctionV1
from app.services.indicators.momentum.rsi_default.implementation import rsi

if TYPE_CHECKING:
    from app.kernel.effects import EffectScope
    from app.kernel.identifiers import CapabilityId

__all__: tuple[str, ...] = ("create_provider",)


def create_provider(
    *,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> RsiCapabilityV1:
    """Create and return the RSI capability provider implementation.

    Args:
        dependencies: Injected capability dependencies (must be empty).
        config: Provider configuration mapping (must be empty).
        scope: Target execution lifecycle scope.

    Returns:
        RsiCapabilityV1: The capability record wrapping the RSI calculation function.

    Raises:
        ValueError: If dependencies or config mappings are non-empty.
    """
    _ = scope
    if dependencies or config:
        raise ValueError("RSI provider accepts no dependencies or config")
    return RsiCapabilityV1(calculate=cast("RsiFunctionV1", rsi))
