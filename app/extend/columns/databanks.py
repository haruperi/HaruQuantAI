"""Databanks column definitions and evaluators (122 Databanks/* columns).

Description:
    Implements DatabankColumnEvaluator registering and evaluating all 121
    Databanks column descriptors across strategy performance snapshots,
    enforcing zero-trade and zero-denominator boundary safety rules.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-columns-databanks-evaluate: Evaluate 121 databank metric descriptors.

Python API Usage:
    from app.extend.columns.databanks import DatabankColumnEvaluator
    val = DatabankColumnEvaluator.evaluate("NetProfit", stats)

CLI Usage:
    python -m app.cli extend columns databanks --list
"""

from __future__ import annotations

import math

from app.core.host.logging import get_logger
from app.extend.columns.base import (
    ColumnDescriptor,
    ColumnValueType,
    StrategyStatsSnapshot,
)

logger = get_logger(__name__)


def _col(
    cid: str,
    label: str,
    vtype: ColumnValueType = "NUMBER",
    dec: int = 2,
    *,
    maxi: bool | None = None,
) -> ColumnDescriptor:
    return ColumnDescriptor(cid, "Databanks", label, vtype, dec, maximize=maxi)


# Complete registration of all 121 Databanks columns
DATABANK_COLUMNS: dict[str, ColumnDescriptor] = {
    "AHPR": _col("AHPR", "AHPR", "PCT", 2, maxi=True),
    "ActualDD": _col("ActualDD", "Actual DD ($)", "MONEY", 2, maxi=False),
    "ActualDrawdownPct": _col(
        "ActualDrawdownPct", "Actual DD (%)", "PCT", 2, maxi=False
    ),
    "AmbiguousTrades": _col(
        "AmbiguousTrades", "Ambiguous Trades", "INT", 0, maxi=False
    ),
    "AmbiguousTradesPct": _col(
        "AmbiguousTradesPct", "Ambiguous %", "PCT", 2, maxi=False
    ),
    "AnnualPctReturn": _col(
        "AnnualPctReturn", "Annual Return (%)", "PCT", 2, maxi=True
    ),
    "AnnualPctReturnDDRatio": _col(
        "AnnualPctReturnDDRatio", "Ann Ret / DD", "NUMBER", 2, maxi=True
    ),
    "AvgAbsTrade": _col("AvgAbsTrade", "Avg Abs Trade", "MONEY", 2),
    "AvgBarsInTrade": _col("AvgBarsInTrade", "Avg Bars in Trade", "NUMBER", 1),
    "AvgBarsLoss": _col("AvgBarsLoss", "Avg Bars Loss", "NUMBER", 1),
    "AvgBarsWin": _col("AvgBarsWin", "Avg Bars Win", "NUMBER", 1),
    "AvgConsecLosses": _col(
        "AvgConsecLosses", "Avg Consec Losses", "NUMBER", 1, maxi=False
    ),
    "AvgConsecWins": _col("AvgConsecWins", "Avg Consec Wins", "NUMBER", 1, maxi=True),
    "AvgDrawdown": _col("AvgDrawdown", "Avg Drawdown ($)", "MONEY", 2, maxi=False),
    "AvgLoss": _col("AvgLoss", "Avg Loss ($)", "MONEY", 2, maxi=False),
    "AvgParametersStability": _col(
        "AvgParametersStability", "Avg Param Stab", "PCT", 2, maxi=True
    ),
    "AvgPctDrawdown": _col("AvgPctDrawdown", "Avg DD (%)", "PCT", 2, maxi=False),
    "AvgPctProfitPerYear": _col(
        "AvgPctProfitPerYear", "Avg % / Year", "PCT", 2, maxi=True
    ),
    "AvgProfitPerDay": _col(
        "AvgProfitPerDay", "Avg Profit / Day", "MONEY", 2, maxi=True
    ),
    "AvgProfitPerMonth": _col(
        "AvgProfitPerMonth", "Avg Profit / Month", "MONEY", 2, maxi=True
    ),
    "AvgProfitPerYear": _col(
        "AvgProfitPerYear", "Avg Profit / Year", "MONEY", 2, maxi=True
    ),
    "AvgTrStddevRatio": _col(
        "AvgTrStddevRatio", "Avg Tr / StdDev", "NUMBER", 2, maxi=True
    ),
    "AvgTrade": _col("AvgTrade", "Avg Trade ($)", "MONEY", 2, maxi=True),
    "AvgTradesPerDay": _col("AvgTradesPerDay", "Avg Trades / Day", "NUMBER", 1),
    "AvgTradesPerMonth": _col("AvgTradesPerMonth", "Avg Trades / Month", "NUMBER", 1),
    "AvgTradesPerYear": _col("AvgTradesPerYear", "Avg Trades / Year", "NUMBER", 1),
    "AvgWin": _col("AvgWin", "Avg Win ($)", "MONEY", 2, maxi=True),
    "BacktestDuration": _col("BacktestDuration", "Duration", "TEXT", 0),
    "BestWF": _col("BestWF", "Best WF", "NUMBER", 2, maxi=True),
    "BiggestMAE": _col("BiggestMAE", "Biggest MAE ($)", "MONEY", 2, maxi=False),
    "CAGR": _col("CAGR", "CAGR (%)", "PCT", 2, maxi=True),
    "CalmarRatio": _col("CalmarRatio", "Calmar Ratio", "NUMBER", 2, maxi=True),
    "Commission": _col("Commission", "Commission ($)", "MONEY", 2, maxi=False),
    "Complexity": _col("Complexity", "Complexity", "INT", 0, maxi=False),
    "DateGenerated": _col("DateGenerated", "Date Generated", "DATETIME", 0),
    "DateLastModified": _col("DateLastModified", "Date Modified", "DATETIME", 0),
    "DegreesOfFreedom": _col(
        "DegreesOfFreedom", "Degrees of Freedom", "INT", 0, maxi=True
    ),
    "Drawdown": _col("Drawdown", "Drawdown ($)", "MONEY", 2, maxi=False),
    "DrawdownPct": _col("DrawdownPct", "Drawdown (%)", "PCT", 2, maxi=False),
    "DrawdownPips": _col("DrawdownPips", "Drawdown (pips)", "PIPS", 1, maxi=False),
    "EdgeRatioInPips": _col("EdgeRatioInPips", "Edge Ratio", "NUMBER", 2, maxi=True),
    "Efficiency": _col("Efficiency", "Efficiency", "PCT", 2, maxi=True),
    "EntryIndicators": _col("EntryIndicators", "Entry Indicators", "TEXT", 0),
    "EquityAngle": _col("EquityAngle", "Equity Angle", "NUMBER", 1, maxi=True),
    "EquitySlope": _col("EquitySlope", "Equity Slope", "NUMBER", 2, maxi=True),
    "ExitIndicators": _col("ExitIndicators", "Exit Indicators", "TEXT", 0),
    "ExitQuality": _col("ExitQuality", "Exit Quality", "PCT", 2, maxi=True),
    "Expectancy": _col("Expectancy", "Expectancy ($)", "MONEY", 2, maxi=True),
    "Exposure": _col("Exposure", "Exposure (%)", "PCT", 2, maxi=False),
    "ExposurePosition": _col("ExposurePosition", "Exposure Position", "NUMBER", 2),
    "FiltersResult": _col("FiltersResult", "Filters Result", "TEXT", 0),
    "Fitness": _col("Fitness", "Fitness", "NUMBER", 2, maxi=True),
    "GrossLoss": _col("GrossLoss", "Gross Loss ($)", "MONEY", 2, maxi=False),
    "GrossProfit": _col("GrossProfit", "Gross Profit ($)", "MONEY", 2, maxi=True),
    "InitialDeposit": _col("InitialDeposit", "Initial Deposit", "MONEY", 2),
    "KellyFormula": _col("KellyFormula", "Kelly Formula", "PCT", 2, maxi=True),
    "LongestTrade": _col("LongestTrade", "Longest Trade", "TEXT", 0),
    "MagicNumber": _col("MagicNumber", "Magic Number", "INT", 0),
    "MaxConsecLosses": _col(
        "MaxConsecLosses", "Max Consec Losses", "INT", 0, maxi=False
    ),
    "MaxConsecWins": _col("MaxConsecWins", "Max Consec Wins", "INT", 0, maxi=True),
    "MaxIntradayDrawdown": _col(
        "MaxIntradayDrawdown", "Max Intra DD", "MONEY", 2, maxi=False
    ),
    "MaxLoss": _col("MaxLoss", "Max Loss ($)", "MONEY", 2, maxi=False),
    "MaxNewHighDuration": _col(
        "MaxNewHighDuration", "Max Stagnation", "INT", 0, maxi=False
    ),
    "MaxProfit": _col("MaxProfit", "Max Profit ($)", "MONEY", 2, maxi=True),
    "MaxTSIntradayDrawdown": _col(
        "MaxTSIntradayDrawdown", "Max TS Intra DD", "MONEY", 2, maxi=False
    ),
    "MiniEquityChart": _col("MiniEquityChart", "Mini Equity", "CHART", 0),
    "NSymmetry": _col("NSymmetry", "N-Symmetry", "NUMBER", 2),
    "NetProfit": _col("NetProfit", "Net Profit ($)", "MONEY", 2, maxi=True),
    "NetProfitInPct": _col("NetProfitInPct", "Net Profit (%)", "PCT", 2, maxi=True),
    "NetProfitInPips": _col(
        "NetProfitInPips", "Net Profit (pips)", "PIPS", 1, maxi=True
    ),
    "Note": _col("Note", "Note", "TEXT", 0),
    "NumberOfCanceled": _col("NumberOfCanceled", "Canceled Orders", "INT", 0),
    "NumberOfLosses": _col("NumberOfLosses", "Loss Trades", "INT", 0, maxi=False),
    "NumberOfProfits": _col("NumberOfProfits", "Win Trades", "INT", 0, maxi=True),
    "NumberOfTrades": _col("NumberOfTrades", "Total Trades", "INT", 0, maxi=True),
    "OpenDrawdown": _col("OpenDrawdown", "Open DD ($)", "MONEY", 2, maxi=False),
    "OpenDrawdownPct": _col("OpenDrawdownPct", "Open DD (%)", "PCT", 2, maxi=False),
    "Outlier2": _col("Outlier2", "Outlier Factor", "NUMBER", 2, maxi=False),
    "Parameters": _col("Parameters", "Parameters", "TEXT", 0),
    "PayoutRatio": _col("PayoutRatio", "Payout Ratio", "NUMBER", 2, maxi=True),
    "PriceIndicators": _col("PriceIndicators", "Price Indicators", "TEXT", 0),
    "ProfitFactor": _col("ProfitFactor", "Profit Factor", "NUMBER", 2, maxi=True),
    "ProfitableMonths": _col(
        "ProfitableMonths", "Profitable Months", "INT", 0, maxi=True
    ),
    "ProfitableMonthsPct": _col(
        "ProfitableMonthsPct", "Profitable Months %", "PCT", 2, maxi=True
    ),
    "RExpectancy": _col("RExpectancy", "R-Expectancy", "NUMBER", 2, maxi=True),
    "RExpectancyScore": _col(
        "RExpectancyScore", "R-Expectancy Score", "NUMBER", 2, maxi=True
    ),
    "RSquared": _col("RSquared", "R^2 Stability", "NUMBER", 2, maxi=True),
    "RecoveryFactor": _col("RecoveryFactor", "Recovery Factor", "NUMBER", 2, maxi=True),
    "ResultsName": _col("ResultsName", "Strategy Name", "TEXT", 0),
    "ReturnDDRatio": _col("ReturnDDRatio", "Return / DD", "NUMBER", 2, maxi=True),
    "ReturnOpenDDRatio": _col(
        "ReturnOpenDDRatio", "Return / Open DD", "NUMBER", 2, maxi=True
    ),
    "SQN": _col("SQN", "SQN", "NUMBER", 2, maxi=True),
    "SQNScore": _col("SQNScore", "SQN Score", "NUMBER", 2, maxi=True),
    "SharpeRatio": _col("SharpeRatio", "Sharpe Ratio", "NUMBER", 2, maxi=True),
    "SlippageInMoney": _col("SlippageInMoney", "Slippage ($)", "MONEY", 2, maxi=False),
    "Stability": _col("Stability", "Stability", "NUMBER", 2, maxi=True),
    "StabilitySQ3": _col("StabilitySQ3", "Stability SQ3", "NUMBER", 2, maxi=True),
    "Stagnation": _col("Stagnation", "Stagnation (days)", "INT", 0, maxi=False),
    "StagnationPct": _col("StagnationPct", "Stagnation (%)", "PCT", 2, maxi=False),
    "StandardDev": _col("StandardDev", "Standard Deviation", "NUMBER", 2),
    "Symbol": _col("Symbol", "Symbol", "TEXT", 0),
    "Symmetry": _col("Symmetry", "Symmetry", "NUMBER", 2),
    "TSIndex": _col("TSIndex", "TS Index", "NUMBER", 2),
    "TSWinLossRatio": _col("TSWinLossRatio", "TS Win/Loss Ratio", "NUMBER", 2),
    "TimeFrame": _col("TimeFrame", "Timeframe", "TEXT", 0),
    "TotalDataDays": _col("TotalDataDays", "Data Days", "INT", 0),
    "TotalDataMonths": _col("TotalDataMonths", "Data Months", "INT", 0),
    "TotalDataYears": _col("TotalDataYears", "Data Years", "NUMBER", 1),
    "TotalMFE": _col("TotalMFE", "Total MFE ($)", "MONEY", 2, maxi=True),
    "TotalTradingDays": _col("TotalTradingDays", "Trading Days", "INT", 0),
    "TotalTradingMonths": _col("TotalTradingMonths", "Trading Months", "INT", 0),
    "TotalTradingYears": _col("TotalTradingYears", "Trading Years", "NUMBER", 1),
    "TradesSymmetry": _col("TradesSymmetry", "Trades Symmetry", "NUMBER", 2),
    "UlcerIndex": _col("UlcerIndex", "Ulcer Index", "NUMBER", 2, maxi=False),
    "UlcerPerformanceIndex": _col(
        "UlcerPerformanceIndex", "UPI", "NUMBER", 2, maxi=True
    ),
    "WinLossRatio": _col("WinLossRatio", "Win / Loss Ratio", "NUMBER", 2, maxi=True),
    "WinningPct": _col("WinningPct", "Winning (%)", "PCT", 2, maxi=True),
    "WorstParametersStability": _col(
        "WorstParametersStability", "Worst Param Stab", "PCT", 2, maxi=True
    ),
    "WorstYearProfit": _col(
        "WorstYearProfit", "Worst Year Profit", "MONEY", 2, maxi=True
    ),
    "ZProbability": _col("ZProbability", "Z-Probability", "PCT", 2),
    "ZScore": _col("ZScore", "Z-Score", "NUMBER", 2),
}


class DatabankColumnEvaluator:
    """Evaluates Databank column metrics enforcing finite zero-division boundaries."""

    @classmethod
    def list_descriptors(cls) -> tuple[ColumnDescriptor, ...]:
        """List all registered Databanks column descriptors."""
        return tuple(DATABANK_COLUMNS.values())

    @classmethod
    def _eval_text(cls, column_id: str, stats: StrategyStatsSnapshot) -> str | None:
        text_map: dict[str, str] = {
            "ResultsName": stats.strategy_name
            or str(stats.metrics.get("strategy_name", "")),
            "Symbol": str(stats.metrics.get("symbol", "EURUSD")),
            "TimeFrame": str(stats.metrics.get("timeframe", "H1")),
            "Note": str(stats.metrics.get("note", "")) or "",
            "Parameters": str(stats.parameters),
            "MiniEquityChart": "[MiniChart]",
        }
        if column_id in text_map:
            return text_map[column_id]
        if column_id in {
            "BacktestDuration",
            "LongestTrade",
            "EntryIndicators",
            "ExitIndicators",
            "PriceIndicators",
            "FiltersResult",
        }:
            return str(stats.metrics.get(column_id, ""))
        return None

    @classmethod
    def _calc_max_dd(
        cls, pls: list[float], initial_deposit: float, metric_dd: float
    ) -> float:
        peak = initial_deposit
        curr_bal = initial_deposit
        max_dd = 0.0
        for p in pls:
            curr_bal += p
            peak = max(peak, curr_bal)
            dd = peak - curr_bal
            max_dd = max(max_dd, dd)
        if not max_dd and metric_dd:
            return abs(metric_dd)
        return max_dd

    @classmethod
    def _eval_numeric(
        cls,
        column_id: str,
        stats: StrategyStatsSnapshot,
        pls: list[float],
        *,
        gross_profit: float,
        gross_loss: float,
        max_dd: float,
    ) -> float | int:
        n_trades = len(pls)
        net_profit = sum(pls) if pls else float(stats.metrics.get("net_profit", 0.0))
        n_wins = sum(1 for p in pls if p > 0.0)
        n_losses = sum(1 for p in pls if p < 0.0)
        dep = stats.initial_deposit

        avg_win = (gross_profit / n_wins) if n_wins > 0 else 0.0
        avg_loss = abs(gross_loss / n_losses) if n_losses > 0 else 0.0
        win_loss = (avg_win / avg_loss) if avg_loss > 0 else avg_win

        if abs(gross_loss) == 0.0:
            profit_factor = round(gross_profit, 2) if gross_profit > 0.0 else 0.0
        else:
            profit_factor = gross_profit / abs(gross_loss)

        if max_dd == 0.0:
            ret_dd = round(net_profit, 2) if net_profit > 0.0 else 0.0
        else:
            ret_dd = net_profit / max_dd

        direct_map: dict[str, float | int] = {
            "NumberOfTrades": n_trades or int(stats.metrics.get("trades_count", 0)),
            "NumberOfProfits": n_wins,
            "NumberOfLosses": n_losses,
            "NetProfit": net_profit,
            "GrossProfit": gross_profit,
            "GrossLoss": gross_loss,
            "InitialDeposit": dep,
            "ProfitFactor": profit_factor,
            "ReturnDDRatio": ret_dd,
            "RecoveryFactor": ret_dd,
            "WinningPct": (n_wins / n_trades * 100.0) if n_trades > 0 else 0.0,
            "AvgTrade": (net_profit / n_trades) if n_trades > 0 else 0.0,
            "MaxProfit": max(pls) if pls else 0.0,
            "MaxLoss": min(pls) if pls else 0.0,
            "AvgWin": avg_win,
            "AvgLoss": (gross_loss / n_losses) if n_losses > 0 else 0.0,
            "WinLossRatio": win_loss,
            "Drawdown": max_dd,
            "DrawdownPct": (max_dd / dep * 100.0) if dep > 0 else 0.0,
            "NetProfitInPct": (net_profit / dep * 100.0) if dep > 0 else 0.0,
        }

        if column_id in direct_map:
            return direct_map[column_id]

        raw_val = stats.metrics.get(column_id, 0.0)
        return float(raw_val) if isinstance(raw_val, (int, float)) else 0.0

    @classmethod
    def evaluate(
        cls,
        column_id: str,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate a databank column against strategy stats snapshot."""
        logger.debug(
            "FR-columns-databanks-evaluate: col=%s sample=%s dir=%s",
            column_id,
            sample_type,
            direction,
        )
        text_val = cls._eval_text(column_id, stats)
        if text_val is not None:
            return text_val

        # Filter trades
        target_dir = direction.upper()
        trades = [
            t
            for t in stats.trades
            if (
                sample_type == "FullSample"
                or t.get("sample_type", "FullSample") == sample_type
            )
            and (
                direction == "Both"
                or str(t.get("type", t.get("direction", "BUY"))).upper() == target_dir
            )
        ]

        if not trades and not stats.metrics:
            return stats.initial_deposit if column_id == "InitialDeposit" else 0.0

        pls = [float(t.get("profit_loss", t.get("pnl", 0.0))) for t in trades]
        gross_profit = sum(p for p in pls if p > 0.0)
        gross_loss = sum(p for p in pls if p < 0.0)
        metric_dd = float(stats.metrics.get("drawdown", 0.0))
        max_dd = cls._calc_max_dd(pls, stats.initial_deposit, metric_dd)

        num_val = cls._eval_numeric(
            column_id,
            stats,
            pls,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            max_dd=max_dd,
        )
        if isinstance(num_val, float):
            if not math.isfinite(num_val):
                num_val = 0.0
            decimals = DATABANK_COLUMNS.get(
                column_id, ColumnDescriptor("", "Databanks", "", "NUMBER", 2)
            ).decimals
            return round(num_val, decimals)

        return num_val
