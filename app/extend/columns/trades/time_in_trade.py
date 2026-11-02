"""Time in Trade trade column snippet.

Description:
    Evaluates Time in Trade metric for single trade row in results tradelist.

Purpose:
    FEAT-EXTEND-COLUMNS-TRADES: Concrete trade column evaluators.

Key Capabilities:
    - FR-COLUMNS-TRADE-TIME-IN-TRADE:
      Extract Time in Trade for trade record.

Python API Usage:
    from app.extend.columns.trades.time_in_trade import (
        TimeInTrade,
    )
    col = TimeInTrade()
    val = col.get_value(trade, index=1, running_balance=10500.0)

CLI Usage:
    uv run pytest tests/extend/test_columns_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.columns.base import TradelistColumn, TradeRecord

logger = get_logger(__name__)


class TimeInTrade(TradelistColumn):
    """Evaluates Time in Trade metric for single trade row."""

    def __init__(self) -> None:
        super().__init__(
            column_id="TimeInTrade",
            label="Time in Trade",
            value_type="TEXT",
            decimals=0,
            source_ref="SQ.Columns.Trades.TimeInTrade",
        )

    @override
    def get_value(
        self,
        trade: TradeRecord,
        *,
        index: int = 1,
        running_balance: float = 0.0,
        running_dd_money: float = 0.0,
        running_dd_pct: float = 0.0,
    ) -> Any:
        """Extract Time in Trade value for single trade snapshot."""
        _ = (trade, index, running_balance, running_dd_money, running_dd_pct)
        logger.debug(
            "FR-COLUMNS-TRADE-%s: evaluating %s idx=%d",
            "TIME-IN-TRADE",
            "TimeInTrade",
            index,
        )
        return trade.time_in_trade
