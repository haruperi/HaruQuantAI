"""Factory plugin for indicator.williams_r.default provider."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

from app.capabilities.indicator.williams_r.v1 import (
    WilliamsRCapabilityV1,
    WilliamsRFunctionV1,
)
from app.services.indicators.momentum.williams_r_default.implementation import (
    williams_r,
)

if TYPE_CHECKING:
    from app.kernel.effects import EffectScope
    from app.kernel.identifiers import CapabilityId

__all__: tuple[str, ...] = ("create_provider",)


def create_provider(
    *,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> WilliamsRCapabilityV1:
    """Create and return the Williams %R capability provider implementation.

    Args:
        dependencies: Injected capability dependencies (must be empty).
        config: Provider configuration mapping (must be empty).
        scope: Target execution lifecycle scope.

    Returns:
        WilliamsRCapabilityV1: The capability record wrapping Williams %R.

    Raises:
        ValueError: If dependencies or config mappings are non-empty.
    """
    _ = scope
    if dependencies or config:
        raise ValueError("Williams R provider accepts no dependencies or config")
    return WilliamsRCapabilityV1(calculate=cast("WilliamsRFunctionV1", williams_r))
