"""Unit, contract, and scenario tests for Volume Profile Source Preparation."""

from decimal import Decimal

import pytest
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    PrepareProfilesRequest,
    PrepareProfilesSuccess,
)
from app.services.data.profile_source_preparation.profile_source_preparation import (
    PrepareProfilesService,
    _generate_uuid7,
    data_validate_profile_source,
)


def test_data_validate_profile_source_valid_tick() -> None:
    """Verify FR-DATA-VALIDATE_PROFILE_SOURCE: valid tick source validation and sufficiency."""
    data_id = _generate_uuid7()
    session_id = _generate_uuid7()

    source = data_validate_profile_source(
        data_version_id=data_id,
        source_kind="TICK",
        session_version_id=session_id,
        price_step=Decimal("0.25"),
        bin_count=120,
        sample_coverage_ratio=0.99,
    )

    assert source.data_version_id == data_id
    assert source.source_kind == "TICK"
    assert source.session_version_id == session_id
    assert source.price_step == "0.25"
    assert source.bin_count == 120
    assert source.is_sufficient is True
    assert len(source.coverage_diagnostics) == 0


def test_data_validate_profile_source_valid_lower_granularity() -> None:
    """Verify FR-DATA-VALIDATE_PROFILE_SOURCE: valid lower-granularity source."""
    data_id = _generate_uuid7()
    session_id = _generate_uuid7()

    source = data_validate_profile_source(
        data_version_id=data_id,
        source_kind="LOWER_GRANULARITY",
        session_version_id=session_id,
        price_step="0.01",
        bin_count=50,
        sample_coverage_ratio=0.98,
    )

    assert source.source_kind == "LOWER_GRANULARITY"
    assert source.price_step == "0.01"
    assert source.is_sufficient is True
    assert len(source.coverage_diagnostics) == 0


def test_data_validate_profile_source_invalid_granularity_and_data_version() -> None:
    """Verify diagnostics for invalid source_kind and data_version_id."""
    session_id = _generate_uuid7()

    source = data_validate_profile_source(
        data_version_id="not-a-uuid",
        source_kind="HOURLY",
        session_version_id=session_id,
        price_step=Decimal("0.10"),
    )

    assert source.is_sufficient is False
    codes = {d.code for d in source.coverage_diagnostics}
    assert "DATA_VERSION_INVALID" in codes
    assert "INVALID_SOURCE_KIND" in codes


def test_data_validate_profile_source_missing_session_boundaries() -> None:
    """Verify diagnostics when session boundaries are missing/invalid."""
    data_id = _generate_uuid7()

    source = data_validate_profile_source(
        data_version_id=data_id,
        source_kind="TICK",
        session_version_id="invalid-session-id",
        price_step=Decimal("0.50"),
        require_session_alignment=True,
    )
    assert source.is_sufficient is False
    assert any(
        d.code == "SESSION_BOUNDARY_MISSING" for d in source.coverage_diagnostics
    )

    source_unaligned = data_validate_profile_source(
        data_version_id=data_id,
        source_kind="TICK",
        session_version_id="invalid-session-id",
        price_step=Decimal("0.50"),
        require_session_alignment=False,
    )
    assert source_unaligned.is_sufficient is True
    assert any(
        d.code == "SESSION_BOUNDARY_UNALIGNED"
        for d in source_unaligned.coverage_diagnostics
    )


def test_data_validate_profile_source_price_step_and_bin_diagnostics() -> None:
    """Verify diagnostics for below-min price step and excessive bin count."""
    data_id = _generate_uuid7()
    session_id = _generate_uuid7()

    source = data_validate_profile_source(
        data_version_id=data_id,
        source_kind="TICK",
        session_version_id=session_id,
        price_step=Decimal("0.00000000001"),
        bin_count=20_000,
        min_price_step=Decimal("0.00001"),
        max_bin_count=5000,
    )

    assert source.is_sufficient is False
    codes = {d.code for d in source.coverage_diagnostics}
    assert "PRICE_STEP_TOO_SMALL" in codes
    assert "BIN_COUNT_EXCEEDED" in codes


def test_data_validate_profile_source_incomplete_coverage() -> None:
    """Verify coverage incomplete diagnostics for ratio < 95%."""
    data_id = _generate_uuid7()
    session_id = _generate_uuid7()

    source = data_validate_profile_source(
        data_version_id=data_id,
        source_kind="TICK",
        session_version_id=session_id,
        price_step=Decimal("0.01"),
        sample_coverage_ratio=0.85,
    )

    assert source.is_sufficient is False
    assert any(d.code == "COVERAGE_INCOMPLETE" for d in source.coverage_diagnostics)


@pytest.mark.asyncio
async def test_prepare_profiles_service_async_success() -> None:
    """Verify PrepareProfilesService handling valid VALIDATE_SOURCE request."""
    service = PrepareProfilesService()
    req_id = _generate_uuid7()
    cap_snap_id = _generate_uuid7()
    data_id = _generate_uuid7()
    session_id = _generate_uuid7()

    request = PrepareProfilesRequest(
        request_id=req_id,
        capability_snapshot_id=cap_snap_id,
        operation="VALIDATE_SOURCE",
        data_version_id=data_id,
        source_kind="TICK",
        session_version_id=session_id,
        price_step="0.01",
        bin_count=100,
    )

    result = await service.prepare_profiles(request)
    assert isinstance(result, PrepareProfilesSuccess)
    assert result.outcome == "SUCCESS"
    assert result.request_id == req_id
    assert result.source is not None
    assert result.source.data_version_id == data_id
    assert result.source.session_version_id == session_id
    assert result.source.is_sufficient is True


@pytest.mark.asyncio
async def test_prepare_profiles_service_unsupported_operation() -> None:
    """Verify DataFailure on unsupported operation."""
    service = PrepareProfilesService()
    req_id = _generate_uuid7()

    request = PrepareProfilesRequest.model_construct(
        request_id=req_id,
        capability_snapshot_id=_generate_uuid7(),
        operation="UNSUPPORTED_OP",
        data_version_id=_generate_uuid7(),
        source_kind="TICK",
        session_version_id=_generate_uuid7(),
        price_step="0.01",
    )

    result = await service.prepare_profiles(request)
    assert isinstance(result, DataFailure)
    assert result.outcome == "FAILURE"
    assert result.code == "DATA_VALIDATION_FAILED"
    assert result.problem.status == 400


@pytest.mark.asyncio
async def test_main_scenario_harness() -> None:
    """Verify execution of the profile source preparation usage harness."""
    from app.services.data.profile_source_preparation.profile_source_preparation import (
        main,
    )

    await main()


def test_profile_source_persistence() -> None:
    """Verify ProfileSourcePersistence store operations."""
    from app.services.data.profile_source_preparation._persistence import (
        ProfileSourcePersistence,
    )
    from app.services.data.profile_source_preparation.profile_source_preparation import (
        data_validate_profile_source,
    )

    store = ProfileSourcePersistence()
    source = data_validate_profile_source(
        data_version_id=_generate_uuid7(),
        source_kind="TICK",
        session_version_id=_generate_uuid7(),
        price_step="0.01",
        bin_count=50,
    )
    store.save_source(source)
    assert store.get_source(source.data_version_id) == source
    assert len(store.get_all_sources()) == 1
    assert store.get_source("unknown") is None

    store.clear()
    assert len(store.get_all_sources()) == 0
