"""Canonical indicators, loaded individually on demand."""

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
