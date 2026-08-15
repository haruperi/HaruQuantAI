"""Verified simulation mutation retcode mapping tests for FR-BRK-183 through 185."""

from __future__ import annotations

import asyncio

import pytest
from app.services.brokers import build_simulation_mutation_envelope

from tests.brokers.unit.simulation.test_simulation_order_mutations import (
    NOW,
    MutationAuthority,
    make_adapter,
    order_request,
    provider_result,
)


@pytest.mark.parametrize(
    ("retcode", "expected"),
    [
        (10008, "success"),
        (10009, "success"),
        (10010, "success"),
        (10025, "success"),
        (10019, "BROKER_INSUFFICIENT_MARGIN"),
        (10018, "BROKER_MARKET_CLOSED"),
        (10021, "BROKER_MARKET_CLOSED"),
        (10013, "BROKER_REQUEST_INVALID"),
        (10014, "BROKER_REQUEST_INVALID"),
        (10015, "BROKER_REQUEST_INVALID"),
        (10016, "BROKER_REQUEST_INVALID"),
        (10022, "BROKER_REQUEST_INVALID"),
        (10030, "BROKER_REQUEST_INVALID"),
        (10035, "BROKER_REQUEST_INVALID"),
        (10038, "BROKER_REQUEST_INVALID"),
        (10006, "BROKER_REQUEST_REJECTED"),
        (10007, "BROKER_REQUEST_REJECTED"),
        (10017, "BROKER_REQUEST_REJECTED"),
        (10031, "BROKER_REQUEST_REJECTED"),
        (10032, "BROKER_REQUEST_REJECTED"),
        (10033, "BROKER_REQUEST_REJECTED"),
        (10034, "BROKER_REQUEST_REJECTED"),
    ],
)
def test_each_verified_order_send_retcode_uses_live_mapping(
    retcode: int, expected: str
) -> None:
    """Each documented retcode retains the live MT5 classification."""

    async def exercise() -> None:
        adapter = make_adapter(MutationAuthority([provider_result(retcode)]))
        await adapter.connect()  # type: ignore[attr-defined]
        response = await adapter.place_order(order_request(f"retcode-{retcode}"))  # type: ignore[attr-defined]
        if expected == "success":
            assert response.status == "success"
        else:
            assert response.error.code == expected

    asyncio.run(exercise())


@pytest.mark.parametrize("payload", [{}, {"retcode": 99999}, {"retcode": True}])
def test_malformed_or_unverified_result_fails_closed(payload: object) -> None:
    """No unknown native condition is guessed into a canonical outcome."""

    async def exercise() -> None:
        authority = MutationAuthority([payload])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        response = await adapter.place_order(order_request("unverified-result"))  # type: ignore[attr-defined]
        assert response.error.code == "BROKER_RESPONSE_INVALID"

    asyncio.run(exercise())


def test_phase_20_fault_marker_is_not_yet_admitted() -> None:
    """Seeded ambiguity remains blocked until its owning phase."""

    async def exercise() -> None:
        def seeded(request: object) -> object:
            return build_simulation_mutation_envelope(
                provider_result=provider_result(),
                request_echo=request,
                simulated_at=NOW,
                seeded_fault=True,
            )

        adapter = make_adapter(MutationAuthority([seeded]))
        await adapter.connect()  # type: ignore[attr-defined]
        response = await adapter.place_order(order_request("seeded-fault"))  # type: ignore[attr-defined]
        assert response.error.code == "BROKER_RESPONSE_INVALID"

    asyncio.run(exercise())
