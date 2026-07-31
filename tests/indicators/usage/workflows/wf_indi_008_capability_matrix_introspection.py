"""WF-INDI-008: plan history from the static capability matrix without calculating."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import (
    get_capability_matrix,
    get_indicator,
    get_warmup_requirement,
    list_indicators,
)
from tests.indicators.usage._support import unwrap_indicator_response
from tests.indicators.usage.workflows._support import indicator_config

WORKFLOW_ID = "WF-INDI-008"
STAGES = (
    "Enumerate the official indicator set.",
    "Read declared capabilities and required input fields.",
    "Resolve the exact warmup cost for each planned indicator and config.",
    "Size the upstream history request from the largest resolved warmup.",
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
    """Run the documented capability-matrix introspection workflow."""
    _feature_header(
        "WF-INDI-008: Capability-Matrix Introspection\n\n"
        "Purpose: Read immutable capability metadata and resolve per-indicator warmup "
        "requirements to size upstream history before calculation.\n\n"
        "Module flow:\n"
        "-> register and capability discovery\n"
        "-> resolve indicator warmup requirements\n"
        "-> derive upstream history requirement"
    )
    print(f"{WORKFLOW_ID} — Capability-Matrix Introspection")
    print("INPUT BOUNDARY — capability and warmup query")
    # Stage 1
    _stage(1)
    specs = unwrap_indicator_response(list_indicators())
    print(_format_result(specs))
    print("Data -> registered=", len(specs))
    # Stage 2
    _stage(2)
    matrix = unwrap_indicator_response(get_capability_matrix())
    print(_format_result(matrix))
    print("Data -> capability_records=", len(matrix))
    # Stage 3
    _stage(3)
    planned = (("sma", 5), ("rsi", 14), ("cmf", 20))
    warmups: dict[str, object] = {}
    for indicator_id, period in planned:
        spec = unwrap_indicator_response(get_indicator(indicator_id))
        config = indicator_config(
            indicator_id,
            period,
            source=None if indicator_id == "cmf" else "close",
        )
        requirement = unwrap_indicator_response(
            get_warmup_requirement(indicator_id, config)
        )
        warmups[indicator_id] = requirement
        print(_format_result(requirement))
        print(
            "Data ->",
            indicator_id,
            "minimum=",
            requirement.minimum_observations,
            "formula=",
            spec.formula_version,
        )
    # Stage 4
    _stage(4)
    print("OUTPUT BOUNDARY — capability matrix and warmup requirements")
    minimum_bars = [
        getattr(requirement, "minimum_observations", None)
        for requirement in warmups.values()
    ]
    resolved = [value for value in minimum_bars if isinstance(value, int)]
    print(_format_result(warmups))
    if resolved:
        required = max(resolved)
        print("Data -> per-indicator minimums:", resolved)
        print("Data -> requested_rows=", required)
    else:
        print("Data -> per-indicator_warmups=", list(warmups.values()))
        print("Data -> upstream rows derived from largest resolved warmup requirement")


if __name__ == "__main__":
    main()
