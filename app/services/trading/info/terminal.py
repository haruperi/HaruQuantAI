"""MQL5-compatible read-only terminal information facade."""
# ruff: noqa: TC001

from __future__ import annotations

from app.services.trading.contracts import JsonObject
from app.services.trading.info._common import (
    broker_call,
    redacted_info_payload,
    safe_attr,
)
from app.utils.logger import logger


class TerminalInfo:
    """Read-only facade for active broker terminal state."""

    def __init__(self) -> None:
        """Initialize terminal facade."""
        logger.info("Initializing trading TerminalInfo facade.")
        self._data: object | None = None

    def _refresh(self) -> None:
        """Refresh terminal data through the active broker module."""
        logger.info("Refreshing terminal info facade.")
        self._data = broker_call("get_terminal_info")

    def language(self) -> str:
        """Return terminal language."""
        logger.info("Reading terminal language.")
        self._refresh()
        return safe_attr(self._data, "language", "Python", str)

    def company(self) -> str:
        """Return broker company."""
        logger.info("Reading terminal company.")
        self._refresh()
        return safe_attr(self._data, "company", "", str)

    def name(self) -> str:
        """Return terminal name."""
        logger.info("Reading terminal name.")
        self._refresh()
        return safe_attr(self._data, "name", "", str)

    def path(self) -> str:
        """Return terminal executable path."""
        logger.info("Reading terminal path.")
        self._refresh()
        return safe_attr(self._data, "path", "", str)

    def data_path(self) -> str:
        """Return terminal data path."""
        logger.info("Reading terminal data path.")
        self._refresh()
        return safe_attr(self._data, "data_path", "", str)

    def common_data_path(self) -> str:
        """Return terminal common data path."""
        logger.info("Reading terminal common data path.")
        self._refresh()
        return safe_attr(self._data, "commondata_path", "", str)

    def build(self) -> int:
        """Return terminal build."""
        logger.info("Reading terminal build.")
        self._refresh()
        return safe_attr(self._data, "build", 0, int)

    def connected(self) -> bool:
        """Return terminal connection state."""
        logger.info("Reading terminal connection state.")
        self._refresh()
        return safe_attr(self._data, "connected", False, bool)

    def trade_allowed(self) -> bool:
        """Return terminal trade permission state."""
        logger.info("Reading terminal trade permission.")
        self._refresh()
        return safe_attr(self._data, "trade_allowed", False, bool)

    def dlls_allowed(self) -> bool:
        """Return terminal DLL permission state."""
        logger.info("Reading terminal DLL permission.")
        self._refresh()
        return safe_attr(self._data, "dlls_allowed", False, bool)

    def ping_last(self) -> int:
        """Return last terminal ping."""
        logger.info("Reading terminal ping.")
        self._refresh()
        return safe_attr(self._data, "ping_last", 0, int)

    def info_integer(self, prop_id: int) -> int:
        """Return MQL5-compatible integer property."""
        logger.info("Reading terminal integer property {}.", prop_id)
        return {
            0: self.build,
            1: lambda: int(self.connected()),
            2: lambda: int(self.trade_allowed()),
            3: lambda: int(self.dlls_allowed()),
            4: self.ping_last,
        }.get(prop_id, lambda: 0)()

    def info_string(self, prop_id: int) -> str:
        """Return MQL5-compatible string property."""
        logger.info("Reading terminal string property {}.", prop_id)
        return {
            0: self.language,
            1: self.company,
            2: self.name,
            3: self.path,
            4: self.data_path,
            5: self.common_data_path,
        }.get(prop_id, lambda: "")()

    def payload(self) -> JsonObject:
        """Return a redacted terminal payload."""
        logger.info("Building redacted terminal info payload.")
        return redacted_info_payload(
            {
                "language": self.language(),
                "company": self.company(),
                "name": self.name(),
                "build": self.build(),
                "connected": self.connected(),
                "trade_allowed": self.trade_allowed(),
                "ping_last": self.ping_last(),
            }
        )
