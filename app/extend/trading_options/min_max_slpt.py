"""Min Max SLPT trading option snippet (TradingOptions cohort).

Description:
    Implements MinMaxSLPT snippet matching StrategyQuant donor
    SQ/TradingOptions/MinMaxSLPT.java.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: MinMaxSLPT trading option.

Key Capabilities:
    - FR-trading-option-min-max-slpt: Clamp stop-loss and profit-target pip distances.

Python API Usage:
    from app.extend.trading_options.min_max_slpt import MinMaxSLPT

    opt = MinMaxSLPT(min_sl=10.0, max_sl=200.0, min_pt=10.0, max_pt=300.0)
    sl = opt.clamp_sl_pips(5.0)

CLI Usage:
    python -m app.cli extend trading-options --option MinMaxSLPT
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.extend.trading_options.base import BaseTradingOption

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MinMaxSLPT(BaseTradingOption):
    """Clamp stop-loss and profit-target pip distances to [min, max] bounds."""

    min_sl: float = 10.0
    max_sl: float = 200.0
    min_pt: float = 10.0
    max_pt: float = 300.0
    name: str = "MinMaxSLPT"
    category: str = "TradingOptions"

    def clamp_sl_pips(self, sl_pips: float) -> float:
        """Clamp stop-loss distance in pips to [min_sl, max_sl]."""
        if sl_pips <= 0.0:
            return 0.0
        val = max(sl_pips, self.min_sl) if self.min_sl > 0.0 else sl_pips
        if self.max_sl > 0.0:
            val = min(val, self.max_sl)
        logger.debug("FR-trading-option-min-max-slpt: MinMaxSLPT.sl=%f", val)
        return val

    def clamp_pt_pips(self, pt_pips: float) -> float:
        """Clamp profit-target distance in pips to [min_pt, max_pt]."""
        if pt_pips <= 0.0:
            return 0.0
        val = max(pt_pips, self.min_pt) if self.min_pt > 0.0 else pt_pips
        if self.max_pt > 0.0:
            val = min(val, self.max_pt)
        logger.debug("FR-trading-option-min-max-slpt: MinMaxSLPT.pt=%f", val)
        return val


__all__ = ["MinMaxSLPT"]
