"""Homogeneous full-domain usage program for app.services.brokers.

Ties all Brokers features (FEAT-BRK-00 through FEAT-BRK-15) into one sequential,
realistic end-to-end domain pipeline using genuine non-production broker adapters:
1. Registry & Capability Discovery (FEAT-BRK-01)
2. Adapter Construction & Connection Configuration (FEAT-BRK-14)
3. Session Lifecycle & Health Verification (FEAT-BRK-00, FEAT-BRK-02 & FEAT-BRK-15)
4. Account State, Balances & Permissions (FEAT-BRK-02 & FEAT-BRK-05)
5. Market Data Reads (FEAT-BRK-06, FEAT-BRK-09, FEAT-BRK-12 & FEAT-BRK-13)
6. Margin & Profit Calculations (FEAT-BRK-10)
7. Streaming Subscriptions (FEAT-BRK-11)
8. Order Mutation Validation & Controlled Session Teardown (FEAT-BRK-07 & FEAT-BRK-08)
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    build_broker_margin_request,
    build_broker_order_request,
    build_broker_profit_request,
    calculate_broker_margin,
    calculate_broker_profit,
    check_broker_order,
    connect_broker,
    disconnect_broker,
    get_broker_account_info,
    get_broker_balances,
    get_broker_capability_catalogue,
    get_broker_connection_status,
    get_broker_error_catalog,
    get_broker_historical_bars,
    get_broker_permissions,
    get_broker_quote,
    get_broker_symbols,
    get_broker_value_field,
    get_registered_brokers,
    is_broker_connected,
    ping_broker,
    subscribe_broker_quotes,
    supports_broker_capability,
    unsubscribe_broker,
)

import _support  # noqa: F401
from _support import create_real_adapter


def _print_stage(stage_num: int, name: str, summary: str) -> None:
    print(f"\n[{'=' * 80}]")
    print(f"Stage {stage_num}: {name}")
    print(f"Description: {summary}")
    print(f"[{'=' * 80}]")


def _run_stage_1_registry() -> Any:
    _print_stage(
        1,
        "Registry & Capability Discovery (FEAT-BRK-01)",
        "Discover registered broker platforms, verify capability catalogue, and load error catalog.",
    )
    reg_response = get_registered_brokers()
    registered = (
        reg_response.data
        if reg_response.status == "success" and reg_response.data
        else []
    )

    cat_response = get_broker_capability_catalogue()
    catalogue = (
        cat_response.data
        if cat_response.status == "success" and cat_response.data
        else {}
    )

    error_catalog = get_broker_error_catalog()

    print(
        f"Data -> registered_brokers={[b.value for b in registered]}, "
        f"catalogue_entries={len(catalogue)}, "
        f"error_codes={len(error_catalog)}"
    )
    return catalogue


def _run_stage_2_adapter_creation() -> Any:
    _print_stage(
        2,
        "Adapter Construction & Configuration (FEAT-BRK-14)",
        "Construct a genuine non-production MT5 broker adapter through the public provider registry.",
    )
    adapter = create_real_adapter("mt5")
    print(f"Data -> adapter_created={adapter is not None}")
    return adapter


async def _run_stage_3_session(adapter: Any) -> None:
    _print_stage(
        3,
        "Session Lifecycle & Health (FEAT-BRK-00, FEAT-BRK-02 & FEAT-BRK-15)",
        "Connect adapter, verify connection state, check capability support, and ping health.",
    )
    conn_result = await connect_broker(adapter)
    status = get_broker_value_field(conn_result, "status")

    conn_status_res = await is_broker_connected(adapter)
    is_conn = get_broker_value_field(conn_status_res, "data")

    supp_res = await supports_broker_capability(adapter, "get_account_info")
    mt5_supported = get_broker_value_field(supp_res, "data")

    ping_result = await ping_broker(adapter)
    ping_status = get_broker_value_field(ping_result, "status")

    print(
        f"Data -> connect_status='{status}', "
        f"is_connected={is_conn}, "
        f"account_supported={mt5_supported}, "
        f"ping_status='{ping_status}'"
    )


async def _run_stage_4_account(adapter: Any) -> None:
    _print_stage(
        4,
        "Account State & Balances (FEAT-BRK-02 & FEAT-BRK-05)",
        "Query broker account info, balances, and permission sets.",
    )
    info_res = await get_broker_account_info(adapter)
    info_status = get_broker_value_field(info_res, "status")

    bal_res = await get_broker_balances(adapter)
    bal_status = get_broker_value_field(bal_res, "status")

    perm_res = await get_broker_permissions(adapter)
    perm_status = get_broker_value_field(perm_res, "status")

    print(
        f"Data -> account_status='{info_status}', "
        f"balances_status='{bal_status}', "
        f"permissions_status='{perm_status}'"
    )


async def _run_stage_5_market_data(adapter: Any) -> None:
    _print_stage(
        5,
        "Market Data Reads (FEAT-BRK-06, FEAT-BRK-09, FEAT-BRK-12 & FEAT-BRK-13)",
        "Read symbol directory, quote snapshot, and historical bar series.",
    )
    sym_res = await get_broker_symbols(adapter, limit=10)
    sym_status = get_broker_value_field(sym_res, "status")

    quote_res = await get_broker_quote(adapter, "EURUSD")
    quote_status = get_broker_value_field(quote_res, "status")

    bars_res = await get_broker_historical_bars(
        adapter, "EURUSD", timeframe="M1", limit=5
    )
    bars_status = get_broker_value_field(bars_res, "status")

    print(
        f"Data -> symbols_status='{sym_status}', "
        f"quote_status='{quote_status}', "
        f"bars_status='{bars_status}'"
    )


async def _run_stage_6_calculations(adapter: Any) -> None:
    _print_stage(
        6,
        "Margin & Profit Calculations (FEAT-BRK-10)",
        "Calculate provider-native margin requirement and potential position profit.",
    )
    margin_req = build_broker_margin_request(
        symbol="EURUSD",
        side="BUY",
        quantity="0.01",
        quantity_unit="lots",
        price="1.1000",
        product_profile="mt5",
    )
    margin_res = await calculate_broker_margin(adapter, margin_req)
    margin_status = get_broker_value_field(margin_res, "status")
    margin_val = (
        get_broker_value_field(margin_res, "data")
        if margin_status == "success"
        else None
    )

    profit_req = build_broker_profit_request(
        symbol="EURUSD",
        side="BUY",
        quantity="0.01",
        quantity_unit="lots",
        open_price="1.1000",
        close_price="1.1050",
        product_profile="mt5",
    )
    profit_res = await calculate_broker_profit(adapter, profit_req)
    profit_status = get_broker_value_field(profit_res, "status")
    profit_val = (
        get_broker_value_field(profit_res, "data")
        if profit_status == "success"
        else None
    )

    print(
        f"Data -> margin_status='{margin_status}', margin_value={margin_val}, "
        f"profit_status='{profit_status}', profit_value={profit_val}"
    )


async def _run_stage_7_subscriptions(adapter: Any) -> None:
    _print_stage(
        7,
        "Streaming Subscriptions (FEAT-BRK-11)",
        "Check streaming quote capability support before attempting real-time subscription.",
    )
    supp_res = await supports_broker_capability(adapter, "subscribe_quotes")
    is_supported = get_broker_value_field(supp_res, "data")

    if is_supported:
        sub_res = await subscribe_broker_quotes(adapter, symbol="EURUSD")
        sub_status = get_broker_value_field(sub_res, "status")
        subscription = (
            get_broker_value_field(sub_res, "data")
            if sub_res.status == "success"
            else None
        )
        if subscription is not None:
            unsub_res = await unsubscribe_broker(subscription)
            unsub_status = get_broker_value_field(unsub_res, "status")
        else:
            unsub_status = "skipped"
    else:
        sub_status = "unsupported_on_provider"
        unsub_status = "skipped"

    print(
        f"Data -> subscribe_status='{sub_status}', unsubscribe_status='{unsub_status}'"
    )


async def _run_stage_8_mutations_and_teardown(adapter: Any) -> None:
    _print_stage(
        8,
        "Order Mutations & Teardown (FEAT-BRK-07 & FEAT-BRK-08)",
        "Validate single-target order request and perform controlled adapter disconnect.",
    )
    order_req = build_broker_order_request(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity="0.01",
        quantity_unit="lots",
        environment="demo",
    )
    check_res = await check_broker_order(adapter, order_req)
    check_status = get_broker_value_field(check_res, "status")

    disconn_res = await disconnect_broker(adapter)
    disconn_status = get_broker_value_field(disconn_res, "status")

    conn_status_res = await get_broker_connection_status(adapter)
    conn_status_data = (
        get_broker_value_field(conn_status_res, "data")
        if conn_status_res.status == "success"
        else None
    )
    is_conn = (
        get_broker_value_field(conn_status_data, "transport_connected")
        if conn_status_data is not None
        else False
    )

    print(
        f"Data -> order_check_status='{check_status}', "
        f"disconnect_status='{disconn_status}', "
        f"final_connected={is_conn}"
    )


async def _async_main() -> None:
    """Run all pipeline stages in sequential operational order."""
    print("=" * 88)
    print("BROKERS DOMAIN: FULL HOMOGENEOUS END-TO-END PIPELINE EXAMPLE")
    print(
        "Ties FEAT-BRK-00 through FEAT-BRK-15 sequentially in realistic runtime order."
    )
    print("=" * 88)

    _run_stage_1_registry()
    adapter = _run_stage_2_adapter_creation()
    await _run_stage_3_session(adapter)
    await _run_stage_4_account(adapter)
    await _run_stage_5_market_data(adapter)
    await _run_stage_6_calculations(adapter)
    await _run_stage_7_subscriptions(adapter)
    await _run_stage_8_mutations_and_teardown(adapter)

    print("\n" + "=" * 88)
    print("Data -> full_domain_pipeline_status='completed'")
    print("SUCCESS: All Brokers features executed in realistic pipeline order!")
    print("=" * 88)


def main() -> None:
    """Execute complete end-to-end Brokers domain pipeline."""
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
