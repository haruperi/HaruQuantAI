"""Canonical simulation read intersection tests for FR-BRK-174 through 179."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.services.brokers import (
    build_broker_connection_config,
    create_configured_fake_broker_adapter,
    create_simulation_broker_adapter,
    get_broker_capability_id,
)
from app.services.brokers.simulation.contracts import SimulationReadEnvelope

NOW = datetime(2024, 1, 2, 12, tzinfo=UTC)


class ReadAuthority:
    """Deterministic authority fixture with exact read envelopes."""

    def __init__(self, envelopes: list[SimulationReadEnvelope]) -> None:
        config = build_broker_connection_config("sim", "simulation")
        self._target = create_configured_fake_broker_adapter(config)
        self.envelopes = envelopes
        self.calls: list[tuple[object, Mapping[str, object]]] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)

    async def ping(self) -> object:
        """Return a canonical local probe."""
        return await self._target.is_connected()

    async def finalize_session(self) -> object:
        """Finalize the fake session."""
        return await self._target.disconnect()

    async def read(
        self, operation: object, arguments: Mapping[str, object]
    ) -> SimulationReadEnvelope:
        """Return the next exact authority envelope."""
        self.calls.append((operation, arguments))
        return self.envelopes.pop(0)


def envelope(
    payload: object, sequence: int = 0, **flags: bool
) -> SimulationReadEnvelope:
    """Build one deterministic authoritative read envelope."""
    return SimulationReadEnvelope(
        payload=payload,
        source_sequence=sequence,
        observed_at=NOW,
        received_at=NOW,
        available_at=NOW,
        simulated_at=NOW,
        **flags,
    )


def make_adapter(authority: ReadAuthority) -> object:
    """Build the public simulation adapter around one authority."""
    config = build_broker_connection_config("sim", "simulation")
    response = create_simulation_broker_adapter(config, authority)
    assert response.data is not None
    return response.data


def test_every_admitted_read_projects_exact_authority_value() -> None:
    """All admitted reads return ledger values without recomputation."""

    async def exercise() -> None:
        payloads: list[object] = [
            "symbols",
            "symbol",
            "specification",
            "sessions",
            Decimal("1.23456789"),
            Decimal("0.00020"),
            "ticks",
            "bars",
            "permissions",
            "account",
            (Decimal("913.27"),),
            "positions",
            "position",
            "orders",
            "order",
            "history",
        ]
        envelopes = [envelope(value) for value in payloads]
        envelopes[3] = replace(envelopes[3], session_revision="revision-3")
        authority = ReadAuthority(envelopes)
        adapter = make_adapter(authority)
        assert (await adapter.connect()).status == "success"  # type: ignore[attr-defined]
        calls = (
            ("get_symbols", ()),
            ("get_symbol_info", ("EURUSD",)),
            ("get_provider_specification", ("EURUSD",)),
            ("get_trading_sessions", ("EURUSD",)),
            ("get_quote", ("EURUSD",)),
            ("get_spread", ("EURUSD",)),
            ("get_ticks", ("EURUSD",)),
            ("get_historical_bars", ("EURUSD", "M1")),
            ("get_permissions", ()),
            ("get_account_info", ()),
            ("get_balances", ()),
            ("get_positions", ()),
            ("get_position", ("position-1",)),
            ("get_orders", ()),
            ("get_order", ("order-1",)),
            ("list_order_history", ()),
        )
        for expected, (name, args) in zip(payloads, calls, strict=True):
            result = await getattr(adapter, name)(*args)
            assert result.status == "success"
            assert result.data == expected
        assert [call[0] for call in authority.calls] == [
            get_broker_capability_id(name) for name, _ in calls
        ]

    asyncio.run(exercise())


def test_disconnected_read_never_reaches_authority() -> None:
    """Session-required reads fail closed without authority side effects."""

    async def exercise() -> None:
        authority = ReadAuthority([envelope("unused")])
        result = await make_adapter(authority).get_quote("EURUSD")  # type: ignore[attr-defined]
        assert result.error.code == "BROKER_NOT_CONNECTED"
        assert authority.calls == []

    asyncio.run(exercise())
