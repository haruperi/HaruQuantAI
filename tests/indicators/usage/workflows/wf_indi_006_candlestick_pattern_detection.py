"""WF-INDI-006: detect official candlestick patterns end to end."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import (
    doji,
    engulfing,
    get_indicator,
    get_indicator_result_metadata,
    get_indicator_result_values,
    get_warmup_requirement,
    inside_bar,
    pinbar,
    validate_indicator,
)
from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    unwrap_indicator_response,
)
from tests.indicators.usage.workflows._support import indicator_config, live_bars

WORKFLOW_ID = "WF-INDI-006"
STAGES = (
    "Resolve the pattern spec and validate the config and input.",
    "Resolve the warmup cost, which for multi-bar patterns exceeds one row.",
    "Execute the approved detector over canonical row order.",
    "Retain warmup rows as explicitly unavailable rather than emitting False.",
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
    """Run the documented candlestick-pattern detection workflow."""
    _feature_header(
        "WF-INDI-006: Candlestick Pattern Detection\n\n"
        "Purpose: Resolve pattern contracts and detect doji/engulfing/pinbar/inside_bar "
        "without retrospective repainting.\n\n"
        "Module flow:\n"
        "-> market data + indicator config\n"
        "-> validation and warmup resolution\n"
        "-> detector execution"
    )
    print(f"{WORKFLOW_ID} — Candlestick Pattern Detection")
    print("INPUT BOUNDARY — one MarketDataset v1 and an official pattern ID")
    # Stage 1
    _stage(1)
    dataset = live_bars()
    print_market_evidence(dataset)
    config = indicator_config("engulfing", source=None)
    spec = unwrap_indicator_response(get_indicator("engulfing"))
    print(_format_result(spec))
    print(f"Data -> spec_id={spec.indicator_id}, formula={spec.formula_version}")
    # Stage 2
    _stage(2)
    validated = unwrap_indicator_response(
        validate_indicator("engulfing", dataset, config)
    )
    warmup = unwrap_indicator_response(get_warmup_requirement("engulfing", config))
    print(_format_result(validated))
    print(
        f"Data -> validated_id={validated.indicator_id}, min_rows={warmup.minimum_observations}"
    )
    print("Data -> warmup_period=", warmup.minimum_observations)
    # Stage 3
    _stage(3)
    detectors = {
        "doji": unwrap_indicator_response(
            doji(
                dataset,
                threshold=0.1,
                config=indicator_config(
                    "doji", source=None, parameters=(("threshold", 0.1),)
                ),
            )
        ),
        "engulfing": unwrap_indicator_response(engulfing(dataset, config=config)),
        "pinbar": unwrap_indicator_response(
            pinbar(dataset, config=indicator_config("pinbar", source=None))
        ),
        "inside_bar": unwrap_indicator_response(
            inside_bar(dataset, config=indicator_config("inside_bar", source=None))
        ),
    }
    for name, result in detectors.items():
        result_values = get_indicator_result_values(result)
        print(_format_result(result))
        print(
            f"Data -> {name} rows={len(result_values)} unavailable={result_values['unavailable_reason'].notna().sum()}"
        )
        print_indicator_evidence(result, label=f"{name} detected-pattern rows")
    # Stage 4
    _stage(4)
    print("OUTPUT BOUNDARY — candlestick pattern result")
    engulfing_result = detectors["engulfing"]
    unavailable = int(
        get_indicator_result_values(engulfing_result)["unavailable_reason"]
        .notna()
        .sum()
    )
    print(_format_result(engulfing_result))
    print(
        f"Data -> unavailable_rows={unavailable}, "
        f"result_rows={get_indicator_result_metadata(engulfing_result)['manifest']['row_count']}"
    )
    print(
        "Quality status:",
        get_indicator_result_metadata(engulfing_result)["manifest"].get(
            "quality_status"
        ),
    )


if __name__ == "__main__":
    main()
