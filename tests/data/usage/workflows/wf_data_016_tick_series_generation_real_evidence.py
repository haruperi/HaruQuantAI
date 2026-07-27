"""WF-DATA-016: generate ticks and Parquet from genuine MT5 bars."""

from __future__ import annotations

import sys
import tempfile
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    DataSettings,
    generate_tick_series,
    generate_tick_series_to_parquet,
    get_market_data,
)
from tests.data.usage.workflows._support import market_request

WORKFLOW_ID = "WF-DATA-016"
STAGES = (
    "Retrieve bounded genuine MT5 bar evidence.",
    "Select one approved tick and spread model.",
    "Generate canonical ordered ticks with intra-bar phase metadata.",
    "Stream the bounded result to a temporary Parquet artifact.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute tick generation from real bars."""
    print(f"{WORKFLOW_ID} — Tick-Series Generation from Real Evidence")
    print("INPUT BOUNDARY — genuine MT5 MarketDataset and approved models")

    # Stage 1 — Retrieve bounded genuine MT5 bar evidence.
    _stage(1)
    bars = get_market_data(market_request("bars", timeframe="M1", limit=10))

    # Stage 2 — Select one approved tick and spread model.
    _stage(2)
    arguments = {
        "model": "trading_bar",
        "trading_timeframe": "M1",
        "spread_model": "fixed_spread",
        "fixed_spread_points": Decimal(2),
        "point_value": Decimal("0.00001"),
    }

    # Stage 3 — Generate canonical ordered ticks with intra-bar phase metadata.
    _stage(3)
    ticks = generate_tick_series(bars, **arguments)
    assert all(record.source_bar_time is not None for record in ticks.records)

    # Stage 4 — Stream the bounded result to a temporary Parquet artifact.
    _stage(4)
    approved_root = DataSettings().approved_storage_roots[0]
    approved_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="wf-data-016-",
        dir=approved_root,
    ) as directory:
        artifact = generate_tick_series_to_parquet(
            bars,
            path=Path(directory) / "ticks.parquet",
            max_output_rows_per_chunk=1000,
            **arguments,
        )
        assert Path(str(artifact["path"])).is_file()
        print("Tick evidence:", ticks.record_count, artifact["rows"])
    print("OUTPUT BOUNDARY — canonical tick MarketDataset and bounded Parquet artifact")


if __name__ == "__main__":
    main()
