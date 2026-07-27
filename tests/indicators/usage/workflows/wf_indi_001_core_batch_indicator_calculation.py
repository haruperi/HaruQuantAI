"""WF-INDI-001: execute the complete core batch-indicator workflow."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import sma, validate_indicator
from tests.indicators.usage.workflows._support import indicator_config, live_bars

WORKFLOW_ID = "WF-INDI-001"
STAGES = (
    "Accept a normalized MarketDataset and immutable IndicatorConfig.",
    "Resolve and validate the official indicator request.",
    "Run the official vectorized formula in canonical row order.",
    "Preserve warmup availability, provenance, and quality evidence.",
    "Return one atomic IndicatorResult or IndicatorError.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Data supplies a genuine MT5-backed MarketDataset.
    _stage(1)
    dataset = live_bars()
    config = indicator_config("sma", 5)
    print("Input:", dataset.symbol, dataset.timeframe, dataset.record_count, "bars")

    # Stage 2: Resolve and validate before calculation.
    _stage(2)
    spec = validate_indicator("sma", dataset, config)
    print("Validated:", spec.indicator_id, spec.formula_version)

    # Stage 3: Execute the official formula.
    _stage(3)
    result = sma(dataset, period=5, source="close", config=config)
    print("Calculated rows:", result.manifest.row_count)

    # Stage 4: Inspect propagated evidence.
    _stage(4)
    print(
        "Evidence:",
        result.manifest.quality_status,
        result.manifest.source_timeframe,
        result.values["unavailable_reason"].notna().sum(),
        "unavailable rows",
    )

    # Stage 5 — OUTPUT BOUNDARY: Return the typed IndicatorResult.
    _stage(5)
    print("Output: IndicatorResult", result.manifest.output_checksum)


if __name__ == "__main__":
    main()
