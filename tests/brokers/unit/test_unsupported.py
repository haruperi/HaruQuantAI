"""Unsupported operation behavior tests."""

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerId,
    BrokerResult,
)
from app.services.brokers.contracts.unsupported import _unsupported_result


def test_unsupported_result_is_deterministic_and_no_call() -> None:
    """Unsupported construction needs no provider module or probe."""
    result: BrokerResult[None] = _unsupported_result(
        broker=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        operation=BrokerCapabilityId.GET_QUOTE,
        request_id="request",
        adapter_version="1",
    )
    assert not result.is_success
    assert result.error is not None
    assert result.error.capability == BrokerCapabilityId.GET_QUOTE
