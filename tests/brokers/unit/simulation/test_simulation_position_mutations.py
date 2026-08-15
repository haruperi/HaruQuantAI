"""Simulation position mutation tests for FR-BRK-187 and 188."""

from __future__ import annotations

import asyncio
from decimal import Decimal

from app.services.brokers import (
    build_broker_position_close_request,
    build_broker_position_modification_request,
    build_broker_position_reduce_request,
    build_broker_value,
    build_simulation_mutation_envelope,
)

from tests.brokers.unit.simulation.test_simulation_order_mutations import (
    NOW,
    MutationAuthority,
    make_adapter,
    provider_result,
)


def test_modify_reduce_and_close_project_only_authority_values() -> None:
    """Position mutations delegate once and never calculate position state."""

    async def exercise() -> None:
        position = build_broker_value(
            "position",
            position_id="position-1",
            symbol="EURUSD",
            side="LONG",
            quantity=Decimal("1.00"),
            quantity_unit="lots",
            retrieved_at=NOW,
            state="OPEN",
            stop_loss=Decimal("1.20"),
        )

        def modified(request: object) -> object:
            return build_simulation_mutation_envelope(
                provider_result=provider_result(),
                request_echo=request,
                simulated_at=NOW,
                projected_position=position,
            )

        authority = MutationAuthority([modified, provider_result(), provider_result()])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        modify = build_broker_position_modification_request(
            "position-1", stop_loss="1.20"
        )
        reduce = build_broker_position_reduce_request(
            "position-1", "0.25", "lots", "reduce-key-1"
        )
        close = build_broker_position_close_request("position-1", "0.75", "lots")
        assert (await adapter.modify_position(modify)).data is position  # type: ignore[attr-defined]
        assert (await adapter.reduce_position(reduce)).data.filled_quantity == Decimal(  # type: ignore[attr-defined,union-attr]
            "1.25"
        )
        assert (await adapter.close_position(close)).data.outcome == "ACCEPTED"  # type: ignore[attr-defined,union-attr]
        assert [call[1] for call in authority.calls] == [modify, reduce, close]

    asyncio.run(exercise())


def test_modify_position_requires_authoritative_post_state() -> None:
    """An acknowledgement alone cannot invent the resulting position."""

    async def exercise() -> None:
        authority = MutationAuthority([provider_result()])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        request = build_broker_position_modification_request(
            "position-1", take_profit="1.30"
        )
        result = await adapter.modify_position(request)  # type: ignore[attr-defined]
        assert result.error.code == "BROKER_RESPONSE_INVALID"

    asyncio.run(exercise())
