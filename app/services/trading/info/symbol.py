"""MQL5-compatible read-only symbol information facade."""
# ruff: noqa: TC001

from __future__ import annotations

from app.services.trading.contracts import JsonObject
from app.services.trading.info._common import (
    broker_call,
    redacted_info_payload,
    safe_attr,
)
from app.utils.logger import logger


class SymbolInfo:
    """Read-only facade for broker symbol specifications."""

    def __init__(self, name: str | None = None) -> None:
        """Initialize symbol facade.

        Args:
            name: Optional symbol name.
        """
        logger.info("Initializing trading SymbolInfo facade.")
        self._name = name or ""
        self._data: object | None = None

    def name(self, name: str | None = None) -> str | bool:
        """Get or set the local symbol name without broker mutation."""
        logger.info("Reading or setting symbol name.")
        if name is not None:
            self._name = name
            self._data = None
            return True
        return self._name

    def refresh(self) -> bool:
        """Refresh read-only symbol data."""
        logger.info("Refreshing symbol info for {}.", self._name)
        if not self._name:
            return False
        self._data = broker_call("get_symbol_info", self._name)
        return self._data is not None

    def refresh_rates(self) -> bool:
        """Refresh read-only symbol rates."""
        logger.info("Refreshing symbol rates for {}.", self._name)
        return self.refresh()

    def select(self, select: bool) -> bool:
        """Validate local symbol selection without broker mutation.

        Args:
            select: Requested selection flag.

        Returns:
            bool: True when a symbol name is present and selection is read-only.
        """
        logger.info("Evaluating read-only symbol select request {}.", select)
        return bool(self._name)

    def is_synchronized(self) -> bool:
        """Return whether read-only symbol data is synchronized."""
        logger.info("Reading symbol synchronization state.")
        return self.refresh()

    def digits(self) -> int:
        """Return symbol digits."""
        logger.info("Reading symbol digits.")
        self.refresh()
        return safe_attr(self._data, "digits", 0, int)

    def point(self) -> float:
        """Return symbol point."""
        logger.info("Reading symbol point.")
        self.refresh()
        return safe_attr(self._data, "point", 0.0, float)

    def tick_size(self) -> float:
        """Return symbol tick size."""
        logger.info("Reading symbol tick size.")
        self.refresh()
        return safe_attr(self._data, "trade_tick_size", 0.0, float)

    def trade_mode(self) -> int:
        """Return symbol trade mode."""
        logger.info("Reading symbol trade mode.")
        self.refresh()
        return safe_attr(self._data, "trade_mode", 0, int)

    def trade_mode_description(self) -> str:
        """Return symbol trade mode description."""
        logger.info("Reading symbol trade mode description.")
        return "Full Access" if self.trade_mode() else "Disabled"

    def contract_size(self) -> float:
        """Return symbol contract size."""
        logger.info("Reading symbol contract size.")
        self.refresh()
        return safe_attr(self._data, "trade_contract_size", 0.0, float)

    def volume_min(self) -> float:
        """Return minimum order volume."""
        logger.info("Reading symbol minimum volume.")
        self.refresh()
        return safe_attr(self._data, "volume_min", 0.0, float)

    def volume_max(self) -> float:
        """Return maximum order volume."""
        logger.info("Reading symbol maximum volume.")
        self.refresh()
        return safe_attr(self._data, "volume_max", 0.0, float)

    def volume_step(self) -> float:
        """Return order volume step."""
        logger.info("Reading symbol volume step.")
        self.refresh()
        return safe_attr(self._data, "volume_step", 0.0, float)

    def swap_mode(self) -> int:
        """Return swap mode."""
        logger.info("Reading symbol swap mode.")
        self.refresh()
        return safe_attr(self._data, "swap_mode", 0, int)

    def swap_long(self) -> float:
        """Return long swap."""
        logger.info("Reading symbol long swap.")
        self.refresh()
        return safe_attr(self._data, "swap_long", 0.0, float)

    def swap_short(self) -> float:
        """Return short swap."""
        logger.info("Reading symbol short swap.")
        self.refresh()
        return safe_attr(self._data, "swap_short", 0.0, float)

    def bid(self) -> float:
        """Return current bid."""
        logger.info("Reading symbol bid.")
        self.refresh()
        return safe_attr(self._data, "bid", 0.0, float)

    def ask(self) -> float:
        """Return current ask."""
        logger.info("Reading symbol ask.")
        self.refresh()
        return safe_attr(self._data, "ask", 0.0, float)

    def last(self) -> float:
        """Return last price."""
        logger.info("Reading symbol last price.")
        self.refresh()
        return safe_attr(self._data, "last", 0.0, float)

    def spread(self) -> int:
        """Return spread in points."""
        logger.info("Reading symbol spread.")
        self.refresh()
        return safe_attr(self._data, "spread", 0, int)

    def info_integer(self, prop_id: int) -> int:
        """Return MQL5-compatible integer property."""
        logger.info("Reading symbol integer property {}.", prop_id)
        return {
            0: self.digits,
            1: self.trade_mode,
            2: self.swap_mode,
            3: self.spread,
        }.get(prop_id, lambda: 0)()

    def info_double(self, prop_id: int) -> float:
        """Return MQL5-compatible float property."""
        logger.info("Reading symbol double property {}.", prop_id)
        return {
            0: self.point,
            1: self.tick_size,
            2: self.contract_size,
            3: self.volume_min,
            4: self.volume_max,
            5: self.volume_step,
            6: self.swap_long,
            7: self.swap_short,
            8: self.bid,
            9: self.ask,
            10: self.last,
        }.get(prop_id, lambda: 0.0)()

    def info_string(self, prop_id: int) -> str:
        """Return MQL5-compatible string property."""
        logger.info("Reading symbol string property {}.", prop_id)
        self.refresh()
        return {
            0: lambda: safe_attr(self._data, "name", self._name, str),
            1: lambda: safe_attr(self._data, "description", "", str),
            2: lambda: safe_attr(self._data, "path", "", str),
        }.get(prop_id, lambda: "")()

    def payload(self) -> JsonObject:
        """Return a redacted symbol payload."""
        logger.info("Building redacted symbol info payload.")
        return redacted_info_payload(
            {
                "name": str(self.name()),
                "digits": self.digits(),
                "tick_size": self.tick_size(),
                "volume_min": self.volume_min(),
                "volume_max": self.volume_max(),
                "volume_step": self.volume_step(),
                "bid": self.bid(),
                "ask": self.ask(),
            }
        )
