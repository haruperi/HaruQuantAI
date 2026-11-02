"""Position sizing algorithms and formula evaluation for orders.

Description:
    Provides canonical calculation of trade volumes from risk models (fixed lots,
    cash risk, percent equity, percent margin, and volatility-adjusted risk),
    matching StrategyQuant Money Management formula behaviors with strict
    lot-grid alignment and instrument constraints.
Purpose:
    FEAT-MONEY-MANAGEMENT: StrategyQuant donor-faithful money management algorithms.
Key Capabilities:
    - FR-MM-SIZING-EVAL: Multi-model position sizing evaluation.
    - FR-MM-LOTS-NORM: Strict tick/lot grid step alignment and clamping.
Python API Usage:
    from app.extend.money_management.sizing import evaluate_sizing
    vol = evaluate_sizing("fixed", lots=0.5)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_strategy_control_features.py --no-cov
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Literal

from app.core.host.logging import get_logger

logger = get_logger(__name__)

MAX_PERCENT: float = 100.0


def normalize_lots(
    volume: float,
    *,
    min_lot: float = 0.01,
    max_lot: float = 100.0,
    lot_step: float = 0.01,
) -> float:
    """Align raw requested volume to instrument lot-step constraints.

    Clamps to [min_lot, max_lot] and rounds to the nearest valid lot step.
    Raises ValueError on non-finite, negative, or degenerate constraints.
    """
    if not math.isfinite(volume) or volume < 0:
        raise ValueError("Trade volume must be finite and nonnegative")
    if not math.isfinite(min_lot) or min_lot <= 0:
        raise ValueError("min_lot must be finite and positive")
    if not math.isfinite(max_lot) or max_lot < min_lot:
        raise ValueError("max_lot must be >= min_lot")
    if not math.isfinite(lot_step) or lot_step <= 0:
        raise ValueError("lot_step must be finite and positive")

    if volume <= 0:
        return 0.0

    step_dec = Decimal(str(lot_step))
    vol_dec = Decimal(str(volume))
    rounded = float(round(vol_dec / step_dec) * step_dec)

    # Clamp to configured broker limits
    if rounded < min_lot:
        return min_lot
    if rounded > max_lot:
        return max_lot
    return rounded


def fixed_lots(
    lots: float,
    *,
    min_lot: float = 0.01,
    max_lot: float = 100.0,
    lot_step: float = 0.01,
) -> float:
    """Return normalized fixed lot size."""
    res = normalize_lots(lots, min_lot=min_lot, max_lot=max_lot, lot_step=lot_step)
    logger.debug("FR-MM-SIZING-EVAL: fixed_lots %s -> %s", lots, res)
    return res


def risk_cash(
    cash_amount: float,
    stop_distance_pips: float,
    pip_value: float = 10.0,
    *,
    min_lot: float = 0.01,
    max_lot: float = 100.0,
    lot_step: float = 0.01,
) -> float:
    """Calculate position size risking a fixed monetary cash amount.

    Formula: volume = cash_amount / (stop_distance_pips * pip_value_per_lot)
    """
    if not math.isfinite(cash_amount) or cash_amount <= 0:
        raise ValueError("Risk cash amount must be finite and positive")
    if not math.isfinite(stop_distance_pips) or stop_distance_pips <= 0:
        raise ValueError("Stop loss distance in pips must be finite and positive")
    if not math.isfinite(pip_value) or pip_value <= 0:
        raise ValueError("Pip value per standard lot must be finite and positive")

    loss_per_lot = stop_distance_pips * pip_value
    raw_lots = cash_amount / loss_per_lot
    res = normalize_lots(raw_lots, min_lot=min_lot, max_lot=max_lot, lot_step=lot_step)
    logger.debug(
        "FR-MM-SIZING-EVAL: risk_cash amount=%s stop_pips=%s -> %s",
        cash_amount,
        stop_distance_pips,
        res,
    )
    return res


def risk_percent(
    equity: float,
    risk_pct: float,
    stop_distance_pips: float,
    pip_value: float = 10.0,
    *,
    min_lot: float = 0.01,
    max_lot: float = 100.0,
    lot_step: float = 0.01,
) -> float:
    """Calculate position size risking a percentage of account equity.

    Formula: volume = (equity * (risk_pct / 100)) / (stop_distance * pip_value)
    """
    if not math.isfinite(equity) or equity <= 0:
        raise ValueError("Account equity must be finite and positive")
    if not math.isfinite(risk_pct) or risk_pct <= 0 or risk_pct > MAX_PERCENT:
        raise ValueError("Risk percentage must be in (0, 100]")

    cash_amount = equity * (risk_pct / MAX_PERCENT)
    res = risk_cash(
        cash_amount,
        stop_distance_pips,
        pip_value=pip_value,
        min_lot=min_lot,
        max_lot=max_lot,
        lot_step=lot_step,
    )
    logger.debug(
        "FR-MM-SIZING-EVAL: risk_percent equity=%s risk_pct=%s stop_pips=%s -> %s",
        equity,
        risk_pct,
        stop_distance_pips,
        res,
    )
    return res


def margin_percent(
    equity: float,
    margin_pct: float,
    price: float,
    *,
    contract_size: float = 100_000.0,
    leverage: float = 30.0,
    min_lot: float = 0.01,
    max_lot: float = 100.0,
    lot_step: float = 0.01,
) -> float:
    """Calculate position size that consumes a fixed percentage of equity.

    Formula:
        target_margin = equity * (margin_pct / 100)
        margin_per_lot = (price * contract_size) / leverage
        volume = target_margin / margin_per_lot
    """
    if not math.isfinite(equity) or equity <= 0:
        raise ValueError("Account equity must be finite and positive")
    if not math.isfinite(margin_pct) or margin_pct <= 0 or margin_pct > MAX_PERCENT:
        raise ValueError("Margin percentage must be in (0, 100]")
    if not math.isfinite(price) or price <= 0:
        raise ValueError("Market price must be finite and positive")
    if not math.isfinite(leverage) or leverage <= 0:
        raise ValueError("Leverage must be finite and positive")

    target_margin = equity * (margin_pct / MAX_PERCENT)
    margin_per_lot = (price * contract_size) / leverage
    raw_lots = target_margin / margin_per_lot
    res = normalize_lots(raw_lots, min_lot=min_lot, max_lot=max_lot, lot_step=lot_step)
    logger.debug(
        "FR-MM-SIZING-EVAL: margin_percent equity=%s margin_pct=%s price=%s -> %s",
        equity,
        margin_pct,
        price,
        res,
    )
    return res


def volatility_risk(
    cash_risk: float,
    atr_value: float,
    point_value: float = 1.0,
    multiplier: float = 2.0,
    *,
    min_lot: float = 0.01,
    max_lot: float = 100.0,
    lot_step: float = 0.01,
) -> float:
    """Calculate position size based on ATR market volatility.

    Formula: volume = cash_risk / (atr_value * multiplier * point_value_per_lot)
    """
    if not math.isfinite(cash_risk) or cash_risk <= 0:
        raise ValueError("Cash risk must be finite and positive")
    if not math.isfinite(atr_value) or atr_value <= 0:
        raise ValueError("ATR volatility value must be finite and positive")
    if not math.isfinite(multiplier) or multiplier <= 0:
        raise ValueError("Volatility multiplier must be finite and positive")
    if not math.isfinite(point_value) or point_value <= 0:
        raise ValueError("Point value must be finite and positive")

    risk_per_lot = atr_value * multiplier * point_value
    raw_lots = cash_risk / risk_per_lot
    res = normalize_lots(raw_lots, min_lot=min_lot, max_lot=max_lot, lot_step=lot_step)
    logger.debug(
        "FR-MM-SIZING-EVAL: volatility_risk cash=%s atr=%s mult=%s -> %s",
        cash_risk,
        atr_value,
        multiplier,
        res,
    )
    return res


SizingMethod = Literal[
    "fixed", "cash_risk", "percent_equity", "percent_margin", "volatility"
]


def evaluate_sizing(
    method: SizingMethod,
    *,
    lots: float = 0.1,
    cash_amount: float = 100.0,
    equity: float = 10_000.0,
    risk_pct: float = 1.0,
    margin_pct: float = 5.0,
    stop_distance_pips: float = 50.0,
    pip_value: float = 10.0,
    price: float = 1.0,
    atr_value: float = 0.0050,
    point_value: float = 1.0,
    multiplier: float = 2.0,
    min_lot: float = 0.01,
    max_lot: float = 100.0,
    lot_step: float = 0.01,
) -> float:
    """Unified evaluator for strategy order sizing selection."""
    if method == "fixed":
        return fixed_lots(lots, min_lot=min_lot, max_lot=max_lot, lot_step=lot_step)
    if method == "cash_risk":
        return risk_cash(
            cash_amount,
            stop_distance_pips,
            pip_value=pip_value,
            min_lot=min_lot,
            max_lot=max_lot,
            lot_step=lot_step,
        )
    if method == "percent_equity":
        return risk_percent(
            equity,
            risk_pct,
            stop_distance_pips,
            pip_value=pip_value,
            min_lot=min_lot,
            max_lot=max_lot,
            lot_step=lot_step,
        )
    if method == "percent_margin":
        return margin_percent(
            equity,
            margin_pct,
            price,
            min_lot=min_lot,
            max_lot=max_lot,
            lot_step=lot_step,
        )
    if method == "volatility":
        return volatility_risk(
            cash_amount,
            atr_value,
            point_value=point_value,
            multiplier=multiplier,
            min_lot=min_lot,
            max_lot=max_lot,
            lot_step=lot_step,
        )
    raise ValueError(f"Unknown sizing method: {method}")


__all__ = [
    "MAX_PERCENT",
    "SizingMethod",
    "evaluate_sizing",
    "fixed_lots",
    "margin_percent",
    "normalize_lots",
    "risk_cash",
    "risk_percent",
    "volatility_risk",
]
