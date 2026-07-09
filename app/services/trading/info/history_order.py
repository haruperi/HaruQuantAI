"""Read-only historical order facade."""

from __future__ import annotations

from app.services.trading.info.order import OrderInfo
from app.utils.logger import logger


class HistoryOrderInfo(OrderInfo):
    """Read-only facade for historical orders."""

    _broker_function = "get_history_order_info"

    def select(self, ticket: int) -> bool:
        """Select a historical order by ticket."""
        logger.info("Selecting historical order {}.", ticket)
        return super().select(ticket)
