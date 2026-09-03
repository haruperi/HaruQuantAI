"""Executable usage demonstration harness for Data Quality Resolution."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

from app.contracts.data.models import (
    DataQualityDecision,
)
from app.services.data.data_quality_resolution._persistence import (
    data_lock_data_publication,
)
from app.services.data.data_quality_resolution.data_quality_resolution import (
    _format_utc_timestamp,
    _generate_uuid7,
    data_detect_data_quality,
    data_order_market_rows,
    data_resolve_quality_findings,
    data_validate_ohlc_bars,
)


def run_usage_scenarios() -> None:
    """Run all usage scenarios for Data Quality Resolution."""
    print("=== FEAT-DATA-RESOLVE_QUALITY Usage Harness ===")

    # Scenario 1: FR-DATA-DETECT_DATA_QUALITY
    print("\nScenario 1: FR-DATA-DETECT_DATA_QUALITY")
    sample_rows: list[dict[str, Any]] = [
        {
            "timestamp": "2024-01-02T00:00:00Z",
            "open": "100.00",
            "high": "101.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "10",
        },
        {
            "timestamp": "2024-01-02T00:01:00Z",
            "open": "100.50",
            "high": "102.00",
            "low": "100.25",
            "close": "101.75",
            "volume": "20",
        },
        {
            "timestamp": "2024-01-02T00:02:00Z",
            "open": "101.75",
            "high": "101.70",
            "low": "101.00",
            "close": "101.25",
            "volume": "30",
        },  # high < max(open,close)
        {
            "timestamp": "2024-01-02T00:02:00Z",
            "open": "101.75",
            "high": "102.00",
            "low": "101.00",
            "close": "101.25",
            "volume": "30",
        },  # duplicate
        {
            "timestamp": "2024-01-02T00:04:00Z",
            "open": "101.25",
            "high": "101.50",
            "low": "100.50",
            "close": "101.00",
            "volume": "-1",
        },  # negative volume
    ]
    version_1 = _generate_uuid7()
    findings = data_detect_data_quality(sample_rows, data_version_id=version_1)
    print(f"Detected {len(findings)} findings:")
    for f in findings:
        print(f" - [{f.severity}] {f.rule_code} at {f.point}: observed={f.observed}")

    # Scenario 2: FR-DATA-RESOLVE_QUALITY_FINDINGS
    print("\nScenario 2: FR-DATA-RESOLVE_QUALITY_FINDINGS")
    if findings:
        decision = DataQualityDecision(
            decision_id=_generate_uuid7(),
            finding_ids=tuple(f.finding_id for f in findings[:2]),
            action="TRANSFORM",
            policy_version=1,
            decided_at=_format_utc_timestamp(datetime.now(tz=UTC)),
        )
        resolved_findings, completed_decision = data_resolve_quality_findings(
            decision, findings
        )
        print(
            f"Resolved decision {completed_decision.decision_id} "
            f"(action={completed_decision.action})"
        )
        print(f"Derived version ID: {completed_decision.derived_version_id}")
        for rf in resolved_findings[:2]:
            print(
                f" - Finding {rf.finding_id}: state={rf.resolution_state}, "
                f"derived={rf.derived_version_id}"
            )

    # Scenario 3: FR-DATA-VALIDATE_OHLC_BARS
    print("\nScenario 3: FR-DATA-VALIDATE_OHLC_BARS")
    bar_rows: list[dict[str, Any]] = [
        {
            "timestamp": "2024-01-02T00:00:00Z",
            "open": "100.00",
            "high": "101.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "10",
            "source_sequence": 1,
            "flags": 0,
        },
        {
            "timestamp": "2024-01-02T00:01:00Z",
            "open": "100.00",
            "high": "98.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "10",
            "source_sequence": 2,
            "flags": 0,
        },  # invalid: high < open
    ]
    valid_bars, bar_issues = data_validate_ohlc_bars(bar_rows)
    print(f"Valid bars: {len(valid_bars)}, Validation issues: {len(bar_issues)}")

    # Scenario 4: FR-DATA-ORDER_MARKET_ROWS
    print("\nScenario 4: FR-DATA-ORDER_MARKET_ROWS")
    raw_ticks: list[dict[str, Any]] = [
        {
            "timestamp": "2024-01-02T00:00:02Z",
            "bid": "100.1",
            "ask": "100.2",
            "source_sequence": 1,
        },
        {
            "timestamp": "2024-01-02T00:00:00Z",
            "bid": "100.0",
            "ask": "100.1",
            "source_sequence": 2,
        },
        {
            "timestamp": "2024-01-02T00:00:00Z",
            "bid": "100.0",
            "ask": "100.1",
            "source_sequence": 1,
        },
    ]
    ordered, content_hash = data_order_market_rows(raw_ticks)
    print(f"Ordered {len(ordered)} rows (hash={content_hash[:16]}...):")
    for r in ordered:
        print(f" - {r['timestamp']} seq={r['source_sequence']}")

    # Scenario 5: FR-DATA-LOCK_DATA_PUBLICATION
    print("\nScenario 5: FR-DATA-LOCK_DATA_PUBLICATION")
    mem_db = sqlite3.connect(":memory:")
    mem_db.execute(
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
    ok1, receipt1, err1 = data_lock_data_publication(
        mem_db, "EURUSD_1M", expected_version=0, lock_owner="ingest_job_1"
    )
    print(f"First lock attempt: ok={ok1}, receipt={receipt1}, err={err1}")
    ok2, receipt2, err2 = data_lock_data_publication(
        mem_db, "EURUSD_1M", expected_version=0, lock_owner="ingest_job_2"
    )
    print(f"Conflicting lock attempt: ok={ok2}, receipt={receipt2}, err={err2}")
    ok3, receipt3, err3 = data_lock_data_publication(
        mem_db, "EURUSD_1M", expected_version=1, lock_owner="ingest_job_1"
    )
    print(f"Subsequent valid version lock: ok={ok3}, receipt={receipt3}, err={err3}")

    print("\nAll 5 usage scenarios demonstrated successfully!")

    print("\n--- Additional Quality Validation Example ---")
    res_qual = example_quality_validation()
    print(f"  * example_quality_validation: findings={res_qual['findings_count']}")


def example_quality_validation() -> dict[str, Any]:
    """Inspect quality calculated from actual canonical records."""
    sample_rows = [
        {
            "timestamp": "2026-08-01T00:00:00Z",
            "open": "1.1000",
            "high": "1.1050",
            "low": "1.0950",
            "close": "1.1020",
            "volume": "100",
        },
        {
            "timestamp": "2026-08-01T00:01:00Z",
            "open": "1.1020",
            "high": "1.1010",
            "low": "1.0990",
            "close": "1.1000",
            "volume": "150",
        },
    ]
    version_id = _generate_uuid7()
    findings = data_detect_data_quality(sample_rows, data_version_id=version_id)
    return {
        "findings_count": len(findings),
        "version_id": version_id,
        "sample_rows_count": len(sample_rows),
    }


def main() -> None:
    """Run standalone usage demonstration."""
    run_usage_scenarios()


if __name__ == "__main__":
    main()
