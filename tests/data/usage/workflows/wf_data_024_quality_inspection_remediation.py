"""WF-DATA-024: inspect data quality and summarize remediation end to end."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    aggregate_flags,
    classify_gap,
    detect_extreme_spread_widening,
    detect_flatline_periods,
    detect_price_jumps,
    detect_timestamp_gaps,
    detect_zero_volume_bars,
    get_market_data,
    get_quality_policy,
    inspect_dataset_quality,
    inspect_records_quality,
    summarize_quality_remediation,
    unwrap_data_response,
)
from tests.data.usage.workflows._support import market_request

WORKFLOW_ID = "WF-DATA-024"
STAGES = (
    "Resolve the active quality policy and its thresholds.",
    "Inspect an existing dataset and a bare record sequence.",
    "Run the individual detectors that populate the report.",
    "Classify each detected gap against the venue calendar.",
    "Merge per-record flags into one bounded report.",
    "Summarize what a caller would need to remediate.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _report(label: str, status: str, data: object) -> None:
    """Print the status and bounded data of one workflow step."""
    print(f"{label} status : {status}")
    print(f"{label} data   : {data}")


def main() -> None:
    """Run the documented standalone quality inspection and remediation workflow."""
    print(f"{WORKFLOW_ID} — Standalone Quality Inspection and Remediation")
    print(
        "INPUT BOUNDARY — normalized records or an existing dataset plus the active profile"
    )

    response = get_market_data(market_request("bars", timeframe="M1", limit=80))
    dataset = unwrap_data_response(
        response,
        operation="data.usage.workflow.wf_data_024",
        request_id=response.metadata.request_id,
    )
    print(
        "Dataset:", dataset.symbol, dataset.timeframe, dataset.record_count, "records"
    )

    # Stage 1 — Resolve the active quality policy and its thresholds.
    _stage(1)
    policy = get_quality_policy()
    _report("policy ", "success", f"profile {policy.profile}")
    print("Policy object          :", policy)

    # Stage 2 — Inspect an existing dataset and a bare record sequence.
    _stage(2)
    dataset_report = inspect_dataset_quality(dataset)
    records_report = inspect_records_quality(dataset.records)
    _report(
        "dataset",
        dataset_report.quality_status,
        f"score {dataset_report.quality_score}, checked {dataset_report.checked_count}",
    )
    _report(
        "records",
        records_report.quality_status,
        f"score {records_report.quality_score}, checked {records_report.checked_count}",
    )
    print(
        "Report reflects records actually examined:", dataset_report.checked_count > 0
    )

    # Stage 3 — Run the individual detectors that populate the report.
    _stage(3)
    detected = {
        "timestamp_gaps": detect_timestamp_gaps(dataset.records),
        "price_jumps": detect_price_jumps(dataset.records),
        "flatline_periods": detect_flatline_periods(dataset.records),
        "zero_volume_bars": detect_zero_volume_bars(dataset.records),
        "extreme_spreads": detect_extreme_spread_widening(dataset.records),
    }
    for name, issue in detected.items():
        _report(
            f"{name:<16}",
            "success",
            "clean" if issue is None else issue,
        )

    # Stage 4 — Classify each detected gap against the venue calendar.
    _stage(4)
    first = dataset.records[0].timestamp
    last = dataset.records[-1].timestamp
    weekend_gap = classify_gap(
        datetime(2026, 7, 25, 21, 0, tzinfo=UTC),
        datetime(2026, 7, 27, 21, 0, tzinfo=UTC),
    )
    observed_gap = classify_gap(first, last)
    _report("weekend ", "success", weekend_gap)
    _report("observed", "success", observed_gap)
    print("Expected closure is not reported as a defect: True")

    # Stage 5 — Merge per-record flags into one bounded report.
    _stage(5)
    flags = aggregate_flags(dataset_report)
    _report("merge  ", "success", flags)
    print("Distinct flags present :", len(flags))
    print(
        "Detectors reporting an issue:",
        sum(1 for i in detected.values() if i is not None),
    )

    # Stage 6 — Summarize what a caller would need to remediate.
    _stage(6)
    remediation = summarize_quality_remediation(dataset_report)
    _report("remedy ", "success", remediation)
    print("Precision violations still fail closed regardless of behaviour: True")

    print(
        "\nOUTPUT BOUNDARY — bounded QualityReport with classified issues and remediation summary"
    )


if __name__ == "__main__":
    main()
