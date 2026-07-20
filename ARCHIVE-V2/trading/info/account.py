"""Read-only account information facade."""

from __future__ import annotations

from app.services.trading.contracts import JsonObject
from app.services.trading.info._common import (
    broker_call,
    redacted_info_payload,
    safe_attr,
)
from app.utils.logger import logger

REAL_TRADE_MODE = 2


class AccountInfo:
    """Read-only facade for the active broker account."""

    def __init__(self) -> None:
        """Initialize the account info facade."""
        logger.info("Initializing trading AccountInfo facade.")
        self._data: object | None = None

    def _refresh(self) -> None:
        """Refresh account data through the active broker module."""
        logger.info("Refreshing account info facade.")
        self._data = broker_call("get_account_info")

    def login(self) -> int:
        """Return account login number."""
        logger.info("Reading account login.")
        self._refresh()
        return safe_attr(self._data, "login", 0, int)

    def trade_mode(self) -> int:
        """Return account trade mode as integer."""
        logger.info("Reading account trade mode.")
        self._refresh()
        server = safe_attr(self._data, "server", "", str).upper()
        return 2 if "REAL" in server or "LIVE" in server else 0

    def trade_mode_description(self) -> str:
        """Return account trade mode description."""
        logger.info("Reading account trade mode description.")
        return "Real" if self.trade_mode() == REAL_TRADE_MODE else "Demo"

    def leverage(self) -> int:
        """Return account leverage."""
        logger.info("Reading account leverage.")
        self._refresh()
        return safe_attr(self._data, "leverage", 1, int)

    def limit_orders(self) -> int:
        """Return pending-order limit."""
        logger.info("Reading account order limit.")
        self._refresh()
        return safe_attr(self._data, "limit_orders", 0, int)

    def trade_allowed(self) -> bool:
        """Return whether account trading is allowed."""
        logger.info("Reading account trade permission.")
        self._refresh()
        return safe_attr(self._data, "trade_allowed", False, bool)

    def trade_expert(self) -> bool:
        """Return whether expert trading is allowed."""
        logger.info("Reading account expert permission.")
        self._refresh()
        return safe_attr(self._data, "trade_expert", False, bool)

    def margin_so_mode(self) -> int:
        """Return stop-out mode."""
        logger.info("Reading account stop-out mode.")
        return 0

    def margin_mode(self) -> int:
        """Return margin mode as integer."""
        logger.info("Reading account margin mode.")
        self._refresh()
        mode = safe_attr(self._data, "margin_mode", "Hedging", str).upper()
        return 0 if "HEDGING" in mode else 1

    def margin_mode_description(self) -> str:
        """Return margin mode description."""
        logger.info("Reading account margin mode description.")
        self._refresh()
        return safe_attr(self._data, "margin_mode", "Hedging", str)

    def balance(self) -> float:
        """Return account balance."""
        logger.info("Reading account balance.")
        self._refresh()
        return safe_attr(self._data, "balance", 0.0, float)

    def credit(self) -> float:
        """Return account credit."""
        logger.info("Reading account credit.")
        self._refresh()
        return safe_attr(self._data, "credit", 0.0, float)

    def profit(self) -> float:
        """Return floating account profit."""
        logger.info("Reading account profit.")
        self._refresh()
        return safe_attr(self._data, "profit", 0.0, float)

    def equity(self) -> float:
        """Return account equity."""
        logger.info("Reading account equity.")
        self._refresh()
        return safe_attr(self._data, "equity", 0.0, float)

    def margin(self) -> float:
        """Return used margin."""
        logger.info("Reading account margin.")
        self._refresh()
        return safe_attr(self._data, "margin", 0.0, float)

    def free_margin(self) -> float:
        """Return free margin."""
        logger.info("Reading account free margin.")
        self._refresh()
        return safe_attr(self._data, "margin_free", 0.0, float)

    def free_margin_mode(self) -> int:
        """Return free-margin mode."""
        logger.info("Reading account free-margin mode.")
        return 0

    def margin_level(self) -> float:
        """Return margin level."""
        logger.info("Reading account margin level.")
        self._refresh()
        return safe_attr(self._data, "margin_level", 0.0, float)

    def margin_so_level(self) -> float:
        """Return stop-out level."""
        logger.info("Reading account stop-out level.")
        self._refresh()
        return safe_attr(self._data, "margin_so_so", 50.0, float)

    def name(self) -> str:
        """Return account holder name."""
        logger.info("Reading account name.")
        self._refresh()
        return safe_attr(self._data, "name", "", str)

    def server(self) -> str:
        """Return account server."""
        logger.info("Reading account server.")
        self._refresh()
        return safe_attr(self._data, "server", "", str)

    def currency(self) -> str:
        """Return account currency."""
        logger.info("Reading account currency.")
        self._refresh()
        return safe_attr(self._data, "currency", "USD", str)

    def company(self) -> str:
        """Return broker company."""
        logger.info("Reading account company.")
        self._refresh()
        return safe_attr(self._data, "company", "", str)

    def info_integer(self, prop_id: int) -> int:
        """Return integer property."""
        logger.info("Reading account integer property {}.", prop_id)
        return {
            0: self.login,
            1: self.trade_mode,
            2: self.leverage,
            3: self.limit_orders,
            4: lambda: int(self.trade_allowed()),
            5: lambda: int(self.trade_expert()),
            6: self.margin_mode,
        }.get(prop_id, lambda: 0)()

    def info_double(self, prop_id: int) -> float:
        """Return float property."""
        logger.info("Reading account double property {}.", prop_id)
        return {
            0: self.balance,
            1: self.credit,
            2: self.profit,
            3: self.equity,
            4: self.margin,
            5: self.free_margin,
            6: self.margin_level,
        }.get(prop_id, lambda: 0.0)()

    def info_string(self, prop_id: int) -> str:
        """Return string property."""
        logger.info("Reading account string property {}.", prop_id)
        return {
            0: self.name,
            1: self.server,
            2: self.currency,
            3: self.company,
        }.get(prop_id, lambda: "")()

    def payload(self) -> JsonObject:
        """Return a redacted account metadata payload."""
        logger.info("Building redacted account info payload.")
        return redacted_info_payload(
            {
                "login": self.login(),
                "trade_mode": self.trade_mode(),
                "leverage": self.leverage(),
                "balance": self.balance(),
                "margin": self.margin(),
                "currency": self.currency(),
                "company": self.company(),
            }
        )
