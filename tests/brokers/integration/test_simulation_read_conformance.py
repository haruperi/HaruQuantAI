"""Simulation read capability and unsupported-surface conformance."""

from __future__ import annotations

import asyncio

from app.services.brokers import (
    get_broker_capability_catalogue,
    get_broker_capability_id,
    get_broker_id,
)

from tests.brokers.unit.simulation.test_simulation_reads import (
    ReadAuthority,
    envelope,
    make_adapter,
)


def test_read_manifest_and_unsupported_deal_surface_are_exact() -> None:
    """Admitted reads are available while deal/transaction reads stay unavailable."""

    async def exercise() -> None:
        catalogue = get_broker_capability_catalogue().data
        assert catalogue is not None
        by_id = {item.capability: item for item in catalogue[get_broker_id("sim")]}
        assert by_id[get_broker_capability_id("get_quote")].availability == "AVAILABLE"
        for name in ("list_deal_history", "get_deal", "list_account_transactions"):
            assert by_id[get_broker_capability_id(name)].availability == "UNAVAILABLE"
        adapter = make_adapter(ReadAuthority([envelope("unused")]))
        await adapter.connect()  # type: ignore[attr-defined]
        result = await adapter.get_deal("deal-1")  # type: ignore[attr-defined]
        assert result.error.code == "BROKER_CAPABILITY_UNSUPPORTED"

    asyncio.run(exercise())


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
