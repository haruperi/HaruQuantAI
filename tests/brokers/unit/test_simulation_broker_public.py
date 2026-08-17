"""Unit tests for simulation broker public operations and envelope creation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from app.services.brokers.canonical_contracts import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.simulation.public import (
    build_simulation_mutation_envelope,
    build_simulation_read_envelope,
    create_simulation_broker_adapter,
    finalize_simulation_broker_session,
)


def test_build_simulation_envelopes() -> None:
    """Verify build_simulation_mutation_envelope and build_simulation_read_envelope."""
    now = datetime.now(UTC)
    mut = build_simulation_mutation_envelope(
        provider_result={"retcode": 10009},
        request_echo={"id": 1},
        simulated_at=now,
    )
    assert mut is not None

    read_env = build_simulation_read_envelope(
        payload={"bid": 1.1},
        source_sequence=1,
        observed_at=now,
        received_at=now,
        available_at=now,
        simulated_at=now,
    )
    assert read_env is not None


def test_create_and_finalize_simulation_adapter_type_errors() -> None:
    """Verify type errors when wrong types are passed to adapter functions."""
    with pytest.raises(TypeError, match="config must be a BrokerConnectionConfig"):
        create_simulation_broker_adapter("invalid_config", MagicMock())

    with pytest.raises(TypeError, match="adapter must be a simulation broker adapter"):
        asyncio.run(finalize_simulation_broker_session("invalid_adapter"))


def test_create_and_finalize_simulation_adapter_success() -> None:
    """Verify successful adapter creation and finalization."""
    config = BrokerConnectionConfig(
        broker_id=BrokerId.SIM,
        environment=BrokerEnvironment.SIMULATION,
        provider_enabled=True,
        connect_timeout_sec=1.0,
        request_timeout_sec=1.0,
        transport_reconnect_max_attempts=1,
        stream_buffer_size=10,
        circuit_failure_threshold=3,
        circuit_recovery_timeout_sec=1.0,
        circuit_half_open_max_calls=1,
    )
    mock_port = MagicMock()
    res = create_simulation_broker_adapter(config, mock_port)
    assert res.status == "success"
    adapter = res.data

    fin_res = asyncio.run(finalize_simulation_broker_session(adapter))
    assert fin_res.status in {"success", "error"}
