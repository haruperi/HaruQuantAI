"""WF-DATA-009: discover genuine MT5 symbol and availability evidence."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_availability_request,
    build_symbol_list_request,
    build_symbol_metadata_request,
    get_data_availability,
    get_symbol_metadata,
    list_symbols,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime

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

    with tempfile.TemporaryDirectory(prefix="wf-data-009-") as directory:
        root = Path(directory)
        with isolated_runtime(root):
            # Stage 1 — Submit a bounded MT5 symbol-discovery query.
            _stage(1)
            req1 = build_symbol_list_request(
                source_id="mt5",
                query="EURUSD",
                limit=10,
                request_id=generate_id("req"),
            )
            symbols_resp = list_symbols(req1)
            symbols = unwrap_data_response(
                symbols_resp, operation="list_symbols", request_id=req1.request_id
            )

            # Stage 2 — Resolve exact EURUSD metadata with provenance.
            _stage(2)
            req2 = build_symbol_metadata_request(
                source_id="mt5",
                symbol="EURUSD",
                request_id=generate_id("req"),
            )
            metadata_resp = get_symbol_metadata(req2)
            metadata = unwrap_data_response(
                metadata_resp,
                operation="get_symbol_metadata",
                request_id=req2.request_id,
            )

            # Stage 3 — Probe bounded M1 availability and gaps.
            _stage(3)
            end = datetime.now(UTC)
            req3 = build_availability_request(
                source_id="mt5",
                symbol="EURUSD",
                data_kind="ohlcv",
                timeframe="M1",
                start=end - timedelta(hours=1),
                end=end,
                max_probe_records=100,
                request_id=generate_id("req"),
            )
            availability_resp = get_data_availability(req3)
            availability = unwrap_data_response(
                availability_resp,
                operation="get_data_availability",
                request_id=req3.request_id,
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
