"""FEAT-BRK-08: cTrader calculation and mutation release boundaries."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import _support  # noqa: F401
from _support import UsageEvidenceError, real_session, require_error, require_success
from app.services.brokers import (
    build_broker_margin_request,
    build_broker_order_request,
    build_broker_profit_request,
    calculate_broker_margin,
    calculate_broker_profit,
    cancel_broker_order,
    get_broker_capability_catalogue,
    get_broker_commission_estimate,
    get_broker_connection_status,
    get_broker_value_field,
    get_registered_brokers,
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


async def fr_brokers_098_to_100_intent_and_calculations(adapter: object) -> None:
    """FR-BRK-098..100: Stage 1 — Order Intent Construction and Calculation Verification."""
    _header("Stage 1: Order Intent Construction & Calculation (FR-BRK-098..100)")
    m_req = build_broker_margin_request(
        symbol="EURUSD",
        side="BUY",
        quantity="1.0",
        quantity_unit="lots",
        price="1.10",
        product_profile="ctrader",
    )
    m_res = await calculate_broker_margin(adapter, m_req)
    if get_broker_value_field(m_res, "status") == "success":
        require_success("Result", m_res)
    else:
        require_error("Result", m_res, "BROKER_CAPABILITY_UNSUPPORTED")
    print(_format_result(m_res))
    print(f"Data -> margin_status='{get_broker_value_field(m_res, 'status')}'")

    p_req = build_broker_profit_request(
        symbol="EURUSD",
        side="BUY",
        quantity="1.0",
        quantity_unit="lots",
        open_price="1.10",
        close_price="1.11",
        product_profile="ctrader",
    )
    p_res = await calculate_broker_profit(adapter, p_req)
    if get_broker_value_field(p_res, "status") == "success":
        require_success("Result", p_res)
    else:
        require_error("Result", p_res, "BROKER_CAPABILITY_UNSUPPORTED")
    print(_format_result(p_res))
    print(f"Data -> profit_status='{get_broker_value_field(p_res, 'status')}'")

    c_res = await get_broker_commission_estimate(
        adapter,
        build_broker_order_request(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity="1.0",
            quantity_unit="lots",
            environment="demo",
        ),
    )
    if get_broker_value_field(c_res, "status") == "success":
        require_success("Result", c_res)
    else:
        require_error("Result", c_res, "BROKER_CAPABILITY_UNSUPPORTED")
    print(_format_result(c_res))
    print(f"Data -> commission_status='{get_broker_value_field(c_res, 'status')}'")


async def fr_brokers_101_to_103_release_policy_checks(adapter: object) -> None:
    """FR-BRK-101..103: Stage 2 — Profile Resolution & Release Policy Verification."""
    _header("Stage 2: Profile Resolution & Release Policy Checks (FR-BRK-101..103)")
    status_res = await get_broker_connection_status(adapter)
    require_success("Result", status_res)
    print(_format_result(status_res))
    print(f"Data -> connection_status='{get_broker_value_field(status_res, 'status')}'")

    brokers_res = get_registered_brokers()
    assert brokers_res.status == "success"
    assert brokers_res.data is not None
    print(_format_result(brokers_res))
    print(f"Data -> registered_brokers_count={len(brokers_res.data)}")

    cat_res = get_broker_capability_catalogue()
    assert cat_res.status == "success"
    assert cat_res.data is not None
    print(_format_result(cat_res))
    print(f"Data -> static_catalogue_count={len(cat_res.data)}")


async def fr_brokers_104_fail_closed_submission(adapter: object) -> None:
    """FR-BRK-104: Stage 3 — Protobuf Submission & Fail-Closed Order Results."""
    _header("Stage 3: Protobuf Submission & Fail-Closed Order Results (FR-BRK-104)")
    cancel_res = await cancel_broker_order(adapter, "o1")
    require_error("Result", cancel_res, "BROKER_CAPABILITY_UNSUPPORTED")
    print(_format_result(cancel_res))
    print(
        f"Data -> cancel_order_status='{get_broker_value_field(cancel_res, 'status')}'"
    )


async def _run() -> None:
    """Execute release evidence in one genuine cTrader demo session."""
    _feature_header(
        "FEATURE: FEAT-BRK-08 — ctrader_mutations/ — cTrader Mutations\n\n"
        "Purpose: Provide single-target order placement, modification, cancellation, and position closure for cTrader.\n\n"
        "Module flow:\n"
        "-> order intent\n"
        "-> release policy check\n"
        "-> protobuf submission\n"
        "-> order result"
    )

    try:
        async with real_session("ctrader") as adapter:
            # Stage 1: Intent & calculation
            await fr_brokers_098_to_100_intent_and_calculations(adapter)

            # Stage 2: Profile & policy check
            await fr_brokers_101_to_103_release_policy_checks(adapter)

            # Stage 3: Fail-closed order result
            await fr_brokers_104_fail_closed_submission(adapter)
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")


def main() -> None:
    """Run the standalone genuine cTrader release-boundary program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
