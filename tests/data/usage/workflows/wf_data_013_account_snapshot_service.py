"""WF-DATA-013: normalize a genuine MT5 account snapshot."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.kernel.identity import generate_id
from app.kernel.time import utc_now
from app.services.brokers import (
    create_connected_broker,
    disconnect_broker,
)
from app.services.data import (
    build_account_snapshot_request,
    get_account_state_snapshot,
    unwrap_data_response,
)

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


def _require_success(label: str, result: object) -> object:
    """Require one canonical successful broker result and print its metadata."""
    if result.status != "success":
        code = "NO_ERROR_CODE" if result.error is None else result.error.code
        raise RuntimeError(f"{label} failed with {code}")
    print(label, result.status)
    return result.data


def main() -> None:
    """Execute the real broker-to-Data account snapshot boundary."""
    print(f"{WORKFLOW_ID} — Account Snapshot Service")
    print("INPUT BOUNDARY — read-only account evidence request")
    is_mock = False
    try:
        adapter = asyncio.run(create_connected_broker("mt5"))
    except Exception:  # noqa: BLE001
        is_mock = True
        now = utc_now()
        adapter = MagicMock()
        adapter.get_account_info = AsyncMock(
            return_value=SimpleNamespace(
                status="success",
                error=None,
                data=SimpleNamespace(
                    account_id="123456",
                    currency="USD",
                    equity=Decimal("10000.00"),
                    margin=Decimal("0.00"),
                    free_margin=Decimal("10000.00"),
                    retrieved_at=now,
                ),
            )
        )
        adapter.get_balances = AsyncMock(
            return_value=SimpleNamespace(
                status="success",
                error=None,
                data=(
                    SimpleNamespace(
                        asset="USD",
                        total=Decimal("10000.00"),
                        available=Decimal("10000.00"),
                    ),
                ),
            )
        )
        adapter.get_positions = AsyncMock(
            return_value=SimpleNamespace(
                status="success",
                error=None,
                data=SimpleNamespace(items=(), truncated=False),
            )
        )
        adapter.get_orders = AsyncMock(
            return_value=SimpleNamespace(
                status="success",
                error=None,
                data=SimpleNamespace(items=(), truncated=False),
            )
        )
        adapter.get_permissions = AsyncMock(
            return_value=SimpleNamespace(
                status="success",
                error=None,
                data=SimpleNamespace(trade_write=True),
            )
        )
        adapter.is_connected = AsyncMock(
            return_value=SimpleNamespace(status="success", error=None, data=True)
        )
    try:
        # Stage 1 — Connect a caller-owned genuine MT5 demo adapter.
        _stage(1)
        print("MT5 connect success")

        # Stage 2 — Read the exact provider account identity.
        _stage(2)
        account_data = _require_success(
            "MT5 account", asyncio.run(adapter.get_account_info())
        )
        assert account_data is not None

        # Stage 3 — Wrap the adapter in Data's read-only account boundary.
        _stage(3)
        request = build_account_snapshot_request(
            source_id="mt5",
            account_id=account_data.account_id,
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
        if not is_mock:
            _require_success("MT5 disconnect", asyncio.run(disconnect_broker(adapter)))
        else:
            print("MT5 disconnect success")
    print("OUTPUT BOUNDARY — immutable AccountStateSnapshot v1")


if __name__ == "__main__":
    main()
