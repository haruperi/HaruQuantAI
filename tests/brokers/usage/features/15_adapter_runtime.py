"""FEAT-BRK-15: exercise runtime lifecycle through a genuine provider adapter."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from _support import UsageEvidenceError, real_session, require_success
from app.services.brokers import get_broker_connection_status, get_broker_value_field


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


async def fr_brokers_runtime_lifecycle(adapter: object) -> None:
    """FR-BRK-135: Stage 1..3 — Failure Trigger, Breaker State Transition, & Circuit State Report."""
    _header(
        "Stage 1..3: Failure Trigger, Breaker Transition & Circuit Report (FR-BRK-135)"
    )
    status = await get_broker_connection_status(adapter)
    require_success("status", status)
    data = get_broker_value_field(status, "data")
    assert data is not None
    assert get_broker_value_field(data, "transport_connected")

    print(_format_result(status))
    print(
        f"Data -> connection_state='{get_broker_value_field(data, 'state')}', execution_ms={get_broker_value_field(get_broker_value_field(status, 'metadata'), 'execution_ms')}"
    )


async def _run() -> None:
    """Exercise runtime lifecycle and invocation-local result wrapping."""
    _feature_header(
        "FEATURE: FEAT-BRK-15 — adapter_runtime/ — Adapter Runtime\n\n"
        "Purpose: Provide transport circuit breaking and subscription channel management.\n\n"
        "Module flow:\n"
        "-> failure trigger\n"
        "-> breaker state transition\n"
        "-> circuit state report"
    )

    try:
        async with real_session("mt5") as adapter:
            # Stage 1..3: Failure trigger to breaker transition to circuit state report
            await fr_brokers_runtime_lifecycle(adapter)
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")
        raise SystemExit(1) from err


def main() -> None:
    """Run the standalone genuine adapter-runtime usage program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
