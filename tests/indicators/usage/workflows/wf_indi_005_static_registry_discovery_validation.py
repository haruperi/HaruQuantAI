"""WF-INDI-005: discover and validate the static indicator registry."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import (
    get_capability_matrix,
    get_indicator,
    list_indicators,
    validate_indicator,
)
from tests.indicators.usage._support import (
    print_market_evidence,
    unwrap_indicator_response,
)
from tests.indicators.usage.workflows._support import indicator_config, live_bars

WORKFLOW_ID = "WF-INDI-005"
STAGES = (
    "List every statically registered official indicator.",
    "Read the immutable capability matrix.",
    "Resolve one indicator specification by canonical ID.",
    "Validate configuration against genuine normalized Data evidence.",
    "Return the resolved specification or deterministic IndicatorError.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Consumer supplies registry discovery/validation inputs.
    _stage(1)
    specs = unwrap_indicator_response(list_indicators())
    print("Registered indicators:", len(specs))

    # Stage 2: Read machine-readable capabilities.
    _stage(2)
    matrix = unwrap_indicator_response(get_capability_matrix())
    print("Capability records:", len(matrix))

    # Stage 3: Resolve the canonical specification.
    _stage(3)
    spec = unwrap_indicator_response(get_indicator("sma"))
    print("Resolved:", spec.indicator_id, spec.formula_version)

    # Stage 4: Validate against real Data output.
    _stage(4)
    dataset = live_bars()
    print_market_evidence(dataset)
    resolved = unwrap_indicator_response(
        validate_indicator("sma", dataset, indicator_config("sma", 5))
    )
    print("Validated:", resolved.indicator_id, dataset.source_metadata.get("source_id"))

    # Stage 5 — OUTPUT BOUNDARY: Return immutable registry/validation evidence.
    _stage(5)
    print("Output:", type(resolved).__name__)


if __name__ == "__main__":
    main()
