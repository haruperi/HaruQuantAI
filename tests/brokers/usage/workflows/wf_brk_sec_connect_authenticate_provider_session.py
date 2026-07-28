"""WF-BRK-SEC: connect and authenticate a genuine MT5 demo session."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import BrokerId
from tests.brokers.usage._support import create_real_adapter, require_success

WORKFLOW_ID = "WF-BRK-SEC"
STAGES = (
    "Validate connection-only configuration.",
    "Establish transport and provider authentication.",
    "Verify account and environment identity.",
    "Refresh capability and lifecycle evidence.",
    "Disconnect and release every owned resource.",
)


async def run() -> None:
    """Execute the complete MT5 lifecycle."""
    print(f"{WORKFLOW_ID} — Connect and Authenticate Provider Session")
    print("INPUT BOUNDARY — caller-owned MT5 adapter with immutable demo config")
    adapter = create_real_adapter(BrokerId.MT5)
    try:
        # Stage 1 — Validate connection-only configuration.
        _stage(1)
        assert adapter.contract_version == "v1"
        assert adapter.schema_id == "brokers.adapter.v1"

        # Stage 2 — Establish transport and provider authentication.
        _stage(2)
        require_success("MT5 connect", await adapter.connect())
        connected = require_success(
            "Verified connectivity", await adapter.is_connected()
        )
        print("Connection Test: ", connected.status)
        assert connected.data is True

        # Stage 3 — Verify account and environment identity.
        _stage(3)
        account_res = require_success(
            "Account identity", await adapter.get_account_info()
        )
        if account_res.data is not None:
            print("Account ID:", account_res.data.account_id)
            print("Account Currency:", account_res.data.currency)
        require_success("Permissions", await adapter.get_permissions())

        # Stage 4 — Refresh capability and lifecycle evidence.
        _stage(4)
        require_success("Feature flags", await adapter.get_feature_flags())
        status = require_success(
            "Connection status", await adapter.get_connection_status()
        )
        assert status.data is not None
        assert status.data.transport_connected
    finally:
        # Stage 5 — Disconnect and release every owned resource.
        _stage(5)
        require_success("MT5 disconnect", await adapter.disconnect())
    print("OUTPUT BOUNDARY — verified session evidence and deterministic disconnect")


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
