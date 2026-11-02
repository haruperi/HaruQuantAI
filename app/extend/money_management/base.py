"""Contract for custom position sizing and money management snippets.

Description:
    Defines the BasePositionSizer abstract contract for StrategyQuant-compatible
    money management and position sizing calculation snippets.
Purpose:
    FEAT-MONEY-MANAGEMENT: Provide the MoneyManagement base contract.
Key Capabilities:
    - FR-MM-SIZER-CONTRACT: Declare abstract compute_size method for lot sizing.
Python API Usage:
    from app.extend.money_management.base import BasePositionSizer
CLI Usage:
    uv run pytest tests/workspace/code_editor/test_extension_cohorts.py --no-cov
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BasePositionSizer(ABC):
    """Contract for custom trade volume calculation."""

    name: str = "BasePositionSizer"
    category: str = "MoneyManagement"

    @abstractmethod
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Calculate lots from account equity and stop distance."""


__all__ = ["BasePositionSizer"]
