"""Read-only historical deal facade."""

from __future__ import annotations

from app.services.trading.info._common import safe_attr
from app.services.trading.info._ticket import TicketInfoFacade
from app.utils.logger import logger


class DealInfo(TicketInfoFacade):
    """Read-only facade for historical deal records."""

    _broker_function = "get_history_deal_info"

    def order(self) -> int:
        """Return originating order ticket."""
        logger.info("Reading deal order ticket.")
        return safe_attr(self._data, "order", 0, int)

    def entry(self) -> int:
        """Return deal entry type."""
        logger.info("Reading deal entry type.")
        return safe_attr(self._data, "entry", 0, int)

    def entry_description(self) -> str:
        """Return deal entry description."""
        logger.info("Reading deal entry description.")
        descriptions = {
            0: "Entry In",
            1: "Entry Out",
            2: "Entry In/Out",
            3: "Entry Out By",
        }
        return descriptions.get(
            self.entry(),
            f"Unknown ({self.entry()})",
        )

    def commission(self) -> float:
        """Return deal commission."""
        logger.info("Reading deal commission.")
        return safe_attr(self._data, "commission", 0.0, float)

    def swap(self) -> float:
        """Return deal swap."""
        logger.info("Reading deal swap.")
        return safe_attr(self._data, "swap", 0.0, float)

    def profit(self) -> float:
        """Return deal profit."""
        logger.info("Reading deal profit.")
        return safe_attr(self._data, "profit", 0.0, float)
