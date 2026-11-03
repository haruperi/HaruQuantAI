"""Market regime indicator package exports and lazy loading registry."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.regime.chop_zone import ChopZone
    from app.extend.blocks.indicators.regime.choppiness import ChoppinessIndex
    from app.extend.blocks.indicators.regime.hurst import HurstExponent
    from app.extend.blocks.indicators.regime.majority_rule import MajorityRule
    from app.extend.blocks.indicators.regime.regime_resolver import (
        MarketRegimeResolver,
    )

_EXPORTS = {
    "ChopZone": "app.extend.blocks.indicators.regime.chop_zone",
    "ChoppinessIndex": "app.extend.blocks.indicators.regime.choppiness",
    "HurstExponent": "app.extend.blocks.indicators.regime.hurst",
    "MajorityRule": "app.extend.blocks.indicators.regime.majority_rule",
    "MarketRegimeResolver": "app.extend.blocks.indicators.regime.regime_resolver",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = [
    "ChopZone",
    "ChoppinessIndex",
    "HurstExponent",
    "MajorityRule",
    "MarketRegimeResolver",
]
