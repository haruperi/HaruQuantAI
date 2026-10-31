"""Concrete donor-faithful MoneyManagement position sizer blocks.

Description:
    Implements all 12 StrategyQuant MoneyManagement snippet classes as typed
    BasePositionSizer subclasses: FixedSize, FixedAmount, RiskFixedPctOfAccount,
    RiskFixedBalancePct, ATRRiskBasedSizing, StocksSizeByPrice, CryptoFixedAmount,
    CryptoFixedBalancePct, CryptoSizeByPrice, PickerFixedAmount,
    PickerRiskFixedPctOfAccount, and SimpleMartingaleMM.
Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: Complete the 12-class MoneyManagement
    extension cohort under app/include/blocks/money_management.
Key Capabilities:
    - FR-mm-sizer-compute: Calculate lot/share/crypto position sizes with donor
      rounding, fallback LotsIfNoMM, maximum lot caps, and martingale state.
Python API Usage:
    from app.include.blocks.money_management.sizers import RiskFixedPctOfAccount
CLI Usage:
    uv run pytest tests/workspace/code_editor/test_extension_cohorts.py
"""

from __future__ import annotations

import logging
import math
from typing import override

from app.include.blocks.money_management.base import BasePositionSizer

logger = logging.getLogger(__name__)


def _round_down(value: float, decimals: int) -> float:
    """Truncate/floor positive lot size to the requested decimal places."""
    if not math.isfinite(value) or value <= 0.0:
        return 0.0
    factor = float(10 ** max(decimals, 0))
    return math.floor(value * factor + 1e-9) / factor


def _clamp_lots(
    computed: float,
    *,
    decimals: int,
    lots_if_no_mm: float,
    max_lots: float = 0.0,
    min_lots: float = 0.0,
) -> float:
    """Apply donor rounding, minimum fallback, and maximum lot cap."""
    rounded = _round_down(computed, decimals)
    if rounded <= min_lots:
        rounded = _round_down(max(lots_if_no_mm, 0.0), decimals)
    if max_lots > 0.0 and rounded > max_lots:
        rounded = _round_down(max_lots, decimals)
    return rounded


class FixedSize(BasePositionSizer):
    """Fixed order size money management block (FixedSize.java)."""

    name: str = "FixedSize"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(self, *, size: float = 0.1, decimals: int = 2) -> None:
        self.size = size
        self.decimals = decimals

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Return fixed position size rounded to configured decimals."""
        _ = (account_equity, stop_loss_pips, pip_value)
        result = _round_down(max(self.size, 0.0), self.decimals)
        logger.debug("FR-mm-sizer-compute: FixedSize=%f", result)
        return result


class FixedAmount(BasePositionSizer):
    """Risk fixed currency amount per trade (FixedAmount.java)."""

    name: str = "FixedAmount"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(
        self,
        *,
        risked_money: float = 100.0,
        decimals: int = 2,
        lots_if_no_mm: float = 0.1,
        max_lots: float = 5.0,
    ) -> None:
        self.risked_money = risked_money
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute lots risking a fixed currency amount over the stop distance."""
        _ = account_equity
        if stop_loss_pips <= 0.0 or pip_value <= 0.0 or self.risked_money <= 0.0:
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            raw = self.risked_money / (stop_loss_pips * pip_value)
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: FixedAmount=%f", result)
        return result


class RiskFixedPctOfAccount(BasePositionSizer):
    """Risk fixed percentage of account equity (RiskFixedPctOfAccount.java)."""

    name: str = "RiskFixedPctOfAccount"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(
        self,
        *,
        risk_in_pct: float = 5.0,
        decimals: int = 2,
        lots_if_no_mm: float = 1.0,
        max_lots: float = 100.0,
    ) -> None:
        self.risk_in_pct = risk_in_pct
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute lots risking risk_in_pct% of current account equity."""
        if (
            account_equity <= 0.0
            or stop_loss_pips <= 0.0
            or pip_value <= 0.0
            or self.risk_in_pct <= 0.0
        ):
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            dollar_risk = account_equity * (self.risk_in_pct / 100.0)
            raw = dollar_risk / (stop_loss_pips * pip_value)
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: RiskFixedPctOfAccount=%f", result)
        return result


class RiskFixedBalancePct(BasePositionSizer):
    """Risk fixed percentage of settled account balance (RiskFixedBalancePct.java)."""

    name: str = "RiskFixedBalancePct"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(
        self,
        *,
        risk_in_pct: float = 5.0,
        decimals: int = 2,
        lots_if_no_mm: float = 1.0,
        max_lots: float = 100.0,
        account_balance: float | None = None,
    ) -> None:
        self.risk_in_pct = risk_in_pct
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots
        self.account_balance = account_balance

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute lots risking risk_in_pct% of settled balance (or equity fallback)."""
        base_capital = (
            self.account_balance if self.account_balance is not None else account_equity
        )
        if (
            base_capital <= 0.0
            or stop_loss_pips <= 0.0
            or pip_value <= 0.0
            or self.risk_in_pct <= 0.0
        ):
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            dollar_risk = base_capital * (self.risk_in_pct / 100.0)
            raw = dollar_risk / (stop_loss_pips * pip_value)
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: RiskFixedBalancePct=%f", result)
        return result


class ATRRiskBasedSizing(BasePositionSizer):
    """ATR volatility risk-based position sizing (ATRRiskBasedSizing.java)."""

    name: str = "ATRRiskBasedSizing"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures", "Stocks")

    def __init__(
        self,
        *,
        risk_in_pct: float = 2.0,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        decimals: int = 2,
        lots_if_no_mm: float = 0.1,
        max_lots: float = 100.0,
    ) -> None:
        self.risk_in_pct = risk_in_pct
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute lots using ATR-scaled volatility distance (stop_loss_pips as ATR)."""
        effective_stop = stop_loss_pips * self.atr_multiplier
        if (
            account_equity <= 0.0
            or effective_stop <= 0.0
            or pip_value <= 0.0
            or self.risk_in_pct <= 0.0
        ):
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            dollar_risk = account_equity * (self.risk_in_pct / 100.0)
            raw = dollar_risk / (effective_stop * pip_value)
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: ATRRiskBasedSizing=%f", result)
        return result


class StocksSizeByPrice(BasePositionSizer):
    """Allocate capital by instrument share price (StocksSizeByPrice.java)."""

    name: str = "StocksSizeByPrice"
    supported_engines: tuple[str, ...] = ("Stocks", "Default")

    def __init__(
        self,
        *,
        use_account_balance: bool = True,
        capital_pct: float = 100.0,
        decimals: int = 0,
        lots_if_no_mm: float = 1.0,
        max_lots: float = 10000.0,
    ) -> None:
        self.use_account_balance = use_account_balance
        self.capital_pct = capital_pct
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute shares from capital allocation and price (passed via pip_value)."""
        _ = stop_loss_pips
        price = pip_value
        if account_equity <= 0.0 or price <= 0.0 or self.capital_pct <= 0.0:
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            allocated = account_equity * (self.capital_pct / 100.0)
            raw = allocated / price
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: StocksSizeByPrice=%f", result)
        return result


class CryptoFixedAmount(BasePositionSizer):
    """Crypto risk fixed currency amount per order (CryptoFixedAmount.java)."""

    name: str = "CryptoFixedAmount"
    supported_engines: tuple[str, ...] = ("Crypto",)

    def __init__(
        self,
        *,
        risked_money: float = 100.0,
        decimals: int = 4,
        lots_if_no_mm: float = 0.01,
        max_lots: float = 1000.0,
    ) -> None:
        self.risked_money = risked_money
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute crypto order quantity from fixed quote-currency risk."""
        _ = account_equity
        if stop_loss_pips <= 0.0 or pip_value <= 0.0 or self.risked_money <= 0.0:
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            raw = self.risked_money / (stop_loss_pips * pip_value)
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: CryptoFixedAmount=%f", result)
        return result


class CryptoFixedBalancePct(BasePositionSizer):
    """Crypto risk fixed percentage of account balance (CryptoFixedBalancePct.java)."""

    name: str = "CryptoFixedBalancePct"
    supported_engines: tuple[str, ...] = ("Crypto",)

    def __init__(
        self,
        *,
        risk_in_pct: float = 2.0,
        decimals: int = 4,
        lots_if_no_mm: float = 0.01,
        max_lots: float = 1000.0,
    ) -> None:
        self.risk_in_pct = risk_in_pct
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute crypto order quantity risking risk_in_pct% of balance."""
        if (
            account_equity <= 0.0
            or stop_loss_pips <= 0.0
            or pip_value <= 0.0
            or self.risk_in_pct <= 0.0
        ):
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            dollar_risk = account_equity * (self.risk_in_pct / 100.0)
            raw = dollar_risk / (stop_loss_pips * pip_value)
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: CryptoFixedBalancePct=%f", result)
        return result


class CryptoSizeByPrice(BasePositionSizer):
    """Crypto size by asset price and capital percentage (CryptoSizeByPrice.java)."""

    name: str = "CryptoSizeByPrice"
    supported_engines: tuple[str, ...] = ("Crypto",)

    def __init__(
        self,
        *,
        capital_pct: float = 10.0,
        decimals: int = 4,
        lots_if_no_mm: float = 0.01,
        max_lots: float = 1000.0,
    ) -> None:
        self.capital_pct = capital_pct
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute crypto units from capital allocation and asset price (pip_value)."""
        _ = stop_loss_pips
        asset_price = pip_value
        if account_equity <= 0.0 or asset_price <= 0.0 or self.capital_pct <= 0.0:
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            allocated = account_equity * (self.capital_pct / 100.0)
            raw = allocated / asset_price
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: CryptoSizeByPrice=%f", result)
        return result


class PickerFixedAmount(BasePositionSizer):
    """Stockpicker fixed cash allocation per position (PickerFixedAmount.java)."""

    name: str = "PickerFixedAmount"
    supported_engines: tuple[str, ...] = ("Stockpicker",)

    def __init__(
        self,
        *,
        amount: float = 1000.0,
        decimals: int = 0,
        lots_if_no_mm: float = 1.0,
        max_lots: float = 100000.0,
    ) -> None:
        self.amount = amount
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute stockpicker share quantity for a fixed cash amount."""
        _ = (account_equity, stop_loss_pips)
        share_price = pip_value
        if self.amount <= 0.0 or share_price <= 0.0:
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            raw = self.amount / share_price
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: PickerFixedAmount=%f", result)
        return result


class PickerRiskFixedPctOfAccount(BasePositionSizer):
    """Stockpicker equity allocation percentage (PickerRiskFixedPctOfAccount)."""

    name: str = "PickerRiskFixedPctOfAccount"
    supported_engines: tuple[str, ...] = ("Stockpicker",)

    def __init__(
        self,
        *,
        risk_in_pct: float = 10.0,
        decimals: int = 0,
        lots_if_no_mm: float = 1.0,
        max_lots: float = 100000.0,
    ) -> None:
        self.risk_in_pct = risk_in_pct
        self.decimals = decimals
        self.lots_if_no_mm = lots_if_no_mm
        self.max_lots = max_lots

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute stockpicker shares from percentage of account equity."""
        _ = stop_loss_pips
        share_price = pip_value
        if account_equity <= 0.0 or share_price <= 0.0 or self.risk_in_pct <= 0.0:
            result = _round_down(max(self.lots_if_no_mm, 0.0), self.decimals)
        else:
            allocated = account_equity * (self.risk_in_pct / 100.0)
            raw = allocated / share_price
            result = _clamp_lots(
                raw,
                decimals=self.decimals,
                lots_if_no_mm=self.lots_if_no_mm,
                max_lots=self.max_lots,
            )
        logger.debug("FR-mm-sizer-compute: PickerRiskFixedPctOfAccount=%f", result)
        return result


class SimpleMartingaleMM(BasePositionSizer):
    """Martingale step-multiplier money management (SimpleMartingaleMM.java)."""

    name: str = "SimpleMartingaleMM"
    supported_engines: tuple[str, ...] = ("Default", "Forex", "Futures")

    def __init__(
        self,
        *,
        mm_StartLots: float = 0.1,  # noqa: N803
        mm_Multiplier: float = 2.0,  # noqa: N803
        mm_MaxLots: float = 10.0,  # noqa: N803
        mm_Decimals: int = 2,  # noqa: N803
        consecutive_losses: int = 0,
    ) -> None:
        self.start_lots = mm_StartLots
        self.multiplier = mm_Multiplier
        self.max_lots = mm_MaxLots
        self.decimals = mm_Decimals
        self.consecutive_losses = max(consecutive_losses, 0)

    def record_trade_outcome(self, profit: float) -> None:
        """Update martingale loss streak from closed trade profit/loss."""
        if profit < 0.0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        """Compute martingale lot size, resetting to start_lots when exceeding max."""
        _ = (account_equity, stop_loss_pips, pip_value)
        if self.start_lots <= 0.0 or self.multiplier <= 0.0:
            return 0.0
        raw = self.start_lots * (self.multiplier**self.consecutive_losses)
        rounded = _round_down(raw, self.decimals)
        if self.max_lots > 0.0 and rounded > self.max_lots:
            rounded = _round_down(self.start_lots, self.decimals)
        logger.debug("FR-mm-sizer-compute: SimpleMartingaleMM=%f", rounded)
        return rounded


__all__ = [
    "ATRRiskBasedSizing",
    "CryptoFixedAmount",
    "CryptoFixedBalancePct",
    "CryptoSizeByPrice",
    "FixedAmount",
    "FixedSize",
    "PickerFixedAmount",
    "PickerRiskFixedPctOfAccount",
    "RiskFixedBalancePct",
    "RiskFixedPctOfAccount",
    "SimpleMartingaleMM",
    "StocksSizeByPrice",
]
