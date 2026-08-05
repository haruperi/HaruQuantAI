"""FEAT-BRK-07: MetaTrader 5 mutation capability safety."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import UsageEvidenceError, real_session, require_error, require_success
from app.services.brokers import (
    build_broker_order_modification_request,
    build_broker_order_request,
    build_broker_position_close_request,
    build_broker_position_modification_request,
    cancel_broker_order,
    check_broker_order,
    close_broker_position,
    get_broker_connection_status,
    get_broker_value_field,
    modify_broker_order,
    modify_broker_position,
    replace_broker_order,
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
    require_success("Result", chk_res)
    print(_format_result(chk_res))
    print(f"Data -> check_order_status='{get_broker_value_field(chk_res, 'status')}'")


async def _run_mutation_op(adapter: object, operation: str) -> None:
    """Exercise one mutation operation safely checking capability support."""
    capability_map = {
        "modify_order": "modify_order",
        "cancel_order": "cancel_order",
        "modify_position": "modify_position",
        "close_position": "close_position",
        "replace_order": "replace_order",
    }
    cap_name = capability_map.get(operation, operation)
    supp_res = await supports_broker_capability(adapter, cap_name)
    if get_broker_value_field(supp_res, "data"):
        if operation == "modify_order":
            req = build_broker_order_modification_request("o1", limit_price="1.11")
            res = await modify_broker_order(adapter, req)
        elif operation == "cancel_order":
            res = await cancel_broker_order(adapter, "o1")
        elif operation == "modify_position":
            req = build_broker_position_modification_request("p1", stop_loss="1.09")
            res = await modify_broker_position(adapter, req)
        elif operation == "close_position":
            req = build_broker_position_close_request(
                "p1", quantity="0.5", quantity_unit="lots"
            )
            res = await close_broker_position(adapter, req)
        else:
            req = build_broker_order_modification_request("o1", limit_price="1.11")
            res = await replace_broker_order(adapter, req)
        require_error("Result", res, "BROKER_REQUEST_INVALID", "BROKER_ORDER_NOT_FOUND")
        print(_format_result(res))
        print(
            f"Data -> operation='{operation}', status='{get_broker_value_field(res, 'status')}'"
        )
    else:
        print(f"Data -> operation='{operation}', status='unsupported_on_provider'")


async def fr_brokers_093_to_097_order_results(adapter: object) -> None:
    """FR-BRK-093..097: Stage 3 — Provider Submission & Order Result / Fail-Closed Output."""
    _header(
        "Stage 3: Provider Submission & Fail-Closed Order Results (FR-BRK-093..097)"
    )
    for op in (
        "modify_order",
        "cancel_order",
        "modify_position",
        "close_position",
        "replace_order",
    ):
        await _run_mutation_op(adapter, op)


async def _run() -> None:
    """Verify a real MT5 demo session, then prove mutation operations capability boundaries."""
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
        async with real_session("mt5") as adapter:
            status_res = await get_broker_connection_status(adapter)
            require_success("Verified demo status", status_res)
            print(_format_result(status_res))

            # Stage 1 & 2: Order intent & release policy check
            await fr_brokers_091_to_092_order_intent_and_check(adapter)

            # Stage 3: Fail-closed order results
            await fr_brokers_093_to_097_order_results(adapter)
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")
        raise SystemExit(1) from err


def main() -> None:
    """Run the genuine-session MT5 mutation capability program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
