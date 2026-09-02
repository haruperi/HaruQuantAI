"""FR 1: MetaTrader 5 Terminal Environment and Connection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.brokers.metatrader._persistence import get_mt5_credentials
from app.services.brokers.metatrader.config import MetaTraderConfig

if TYPE_CHECKING:
    from app.services.brokers.metatrader.client import MetaTraderClient

_terminal_state: dict[str, Any] = {
    "connected": False,
    "login": None,
    "server": None,
    "terminal_path": None,
    "last_error": (0, "Success"),
}


def _resolve_client(client: MetaTraderClient | Any | None = None) -> Any:
    """Resolve the provided client instance or fall back to the active default."""
    if client is not None:
        return client
    from app.services.brokers.metatrader.client import get_default_client

    return get_default_client()


def connect(
    path: str | None = None,
    login: int | str | None = None,
    password: str | None = None,
    server: str | None = None,
    timeout: int = 30,
    portable: bool = False,
    config: MetaTraderConfig | None = None,
    client: MetaTraderClient | Any | None = None,
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
        client: Optional MetaTraderClient instance.

    Returns:
        Connection summary dictionary on success.

    Raises:
        RuntimeError: If MetaTrader5 package is unavailable or terminal initialization fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 Python package is not installed or available in the environment."
        raise RuntimeError(msg)

    cfg = config or getattr(client_inst, "config", None)
    db_creds = get_mt5_credentials(cfg.database_path if cfg else None)

    final_path = (
        path or (cfg.terminal_path if cfg else None) or db_creds["terminal_path"]
    )
    final_login = login or (cfg.login if cfg else None) or db_creds["login"]
    final_pwd = password or (cfg.password if cfg else None) or db_creds["password"]
    final_server = server or (cfg.server if cfg else None) or db_creds["server"]
    final_timeout = timeout or (cfg.timeout if cfg else 30)

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
        client_inst.state["connected"] = False
        client_inst.state["last_error"] = err
        _terminal_state["connected"] = False
        _terminal_state["last_error"] = err
        msg = f"Failed to initialize MetaTrader 5 terminal: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    client_inst.state["connected"] = True
    client_inst.state["login"] = login_int
    client_inst.state["server"] = final_server
    client_inst.state["terminal_path"] = final_path
    client_inst.state["last_error"] = (0, "Success")

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


def disconnect(client: MetaTraderClient | Any | None = None) -> bool:
    """Disconnect and shut down MetaTrader 5 terminal connection.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        True if successfully disconnected.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is not None and hasattr(mt5, "shutdown"):
        mt5.shutdown()
    client_inst.state["connected"] = False
    _terminal_state["connected"] = False
    return True


def ping(client: MetaTraderClient | Any | None = None) -> float:
    """Retrieve connection ping in milliseconds.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        Ping in milliseconds.

    Raises:
        RuntimeError: If terminal is not connected.
    """
    client_inst = _resolve_client(client)
    if not is_connected(client=client_inst):
        msg = "MetaTrader 5 terminal is not connected."
        raise RuntimeError(msg)

    mt5 = getattr(client_inst, "mt5", client_inst)
    t_info = (
        mt5.terminal_info()
        if (mt5 is not None and hasattr(mt5, "terminal_info"))
        else None
    )
    if t_info is None:
        err = (
            mt5.last_error()
            if (mt5 is not None and hasattr(mt5, "last_error"))
            else (-1, "Unavailable")
        )
        msg = f"Failed to retrieve ping from terminal_info: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)
    return float(getattr(t_info, "ping_last", 0)) / 1000.0


def is_connected(client: MetaTraderClient | Any | None = None) -> bool:
    """Check if MetaTrader 5 terminal is connected.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        True if connected, False otherwise.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if (
        mt5 is not None
        and hasattr(mt5, "terminal_info")
        and client_inst.state.get("connected", False)
    ):
        t_info = mt5.terminal_info()
        return bool(t_info.connected) if t_info is not None else False
    return False


def get_connection_status(
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Retrieve current connection status details.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        Dictionary with connection status metadata.
    """
    client_inst = _resolve_client(client)
    connected = is_connected(client=client_inst)
    return {
        "connected": connected,
        "login": client_inst.state.get("login"),
        "server": client_inst.state.get("server"),
        "ping_ms": ping(client=client_inst) if connected else 0.0,
        "last_error": client_inst.state.get("last_error", (0, "Success")),
    }


def get_platform_info(
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Retrieve MetaTrader 5 platform version and build.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        Dictionary describing platform version and build.

    Raises:
        RuntimeError: If version query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
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


def get_terminal_info(
    client: MetaTraderClient | Any | None = None,
) -> dict[str, Any]:
    """Retrieve detailed terminal environment properties.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        Dictionary of terminal environment settings.

    Raises:
        RuntimeError: If terminal info query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
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


def get_last_error(
    client: MetaTraderClient | Any | None = None,
) -> tuple[int, str]:
    """Retrieve last MetaTrader 5 error code and description.

    Args:
        client: Optional MetaTraderClient instance.

    Returns:
        Tuple of (error_code, description).
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is not None and hasattr(mt5, "last_error"):
        return mt5.last_error()
    return client_inst.state.get("last_error", (0, "Success"))
