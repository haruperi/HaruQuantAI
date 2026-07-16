"""Structured observability logging tests (NFR-BRK-008)."""

import asyncio
import logging

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.testing import FakeBrokerAdapter
from pydantic import SecretStr

_SECRET = "super-secret-credential-value"
_LOGGER_NAME = "haruquant"


class _RecordCollector(logging.Handler):
    """Capture every emitted record for assertion."""

    def __init__(self) -> None:
        """Initialize an empty in-memory record buffer."""
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Buffer one emitted record."""
        self.records.append(record)


def _config() -> BrokerConnectionConfig:
    """Build a minimal fake-adapter config carrying a secret credential."""
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
        credentials={"password": SecretStr(_SECRET)},
    )


def _capture() -> tuple[_RecordCollector, logging.Logger, int]:
    """Attach a capturing handler at DEBUG and return prior level for restore."""
    collector = _RecordCollector()
    domain_logger = logging.getLogger(_LOGGER_NAME)
    previous_level = domain_logger.level
    domain_logger.setLevel(logging.DEBUG)
    domain_logger.addHandler(collector)
    return collector, domain_logger, previous_level


def test_operations_emit_structured_logs() -> None:
    """A completed operation emits a record with the NFR-BRK-008 fields."""
    collector, domain_logger, previous_level = _capture()
    try:
        adapter = FakeBrokerAdapter(_config(), {})
        asyncio.run(adapter.connect())
    finally:
        domain_logger.removeHandler(collector)
        domain_logger.setLevel(previous_level)

    operation_records = [
        record
        for record in collector.records
        if getattr(record, "operation", None) == BrokerCapabilityId.CONNECT.value
    ]
    assert operation_records, "connect must emit a structured operation log"
    record = operation_records[-1]
    assert record.broker == BrokerId.MT5.value
    assert record.environment == BrokerEnvironment.DEMO.value
    assert record.result == "success"
    assert isinstance(record.request_id, str)
    assert record.request_id
    assert isinstance(record.latency_ms, float)


def test_state_transitions_are_logged() -> None:
    """Every verified state transition emits a lifecycle record."""
    collector, domain_logger, previous_level = _capture()
    try:
        adapter = FakeBrokerAdapter(_config(), {})
        asyncio.run(adapter.connect())
    finally:
        domain_logger.removeHandler(collector)
        domain_logger.setLevel(previous_level)

    new_states = {getattr(record, "new_state", None) for record in collector.records}
    assert "connecting" in new_states
    assert "ready" in new_states


def test_error_results_log_provider_code_without_secret_leak() -> None:
    """An error result logs its provider code and never leaks a secret."""
    collector, domain_logger, previous_level = _capture()
    try:
        adapter = FakeBrokerAdapter(_config(), {})
        adapter.inject_error(
            BrokerCapabilityId.GET_QUOTE,
            BrokerError(
                code=BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND,
                message="symbol absent",
            ),
        )
        asyncio.run(adapter.get_quote("EURUSD"))
    finally:
        domain_logger.removeHandler(collector)
        domain_logger.setLevel(previous_level)

    error_records = [
        record
        for record in collector.records
        if getattr(record, "result", None) == "error"
    ]
    assert error_records, "an error result must emit a warning record"
    assert any(
        getattr(record, "provider_code", None)
        == BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND.value
        for record in error_records
    )
    for record in collector.records:
        assert _SECRET not in record.getMessage()
        assert _SECRET not in str(record.__dict__)
