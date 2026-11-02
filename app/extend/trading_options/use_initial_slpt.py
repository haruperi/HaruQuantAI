"""Use initial SLPT trading option snippet (TradingOptions cohort).

Description:
    Implements UseInitialSLPT snippet matching StrategyQuant donor
    SQ/TradingOptions/UseInitialSLPT.java.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: UseInitialSLPT trading option.

Key Capabilities:
    - FR-trading-option-use-initial-slpt: Control initial bracket attachment.

Python API Usage:
    from app.extend.trading_options.use_initial_slpt import UseInitialSLPT

    opt = UseInitialSLPT(use_initial_sl_pt=True)
    attach = opt.should_attach_initial_brackets()

CLI Usage:
    python -m app.cli extend trading-options --option UseInitialSLPT
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.extend.trading_options.base import BaseTradingOption

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class UseInitialSLPT(BaseTradingOption):
    """Enforce initial stop-loss and profit-target placement on order submission."""

    use_initial_sl_pt: bool = True
    name: str = "UseInitialSLPT"
    category: str = "TradingOptions"

    def should_attach_initial_brackets(self) -> bool:
        """Return whether SL/PT brackets are submitted with the initial entry order."""
        logger.debug(
            "FR-trading-option-use-initial-slpt: UseInitialSLPT=%s",
            self.use_initial_sl_pt,
        )
        return self.use_initial_sl_pt


__all__ = ["UseInitialSLPT"]
