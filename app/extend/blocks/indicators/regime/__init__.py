"""Indicator package module: regime/__init__.py.

Description:
    Market regime indicator package exports and lazy loading registry.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative indicator library.
Key Capabilities:
    - FR-indicator-regime: Regime indicator exports.
Python API Usage:
    from app.extend.blocks.indicators import *
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.regime.choppiness import ChoppinessIndex
    from app.extend.blocks.indicators.regime.hurst import HurstExponent
    from app.extend.blocks.indicators.regime.regime_resolver import (
        MarketRegimeResolver,
    )

_EXPORTS = {
    "ChoppinessIndex": "app.extend.blocks.indicators.regime.choppiness",
    "HurstExponent": "app.extend.blocks.indicators.regime.hurst",
    "MarketRegimeResolver": "app.extend.blocks.indicators.regime.regime_resolver",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = ["ChoppinessIndex", "HurstExponent", "MarketRegimeResolver"]
