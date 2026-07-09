"""Shared ticket-based read-only info facade base."""
# ruff: noqa: TC001

from __future__ import annotations

from app.services.trading.contracts import JsonObject
from app.services.trading.info._common import (
    broker_call,
    first_or_none,
    redacted_info_payload,
    safe_attr,
)
from app.utils.logger import logger


class TicketInfoFacade:
    """Base class for read-only ticket-based broker records."""

    _broker_function: str = ""

    def __init__(self, ticket: int | None = None) -> None:
        """Initialize ticket facade.

        Args:
            ticket: Optional ticket to select.
        """
        logger.info("Initializing ticket info facade for {}.", self._broker_function)
        self._data: object | None = None
        if ticket is not None:
            self.select(ticket)

    def select(self, ticket: int) -> bool:
        """Select a record by ticket using a read-only broker query."""
        logger.info("Selecting ticket {} via {}.", ticket, self._broker_function)
        self._data = first_or_none(broker_call(self._broker_function, ticket=ticket))
        return self._data is not None

    def ticket(self) -> int:
        """Return record ticket."""
        logger.info("Reading ticket.")
        return safe_attr(self._data, "ticket", 0, int)

    def time(self) -> int:
        """Return record time."""
        logger.info("Reading record time.")
        return safe_attr(self._data, "time", 0, int)

    def time_msc(self) -> int:
        """Return record millisecond time."""
        logger.info("Reading record millisecond time.")
        return safe_attr(self._data, "time_msc", 0, int)

    def type(self) -> int:
        """Return record type."""
        logger.info("Reading record type.")
        return safe_attr(self._data, "type", 0, int)

    def type_description(self) -> str:
        """Return record type description."""
        logger.info("Reading record type description.")
        value = self.type()
        return {0: "Buy", 1: "Sell", 2: "Buy Limit", 3: "Sell Limit"}.get(
            value,
            f"Unknown ({value})",
        )

    def magic(self) -> int:
        """Return magic number."""
        logger.info("Reading magic number.")
        return safe_attr(self._data, "magic", 0, int)

    def position_id(self) -> int:
        """Return associated position ID."""
        logger.info("Reading position ID.")
        return safe_attr(self._data, "position_id", 0, int)

    def volume(self) -> float:
        """Return record volume."""
        logger.info("Reading record volume.")
        return safe_attr(self._data, "volume", 0.0, float)

    def price(self) -> float:
        """Return record price."""
        logger.info("Reading record price.")
        return safe_attr(self._data, "price", 0.0, float)

    def symbol(self) -> str:
        """Return record symbol."""
        logger.info("Reading record symbol.")
        return safe_attr(self._data, "symbol", "", str)

    def comment(self) -> str:
        """Return record comment."""
        logger.info("Reading record comment.")
        return safe_attr(self._data, "comment", "", str)

    def info_integer(self, prop_id: int) -> int:
        """Return MQL5-compatible integer property."""
        logger.info("Reading ticket integer property {}.", prop_id)
        return {
            0: self.ticket,
            1: self.time,
            2: self.type,
            3: self.magic,
            4: self.position_id,
        }.get(prop_id, lambda: 0)()

    def info_double(self, prop_id: int) -> float:
        """Return MQL5-compatible float property."""
        logger.info("Reading ticket double property {}.", prop_id)
        return {0: self.volume, 1: self.price}.get(prop_id, lambda: 0.0)()

    def info_string(self, prop_id: int) -> str:
        """Return MQL5-compatible string property."""
        logger.info("Reading ticket string property {}.", prop_id)
        return {0: self.symbol, 1: self.comment}.get(prop_id, lambda: "")()

    def payload(self) -> JsonObject:
        """Return a redacted ticket record payload."""
        logger.info("Building redacted ticket info payload.")
        return redacted_info_payload(
            {
                "ticket": self.ticket(),
                "type": self.type(),
                "symbol": self.symbol(),
                "volume": self.volume(),
                "price": self.price(),
                "comment": self.comment(),
            }
        )
