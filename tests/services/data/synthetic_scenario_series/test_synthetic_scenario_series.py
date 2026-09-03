"""Unit tests for Synthetic and Scenario Series domain service."""

import pytest
from app.contracts.catalogue.models import InstrumentRef
from app.contracts.common.models import Timeframe
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    GenerateScenariosRequest,
    GenerateScenariosSuccess,
    ScenarioTransform,
    SyntheticModelSpec,
)
from app.services.data.synthetic_scenario_series.config import (
    SyntheticScenarioSeriesConfig,
)
from app.services.data.synthetic_scenario_series.synthetic_scenario_series import (
    GenerateScenariosService,
    _generate_uuid7,
    _run_usage_scenarios,
    compute_spec_content_hash,
)


def _make_spec(
    *,
    spec_id: str | None = None,
    mu: float = 0.05,
    sigma: float = 0.2,
    start_val: float = 100.0,
    from_at: str = "2026-07-01T12:00:00.000000Z",
    to_at: str = "2026-07-01T13:00:00.000000Z",
) -> SyntheticModelSpec:
    spec = SyntheticModelSpec(
        spec_id=spec_id or _generate_uuid7(),
        model_type="gbm",
        model_version="1.0",
        parameters={
            "mu": mu,
            "sigma": sigma,
            "start_val": start_val,
            "spread_min": 10,
            "spread_max": 20,
        },
        timeframe=Timeframe(unit="MINUTE", multiple=1),
        from_at=from_at,
        to_at=to_at,
        instrument=InstrumentRef(instrument_id=_generate_uuid7()),
        seed_streams=("prices", "volumes"),
        content_hash="0" * 64,
    )
    object.__setattr__(spec, "content_hash", compute_spec_content_hash(spec))
    return spec


@pytest.mark.asyncio
async def test_configure_model_success() -> None:
    """Test FR-DATA-CONFIGURE_SYNTHETIC_MODEL standard success."""
    service = GenerateScenariosService()
    spec = _make_spec()
    req = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="CONFIGURE_MODEL",
        spec=spec,
    )
    res = await service.generate_scenarios(req)
    assert isinstance(res, GenerateScenariosSuccess)
    assert res.spec == spec
    assert res.outcome == "SUCCESS"


@pytest.mark.asyncio
async def test_configure_model_invalid_params() -> None:
    """Test rejection of invalid parameters."""
    service = GenerateScenariosService()
    spec = _make_spec(sigma=0.2)
    # Manually modify to invalid parameter
    object.__setattr__(
        spec, "parameters", {"mu": 0.05, "sigma": -0.2, "start_val": 100.0}
    )
    req = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="CONFIGURE_MODEL",
        spec=spec,
    )
    res = await service.generate_scenarios(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_generate_synthetic_series_reproducibility() -> None:
    """Test FR-DATA-GENERATE_SYNTHETIC_SERIES determinism and invariants."""
    service = GenerateScenariosService()
    spec_id = _generate_uuid7()
    spec1 = _make_spec(spec_id=spec_id)
    spec2 = _make_spec(spec_id=spec_id)

    req1 = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="GENERATE",
        spec=spec1,
    )
    req2 = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="GENERATE",
        spec=spec2,
    )

    res1 = await service.generate_scenarios(req1)
    res2 = await service.generate_scenarios(req2)

    assert isinstance(res1, GenerateScenariosSuccess)
    assert isinstance(res2, GenerateScenariosSuccess)
    assert res1.scenario_version_id is not None
    assert res2.scenario_version_id is not None


@pytest.mark.asyncio
async def test_generate_limit_exceeded() -> None:
    """Test record limit enforcement."""
    service = GenerateScenariosService(
        config=SyntheticScenarioSeriesConfig(max_records=10)
    )
    spec = _make_spec(
        from_at="2026-07-01T00:00:00.000000Z",
        to_at="2026-07-01T12:00:00.000000Z",
    )
    req = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="GENERATE",
        spec=spec,
    )
    res = await service.generate_scenarios(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_transform_scenario_data() -> None:
    """Test FR-DATA-TRANSFORM_SCENARIO_DATA applying bounded transforms."""
    service = GenerateScenariosService()
    source_vid = _generate_uuid7()
    req = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="TRANSFORM",
        source_version_id=source_vid,
        source_hash="b" * 64,
        transforms=(
            ScenarioTransform(kind="SHOCK", parameters={"magnitude": 0.1}),
            ScenarioTransform(kind="GAP", parameters={"duration_minutes": 30}),
            ScenarioTransform(kind="VOLATILITY", parameters={"multiplier": 2.0}),
            ScenarioTransform(kind="LIQUIDITY", parameters={"multiplier": 0.5}),
            ScenarioTransform(kind="OUTAGE", parameters={"duration_seconds": 600}),
            ScenarioTransform(kind="MISSINGNESS", parameters={"drop_ratio": 0.05}),
        ),
        classification="SCENARIO",
    )
    res = await service.generate_scenarios(req)
    assert isinstance(res, GenerateScenariosSuccess)
    assert res.scenario_version_id is not None


@pytest.mark.asyncio
async def test_classify_synthetic_data() -> None:
    """Test FR-DATA-CLASSIFY_SYNTHETIC_DATA classification verification."""
    service = GenerateScenariosService()
    req = GenerateScenariosRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="TRANSFORM",
        source_version_id=_generate_uuid7(),
        source_hash="c" * 64,
        transforms=(ScenarioTransform(kind="SHOCK", parameters={"magnitude": 0.01}),),
        classification="SYNTHETIC",
    )
    res = await service.generate_scenarios(req)
    assert isinstance(res, GenerateScenariosSuccess)


@pytest.mark.asyncio
async def test_generate_scenarios_validation_failures() -> None:
    """Verify DataFailure on missing spec, missing source_version_id, or unsupported operation."""
    service = GenerateScenariosService()

    # CONFIGURE_MODEL with spec=None
    req_no_spec = GenerateScenariosRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="CONFIGURE_MODEL",
        spec=None,
        schema_version=1,
    )
    res1 = await service.generate_scenarios(req_no_spec)
    assert isinstance(res1, DataFailure)
    assert res1.code == "DATA_VALIDATION_FAILED"

    # GENERATE with spec=None
    req_gen_no_spec = GenerateScenariosRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="GENERATE",
        spec=None,
        schema_version=1,
    )
    res2 = await service.generate_scenarios(req_gen_no_spec)
    assert isinstance(res2, DataFailure)
    assert res2.code == "DATA_VALIDATION_FAILED"

    # TRANSFORM with source_version_id=None
    req_no_src = GenerateScenariosRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="TRANSFORM",
        source_version_id=None,
        source_hash="a" * 64,
        transforms=(ScenarioTransform(kind="SHOCK", parameters={"magnitude": 0.01}),),
        schema_version=1,
    )
    res3 = await service.generate_scenarios(req_no_src)
    assert isinstance(res3, DataFailure)
    assert res3.code == "DATA_VALIDATION_FAILED"

    # TRANSFORM with transforms=None
    req_no_trans = GenerateScenariosRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="TRANSFORM",
        source_version_id=_generate_uuid7(),
        source_hash="a" * 64,
        transforms=None,
        schema_version=1,
    )
    res4 = await service.generate_scenarios(req_no_trans)
    assert isinstance(res4, DataFailure)
    assert res4.code == "DATA_VALIDATION_FAILED"

    # Unsupported operation
    req_unsupported = GenerateScenariosRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="UNSUPPORTED_OP",
        schema_version=1,
    )
    res5 = await service.generate_scenarios(req_unsupported)
    assert isinstance(res5, DataFailure)
    assert res5.code == "DATA_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_run_usage_scenarios_harness() -> None:
    """Verify execution of standalone usage scenarios."""
    await _run_usage_scenarios()


def test_synthetic_scenario_persistence() -> None:
    """Verify SyntheticScenarioPersistence operations."""
    from app.services.data.synthetic_scenario_series._persistence import (
        SyntheticScenarioPersistence,
    )

    store = SyntheticScenarioPersistence()
    spec_id = _generate_uuid7()
    from app.contracts.data.models import SyntheticModelSpec

    spec = SyntheticModelSpec(
        spec_id=spec_id,
        model_type="gbm",
        model_version="1.0",
        parameters={},
        timeframe=Timeframe(unit="MINUTE", multiple=1),
        from_at="2026-07-01T12:00:00.000000Z",
        to_at="2026-07-01T13:00:00.000000Z",
        instrument=InstrumentRef(instrument_id=_generate_uuid7()),
        seed_streams=(),
        content_hash="0" * 64,
    )
    store.save_spec(spec)
    assert store.get_spec(spec_id) == spec
    assert len(store.get_all_specs()) == 1

    scenario_id = _generate_uuid7()
    store.save_scenario(scenario_id, "0" * 64, "SYNTHETIC")
    assert store.get_scenario(scenario_id) == ("0" * 64, "SYNTHETIC")
    assert store.get_scenario("unknown") is None

    store.clear()
    assert len(store.get_all_specs()) == 0
