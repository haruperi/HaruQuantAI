"""WF-INDI-006: detect official candlestick patterns end to end."""

from __future__ import annotations

import sys
from pathlib import Path

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
    """Run the documented candlestick-pattern detection workflow."""
    print(f"{WORKFLOW_ID} — Candlestick Pattern Detection")
    print("INPUT BOUNDARY — one MarketDataset v1 and an official pattern ID")

    dataset = live_bars()
    print_market_evidence(dataset)

    # Stage 1 — Resolve the pattern spec and validate the config and input.
    _stage(1)
    config = indicator_config("engulfing", source=None)
    spec = unwrap_indicator_response(get_indicator("engulfing"))
    _report("spec   ", "success", f"{spec.indicator_id} v{spec.formula_version}")
    validated = unwrap_indicator_response(
        validate_indicator("engulfing", dataset, config)
    )
    _report("valid  ", "success", validated.indicator_id)

    # Stage 2 — Resolve the warmup cost, which for multi-bar patterns exceeds one row.
    _stage(2)
    warmup = unwrap_indicator_response(get_warmup_requirement("engulfing", config))
    _report("warmup ", "success", warmup)
    print("Multi-bar pattern needs prior bar: True")

    # Stage 3 — Execute the approved detector over canonical row order.
    _stage(3)
    detectors = {
        "doji": unwrap_indicator_response(
            doji(
                dataset,
                threshold=0.1,
                config=indicator_config(
                    "doji",
                    source=None,
                    parameters=(("threshold", 0.1),),
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
        _report(
            f"{name:<10}",
            "success",
            f"{get_indicator_result_metadata(result)['manifest']['row_count']} rows, checksum {get_indicator_result_metadata(result)['manifest']['output_checksum']}",
        )
        print_indicator_evidence(result, label=f"{name} detected-pattern rows")

    # Stage 4 — Retain warmup rows as explicitly unavailable rather than emitting False.
    _stage(4)
    engulfing_result = detectors["engulfing"]
    unavailable = (
        get_indicator_result_values(engulfing_result)["unavailable_reason"]
        .notna()
        .sum()
    )
    print(
        "Rows retained          :",
        get_indicator_result_metadata(engulfing_result)["manifest"]["row_count"],
    )
    print("Rows marked unavailable:", unavailable)
    print(
        "Quality status         :",
        get_indicator_result_metadata(engulfing_result)["manifest"].get(
            "quality_status"
        ),
    )
    assert (
        get_indicator_result_metadata(engulfing_result)["manifest"]["row_count"]
        == dataset.record_count
    )

    print(
        "\nOUTPUT BOUNDARY — boolean pattern series with indicator availability semantics"
    )


if __name__ == "__main__":
    main()
