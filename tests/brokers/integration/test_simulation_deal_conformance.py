"""Capability and fail-closed conformance for Simulation deal reads."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from app.services.brokers import (
    build_broker_value,
)

from tests.brokers.unit.simulation.test_simulation_deals import NOW, deal
from tests.brokers.unit.simulation.test_simulation_reads import (
    ReadAuthority,
    envelope,
    make_adapter,
)


def test_deal_capabilities_match_adapter_and_reject_delivery_gaps() -> None:
    """Stale/gapped authority evidence is rejected."""

    async def exercise() -> None:
        page = build_broker_value("page", items=(deal(),), limit=10)
        adapter = make_adapter(ReadAuthority([envelope(page, gap=True)]))
        disconnected = await adapter.list_deal_history(  # type: ignore[attr-defined]
            NOW - timedelta(seconds=1), NOW + timedelta(seconds=1), limit=10
        )
        assert disconnected.error.code == "BROKER_NOT_CONNECTED"
        await adapter.connect()  # type: ignore[attr-defined]
        gapped = await adapter.list_deal_history(  # type: ignore[attr-defined]
            NOW - timedelta(seconds=1), NOW + timedelta(seconds=1), limit=10
        )
        assert gapped.error.code == "BROKER_RESPONSE_INVALID"

    asyncio.run(exercise())
