"""WF-DATA-SEC: project canonical MT5 history for analytical consumers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import get_market_data, to_ohlcv_dataframe, unwrap_data_response
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime, market_request

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

    with (
        tempfile.TemporaryDirectory(prefix="wf-data-sec-") as directory,
        isolated_runtime(Path(directory)),
    ):
        request_id = generate_id("req")

        # Stage 1 — Accept an approved typed analytical request.
        _stage(1)
        request = market_request("bars", timeframe="M1")

        # Stage 2 — Retrieve one canonical MT5 MarketDataset.
        _stage(2)
        dataset_resp = get_market_data(request)
        dataset = unwrap_data_response(
            dataset_resp, operation="get_market_data", request_id=request_id
        )
        assert dataset.request_id == request.request_id

        # Stage 3 — Create a detached analytical projection without exposing provider state.
        _stage(3)
        frame_resp = to_ohlcv_dataframe(dataset)
        frame = unwrap_data_response(
            frame_resp, operation="to_ohlcv_dataframe", request_id=request_id
        )
        assert len(frame) == dataset.record_count
        print("Analytical shape:", frame.shape)
    print("OUTPUT BOUNDARY — typed MarketDataset plus detached DataFrame")


if __name__ == "__main__":
    main()
