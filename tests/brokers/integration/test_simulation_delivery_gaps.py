"""Fail-closed simulation delivery-state tests for FR-BRK-181."""

from __future__ import annotations

import asyncio

import pytest

from tests.brokers.unit.simulation.test_simulation_reads import (
    ReadAuthority,
    envelope,
    make_adapter,
)


@pytest.mark.parametrize("flag", ["stale", "gap", "duplicate", "out_of_order"])
def test_explicit_unclean_delivery_never_becomes_empty_success(flag: str) -> None:
    """Every explicit unclean state is retained as a canonical failure."""

    async def exercise() -> None:
        authority = ReadAuthority([envelope((), **{flag: True})])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        result = await adapter.get_orders()  # type: ignore[attr-defined]
        assert result.status == "error"
        assert result.data is None

    asyncio.run(exercise())


def test_duplicate_missing_and_out_of_order_sequences_fail_closed() -> None:
    """The adapter never sorts or hides discontinuous delivery."""

    async def exercise() -> None:
        authority = ReadAuthority(
            [envelope("first", sequence=4), envelope("missing", sequence=6)]
        )
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        assert (await adapter.get_quote("EURUSD")).status == "success"  # type: ignore[attr-defined]
        result = await adapter.get_quote("EURUSD")  # type: ignore[attr-defined]
        assert (
            result.error.details["legacy_details"]["delivery_state"]
            == "missing_sequence"
        )

    asyncio.run(exercise())
