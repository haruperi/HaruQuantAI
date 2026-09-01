"""Unit evidence for Broker order-policy v2 and MT5 mapping."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.brokers import build_broker_order_request_v2
from app.services.brokers.canonical_contracts.enums import BrokerEnvironment
from app.services.brokers.metatrader.commands import _MT5MutationsMixin


class _Transport:
    """Resolve verified constant names without provider access."""

    async def constant(self, name: str) -> str:
        """Return the requested constant name as observable evidence."""
        return name

    async def call(self, name: str, *_args: object, **_kwargs: object) -> object:
        """Return a deterministic market tick only when requested."""
        if name == "symbol_info_tick":
            return {"ask": 1.1, "bid": 1.0}
        raise AssertionError(f"unexpected provider-derived call: {name}")


class _Harness(_MT5MutationsMixin):
    """Expose the private adapter mapper with an injected fake transport."""

    def __init__(self) -> None:
        self._transport = _Transport()
        self._last_error = None


@pytest.fixture(autouse=True)
def _snapshot_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expose exact supported policy fields through the public snapshot getter."""

    def get_field(_snapshot: object, field: str) -> object:
        return {
            "filling_modes": ("FOK", "IOC", "RETURN"),
            "expiration_modes": ("GTC", "DAY", "SPECIFIED", "SPECIFIED_DAY"),
            "checksum": "d" * 64,
        }[field]

    monkeypatch.setattr(
        "app.services.brokers.metatrader.specifications.get_provider_specification_snapshot_field",
        get_field,
    )
    monkeypatch.setattr(
        "app.services.brokers.metatrader.commands.get_provider_specification_snapshot_field",
        get_field,
    )


def _request(fill_policy: str, time_policy: str) -> object:
    """Build one opaque v2 request through the package root."""
    fields: dict[str, object] = {
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": Decimal(1),
        "quantity_unit": "lots",
        "environment": BrokerEnvironment.DEMO,
        "fill_policy": fill_policy,
        "time_policy": time_policy,
    }
    if time_policy.startswith("SPECIFIED"):
        fields["expiration"] = datetime(2026, 8, 16, tzinfo=UTC)
    return build_broker_order_request_v2(provider_specification=object(), **fields)


@pytest.mark.parametrize(
    ("fill_policy", "fill_constant"),
    [
        ("FOK", "ORDER_FILLING_FOK"),
        ("IOC", "ORDER_FILLING_IOC"),
        ("RETURN", "ORDER_FILLING_RETURN"),
    ],
)
@pytest.mark.parametrize(
    ("time_policy", "time_constant"),
    [
        ("GTC", "ORDER_TIME_GTC"),
        ("DAY", "ORDER_TIME_DAY"),
        ("SPECIFIED", "ORDER_TIME_SPECIFIED"),
        ("SPECIFIED_DAY", "ORDER_TIME_SPECIFIED_DAY"),
    ],
)
def test_fr_brk_164_165_maps_policies_independently(
    fill_policy: str,
    fill_constant: str,
    time_policy: str,
    time_constant: str,
) -> None:
    """FR-BRK-164/165: every admitted policy maps independently."""
    native = asyncio.run(
        _Harness()._native_order_request(_request(fill_policy, time_policy))
    )
    assert native["type_filling"] == fill_constant
    assert native["type_time"] == time_constant


def test_fr_brk_166_unsupported_boc_fails_before_mapping() -> None:
    """FR-BRK-166: unsupported BOC never reaches adapter mapping."""
    with pytest.raises(ValueError, match="fill_policy is unsupported"):
        _request("BOC", "GTC")
