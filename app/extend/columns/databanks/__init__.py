"""Databanks column definitions and evaluators (121 Databanks/* columns).

Description:
    Implements DatabankColumnEvaluator registering and evaluating all 121
    Databanks column descriptors across strategy performance snapshots.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANKS-EVALUATE: Evaluate 121 databank metric descriptors.

Python API Usage:
    from app.extend.columns.databanks import DatabankColumnEvaluator
    val = DatabankColumnEvaluator.evaluate("NetProfit", stats)

CLI Usage:
    uv run pytest tests/extend/test_columns_catalog.py --no-cov
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.columns.base import (
    ColumnDescriptor,
    DatabankColumn,
    StrategyStatsSnapshot,
)
from app.extend.columns.databanks.actual_dd import ActualDD
from app.extend.columns.databanks.actual_drawdown_pct import ActualDrawdownPct
from app.extend.columns.databanks.ahpr import AHPR
from app.extend.columns.databanks.ambiguous_trades import AmbiguousTrades
from app.extend.columns.databanks.ambiguous_trades_pct import AmbiguousTradesPct
from app.extend.columns.databanks.annual_pct_return import AnnualPctReturn
from app.extend.columns.databanks.annual_pct_return_dd_ratio import (
    AnnualPctReturnDDRatio,
)
from app.extend.columns.databanks.avg_abs_trade import AvgAbsTrade
from app.extend.columns.databanks.avg_bars_in_trade import AvgBarsInTrade
from app.extend.columns.databanks.avg_bars_loss import AvgBarsLoss
from app.extend.columns.databanks.avg_bars_win import AvgBarsWin
from app.extend.columns.databanks.avg_consec_losses import AvgConsecLosses
from app.extend.columns.databanks.avg_consec_wins import AvgConsecWins
from app.extend.columns.databanks.avg_drawdown import AvgDrawdown
from app.extend.columns.databanks.avg_loss import AvgLoss
from app.extend.columns.databanks.avg_parameters_stability import AvgParametersStability
from app.extend.columns.databanks.avg_pct_drawdown import AvgPctDrawdown
from app.extend.columns.databanks.avg_pct_profit_per_year import AvgPctProfitPerYear
from app.extend.columns.databanks.avg_profit_per_day import AvgProfitPerDay
from app.extend.columns.databanks.avg_profit_per_month import AvgProfitPerMonth
from app.extend.columns.databanks.avg_profit_per_year import AvgProfitPerYear
from app.extend.columns.databanks.avg_tr_stddev_ratio import AvgTrStddevRatio
from app.extend.columns.databanks.avg_trade import AvgTrade
from app.extend.columns.databanks.avg_trades_per_day import AvgTradesPerDay
from app.extend.columns.databanks.avg_trades_per_month import AvgTradesPerMonth
from app.extend.columns.databanks.avg_trades_per_year import AvgTradesPerYear
from app.extend.columns.databanks.avg_win import AvgWin
from app.extend.columns.databanks.backtest_duration import BacktestDuration
from app.extend.columns.databanks.best_wf import BestWF
from app.extend.columns.databanks.biggest_mae import BiggestMAE
from app.extend.columns.databanks.cagr import CAGR
from app.extend.columns.databanks.calmar_ratio import CalmarRatio
from app.extend.columns.databanks.commission import Commission
from app.extend.columns.databanks.complexity import Complexity
from app.extend.columns.databanks.date_generated import DateGenerated
from app.extend.columns.databanks.date_last_modified import DateLastModified
from app.extend.columns.databanks.degrees_of_freedom import DegreesOfFreedom
from app.extend.columns.databanks.drawdown import Drawdown
from app.extend.columns.databanks.drawdown_pct import DrawdownPct
from app.extend.columns.databanks.drawdown_pips import DrawdownPips
from app.extend.columns.databanks.edge_ratio_in_pips import EdgeRatioInPips
from app.extend.columns.databanks.efficiency import Efficiency
from app.extend.columns.databanks.entry_indicators import EntryIndicators
from app.extend.columns.databanks.equity_angle import EquityAngle
from app.extend.columns.databanks.equity_slope import EquitySlope
from app.extend.columns.databanks.exit_indicators import ExitIndicators
from app.extend.columns.databanks.exit_quality import ExitQuality
from app.extend.columns.databanks.expectancy import Expectancy
from app.extend.columns.databanks.exposure import Exposure
from app.extend.columns.databanks.exposure_position import ExposurePosition
from app.extend.columns.databanks.filters_result import FiltersResult
from app.extend.columns.databanks.fitness import Fitness
from app.extend.columns.databanks.gross_loss import GrossLoss
from app.extend.columns.databanks.gross_profit import GrossProfit
from app.extend.columns.databanks.initial_deposit import InitialDeposit
from app.extend.columns.databanks.kelly_formula import KellyFormula
from app.extend.columns.databanks.longest_trade import LongestTrade
from app.extend.columns.databanks.magic_number import MagicNumber
from app.extend.columns.databanks.max_consec_losses import MaxConsecLosses
from app.extend.columns.databanks.max_consec_wins import MaxConsecWins
from app.extend.columns.databanks.max_intraday_drawdown import MaxIntradayDrawdown
from app.extend.columns.databanks.max_loss import MaxLoss
from app.extend.columns.databanks.max_new_high_duration import MaxNewHighDuration
from app.extend.columns.databanks.max_profit import MaxProfit
from app.extend.columns.databanks.max_ts_intraday_drawdown import MaxTSIntradayDrawdown
from app.extend.columns.databanks.mini_equity_chart import MiniEquityChart
from app.extend.columns.databanks.n_symmetry import NSymmetry
from app.extend.columns.databanks.net_profit import NetProfit
from app.extend.columns.databanks.net_profit_in_pct import NetProfitInPct
from app.extend.columns.databanks.net_profit_in_pips import NetProfitInPips
from app.extend.columns.databanks.note import Note
from app.extend.columns.databanks.number_of_canceled import NumberOfCanceled
from app.extend.columns.databanks.number_of_losses import NumberOfLosses
from app.extend.columns.databanks.number_of_profits import NumberOfProfits
from app.extend.columns.databanks.number_of_trades import NumberOfTrades
from app.extend.columns.databanks.open_drawdown import OpenDrawdown
from app.extend.columns.databanks.open_drawdown_pct import OpenDrawdownPct
from app.extend.columns.databanks.outlier2 import Outlier2
from app.extend.columns.databanks.parameters import Parameters
from app.extend.columns.databanks.payout_ratio import PayoutRatio
from app.extend.columns.databanks.price_indicators import PriceIndicators
from app.extend.columns.databanks.profit_factor import ProfitFactor
from app.extend.columns.databanks.profitable_months import ProfitableMonths
from app.extend.columns.databanks.profitable_months_pct import ProfitableMonthsPct
from app.extend.columns.databanks.r_expectancy import RExpectancy
from app.extend.columns.databanks.r_expectancy_score import RExpectancyScore
from app.extend.columns.databanks.r_squared import RSquared
from app.extend.columns.databanks.recovery_factor import RecoveryFactor
from app.extend.columns.databanks.results_name import ResultsName
from app.extend.columns.databanks.return_dd_ratio import ReturnDDRatio
from app.extend.columns.databanks.return_open_dd_ratio import ReturnOpenDDRatio
from app.extend.columns.databanks.sharpe_ratio import SharpeRatio
from app.extend.columns.databanks.slippage_in_money import SlippageInMoney
from app.extend.columns.databanks.sqn import SQN
from app.extend.columns.databanks.sqn_score import SQNScore
from app.extend.columns.databanks.stability import Stability
from app.extend.columns.databanks.stability_sq3 import StabilitySQ3
from app.extend.columns.databanks.stagnation import Stagnation
from app.extend.columns.databanks.stagnation_pct import StagnationPct
from app.extend.columns.databanks.standard_dev import StandardDev
from app.extend.columns.databanks.symbol import Symbol
from app.extend.columns.databanks.symmetry import Symmetry
from app.extend.columns.databanks.time_frame import TimeFrame
from app.extend.columns.databanks.total_data_days import TotalDataDays
from app.extend.columns.databanks.total_data_months import TotalDataMonths
from app.extend.columns.databanks.total_data_years import TotalDataYears
from app.extend.columns.databanks.total_mfe import TotalMFE
from app.extend.columns.databanks.total_trading_days import TotalTradingDays
from app.extend.columns.databanks.total_trading_months import TotalTradingMonths
from app.extend.columns.databanks.total_trading_years import TotalTradingYears
from app.extend.columns.databanks.trades_symmetry import TradesSymmetry
from app.extend.columns.databanks.ts_index import TSIndex
from app.extend.columns.databanks.ts_win_loss_ratio import TSWinLossRatio
from app.extend.columns.databanks.ulcer_index import UlcerIndex
from app.extend.columns.databanks.ulcer_performance_index import UlcerPerformanceIndex
from app.extend.columns.databanks.win_loss_ratio import WinLossRatio
from app.extend.columns.databanks.winning_pct import WinningPct
from app.extend.columns.databanks.worst_parameters_stability import (
    WorstParametersStability,
)
from app.extend.columns.databanks.worst_year_profit import WorstYearProfit
from app.extend.columns.databanks.z_probability import ZProbability
from app.extend.columns.databanks.z_score import ZScore

logger = get_logger(__name__)

DATABANK_INSTANCES: dict[str, DatabankColumn] = {
    "AHPR": AHPR(),
    "ActualDD": ActualDD(),
    "ActualDrawdownPct": ActualDrawdownPct(),
    "AmbiguousTrades": AmbiguousTrades(),
    "AmbiguousTradesPct": AmbiguousTradesPct(),
    "AnnualPctReturn": AnnualPctReturn(),
    "AnnualPctReturnDDRatio": AnnualPctReturnDDRatio(),
    "AvgAbsTrade": AvgAbsTrade(),
    "AvgBarsInTrade": AvgBarsInTrade(),
    "AvgBarsLoss": AvgBarsLoss(),
    "AvgBarsWin": AvgBarsWin(),
    "AvgConsecLosses": AvgConsecLosses(),
    "AvgConsecWins": AvgConsecWins(),
    "AvgDrawdown": AvgDrawdown(),
    "AvgLoss": AvgLoss(),
    "AvgParametersStability": AvgParametersStability(),
    "AvgPctDrawdown": AvgPctDrawdown(),
    "AvgPctProfitPerYear": AvgPctProfitPerYear(),
    "AvgProfitPerDay": AvgProfitPerDay(),
    "AvgProfitPerMonth": AvgProfitPerMonth(),
    "AvgProfitPerYear": AvgProfitPerYear(),
    "AvgTrStddevRatio": AvgTrStddevRatio(),
    "AvgTrade": AvgTrade(),
    "AvgTradesPerDay": AvgTradesPerDay(),
    "AvgTradesPerMonth": AvgTradesPerMonth(),
    "AvgTradesPerYear": AvgTradesPerYear(),
    "AvgWin": AvgWin(),
    "BacktestDuration": BacktestDuration(),
    "BestWF": BestWF(),
    "BiggestMAE": BiggestMAE(),
    "CAGR": CAGR(),
    "CalmarRatio": CalmarRatio(),
    "Commission": Commission(),
    "Complexity": Complexity(),
    "DateGenerated": DateGenerated(),
    "DateLastModified": DateLastModified(),
    "DegreesOfFreedom": DegreesOfFreedom(),
    "Drawdown": Drawdown(),
    "DrawdownPct": DrawdownPct(),
    "DrawdownPips": DrawdownPips(),
    "EdgeRatioInPips": EdgeRatioInPips(),
    "Efficiency": Efficiency(),
    "EntryIndicators": EntryIndicators(),
    "EquityAngle": EquityAngle(),
    "EquitySlope": EquitySlope(),
    "ExitIndicators": ExitIndicators(),
    "ExitQuality": ExitQuality(),
    "Expectancy": Expectancy(),
    "Exposure": Exposure(),
    "ExposurePosition": ExposurePosition(),
    "FiltersResult": FiltersResult(),
    "Fitness": Fitness(),
    "GrossLoss": GrossLoss(),
    "GrossProfit": GrossProfit(),
    "InitialDeposit": InitialDeposit(),
    "KellyFormula": KellyFormula(),
    "LongestTrade": LongestTrade(),
    "MagicNumber": MagicNumber(),
    "MaxConsecLosses": MaxConsecLosses(),
    "MaxConsecWins": MaxConsecWins(),
    "MaxIntradayDrawdown": MaxIntradayDrawdown(),
    "MaxLoss": MaxLoss(),
    "MaxNewHighDuration": MaxNewHighDuration(),
    "MaxProfit": MaxProfit(),
    "MaxTSIntradayDrawdown": MaxTSIntradayDrawdown(),
    "MiniEquityChart": MiniEquityChart(),
    "NSymmetry": NSymmetry(),
    "NetProfit": NetProfit(),
    "NetProfitInPct": NetProfitInPct(),
    "NetProfitInPips": NetProfitInPips(),
    "Note": Note(),
    "NumberOfCanceled": NumberOfCanceled(),
    "NumberOfLosses": NumberOfLosses(),
    "NumberOfProfits": NumberOfProfits(),
    "NumberOfTrades": NumberOfTrades(),
    "OpenDrawdown": OpenDrawdown(),
    "OpenDrawdownPct": OpenDrawdownPct(),
    "Outlier2": Outlier2(),
    "Parameters": Parameters(),
    "PayoutRatio": PayoutRatio(),
    "PriceIndicators": PriceIndicators(),
    "ProfitFactor": ProfitFactor(),
    "ProfitableMonths": ProfitableMonths(),
    "ProfitableMonthsPct": ProfitableMonthsPct(),
    "RExpectancy": RExpectancy(),
    "RExpectancyScore": RExpectancyScore(),
    "RSquared": RSquared(),
    "RecoveryFactor": RecoveryFactor(),
    "ResultsName": ResultsName(),
    "ReturnDDRatio": ReturnDDRatio(),
    "ReturnOpenDDRatio": ReturnOpenDDRatio(),
    "SQN": SQN(),
    "SQNScore": SQNScore(),
    "SharpeRatio": SharpeRatio(),
    "SlippageInMoney": SlippageInMoney(),
    "Stability": Stability(),
    "StabilitySQ3": StabilitySQ3(),
    "Stagnation": Stagnation(),
    "StagnationPct": StagnationPct(),
    "StandardDev": StandardDev(),
    "Symbol": Symbol(),
    "Symmetry": Symmetry(),
    "TSIndex": TSIndex(),
    "TSWinLossRatio": TSWinLossRatio(),
    "TimeFrame": TimeFrame(),
    "TotalDataDays": TotalDataDays(),
    "TotalDataMonths": TotalDataMonths(),
    "TotalDataYears": TotalDataYears(),
    "TotalMFE": TotalMFE(),
    "TotalTradingDays": TotalTradingDays(),
    "TotalTradingMonths": TotalTradingMonths(),
    "TotalTradingYears": TotalTradingYears(),
    "TradesSymmetry": TradesSymmetry(),
    "UlcerIndex": UlcerIndex(),
    "UlcerPerformanceIndex": UlcerPerformanceIndex(),
    "WinLossRatio": WinLossRatio(),
    "WinningPct": WinningPct(),
    "WorstParametersStability": WorstParametersStability(),
    "WorstYearProfit": WorstYearProfit(),
    "ZProbability": ZProbability(),
    "ZScore": ZScore(),
}

DATABANK_COLUMNS: dict[str, ColumnDescriptor] = {
    k: v.descriptor for k, v in DATABANK_INSTANCES.items()
}


class DatabankColumnEvaluator:
    """Evaluates Databank column metrics enforcing finite zero-division boundaries."""

    @classmethod
    def list_descriptors(cls) -> tuple[ColumnDescriptor, ...]:
        """List all registered Databanks column descriptors."""
        return tuple(DATABANK_COLUMNS.values())

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
            "FR-COLUMNS-DATABANKS-EVALUATE: col=%s sample=%s dir=%s",
            column_id,
            sample_type,
            direction,
        )
        col = DATABANK_INSTANCES.get(column_id)
        if col is None:
            raw = stats.metrics.get(column_id, 0.0)
            return float(raw) if isinstance(raw, (int, float)) else 0.0
        return col.compute(stats, sample_type=sample_type, direction=direction)


__all__ = [
    "AHPR",
    "CAGR",
    "DATABANK_COLUMNS",
    "DATABANK_INSTANCES",
    "SQN",
    "ActualDD",
    "ActualDrawdownPct",
    "AmbiguousTrades",
    "AmbiguousTradesPct",
    "AnnualPctReturn",
    "AnnualPctReturnDDRatio",
    "AvgAbsTrade",
    "AvgBarsInTrade",
    "AvgBarsLoss",
    "AvgBarsWin",
    "AvgConsecLosses",
    "AvgConsecWins",
    "AvgDrawdown",
    "AvgLoss",
    "AvgParametersStability",
    "AvgPctDrawdown",
    "AvgPctProfitPerYear",
    "AvgProfitPerDay",
    "AvgProfitPerMonth",
    "AvgProfitPerYear",
    "AvgTrStddevRatio",
    "AvgTrade",
    "AvgTradesPerDay",
    "AvgTradesPerMonth",
    "AvgTradesPerYear",
    "AvgWin",
    "BacktestDuration",
    "BestWF",
    "BiggestMAE",
    "CalmarRatio",
    "Commission",
    "Complexity",
    "DatabankColumnEvaluator",
    "DateGenerated",
    "DateLastModified",
    "DegreesOfFreedom",
    "Drawdown",
    "DrawdownPct",
    "DrawdownPips",
    "EdgeRatioInPips",
    "Efficiency",
    "EntryIndicators",
    "EquityAngle",
    "EquitySlope",
    "ExitIndicators",
    "ExitQuality",
    "Expectancy",
    "Exposure",
    "ExposurePosition",
    "FiltersResult",
    "Fitness",
    "GrossLoss",
    "GrossProfit",
    "InitialDeposit",
    "KellyFormula",
    "LongestTrade",
    "MagicNumber",
    "MaxConsecLosses",
    "MaxConsecWins",
    "MaxIntradayDrawdown",
    "MaxLoss",
    "MaxNewHighDuration",
    "MaxProfit",
    "MaxTSIntradayDrawdown",
    "MiniEquityChart",
    "NSymmetry",
    "NetProfit",
    "NetProfitInPct",
    "NetProfitInPips",
    "Note",
    "NumberOfCanceled",
    "NumberOfLosses",
    "NumberOfProfits",
    "NumberOfTrades",
    "OpenDrawdown",
    "OpenDrawdownPct",
    "Outlier2",
    "Parameters",
    "PayoutRatio",
    "PriceIndicators",
    "ProfitFactor",
    "ProfitableMonths",
    "ProfitableMonthsPct",
    "RExpectancy",
    "RExpectancyScore",
    "RSquared",
    "RecoveryFactor",
    "ResultsName",
    "ReturnDDRatio",
    "ReturnOpenDDRatio",
    "SQNScore",
    "SharpeRatio",
    "SlippageInMoney",
    "Stability",
    "StabilitySQ3",
    "Stagnation",
    "StagnationPct",
    "StandardDev",
    "Symbol",
    "Symmetry",
    "TSIndex",
    "TSWinLossRatio",
    "TimeFrame",
    "TotalDataDays",
    "TotalDataMonths",
    "TotalDataYears",
    "TotalMFE",
    "TotalTradingDays",
    "TotalTradingMonths",
    "TotalTradingYears",
    "TradesSymmetry",
    "UlcerIndex",
    "UlcerPerformanceIndex",
    "WinLossRatio",
    "WinningPct",
    "WorstParametersStability",
    "WorstYearProfit",
    "ZProbability",
    "ZScore",
]
