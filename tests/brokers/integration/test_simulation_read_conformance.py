"""Simulation read capability and unsupported-surface conformance."""

from __future__ import annotations

import asyncio

from tests.brokers.unit.simulation.test_simulation_reads import (
    ReadAuthority,
    envelope,
    make_adapter,
)


def test_session_read_requires_revision_bound_evidence() -> None:
    """Weekly-looking values cannot silently certify dated exceptions."""

    async def exercise() -> None:
        adapter = make_adapter(ReadAuthority([envelope(("weekly",))]))
        await adapter.connect()  # type: ignore[attr-defined]
        result = await adapter.get_trading_sessions("EURUSD")  # type: ignore[attr-defined]
        assert result.status == "error"
        assert result.error.details["legacy_details"]["delivery_state"] == (
            "exceptional_session_unproven"
        )

    asyncio.run(exercise())
