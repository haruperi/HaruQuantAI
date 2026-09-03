"""Unit, contract, and scenario tests for Run Data Binding."""

import pytest
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


def test_data_bind_committed_data() -> None:
    """Verify FR-DATA-BIND_COMMITTED_DATA: binding creation and immutability."""
    run_id = _generate_uuid7()
    s1 = _generate_uuid7()
    s2 = _generate_uuid7()

    binding = data_bind_committed_data(
        run_manifest_id=run_id,
        series_version_ids=(s1, s2),
        precision="SELECTED_TIMEFRAME",
    )

    assert binding.run_manifest_id == run_id
    assert binding.series_version_ids == (s1, s2)
    assert binding.precision == "SELECTED_TIMEFRAME"
    assert binding.schema_version == 1
    assert len(binding.binding_id) > 0
    assert "T" in binding.validated_at

    # Verify invalid manifest UUID raises ValueError
    with pytest.raises(ValueError, match="Invalid run_manifest_id UUID"):
        data_bind_committed_data(
            run_manifest_id="not-a-uuid",
            series_version_ids=(s1,),
            precision="SELECTED_TIMEFRAME",
        )

    # Verify empty series version tuple raises ValueError
    with pytest.raises(ValueError, match="Precision validation failed"):
        data_bind_committed_data(
            run_manifest_id=run_id,
            series_version_ids=(),
            precision="SELECTED_TIMEFRAME",
        )


def test_data_validate_precision_inputs() -> None:
    """Verify FR-DATA-VALIDATE_PRECISION_INPUTS: fail fast without fallback."""
    s1 = _generate_uuid7()

    # Valid tick data with recorded spread
    valid, reason = data_validate_precision_inputs(
        series_version_ids=(s1,),
        precision="REAL_TICK_RECORDED_SPREAD",
        has_tick_data=True,
        has_recorded_spread=True,
    )
    assert valid is True
    assert reason is None

    # Real-tick mode with only H1 data fails with precision unavailable
    valid_h1, reason_h1 = data_validate_precision_inputs(
        series_version_ids=(s1,),
        precision="REAL_TICK_RECORDED_SPREAD",
        has_tick_data=False,
        has_recorded_spread=False,
        available_timeframe="H1",
    )
    assert valid_h1 is False
    assert reason_h1 is not None
    assert "requires recorded tick spread data" in reason_h1
    assert "no fallback permitted" in reason_h1

    # Real tick custom spread without tick data fails
    valid_custom, reason_custom = data_validate_precision_inputs(
        series_version_ids=(s1,),
        precision="REAL_TICK_CUSTOM_SPREAD",
        has_tick_data=False,
        available_timeframe="D1",
    )
    assert valid_custom is False
    assert reason_custom is not None
    assert "requires tick market data" in reason_custom

    # M1 simulation with only D1 data fails
    valid_m1, reason_m1 = data_validate_precision_inputs(
        series_version_ids=(s1,),
        precision="M1_SIMULATION",
        has_tick_data=False,
        available_timeframe="D1",
    )
    assert valid_m1 is False
    assert reason_m1 is not None
    assert "requires M1 or finer data" in reason_m1

    # Selected timeframe precision is accepted for valid timeframe data
    valid_selected, reason_selected = data_validate_precision_inputs(
        series_version_ids=(s1,),
        precision="SELECTED_TIMEFRAME",
        has_tick_data=False,
        available_timeframe="H1",
    )
    assert valid_selected is True
    assert reason_selected is None


@pytest.mark.asyncio
async def test_bind_run_data_service_bind_success() -> None:
    """Verify BindRunDataService handling of BIND request."""
    service = BindRunDataService()
    run_id = _generate_uuid7()
    s1 = _generate_uuid7()

    req = BindRunDataRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="BIND",
        run_manifest_id=run_id,
        series_version_ids=(s1,),
        precision="SELECTED_TIMEFRAME",
    )
    resp = await service.bind_run_data(req)
    assert isinstance(resp, BindRunDataSuccess)
    assert resp.outcome == "SUCCESS"
    assert resp.binding is not None
    assert resp.binding.run_manifest_id == run_id
    assert resp.binding.series_version_ids == (s1,)


@pytest.mark.asyncio
async def test_bind_run_data_service_validate_precision_success() -> None:
    """Verify BindRunDataService handling of VALIDATE_PRECISION request."""
    service = BindRunDataService()
    s1 = _generate_uuid7()

    req = BindRunDataRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="VALIDATE_PRECISION",
        series_version_ids=(s1,),
        precision="SELECTED_TIMEFRAME",
    )
    resp = await service.bind_run_data(req)
    assert isinstance(resp, BindRunDataSuccess)
    assert resp.outcome == "SUCCESS"
    assert resp.binding is None


@pytest.mark.asyncio
async def test_main_scenario_harness() -> None:
    """Verify execution of the run data binding usage harness."""
    from app.services.data.run_data_binding.run_data_binding import main

    await main()


def test_run_data_binding_persistence() -> None:
    """Verify RunDataBindingPersistence store operations."""
    from app.services.data.run_data_binding._persistence import (
        RunDataBindingPersistence,
    )
    from app.services.data.run_data_binding.run_data_binding import (
        data_bind_committed_data,
    )

    store = RunDataBindingPersistence()
    binding = data_bind_committed_data(
        run_manifest_id=_generate_uuid7(),
        series_version_ids=(_generate_uuid7(),),
        precision="SELECTED_TIMEFRAME",
    )
    store.save_binding(binding)
    assert store.get_binding(binding.binding_id) == binding
    assert len(store.get_all_bindings()) == 1
    assert store.get_binding("unknown") is None

    store.clear()
    assert len(store.get_all_bindings()) == 0
