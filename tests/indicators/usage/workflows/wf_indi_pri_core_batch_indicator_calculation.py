"""WF-INDI-PRI: execute the complete core batch-indicator workflow."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import (
    get_indicator,
    get_indicator_result_metadata,
    get_indicator_result_values,
    sma,
    validate_indicator,
)
from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    unwrap_indicator_response,
)
from tests.indicators.usage.workflows._support import indicator_config, live_bars

WORKFLOW_ID = "WF-INDI-PRI"
STAGES = (
    "Resolve and validate the official indicator request.",
    "Resolve and validate the request before calculation.",
    "Run the official vectorized formula in canonical row order.",
    "Preserve warmup availability, provenance, and quality evidence.",
    "Return one atomic IndicatorResult.",
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
        "WF-INDI-PRI: Core Batch Indicator Calculation\n\n"
        "Purpose: Execute the canonical batch pipeline from normalized input through "
        "official validation and indicator calculation, returning one atomic IndicatorResult.\n\n"
        "Module flow:\n"
        "-> dataset + config\n"
        "-> resolve and validate indicator request\n"
        "-> execute official formula and return IndicatorResult"
    )
    print("INPUT BOUNDARY — dataset + config")
    # Stage 1
    _stage(1)
    dataset = live_bars()
    spec = unwrap_indicator_response(get_indicator("sma"))
    config = indicator_config("sma", 5)
    print(f"\n\nIndicator Spec: {_format_result(spec)}")
    print(
        f"\nData -> indicator={spec.indicator_id}, formula={spec.formula_version}, "
        f"\ncache_limit={dataset.record_count}"
    )
    print_market_evidence(dataset)
    # Stage 2
    _stage(2)
    resolved_spec = unwrap_indicator_response(
        validate_indicator("sma", dataset, config)
    )
    print(f"\n\nResolved Spec: {_format_result(resolved_spec)}")
    print(f"\nData -> validated_indicator={resolved_spec.indicator_id}")
    # Stage 3
    _stage(3)
    result = unwrap_indicator_response(sma(dataset, period=5, config=config))
    result_values = get_indicator_result_values(result)
    unavailable_rows = int(result_values["unavailable_reason"].notna().sum())
    print(f"\n\nCalculated Result: {_format_result(result)}")
    print(f"\nData -> rows={len(result_values)}, unavailable_rows={unavailable_rows}")
    print_indicator_evidence(result, label="Calculated SMA workflow rows")
    # Stage 4
    _stage(4)
    metadata = get_indicator_result_metadata(result)
    manifest = metadata["manifest"]
    print(f"\n\nManifest: {_format_result(manifest)}")
    print(
        f"\nData -> manifest_quality={manifest['quality_status']}, "
        f"source_timeframe={manifest['source_timeframe']}",
    )
    print(
        f"\nEvidence: {manifest['quality_status']}, "
        f"{manifest['source_timeframe']}, "
        f"{result_values['unavailable_reason'].notna().sum()} unavailable rows",
    )
    # Stage 5
    _stage(5)
    print("OUTPUT BOUNDARY — atomic IndicatorResult")
    print(f"\n\nOutput: {_format_result(result)}")
    print(
        f"Output: {type(result).__name__}, {manifest['output_checksum']}",
    )
    print(f"Data -> unavailable_rows={unavailable_rows}")


if __name__ == "__main__":
    main()
