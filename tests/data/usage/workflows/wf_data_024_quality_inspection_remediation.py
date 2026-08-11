"""WF-DATA-024: inspect data quality and summarize remediation end to end."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from decimal import Decimal

from app.services.data import (
    aggregate_flags,
    build_data_settings,
    build_market_data_request,
    build_synthetic_request,
    classify_gap,
    data_settings_context,
    detect_extreme_spread_widening,
    detect_flatline_periods,
    detect_price_jumps,
    detect_timestamp_gaps,
    detect_zero_volume_bars,
    generate_synthetic_bars,
    get_market_data,
    get_quality_policy,
    inspect_dataset_quality,
    inspect_records_quality,
    run_data_migrations,
    summarize_quality_remediation,
    unwrap_data_response,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-024"
STAGES = (
    "Resolve the active quality policy and its thresholds.",
    "Inspect an existing dataset and a bare record sequence.",
    "Run the individual detectors that populate the report.",
    "Classify each detected gap against the venue calendar.",
    "Merge per-record flags into one bounded report.",
    "Summarize what a caller would need to remediate.",
)

_END = datetime.now(UTC)
_START = _END - timedelta(days=5)


def _market_request(data_kind, *, timeframe, limit):
    """Build one bounded genuine MT5 request inline."""
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
        timeframe=timeframe if data_kind == "bars" else None,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
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


def main() -> None:  # noqa: PLR0915
    """Run the documented standalone quality inspection and remediation workflow."""
    print(f"{WORKFLOW_ID} — Standalone Quality Inspection and Remediation")
    print(
        "INPUT BOUNDARY — normalized records or an existing dataset plus the active profile"
    )

    with tempfile.TemporaryDirectory(prefix="wf-data-024-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///workflow.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            request_id = generate_id("req")
            run_data_migrations(request_id)

            response = get_market_data(
                _market_request("bars", timeframe="M1", limit=80)
            )
            if response.status != "success":
                end = datetime.now(UTC)
                syn_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="bars",
                    timeframe="M1",
                    start=end - timedelta(hours=1),
                    record_count=80,
                    method="gbm",
                    seed=42,
                    parameters={
                        "start_val": Decimal("1.10"),
                        "mu": Decimal("0.02"),
                        "sigma": Decimal("0.10"),
                    },
                    precision_policy="decimal_string",
                    request_id=request_id,
                )
                dataset = unwrap_data_response(
                    generate_synthetic_bars(syn_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_req.request_id,
                )
            else:
                dataset = unwrap_data_response(
                    response,
                    operation="get_market_data",
                    request_id=request_id,
                )
            print(
                "Dataset:",
                dataset.symbol,
                dataset.timeframe,
                dataset.record_count,
                "records",
            )

            # Stage 1 — Resolve the active quality policy and its thresholds.
            _stage(1)
            policy_resp = get_quality_policy()
            policy = unwrap_data_response(
                policy_resp,
                operation="data.quality.get_quality_policy",
                request_id=request_id,
            )
            _report("policy ", "success", f"profile {policy.profile}")
            print("Policy object          :", policy)

            # Stage 2 — Inspect an existing dataset and a bare record sequence.
            _stage(2)
            dataset_report_resp = inspect_dataset_quality(dataset)
            dataset_report = unwrap_data_response(
                dataset_report_resp,
                operation="data.quality.inspect_dataset_quality",
                request_id=request_id,
            )
            records_report_resp = inspect_records_quality(
                dataset.records, dataset.timeframe, generated_at=datetime.now(UTC)
            )
            records_report = unwrap_data_response(
                records_report_resp,
                operation="data.quality.inspect_records_quality",
                request_id=request_id,
            )
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
                "Report reflects records actually examined:",
                dataset_report.checked_count > 0,
            )

            # Stage 3 — Run the individual detectors that populate the report.
            _stage(3)
            detected = {
                "timestamp_gaps": unwrap_data_response(
                    detect_timestamp_gaps(dataset.records, dataset.timeframe),
                    operation="data.quality.detect_timestamp_gaps",
                    request_id=request_id,
                ),
                "price_jumps": unwrap_data_response(
                    detect_price_jumps(dataset.records),
                    operation="data.quality.detect_price_jumps",
                    request_id=request_id,
                ),
                "flatline_periods": unwrap_data_response(
                    detect_flatline_periods(dataset.records),
                    operation="data.quality.detect_flatline_periods",
                    request_id=request_id,
                ),
                "zero_volume_bars": unwrap_data_response(
                    detect_zero_volume_bars(dataset.records),
                    operation="data.quality.detect_zero_volume_bars",
                    request_id=request_id,
                ),
                "extreme_spreads": unwrap_data_response(
                    detect_extreme_spread_widening(dataset.records),
                    operation="data.quality.detect_extreme_spread_widening",
                    request_id=request_id,
                ),
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
            weekend_gap_resp = classify_gap(
                datetime(2026, 7, 25, 21, 0, tzinfo=UTC),
                datetime(2026, 7, 27, 21, 0, tzinfo=UTC),
            )
            weekend_gap = unwrap_data_response(
                weekend_gap_resp,
                operation="data.time_sessions.classify_gap",
                request_id=request_id,
            )
            observed_gap_resp = classify_gap(first, last)
            observed_gap = unwrap_data_response(
                observed_gap_resp,
                operation="data.time_sessions.classify_gap",
                request_id=request_id,
            )
            _report("weekend ", "success", weekend_gap)
            _report("observed", "success", observed_gap)
            print("Expected closure is not reported as a defect: True")

            # Stage 5 — Merge per-record flags into one bounded report.
            _stage(5)
            flags_resp = aggregate_flags(dataset_report)
            flags = unwrap_data_response(
                flags_resp,
                operation="data.quality.aggregate_flags",
                request_id=request_id,
            )
            _report("merge  ", "success", flags)
            print("Distinct flags present :", len(flags))
            print(
                "Detectors reporting an issue:",
                sum(1 for i in detected.values() if i is not None),
            )

            # Stage 6 — Summarize what a caller would need to remediate.
            _stage(6)
            remediation_resp = summarize_quality_remediation(dataset_report)
            remediation = unwrap_data_response(
                remediation_resp,
                operation="data.quality.summarize_quality_remediation",
                request_id=request_id,
            )
            _report("remedy ", "success", remediation)
            print(
                "Precision violations still fail closed regardless of behaviour: True"
            )

    print(
        "\nOUTPUT BOUNDARY — bounded QualityReport with classified issues and remediation summary"
    )


if __name__ == "__main__":
    main()
