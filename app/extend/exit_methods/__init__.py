"""StrategyQuant-compatible exit methods package.

Description:
    Exposes all 5 concrete StrategyQuant ExitMethod implementations:
    ExitAfterBars, MoveSL2BE, ProfitTarget, StopLoss, and TrailingStop,
    along with base contracts, enumerations, and catalog registry.

Purpose:
    FEAT-EXIT-METHODS: StrategyQuant donor-faithful exit methods.

Key Capabilities:
    - FR-exit-methods-exports: Canonical exit method exports and registry interface.

Python API Usage:
    from app.extend.exit_methods import (
        ExitAfterBars,
        MoveSL2BE,
        ProfitTarget,
        StopLoss,
        TrailingStop,
    )

CLI Usage:
    python -c "import app.extend.exit_methods; print(dir(app.extend.exit_methods))"
"""

from __future__ import annotations

from app.extend.exit_methods.base import ExitMethod, ExitType, correct_sl_pt
from app.extend.exit_methods.catalogue import (
    EXIT_METHODS_CATALOGUE,
    ExitMethodDescriptor,
    create_exit_method,
    get_exit_method_descriptor,
    list_exit_methods,
)
from app.extend.exit_methods.exit_after_bars import ExitAfterBars
from app.extend.exit_methods.move_sl_2_be import MoveSL2BE
from app.extend.exit_methods.profit_target import ProfitTarget
from app.extend.exit_methods.stop_loss import StopLoss
from app.extend.exit_methods.trailing_stop import TrailingStop

__all__ = [
    "EXIT_METHODS_CATALOGUE",
    "ExitAfterBars",
    "ExitMethod",
    "ExitMethodDescriptor",
    "ExitType",
    "MoveSL2BE",
    "ProfitTarget",
    "StopLoss",
    "TrailingStop",
    "correct_sl_pt",
    "create_exit_method",
    "get_exit_method_descriptor",
    "list_exit_methods",
]
