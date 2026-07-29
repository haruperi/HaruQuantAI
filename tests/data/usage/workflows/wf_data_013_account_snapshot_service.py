"""WF-DATA-013: normalize a genuine MT5 account snapshot."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_account_snapshot_request,
    get_account_state_snapshot,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.brokers.usage._support import create_real_adapter, require_success

WORKFLOW_ID = "WF-DATA-013"
STAGES = (
    "Connect a caller-owned genuine MT5 demo adapter.",
    "Read the exact provider account identity.",
    "Wrap the adapter in Data's read-only account boundary.",
    "Normalize balances, margin, positions, orders, connectivity, and freshness.",
    "Return AccountStateSnapshot and disconnect the caller-owned adapter.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute the real broker-to-Data account snapshot boundary."""
    print(f"{WORKFLOW_ID} — Account Snapshot Service")
    print("INPUT BOUNDARY — read-only account evidence request")
    adapter = create_real_adapter("mt5")
    try:
        # Stage 1 — Connect a caller-owned genuine MT5 demo adapter.
        _stage(1)
        require_success("MT5 connect", asyncio.run(adapter.connect()))

        # Stage 2 — Read the exact provider account identity.
        _stage(2)
        account_result = require_success(
            "MT5 account", asyncio.run(adapter.get_account_info())
        )
        assert account_result.data is not None

        # Stage 3 — Wrap the adapter in Data's read-only account boundary.
        _stage(3)
        request = build_account_snapshot_request(
            source_id="mt5",
            account_id=account_result.data.account_id,
            max_age_seconds=315360000,
            request_id=generate_id("req"),
        )

        # Stage 4 — Normalize balances, margin, positions, orders, connectivity, and freshness.
        _stage(4)
        snapshot_resp = get_account_state_snapshot(request, adapter)
        snapshot = unwrap_data_response(
            snapshot_resp,
            operation="get_account_state_snapshot",
            request_id=request.request_id,
        )

        # Stage 5 — Return AccountStateSnapshot and disconnect the caller-owned adapter.
        _stage(5)
        print(
            "Snapshot evidence:",
            snapshot.currency,
            len(snapshot.balances),
            len(snapshot.positions),
            snapshot.connected,
        )
    finally:
        require_success("MT5 disconnect", asyncio.run(adapter.disconnect()))
    print("OUTPUT BOUNDARY — immutable AccountStateSnapshot v1")


if __name__ == "__main__":
    main()
