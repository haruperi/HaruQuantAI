"""Orig Open Price trade column snippet.

Description:
    Evaluates Orig Open Price metric for single trade row in results tradelist.

Purpose:
    FEAT-EXTEND-COLUMNS-TRADES: Concrete trade column evaluators.

Key Capabilities:
    - FR-COLUMNS-TRADE-ORIGINAL-OPEN-PRICE:
      Extract Orig Open Price for trade record.

Python API Usage:
    from app.extend.columns.trades.original_open_price import (
        OriginalOpenPrice,
    )
    col = OriginalOpenPrice()
    val = col.get_value(trade, index=1, running_balance=10500.0)

CLI Usage:
    uv run pytest tests/extend/test_columns_catalog.py --no-cov
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.columns.base import TradelistColumn, TradeRecord

logger = get_logger(__name__)


class OriginalOpenPrice(TradelistColumn):
    """Evaluates Orig Open Price metric for single trade row."""

    def __init__(self) -> None:
        super().__init__(
            column_id="OriginalOpenPrice",
            label="Orig Open Price",
            value_type="NUMBER",
            decimals=5,
            source_ref="SQ.Columns.Trades.OriginalOpenPrice",
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
        """Extract Orig Open Price value for single trade snapshot."""
        _ = (trade, index, running_balance, running_dd_money, running_dd_pct)
        logger.debug(
            "FR-COLUMNS-TRADE-%s: evaluating %s idx=%d",
            "ORIGINAL-OPEN-PRICE",
            "OriginalOpenPrice",
            index,
        )
        return trade.open_price
