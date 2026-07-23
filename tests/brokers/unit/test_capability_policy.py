"""Prove capability access modes and production construction fail closed."""

import asyncio
import inspect
from decimal import Decimal

import pytest
from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    BrokerOrderRequest,
)
from app.services.brokers.mt5_account import MT5BrokerAdapter
from pydantic import SecretStr


def _config() -> BrokerConnectionConfig:
    """Return a bounded MT5 demo configuration."""
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=4,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="1",
        credentials={
            "login": SecretStr("1"),
            "password": SecretStr("x"),
            "server": SecretStr("Demo"),
        },
    )


def _capability(
    capability: BrokerCapabilityId,
    access_mode: str,
) -> BrokerCapability:
    """Build one declaration for invariant testing."""
    return BrokerCapability(
        capability=capability,
        implementation_status="IMPLEMENTED",
        availability="UNAVAILABLE",
        access_mode=access_mode,  # type: ignore[arg-type]
        requirement="NONE",
        verification_status="NOT_TESTED",
        execution_model="PROVIDER_CALL",
    )


def test_access_mode_cannot_reclassify_reads_or_mutations() -> None:
    """Reject both directions of access-mode forgery."""
    with pytest.raises(ValueError, match="mutation capability"):
        _capability(BrokerCapabilityId.PLACE_ORDER, "READ")
    with pytest.raises(ValueError, match="non-mutation capability"):
        _capability(BrokerCapabilityId.GET_QUOTE, "WRITE")


def test_direct_mt5_construction_has_no_capability_injection_and_blocks_write() -> None:
    """Direct construction derives policy and makes zero mutation calls."""
    assert "capabilities" not in inspect.signature(MT5BrokerAdapter).parameters
    adapter = MT5BrokerAdapter(_config())
    request = BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
    )
    result = asyncio.run(adapter.place_order(request))
    assert not result.is_success
    assert result.operation == BrokerCapabilityId.PLACE_ORDER
