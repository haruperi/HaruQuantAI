"""FR 1: MetaTrader 5 Terminal Environment and Connection."""

from __future__ import annotations

from typing import Any

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False

from app.services.brokers.metatrader._persistence import get_mt5_credentials
from app.services.brokers.metatrader.config import MetaTraderConfig

_terminal_state: dict[str, Any] = {
    "connected": False,
    "login": None,
    "server": None,
    "terminal_path": None,
    "last_error": (0, "Success"),
}


def connect(
    path: str | None = None,
    login: int | str | None = None,
    password: str | None = None,
    server: str | None = None,
    timeout: int = 30,
    portable: bool = False,
    config: MetaTraderConfig | None = None,
) -> dict[str, Any]:
    """Connect and initialize MetaTrader 5 terminal with database or explicit credentials.

    Args:
        path: Path to terminal64.exe executable.
        login: Account login number.
        password: Account password.
        server: Trade server name.
        timeout: Connection timeout in seconds.
        portable: Whether to launch terminal in portable mode.
        config: Optional MetaTraderConfig instance.

    Returns:
        Connection summary dictionary on success.

    Raises:
        RuntimeError: If MetaTrader5 package is unavailable or terminal initialization fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 Python package is not installed or available in the environment."
        raise RuntimeError(msg)

    db_creds = get_mt5_credentials(config.database_path if config else None)

    final_path = (
        path or (config.terminal_path if config else None) or db_creds["terminal_path"]
    )
    final_login = login or (config.login if config else None) or db_creds["login"]
    final_pwd = (
        password or (config.password if config else None) or db_creds["password"]
    )
    final_server = server or (config.server if config else None) or db_creds["server"]
    final_timeout = timeout or (config.timeout if config else 30)

    login_int = int(final_login) if final_login and str(final_login).isdigit() else None

    init_kwargs: dict[str, Any] = {
        "timeout": final_timeout * 1000,
        "portable": portable,
    }
    if final_path:
        init_kwargs["path"] = final_path
    if login_int:
        init_kwargs["login"] = login_int
    if final_pwd:
        init_kwargs["password"] = final_pwd
    if final_server:
        init_kwargs["server"] = final_server

    initialized = mt5.initialize(**init_kwargs)
    if not initialized:
        err = mt5.last_error()
        _terminal_state["connected"] = False
        _terminal_state["last_error"] = err
        msg = f"Failed to initialize MetaTrader 5 terminal: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    _terminal_state["connected"] = True
    _terminal_state["login"] = login_int
    _terminal_state["server"] = final_server
    _terminal_state["terminal_path"] = final_path
    _terminal_state["last_error"] = (0, "Success")
    return {
        "status": "connected",
        "connected": True,
        "login": login_int,
        "server": final_server,
        "platform": "mt5",
    }


def disconnect() -> bool:
    """Disconnect and shut down MetaTrader 5 terminal connection.

    Returns:
        True if successfully disconnected.
    """
    if _MT5_AVAILABLE and mt5 is not None:
        mt5.shutdown()
    _terminal_state["connected"] = False
    return True


def ping() -> float:
    """Retrieve connection ping in milliseconds.

    Returns:
        Ping in milliseconds.

    Raises:
        RuntimeError: If terminal is not connected.
    """
    if not is_connected():
        msg = "MetaTrader 5 terminal is not connected."
        raise RuntimeError(msg)

    t_info = mt5.terminal_info() if (_MT5_AVAILABLE and mt5 is not None) else None
    if t_info is None:
        err = (
            mt5.last_error()
            if (_MT5_AVAILABLE and mt5 is not None)
            else (-1, "Unavailable")
        )
        msg = f"Failed to retrieve ping from terminal_info: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)
    return float(getattr(t_info, "ping_last", 0)) / 1000.0


def is_connected() -> bool:
    """Check if MetaTrader 5 terminal is connected.

    Returns:
        True if connected, False otherwise.
    """
    if _MT5_AVAILABLE and mt5 is not None and _terminal_state["connected"]:
        t_info = mt5.terminal_info()
        return bool(t_info.connected) if t_info is not None else False
    return False


def get_connection_status() -> dict[str, Any]:
    """Retrieve current connection status details.

    Returns:
        Dictionary with connection status metadata.
    """
    return {
        "connected": is_connected(),
        "login": _terminal_state["login"],
        "server": _terminal_state["server"],
        "ping_ms": ping() if is_connected() else 0.0,
        "last_error": _terminal_state["last_error"],
    }


def get_platform_info() -> dict[str, Any]:
    """Retrieve MetaTrader 5 platform version and build.

    Returns:
        Dictionary describing platform version and build.

    Raises:
        RuntimeError: If version query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    ver = mt5.version()
    if ver is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve MetaTrader 5 platform version: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return {
        "platform": "mt5",
        "version": ver[0],
        "build": ver[1],
        "release_date": ver[2],
    }


def get_terminal_info() -> dict[str, Any]:
    """Retrieve detailed terminal environment properties.

    Returns:
        Dictionary of terminal environment settings.

    Raises:
        RuntimeError: If terminal info query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    t_info = mt5.terminal_info()
    if t_info is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve MetaTrader 5 terminal info: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return t_info._asdict()


def get_provider_specification() -> dict[str, Any]:
    """Retrieve supported MetaTrader 5 specifications.

    Returns:
        Provider capability matrix.
    """
    return {
        "provider": "mt5",
        "supports_market_orders": True,
        "supports_limit_orders": True,
        "supports_stop_orders": True,
        "supports_stop_limit": True,
        "supports_close_by": True,
        "supports_multiple_accounts": True,
        "max_orders": 500,
    }


def get_last_error() -> tuple[int, str]:
    """Retrieve last MetaTrader 5 error code and description.

    Returns:
        Tuple of (error_code, description).
    """
    if _MT5_AVAILABLE and mt5 is not None:
        return mt5.last_error()
    return _terminal_state["last_error"]
