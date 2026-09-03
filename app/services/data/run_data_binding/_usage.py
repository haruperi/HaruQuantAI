"""Executable usage demonstration harness for Run Data Binding."""

from __future__ import annotations

import asyncio

from app.contracts.data.models import (
    BindRunDataRequest,
    BindRunDataSuccess,
)
from app.services.data.run_data_binding.run_data_binding import (
    BindRunDataService,
    _generate_uuid7,
    data_bind_committed_data,
    data_validate_precision_inputs,
)


async def main() -> None:
    """Run teaching and usage evidence scenarios for Run Data Binding."""
    print("=== Scenario 1: FR-DATA-BIND_COMMITTED_DATA ===")
    run_id = _generate_uuid7()
    s1 = _generate_uuid7()
    s2 = _generate_uuid7()
    binding = data_bind_committed_data(
        run_manifest_id=run_id,
        series_version_ids=(s1, s2),
        precision="SELECTED_TIMEFRAME",
    )
    assert bool(binding.binding_id)
    print(f"Bound manifest {run_id} -> binding_id {binding.binding_id}")
    print(f"Series versions bound: {binding.series_version_ids}")
    print(f"Validated at: {binding.validated_at}")

    print()
    print("=== Scenario 2: FR-DATA-VALIDATE_PRECISION_INPUTS ===")
    valid_tick, msg1 = data_validate_precision_inputs(
        series_version_ids=(s1,),
        precision="REAL_TICK_RECORDED_SPREAD",
        has_tick_data=True,
        has_recorded_spread=True,
    )
    assert valid_tick is True
    print(f"Valid tick check: {valid_tick} (reason={msg1})")

    invalid_h1, msg2 = data_validate_precision_inputs(
        series_version_ids=(s1,),
        precision="REAL_TICK_RECORDED_SPREAD",
        has_tick_data=False,
        has_recorded_spread=False,
        available_timeframe="H1",
    )
    assert invalid_h1 is False
    print(f"Invalid H1 for real-tick check: valid={invalid_h1}, reason='{msg2}'")

    service = BindRunDataService()
    req = BindRunDataRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="BIND",
        run_manifest_id=run_id,
        series_version_ids=(s1,),
        precision="M1_SIMULATION",
    )
    res = await service.bind_run_data(req)
    assert isinstance(res, BindRunDataSuccess) and res.outcome == "SUCCESS"
    print(f"Service BIND result: outcome={res.outcome}")


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
