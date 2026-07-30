"""WF-INDI-003: coordinate indicator warmup before calculation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import (
    get_indicator,
    get_indicator_result_metadata,
    get_indicator_result_values,
    get_warmup_requirement,
    sma,
    validate_indicator,
)
from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    unwrap_indicator_response,
)
from tests.indicators.usage.workflows._support import indicator_config, live_bars

WORKFLOW_ID = "WF-INDI-003"
STAGES = (
    "Resolve the official indicator specification without fetching data.",
    "Calculate the exact warmup requirement from immutable configuration.",
    "Request enough genuine normalized history through Data.",
    "Validate and calculate while retaining unavailable warmup rows.",
    "Return typed values with explicit warmup availability.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Consumer supplies indicator ID and parameters.
    _stage(1)
    spec = unwrap_indicator_response(get_indicator("sma"))
    print("Specification:", spec.indicator_id, spec.formula_version)

    # Stage 2: Resolve the warmup contract.
    _stage(2)
    config = indicator_config("sma", 10)
    requirement = unwrap_indicator_response(get_warmup_requirement("sma", config))
    print("Minimum observations:", requirement.minimum_observations)

    # Stage 3: Data performs the genuine MT5 read.
    _stage(3)
    dataset = live_bars(limit=max(40, requirement.minimum_observations + 1))
    print_market_evidence(dataset)

    # Stage 4: Validate and calculate without silently dropping warmup.
    _stage(4)
    unwrap_indicator_response(validate_indicator("sma", dataset, config))
    result = unwrap_indicator_response(sma(dataset, period=10, config=config))
    unavailable = int(
        get_indicator_result_values(result)["unavailable_reason"].notna().sum()
    )
    print_indicator_evidence(result, label="Warmup-preserving SMA rows")
    print("Retained warmup rows:", unavailable)

    # Stage 5 — OUTPUT BOUNDARY: Return the typed IndicatorResult.
    _stage(5)
    print(
        "Output:",
        type(result).__name__,
        get_indicator_result_metadata(result)["manifest"]["row_count"],
        "rows",
    )


if __name__ == "__main__":
    main()
