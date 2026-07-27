"""WF-DATA-009: discover genuine MT5 symbol and availability evidence."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    AvailabilityRequest,
    SymbolListRequest,
    SymbolMetadataRequest,
    get_data_availability,
    get_symbol_metadata,
    list_symbols,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-009"
STAGES = (
    "Submit a bounded MT5 symbol-discovery query.",
    "Resolve exact EURUSD metadata with provenance.",
    "Probe bounded M1 availability and gaps.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute discovery, metadata, and availability."""
    print(f"{WORKFLOW_ID} — Symbol Discovery, Metadata, Availability")
    print("INPUT BOUNDARY — bounded MT5 symbol and range queries")

    # Stage 1 — Submit a bounded MT5 symbol-discovery query.
    _stage(1)
    symbols = list_symbols(
        SymbolListRequest(
            source_id="mt5",
            query="EURUSD",
            limit=10,
            request_id=generate_id("req"),
        )
    )

    # Stage 2 — Resolve exact EURUSD metadata with provenance.
    _stage(2)
    metadata = get_symbol_metadata(
        SymbolMetadataRequest(
            source_id="mt5",
            symbol="EURUSD",
            request_id=generate_id("req"),
        )
    )

    # Stage 3 — Probe bounded M1 availability and gaps.
    _stage(3)
    end = datetime.now(UTC)
    availability = get_data_availability(
        AvailabilityRequest(
            source_id="mt5",
            symbol="EURUSD",
            data_kind="ohlcv",
            timeframe="M1",
            start=end - timedelta(hours=1),
            end=end,
            max_probe_records=100,
            request_id=generate_id("req"),
        )
    )
    print(
        "Discovery evidence:",
        len(symbols.items),
        metadata.canonical_symbol,
        availability.record_count,
    )
    print("OUTPUT BOUNDARY — SymbolPage, SymbolMetadata, and DataAvailability")


if __name__ == "__main__":
    main()
