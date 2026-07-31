"""FEAT-BRK-02: MetaTrader 5 account and lifecycle capabilities."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import (
    create_real_adapter,
    real_session,
    require_success,
)
from app.services.brokers import (
    disconnect_broker,
    get_broker_connection_status,
    get_broker_last_error,
    get_broker_server_time,
    get_broker_value_field,
    is_broker_connected,
    ping_broker,
    reconnect_broker,
    refresh_broker_session,
    supports_broker_capability,
)


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


async def fr_brokers_048_to_051_connection_and_session(adapter: object) -> None:
    """FR-BRK-048..051: Stage 1 & 2 — Terminal Connection, Verification, and Session Recovery."""
    _header("Stage 1 & 2: Terminal Connection & Session Recovery (FR-BRK-048..051)")
    result = await get_broker_connection_status(adapter)
    require_success("Result", result)
    data = get_broker_value_field(result, "data")
    assert data is not None
    assert get_broker_value_field(data, "transport_connected")
    print(_format_result(result))
    print(
        f"Data -> transport_connected={get_broker_value_field(data, 'transport_connected')}"
    )

    disconnected = create_real_adapter("mt5")
    dis_res = await disconnect_broker(disconnected)
    require_success("Result", dis_res)
    print(_format_result(dis_res))
    print(f"Data -> disconnect_status='{get_broker_value_field(dis_res, 'status')}'")

    rec_res = await reconnect_broker(adapter)
    require_success("Result", rec_res)
    print(_format_result(rec_res))
    print(f"Data -> reconnect_status='{get_broker_value_field(rec_res, 'status')}'")

    conn_res = await is_broker_connected(adapter)
    require_success("Connected status", conn_res)
    assert get_broker_value_field(conn_res, "data") is True
    print(_format_result(conn_res))
    print(f"Data -> is_connected={get_broker_value_field(conn_res, 'data')}")


async def fr_brokers_052_to_056_verified_account_info(adapter: object) -> None:
    """FR-BRK-052..056: Stage 3 — Verified MT5 Session Status & Account Info Output."""
    _header("Stage 3: Verified Session & Account Info Output (FR-BRK-052..056)")
    status_res = await get_broker_connection_status(adapter)
    require_success("Lifecycle state", status_res)
    status_data = get_broker_value_field(status_res, "data")
    assert status_data is not None
    print(_format_result(status_res))
    print(f"Data -> lifecycle_state='{get_broker_value_field(status_data, 'state')}'")

    ping_res = await ping_broker(adapter)
    require_success("Liveness probe", ping_res)
    print(_format_result(ping_res))
    print(f"Data -> ping_status='{get_broker_value_field(ping_res, 'status')}'")

    supp_refresh = await supports_broker_capability(adapter, "refresh_session")
    if get_broker_value_field(supp_refresh, "data"):
        refresh_res = await refresh_broker_session(adapter)
        require_success("Session refresh", refresh_res)
        print(_format_result(refresh_res))
        print(
            f"Data -> refresh_status='{get_broker_value_field(refresh_res, 'status')}'"
        )
    else:
        print("Data -> refresh_status='unsupported_on_provider'")

    supp_time = await supports_broker_capability(adapter, "get_server_time")
    if get_broker_value_field(supp_time, "data"):
        time_res = await get_broker_server_time(adapter)
        require_success("Server time", time_res)
        print(_format_result(time_res))
        print(
            f"Data -> server_time_status='{get_broker_value_field(time_res, 'status')}'"
        )
    else:
        print("Data -> server_time_status='unsupported_on_provider'")

    err_res = await get_broker_last_error(adapter)
    require_success("Last error", err_res)
    print(_format_result(err_res))
    print(f"Data -> last_error_status='{get_broker_value_field(err_res, 'status')}'")


async def _run() -> None:
    """Execute every lifecycle requirement in one genuine MT5 demo session."""
    _feature_header(
        "FEATURE: FEAT-BRK-02 — mt5_account/ — MetaTrader 5 Account Lifecycle\n\n"
        "Purpose: Provide MT5 connection, account, platform, and permissions state.\n\n"
        "Module flow:\n"
        "-> MT5 connection config\n"
        "-> terminal connection & login\n"
        "-> verified session & account info"
    )

    async with real_session("mt5") as adapter:
        # Stage 1 & 2: Connection config & session recovery
        await fr_brokers_048_to_051_connection_and_session(adapter)

        # Stage 3: Verified session & account info output
        await fr_brokers_052_to_056_verified_account_info(adapter)


def main() -> None:
    """Run the standalone genuine MT5 lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
