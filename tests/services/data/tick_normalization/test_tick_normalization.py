"""Unit and contract tests for Tick Normalization service."""

import pytest
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    NormalizeTicksRequest,
    NormalizeTicksSuccess,
    Tick,
)
from app.services.data.tick_normalization.config import TickNormalizationConfig
from app.services.data.tick_normalization.tick_normalization import (
    TickNormalizationService,
    data_preserve_tick_fields,
    main,
)


def _sample_ticks() -> tuple[Tick, ...]:
    """Generate sample test ticks."""
    t0 = "2026-08-28T10:00:00.000000Z"
    t1 = "2026-08-28T10:00:01.000000Z"
    return (
        Tick(
            timestamp=t0,
            bid="1.1",
            ask="1.10005",
            last="1.10002",
            volume="50",
            source_sequence=1,
            flags=0,
        ),
        Tick(
            timestamp=t0,
            bid="1.10001",
            ask="1.10006",
            last="1.10003",
            volume="150",
            source_sequence=2,
            flags=1,
        ),
        Tick(
            timestamp=t1,
            bid="1.10002",
            ask="1.10007",
            last=None,
            volume=None,
            source_sequence=3,
            flags=0,
        ),
    )


def test_data_preserve_tick_fields() -> None:
    """Verify FR-DATA-PRESERVE_TICK_FIELDS: preserves all fields and duplicate timestamp order."""
    ticks = _sample_ticks()
    normalized, findings = data_preserve_tick_fields(ticks)

    assert len(normalized) == len(ticks)
    assert len(findings) == 0

    # Verify complete field preservation
    for orig, norm in zip(ticks, normalized, strict=True):
        assert norm.timestamp == orig.timestamp
        assert norm.bid == orig.bid
        assert norm.ask == orig.ask
        assert norm.last == orig.last
        assert norm.volume == orig.volume
        assert norm.source_sequence == orig.source_sequence
        assert norm.flags == orig.flags

    # Verify duplicate timestamps remain in source sequence order
    assert normalized[0].timestamp == normalized[1].timestamp
    assert normalized[0].source_sequence == 1
    assert normalized[1].source_sequence == 2


def test_preserve_tick_fields_out_of_order_sequence() -> None:
    """Verify ticks with same timestamp are sorted deterministically by source sequence."""
    t0 = "2026-08-28T10:00:00.000000Z"
    raw = (
        Tick(
            timestamp=t0,
            bid="1.10002",
            ask="1.10007",
            source_sequence=2,
            flags=0,
        ),
        Tick(
            timestamp=t0,
            bid="1.10001",
            ask="1.10006",
            source_sequence=1,
            flags=0,
        ),
    )
    normalized, findings = data_preserve_tick_fields(raw)
    assert len(normalized) == 2
    assert normalized[0].source_sequence == 1
    assert normalized[1].source_sequence == 2
    assert len(findings) == 0


def test_inverted_spread_finding() -> None:
    """Verify inverted spread generates a validation issue."""
    t0 = "2026-08-28T10:00:00.000000Z"
    raw = (
        Tick(
            timestamp=t0,
            bid="1.1005",
            ask="1.1",  # ask < bid
            source_sequence=1,
            flags=0,
        ),
    )
    normalized, findings = data_preserve_tick_fields(raw)
    assert len(normalized) == 1
    assert len(findings) == 1
    assert findings[0].code == "INVERTED_SPREAD"
    assert findings[0].path == ("ticks", "0", "ask")


def test_non_positive_price_findings() -> None:
    """Verify non-positive bid/ask generates validation findings."""
    t0 = "2026-08-28T10:00:00.000000Z"
    raw = (
        Tick(
            timestamp=t0,
            bid="0",
            ask="0",
            source_sequence=1,
            flags=0,
        ),
    )
    normalized, findings = data_preserve_tick_fields(raw)
    assert len(normalized) == 1
    codes = {f.code for f in findings}
    assert "NON_POSITIVE_BID" in codes
    assert "NON_POSITIVE_ASK" in codes


@pytest.mark.asyncio
async def test_service_normalize_ticks_success() -> None:
    """Verify successful tick normalization request via service."""
    service = TickNormalizationService()
    ticks = _sample_ticks()
    req_id = "018f6e2b-1111-7000-8000-000000000001"
    snap_id = "018f6e2b-2222-7000-8000-000000000002"

    request = NormalizeTicksRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="NORMALIZE",
        ticks=ticks,
    )

    result = await service.normalize_ticks(request)
    assert isinstance(result, NormalizeTicksSuccess)
    assert result.outcome == "SUCCESS"
    assert result.request_id == req_id
    assert len(result.findings) == 0


@pytest.mark.asyncio
async def test_service_batch_size_exceeded() -> None:
    """Verify DataFailure when batch size exceeds configuration limit."""
    cfg = TickNormalizationConfig(max_batch_size=2)
    service = TickNormalizationService(config=cfg)
    ticks = _sample_ticks()  # 3 ticks > limit 2
    req_id = "018f6e2b-1111-7000-8000-000000000001"
    snap_id = "018f6e2b-2222-7000-8000-000000000002"

    request = NormalizeTicksRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="NORMALIZE",
        ticks=ticks,
    )

    result = await service.normalize_ticks(request)
    assert isinstance(result, DataFailure)
    assert result.code == "DATA_VALIDATION_FAILED"
    assert "Batch size" in result.problem.detail


@pytest.mark.asyncio
async def test_service_unsupported_operation() -> None:
    """Verify DataFailure for unsupported operation string."""
    service = TickNormalizationService()
    ticks = _sample_ticks()
    req_id = "018f6e2b-1111-7000-8000-000000000001"
    snap_id = "018f6e2b-2222-7000-8000-000000000002"

    # Construct request bypassing Pydantic literal for testing defensive handling
    request = NormalizeTicksRequest.model_construct(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="UNSUPPORTED_OP",
        ticks=ticks,
        schema_version=1,
    )

    result = await service.normalize_ticks(request)
    assert isinstance(result, DataFailure)
    assert result.code == "DATA_VALIDATION_FAILED"
    assert "not supported" in result.problem.detail


@pytest.mark.asyncio
async def test_main_scenario_harness() -> None:
    """Verify execution of standalone main scenario harness."""
    await main()


def test_tick_normalization_persistence() -> None:
    """Verify TickNormalizationPersistence operations."""
    from app.services.data.tick_normalization._persistence import (
        TickNormalizationPersistence,
    )

    store = TickNormalizationPersistence()
    ticks = _sample_ticks()
    store.save_batch("b1", ticks)
    assert store.get_batch("b1") == ticks
    assert len(store.get_all_batches()) == 1
    assert store.get_batch("unknown") is None

    store.clear()
    assert len(store.get_all_batches()) == 0
