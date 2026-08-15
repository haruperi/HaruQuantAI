"""Unit evidence for bounded Simulation deal reads."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers.canonical_contracts import BrokerDeal, BrokerPage

from tests.brokers.unit.simulation.test_simulation_reads import (
    ReadAuthority,
    envelope,
    make_adapter,
)

NOW = datetime(2026, 8, 17, 10, tzinfo=UTC)


def deal(identity: str = "deal-1", *, at: datetime = NOW) -> BrokerDeal:
    """Return one referentially complete authority deal."""
    return BrokerDeal(
        deal_id=identity,
        order_id="order-1",
        position_id="position-1",
        symbol="EURUSD",
        side="BUY",
        quantity=Decimal(1),
        quantity_unit="lots",
        price=Decimal("1.1"),
        partial=False,
        fee=Decimal(-1),
        fee_currency="USD",
        provider_timestamp=at,
        retrieved_at=at,
        entry="DEAL_ENTRY_IN",
        reason="EXPERT",
    )


def test_bounded_history_and_exact_deal_preserve_authority_evidence() -> None:
    """Half-open range, linkage, pagination, and exact lookup are unchanged."""

    async def exercise() -> None:
        page = BrokerPage(items=(deal(),), limit=10)
        authority = ReadAuthority([envelope(page), envelope(deal())])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        history = await adapter.list_deal_history(  # type: ignore[attr-defined]
            NOW - timedelta(seconds=1),
            NOW + timedelta(seconds=1),
            symbol="EURUSD",
            limit=10,
        )
        assert history.data == page
        exact = await adapter.get_deal("deal-1")  # type: ignore[attr-defined]
        assert exact.data == deal()
        assert exact.data.entry == "DEAL_ENTRY_IN"
        assert exact.data.reason == "EXPERT"

    asyncio.run(exercise())


def test_unknown_or_unbounded_deal_read_fails_closed() -> None:
    """Unknown identity and omitted bounds never become invented history."""

    async def exercise() -> None:
        authority = ReadAuthority([envelope(None)])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        missing = await adapter.get_deal("missing")  # type: ignore[attr-defined]
        assert missing.error.code == "BROKER_DEAL_NOT_FOUND"
        unbounded = await adapter.list_deal_history(limit=10)  # type: ignore[attr-defined]
        assert unbounded.error.code == "BROKER_RESPONSE_INVALID"

    asyncio.run(exercise())
