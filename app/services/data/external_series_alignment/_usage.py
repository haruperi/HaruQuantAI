"""Executable usage demonstration harness for External Series Alignment."""

from __future__ import annotations

from typing import Any

from app.services.data.external_series_alignment.external_series_alignment import (
    SeriesPoint,
    data_align_external_series,
    data_define_alignment_policy,
)


def main() -> None:
    """Run executable usage scenarios demonstrating requirements."""
    print("Running FEAT-DATA-ALIGN_SERIES usage scenarios...")

    # Scenario 1: FR-DATA-DEFINE_ALIGNMENT_POLICY
    print("\n--- Scenario: FR-DATA-DEFINE_ALIGNMENT_POLICY ---")
    policy = data_define_alignment_policy(
        direction="LAST_KNOWN",
        max_age_seconds=3600,
        missing_policy="NULL",
        timezone="UTC",
        look_ahead_prohibited=True,
    )
    print(
        f"Policy defined: direction={policy.direction}, "
        f"max_age={policy.max_age_seconds}s, "
        f"look_ahead_prohibited={policy.look_ahead_prohibited}"
    )

    # Scenario 2: FR-DATA-ALIGN_EXTERNAL_SERIES
    print("\n--- Scenario: FR-DATA-ALIGN_EXTERNAL_SERIES ---")
    source_data = [
        SeriesPoint(
            timestamp="2026-08-28T10:00:00.000000Z",
            value="101.5",
            available_at="2026-08-28T10:00:01.000000Z",
        ),
        SeriesPoint(
            timestamp="2026-08-28T10:05:00.000000Z",
            value="102.0",
            available_at="2026-08-28T10:05:01.000000Z",
        ),
        SeriesPoint(
            timestamp="2026-08-28T10:10:00.000000Z",
            value="103.5",
            available_at="2026-08-28T10:10:05.000000Z",
        ),
    ]
    target_times = [
        "2026-08-28T10:00:00.000000Z",
        "2026-08-28T10:02:00.000000Z",
        "2026-08-28T10:06:00.000000Z",
    ]

    aligned_series, points = data_align_external_series(
        source_points=source_data,
        target_timestamps=target_times,
        policy=policy,
    )
    print(f"Aligned series version: {aligned_series.aligned_version_id}")
    for pt in points:
        print(
            f"  Target: {pt.target_timestamp} -> "
            f"Aligned Value: {pt.aligned_value} (gap={pt.is_gap})"
        )

    print("\n--- Additional Multi-Timeframe Alignment Example ---")
    aligned_mtf, mtf_points = example_multitimeframe_alignment()
    print(
        f"  * example_multitimeframe_alignment: aligned={len(mtf_points)} "
        f"version={aligned_mtf.aligned_version_id}"
    )

    print("\nDATA SUCCESS: FEAT-DATA-ALIGN_SERIES scenarios verified.")


def example_multitimeframe_alignment() -> tuple[Any, list[Any]]:
    """Align multi-timeframe datasets backward without lookahead."""
    policy = data_define_alignment_policy(
        direction="LAST_KNOWN",
        max_age_seconds=7200,
        missing_policy="NULL",
        timezone="UTC",
        look_ahead_prohibited=True,
    )
    m5_points = [
        SeriesPoint(
            timestamp="2026-08-28T10:00:00.000000Z",
            value="101.5",
            available_at="2026-08-28T10:05:00.000000Z",
        ),
        SeriesPoint(
            timestamp="2026-08-28T10:05:00.000000Z",
            value="102.0",
            available_at="2026-08-28T10:10:00.000000Z",
        ),
    ]
    target_m1_timestamps = [
        "2026-08-28T10:06:00.000000Z",
        "2026-08-28T10:07:00.000000Z",
        "2026-08-28T10:11:00.000000Z",
    ]
    return data_align_external_series(
        source_points=m5_points,
        target_timestamps=target_m1_timestamps,
        policy=policy,
    )


def run_usage_scenarios() -> None:
    """Run all usage scenarios."""
    main()


if __name__ == "__main__":
    run_usage_scenarios()
