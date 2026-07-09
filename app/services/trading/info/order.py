"""Read-only pending order facade."""

from __future__ import annotations

from app.services.trading.info._common import safe_attr
from app.services.trading.info._ticket import TicketInfoFacade
from app.utils.logger import logger


class OrderInfo(TicketInfoFacade):
    """Read-only facade for active pending orders."""

    _broker_function = "get_order_info"

    def time_setup(self) -> int:
        """Return setup time."""
        logger.info("Reading order setup time.")
        return safe_attr(self._data, "time_setup", 0, int)

    def time_setup_msc(self) -> int:
        """Return setup millisecond time."""
        logger.info("Reading order setup millisecond time.")
        return safe_attr(self._data, "time_setup_msc", 0, int)

    def time_expiration(self) -> int:
        """Return expiration time."""
        logger.info("Reading order expiration time.")
        return safe_attr(self._data, "time_expiration", 0, int)

    def time_done(self) -> int:
        """Return done time."""
        logger.info("Reading order done time.")
        return safe_attr(self._data, "time_done", 0, int)

    def time_done_msc(self) -> int:
        """Return done millisecond time."""
        logger.info("Reading order done millisecond time.")
        return safe_attr(self._data, "time_done_msc", 0, int)

    def type_time(self) -> int:
        """Return order expiration type."""
        logger.info("Reading order time type.")
        return safe_attr(self._data, "type_time", 0, int)

    def type_time_description(self) -> str:
        """Return order time type description."""
        logger.info("Reading order time type description.")
        return {0: "GTC", 1: "Day", 2: "Specified", 3: "Specified Day"}.get(
            self.type_time(),
            f"Unknown ({self.type_time()})",
        )

    def type_filling(self) -> int:
        """Return order filling type."""
        logger.info("Reading order filling type.")
        return safe_attr(self._data, "type_filling", 0, int)

    def type_filling_description(self) -> str:
        """Return order filling description."""
        logger.info("Reading order filling description.")
        return {0: "FOK", 1: "IOC", 2: "Return"}.get(
            self.type_filling(),
            f"Unknown ({self.type_filling()})",
        )

    def state(self) -> int:
        """Return order state."""
        logger.info("Reading order state.")
        return safe_attr(self._data, "state", 0, int)

    def state_description(self) -> str:
        """Return order state description."""
        logger.info("Reading order state description.")
        return {
            0: "Started",
            1: "Placed",
            2: "Canceled",
            3: "Partial",
            4: "Filled",
            5: "Rejected",
            6: "Expired",
            7: "Request Sent",
            8: "Request Cancelled",
        }.get(self.state(), f"Unknown ({self.state()})")

    def position_by_id(self) -> int:
        """Return position-by ID."""
        logger.info("Reading order position-by ID.")
        return safe_attr(self._data, "position_by_id", 0, int)

    def volume_initial(self) -> float:
        """Return initial volume."""
        logger.info("Reading order initial volume.")
        return safe_attr(self._data, "volume_initial", 0.0, float)

    def volume_current(self) -> float:
        """Return current volume."""
        logger.info("Reading order current volume.")
        return safe_attr(self._data, "volume_current", 0.0, float)

    def price_open(self) -> float:
        """Return open price."""
        logger.info("Reading order open price.")
        return safe_attr(self._data, "price_open", 0.0, float)

    def stop_loss(self) -> float:
        """Return stop loss."""
        logger.info("Reading order stop loss.")
        return safe_attr(self._data, "sl", 0.0, float)

    def take_profit(self) -> float:
        """Return take profit."""
        logger.info("Reading order take profit.")
        return safe_attr(self._data, "tp", 0.0, float)

    def price_current(self) -> float:
        """Return current price."""
        logger.info("Reading order current price.")
        return safe_attr(self._data, "price_current", 0.0, float)

    def price_stop_limit(self) -> float:
        """Return stop-limit price."""
        logger.info("Reading order stop-limit price.")
        return safe_attr(self._data, "price_stoplimit", 0.0, float)

    def info_double(self, prop_id: int) -> float:
        """Return order float property."""
        logger.info("Reading order double property {}.", prop_id)
        return {
            0: self.volume_initial,
            1: self.volume_current,
            2: self.price_open,
            3: self.stop_loss,
            4: self.take_profit,
            5: self.price_current,
        }.get(prop_id, lambda: 0.0)()
