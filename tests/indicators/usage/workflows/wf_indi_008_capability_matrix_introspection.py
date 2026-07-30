"""WF-INDI-008: plan history from the static capability matrix without calculating."""

from __future__ import annotations

import sys
from pathlib import Path

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
    """Run the documented capability-matrix introspection workflow."""
    print(f"{WORKFLOW_ID} — Capability-Matrix Introspection")
    print(
        "INPUT BOUNDARY — planning caller queries the registry before requesting history"
    )

    # Stage 1 — Enumerate the official indicator set.
    _stage(1)
    specs = unwrap_indicator_response(list_indicators())
    _report("registry", "success", f"{len(specs)} official indicators")
    print("First identifiers      :", [spec.indicator_id for spec in specs[:6]])

    # Stage 2 — Read declared capabilities and required input fields.
    _stage(2)
    matrix = unwrap_indicator_response(get_capability_matrix())
    _report("matrix  ", "success", f"{len(matrix)} capability records")
    sample = matrix[0]
    print("Record keys            :", list(sample.keys()))
    print("Sample record          :", dict(sample))
    assert len(matrix) == len(specs)

    # Stage 3 — Resolve the exact warmup cost for each planned indicator and config.
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
        _report(
            f"{indicator_id:<8}",
            "success",
            f"period {period}, spec v{spec.formula_version}, warmup {requirement}",
        )

    # Stage 4 — Size the upstream history request from the largest resolved warmup.
    _stage(4)
    minimum_bars = [
        getattr(requirement, "minimum_observations", None)
        for requirement in warmups.values()
    ]
    resolved = [value for value in minimum_bars if isinstance(value, int)]
    if resolved:
        required = max(resolved)
        print("Per-indicator minimums :", resolved)
        print("History rows to request:", required)
    else:
        print("Per-indicator warmups  :", list(warmups.values()))
        print("History sizing uses the largest declared warmup requirement.")
    print("No calculation performed and no data fetched: True")

    print("\nOUTPUT BOUNDARY — capability matrix plus per-indicator WarmupRequirement")


if __name__ == "__main__":
    main()
