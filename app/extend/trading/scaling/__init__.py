"""Position scaling methods package conforming to StrategyQuant SQ.Trading.Scaling.

Description:
    Exposes concrete StrategyQuant position scaling snippets (NoScaling)
    alongside the ScalingMethod base contract and ScalingMethodsList singleton
    registry.

Purpose:
    FEAT-TRADING-SCALING: Canonical exports for SQ Trading Scaling.

Key Capabilities:
    - FR-TRADING-SCALING-EXPORTS: Unified exports of all position scaling methods.

Python API Usage:
    from app.extend.trading.scaling import ScalingMethod, ScalingMethodsList, NoScaling

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py --no-cov
"""

from app.extend.trading.scaling.base import (
    ScalingMethod,
    ScalingMethodsList,
)
from app.extend.trading.scaling.no_scaling import (
    NoScaling,
)

__all__ = [
    "NoScaling",
    "ScalingMethod",
    "ScalingMethodsList",
]
