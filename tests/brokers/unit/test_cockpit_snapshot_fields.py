"""Snapshot field, capability-trait, and safe-order-command unit tests.

Covers ``TC-IMP-BRK-05`` (order/position uncertainty fields), ``TC-IMP-BRK-02``
(capability matrix trait extensions), and ``TC-IMP-BRK-06`` (safe order command
port additions: attach-protection, reduce, explicit idempotency).
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.brokers import (
    build_broker_order_protection_request,
    build_broker_position_reduce_request,
)
from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
    BrokerUncertainty,
)
from app.services.brokers.contracts.models import (
    BrokerCapability,
    BrokerOrder,
    BrokerOrderProtectionRequest,
    BrokerPosition,
    BrokerPositionReductionRequest,
)
from app.services.brokers.registry.catalogue import get_broker_capability_catalogue

_NOW = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)


# --- TC-IMP-BRK-05: snapshot uncertainty fields ---


def test_broker_order_defaults_to_known_uncertainty() -> None:
    """An order constructed without uncertainty defaults to KNOWN."""
    order = BrokerOrder(
        order_id="o1",
        symbol="EURUSD",
        side="BUY",
        order_type="LIMIT",
        state="ACCEPTED",
        quantity=Decimal(1),
        filled=Decimal(0),
        remaining=Decimal(1),
        quantity_unit="lots",
        retrieved_at=_NOW,
    )
    assert order.uncertainty is BrokerUncertainty.KNOWN
    assert order.source_sequence is None
    assert order.receive_time is None
    assert order.raw_payload_ref is None


def test_broker_position_accepts_unknown_uncertainty_and_sequence() -> None:
    """A position may carry UNKNOWN uncertainty plus source evidence."""
    position = BrokerPosition(
        position_id="p1",
        symbol="EURUSD",
        side="LONG",
        quantity=Decimal(1),
        quantity_unit="lots",
        retrieved_at=_NOW,
        source_sequence=42,
        receive_time=_NOW,
        raw_payload_ref="ticket-42",
        uncertainty=BrokerUncertainty.UNKNOWN,
    )
    assert position.uncertainty is BrokerUncertainty.UNKNOWN
    assert position.source_sequence == 42


def test_broker_order_rejects_negative_source_sequence() -> None:
    """A negative source sequence is rejected."""
    with pytest.raises(ValueError, match="source_sequence"):
        BrokerOrder(
            order_id="o1",
            symbol="EURUSD",
            side="BUY",
            order_type="LIMIT",
            state="ACCEPTED",
            quantity=Decimal(1),
            filled=Decimal(0),
            remaining=Decimal(1),
            quantity_unit="lots",
            retrieved_at=_NOW,
            source_sequence=-1,
        )


# --- TC-IMP-BRK-02: capability matrix trait extensions ---


def test_broker_capability_defaults_traits_to_undeclared() -> None:
    """Undeclared traits default fail-closed to UNDECLARED."""
    capability = BrokerCapability(
        capability=BrokerCapabilityId.GET_QUOTE,
        implementation_status="IMPLEMENTED",
        availability="AVAILABLE",
        access_mode="READ",
        requirement="AUTHENTICATION",
        verification_status="TESTED_SANDBOX",
        execution_model="PROVIDER_CALL",
    )
    assert capability.bracket_order_support == "UNDECLARED"
    assert capability.oco_order_support == "UNDECLARED"
    assert capability.position_mode == "UNDECLARED"
    assert capability.partial_fill_support == "UNDECLARED"
    assert capability.modification_support == "UNDECLARED"
    assert capability.cancellation_support == "UNDECLARED"
    assert capability.sandbox_availability == "UNDECLARED"


def test_broker_capability_accepts_declared_traits() -> None:
    """A capability may declare explicit trait support."""
    capability = BrokerCapability(
        capability=BrokerCapabilityId.PLACE_ORDER,
        implementation_status="IMPLEMENTED",
        availability="UNAVAILABLE",
        access_mode="WRITE",
        requirement="PERMISSION",
        verification_status="NOT_TESTED",
        execution_model="PROVIDER_CALL",
        bracket_order_support="SUPPORTED",
        position_mode="NETTING",
        partial_fill_support="SUPPORTED",
        sandbox_availability="AVAILABLE",
    )
    assert capability.bracket_order_support == "SUPPORTED"
    assert capability.position_mode == "NETTING"
    assert capability.sandbox_availability == "AVAILABLE"


def test_attach_protection_and_reduce_position_are_unavailable_in_catalogue() -> None:
    """The two new write capabilities are fail-closed UNAVAILABLE everywhere."""
    response = get_broker_capability_catalogue()
    assert response.status == "success"
    catalogue = response.data
    for broker_entries in catalogue.values():
        for entry in broker_entries:
            if entry.capability in {
                BrokerCapabilityId.ATTACH_PROTECTION,
                BrokerCapabilityId.REDUCE_POSITION,
            }:
                assert entry.availability == "UNAVAILABLE"
                assert entry.implementation_status == "NOT_IMPLEMENTED"
                assert entry.access_mode == "WRITE"


# --- TC-IMP-BRK-06: safe order command port additions ---


def test_build_order_protection_request_requires_one_protection_field() -> None:
    """A protection request requires at least one protection price."""
    with pytest.raises(ValueError, match="order protection requires"):
        BrokerOrderProtectionRequest(
            order_id="o1",
            idempotency_key="idem-1",
        )


def test_build_order_protection_request_builder_round_trip() -> None:
    """The public builder constructs a valid protection request."""
    request = build_broker_order_protection_request(
        order_id="o1",
        idempotency_key="idem-1",
        stop_loss="1.05",
        take_profit="1.10",
    )
    assert isinstance(request, BrokerOrderProtectionRequest)
    assert request.stop_loss == Decimal("1.05")
    assert request.idempotency_key == "idem-1"


def test_build_position_reduce_request_builder_round_trip() -> None:
    """The public builder constructs a valid reduction request."""
    request = build_broker_position_reduce_request(
        position_id="p1",
        quantity="0.5",
        quantity_unit="lots",
        idempotency_key="idem-2",
    )
    assert isinstance(request, BrokerPositionReductionRequest)
    assert request.quantity == Decimal("0.5")
    assert request.idempotency_key == "idem-2"


def test_protocols_expose_attach_protection_and_reduce_position() -> None:
    """The adapter protocol exposes the two new safe-order methods."""
    from app.services.brokers.contracts.protocols import BrokerAdapter

    assert hasattr(BrokerAdapter, "attach_protection")
    assert hasattr(BrokerAdapter, "reduce_position")
