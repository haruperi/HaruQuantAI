"""MQL5-compatible read-only open position facade."""

from __future__ import annotations

from app.services.trading.info._common import broker_call, first_or_none, safe_attr
from app.services.trading.info._ticket import TicketInfoFacade
from app.utils.logger import logger


class PositionInfo(TicketInfoFacade):
    """Read-only facade for active broker positions."""

    _broker_function = "get_position_info"

    def select(self, symbol: str) -> bool:  # type: ignore[override]
        """Select an open position by symbol using a read-only query."""
        logger.info("Selecting position by symbol {}.", symbol)
        self._data = first_or_none(broker_call(self._broker_function, symbol=symbol))
        return self._data is not None

    def select_by_ticket(self, ticket: int) -> bool:
        """Select an open position by ticket using a read-only query."""
        logger.info("Selecting position by ticket {}.", ticket)
        self._data = first_or_none(broker_call(self._broker_function, ticket=ticket))
        return self._data is not None

    def time_update(self) -> int:
        """Return position update time."""
        logger.info("Reading position update time.")
        return safe_attr(self._data, "time_update", 0, int)

    def time_update_msc(self) -> int:
        """Return position millisecond update time."""
        logger.info("Reading position millisecond update time.")
        return safe_attr(self._data, "time_update_msc", 0, int)

    def identifier(self) -> int:
        """Return position identifier."""
        logger.info("Reading position identifier.")
        return safe_attr(self._data, "identifier", self.ticket(), int)

    def price_open(self) -> float:
        """Return position open price."""
        logger.info("Reading position open price.")
        return safe_attr(self._data, "price_open", 0.0, float)

    def stop_loss(self) -> float:
        """Return stop loss."""
        logger.info("Reading position stop loss.")
        return safe_attr(self._data, "sl", 0.0, float)

    def take_profit(self) -> float:
        """Return take profit."""
        logger.info("Reading position take profit.")
        return safe_attr(self._data, "tp", 0.0, float)

    def price_current(self) -> float:
        """Return current position price."""
        logger.info("Reading current position price.")
        return safe_attr(self._data, "price_current", 0.0, float)

    def swap(self) -> float:
        """Return position swap."""
        logger.info("Reading position swap.")
        return safe_attr(self._data, "swap", 0.0, float)

    def profit(self) -> float:
        """Return position profit."""
        logger.info("Reading position profit.")
        return safe_attr(self._data, "profit", 0.0, float)

    def info_double(self, prop_id: int) -> float:
        """Return MQL5-compatible position float property."""
        logger.info("Reading position double property {}.", prop_id)
        return {
            0: self.volume,
            1: self.price_open,
            2: self.stop_loss,
            3: self.take_profit,
            4: self.price_current,
            5: self.swap,
            6: self.profit,
        }.get(prop_id, lambda: 0.0)()
