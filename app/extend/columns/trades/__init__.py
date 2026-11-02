"""Trades column definitions and evaluators (Trades/* cohort).

Description:
    Implements TradeColumnEvaluator and registers all 31 Trades column
    descriptors evaluating single trade metrics.

Purpose:
    FEAT-EXTEND-COLUMNS-TRADES: Concrete trade column evaluators.

Key Capabilities:
    - FR-COLUMNS-TRADES-EVALUATE: Evaluate trade row metrics against trade snapshots.

Python API Usage:
    from app.extend.columns.trades import TradeColumnEvaluator
    val = TradeColumnEvaluator.evaluate("ProfitLoss", trade, index=1)

CLI Usage:
    uv run pytest tests/extend/test_columns_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.extend.columns.base import (
    ColumnDescriptor,
    TradelistColumn,
    TradeRecord,
)
from app.extend.columns.trades.balance import Balance
from app.extend.columns.trades.bars_in_trade import BarsInTrade
from app.extend.columns.trades.close_price import ClosePrice
from app.extend.columns.trades.close_time import CloseTime
from app.extend.columns.trades.close_type import CloseType
from app.extend.columns.trades.comm_swap import CommSwap
from app.extend.columns.trades.comment import Comment
from app.extend.columns.trades.drawdown import Drawdown
from app.extend.columns.trades.mae import MAE
from app.extend.columns.trades.mae_pips import MAEPips
from app.extend.columns.trades.mfe import MFE
from app.extend.columns.trades.mfe_pips import MFEPips
from app.extend.columns.trades.number_of_trade import NumberOfTrade
from app.extend.columns.trades.open_price import OpenPrice
from app.extend.columns.trades.open_time import OpenTime
from app.extend.columns.trades.original_open_price import OriginalOpenPrice
from app.extend.columns.trades.original_open_time import OriginalOpenTime
from app.extend.columns.trades.pct_drawdown import PctDrawdown
from app.extend.columns.trades.profit_loss import ProfitLoss
from app.extend.columns.trades.profit_loss_pct import ProfitLossPct
from app.extend.columns.trades.profit_loss_pips import ProfitLossPips
from app.extend.columns.trades.pt_level import PTLevel
from app.extend.columns.trades.result_name import ResultName
from app.extend.columns.trades.sample_type import SampleType
from app.extend.columns.trades.size import Size
from app.extend.columns.trades.sl_level import SLLevel
from app.extend.columns.trades.slippage_in_money import SlippageInMoney
from app.extend.columns.trades.symbol import Symbol
from app.extend.columns.trades.ticket import Ticket
from app.extend.columns.trades.time_in_trade import TimeInTrade
from app.extend.columns.trades.type import Type

logger = get_logger(__name__)

TRADE_INSTANCES: dict[str, TradelistColumn] = {
    "Balance": Balance(),
    "BarsInTrade": BarsInTrade(),
    "ClosePrice": ClosePrice(),
    "CloseTime": CloseTime(),
    "CloseType": CloseType(),
    "CommSwap": CommSwap(),
    "Comment": Comment(),
    "Drawdown": Drawdown(),
    "MAE": MAE(),
    "MAEPips": MAEPips(),
    "MFE": MFE(),
    "MFEPips": MFEPips(),
    "NumberOfTrade": NumberOfTrade(),
    "OpenPrice": OpenPrice(),
    "OpenTime": OpenTime(),
    "OriginalOpenPrice": OriginalOpenPrice(),
    "OriginalOpenTime": OriginalOpenTime(),
    "PTLevel": PTLevel(),
    "PctDrawdown": PctDrawdown(),
    "ProfitLoss": ProfitLoss(),
    "ProfitLossPct": ProfitLossPct(),
    "ProfitLossPips": ProfitLossPips(),
    "ResultName": ResultName(),
    "SLLevel": SLLevel(),
    "SampleType": SampleType(),
    "Size": Size(),
    "SlippageInMoney": SlippageInMoney(),
    "Symbol": Symbol(),
    "Ticket": Ticket(),
    "TimeInTrade": TimeInTrade(),
    "Type": Type(),
}

TRADE_COLUMNS: dict[str, ColumnDescriptor] = {
    k: v.descriptor for k, v in TRADE_INSTANCES.items()
}


class TradeColumnEvaluator:
    """Evaluates single-trade column values for the Results Trade List."""

    @classmethod
    def list_descriptors(cls) -> tuple[ColumnDescriptor, ...]:
        """List all registered Trades column descriptors."""
        return tuple(TRADE_COLUMNS.values())

    @classmethod
    def evaluate(
        cls,
        column_id: str,
        trade: TradeRecord,
        *,
        index: int = 1,
        running_balance: float = 0.0,
        running_dd_money: float = 0.0,
        running_dd_pct: float = 0.0,
    ) -> Any:
        """Evaluate a specific column against the trade snapshot."""
        logger.debug(
            "FR-COLUMNS-TRADES-EVALUATE: evaluating col=%s idx=%d",
            column_id,
            index,
        )
        col = TRADE_INSTANCES.get(column_id)
        if col is None:
            return None
        return col.get_value(
            trade,
            index=index,
            running_balance=running_balance,
            running_dd_money=running_dd_money,
            running_dd_pct=running_dd_pct,
        )


__all__ = [
    "MAE",
    "MFE",
    "TRADE_COLUMNS",
    "TRADE_INSTANCES",
    "Balance",
    "BarsInTrade",
    "ClosePrice",
    "CloseTime",
    "CloseType",
    "CommSwap",
    "Comment",
    "Drawdown",
    "MAEPips",
    "MFEPips",
    "NumberOfTrade",
    "OpenPrice",
    "OpenTime",
    "OriginalOpenPrice",
    "OriginalOpenTime",
    "PTLevel",
    "PctDrawdown",
    "ProfitLoss",
    "ProfitLossPct",
    "ProfitLossPips",
    "ResultName",
    "SLLevel",
    "SampleType",
    "Size",
    "SlippageInMoney",
    "Symbol",
    "Ticket",
    "TimeInTrade",
    "TradeColumnEvaluator",
    "Type",
]
