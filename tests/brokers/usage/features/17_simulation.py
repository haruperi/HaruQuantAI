"""Standalone usage evidence for FEAT-BRK-17 simulation channel."""

from __future__ import annotations

import asyncio
import sys
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    build_broker_connection_config,
    build_broker_order_modification_request,
    build_broker_position_close_request,
    build_broker_position_modification_request,
    build_broker_position_reduce_request,
    build_broker_value,
    build_simulation_mutation_envelope,
    build_simulation_read_envelope,
    create_configured_fake_broker_adapter,
    create_simulation_broker_adapter,
    finalize_simulation_broker_session,
    get_broker_capability_catalogue,
    get_broker_deal,
    get_broker_environment,
    get_broker_id,
    get_broker_value_field,
    list_broker_account_transactions,
    list_broker_deal_history,
)

import _support  # noqa: F401


class _UsageAuthority:
    """In-memory authority satisfying the Brokers-owned structural port."""

    def __init__(self, target: object) -> None:
        self._target = target
        self.read_count = 0
        self.mutation_count = 0
        self.mutation_retcode = 10009

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)

    async def ping(self) -> object:
        """Return a successful canonical local probe."""
        return await self._target.is_connected()  # type: ignore[attr-defined, no-any-return]

    async def finalize_session(self) -> object:
        """Finalize without any external side effect."""
        return await self._target.disconnect()  # type: ignore[attr-defined, no-any-return]

    async def read(self, operation: object, arguments: Mapping[str, object]) -> object:
        """Return exact canonical fixture values with simulated-time evidence."""
        self.read_count += 1
        name = str(operation)
        now = datetime(2024, 1, 2, 12, tzinfo=UTC)
        deal = build_broker_value(
            "deal",
            deal_id="deal-1",
            order_id="order-1",
            position_id="position-1",
            symbol="EURUSD",
            side="BUY",
            quantity=Decimal("1.00"),
            quantity_unit="lots",
            price=Decimal("1.2345"),
            partial=False,
            fee=Decimal("-0.50"),
            fee_currency="USD",
            provider_timestamp=now,
            retrieved_at=now,
            entry="DEAL_ENTRY_IN",
            reason="EXPERT",
        )
        transaction = build_broker_value(
            "account_transaction",
            transaction_id="transaction-1",
            transaction_type="COMMISSION",
            asset="ACCOUNT",
            currency="USD",
            amount=Decimal("-0.50"),
            provider_timestamp=now,
            retrieved_at=now,
            provider_metadata={"source_sequence": 1},
        )
        payloads: dict[str, object] = {
            "get_symbols": ("EURUSD",),
            "get_symbol_info": "EURUSD-specification-shape",
            "get_provider_specification": "revision-spec-7",
            "get_trading_sessions": ("weekly+dated-exception:revision-3",),
            "get_quote": Decimal("1.23456"),
            "get_account_info": {"equity": Decimal("1000.00")},
            "get_positions": ("position-1",),
            "get_orders": ("order-1",),
            "list_deal_history": build_broker_value(
                "page", items=(deal,), limit=arguments.get("limit", 10)
            ),
            "get_deal": deal if arguments.get("deal_id") == "deal-1" else None,
            "list_account_transactions": build_broker_value(
                "page", items=(transaction,), limit=arguments.get("limit", 10)
            ),
        }
        return build_simulation_read_envelope(
            payload=payloads[name],
            source_sequence=0,
            observed_at=now,
            received_at=now,
            available_at=now,
            simulated_at=now,
            session_revision="revision-3" if name == "get_trading_sessions" else None,
        )

    async def mutate(self, operation: object, request: object) -> object:
        """Return one exact request-bound provider-shaped mutation result."""
        self.mutation_count += 1
        now = datetime(2024, 1, 2, 12, tzinfo=UTC)
        retcode = 0 if str(operation) == "check_order" else self.mutation_retcode
        projected_position = None
        if str(operation) == "modify_position":
            projected_position = build_broker_value(
                "position",
                position_id="position-1",
                symbol="EURUSD",
                side="LONG",
                quantity=Decimal("1.00"),
                quantity_unit="lots",
                retrieved_at=now,
                state="OPEN",
                stop_loss=Decimal("1.20"),
            )
        return build_simulation_mutation_envelope(
            provider_result={
                "retcode": retcode,
                "order": 41,
                "deal": 42,
                "volume": "1.00",
                "price": "1.2345",
                "comment": "usage fixture",
                "margin": "12.50",
            },
            request_echo=request,
            simulated_at=now,
            projected_position=projected_position,
        )


def _values() -> tuple[object, object, object]:
    config = build_broker_connection_config("sim", "simulation")
    authority = _UsageAuthority(create_configured_fake_broker_adapter(config))
    adapter = create_simulation_broker_adapter(config, authority).data
    assert adapter is not None
    return config, authority, adapter


def fr_brk_167() -> None:
    """Demonstrate the exact simulation identity and environment."""
    assert str(get_broker_id("sim")) == "sim"
    assert str(get_broker_environment("simulation")) == "simulation"


def fr_brk_168() -> None:
    """Demonstrate exact factory construction."""
    assert _values()[2] is not None


def fr_brk_169() -> None:
    """Demonstrate the published capability intersection."""
    catalogue = get_broker_capability_catalogue().data
    assert catalogue is not None
    assert catalogue[get_broker_id("sim")]


async def fr_brk_170() -> None:
    """Demonstrate authority-backed lifecycle and finalization."""
    adapter = _values()[2]
    assert (await adapter.connect()).status == "success"  # type: ignore[attr-defined]
    assert (await adapter.ping()).status == "success"  # type: ignore[attr-defined]
    assert (await adapter.reconnect()).status == "success"  # type: ignore[attr-defined]
    assert (await finalize_simulation_broker_session(adapter)).status == "success"


def fr_brk_171() -> None:
    """Demonstrate credential- and endpoint-free isolation."""
    config = _values()[0]
    assert config.credentials is None  # type: ignore[attr-defined]
    assert config.endpoint is None  # type: ignore[attr-defined]


def fr_brk_172() -> None:
    """Demonstrate structural authority injection."""
    assert isinstance(_values()[1], _UsageAuthority)


async def _read_values() -> tuple[object, _UsageAuthority]:
    """Return one connected read adapter and its socket-free authority."""
    _, authority, adapter = _values()
    assert isinstance(authority, _UsageAuthority)
    assert (await adapter.connect()).status == "success"  # type: ignore[attr-defined]
    return adapter, authority


async def fr_brk_174() -> None:
    """Demonstrate structural authority read-port binding."""
    adapter, authority = await _read_values()
    assert (await adapter.get_quote("EURUSD")).data == Decimal("1.23456")  # type: ignore[attr-defined]
    assert authority.read_count == 1


def fr_brk_175() -> None:
    """Demonstrate injected simulated observation/availability timestamps."""
    now = datetime(2024, 1, 2, 12, tzinfo=UTC)
    assert build_simulation_read_envelope(
        payload="quote",
        source_sequence=0,
        observed_at=now,
        received_at=now,
        available_at=now,
        simulated_at=now,
    )


async def fr_brk_176() -> None:
    """Demonstrate canonical symbol and specification projection."""
    adapter, _ = await _read_values()
    assert (await adapter.get_symbols()).data == ("EURUSD",)  # type: ignore[attr-defined]
    assert (
        await adapter.get_provider_specification("EURUSD")
    ).data == "revision-spec-7"  # type: ignore[attr-defined]


async def fr_brk_177() -> None:
    """Demonstrate the no-future-read boundary with fixed authority time."""
    adapter, _ = await _read_values()
    result = await adapter.get_quote("EURUSD")  # type: ignore[attr-defined]
    assert (
        result.metadata.extensions["provider_metadata"]["available_at"]
        == "2024-01-02T12:00:00+00:00"
    )


async def fr_brk_178() -> None:
    """Demonstrate exact account-ledger projection."""
    adapter, _ = await _read_values()
    assert (await adapter.get_account_info()).data["equity"] == Decimal("1000.00")  # type: ignore[attr-defined,index]


async def fr_brk_179() -> None:
    """Demonstrate exact position and order projection."""
    adapter, _ = await _read_values()
    assert (await adapter.get_positions()).data == ("position-1",)  # type: ignore[attr-defined]
    assert (await adapter.get_orders()).data == ("order-1",)  # type: ignore[attr-defined]


async def fr_brk_180() -> None:
    """Demonstrate revision-bound sessions."""
    adapter, _ = await _read_values()
    assert (await adapter.get_trading_sessions("EURUSD")).status == "success"  # type: ignore[attr-defined]


async def fr_brk_181() -> None:
    """Demonstrate read isolation and explicit delivery evidence."""
    adapter, authority = await _read_values()
    response = await adapter.get_quote("EURUSD")  # type: ignore[attr-defined]
    evidence = response.metadata.extensions["provider_metadata"]
    assert evidence["source_sequence"] == 0
    assert evidence["gap"] is False
    assert authority.read_count == 1


def _order_request() -> object:
    """Return one immutable simulation order request."""
    return build_broker_value(
        "order_request",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("1.00"),
        quantity_unit="lots",
        environment=get_broker_environment("simulation"),
        client_request_id=f"req-{uuid.uuid4()}",
    )


async def _mutation_values() -> tuple[object, _UsageAuthority]:
    """Return one connected mutation adapter and authority."""
    _, authority, adapter = _values()
    assert isinstance(authority, _UsageAuthority)
    assert (await adapter.connect()).status == "success"  # type: ignore[attr-defined]
    return adapter, authority


async def fr_brk_182() -> None:
    """Demonstrate the exact simulation route and request echo guard."""
    adapter, authority = await _mutation_values()
    request = _order_request()
    assert (await adapter.place_order(request)).status == "success"  # type: ignore[attr-defined]
    assert authority.mutation_count == 1


def fr_brk_183() -> None:
    """Demonstrate the provider-shaped mutation envelope boundary."""
    now = datetime(2024, 1, 2, 12, tzinfo=UTC)
    assert build_simulation_mutation_envelope(
        provider_result={"retcode": 10009},
        request_echo=_order_request(),
        simulated_at=now,
    )


async def fr_brk_184() -> None:
    """Demonstrate verified provider rejection classification."""
    adapter, authority = await _mutation_values()
    authority.mutation_retcode = 10006
    result = await adapter.place_order(_order_request())  # type: ignore[attr-defined]
    assert result.status == "error"
    assert result.error.code == "BROKER_REQUEST_REJECTED"


async def fr_brk_185() -> None:
    """Demonstrate deterministic acknowledgement without spontaneous ambiguity."""
    adapter, _ = await _mutation_values()
    result = await adapter.place_order(_order_request())  # type: ignore[attr-defined]
    assert result.data.outcome == "ACCEPTED"


async def fr_brk_186() -> None:
    """Demonstrate all admitted order mutations."""
    adapter, authority = await _mutation_values()
    assert (await adapter.check_order(_order_request())).status == "success"  # type: ignore[attr-defined]
    assert (await adapter.place_order(_order_request())).status == "success"  # type: ignore[attr-defined]
    modify = build_broker_order_modification_request("41", quantity="0.75")
    assert (await adapter.modify_order(modify)).status == "success"  # type: ignore[attr-defined]
    assert (await adapter.cancel_order("41", "cancel-usage-1")).status == "success"  # type: ignore[attr-defined]
    assert authority.mutation_count == 4


async def fr_brk_187() -> None:
    """Demonstrate all admitted position mutations."""
    adapter, authority = await _mutation_values()
    modify = build_broker_position_modification_request("position-1", stop_loss="1.20")
    reduce = build_broker_position_reduce_request(
        "position-1", "0.25", "lots", "reduce-usage-1"
    )
    close = build_broker_position_close_request("position-1", "0.75", "lots")
    assert (await adapter.modify_position(modify)).status == "success"  # type: ignore[attr-defined]
    assert (await adapter.reduce_position(reduce)).status == "success"  # type: ignore[attr-defined]
    assert (await adapter.close_position(close)).status == "success"  # type: ignore[attr-defined]
    assert authority.mutation_count == 3


async def fr_brk_188() -> None:
    """Demonstrate that the adapter delegates one mutation without accounting."""
    adapter, authority = await _mutation_values()
    await adapter.place_order(_order_request())  # type: ignore[attr-defined]
    assert authority.mutation_count == 1
    assert authority.read_count == 0


async def fr_brk_189() -> None:
    """Demonstrate exact v2 fill/time-policy fidelity."""
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
    adapter, _ = await _mutation_values()
    assert (await adapter.place_order(request)).status == "success"  # type: ignore[attr-defined]
    assert get_broker_value_field(request, "fill_policy") == "RETURN"
    assert get_broker_value_field(request, "time_policy") == "GTC"


async def fr_brk_194() -> None:
    """FR-BRK-194: Read bounded provider-shaped Simulation deal history."""
    adapter, _ = await _read_values()
    result = await list_broker_deal_history(
        adapter,
        datetime(2024, 1, 2, 11, tzinfo=UTC),
        datetime(2024, 1, 2, 13, tzinfo=UTC),
        limit=10,
    )
    items = get_broker_value_field(result.data, "items")
    assert get_broker_value_field(items[0], "order_id") == "order-1"


async def fr_brk_195() -> None:
    """FR-BRK-195: Read one exact Simulation authority deal."""
    adapter, _ = await _read_values()
    result = await get_broker_deal(adapter, "deal-1")
    assert get_broker_value_field(result.data, "position_id") == "position-1"


async def fr_brk_196() -> None:
    """FR-BRK-196: Read bounded signed account transactions."""
    adapter, _ = await _read_values()
    result = await list_broker_account_transactions(
        adapter,
        datetime(2024, 1, 2, 11, tzinfo=UTC),
        datetime(2024, 1, 2, 13, tzinfo=UTC),
        limit=10,
    )
    items = get_broker_value_field(result.data, "items")
    assert get_broker_value_field(items[0], "amount") == Decimal("-0.50")


async def _run() -> None:
    fr_brk_167()
    fr_brk_168()
    fr_brk_169()
    await fr_brk_170()
    fr_brk_171()
    fr_brk_172()
    await fr_brk_174()
    fr_brk_175()
    await fr_brk_176()
    await fr_brk_177()
    await fr_brk_178()
    await fr_brk_179()
    await fr_brk_180()
    await fr_brk_181()
    await fr_brk_182()
    fr_brk_183()
    await fr_brk_184()
    await fr_brk_185()
    await fr_brk_186()
    await fr_brk_187()
    await fr_brk_188()
    await fr_brk_189()
    await fr_brk_194()
    await fr_brk_195()
    await fr_brk_196()


def main() -> None:
    """Execute all requirement evidence."""
    asyncio.run(_run())
    print("FEAT-BRK-17 simulation usage: SUCCESS")


if __name__ == "__main__":
    main()
