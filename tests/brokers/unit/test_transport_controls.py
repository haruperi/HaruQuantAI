"""Validate transport circuit admission without provider replay."""

import asyncio

import pytest
from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.contracts.protocols import _CircuitOpenError
from app.services.brokers.mt5_account.transport import _MT5Transport
from pydantic import SecretStr


def _config() -> BrokerConnectionConfig:
    """Return an MT5 configuration whose circuit opens after one failure."""
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=4,
        circuit_failure_threshold=1,
        circuit_recovery_timeout_sec=60,
        circuit_half_open_max_calls=1,
        account_reference="1",
        credentials={
            "login": SecretStr("1"),
            "password": SecretStr("x"),
            "server": SecretStr("Demo"),
        },
    )


def test_open_circuit_causes_zero_additional_sdk_calls() -> None:
    """One qualifying failure opens the circuit before the next SDK call."""

    async def run() -> int:
        calls = 0

        def fail() -> None:
            nonlocal calls
            calls += 1
            raise OSError("offline")

        transport = _MT5Transport(_config())
        with pytest.raises(OSError, match="offline"):
            await transport._run(fail)
        with pytest.raises(_CircuitOpenError):
            await transport._run(fail)
        return calls

    assert asyncio.run(run()) == 1
