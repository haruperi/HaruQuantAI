"""Unit and contract tests for Data Quality and Resolution feature."""

import sqlite3
from datetime import UTC, datetime
from typing import Any

import pytest
from app.contracts.data.models import (
    DataQualityDecision,
    DataQualityFinding,
    ResolveQualityRequest,
    ResolveQualitySuccess,
    Tick,
)
from app.services.data.data_quality_resolution.data_quality_resolution import (
    DataQualityResolutionService,
    _format_utc_timestamp,
    _generate_uuid7,
    data_detect_data_quality,
    data_lock_data_publication,
    data_order_market_rows,
    data_resolve_quality_findings,
    data_validate_ohlc_bars,
)


def test_data_detect_data_quality() -> None:
    """Verify FR-DATA-DETECT_DATA_QUALITY: detects anomalies per section 16.4 rules."""
    version_id = _generate_uuid7()
    records: list[dict[str, Any]] = [
        # Valid row
        {
            "timestamp": "2024-01-02T00:00:00.000000Z",
            "open": "100.00",
            "high": "101.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "10",
        },
        # Unsorted timestamp
        {
            "timestamp": "2023-12-31T23:59:00.000000Z",
            "open": "100.00",
            "high": "101.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "10",
        },
        # OHLC low above body (low > min(open, close))
        {
            "timestamp": "2024-01-02T00:02:00.000000Z",
            "open": "100.00",
            "high": "102.00",
            "low": "101.00",
            "close": "101.50",
            "volume": "10",
        },
        # OHLC high below body (high < max(open, close))
        {
            "timestamp": "2024-01-02T00:03:00.000000Z",
            "open": "100.00",
            "high": "100.50",
            "low": "99.00",
            "close": "101.00",
            "volume": "10",
        },
        # OHLC low above high
        {
            "timestamp": "2024-01-02T00:04:00.000000Z",
            "open": "100.00",
            "high": "98.00",
            "low": "99.00",
            "close": "98.50",
            "volume": "10",
        },
        # Duplicate bar timestamp
        {
            "timestamp": "2024-01-02T00:00:00.000000Z",
            "open": "100.00",
            "high": "101.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "10",
        },
        # Negative volume
        {
            "timestamp": "2024-01-02T00:05:00.000000Z",
            "open": "100.00",
            "high": "101.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "-5",
        },
        # Invalid / unparsable timestamp
        {
            "timestamp": "invalid-time",
            "open": "100.00",
            "high": "101.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "10",
        },
        # Out-of-session (hour 12 with session [0, 8))
        {
            "timestamp": "2024-01-02T12:00:00.000000Z",
            "open": "100.00",
            "high": "101.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "10",
        },
    ]

    findings = data_detect_data_quality(
        records,
        data_version_id=version_id,
        session_start_hour=0,
        session_end_hour=8,
    )

    codes = [f.rule_code for f in findings]
    assert "UNSORTED_TIME" in codes
    assert "OHLC_LOW_ABOVE_BODY" in codes
    assert "OHLC_HIGH_BELOW_BODY" in codes
    assert "OHLC_LOW_ABOVE_HIGH" in codes
    assert "DUPLICATE_BAR" in codes
    assert "NEGATIVE_VOLUME" in codes
    assert "TIME_PARSE" in codes
    assert "OUT_OF_SESSION" in codes

    for f in findings:
        assert f.data_version_id == version_id
        assert f.resolution_state == "OPEN"


def test_data_detect_tick_spread_inversion() -> None:
    """Verify tick quality rules detect inverted bid/ask."""
    ticks: list[dict[str, Any]] = [
        {
            "timestamp": "2024-01-02T00:00:00.000000Z",
            "bid": "1.1005",
            "ask": "1.1000",
            "source_sequence": 1,
        },
    ]
    findings = data_detect_data_quality(ticks)
    codes = [f.rule_code for f in findings]
    assert "BID_ABOVE_ASK" in codes


def test_data_resolve_quality_findings() -> None:
    """Verify FR-DATA-RESOLVE_QUALITY_FINDINGS: accepts/rejects/transforms without mutating source."""
    v_source = _generate_uuid7()
    finding_1 = DataQualityFinding(
        finding_id=_generate_uuid7(),
        data_version_id=v_source,
        rule_code="OHLC_LOW_ABOVE_BODY",
        severity="ERROR",
        observed="101.00",
        expected="<= 100.00",
    )
    finding_2 = DataQualityFinding(
        finding_id=_generate_uuid7(),
        data_version_id=v_source,
        rule_code="NEGATIVE_VOLUME",
        severity="ERROR",
        observed="-1",
        expected=">= 0",
    )

    decision = DataQualityDecision(
        decision_id=_generate_uuid7(),
        finding_ids=(finding_1.finding_id, finding_2.finding_id),
        action="TRANSFORM",
        policy_version=1,
        decided_at=_format_utc_timestamp(datetime.now(tz=UTC)),
    )

    resolved_findings, completed_decision = data_resolve_quality_findings(
        decision, [finding_1, finding_2]
    )

    assert len(resolved_findings) == 2
    assert completed_decision.derived_version_id is not None

    for rf in resolved_findings:
        assert rf.resolution_state == "TRANSFORMED"
        assert rf.derived_version_id == completed_decision.derived_version_id
        # Source version is preserved
        assert rf.data_version_id == v_source


def test_data_validate_ohlc_bars() -> None:
    """Verify FR-DATA-VALIDATE_OHLC_BARS: rejects bars violating invariants."""
    valid_raw = {
        "timestamp": "2024-01-02T00:00:00.000000Z",
        "open": "100.00",
        "high": "102.00",
        "low": "99.00",
        "close": "101.00",
        "volume": "50",
        "source_sequence": 1,
        "flags": 0,
    }
    invalid_high = {
        "timestamp": "2024-01-02T00:01:00.000000Z",
        "open": "100.00",
        "high": "98.00",  # high < open
        "low": "97.00",
        "close": "99.00",
        "volume": "50",
        "source_sequence": 2,
        "flags": 0,
    }
    invalid_low = {
        "timestamp": "2024-01-02T00:02:00.000000Z",
        "open": "100.00",
        "high": "105.00",
        "low": "101.00",  # low > min(open, close)
        "close": "103.00",
        "volume": "50",
        "source_sequence": 3,
        "flags": 0,
    }

    valid_bars, issues = data_validate_ohlc_bars([valid_raw, invalid_high, invalid_low])

    assert len(valid_bars) == 1
    assert valid_bars[0].open == "100"
    assert len(issues) == 2
    assert all(issue.code == "OHLC_INVARIANT_VIOLATION" for issue in issues)


def test_data_order_market_rows() -> None:
    """Verify FR-DATA-ORDER_MARKET_ROWS: chronological sort with deterministic duplicate sequence preservation."""
    t0 = "2024-01-02T00:00:00.000000Z"
    t1 = "2024-01-02T00:01:00.000000Z"

    ticks = (
        Tick(timestamp=t1, bid="100.2", ask="100.3", source_sequence=3, flags=0),
        Tick(timestamp=t0, bid="100", ask="100.1", source_sequence=2, flags=0),
        Tick(timestamp=t0, bid="100", ask="100.1", source_sequence=1, flags=0),
    )

    ordered, hash1 = data_order_market_rows(ticks)
    assert len(ordered) == 3
    assert ordered[0].timestamp == t0
    assert ordered[0].source_sequence == 1
    assert ordered[1].timestamp == t0
    assert ordered[1].source_sequence == 2
    assert ordered[2].timestamp == t1
    assert ordered[2].source_sequence == 3

    # Re-ordering produces identical hash
    _, hash2 = data_order_market_rows(ordered)
    assert hash1 == hash2


def test_data_lock_data_publication() -> None:
    """Verify FR-DATA-LOCK_DATA_PUBLICATION: optimistic version checks and exclusive locks."""
    db = sqlite3.connect(":memory:")
    db.execute(
        """
        CREATE TABLE publication_locks (
            series_key TEXT PRIMARY KEY,
            current_version INTEGER NOT NULL,
            lock_owner TEXT,
            acquired_at TEXT,
            lock_id TEXT
        )
        """
    )

    # Initial creation (expected_version=0)
    ok1, receipt1, err1 = data_lock_data_publication(
        db, "SERIES_1", expected_version=0, lock_owner="proc_1"
    )
    assert ok1 is True
    assert receipt1 is not None
    assert receipt1.acquired_version == 1
    assert err1 is None

    # Version conflict (expecting version 0 when version is 1)
    ok2, receipt2, err2 = data_lock_data_publication(
        db, "SERIES_1", expected_version=0, lock_owner="proc_2"
    )
    assert ok2 is False
    assert receipt2 is None
    assert err2 is not None
    assert "version conflict" in err2.lower()

    # Valid optimistic advance to version 2
    ok3, receipt3, _ = data_lock_data_publication(
        db, "SERIES_1", expected_version=1, lock_owner="proc_1"
    )
    assert ok3 is True
    assert receipt3 is not None
    assert receipt3.acquired_version == 2


@pytest.mark.asyncio
async def test_data_quality_service_resolve_quality_port() -> None:
    """Verify DataQualityResolutionService port implementation."""
    service = DataQualityResolutionService()
    v_id = _generate_uuid7()

    # Register initial finding
    f = DataQualityFinding(
        finding_id=_generate_uuid7(),
        data_version_id=v_id,
        rule_code="OHLC_LOW_ABOVE_BODY",
        severity="ERROR",
        observed="105",
        expected="<= 100",
    )
    service.register_findings(v_id, [f])

    # 1. DETECT operation
    detect_req = ResolveQualityRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="DETECT",
        data_version_id=v_id,
    )
    detect_res = await service.resolve_quality(detect_req)
    assert isinstance(detect_res, ResolveQualitySuccess)
    assert len(detect_res.findings) == 1
    assert detect_res.findings[0].rule_code == "OHLC_LOW_ABOVE_BODY"

    # 2. RESOLVE operation
    decision = DataQualityDecision(
        decision_id=_generate_uuid7(),
        finding_ids=(f.finding_id,),
        action="ACCEPT",
        policy_version=1,
        decided_at=_format_utc_timestamp(datetime.now(tz=UTC)),
    )
    resolve_req = ResolveQualityRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="RESOLVE",
        decision=decision,
    )
    resolve_res = await service.resolve_quality(resolve_req)
    assert isinstance(resolve_res, ResolveQualitySuccess)
    assert len(resolve_res.findings) == 1
    assert resolve_res.findings[0].resolution_state == "ACCEPTED"


def test_main_scenario_harness() -> None:
    """Verify executable usage scenario harness executes without error."""
    from app.services.data.data_quality_resolution.data_quality_resolution import (
        run_usage_scenarios,
    )

    run_usage_scenarios()
