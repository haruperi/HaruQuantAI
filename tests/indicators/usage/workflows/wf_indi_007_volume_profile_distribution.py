"""WF-INDI-007: build volume-profile and volume-flow evidence end to end."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import detect_zero_volume_bars
from app.services.indicators import (
    cmf,
    mfi,
    obv,
    price_volume_distribution,
    validate_indicator,
)
from tests.indicators.usage._support import unwrap_indicator_response
from tests.indicators.usage.workflows._support import indicator_config, live_bars

WORKFLOW_ID = "WF-INDI-007"
STAGES = (
    "Validate that the dataset carries usable volume for the request.",
    "Build the price-bucketed volume distribution over the bounded window.",
    "Calculate cumulative and money-weighted flow series.",
    "Mark rows whose source volume is zero or missing as unavailable.",
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
    """Run the documented volume-profile and volume-flow workflow."""
    print(f"{WORKFLOW_ID} — Volume-Profile and Volume-Flow Distribution")
    print("INPUT BOUNDARY — one MarketDataset v1 carrying volume plus bounded config")

    dataset = live_bars()
    print("Dataset:", dataset.symbol, dataset.timeframe, dataset.record_count, "bars")

    # Stage 1 — Validate that the dataset carries usable volume for the request.
    _stage(1)
    config = indicator_config("obv", 1)
    validated = unwrap_indicator_response(validate_indicator("obv", dataset, config))
    _report("valid  ", "success", validated.indicator_id)
    first_record = dataset.records[0]
    print("Volume field present   :", hasattr(first_record, "volume"))
    print("First record volume    :", getattr(first_record, "volume", None))

    # Stage 2 — Build the price-bucketed volume distribution over the bounded window.
    _stage(2)
    distribution = unwrap_indicator_response(
        price_volume_distribution(
            dataset,
            period=20,
            bins=10,
            config=indicator_config("price_volume_distribution", 20),
        )
    )
    _report(
        "profile",
        "success",
        f"{distribution.manifest.row_count} rows over 10 price buckets",
    )
    print("Output columns         :", list(distribution.values.columns)[:6])

    # Stage 3 — Calculate cumulative and money-weighted flow series.
    _stage(3)
    flows = {
        "obv": unwrap_indicator_response(obv(dataset, config=config)),
        "mfi": unwrap_indicator_response(
            mfi(dataset, period=14, config=indicator_config("mfi", 14))
        ),
        "cmf": unwrap_indicator_response(
            cmf(dataset, period=20, config=indicator_config("cmf", 20))
        ),
    }
    for name, result in flows.items():
        _report(
            f"{name:<7}",
            "success",
            f"{result.manifest.row_count} rows, checksum {result.manifest.output_checksum}",
        )

    # Stage 4 — Mark rows whose source volume is zero or missing as unavailable.
    _stage(4)
    zero_volume_issue = detect_zero_volume_bars(dataset.records)
    _report(
        "zerovol",
        "success",
        "no zero-volume run detected"
        if zero_volume_issue is None
        else zero_volume_issue,
    )
    mfi_result = flows["mfi"]
    unavailable = mfi_result.values["unavailable_reason"].notna().sum()
    print("Rows marked unavailable:", unavailable)
    print("Absence treated as zero flow: False")
    assert mfi_result.manifest.row_count == dataset.record_count

    print(
        "\nOUTPUT BOUNDARY — distribution or flow series with explicit unavailability"
    )


if __name__ == "__main__":
    main()
