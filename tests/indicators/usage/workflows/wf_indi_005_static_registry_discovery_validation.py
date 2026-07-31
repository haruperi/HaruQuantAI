"""WF-INDI-005: discover and validate the static indicator registry."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

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
        "WF-INDI-005: Static Registry Discovery and Validation\n\n"
        "Purpose: Read registry and capabilities, validate candidate configs, and "
        "emit deterministic validation outcomes.\n\n"
        "Module flow:\n"
        "-> discover official indicator specs\n"
        "-> resolve indicator and capability metadata\n"
        "-> validate config against normalized dataset"
    )
    print("INPUT BOUNDARY — requested indicator query")
    # Stage 1
    _stage(1)
    specs = unwrap_indicator_response(list_indicators())
    print(_format_result(specs))
    print(f"Data -> Registered indicators={len(specs)}")
    # Stage 2
    _stage(2)
    matrix = unwrap_indicator_response(get_capability_matrix())
    print(_format_result(matrix))
    print(f"Data -> Capability records={len(matrix)}")
    # Stage 3
    _stage(3)
    spec = unwrap_indicator_response(get_indicator("sma"))
    print(_format_result(spec))
    print(f"Data -> Resolved={spec.indicator_id}")
    # Stage 4
    _stage(4)
    dataset = live_bars()
    print_market_evidence(dataset)
    resolved = unwrap_indicator_response(
        validate_indicator("sma", dataset, indicator_config("sma", 5))
    )
    print(_format_result(resolved))
    print(
        f"Data -> Validated indicator={resolved.indicator_id}, source={dataset.source_metadata.get('source_id')}"
    )
    # Stage 5
    _stage(5)
    print("OUTPUT BOUNDARY — spec and capability record")
    print(_format_result(resolved))
    print(f"Data -> final_output={type(resolved).__name__}")


if __name__ == "__main__":
    main()
