"""WF-INDI-004: calculate independently aligned multi-timeframe indicators."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import align_multitimeframe_data, unwrap_data_response
from app.services.indicators import sma
from tests.indicators.usage._support import unwrap_indicator_response
from tests.indicators.usage.workflows._support import live_bars

WORKFLOW_ID = "WF-INDI-004"
STAGES = (
    "Read genuine primary and higher-timeframe MarketDataset values.",
    "Align both datasets to caller-owned decision timestamps.",
    "Calculate the official indicator independently per timeframe.",
    "Qualify higher-timeframe values by availability at decision time.",
    "Return separate typed results without hidden cross-timeframe joining.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Data supplies two genuine MT5-backed datasets.
    _stage(1)
    primary = live_bars("M1", 80)
    higher = live_bars("M5", 40)
    print(
        "Inputs:",
        primary.timeframe,
        primary.record_count,
        higher.timeframe,
        higher.record_count,
    )

    # Stage 2: Data aligns to explicit decision timestamps.
    _stage(2)
    decision_start = max(primary.available_at, higher.available_at)
    target = tuple(decision_start + timedelta(seconds=index) for index in range(6))
    aligned_response = align_multitimeframe_data(
        {"primary": primary, "higher": higher},
        target,
    )
    aligned = unwrap_data_response(
        aligned_response,
        operation="indicators.usage.workflow.align_multitimeframe_data",
        request_id=aligned_response.metadata.request_id,
    )
    print("Aligned rows:", len(target))

    # Stage 3: Indicators calculates each timeframe independently.
    _stage(3)
    primary_result = unwrap_indicator_response(sma(aligned["primary"], period=5))
    higher_result = unwrap_indicator_response(sma(aligned["higher"], period=5))
    print(
        "Calculated:",
        primary_result.manifest.source_timeframe,
        higher_result.manifest.source_timeframe,
    )

    # Stage 4: Caller applies availability-aware decision qualification.
    _stage(4)
    decision_time = primary_result.values["available_at"].iloc[-1]
    qualified_higher = higher_result.values.loc[
        higher_result.values["available_at"] <= decision_time
    ]
    print("Qualified higher-timeframe rows:", len(qualified_higher))

    # Stage 5 — OUTPUT BOUNDARY: Return independent typed IndicatorResult values.
    _stage(5)
    print("Output:", type(primary_result).__name__, type(higher_result).__name__)


if __name__ == "__main__":
    main()
