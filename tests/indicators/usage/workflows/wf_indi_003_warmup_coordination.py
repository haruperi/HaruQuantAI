"""WF-INDI-003: coordinate indicator warmup before calculation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

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


def _feature_header(title: str) -> None:
    """Print the feature banner and module flow."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    _feature_header(
        "WF-INDI-003: Warmup Coordination\n\n"
        "Purpose: Resolve required warmup, fetch sufficient history, and keep warmup rows "
        "explicitly unavailable while retaining deterministic ordering.\n\n"
        "Module flow:\n"
        "-> input spec + warmup requirement\n"
        "-> fetch sufficient dataset history\n"
        "-> validate, calculate, and retain unavailable warmup rows"
    )
    print("INPUT BOUNDARY — indicator config + warmup query")
    # Stage 1
    _stage(1)
    spec = unwrap_indicator_response(get_indicator("sma"))
    print(_format_result(spec))
    print(
        f"Data -> spec_id={spec.indicator_id}, source_timeframe={spec.required_columns}"
    )
    # Stage 2
    _stage(2)
    config = indicator_config("sma", 10)
    requirement = unwrap_indicator_response(get_warmup_requirement("sma", config))
    print(_format_result(requirement))
    print(f"Data -> minimum_observations={requirement.minimum_observations}")
    # Stage 3
    _stage(3)
    dataset = live_bars(limit=max(40, requirement.minimum_observations + 1))
    print_market_evidence(dataset)
    print(_format_result(dataset))
    print(f"Data -> requested_rows={len(dataset)}")
    # Stage 4
    _stage(4)
    unwrap_indicator_response(validate_indicator("sma", dataset, config))
    # NOTE: Existing behavior intentionally validates and calculates in-place.
    result = unwrap_indicator_response(sma(dataset, period=10, config=config))
    unavailable = int(
        get_indicator_result_values(result)["unavailable_reason"].notna().sum()
    )
    _ = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> unavailable_rows={unavailable}")
    print_indicator_evidence(result, label="Warmup-preserving SMA rows")
    # Stage 5
    _stage(5)
    print("OUTPUT BOUNDARY — warmup-preserving indicator result")
    metadata = get_indicator_result_metadata(result)
    print(_format_result(metadata))
    print(
        f"Data -> output_rows={metadata['manifest']['row_count']}, "
        f"quality={metadata['manifest']['quality_status']}"
    )
    print(
        "Output:",
        type(result).__name__,
        metadata["manifest"]["row_count"],
        "rows",
    )


if __name__ == "__main__":
    main()
