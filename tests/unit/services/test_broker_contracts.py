"""Verify shared broker model and flattened export compatibility.

Description:
    Check public identities, immutable records and failure metadata without
    starting a listener, journal or live broker connection.

Purpose:
    FEAT-BROKER-CONTRACTS: Preserve the moved broker contract surface.

Key Capabilities:
    - FR-BROKER-CONTRACTS-RECORDS: Verify enum values and immutable defaults.
      Associated: `Receipt`, `PropertyValue`, `BridgeEvent`, `Timeframe`
      Logging: Passive model checks; no operational capability executes here.
    - FR-BROKER-CONTRACTS-ERRORS: Verify error metadata and public exports.
      Associated: `BridgeError`
      Logging: No secret-bearing messages are emitted by these tests.

Python API Usage:
    Run this module through pytest.

CLI Usage:
    uv run pytest tests/unit/services/test_broker_contracts.py --no-cov
"""

from dataclasses import FrozenInstanceError

import pytest
from app.services.brokers import contracts, metatrader


@pytest.mark.parametrize(
    "name",
    ["BridgeError", "PropertyValue", "Receipt", "ReceiptStatus", "TradeResolution"],
)
def test_flattened_contract_exports(name: str) -> None:
    """Keep previous package exports identical to their shared declarations."""
    assert getattr(metatrader, name) is getattr(contracts, name)
    assert name in metatrader.__all__


def test_contract_enum_values() -> None:
    """Preserve externally serialized status and resolution strings."""
    assert tuple(contracts.ReceiptStatus) == (
        "created",
        "sent",
        "acknowledged",
        "resolved",
        "rejected",
        "uncertain",
    )
    assert tuple(contracts.TradeResolution) == (
        "dispatched",
        "filled",
        "placed",
        "partially_filled",
        "rejected",
        "cancelled",
        "expired",
        "not_found",
        "uncertain",
    )


def test_immutable_receipt_and_property() -> None:
    """Keep receipt defaults isolated and records frozen."""
    receipt = contracts.Receipt(
        command_id="test",
        object_id="trade",
        class_name="Trade",
        method_name="Buy",
        status=contracts.ReceiptStatus.CREATED,
        created_at=1.0,
    )
    other = contracts.Receipt(
        command_id="other",
        object_id="trade",
        class_name="Trade",
        method_name="Buy",
        status=contracts.ReceiptStatus.CREATED,
        created_at=1.0,
    )
    assert receipt.meta == {}
    assert receipt.meta is not other.meta
    assert receipt.native_request_id is None
    assert receipt.error is None
    assert receipt.value is None
    with pytest.raises(FrozenInstanceError):
        receipt.command_id = "replacement"  # type: ignore[misc]
    value = contracts.PropertyValue(ok=False, error="unavailable")
    assert value.value is None
    with pytest.raises(FrozenInstanceError):
        value.ok = True  # type: ignore[misc]
    event = contracts.BridgeEvent(event_type="transaction", payload={})
    assert event.command_id is None
    assert event.request_id is None


def test_error_metadata() -> None:
    """Retain failure classification and reconciliation metadata."""
    error = contracts.BridgeError(
        "outcome unknown",
        code="CONNECTION_LOST",
        command_id="test",
        uncertain=True,
    )
    assert isinstance(error, RuntimeError)
    assert str(error) == "outcome unknown"
    assert error.code == "CONNECTION_LOST"
    assert error.command_id == "test"
    assert error.uncertain
    default = contracts.BridgeError("failure")
    assert default.code == "BRIDGE_ERROR"
    assert default.command_id is None
    assert not default.uncertain


def test_timeframe_enum_members() -> None:
    """Verify all 22 Timeframe members, values, and string compatibility."""
    expected_members = {
        "PERIOD_CURRENT": "CURRENT",
        "PERIOD_M1": "M1",
        "PERIOD_M2": "M2",
        "PERIOD_M3": "M3",
        "PERIOD_M4": "M4",
        "PERIOD_M5": "M5",
        "PERIOD_M6": "M6",
        "PERIOD_M10": "M10",
        "PERIOD_M12": "M12",
        "PERIOD_M15": "M15",
        "PERIOD_M20": "M20",
        "PERIOD_M30": "M30",
        "PERIOD_H1": "H1",
        "PERIOD_H2": "H2",
        "PERIOD_H3": "H3",
        "PERIOD_H4": "H4",
        "PERIOD_H6": "H6",
        "PERIOD_H8": "H8",
        "PERIOD_H12": "H12",
        "PERIOD_D1": "D1",
        "PERIOD_W1": "W1",
        "PERIOD_MN1": "MN1",
    }
    assert len(contracts.Timeframe) == 22
    for name, value in expected_members.items():
        member = getattr(contracts.Timeframe, name)
        assert member == value
        assert member.value == value
        assert contracts.Timeframe(value) is member
