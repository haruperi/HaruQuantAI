"""Trades column definitions and evaluators (Trades/* cohort).

Description:
    Implements TradeColumnEvaluator and registers all 31 Trades column
    descriptors evaluating single trade metrics (Balance, Drawdown,
    Open/Close, Profit/Loss, MAE/MFE, Ticket, Symbol, etc.).

Purpose:
    FEAT-EXTEND-COLUMNS-TRADES: Concrete trade column evaluators.

Key Capabilities:
    - FR-columns-trades-evaluate: Evaluate trade row metrics against trade snapshots.

Python API Usage:
    from app.extend.columns.trades import TradeColumnEvaluator
    val = TradeColumnEvaluator.evaluate(
        "ProfitLoss", trade, index=1, running_balance=10500.0,
        running_dd_money=0.0, running_dd_pct=0.0
    )

CLI Usage:
    python -m app.cli extend columns trades --list
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.columns.base import (
    ColumnDescriptor,
    ColumnValueType,
    TradeRecord,
)

logger = get_logger(__name__)


def _tcol(
    cid: str, label: str, vtype: ColumnValueType, dec: int = 0
) -> ColumnDescriptor:
    return ColumnDescriptor(cid, "Trades", label, vtype, dec)


TRADE_COLUMNS: dict[str, ColumnDescriptor] = {
    "Balance": _tcol("Balance", "Balance", "MONEY", 2),
    "BarsInTrade": _tcol("BarsInTrade", "Bars in Trade", "INT", 0),
    "ClosePrice": _tcol("ClosePrice", "Close Price", "NUMBER", 5),
    "CloseTime": _tcol("CloseTime", "Close Time", "DATETIME", 0),
    "CloseType": _tcol("CloseType", "Close Type", "TEXT", 0),
    "CommSwap": _tcol("CommSwap", "Commission / Swap", "MONEY", 2),
    "Comment": _tcol("Comment", "Comment", "TEXT", 0),
    "Drawdown": _tcol("Drawdown", "Drawdown ($)", "MONEY", 2),
    "MAE": _tcol("MAE", "MAE ($)", "MONEY", 2),
    "MAEPips": _tcol("MAEPips", "MAE (pips)", "PIPS", 1),
    "MFE": _tcol("MFE", "MFE ($)", "MONEY", 2),
    "MFEPips": _tcol("MFEPips", "MFE (pips)", "PIPS", 1),
    "NumberOfTrade": _tcol("NumberOfTrade", "#", "INT", 0),
    "OpenPrice": _tcol("OpenPrice", "Open Price", "NUMBER", 5),
    "OpenTime": _tcol("OpenTime", "Open Time", "DATETIME", 0),
    "OriginalOpenPrice": _tcol("OriginalOpenPrice", "Orig Open Price", "NUMBER", 5),
    "OriginalOpenTime": _tcol("OriginalOpenTime", "Orig Open Time", "DATETIME", 0),
    "PTLevel": _tcol("PTLevel", "Profit Target", "NUMBER", 5),
    "PctDrawdown": _tcol("PctDrawdown", "Drawdown (%)", "PCT", 2),
    "ProfitLoss": _tcol("ProfitLoss", "Profit / Loss ($)", "MONEY", 2),
    "ProfitLossPct": _tcol("ProfitLossPct", "Profit / Loss (%)", "PCT", 2),
    "ProfitLossPips": _tcol("ProfitLossPips", "Profit / Loss (pips)", "PIPS", 1),
    "ResultName": _tcol("ResultName", "Result Name", "TEXT", 0),
    "SLLevel": _tcol("SLLevel", "Stop Loss", "NUMBER", 5),
    "SampleType": _tcol("SampleType", "Sample Type", "TEXT", 0),
    "Size": _tcol("Size", "Size", "NUMBER", 2),
    "SlippageInMoney": _tcol("SlippageInMoney", "Slippage ($)", "MONEY", 2),
    "Symbol": _tcol("Symbol", "Symbol", "TEXT", 0),
    "Ticket": _tcol("Ticket", "Ticket", "INT", 0),
    "TimeInTrade": _tcol("TimeInTrade", "Time in Trade", "TEXT", 0),
    "Type": _tcol("Type", "Type", "TEXT", 0),
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
        index: int,
        running_balance: float,
        running_dd_money: float,
        running_dd_pct: float,
    ) -> float | int | str | None:
        """Evaluate a specific column against the trade snapshot."""
        logger.debug(
            "FR-columns-trades-evaluate: evaluating col=%s idx=%d",
            column_id,
            index,
        )
        trade_map: dict[str, float | int | str | None] = {
            "NumberOfTrade": index,
            "Balance": round(running_balance, 2),
            "Drawdown": round(running_dd_money, 2),
            "PctDrawdown": round(running_dd_pct, 2),
            "Ticket": trade.ticket,
            "Symbol": trade.symbol,
            "Type": trade.type or trade.direction,
            "OpenTime": str(trade.open_time),
            "CloseTime": str(trade.close_time),
            "OpenPrice": trade.open_price,
            "ClosePrice": trade.close_price,
            "Size": trade.size,
            "ProfitLoss": round(trade.profit_loss, 2),
            "ProfitLossPct": round(trade.profit_loss_pct, 2),
            "ProfitLossPips": round(trade.profit_loss_pips, 1),
            "Comment": trade.comment,
            "MAE": round(trade.mae, 2),
            "MAEPips": round(trade.mae_pips, 1),
            "MFE": round(trade.mfe, 2),
            "MFEPips": round(trade.mfe_pips, 1),
            "SLLevel": trade.sl_level,
            "PTLevel": trade.pt_level,
            "SampleType": trade.sample_type,
            "BarsInTrade": trade.bars_in_trade,
            "TimeInTrade": trade.time_in_trade,
            "CommSwap": round(trade.comm_swap, 2),
            "SlippageInMoney": round(trade.slippage_money, 2),
            "ResultName": trade.result_name,
            "CloseType": "Exit",
            "OriginalOpenPrice": trade.open_price,
            "OriginalOpenTime": str(trade.open_time),
        }
        return trade_map.get(column_id)
