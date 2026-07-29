"""WF-BRK-SEC: connect and authenticate a genuine MT5 demo session."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    connect_broker,
    disconnect_broker,
    get_broker_account_info,
    get_broker_adapter_contract_version,
    get_broker_adapter_schema_id,
    get_broker_connection_status,
    get_broker_feature_flags,
    get_broker_permissions,
    get_broker_value_field,
    is_broker_connected,
)
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
    adapter = create_real_adapter("mt5")
    try:
        # Stage 1 — Validate connection-only configuration.
        _stage(1)
        assert get_broker_adapter_contract_version(adapter) == "v1"
        assert get_broker_adapter_schema_id(adapter) == "brokers.adapter.v1"

        # Stage 2 — Establish transport and provider authentication.
        _stage(2)
        require_success("MT5 connect", await connect_broker(adapter))
        connected = require_success(
            "Verified connectivity", await is_broker_connected(adapter)
        )
        print("Connection Test: ", get_broker_value_field(connected, "status"))
        assert get_broker_value_field(connected, "data") is True

        # Stage 3 — Verify account and environment identity.
        _stage(3)
        account_res = require_success(
            "Account identity", await get_broker_account_info(adapter)
        )
        data = get_broker_value_field(account_res, "data")
        if data is not None:
            print("Account ID:", get_broker_value_field(data, "account_id"))
            print("Account Currency:", get_broker_value_field(data, "currency"))
        require_success("Permissions", await get_broker_permissions(adapter))

        # Stage 4 — Refresh capability and lifecycle evidence.
        _stage(4)
        require_success("Feature flags", await get_broker_feature_flags(adapter))
        status = require_success(
            "Connection status", await get_broker_connection_status(adapter)
        )
        status_data = get_broker_value_field(status, "data")
        assert status_data is not None
        assert get_broker_value_field(status_data, "transport_connected") is True
    finally:
        # Stage 5 — Disconnect and release every owned resource.
        _stage(5)
        require_success("MT5 disconnect", await disconnect_broker(adapter))
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
