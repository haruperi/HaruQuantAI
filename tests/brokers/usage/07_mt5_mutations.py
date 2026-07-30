"""FEAT-BRK-07: MetaTrader 5 mutation capability safety."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import _support  # noqa: F401
from _support import (
    UsageEvidenceError,
    create_real_adapter,
    real_session,
    require_error,
    require_success,
)
from app.services.brokers import (
    build_broker_order_modification_request,
    build_broker_order_request,
    build_broker_position_close_request,
    build_broker_position_modification_request,
    cancel_broker_order,
    check_broker_order,
    close_broker_position,
    disconnect_broker,
    get_broker_connection_status,
    get_broker_value_field,
    modify_broker_order,
    modify_broker_position,
    place_broker_order,
    replace_broker_order,
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


def _order() -> object:
    """Build one bounded demo order request without transmitting it."""
    return build_broker_order_request(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity="0.01",
        quantity_unit="lots",
        environment="demo",
    )


async def fr_brokers_091_to_092_order_intent_and_check(adapter: object) -> None:
    """FR-BRK-091..092: Stage 1 & 2 — Order Intent Construction and Release Policy Check."""
    _header("Stage 1 & 2: Order Intent & Release Policy Check (FR-BRK-091..092)")
    chk_res = await check_broker_order(adapter, _order())
    require_error(
        "Result", chk_res, "BROKER_NOT_CONNECTED", "BROKER_CAPABILITY_UNSUPPORTED"
    )
    print(_format_result(chk_res))
    print(f"Data -> check_order_status='{get_broker_value_field(chk_res, 'status')}'")

    plc_res = await place_broker_order(adapter, _order())
    require_error(
        "Result", plc_res, "BROKER_NOT_CONNECTED", "BROKER_CAPABILITY_UNSUPPORTED"
    )
    print(_format_result(plc_res))
    print(f"Data -> place_order_status='{get_broker_value_field(plc_res, 'status')}'")


async def fr_brokers_093_to_097_order_results(adapter: object) -> None:
    """FR-BRK-093..097: Stage 3 — Provider Submission & Order Result / Fail-Closed Output."""
    _header(
        "Stage 3: Provider Submission & Fail-Closed Order Results (FR-BRK-093..097)"
    )
    mod_req = build_broker_order_modification_request("o1", limit_price="1.11")
    mod_res = await modify_broker_order(adapter, mod_req)
    require_error(
        "Result", mod_res, "BROKER_CAPABILITY_UNSUPPORTED", "BROKER_NOT_CONNECTED"
    )
    print(_format_result(mod_res))
    print(f"Data -> modify_order_status='{get_broker_value_field(mod_res, 'status')}'")

    cnl_res = await cancel_broker_order(adapter, "o1")
    require_error(
        "Result", cnl_res, "BROKER_NOT_CONNECTED", "BROKER_CAPABILITY_UNSUPPORTED"
    )
    print(_format_result(cnl_res))
    print(f"Data -> cancel_order_status='{get_broker_value_field(cnl_res, 'status')}'")

    pos_mod_req = build_broker_position_modification_request("p1", stop_loss="1.09")
    pos_mod_res = await modify_broker_position(adapter, pos_mod_req)
    require_error(
        "Result", pos_mod_res, "BROKER_CAPABILITY_UNSUPPORTED", "BROKER_NOT_CONNECTED"
    )
    print(_format_result(pos_mod_res))
    print(
        f"Data -> modify_position_status='{get_broker_value_field(pos_mod_res, 'status')}'"
    )

    cls_req = build_broker_position_close_request(
        "p1", quantity="0.5", quantity_unit="lots"
    )
    cls_res = await close_broker_position(adapter, cls_req)
    require_error(
        "Result", cls_res, "BROKER_NOT_CONNECTED", "BROKER_CAPABILITY_UNSUPPORTED"
    )
    print(_format_result(cls_res))
    print(
        f"Data -> close_position_status='{get_broker_value_field(cls_res, 'status')}'"
    )

    rep_res = await replace_broker_order(adapter, mod_req)
    require_error(
        "Result", rep_res, "BROKER_CAPABILITY_UNSUPPORTED", "BROKER_NOT_CONNECTED"
    )
    print(_format_result(rep_res))
    print(f"Data -> replace_order_status='{get_broker_value_field(rep_res, 'status')}'")


async def _run() -> None:
    """Verify a real MT5 demo session, then prove mutations remain no-side-effect."""
    _feature_header(
        "FEATURE: FEAT-BRK-07 — mt5_mutations/ — MetaTrader 5 Mutations\n\n"
        "Purpose: Provide single-target order placement, modification, cancellation, and position closure for MT5.\n\n"
        "Module flow:\n"
        "-> order intent\n"
        "-> release policy check\n"
        "-> provider submission\n"
        "-> order result"
    )

    try:
        async with real_session("mt5") as connected:
            status_res = await get_broker_connection_status(connected)
            require_success("Verified demo status", status_res)
            print(_format_result(status_res))

        disconnected = create_real_adapter("mt5")
        # Stage 1 & 2: Order intent & release policy check
        await fr_brokers_091_to_092_order_intent_and_check(disconnected)

        # Stage 3: Fail-closed order results
        await fr_brokers_093_to_097_order_results(disconnected)

        clean_res = await disconnect_broker(disconnected)
        require_success("Final cleanup", clean_res)
        print(_format_result(clean_res))
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")


def main() -> None:
    """Run the genuine-session, no-mutation MT5 safety program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
