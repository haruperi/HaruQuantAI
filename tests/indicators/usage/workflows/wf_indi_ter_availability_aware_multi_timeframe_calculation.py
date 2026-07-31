"""WF-INDI-TER: calculate independently aligned multi-timeframe indicators."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import align_multitimeframe_data, unwrap_data_response
from app.services.indicators import (
    get_indicator_result_metadata,
    get_indicator_result_values,
    sma,
)
from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    unwrap_indicator_response,
)
from tests.indicators.usage.workflows._support import live_bars

WORKFLOW_ID = "WF-INDI-TER"
STAGES = (
    "Read genuine primary and higher-timeframe MarketDataset values.",
    "Align both datasets to caller-owned decision timestamps.",
    "Calculate the official indicator independently per timeframe.",
    "Qualify higher-timeframe values by availability at decision time.",
    "Return separate typed results without hidden cross-timeframe joining.",
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
        "WF-INDI-TER: Availability-aware Multi-Timeframe Calculation\n\n"
        "Purpose: Preserve source-timeframe availability while calculating independent "
        "indicator series for primary and higher-timeframe datasets.\n\n"
        "Module flow:\n"
        "-> aligned dataset mapping + decision times\n"
        "-> resolve and validate per timeframe\n"
        "-> calculate independently and return typed IndicatorResult rows"
    )
    print("INPUT BOUNDARY — aligned multi-timeframe datasets")
    # Stage 1
    _stage(1)
    primary = live_bars("M1", 80)
    higher = live_bars("M5", 40)
    print_market_evidence(primary)
    print_market_evidence(higher)
    # Stage 2
    _stage(2)
    decision_start = max(primary.available_at, higher.available_at)
    target = tuple(decision_start + timedelta(seconds=index) for index in range(6))
    aligned_response = align_multitimeframe_data(
        {"primary": primary, "higher": higher},
        target,
    )
    aligned = unwrap_data_response(
        aligned_response,
        operation="indicators.usage.workflow.align_multitimeframe_data",
        request_id=aligned_response.metadata.request_id,
    )
    print(_format_result(aligned))
    print(
        f"Data -> aligned_primary={len(aligned['primary'])}, aligned_higher={len(aligned['higher'])}"
    )
    # Stage 3
    _stage(3)
    primary_result = unwrap_indicator_response(sma(aligned["primary"], period=5))
    higher_result = unwrap_indicator_response(sma(aligned["higher"], period=5))
    primary_values = get_indicator_result_values(primary_result)
    higher_values = get_indicator_result_values(higher_result)
    print(_format_result(primary_result))
    print(_format_result(higher_result))
    print(
        f"Data -> primary_rows={len(primary_values)}, higher_rows={len(higher_values)}"
    )
    print_indicator_evidence(primary_result, label="Primary-timeframe SMA rows")
    print_indicator_evidence(higher_result, label="Higher-timeframe SMA rows")
    print(
        "Data ->",
        get_indicator_result_metadata(primary_result)["manifest"]["source_timeframe"],
        get_indicator_result_metadata(higher_result)["manifest"]["source_timeframe"],
    )
    # Stage 4
    _stage(4)
    decision_time = primary_values["available_at"].iloc[-1]
    qualified_higher = higher_values.loc[higher_values["available_at"] <= decision_time]
    print(_format_result(qualified_higher))
    print(f"Data -> qualified_higher_rows={len(qualified_higher)}")
    # Stage 5
    _stage(5)
    print("OUTPUT BOUNDARY — combined multi-timeframe series")
    print("Output:", type(primary_result).__name__, type(higher_result).__name__)
    print(
        "Data -> output_boundary=",
        primary_values["available_at"].iloc[-1],
        qualified_higher["available_at"].iloc[-1]
        if not qualified_higher.empty
        else None,
    )


if __name__ == "__main__":
    main()
