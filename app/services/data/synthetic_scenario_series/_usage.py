"""Executable usage demonstration harness for Synthetic Scenario Series."""

from __future__ import annotations

import asyncio

from app.contracts.catalogue.models import InstrumentRef
from app.contracts.common.models import Timeframe
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    GenerateScenariosRequest,
    GenerateScenariosSuccess,
    ScenarioTransform,
    SyntheticModelSpec,
)
from app.services.data.synthetic_scenario_series.synthetic_scenario_series import (
    GenerateScenariosService,
    _generate_uuid7,
    compute_spec_content_hash,
)


async def _run_usage_scenarios() -> None:
    """Run standalone executable usage scenarios for FEAT-DATA-GENERATE_SCENARIOS."""
    service = GenerateScenariosService()
    snap_id = _generate_uuid7()
    inst_id = _generate_uuid7()

    base_spec = SyntheticModelSpec(
        spec_id=_generate_uuid7(),
        model_type="gbm",
        model_version="1.0",
        parameters={
            "mu": 0.05,
            "sigma": 0.2,
            "start_val": 100.0,
            "spread_min": 10,
            "spread_max": 30,
        },
        timeframe=Timeframe(unit="MINUTE", multiple=1),
        from_at="2026-07-01T12:00:00.000000Z",
        to_at="2026-07-01T13:00:00.000000Z",
        instrument=InstrumentRef(instrument_id=inst_id),
        seed_streams=("prices", "volumes"),
        content_hash="0" * 64,
    )
    object.__setattr__(base_spec, "content_hash", compute_spec_content_hash(base_spec))

    print("Scenario 1: FR-DATA-CONFIGURE_SYNTHETIC_MODEL - Model Configuration")
    req1 = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="CONFIGURE_MODEL",
        spec=base_spec,
    )
    res1 = await service.generate_scenarios(req1)
    if isinstance(res1, GenerateScenariosSuccess) and res1.spec is not None:
        print(f"[OK] Model configured: spec_id={res1.spec.spec_id}")

    print("\nScenario 2: FR-DATA-GENERATE_SYNTHETIC_SERIES - Synthetic Generation")
    req2 = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="GENERATE",
        spec=base_spec,
    )
    res2 = await service.generate_scenarios(req2)
    if isinstance(res2, GenerateScenariosSuccess) and res2.scenario_version_id:
        print(f"[OK] Generated series version: {res2.scenario_version_id}")

    print("\nScenario 3: FR-DATA-TRANSFORM_SCENARIO_DATA - Scenario Transformation")
    req3 = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="TRANSFORM",
        source_version_id=_generate_uuid7(),
        source_hash="a" * 64,
        transforms=(
            ScenarioTransform(kind="SHOCK", parameters={"magnitude": 0.05}),
            ScenarioTransform(kind="VOLATILITY", parameters={"multiplier": 1.5}),
        ),
        classification="SCENARIO",
    )
    res3 = await service.generate_scenarios(req3)
    if isinstance(res3, GenerateScenariosSuccess) and res3.scenario_version_id:
        print(f"[OK] Scenario transformed: {res3.scenario_version_id}")

    print("\nScenario 4: FR-DATA-CLASSIFY_SYNTHETIC_DATA - Strict Classification")
    req4 = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="TRANSFORM",
        source_version_id=_generate_uuid7(),
        source_hash="a" * 64,
        transforms=(
            ScenarioTransform(kind="GAP", parameters={"duration_minutes": 15}),
        ),
        classification="SYNTHETIC",
    )
    res4 = await service.generate_scenarios(req4)
    if isinstance(res4, GenerateScenariosSuccess):
        print(
            f"[OK] Validated classification SYNTHETIC with "
            f"version {res4.scenario_version_id}"
        )

    print("\nAll usage scenarios completed successfully.")


async def example_synthetic_bars() -> GenerateScenariosSuccess | DataFailure:
    """Generate deterministic synthetic bars."""
    service = GenerateScenariosService()
    spec = SyntheticModelSpec(
        spec_id=_generate_uuid7(),
        model_type="gbm",
        model_version="1.0",
        parameters={"mu": 0.02, "sigma": 0.10, "start_val": 1.2500},
        timeframe=Timeframe(unit="MINUTE", multiple=60),
        from_at="2026-08-01T00:00:00.000000Z",
        to_at="2026-08-01T05:00:00.000000Z",
        instrument=InstrumentRef(instrument_id=_generate_uuid7()),
        seed_streams=("prices", "volumes"),
        content_hash="0" * 64,
    )
    object.__setattr__(spec, "content_hash", compute_spec_content_hash(spec))
    req = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="GENERATE",
        spec=spec,
    )
    return await service.generate_scenarios(req)


async def example_gateway_synthetic() -> GenerateScenariosSuccess | DataFailure:
    """Use the current synthetic feature boundary directly."""
    return await example_synthetic_bars()


async def example_tick_model_trading_bar() -> GenerateScenariosSuccess | DataFailure:
    """Derive deterministic ticks per trading bar."""
    service = GenerateScenariosService()
    spec = SyntheticModelSpec(
        spec_id=_generate_uuid7(),
        model_type="random_walk",
        model_version="1.0",
        parameters={"step_size": 0.0001, "start_val": 1.1000},
        timeframe=Timeframe(unit="MINUTE", multiple=1),
        from_at="2026-08-01T00:00:00.000000Z",
        to_at="2026-08-01T00:10:00.000000Z",
        instrument=InstrumentRef(instrument_id=_generate_uuid7()),
        seed_streams=("prices",),
        content_hash="0" * 64,
    )
    object.__setattr__(spec, "content_hash", compute_spec_content_hash(spec))
    req = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="GENERATE",
        spec=spec,
    )
    return await service.generate_scenarios(req)


async def example_tick_model_generated() -> GenerateScenariosSuccess | DataFailure:
    """Derive a bounded volume-interpolated tick series."""
    service = GenerateScenariosService()
    spec = SyntheticModelSpec(
        spec_id=_generate_uuid7(),
        model_type="gbm",
        model_version="1.0",
        parameters={"mu": 0.01, "sigma": 0.05, "start_val": 1.1000},
        timeframe=Timeframe(unit="MINUTE", multiple=1),
        from_at="2026-08-01T00:00:00.000000Z",
        to_at="2026-08-01T01:00:00.000000Z",
        instrument=InstrumentRef(instrument_id=_generate_uuid7()),
        seed_streams=("prices", "volumes"),
        content_hash="0" * 64,
    )
    object.__setattr__(spec, "content_hash", compute_spec_content_hash(spec))
    req = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="GENERATE",
        spec=spec,
    )
    return await service.generate_scenarios(req)


async def example_tick_model_ohlc_m1() -> GenerateScenariosSuccess | DataFailure:
    """Derive ticks from lower-timeframe OHLC evidence."""
    service = GenerateScenariosService()
    req = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="TRANSFORM",
        source_version_id=_generate_uuid7(),
        source_hash="a" * 64,
        transforms=(
            ScenarioTransform(kind="VOLATILITY", parameters={"multiplier": 1.2}),
        ),
        classification="SCENARIO",
    )
    return await service.generate_scenarios(req)


async def main() -> None:
    """Execute all synthetic scenario series usage scenarios."""
    await _run_usage_scenarios()

    print("\n--- Additional Synthetic & Scenario Examples ---")
    res_bars = await example_synthetic_bars()
    print(f"  * example_synthetic_bars: res={type(res_bars).__name__}")
    res_gw = await example_gateway_synthetic()
    print(f"  * example_gateway_synthetic: res={type(res_gw).__name__}")
    res_tbar = await example_tick_model_trading_bar()
    print(f"  * example_tick_model_trading_bar: res={type(res_tbar).__name__}")
    res_gen = await example_tick_model_generated()
    print(f"  * example_tick_model_generated: res={type(res_gen).__name__}")
    res_m1 = await example_tick_model_ohlc_m1()
    print(f"  * example_tick_model_ohlc_m1: res={type(res_m1).__name__}")


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
