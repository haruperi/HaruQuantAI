"""Integration evidence for the opaque Broker v2 boundary."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.brokers import (
    build_broker_order_request_v2,
    get_broker_environment,
    get_broker_value_field,
)


def test_fr_brk_164_166_root_boundary_preserves_exact_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-BRK-164/166: root construction preserves policies and UTC expiry."""

    def get_field(_snapshot: object, field: str) -> object:
        return {
            "filling_modes": ("IOC",),
            "expiration_modes": ("SPECIFIED_DAY",),
            "checksum": "e" * 64,
        }[field]

    domain = "brokers"
    getter_path = f"app.services.{domain}.specifications.public.get_provider_specification_snapshot_field"
    monkeypatch.setattr(getter_path, get_field)
    expiration = datetime(2026, 8, 16, 21, 59, 59, tzinfo=UTC)
    request = build_broker_order_request_v2(
        provider_specification=object(),
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal(1),
        quantity_unit="lots",
        environment=get_broker_environment("demo"),
        fill_policy="IOC",
        time_policy="SPECIFIED_DAY",
        expiration=expiration,
    )
    assert get_broker_value_field(request, "contract_version") == "v2"
    assert get_broker_value_field(request, "fill_policy") == "IOC"
    assert get_broker_value_field(request, "time_policy") == "SPECIFIED_DAY"
    assert get_broker_value_field(request, "expiration") == expiration
    assert (
        get_broker_value_field(request, "provider_specification_checksum") == "e" * 64
    )
