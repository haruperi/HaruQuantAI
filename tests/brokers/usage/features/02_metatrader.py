"""FEAT-BRK-02: MetaTrader direct broker channel."""

import asyncio
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import (
    create_real_adapter,
    real_session,
    require_success,
)
from app.services.brokers import (
    acquire_metatrader_snapshot_symbols,
    build_broker_order_request_v2,
    build_provider_specification_snapshot,
    disconnect_broker,
    get_broker_connection_status,
    get_broker_last_error,
    get_broker_server_time,
    get_broker_value_field,
    get_metatrader_snapshot_gateway_status,
    is_broker_connected,
    ping_broker,
    reconnect_broker,
    refresh_broker_session,
    release_metatrader_snapshot_symbols,
    supports_broker_capability,
)


class _SymbolInfo(NamedTuple):
    """Minimal verified MT5-shaped provider snapshot fixture."""

    name: object = "EURUSD"
    digits: object = 5
    point: object = 0.00001
    filling_mode: object = 3
    order_mode: object = 15
    expiration_mode: object = 15
    order_gtc_mode: object = 0
    trade_exemode: object = 2
    trade_mode: object = 4
    trade_calc_mode: object = 0
    swap_mode: object = 1
    swap_rollover3days: object = 3
    trade_stops_level: object = 0
    trade_freeze_level: object = 0
    volume_min: object = 0.01
    volume_max: object = 100.0
    volume_step: object = 0.01
    volume_limit: object = 0.0
    trade_tick_size: object = 0.00001
    trade_tick_value: object = 1.0
    trade_tick_value_profit: object = 1.0
    trade_tick_value_loss: object = 1.0
    trade_contract_size: object = 100000.0
    currency_base: object = "EUR"
    currency_profit: object = "USD"
    currency_margin: object = "USD"
    margin_initial: object = 0.0
    margin_maintenance: object = 0.0
    margin_hedged: object = 100000.0
    margin_hedged_use_leg: object = False
    swap_long: object = -0.2
    swap_short: object = -1.2


def _specification() -> object:
    """Build transport-free provider specification evidence."""
    return build_provider_specification_snapshot(
        symbol_info=_SymbolInfo(),
        broker="mt5",
        server="DemoServer",
        account_id="usage-account",
        environment="demo",
        terminal_build="4410",
        source_revision="mt5:4410",
        observed_at=datetime(2026, 8, 15, tzinfo=UTC),
        account_info=None,
    )


def _v2_request(time_policy: str = "GTC") -> object:
    """Build one opaque order request v2 through the Brokers root."""
    fields: dict[str, object] = {
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": Decimal(1),
        "quantity_unit": "lots",
        "environment": "demo",
        "fill_policy": "IOC",
        "time_policy": time_policy,
    }
    if time_policy == "SPECIFIED_DAY":
        fields["expiration"] = datetime(2026, 8, 16, tzinfo=UTC)
    return build_broker_order_request_v2(
        provider_specification=_specification(), **fields
    )


def fr_brk_164() -> None:
    """FR-BRK-164: construct a v2 request with two explicit policies."""
    request = _v2_request()
    print("SUCCESS FR-BRK-164", get_broker_value_field(request, "contract_version"))


def fr_brk_165() -> None:
    """FR-BRK-165: preserve SPECIFIED_DAY expiration independently."""
    request = _v2_request("SPECIFIED_DAY")
    print("SUCCESS FR-BRK-165", get_broker_value_field(request, "time_policy"))


def fr_brk_166() -> None:
    """FR-BRK-166: expose the exact provider revision binding."""
    request = _v2_request()
    checksum = str(get_broker_value_field(request, "provider_specification_checksum"))
    print("SUCCESS FR-BRK-166", checksum[:12])


async def fr_brokers_152_to_158_snapshot_symbol_demand() -> None:
    """FR-BRK-152..158: Exercise connected revisioned snapshot demand."""
    _header("Stage 4: Revisioned MT5 Snapshot Symbol Demand (FR-BRK-152..158)")
    status = get_metatrader_snapshot_gateway_status()
    print(_format_result(status))
    if not status["connected"]:
        print("Data -> snapshot_gateway='not_connected'; demand exercise skipped")
        return
    consumer_id = await acquire_metatrader_snapshot_symbols(("EURUSD",))
    try:
        applied = get_metatrader_snapshot_gateway_status()
        assert applied["applied_symbol_count"] >= 1
        print(
            "Data -> "
            f"desired_revision={applied['desired_revision']}, "
            f"applied_revision={applied['applied_revision']}"
        )
    finally:
        await release_metatrader_snapshot_symbols(consumer_id)


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

    fr_brk_164()
    fr_brk_165()
    fr_brk_166()

    async with real_session("mt5") as adapter:
        # Stage 1 & 2: Connection config & session recovery
        await fr_brokers_048_to_051_connection_and_session(adapter)

        # Stage 3: Verified session & account info output
        await fr_brokers_052_to_056_verified_account_info(adapter)

        await fr_brokers_152_to_158_snapshot_symbol_demand()


def main() -> None:
    """Run the standalone genuine MT5 lifecycle program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
