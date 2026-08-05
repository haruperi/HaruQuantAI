"""FEAT-BRK-14: deterministic fake-adapter evidence."""

import asyncio
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import UsageEvidenceError, require_error, require_success
from app.services.brokers import (
    build_broker_connection_config,
    build_broker_value,
    connect_broker,
    create_configured_fake_broker_adapter,
    disconnect_broker,
    get_broker_quote,
    get_broker_value_field,
    set_fake_broker_error,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


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


def _quote() -> object:
    """Return one valid deterministic quote fixture."""
    return build_broker_value(
        "quote",
        symbol="EURUSD",
        price_unit="USD",
        quantity_unit="units",
        retrieved_at=_NOW,
        bid=Decimal("1.10"),
        ask=Decimal("1.11"),
    )


async def fr_brokers_133_test_config(adapter: object) -> None:
    """FR-BRK-133: Stage 1 — Test Configuration and Quote Fixture Injection."""
    _header("Stage 1: Test Configuration & Quote Fixture Injection (FR-BRK-133)")
    res = await get_broker_quote(adapter, "EURUSD")
    require_success("Result", res)
    assert get_broker_value_field(res, "data") == _quote()
    print(_format_result(res))
    print(
        f"Data -> quote_bid='{get_broker_value_field(get_broker_value_field(res, 'data'), 'bid')}'"
    )


async def fr_brokers_134_fake_instantiation(adapter: object) -> None:
    """FR-BRK-134: Stage 2 — Fake Adapter Instantiation and Error Injection."""
    _header("Stage 2: Fake Adapter Instantiation & Error Injection (FR-BRK-134)")
    require_success(
        "Injected fixture",
        set_fake_broker_error(
            adapter, "get_quote", "BROKER_TIMEOUT", "bounded timeout"
        ),
    )
    err_res = await get_broker_quote(adapter, "EURUSD")
    require_error("Injected result", err_res, "BROKER_TIMEOUT")
    print(_format_result(err_res))
    print(
        f"Data -> injected_error_status='{get_broker_value_field(err_res, 'status')}'"
    )

    require_success("Cleared fixture", set_fake_broker_error(adapter, "get_quote"))
    clr_res = await get_broker_quote(adapter, "EURUSD")
    require_success("Cleared result", clr_res)
    print(_format_result(clr_res))
    print(
        f"Data -> cleared_result_status='{get_broker_value_field(clr_res, 'status')}'"
    )


async def fr_brokers_135_simulated_outcome(adapter: object) -> None:
    """FR-BRK-135: Stage 3 — Simulated Outcome and Package-Root Boundary Export Output."""
    _header("Stage 3: Simulated Outcome & Root Export Output (FR-BRK-135)")
    del adapter
    print(_format_result(create_configured_fake_broker_adapter))
    print(
        f"Data -> root_export_callable={callable(create_configured_fake_broker_adapter)}"
    )


async def _run() -> None:
    """Execute the feature whose explicit purpose is deterministic fake behavior."""
    _feature_header(
        "FEATURE: FEAT-BRK-14 — testing/ — Deterministic Fake Adapter\n\n"
        "Purpose: Provide a deterministic test double implementing the complete BrokerAdapter surface.\n\n"
        "Module flow:\n"
        "-> test configuration\n"
        "-> fake adapter instantiation\n"
        "-> simulated outcome"
    )

    try:
        quote = _quote()
        adapter = create_configured_fake_broker_adapter(
            build_broker_connection_config(
                broker_id="yahoo",
                environment="sandbox",
                provider_enabled=True,
            ),
            {"get_quote": quote},
        )
        conn_res = await connect_broker(adapter)
        require_success("connect", conn_res)
        print(_format_result(conn_res))

        try:
            # Stage 1: Test configuration & fixture injection
            await fr_brokers_133_test_config(adapter)

            # Stage 2: Fake adapter instantiation & error injection
            await fr_brokers_134_fake_instantiation(adapter)

            # Stage 3: Simulated outcome & root export
            await fr_brokers_135_simulated_outcome(adapter)
        finally:
            dis_res = await disconnect_broker(adapter)
            require_success("disconnect", dis_res)
            print(_format_result(dis_res))
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")
        raise SystemExit(1) from err


def main() -> None:
    """Run the standalone deterministic fake-adapter feature program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
