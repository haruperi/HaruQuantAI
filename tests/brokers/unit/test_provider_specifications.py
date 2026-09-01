"""Unit tests for MetaTrader provider specification snapshots (provider truth)."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import NamedTuple

import pytest
from app.services.brokers import (
    build_provider_specification_snapshot,
    dump_provider_specification_snapshot,
    get_provider_specification_snapshot_field,
    parse_provider_specification_snapshot,
    verify_provider_specification_snapshot,
)

_SHA256_LENGTH = 64


class _SI(NamedTuple):
    name: object
    digits: object
    point: object
    filling_mode: object
    order_mode: object
    expiration_mode: object
    order_gtc_mode: object
    trade_exemode: object
    trade_mode: object
    trade_calc_mode: object
    swap_mode: object
    swap_rollover3days: object
    trade_stops_level: object
    trade_freeze_level: object
    volume_min: object
    volume_max: object
    volume_step: object
    volume_limit: object
    trade_tick_size: object
    trade_tick_value: object
    trade_tick_value_profit: object
    trade_tick_value_loss: object
    trade_contract_size: object
    currency_base: object
    currency_profit: object
    currency_margin: object
    margin_initial: object
    margin_maintenance: object
    margin_hedged: object
    margin_hedged_use_leg: object
    swap_long: object
    swap_short: object


class _AI(NamedTuple):
    login: object
    margin_mode: object


def _symbol_info() -> _SI:
    return _SI(
        name="EURUSD",
        digits=5,
        point=0.00001,
        filling_mode=1,
        order_mode=127,
        expiration_mode=7,
        order_gtc_mode=0,
        trade_exemode=2,
        trade_mode=4,
        trade_calc_mode=0,
        swap_mode=1,
        swap_rollover3days=3,
        trade_stops_level=0,
        trade_freeze_level=0,
        volume_min=0.01,
        volume_max=500.0,
        volume_step=0.01,
        volume_limit=0.0,
        trade_tick_size=0.00001,
        trade_tick_value=1.0,
        trade_tick_value_profit=1.0,
        trade_tick_value_loss=1.0,
        trade_contract_size=100000.0,
        currency_base="EUR",
        currency_profit="USD",
        currency_margin="USD",
        margin_initial=0.0,
        margin_maintenance=0.0,
        margin_hedged=100000.0,
        margin_hedged_use_leg=False,
        swap_long=-0.2,
        swap_short=-1.2,
    )


def _build(**overrides: object) -> object:
    kwargs: dict[str, object] = {
        "symbol_info": _symbol_info(),
        "broker": "mt5",
        "server": "DemoServer",
        "account_id": "123456",
        "environment": "demo",
        "terminal_build": "4410",
        "source_revision": "mt5:4410",
        "observed_at": datetime(2026, 8, 20, 12, 0, 0, tzinfo=UTC),
        "account_info": _AI(123456, 2),
    }
    kwargs.update(overrides)
    return build_provider_specification_snapshot(**kwargs)


def test_fr_brokers_159_builds_typed_current_snapshot() -> None:
    """FR-BRK-159: the typed snapshot covers every admitted mode block."""
    dumped = dump_provider_specification_snapshot(_build())
    assert dumped["provider_symbol"] == "EURUSD"
    assert dumped["filling_modes"] == ["FOK"]
    assert len(dumped["order_types"]) == 7
    assert dumped["expiration_modes"] == ["DAY", "GTC", "SPECIFIED"]
    assert dumped["gtc_mode"] == "GTC"
    assert dumped["execution_mode"] == "MARKET"
    assert dumped["trade_mode"] == "FULL"
    assert dumped["calculation_mode"] == "FOREX"
    assert dumped["swap_mode"] == "POINTS"
    assert dumped["swap_rollover3days"] == "WEDNESDAY"
    assert dumped["stops_level_points"] == 0
    assert dumped["freeze_level_points"] == 0
    assert dumped["directional_volume_limit"] == "0.0"
    assert dumped["contract_size"] == "100000.0"
    assert dumped["margin_hedged"] == "100000.0"
    assert dumped["base_currency"] == "EUR"
    assert dumped["tick_value_profit"] == "1.0"


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [(0, "SUNDAY"), (6, "SATURDAY"), (7, "UNSPECIFIED")],
)
def test_rollover_day_preserves_verified_and_unspecified_values(
    raw_value: int, expected: str
) -> None:
    """MT5 weekdays map exactly while provider sentinel 7 stays unspecified."""
    symbol = _symbol_info()._replace(swap_rollover3days=raw_value)  # type: ignore[union-attr]
    dumped = dump_provider_specification_snapshot(_build(symbol_info=symbol))
    assert dumped["swap_rollover3days"] == expected


@pytest.mark.parametrize("raw_value", [-1, 8])
def test_unknown_rollover_day_fails_closed(raw_value: int) -> None:
    """Values outside the observed MT5/provider range remain ineligible."""
    symbol = _symbol_info()._replace(swap_rollover3days=raw_value)  # type: ignore[union-attr]
    with pytest.raises(ValueError, match="outside the verified provider range"):
        _build(symbol_info=symbol)


def test_fr_brokers_160_binds_source_and_observation_identity() -> None:
    """FR-BRK-160: identity, provenance, and checksum are bound."""
    snapshot = _build()
    dumped = dump_provider_specification_snapshot(snapshot)
    assert dumped["broker"] == "mt5"
    assert dumped["server"] == "DemoServer"
    assert dumped["environment"] == "demo"
    assert dumped["terminal_build"] == "4410"
    assert dumped["source_revision"] == "mt5:4410"
    assert dumped["retrieval_provenance"].startswith("metatrader.")
    assert len(dumped["account_digest"]) == _SHA256_LENGTH
    assert "123456" not in str(dumped)
    assert verify_provider_specification_snapshot(snapshot) is True


def test_fr_brokers_161_missing_required_field_fails_closed() -> None:
    """FR-BRK-161: every required raw field fails closed when absent."""
    for field_name in (
        "name",
        "digits",
        "point",
        "filling_mode",
        "order_mode",
        "expiration_mode",
        "order_gtc_mode",
        "trade_exemode",
        "trade_mode",
        "trade_calc_mode",
        "swap_mode",
        "swap_rollover3days",
        "trade_stops_level",
        "trade_freeze_level",
        "volume_min",
        "volume_max",
        "volume_step",
        "trade_tick_size",
        "trade_contract_size",
        "currency_base",
        "currency_profit",
        "currency_margin",
        "swap_long",
        "swap_short",
    ):
        incomplete = _symbol_info()._replace(**{field_name: None})  # type: ignore[union-attr]
        with pytest.raises(ValueError, match="missing required"):
            _build(symbol_info=incomplete)


def test_fr_brokers_161_non_finite_numeric_fails_closed() -> None:
    """FR-BRK-161: non-finite numeric evidence never builds a snapshot."""
    with pytest.raises(ValueError, match="not finite"):
        _build(symbol_info=_symbol_info()._replace(volume_max=float("nan")))  # type: ignore[union-attr]


def test_fr_brokers_162_keeps_cost_evidence_separate_and_typed() -> None:
    """FR-BRK-162: dynamic costs stay a separate typed reference."""
    without = dump_provider_specification_snapshot(_build())
    assert without["cost_evidence"] is None
    reference = _build(
        cost_evidence_id="cost-evidence/demo/4410/EURUSD",
        cost_evidence_checksum="a" * 64,
    )
    dumped = dump_provider_specification_snapshot(reference)
    block = dumped["cost_evidence"]
    assert isinstance(block, dict)
    assert block["evidence_kind"] == "dynamic_commission_schedule"
    assert "commission" not in dumped
    assert "fee" not in dumped


def test_fr_brokers_162_half_supplied_cost_evidence_rejected() -> None:
    """FR-BRK-162: a cost reference needs both identifier and checksum."""
    with pytest.raises(ValueError, match="cost evidence requires"):
        _build(cost_evidence_id="only-id")


def test_fr_brokers_163_snapshot_is_current_observation_only() -> None:
    """FR-BRK-163: no effective bounds exist on the type or parse path."""
    dumped = dump_provider_specification_snapshot(_build())
    assert "effective_from" not in dumped
    assert "effective_to" not in dumped
    with pytest.raises(ValueError, match="no effective bounds"):
        parse_provider_specification_snapshot(
            {**dumped, "effective_from": "2026-01-01T00:00:00+00:00"}
        )


def test_checksum_tamper_is_detected_on_parse() -> None:
    """The canonical checksum rejects any mutated material."""
    dumped = dump_provider_specification_snapshot(_build())
    for key, value in (
        ("swap_mode", "CURRENCY_SYMBOL"),
        ("volume_max", "999.0"),
        ("account_digest", "b" * 64),
    ):
        tampered = dict(dumped)
        tampered[key] = value
        with pytest.raises(ValueError, match="checksum"):
            parse_provider_specification_snapshot(tampered)


def test_parse_round_trip_preserves_identity() -> None:
    """Dump and parse round-trip the typed contract exactly."""
    snapshot = _build()
    parsed = parse_provider_specification_snapshot(
        dump_provider_specification_snapshot(snapshot)
    )
    assert verify_provider_specification_snapshot(parsed) is True
    assert get_provider_specification_snapshot_field(
        parsed, "checksum"
    ) == get_provider_specification_snapshot_field(snapshot, "checksum")


def test_account_permissions_mark_unverified_exclusions() -> None:
    """Fields the upstream contract lacks stay explicit unverified names."""
    dumped = dump_provider_specification_snapshot(_build())
    block = dumped["account_permissions"]
    assert block["margin_mode"] == "RETAIL_HEDGING"
    assert block["hedging_permitted"] is True
    assert block["stop_out_mode"] is None
    assert block["fifo"] is None
    assert set(block["unverified"]) == {"stop_out_mode", "fifo"}
    absent = dump_provider_specification_snapshot(_build(account_info=None))
    assert absent["account_permissions"]["margin_mode"] is None
    assert "margin_mode" in absent["account_permissions"]["unverified"]


def test_unmapped_enum_values_fail_canonical_eligibility() -> None:
    """Unmapped provider indices become UNKNOWN, never guessed names."""
    dumped = dump_provider_specification_snapshot(
        _build(symbol_info=_symbol_info()._replace(trade_calc_mode=99))  # type: ignore[union-attr]
    )
    assert dumped["calculation_mode"] == "UNKNOWN"


def test_filling_mode_return_fallback() -> None:
    """A zero filling mask admits the MT5 default RETURN policy."""
    dumped = dump_provider_specification_snapshot(
        _build(symbol_info=_symbol_info()._replace(filling_mode=0))  # type: ignore[union-attr]
    )
    assert dumped["filling_modes"] == ["RETURN"]


def test_getter_rejects_unknown_field() -> None:
    """Reading a field outside the schema fails closed."""
    with pytest.raises(ValueError, match="unknown snapshot field"):
        get_provider_specification_snapshot_field(_build(), "not_a_field")


def test_decimal_volume_bounds_are_exact() -> None:
    """Volumes parse through exact Decimal strings, not binary floats."""
    dumped = dump_provider_specification_snapshot(_build())
    assert Decimal(str(dumped["volume_min"])) == Decimal("0.01")
    assert Decimal(str(dumped["volume_step"])) == Decimal("0.01")


_SYMBOL_INFO_DICT = {
    "name": "EURUSD",
    "digits": 5,
    "point": 0.00001,
    "filling_mode": 3,
    "order_mode": 15,
    "expiration_mode": 5,
    "order_gtc_mode": 0,
    "trade_exemode": 2,
    "trade_mode": 4,
    "trade_calc_mode": 0,
    "swap_mode": 1,
    "swap_rollover3days": 3,
    "trade_stops_level": 10,
    "trade_freeze_level": 5,
    "volume_min": 0.01,
    "volume_max": 500.0,
    "volume_step": 0.01,
    "volume_limit": 300.0,
    "trade_tick_size": 0.00001,
    "trade_tick_value": 1.0,
    "trade_tick_value_profit": 1.0,
    "trade_tick_value_loss": 1.0,
    "trade_contract_size": 100000.0,
    "currency_base": "EUR",
    "currency_profit": "USD",
    "currency_margin": "USD",
    "margin_initial": 0.0,
    "margin_maintenance": 0.0,
    "margin_hedged": 100000.0,
    "margin_hedged_use_leg": False,
    "swap_long": -0.2,
    "swap_short": -1.2,
}

_ACCOUNT_INFO_DICT = {
    "login": 12345,
    "server": "Demo-Server",
    "currency": "USD",
    "balance": 1000,
    "equity": 1100,
    "margin": 100,
    "margin_free": 1000,
    "trade_allowed": True,
    "margin_mode": 2,
}

_TERMINAL_INFO_DICT = {
    "name": "MetaTrader 5",
    "company": "MetaQuotes Ltd.",
    "build": 4570,
    "connected": True,
    "trade_allowed": True,
}


class _SpecificationTransport:
    """Return one bounded provider observation per transport call."""

    def __init__(
        self,
        symbol_info: object | None = _SYMBOL_INFO_DICT,
        account_info: object | None = _ACCOUNT_INFO_DICT,
        terminal_info: object | None = _TERMINAL_INFO_DICT,
    ) -> None:
        self._responses = {
            "symbol_info": symbol_info,
            "account_info": account_info,
            "terminal_info": terminal_info,
        }

    async def connect(self) -> bool:
        return True

    async def call(self, name: str, *args: object) -> object:
        del args
        return self._responses.get(name)

    async def constant(self, name: str) -> object:
        del name
        return 1

    async def close(self) -> None:
        return None


def _mt5_adapter(transport: _SpecificationTransport) -> object:
    from app.services.brokers.canonical_contracts.enums import (
        BrokerEnvironment,
        BrokerId,
    )
    from app.services.brokers.canonical_contracts.models import BrokerConnectionConfig
    from app.services.brokers.metatrader.adapter import MT5BrokerAdapter
    from pydantic import SecretStr

    config = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="12345",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )
    return MT5BrokerAdapter(config, transport=transport)


def test_adapter_reads_checksum_verified_snapshot() -> None:
    """The MT5 adapter returns a checksum-verified current snapshot."""
    import asyncio

    adapter = _mt5_adapter(_SpecificationTransport())

    async def exercise() -> None:
        await adapter.connect()
        response = await adapter.get_provider_specification("EURUSD")
        assert response.status == "success"
        assert response.data is not None
        dumped = dump_provider_specification_snapshot(response.data)
        assert dumped["provider_symbol"] == "EURUSD"
        assert dumped["filling_modes"] == ["FOK", "IOC"]
        assert dumped["terminal_build"] == "4570"
        assert verify_provider_specification_snapshot(response.data) is True

    asyncio.run(exercise())


def test_adapter_missing_symbol_fails_closed() -> None:
    """An absent symbol observation returns the canonical error."""
    import asyncio

    adapter = _mt5_adapter(_SpecificationTransport(symbol_info=None))

    async def exercise() -> None:
        await adapter.connect()
        response = await adapter.get_provider_specification("MISSING")
        assert response.status == "error"
        assert response.error is not None
        assert response.error.code == "BROKER_SYMBOL_NOT_FOUND"

    asyncio.run(exercise())


def test_adapter_incomplete_payload_fails_closed() -> None:
    """A malformed provider record returns a structured response error."""
    import asyncio

    incomplete = {
        key: value
        for key, value in _SYMBOL_INFO_DICT.items()
        if key not in {"trade_calc_mode", "swap_mode"}
    }
    adapter = _mt5_adapter(_SpecificationTransport(symbol_info=incomplete))

    async def exercise() -> None:
        await adapter.connect()
        response = await adapter.get_provider_specification("EURUSD")
        assert response.status == "error"
        assert response.error is not None
        assert response.error.code == "BROKER_RESPONSE_INVALID"

    asyncio.run(exercise())


def test_adapter_snapshot_omits_raw_provider_payload() -> None:
    """No raw provider record or credential material leaks into the dump."""
    import asyncio

    adapter = _mt5_adapter(_SpecificationTransport())

    async def exercise() -> None:
        await adapter.connect()
        response = await adapter.get_provider_specification("EURUSD")
        assert response.data is not None
        dumped = dump_provider_specification_snapshot(response.data)
        assert "provider_metadata" not in dumped
        assert "hunter2" not in str(dumped)
        assert "12345" not in str(dumped)

    asyncio.run(exercise())
