"""Static capability catalogue tests."""

from app.services.brokers import BrokerCapabilityId, BrokerId
from app.services.brokers.registry import get_broker_capability_catalogue


def test_catalogue_is_the_single_complete_declaration_source() -> None:
    """Every profile declares every canonical operation exactly once."""
    catalogue = get_broker_capability_catalogue()
    assert set(catalogue) == set(BrokerId)
    for entries in catalogue.values():
        assert {entry.capability for entry in entries} == set(BrokerCapabilityId)
        writes = {
            BrokerCapabilityId.CHECK_ORDER,
            BrokerCapabilityId.PLACE_ORDER,
            BrokerCapabilityId.MODIFY_ORDER,
            BrokerCapabilityId.CANCEL_ORDER,
            BrokerCapabilityId.MODIFY_POSITION,
            BrokerCapabilityId.CLOSE_POSITION,
        }
        for entry in entries:
            if entry.capability in writes:
                assert entry.availability == "UNAVAILABLE"


def test_implemented_writes_are_still_unconditionally_unavailable() -> None:
    """DEC-BRK-003 release policy cannot be bypassed by implementation state."""
    catalogue = get_broker_capability_catalogue()
    for broker in (BrokerId.MT5, BrokerId.CTRADER):
        writes = tuple(
            entry for entry in catalogue[broker] if entry.access_mode == "WRITE"
        )
        assert writes
        assert all(entry.implementation_status == "IMPLEMENTED" for entry in writes)
        assert all(entry.availability == "UNAVAILABLE" for entry in writes)
