"""Contract for custom position sizing and money management blocks."""

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
