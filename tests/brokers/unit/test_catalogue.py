"""Static capability catalogue tests."""

from app.services.brokers import BrokerCapabilityId, BrokerId
from app.services.brokers.registry import get_broker_capability_catalogue


def test_catalogue_is_the_single_complete_declaration_source() -> None:
    """Every profile declares every canonical operation exactly once."""
    catalogue = get_broker_capability_catalogue()
    assert set(catalogue) == set(BrokerId)
    for entries in catalogue.values():
        assert {entry.capability for entry in entries} == set(BrokerCapabilityId)
        for entry in entries:
            if entry.capability == BrokerCapabilityId.PLACE_ORDER:
                assert entry.availability == "UNAVAILABLE"
