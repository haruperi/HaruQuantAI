"""WF-INDI-007: build volume-profile and volume-flow evidence end to end."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import detect_zero_volume_bars, unwrap_data_response
from app.services.indicators import (
    cmf,
    get_indicator_result_metadata,
    get_indicator_result_values,
    mfi,
    obv,
    price_volume_distribution,
    validate_indicator,
)
from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    unwrap_indicator_response,
)
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
    print_market_evidence(dataset)

    # Stage 1 — Validate that the dataset carries usable volume for the request.
    _stage(1)
    config = indicator_config("obv", source=None)
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
            config=indicator_config(
                "price_volume_distribution",
                20,
                source=None,
                parameters=(("bins", 10),),
            ),
        )
    )
    _report(
        "profile",
        "success",
        f"{get_indicator_result_metadata(distribution)['manifest']['row_count']} rows over 10 price buckets",
    )
    print(
        "Output columns         :",
        list(get_indicator_result_values(distribution).columns)[:6],
    )
    print_indicator_evidence(
        distribution,
        label="Price-volume distribution rows",
    )

    # Stage 3 — Calculate cumulative and money-weighted flow series.
    _stage(3)
    flows = {
        "obv": unwrap_indicator_response(obv(dataset, config=config)),
        "mfi": unwrap_indicator_response(
            mfi(
                dataset,
                period=14,
                config=indicator_config("mfi", 14, source=None),
            )
        ),
        "cmf": unwrap_indicator_response(
            cmf(
                dataset,
                period=20,
                config=indicator_config("cmf", 20, source=None),
            )
        ),
    }
    for name, result in flows.items():
        _report(
            f"{name:<7}",
            "success",
            f"{get_indicator_result_metadata(result)['manifest']['row_count']} rows, checksum {get_indicator_result_metadata(result)['manifest']['output_checksum']}",
        )
        print_indicator_evidence(result, label=f"{name} flow rows")

    # Stage 4 — Mark rows whose source volume is zero or missing as unavailable.
    _stage(4)
    zero_volume_response = detect_zero_volume_bars(dataset.records)
    zero_volume_issue = unwrap_data_response(
        zero_volume_response,
        operation="indicators.usage.workflow.detect_zero_volume_bars",
        request_id=zero_volume_response.metadata.request_id,
    )
    _report(
        "zerovol",
        "success",
        "no zero-volume run detected"
        if zero_volume_issue is None
        else zero_volume_issue,
    )
    mfi_result = flows["mfi"]
    unavailable = (
        get_indicator_result_values(mfi_result)["unavailable_reason"].notna().sum()
    )
    print("Rows marked unavailable:", unavailable)
    print("Absence treated as zero flow: False")
    assert (
        get_indicator_result_metadata(mfi_result)["manifest"]["row_count"]
        == dataset.record_count
    )

    print(
        "\nOUTPUT BOUNDARY — distribution or flow series with explicit unavailability"
    )


if __name__ == "__main__":
    main()
