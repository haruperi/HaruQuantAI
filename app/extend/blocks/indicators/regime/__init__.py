"""Market regime indicator package exports and lazy loading registry.

Description:
    Market regime indicator package exports and lazy loading registry.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative market regime indicator library.
Key Capabilities:
    - FR-indicator-regime: Regime indicator exports.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.regime import ChoppinessIndex, HurstExponent
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

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
