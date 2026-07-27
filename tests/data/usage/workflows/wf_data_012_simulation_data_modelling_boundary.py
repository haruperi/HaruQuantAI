"""WF-DATA-012: demonstrate the Data-to-Simulation modelling boundary."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    get_market_data,
    inspect_dataset_quality,
    to_ohlcv_dataframe,
)
from tests.data.usage.workflows._support import market_request

WORKFLOW_ID = "WF-DATA-012"
STAGES = (
    "Accept Simulation's bounded canonical-history request.",
    "Retrieve genuine MT5 bars through Data normalization and quality.",
    "Return the typed dataset without constructing simulation ticks or fills.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute the ownership boundary without simulation modelling."""
    print(f"{WORKFLOW_ID} — Simulation Data-Modelling Boundary")
    print("INPUT BOUNDARY — Simulation requests canonical MT5 history")

    # Stage 1 — Accept Simulation's bounded canonical-history request.
    _stage(1)
    request = market_request("bars", timeframe="M1")

    # Stage 2 — Retrieve genuine MT5 bars through Data normalization and quality.
    _stage(2)
    dataset = get_market_data(request)
    report = inspect_dataset_quality(dataset)

    # Stage 3 — Return the typed dataset without constructing simulation ticks or fills.
    _stage(3)
    projection = to_ohlcv_dataframe(dataset)
    print(
        "Boundary evidence:",
        dataset.record_count,
        report.quality_status,
        projection.shape,
    )
    print("OUTPUT BOUNDARY — canonical MarketDataset; Simulation owns modelling")


if __name__ == "__main__":
    main()
