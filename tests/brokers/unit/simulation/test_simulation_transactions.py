"""Unit evidence for bounded Simulation account-transaction reads."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers.canonical_contracts import (
    BrokerAccountTransaction,
    BrokerPage,
)

from tests.brokers.unit.simulation.test_simulation_reads import (
    ReadAuthority,
    envelope,
    make_adapter,
)

NOW = datetime(2026, 8, 17, 10, tzinfo=UTC)


def transaction(identity: str, kind: str, amount: Decimal) -> BrokerAccountTransaction:
    """Return one signed authority transaction."""
    return BrokerAccountTransaction(
        transaction_id=identity,
        transaction_type=kind,
        asset="ACCOUNT",
        currency="USD",
        amount=amount,
        provider_timestamp=NOW,
        retrieved_at=NOW,
        provider_metadata={"source_sequence": 1},
    )


def test_transaction_history_preserves_every_authority_sign() -> None:
    """Commission and deposit signs pass through without recomputation."""

    async def exercise() -> None:
        items = (
            transaction("transaction-1", "COMMISSION", Decimal(-1)),
            transaction("transaction-2", "DEPOSIT", Decimal(100)),
        )
        page = BrokerPage(items=items, limit=10)
        adapter = make_adapter(ReadAuthority([envelope(page)]))
        await adapter.connect()  # type: ignore[attr-defined]
        result = await adapter.list_account_transactions(  # type: ignore[attr-defined]
            NOW - timedelta(seconds=1), NOW + timedelta(seconds=1), limit=10
        )
        assert result.data == page
        assert tuple(item.amount for item in result.data.items) == (
            Decimal(-1),
            Decimal(100),
        )

    asyncio.run(exercise())
