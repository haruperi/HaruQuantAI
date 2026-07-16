"""WF-BRK-005: read account and execution state."""

import asyncio
from datetime import UTC, datetime

from app.services.brokers import (
    BrokerAccountInfo,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.testing import FakeBrokerAdapter


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for operation in BrokerCapabilityId
    }


def test_account_state_preserves_provider_ids_and_bounds() -> None:
    """Account reads preserve the exact provider account ID and redaction."""
    account = BrokerAccountInfo(
        account_id="12345",
        retrieved_at=datetime.now(UTC),
        account_reference_redacted="***",
    )
    adapter = FakeBrokerAdapter(
        _config(),
        _capabilities(),
        fixtures={BrokerCapabilityId.GET_ACCOUNT_INFO: account},
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_account_info()
        assert result.data is account
        assert result.data.account_id == "12345"
        assert result.data.account_reference_redacted == "***"

    asyncio.run(exercise())


def test_missing_account_target_returns_exact_not_found_code() -> None:
    """A missing target returns the exact BROKER_*_NOT_FOUND result."""
    adapter = FakeBrokerAdapter(_config(), _capabilities())
    adapter.inject_error(
        BrokerCapabilityId.GET_ACCOUNT_INFO,
        BrokerError(code=BrokerErrorCode.BROKER_ACCOUNT_NOT_FOUND, message="not found"),
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_account_info()
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_ACCOUNT_NOT_FOUND

    asyncio.run(exercise())
