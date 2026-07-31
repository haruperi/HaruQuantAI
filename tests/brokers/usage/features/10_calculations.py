"""FEAT-BRK-10: genuine provider-native calculations."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import (
    UsageEvidenceError,
    create_real_adapter,
    real_session,
    require_error,
    require_success,
)
from app.services.brokers import (
    build_broker_margin_request,
    build_broker_order_request,
    build_broker_profit_request,
    calculate_broker_margin,
    calculate_broker_profit,
    disconnect_broker,
    get_broker_commission_estimate,
    get_broker_value_field,
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


def _margin_request() -> object:
    """Build one bounded genuine provider margin request."""
    return build_broker_margin_request(
        symbol="EURUSD",
        side="BUY",
        quantity="0.01",
        quantity_unit="lots",
        price="1.10",
        product_profile="mt5",
    )


def _profit_request() -> object:
    """Build one bounded genuine provider profit request."""
    return build_broker_profit_request(
        symbol="EURUSD",
        side="BUY",
        quantity="0.01",
        quantity_unit="lots",
        open_price="1.10",
        close_price="1.11",
        product_profile="mt5",
    )


async def fr_brokers_112_to_114_margin_and_profit(adapter: object) -> None:
    """FR-BRK-112..114: Stage 1 & 2 — Calculation Request & Formula Execution."""
    _header("Stage 1 & 2: Calculation Request & Formula Execution (FR-BRK-112..114)")
    m_res = await calculate_broker_margin(adapter, _margin_request())
    require_success("Result", m_res)
    print(_format_result(m_res))
    print(f"Data -> margin_status='{get_broker_value_field(m_res, 'status')}'")

    p_res = await calculate_broker_profit(adapter, _profit_request())
    require_success("Result", p_res)
    print(_format_result(p_res))
    print(f"Data -> profit_status='{get_broker_value_field(p_res, 'status')}'")


async def fr_brokers_115_to_117_results_and_safety(
    adapter: object, disconnected: object
) -> None:
    """FR-BRK-115..117: Stage 3 — Margin/Profit Result & Safety Gates Output."""
    _header("Stage 3: Margin/Profit Results & Safety Output (FR-BRK-115..117)")
    c_res = await get_broker_commission_estimate(
        adapter,
        build_broker_order_request("EURUSD", "BUY", "MARKET", "0.01", "lots", "demo"),
    )
    if get_broker_value_field(c_res, "status") == "success":
        require_success("Result", c_res)
    else:
        require_error("Result", c_res, "BROKER_CAPABILITY_UNSUPPORTED")
    print(_format_result(c_res))
    print(f"Data -> commission_status='{get_broker_value_field(c_res, 'status')}'")

    dis_m_res = await calculate_broker_margin(disconnected, _margin_request())
    require_error("Result", dis_m_res, "BROKER_NOT_CONNECTED")
    print(_format_result(dis_m_res))
    print(
        f"Data -> disconnected_margin_status='{get_broker_value_field(dis_m_res, 'status')}'"
    )


async def _run() -> None:
    """Execute genuine calculations and disconnected fail-closed evidence."""
    _feature_header(
        "FEATURE: FEAT-BRK-10 — provider_calculations/ — Provider Calculations\n\n"
        "Purpose: Provide provider-native margin and profit calculations.\n\n"
        "Module flow:\n"
        "-> calculation request\n"
        "-> provider formula execution\n"
        "-> margin/profit result"
    )

    try:
        async with real_session("mt5") as adapter:
            disconnected = create_real_adapter("mt5")
            # Stage 1 & 2: Calculation request & formula execution
            await fr_brokers_112_to_114_margin_and_profit(adapter)

            # Stage 3: Margin/profit result & safety gates output
            await fr_brokers_115_to_117_results_and_safety(adapter, disconnected)

            clean_res = await disconnect_broker(disconnected)
            require_success("Final cleanup", clean_res)
            print(_format_result(clean_res))
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")


def main() -> None:
    """Run the standalone genuine provider-calculation program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
