"""Simulation order mutation tests for FR-BRK-182 through 186 and 189."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.services.brokers import (
    build_broker_connection_config,
    build_broker_order_modification_request,
    build_broker_value,
    build_simulation_mutation_envelope,
    create_configured_fake_broker_adapter,
    create_simulation_broker_adapter,
    get_broker_environment,
    get_broker_value_field,
)
from app.services.brokers.canonical_contracts import BrokerOrderRequest

NOW = datetime(2024, 1, 2, 12, tzinfo=UTC)


def provider_result(retcode: int = 10009) -> Mapping[str, object]:
    """Return one bounded MT5 OrderSendResult-shaped fixture."""
    return {
        "retcode": retcode,
        "order": 41,
        "deal": 42,
        "volume": "1.25",
        "price": "1.2345",
        "comment": "fixture",
    }


class MutationAuthority:
    """Deterministic in-process mutation authority."""

    def __init__(self, results: list[object]) -> None:
        config = build_broker_connection_config("sim", "simulation")
        self._target = create_configured_fake_broker_adapter(config)
        self.results = results
        self.calls: list[tuple[object, object]] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)

    async def ping(self) -> object:
        """Return a canonical local probe."""
        return await self._target.is_connected()

    async def finalize_session(self) -> object:
        """Finalize the fake session."""
        return await self._target.disconnect()

    async def mutate(self, operation: object, request: object) -> object:
        """Return the next request-bound provider-shaped result."""
        self.calls.append((operation, request))
        result = self.results.pop(0)
        if isinstance(result, BaseException):
            raise result
        if callable(result):
            return result(request)
        return build_simulation_mutation_envelope(
            provider_result=result,
            request_echo=request,
            simulated_at=NOW,
        )


def make_adapter(authority: MutationAuthority) -> object:
    """Build one public simulation adapter."""
    config = build_broker_connection_config("sim", "simulation")
    response = create_simulation_broker_adapter(config, authority)
    assert response.data is not None
    return response.data


def order_request(client_request_id: str = "req-order-1") -> object:
    """Build one exact immutable simulation order request."""
    del client_request_id
    request_id = f"req-{uuid.uuid4()}"
    return BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("1.25"),
        quantity_unit="lots",
        environment=get_broker_environment("simulation"),
        client_request_id=request_id,
    )


def test_check_place_modify_and_cancel_delegate_exactly_once() -> None:
    """Every admitted order mutation preserves its exact immutable request."""

    async def exercise() -> None:
        authority = MutationAuthority(
            [
                {"retcode": 0, "comment": "ok", "margin": "12.50"},
                provider_result(),
                provider_result(),
                provider_result(),
            ]
        )
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        check = order_request("req-check-1")
        place = order_request("req-place-1")
        modify = build_broker_order_modification_request("41", quantity="1.00")
        assert (await adapter.check_order(check)).data.accepted_for_submission  # type: ignore[attr-defined,union-attr]
        assert (await adapter.place_order(place)).data.outcome == "ACCEPTED"  # type: ignore[attr-defined,union-attr]
        assert (await adapter.modify_order(modify)).data.outcome == "ACCEPTED"  # type: ignore[attr-defined,union-attr]
        assert (
            await adapter.cancel_order("41", "req-cancel-1")
        ).data.outcome == "ACCEPTED"  # type: ignore[attr-defined,union-attr]
        assert len(authority.calls) == 4
        assert authority.calls[0][1] is check
        assert authority.calls[1][1] is place
        assert authority.calls[2][1] is modify
        assert authority.calls[3][1] == ("41", "req-cancel-1")

    asyncio.run(exercise())


def test_tamper_duplicate_disconnect_and_timeout_fail_before_ambiguity() -> None:
    """Route/request guards reject mutation ambiguity deterministically."""

    async def exercise() -> None:
        def tampered(_request: object) -> object:
            return build_simulation_mutation_envelope(
                provider_result=provider_result(),
                request_echo=order_request("different-request"),
                simulated_at=NOW,
            )

        authority = MutationAuthority([provider_result(), tampered, TimeoutError()])
        adapter = make_adapter(authority)
        disconnected = await adapter.place_order(order_request("req-offline"))  # type: ignore[attr-defined]
        assert disconnected.error.code == "BROKER_NOT_CONNECTED"
        await adapter.connect()  # type: ignore[attr-defined]
        first = order_request("req-duplicate")
        assert (await adapter.place_order(first)).status == "success"  # type: ignore[attr-defined]
        duplicate = await adapter.place_order(first)  # type: ignore[attr-defined]
        assert duplicate.error.code == "BROKER_REQUEST_REJECTED"
        tamper = await adapter.place_order(order_request("req-tamper"))  # type: ignore[attr-defined]
        assert tamper.error.code == "BROKER_REQUEST_INVALID"
        timeout = await adapter.place_order(order_request("req-timeout"))  # type: ignore[attr-defined]
        assert timeout.error.code == "BROKER_RESPONSE_INVALID"
        assert len(authority.calls) == 3

    asyncio.run(exercise())


def test_order_target_environment_must_match_simulation_route() -> None:
    """An order cannot cross a non-simulation environment boundary."""

    async def exercise() -> None:
        request = BrokerOrderRequest(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal("1.00"),
            quantity_unit="lots",
            environment=get_broker_environment("demo"),
        )
        authority = MutationAuthority([provider_result()])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        response = await adapter.place_order(request)  # type: ignore[attr-defined]
        assert response.error.code == "BROKER_REQUEST_INVALID"
        assert authority.calls == []

    asyncio.run(exercise())


def test_v2_fill_and_time_policies_cross_the_port_unchanged() -> None:
    """Independent v2 policies and revision identity are never inferred."""

    async def exercise() -> None:
        request = build_broker_value(
            "order_request_v2",
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal("0.75"),
            quantity_unit="lots",
            environment=get_broker_environment("simulation"),
            fill_policy="RETURN",
            time_policy="GTC",
            provider_specification_checksum="a" * 64,
        )
        authority = MutationAuthority([provider_result()])
        adapter = make_adapter(authority)
        await adapter.connect()  # type: ignore[attr-defined]
        assert (await adapter.place_order(request)).status == "success"  # type: ignore[attr-defined]
        echoed = authority.calls[0][1]
        assert echoed is request
        assert get_broker_value_field(echoed, "fill_policy") == "RETURN"
        assert get_broker_value_field(echoed, "time_policy") == "GTC"
        assert (
            get_broker_value_field(echoed, "provider_specification_checksum")
            == "a" * 64
        )

    asyncio.run(exercise())
