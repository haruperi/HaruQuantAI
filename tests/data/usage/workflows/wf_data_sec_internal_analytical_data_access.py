"""WF-DATA-SEC: project canonical MT5 history for analytical consumers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import get_market_data, to_ohlcv_dataframe
from tests.data.usage.workflows._support import market_request

WORKFLOW_ID = "WF-DATA-SEC"
STAGES = (
    "Accept an approved typed analytical request.",
    "Retrieve one canonical MT5 MarketDataset.",
    "Create a detached analytical projection without exposing provider state.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute canonical-to-analytical access."""
    print(f"{WORKFLOW_ID} — Internal Analytical Data Access")
    print("INPUT BOUNDARY — approved Python consumer MarketDataRequest")

    # Stage 1 — Accept an approved typed analytical request.
    _stage(1)
    request = market_request("bars", timeframe="M1")

    # Stage 2 — Retrieve one canonical MT5 MarketDataset.
    _stage(2)
    dataset = get_market_data(request)
    assert dataset.request_id == request.request_id

    # Stage 3 — Create a detached analytical projection without exposing provider state.
    _stage(3)
    frame = to_ohlcv_dataframe(dataset)
    assert len(frame) == dataset.record_count
    print("Analytical shape:", frame.shape)
    print("OUTPUT BOUNDARY — typed MarketDataset plus detached DataFrame")


if __name__ == "__main__":
    main()
