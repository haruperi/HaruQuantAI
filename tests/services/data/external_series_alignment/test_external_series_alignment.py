"""Unit, contract, and scenario tests for External Series Alignment."""

from decimal import Decimal

import pytest
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    AlignSeriesRequest,
    AlignSeriesSuccess,
)
from app.services.data.external_series_alignment.external_series_alignment import (
    AlignSeriesService,
    SeriesPoint,
    _generate_uuid7,
    _parse_utc_timestamp,
    _validate_timezone,
    data_align_external_series,
    data_define_alignment_policy,
    main,
)


def test_data_define_alignment_policy() -> None:
    """Verify FR-DATA-DEFINE_ALIGNMENT_POLICY: valid policy declaration and invariant rules."""
    policy = data_define_alignment_policy(
        direction="LAST_KNOWN",
        max_age_seconds=7200,
        missing_policy="CARRY_FORWARD",
        timezone="America/New_York",
        look_ahead_prohibited=True,
    )
    assert policy.direction == "LAST_KNOWN"
    assert policy.max_age_seconds == 7200
    assert policy.missing_policy == "CARRY_FORWARD"
    assert policy.timezone == "America/New_York"
    assert policy.look_ahead_prohibited is True

    # Invalid direction
    with pytest.raises(ValueError, match="Invalid direction"):
        data_define_alignment_policy(direction="FORWARD")  # type: ignore[arg-type]

    # Non-positive max age
    with pytest.raises(ValueError, match="max_age_seconds must be >= 1"):
        data_define_alignment_policy(max_age_seconds=0)

    # Invalid missing policy
    with pytest.raises(ValueError, match="Invalid missing_policy"):
        data_define_alignment_policy(missing_policy="INTERPOLATE")  # type: ignore[arg-type]

    # Invalid timezone
    with pytest.raises(ValueError, match="Invalid timezone"):
        data_define_alignment_policy(timezone="NonExistent/Timezone")

    # Look-ahead prohibited must be True
    with pytest.raises(ValueError, match="look_ahead_prohibited must be strictly True"):
        data_define_alignment_policy(look_ahead_prohibited=False)


def test_data_align_external_series() -> None:
    """Verify FR-DATA-ALIGN_EXTERNAL_SERIES: exact, last-known, and aggregation alignments."""
    source_points = [
        SeriesPoint(
            timestamp="2026-08-28T10:00:00.000000Z",
            value=Decimal("100.0"),
            available_at="2026-08-28T10:00:05.000000Z",
        ),
        SeriesPoint(
            timestamp="2026-08-28T10:05:00.000000Z",
            value=Decimal("105.0"),
            available_at="2026-08-28T10:05:05.000000Z",
        ),
        SeriesPoint(
            timestamp="2026-08-28T10:10:00.000000Z",
            value=Decimal("110.0"),
            available_at="2026-08-28T10:10:05.000000Z",
        ),
    ]

    targets = [
        "2026-08-28T10:00:00.000000Z",
        "2026-08-28T10:02:00.000000Z",
        "2026-08-28T10:05:05.000000Z",
        "2026-08-28T10:08:00.000000Z",
    ]

    # 1. EXACT direction with NULL missing policy
    policy_exact = data_define_alignment_policy(
        direction="EXACT", missing_policy="NULL"
    )
    aligned_series, points = data_align_external_series(
        source_points, targets, policy_exact
    )
    assert aligned_series.policy.direction == "EXACT"
    # Target 1 (10:00:00): available_at is 10:00:05 -> unavailable -> gap (None)
    assert points[0].aligned_value is None
    assert points[0].is_gap is True
    # Target 2 (10:02:00): no exact point at 10:02:00 -> gap (None)
    assert points[1].aligned_value is None
    assert points[1].is_gap is True
    # Target 3 (10:05:05): source at 10:05:00 available, but target is 10:05:05 -> gap
    assert points[2].aligned_value is None

    # 2. LAST_KNOWN direction with NULL missing policy
    policy_lk = data_define_alignment_policy(
        direction="LAST_KNOWN", max_age_seconds=600, missing_policy="NULL"
    )
    _, points_lk = data_align_external_series(source_points, targets, policy_lk)
    # Target 1 (10:00:00): available_at is 10:00:05 -> not visible yet -> None
    assert points_lk[0].aligned_value is None
    assert points_lk[0].is_gap is True
    # Target 2 (10:02:00): point 10:00:00 visible (avail 10:00:05 <= 10:02:00) -> 100.0
    assert points_lk[1].aligned_value == Decimal("100.0")
    assert points_lk[1].is_gap is False
    # Target 3 (10:05:05): point 10:05:00 visible (avail 10:05:05 <= 10:05:05) -> 105.0
    assert points_lk[2].aligned_value == Decimal("105.0")
    # Target 4 (10:08:00): point 10:05:00 visible -> 105.0
    assert points_lk[3].aligned_value == Decimal("105.0")

    # 3. AGGREGATE direction
    policy_agg = data_define_alignment_policy(
        direction="AGGREGATE", max_age_seconds=600, missing_policy="NULL"
    )
    _, points_agg = data_align_external_series(
        source_points, ["2026-08-28T10:08:00.000000Z"], policy_agg
    )
    # Points at 10:00:00 (100) and 10:05:00 (105) in window -> Mean: 102.5
    assert points_agg[0].aligned_value == Decimal("102.5")


def test_lookahead_zero_visibility_guarantee() -> None:
    """Verify that future data is strictly never visible at target decision time."""
    source_points = [
        # timestamp is in future relative to 10:00 decision
        SeriesPoint(
            timestamp="2026-08-28T10:05:00.000000Z",
            value=Decimal("999.0"),
            available_at="2026-08-28T09:59:00.000000Z",
        ),
        # timestamp is in past, but available_at is in future relative to 10:00 decision
        SeriesPoint(
            timestamp="2026-08-28T09:55:00.000000Z",
            value=Decimal("888.0"),
            available_at="2026-08-28T10:02:00.000000Z",
        ),
        # valid point in past and available in past
        SeriesPoint(
            timestamp="2026-08-28T09:50:00.000000Z",
            value=Decimal("50.0"),
            available_at="2026-08-28T09:51:00.000000Z",
        ),
    ]

    target = "2026-08-28T10:00:00.000000Z"
    policy = data_define_alignment_policy(direction="LAST_KNOWN", max_age_seconds=3600)
    _, points = data_align_external_series(source_points, [target], policy)

    # Neither 999.0 nor 888.0 should be visible. Only 50.0 is visible.
    assert points[0].aligned_value == Decimal("50.0")
    assert points[0].source_timestamp == "2026-08-28T09:50:00.000000Z"


def test_missing_policy_fail_and_carry_forward() -> None:
    """Verify missing policies: FAIL raises error; CARRY_FORWARD preserves past value."""
    source_points = [
        SeriesPoint(
            timestamp="2026-08-28T10:00:00.000000Z",
            value=Decimal("100.0"),
            available_at="2026-08-28T10:00:00.000000Z",
        ),
    ]

    # FAIL policy raises on missing
    policy_fail = data_define_alignment_policy(direction="EXACT", missing_policy="FAIL")
    with pytest.raises(ValueError, match="under FAIL policy"):
        data_align_external_series(
            source_points, ["2026-08-28T10:05:00.000000Z"], policy_fail
        )

    # CARRY_FORWARD policy on EXACT
    policy_cf = data_define_alignment_policy(
        direction="EXACT", max_age_seconds=600, missing_policy="CARRY_FORWARD"
    )
    _, points_cf = data_align_external_series(
        source_points,
        ["2026-08-28T10:00:00.000000Z", "2026-08-28T10:05:00.000000Z"],
        policy_cf,
    )
    assert points_cf[0].aligned_value == Decimal("100.0")
    assert points_cf[1].aligned_value == Decimal("100.0")


def test_target_timestamps_validation() -> None:
    """Verify target timestamp sequence errors."""
    policy = data_define_alignment_policy()
    with pytest.raises(ValueError, match="target_timestamps sequence cannot be empty"):
        data_align_external_series([], [], policy)

    with pytest.raises(ValueError, match="chronological ascending order"):
        data_align_external_series(
            [SeriesPoint(timestamp="2026-08-28T10:00:00.000000Z", value=1)],
            ["2026-08-28T10:05:00.000000Z", "2026-08-28T10:00:00.000000Z"],
            policy,
        )


@pytest.mark.asyncio
async def test_align_series_service_operations() -> None:
    """Verify AlignSeriesService operations: DEFINE_POLICY and ALIGN."""
    service = AlignSeriesService()
    policy = data_define_alignment_policy(direction="LAST_KNOWN", max_age_seconds=3600)
    req_id = _generate_uuid7()
    snap_id = _generate_uuid7()
    src_ver_id = _generate_uuid7()

    # DEFINE_POLICY
    req_def = AlignSeriesRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="DEFINE_POLICY",
        source_version_id=src_ver_id,
        policy=policy,
    )
    res_def = await service.align_series(req_def)
    assert isinstance(res_def, AlignSeriesSuccess)
    assert res_def.aligned is not None
    assert res_def.aligned.policy.direction == "LAST_KNOWN"

    # ALIGN
    req_align = AlignSeriesRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="ALIGN",
        source_version_id=src_ver_id,
        policy=policy,
    )
    res_align = await service.align_series(req_align)
    assert isinstance(res_align, AlignSeriesSuccess)
    assert res_align.aligned is not None


@pytest.mark.asyncio
async def test_align_series_service_failures() -> None:
    """Verify AlignSeriesService failure handling."""
    service = AlignSeriesService()
    req_id = _generate_uuid7()
    snap_id = _generate_uuid7()
    src_ver_id = _generate_uuid7()

    # Unsupported operation
    req_unsupported = AlignSeriesRequest.model_construct(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="UNKNOWN_OP",
        source_version_id=src_ver_id,
        policy=None,
    )
    res_unsupported = await service.align_series(req_unsupported)
    assert isinstance(res_unsupported, DataFailure)
    assert res_unsupported.code == "DATA_VALIDATION_FAILED"

    # DEFINE_POLICY with missing policy
    req_no_policy_def = AlignSeriesRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="DEFINE_POLICY",
        policy=None,
    )
    res_no_policy_def = await service.align_series(req_no_policy_def)
    assert isinstance(res_no_policy_def, DataFailure)
    assert res_no_policy_def.code == "DATA_VALIDATION_FAILED"

    # ALIGN with missing policy
    req_no_policy_align = AlignSeriesRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="ALIGN",
        policy=None,
    )
    res_no_policy_align = await service.align_series(req_no_policy_align)
    assert isinstance(res_no_policy_align, DataFailure)
    assert res_no_policy_align.code == "DATA_VALIDATION_FAILED"


def test_parse_utc_and_timezone_helpers() -> None:
    """Verify internal UTC parser and timezone validation."""
    from datetime import UTC, datetime

    # Naive datetime
    naive = datetime(2026, 8, 28, 10, 0, 0, tzinfo=None)  # noqa: DTZ001
    parsed = _parse_utc_timestamp(naive)
    assert parsed.tzinfo == UTC

    # String without explicit tz
    parsed_str = _parse_utc_timestamp("2026-08-28T10:00:00")
    assert parsed_str.tzinfo == UTC

    # Invalid timezone
    with pytest.raises(
        ValueError, match="Timezone identifier must be a non-empty string"
    ):
        _validate_timezone("")
    with pytest.raises(
        ValueError, match="Timezone identifier must be a non-empty string"
    ):
        _validate_timezone(None)  # type: ignore[arg-type]


def test_main_scenario_harness() -> None:
    """Verify execution of the main scenario harness."""
    main()


def test_series_alignment_persistence() -> None:
    """Verify SeriesAlignmentPersistence operations."""
    from app.contracts.data.models import AlignedSeries, AlignmentPolicy
    from app.services.data.external_series_alignment._persistence import (
        SeriesAlignmentPersistence,
    )

    store = SeriesAlignmentPersistence()
    policy = AlignmentPolicy(
        direction="LAST_KNOWN",
        max_age_seconds=300,
        missing_policy="NULL",
        timezone="UTC",
        look_ahead_prohibited=True,
    )
    store.save_policy("p1", policy)
    assert store.get_policy("p1") == policy
    assert store.get_policy("unknown") is None

    series_id = _generate_uuid7()
    series = AlignedSeries(
        alignment_id=_generate_uuid7(),
        source_version_id=_generate_uuid7(),
        policy=policy,
        aligned_version_id=series_id,
    )
    store.save_aligned_series(series)
    assert store.get_aligned_series(series_id) == series
    assert len(store.get_all_aligned_series()) == 1

    store.clear()
    assert store.get_policy("p1") is None
