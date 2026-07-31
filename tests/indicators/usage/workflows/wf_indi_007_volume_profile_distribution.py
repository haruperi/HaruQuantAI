"""WF-INDI-007: build volume-profile and volume-flow evidence end to end."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

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
    """Run the documented volume-profile and volume-flow workflow."""
    _feature_header(
        "WF-INDI-007: Volume-Profile and Volume-Flow Distribution\n\n"
        "Purpose: Validate volume availability and produce profile/flow outputs while "
        "preserving unavailable rows where source volume is absent.\n\n"
        "Module flow:\n"
        "-> dataset + validated volume config\n"
        "-> distribution or flow calculation per stage\n"
        "-> explicit unavailability for missing volume"
    )
    print(f"{WORKFLOW_ID} — Volume-Profile and Volume-Flow Distribution")
    print("INPUT BOUNDARY — one MarketDataset v1 carrying volume plus bounded config")
    # Stage 1
    _stage(1)
    dataset = live_bars()
    print_market_evidence(dataset)
    config = indicator_config("obv", source=None)
    validated = unwrap_indicator_response(validate_indicator("obv", dataset, config))
    first_record = dataset.records[0]
    print(_format_result(validated))
    print(
        "Data -> ",
        "has_volume_field=",
        hasattr(first_record, "volume"),
        "volume=",
        getattr(first_record, "volume", None),
    )
    # Stage 2
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
    distribution_values = get_indicator_result_values(distribution)
    print(_format_result(distribution))
    print(
        f"Data -> distribution_rows={len(distribution_values)}, "
        f"columns={list(distribution_values.columns)}"
    )
    print_indicator_evidence(
        distribution,
        label="Price-volume distribution rows",
    )
    # Stage 3
    _stage(3)
    flows = {
        "obv": unwrap_indicator_response(obv(dataset, config=config)),
        "mfi": unwrap_indicator_response(
            mfi(dataset, period=14, config=indicator_config("mfi", 14, source=None))
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
        flow_values = get_indicator_result_values(result)
        print(_format_result(result))
        print(
            f"Data -> {name} rows={len(flow_values)}, "
            f"row_checksum_columns={list(flow_values.columns)[:4]}"
        )
        print_indicator_evidence(result, label=f"{name} flow rows")
    # Stage 4
    _stage(4)
    print("OUTPUT BOUNDARY — volume profile distribution series")
    zero_volume_response = detect_zero_volume_bars(dataset.records)
    zero_volume_issue = unwrap_data_response(
        zero_volume_response,
        operation="indicators.usage.workflow.detect_zero_volume_bars",
        request_id=zero_volume_response.metadata.request_id,
    )
    unavailable = int(
        get_indicator_result_values(flows["mfi"])["unavailable_reason"].notna().sum()
    )
    print(_format_result(flows["mfi"]))
    print(
        "Data -> ",
        "zero_volume_issue=",
        "none" if zero_volume_issue is None else zero_volume_issue,
        ", unavailable_rows=",
        unavailable,
    )
    print("Rows marked unavailable:", unavailable)
    metadata = get_indicator_result_metadata(flows["mfi"])
    print(
        f"Data -> manifest_rows={metadata['manifest']['row_count']}, checksum={metadata['manifest']['output_checksum']}"
    )


if __name__ == "__main__":
    main()
