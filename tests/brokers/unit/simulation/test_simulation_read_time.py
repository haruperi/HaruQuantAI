"""Simulation read time-safety tests for FR-BRK-175 and 177."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime

from tests.brokers.unit.simulation.test_simulation_reads import (
    NOW,
    ReadAuthority,
    envelope,
    make_adapter,
)


def test_future_and_reversed_availability_fail_closed() -> None:
    """No payload may become visible before its authoritative availability."""

    async def exercise() -> None:
        future = replace(envelope("quote"), available_at=NOW.replace(hour=13))
        authority = ReadAuthority([future])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        result = await adapter.get_quote("EURUSD")  # type: ignore[attr-defined]
        assert result.error.code == "BROKER_RESPONSE_INVALID"
        assert (
            result.error.details["legacy_details"]["delivery_state"]
            == "future_or_reversed_time"
        )

    asyncio.run(exercise())


def test_naive_authority_time_is_rejected() -> None:
    """Every authority timestamp must be aware UTC."""

    async def exercise() -> None:
        invalid = replace(envelope("quote"), observed_at=datetime(2024, 1, 2, 12))  # noqa: DTZ001
        authority = ReadAuthority([invalid])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        result = await adapter.get_quote("EURUSD")  # type: ignore[attr-defined]
        assert result.error.code == "BROKER_REQUEST_INVALID"

    asyncio.run(exercise())
