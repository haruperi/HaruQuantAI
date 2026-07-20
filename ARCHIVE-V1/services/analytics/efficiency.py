"""efficiency.py - Measure how effectively strategies convert capital, time, risk, and excursions into returns.

Functions:
    capital_efficiency: Return per unit of nominal capital deployed.
    avg_trade_notional_efficiency: Alias for capital_efficiency; clearer semantic name.
    return_per_unit_mae: Total return relative to absolute adverse excursion (MAE) experienced.
    risk_adjusted_efficiency: Return relative to total defined initial risk (R).
    avg_return_per_risk_unit: Average R-multiple per closed trade.
    return_per_trade_hour: Net Profit per hour spent in active trades (sum of all trade-hours).
    return_per_market_hour: Net Profit per hour where at least one trade was open (merged market time).
    trades_per_day: Average number of closed trades per calendar day in the test period.
    return_per_calendar_day: Net Profit per calendar day in the test period.
    profit_per_trade_per_day: Net profit normalized by both number of trades and calendar days.
    mfe_efficiency: Average percentage of MFE captured by winning trades.
    aggregate_mfe_capture_ratio: Aggregate MFE capture ratio for winning trades.
    profit_per_pip_risk: Reward-to-risk based on price movement (Profit Pips / |MAE Pips|).
    mae_efficiency: Average realized-loss-to-MAE ratio for losing trades.
    exit_efficiency: Combined measure of capturing wins and containing losses (0-1).
    loss_containment_efficiency: Average measure of how well realized losses stayed above their absolute valley (MAE).
    aggregate_loss_containment_efficiency: Aggregate loss containment for losing trades.
    position_size_efficiency: Correlation between absolute position size and normalized trade outcome (R-multiple).
    calculate_efficiency_metrics: Calculate MAE and MFE efficiency context from trades.
"""

from typing import Any

import pandas as pd

from app.services.utils.logger import logger

from .common import (
    EPSILON,
    analytics_tool_result,
    get_closed_trades,
    get_r_multiples,
    time_in_market_duration,
)

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "analytics"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False
CREATES = False
READS = True
UPDATES = False
DELETES = False
TRADES = False


# =========================================================================
# Internal Implementation Functions
# =========================================================================


def _capital_efficiency_impl(
    trades: pd.DataFrame,
    contract_size: float = 100000.0,
) -> float:
    """
    Calculate return per unit of nominal capital deployed.

    Logic:
        The function filters for closed trades, sums the total profit_loss, and calculates
        the average absolute nominal exposure (average size * contract_size). It then
        divides the total profit by this average nominal exposure.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.
        contract_size (float): The multiplier to convert size to nominal value. Defaults to 100000.0.

    Returns:
        float: Capital efficiency ratio.
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns or "size" not in data.columns:
        return 0.0

    total_profit = data["profit_loss"].sum()
    # Use absolute size to handle short positions correctly
    avg_nominal = data["size"].abs().mean() * contract_size

    if avg_nominal < EPSILON:
        return 0.0

    return float(total_profit / avg_nominal)


def _avg_trade_notional_efficiency_impl(
    trades: pd.DataFrame,
    contract_size: float = 100000.0,
) -> float:
    """
    Calculate Average Trade Notional Efficiency.

    Logic:
        This is an alias for the capital efficiency implementation, providing a more
        semantically descriptive name for the same underlying calculation.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.
        contract_size (float): The multiplier to convert size to nominal value. Defaults to 100000.0.

    Returns:
        float: Notional efficiency ratio.
    """
    return _capital_efficiency_impl(trades, contract_size)


def _return_per_unit_mae_impl(trades: pd.DataFrame) -> float:
    """
    Calculate total return relative to absolute adverse excursion (MAE) experienced.

    Logic:
        The function sums the profit_loss for all closed trades and divides it by the
        sum of the absolute values of Maximum Adverse Excursion (MAE) in USD.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Return per unit of MAE.
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns or "mae_usd" not in data.columns:
        return 0.0

    total_profit = data["profit_loss"].sum()
    total_mae = data["mae_usd"].abs().sum()

    if total_mae < EPSILON:
        return float("inf") if total_profit > EPSILON else 0.0

    return float(total_profit / total_mae)


def _risk_adjusted_efficiency_impl(trades: pd.DataFrame) -> float:
    """
    Calculate return relative to total defined initial risk (R).

    Logic:
        The function sums the total profit_loss and divides it by the sum of absolute
        initial risk amounts. It looks for columns like 'initial_risk_amount' or 'initial_risk_usd'.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Risk-adjusted efficiency ratio.
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns:
        return 0.0

    # Support multiple risk column names
    risk_col = next(
        (
            col
            for col in ["initial_risk_amount", "initial_risk", "initial_risk_usd"]
            if col in data.columns
        ),
        None,
    )

    if not risk_col:
        return 0.0

    total_profit = data["profit_loss"].sum()
    total_risk = data[risk_col].abs().sum()

    if total_risk < EPSILON:
        return float("inf") if total_profit > EPSILON else 0.0

    return float(total_profit / total_risk)


def _avg_return_per_risk_unit_impl(trades: pd.DataFrame) -> float:
    """
    Calculate average R-multiple per closed trade.

    Logic:
        The function calculates R-multiples for all closed trades (profit_loss / initial_risk)
        and returns the arithmetic mean of these values.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Average R-multiple.
    """
    r = get_r_multiples(trades)
    if r.empty:
        return 0.0
    return float(r.mean())


def _return_per_trade_hour_impl(trades: pd.DataFrame) -> float:
    """
    Calculate net Profit per hour spent in active trades (sum of all trade-hours).

    Logic:
        The function sums the total profit_loss and divides it by the sum of 'time_in_trade'
        hours for all closed trades.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Profit per trade hour.
    """
    data = get_closed_trades(trades)
    if (
        data.empty
        or "profit_loss" not in data.columns
        or "time_in_trade" not in data.columns
    ):
        return 0.0

    total_profit = data["profit_loss"].sum()
    total_trade_hours = data["time_in_trade"].sum()

    if total_trade_hours == 0:
        return 0.0

    return float(total_profit / total_trade_hours)


def _return_per_market_hour_impl(
    trades: pd.DataFrame, end_time: pd.Timestamp | None = None
) -> float:
    """
    Calculate net Profit per hour where at least one trade was open (merged market time).

    Logic:
        The function calculates the total duration the strategy was in the market (merging
        overlapping trade durations) and divides the total profit_loss by the total
        market hours.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.
        end_time (Optional[pd.Timestamp]): Optional end time for calculation.

    Returns:
        float: Profit per market hour.
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns:
        return 0.0

    total_profit = data["profit_loss"].sum()
    market_time = time_in_market_duration(data, end_time)
    market_hours = market_time.total_seconds() / 3600.0

    if market_hours == 0:
        return 0.0

    return float(total_profit / market_hours)


def _trades_per_day_impl(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> float:
    """
    Calculate average number of closed trades per calendar day in the test period.

    Logic:
        The function determines the total duration of the test period in days and divides
        the total number of closed trades by this duration.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.
        start_time (Optional[pd.Timestamp]): Optional start time of the period.
        end_time (Optional[pd.Timestamp]): Optional end time of the period.

    Returns:
        float: Trades per day.
    """
    data = get_closed_trades(trades)
    if (
        data.empty
        or "open_time" not in data.columns
        or "close_time" not in data.columns
    ):
        return 0.0

    # Ensure clean timestamps
    open_times = pd.to_datetime(data["open_time"])
    close_times = pd.to_datetime(data["close_time"])

    t_start = start_time if start_time else open_times.min()
    t_end = end_time if end_time else close_times.max()

    if pd.isna(t_start) or pd.isna(t_end) or t_end <= t_start:
        return 0.0

    total_days = (t_end - t_start).total_seconds() / 86400.0
    return float(len(data) / total_days) if total_days > 0 else 0.0


def _return_per_calendar_day_impl(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> float:
    """
    Calculate Net Profit per calendar day in the test period.

    Logic:
        The function calculates total profit_loss and divides it by the total duration
        of the test period in calendar days.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.
        start_time (Optional[pd.Timestamp]): Optional start time.
        end_time (Optional[pd.Timestamp]): Optional end time.

    Returns:
        float: Return per calendar day.
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns:
        return 0.0
    if "open_time" not in data.columns or "close_time" not in data.columns:
        return 0.0

    total_profit = data["profit_loss"].sum()

    # Ensure clean timestamps
    open_times = pd.to_datetime(data["open_time"])
    close_times = pd.to_datetime(data["close_time"])

    t_start = start_time if start_time else open_times.min()
    t_end = end_time if end_time else close_times.max()

    if pd.isna(t_start) or pd.isna(t_end) or t_end <= t_start:
        return 0.0

    total_days = (t_end - t_start).total_seconds() / 86400.0
    return float(total_profit / total_days) if total_days > 0 else 0.0


def _profit_per_trade_per_day_impl(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> float:
    """
    Calculate net profit normalized by both number of trades and calendar days.

    Logic:
        The function multiplies the average profit per trade by the number of trades
        per day. This provides a normalized view of daily earning potential.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.
        start_time (Optional[pd.Timestamp]): Optional start time.
        end_time (Optional[pd.Timestamp]): Optional end time.

    Returns:
        float: Profit per trade per day.
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns:
        return 0.0

    tpd = _trades_per_day_impl(data, start_time, end_time)
    if tpd <= 0:
        return 0.0

    avg_trade = data["profit_loss"].mean()
    return float(avg_trade * tpd)


def _mfe_efficiency_impl(trades: pd.DataFrame) -> float:
    """
    Calculate average percentage of MFE captured by winning trades.

    Logic:
        For winning trades, the function calculates the ratio of realized profit_loss
        to Maximum Favorable Excursion (MFE). It caps the efficiency per trade at 100%
        and returns the average.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: MFE efficiency ratio (0.0 to 1.0).
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns or "mfe_usd" not in data.columns:
        return 0.0

    winners = data[data["profit_loss"] > EPSILON]
    if winners.empty:
        return 0.0

    pnl = winners["profit_loss"].astype(float)
    mfe = winners["mfe_usd"].astype(float).clip(lower=0.0)

    # Avoid division by zero
    valid = mfe > EPSILON
    if not valid.any():
        return 0.0

    # Efficiency per trade capped at 100%
    eff = pnl[valid] / mfe[valid]
    eff = eff.clip(lower=0.0, upper=1.0)

    return float(eff.mean())


def _aggregate_mfe_capture_ratio_impl(trades: pd.DataFrame) -> float:
    """
    Calculate aggregate MFE capture ratio for winning trades.

    Logic:
        The function sums the total profit_loss of winning trades and divides it by
        the sum of their MFE values. This provides a portfolio-level view of capture efficiency.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Aggregate MFE capture ratio.
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns or "mfe_usd" not in data.columns:
        return 0.0

    winners = data[data["profit_loss"] > EPSILON]
    if winners.empty:
        return 0.0

    total_profit = winners["profit_loss"].sum()
    total_mfe = winners["mfe_usd"].astype(float).clip(lower=0.0).sum()

    if total_mfe <= EPSILON:
        return 0.0

    return float(max(0.0, min(1.0, total_profit / total_mfe)))


def _profit_per_pip_risk_impl(trades: pd.DataFrame) -> float:
    """
    Calculate reward-to-risk based on price movement (Profit Pips / |MAE Pips|).

    Logic:
        The function sums profit pips and divides by the sum of absolute MAE pips across all trades.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Profit per pip of risk.
    """
    data = get_closed_trades(trades)
    if data.empty:
        return 0.0

    profit_col = None
    for col in ["profit_loss_pips", "profit_pips", "pips"]:
        if col in data.columns:
            profit_col = col
            break

    mae_col = None
    for col in ["mae_pips", "mae_points"]:
        if col in data.columns:
            mae_col = col
            break

    if not profit_col or not mae_col:
        return 0.0

    total_profit_pips = data[profit_col].sum()
    total_mae_pips = data[mae_col].abs().sum()

    if total_mae_pips < EPSILON:
        return 0.0

    return float(total_profit_pips / total_mae_pips)


def _mae_efficiency_impl(trades: pd.DataFrame) -> float:
    """
    Calculate average realized-loss-to-MAE ratio for losing trades.

    Logic:
        For losing trades, it calculates the ratio of absolute realized loss to absolute MAE.
        A ratio of 1.0 means the trade closed at its worst point (maximum pain).

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: MAE efficiency ratio.
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns or "mae_usd" not in data.columns:
        return 0.0

    losers = data[data["profit_loss"] < -EPSILON]
    if losers.empty:
        return 0.0

    loss = losers["profit_loss"].abs().astype(float)
    mae = losers["mae_usd"].abs().astype(float)

    valid = mae > EPSILON
    if not valid.any():
        return 0.0

    # Efficiency per trade: |P&L| / |MAE|
    eff = loss[valid] / mae[valid]
    eff = eff.clip(lower=0.0, upper=1.0)

    return float(eff.mean())


def _exit_efficiency_impl(trades: pd.DataFrame) -> float:
    """
    Calculate combined measure of capturing wins and containing losses (0-1).

    Logic:
        This is a composite metric calculating the average of MFE efficiency and
        MAE containment (1 - MAE efficiency).

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Combined exit efficiency score.
    """
    mfe_eff = max(0.0, min(1.0, _mfe_efficiency_impl(trades)))

    # MAE containment: 1 - mae_efficiency (how much 'heat' was avoided)
    mae_eff_val = _mae_efficiency_impl(trades)
    mae_containment = max(0.0, min(1.0, 1.0 - mae_eff_val))

    return float((mfe_eff + mae_containment) / 2.0)


def _loss_containment_efficiency_impl(trades: pd.DataFrame) -> float:
    """
    Calculate average measure of how well realized losses stayed above their absolute valley (MAE).

    Logic:
        For losing trades, it calculates (1 - |Loss|/|MAE|) and returns the average as a percentage.
        100% containment means zero realized loss despite the MAE.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Loss containment efficiency (percentage).
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns or "mae_usd" not in data.columns:
        return 0.0

    losers = data[data["profit_loss"] < -EPSILON]
    if losers.empty:
        return 100.0

    pnl = losers["profit_loss"].abs()
    mae = losers["mae_usd"].abs()

    valid = mae > EPSILON
    if not valid.any():
        return 100.0

    # Per-trade containment
    containment = 1.0 - (pnl[valid] / mae[valid])
    containment = containment.clip(lower=0.0, upper=1.0)

    return float(containment.mean() * 100.0)


def _aggregate_loss_containment_efficiency_impl(trades: pd.DataFrame) -> float:
    """
    Calculate aggregate loss containment for losing trades.

    Logic:
        Calculates (1 - Total Absolute Loss / Total Absolute MAE) for all losing trades
        and returns it as a percentage.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Aggregate loss containment efficiency (percentage).
    """
    data = get_closed_trades(trades)
    if data.empty or "profit_loss" not in data.columns or "mae_usd" not in data.columns:
        return 0.0

    losers = data[data["profit_loss"] < -EPSILON]
    if losers.empty:
        return 100.0

    total_loss = losers["profit_loss"].abs().sum()
    total_mae = losers["mae_usd"].abs().sum()

    if total_mae <= EPSILON:
        return 100.0

    containment = 1.0 - (total_loss / total_mae)
    containment = max(0.0, min(1.0, containment))

    return float(containment * 100.0)


def _position_size_efficiency_impl(trades: pd.DataFrame) -> float:
    """
    Calculate correlation between absolute position size and normalized trade outcome (R-multiple).

    Logic:
        Calculates the Pearson correlation coefficient between the absolute trade volume/size
        and the resulting R-multiple. High positive correlation suggests effective sizing.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        float: Correlation coefficient.
    """
    data = get_closed_trades(trades)
    if data.empty:
        return 0.0

    size_col = None
    for col in ["size", "volume", "quantity"]:
        if col in data.columns:
            size_col = col
            break

    if not size_col:
        return 0.0

    r_multiples = get_r_multiples(data)
    if r_multiples.empty:
        # Fallback to normalized P&L correlation
        pnl = data["profit_loss"].astype(float)
        size = data[size_col].abs()
        if pnl.std() < EPSILON or size.std() < EPSILON:
            return 0.0
        return float(size.corr(pnl))

    size = data.loc[r_multiples.index, size_col].abs()
    if size.std() < EPSILON or r_multiples.std() < EPSILON:
        return 0.0

    return float(size.corr(r_multiples))


def _calculate_efficiency_metrics_impl(
    trades: pd.DataFrame,
) -> dict[str, float]:
    """
    Calculate MAE and MFE efficiency context from trades.

    Logic:
        Calculates the mean value of Maximum Adverse Excursion (MAE) and Maximum
        Favorable Excursion (MFE) from the provided trades.

    Args:
        trades (pd.DataFrame): DataFrame containing trade data.

    Returns:
        Dict[str, float]: Dictionary containing avg_mae and avg_mfe.
    """
    mae = pd.to_numeric(trades.get("mae", pd.Series(dtype=float)), errors="coerce")
    mfe = pd.to_numeric(trades.get("mfe", pd.Series(dtype=float)), errors="coerce")
    return {
        "avg_mae": float(mae.mean()) if not mae.empty else 0.0,
        "avg_mfe": float(mfe.mean()) if not mfe.empty else 0.0,
    }


# =========================================================================
# AI Tools (External Facing)
# =========================================================================


def _capital_efficiency_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
    contract_size: float = 100000.0,
) -> dict[str, Any]:
    """Calculate capital efficiency (return per unit of nominal capital deployed)."""
    try:
        # 1. Input Validation
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"capital_efficiency": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        # 2. Core Execution
        result = _capital_efficiency_impl(df, contract_size)

        # 3. Structured Return
        res = analytics_tool_result(
            "capital_efficiency", data={"capital_efficiency": result}
        )
        logger.info("Executed capital_efficiency successfully.")
        return res

    except Exception as e:
        # 4. Graceful Error Handling
        logger.error(f"Error in capital_efficiency: {e!s}")
        return {"status": "error", "message": str(e)}


def _avg_trade_notional_efficiency_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
    contract_size: float = 100000.0,
) -> dict[str, Any]:
    """Calculate average trade notional efficiency (alias for capital efficiency)."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"avg_trade_notional_efficiency": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _avg_trade_notional_efficiency_impl(df, contract_size)

        res = analytics_tool_result(
            "avg_trade_notional_efficiency",
            data={"avg_trade_notional_efficiency": result},
        )
        logger.info("Executed avg_trade_notional_efficiency successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in avg_trade_notional_efficiency: {e!s}")
        return {"status": "error", "message": str(e)}


def _return_per_unit_mae_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate total return relative to absolute adverse excursion (MAE) experienced."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"return_per_unit_mae": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _return_per_unit_mae_impl(df)

        res = analytics_tool_result(
            "return_per_unit_mae", data={"return_per_unit_mae": result}
        )
        logger.info("Executed return_per_unit_mae successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in return_per_unit_mae: {e!s}")
        return {"status": "error", "message": str(e)}


def _risk_adjusted_efficiency_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate return relative to total defined initial risk (R)."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"risk_adjusted_efficiency": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _risk_adjusted_efficiency_impl(df)

        res = analytics_tool_result(
            "risk_adjusted_efficiency", data={"risk_adjusted_efficiency": result}
        )
        logger.info("Executed risk_adjusted_efficiency successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in risk_adjusted_efficiency: {e!s}")
        return {"status": "error", "message": str(e)}


def _avg_return_per_risk_unit_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate average R-multiple per closed trade."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"avg_return_per_risk_unit": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _avg_return_per_risk_unit_impl(df)

        res = analytics_tool_result(
            "avg_return_per_risk_unit", data={"avg_return_per_risk_unit": result}
        )
        logger.info("Executed avg_return_per_risk_unit successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in avg_return_per_risk_unit: {e!s}")
        return {"status": "error", "message": str(e)}


def _return_per_trade_hour_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate net Profit per hour spent in active trades."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"return_per_trade_hour": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _return_per_trade_hour_impl(df)

        res = analytics_tool_result(
            "return_per_trade_hour", data={"return_per_trade_hour": result}
        )
        logger.info("Executed return_per_trade_hour successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in return_per_trade_hour: {e!s}")
        return {"status": "error", "message": str(e)}


def _return_per_market_hour_impl(
    trades: pd.DataFrame | list[dict[str, Any]], end_time: pd.Timestamp | None = None
) -> dict[str, Any]:
    """Calculate net Profit per hour where at least one trade was open."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"return_per_market_hour": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _return_per_market_hour_impl(df, end_time)

        res = analytics_tool_result(
            "return_per_market_hour", data={"return_per_market_hour": result}
        )
        logger.info("Executed return_per_market_hour successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in return_per_market_hour: {e!s}")
        return {"status": "error", "message": str(e)}


def _trades_per_day_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """Calculate average number of closed trades per calendar day."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"trades_per_day": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _trades_per_day_impl(df, start_time, end_time)

        res = analytics_tool_result("trades_per_day", data={"trades_per_day": result})
        logger.info("Executed trades_per_day successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in trades_per_day: {e!s}")
        return {"status": "error", "message": str(e)}


def _return_per_calendar_day_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """Calculate Net Profit per calendar day in the test period."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"return_per_calendar_day": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _return_per_calendar_day_impl(df, start_time, end_time)

        res = analytics_tool_result(
            "return_per_calendar_day", data={"return_per_calendar_day": result}
        )
        logger.info("Executed return_per_calendar_day successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in return_per_calendar_day: {e!s}")
        return {"status": "error", "message": str(e)}


def _profit_per_trade_per_day_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """Calculate net profit normalized by both number of trades and calendar days."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"profit_per_trade_per_day": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _profit_per_trade_per_day_impl(df, start_time, end_time)

        res = analytics_tool_result(
            "profit_per_trade_per_day", data={"profit_per_trade_per_day": result}
        )
        logger.info("Executed profit_per_trade_per_day successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in profit_per_trade_per_day: {e!s}")
        return {"status": "error", "message": str(e)}


def _mfe_efficiency_impl(trades: pd.DataFrame | list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate average percentage of MFE captured by winning trades."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"mfe_efficiency": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _mfe_efficiency_impl(df)

        res = analytics_tool_result("mfe_efficiency", data={"mfe_efficiency": result})
        logger.info("Executed mfe_efficiency successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in mfe_efficiency: {e!s}")
        return {"status": "error", "message": str(e)}


def _aggregate_mfe_capture_ratio_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate aggregate MFE capture ratio for winning trades."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"aggregate_mfe_capture_ratio": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _aggregate_mfe_capture_ratio_impl(df)

        res = analytics_tool_result(
            "aggregate_mfe_capture_ratio", data={"aggregate_mfe_capture_ratio": result}
        )
        logger.info("Executed aggregate_mfe_capture_ratio successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in aggregate_mfe_capture_ratio: {e!s}")
        return {"status": "error", "message": str(e)}


def _profit_per_pip_risk_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate reward-to-risk based on price movement."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"profit_per_pip_risk": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _profit_per_pip_risk_impl(df)

        res = analytics_tool_result(
            "profit_per_pip_risk", data={"profit_per_pip_risk": result}
        )
        logger.info("Executed profit_per_pip_risk successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in profit_per_pip_risk: {e!s}")
        return {"status": "error", "message": str(e)}


def _mae_efficiency_impl(trades: pd.DataFrame | list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate average realized-loss-to-MAE ratio for losing trades."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"mae_efficiency": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _mae_efficiency_impl(df)

        res = analytics_tool_result("mae_efficiency", data={"mae_efficiency": result})
        logger.info("Executed mae_efficiency successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in mae_efficiency: {e!s}")
        return {"status": "error", "message": str(e)}


def _exit_efficiency_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate combined measure of capturing wins and containing losses."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"exit_efficiency": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _exit_efficiency_impl(df)

        res = analytics_tool_result("exit_efficiency", data={"exit_efficiency": result})
        logger.info("Executed exit_efficiency successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in exit_efficiency: {e!s}")
        return {"status": "error", "message": str(e)}


def _loss_containment_efficiency_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate average measure of how well realized losses stayed above their MAE."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"loss_containment_efficiency": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _loss_containment_efficiency_impl(df)

        res = analytics_tool_result(
            "loss_containment_efficiency", data={"loss_containment_efficiency": result}
        )
        logger.info("Executed loss_containment_efficiency successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in loss_containment_efficiency: {e!s}")
        return {"status": "error", "message": str(e)}


def _aggregate_loss_containment_efficiency_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate aggregate loss containment for losing trades."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {
                "status": "success",
                "data": {"aggregate_loss_containment_efficiency": 0.0},
            }
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _aggregate_loss_containment_efficiency_impl(df)

        res = analytics_tool_result(
            "aggregate_loss_containment_efficiency",
            data={"aggregate_loss_containment_efficiency": result},
        )
        logger.info("Executed aggregate_loss_containment_efficiency successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in aggregate_loss_containment_efficiency: {e!s}")
        return {"status": "error", "message": str(e)}


def _position_size_efficiency_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate correlation between absolute position size and R-multiple."""
    try:
        if trades is None or (isinstance(trades, pd.DataFrame) and trades.empty):
            return {"status": "success", "data": {"position_size_efficiency": 0.0}}
        df = pd.DataFrame(trades) if not isinstance(trades, pd.DataFrame) else trades

        result = _position_size_efficiency_impl(df)

        res = analytics_tool_result(
            "position_size_efficiency", data={"position_size_efficiency": result}
        )
        logger.info("Executed position_size_efficiency successfully.")
        return res
    except Exception as e:
        logger.error(f"Error in position_size_efficiency: {e!s}")
        return {"status": "error", "message": str(e)}


def _calculate_efficiency_metrics_impl(
    *,
    trades: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate MAE and MFE efficiency context from trades."""
    try:
        # 1. Input Validation
        if not trades:
            return analytics_tool_result(
                "calculate_efficiency_metrics",
                data={"avg_mae": 0.0, "avg_mfe": 0.0},
                request_id=request_id,
                agent_name=agent_name,
                environment=environment,
                dry_run=dry_run,
            )
        df = pd.DataFrame(trades)

        # 2. Core Execution
        result = _calculate_efficiency_metrics_impl(df)

        # 3. Structured Return
        res = analytics_tool_result(
            "calculate_efficiency_metrics",
            data=result,
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )
        logger.info("Executed calculate_efficiency_metrics successfully.")
        return res

    except Exception as e:
        # 4. Graceful Error Handling
        logger.error(f"Error in calculate_efficiency_metrics: {e!s}")
        return {"status": "error", "message": str(e)}


def capital_efficiency(
    trades: pd.DataFrame,
    contract_size: float = 100000.0,
) -> dict[str, Any]:
    """AI Tool wrapper for _capital_efficiency_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

        res = _capital_efficiency_impl(**kwargs)
        logger.info("Executed capital_efficiency tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "capital_efficiency", data={"capital_efficiency": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_trade_notional_efficiency(
    trades: pd.DataFrame,
    contract_size: float = 100000.0,
) -> dict[str, Any]:
    """AI Tool wrapper for _avg_trade_notional_efficiency_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_contract_size = contract_size
        if "contract_size" in ["trades", "open_trades"] and isinstance(
            arg_contract_size, (list, dict)
        ):
            arg_contract_size = pd.DataFrame(arg_contract_size)
        elif "contract_size" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_contract_size, list):
            arg_contract_size = pd.Series(arg_contract_size)
        kwargs["contract_size"] = arg_contract_size

        res = _avg_trade_notional_efficiency_impl(**kwargs)
        logger.info("Executed avg_trade_notional_efficiency tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "avg_trade_notional_efficiency",
            data={"avg_trade_notional_efficiency": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_per_unit_mae(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _return_per_unit_mae_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _return_per_unit_mae_impl(**kwargs)
        logger.info("Executed return_per_unit_mae tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "return_per_unit_mae", data={"return_per_unit_mae": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def risk_adjusted_efficiency(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _risk_adjusted_efficiency_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _risk_adjusted_efficiency_impl(**kwargs)
        logger.info("Executed risk_adjusted_efficiency tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "risk_adjusted_efficiency", data={"risk_adjusted_efficiency": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_return_per_risk_unit(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _avg_return_per_risk_unit_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _avg_return_per_risk_unit_impl(**kwargs)
        logger.info("Executed avg_return_per_risk_unit tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "avg_return_per_risk_unit", data={"avg_return_per_risk_unit": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_per_trade_hour(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _return_per_trade_hour_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _return_per_trade_hour_impl(**kwargs)
        logger.info("Executed return_per_trade_hour tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "return_per_trade_hour", data={"return_per_trade_hour": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_per_market_hour(
    trades: pd.DataFrame, end_time: pd.Timestamp | None = None
) -> dict[str, Any]:
    """AI Tool wrapper for _return_per_market_hour_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _return_per_market_hour_impl(**kwargs)
        logger.info("Executed return_per_market_hour tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "return_per_market_hour", data={"return_per_market_hour": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def trades_per_day(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _trades_per_day_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_start_time = start_time
        if "start_time" in ["trades", "open_trades"] and isinstance(
            arg_start_time, (list, dict)
        ):
            arg_start_time = pd.DataFrame(arg_start_time)
        elif "start_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_start_time, list):
            arg_start_time = pd.Series(arg_start_time)
        kwargs["start_time"] = arg_start_time

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _trades_per_day_impl(**kwargs)
        logger.info("Executed trades_per_day tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "trades_per_day", data={"trades_per_day": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def return_per_calendar_day(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _return_per_calendar_day_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_start_time = start_time
        if "start_time" in ["trades", "open_trades"] and isinstance(
            arg_start_time, (list, dict)
        ):
            arg_start_time = pd.DataFrame(arg_start_time)
        elif "start_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_start_time, list):
            arg_start_time = pd.Series(arg_start_time)
        kwargs["start_time"] = arg_start_time

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _return_per_calendar_day_impl(**kwargs)
        logger.info("Executed return_per_calendar_day tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "return_per_calendar_day", data={"return_per_calendar_day": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def profit_per_trade_per_day(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _profit_per_trade_per_day_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_start_time = start_time
        if "start_time" in ["trades", "open_trades"] and isinstance(
            arg_start_time, (list, dict)
        ):
            arg_start_time = pd.DataFrame(arg_start_time)
        elif "start_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_start_time, list):
            arg_start_time = pd.Series(arg_start_time)
        kwargs["start_time"] = arg_start_time

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _profit_per_trade_per_day_impl(**kwargs)
        logger.info("Executed profit_per_trade_per_day tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "profit_per_trade_per_day", data={"profit_per_trade_per_day": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def mfe_efficiency(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _mfe_efficiency_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _mfe_efficiency_impl(**kwargs)
        logger.info("Executed mfe_efficiency tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "mfe_efficiency", data={"mfe_efficiency": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def aggregate_mfe_capture_ratio(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _aggregate_mfe_capture_ratio_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _aggregate_mfe_capture_ratio_impl(**kwargs)
        logger.info("Executed aggregate_mfe_capture_ratio tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "aggregate_mfe_capture_ratio",
            data={"aggregate_mfe_capture_ratio": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def profit_per_pip_risk(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _profit_per_pip_risk_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _profit_per_pip_risk_impl(**kwargs)
        logger.info("Executed profit_per_pip_risk tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "profit_per_pip_risk", data={"profit_per_pip_risk": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def mae_efficiency(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _mae_efficiency_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _mae_efficiency_impl(**kwargs)
        logger.info("Executed mae_efficiency tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "mae_efficiency", data={"mae_efficiency": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def exit_efficiency(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _exit_efficiency_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _exit_efficiency_impl(**kwargs)
        logger.info("Executed exit_efficiency tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "exit_efficiency", data={"exit_efficiency": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def loss_containment_efficiency(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _loss_containment_efficiency_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _loss_containment_efficiency_impl(**kwargs)
        logger.info("Executed loss_containment_efficiency tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "loss_containment_efficiency",
            data={"loss_containment_efficiency": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def aggregate_loss_containment_efficiency(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _aggregate_loss_containment_efficiency_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _aggregate_loss_containment_efficiency_impl(**kwargs)
        logger.info("Executed aggregate_loss_containment_efficiency tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "aggregate_loss_containment_efficiency",
            data={"aggregate_loss_containment_efficiency": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def position_size_efficiency(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _position_size_efficiency_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _position_size_efficiency_impl(**kwargs)
        logger.info("Executed position_size_efficiency tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "position_size_efficiency", data={"position_size_efficiency": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def calculate_efficiency_metrics(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    """AI Tool wrapper for _calculate_efficiency_metrics_impl."""
    try:
        import pandas as pd

        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _calculate_efficiency_metrics_impl(**kwargs)
        logger.info("Executed calculate_efficiency_metrics tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "calculate_efficiency_metrics",
            data={"calculate_efficiency_metrics": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
