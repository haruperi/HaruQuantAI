"""Transport circuit state-machine tests."""

import asyncio

import pytest
from app.services.brokers import BrokerErrorCode
from app.services.brokers.runtime.circuit_breaker import _TransportCircuitBreaker


def test_circuit_state_machine_and_failure_classification() -> None:
    """Only qualifying consecutive failures open the circuit."""

    async def exercise() -> None:
        circuit = _TransportCircuitBreaker(
            failure_threshold=2,
            recovery_timeout_sec=0.1,
            half_open_max_calls=1,
        )
        await circuit.record_failure(BrokerErrorCode.BROKER_REQUEST_INVALID)
        assert circuit.state == "closed"
        await circuit.record_failure(BrokerErrorCode.BROKER_TIMEOUT)
        await circuit.record_failure(BrokerErrorCode.BROKER_CONNECTION_LOST)
        assert circuit.state == "open"
        assert await circuit.before_call() == BrokerErrorCode.BROKER_CIRCUIT_OPEN
        await asyncio.sleep(0.11)
        assert await circuit.before_call() is None
        await circuit.record_success()
        assert circuit.state == "closed"

    asyncio.run(exercise())


def test_circuit_reopens_on_half_open_failure() -> None:
    """A qualifying failure during the half-open probe reopens the circuit."""

    async def exercise() -> None:
        circuit = _TransportCircuitBreaker(
            failure_threshold=1,
            recovery_timeout_sec=0.05,
            half_open_max_calls=1,
        )
        await circuit.record_failure(BrokerErrorCode.BROKER_TIMEOUT)
        assert circuit.state == "open"
        await asyncio.sleep(0.06)
        assert await circuit.before_call() is None
        assert circuit.state == "half_open"
        await circuit.record_failure(BrokerErrorCode.BROKER_TIMEOUT)
        assert circuit.state == "open"

    asyncio.run(exercise())


def test_circuit_half_open_admits_only_bounded_calls() -> None:
    """Half-open admits at most ``half_open_max_calls`` concurrent probes."""

    async def exercise() -> None:
        circuit = _TransportCircuitBreaker(
            failure_threshold=1,
            recovery_timeout_sec=0.05,
            half_open_max_calls=1,
        )
        await circuit.record_failure(BrokerErrorCode.BROKER_TIMEOUT)
        await asyncio.sleep(0.06)
        assert await circuit.before_call() is None
        assert await circuit.before_call() == BrokerErrorCode.BROKER_CIRCUIT_OPEN

    asyncio.run(exercise())


def test_circuit_non_qualifying_failure_never_opens() -> None:
    """Structural/business errors never count toward the transport threshold."""

    async def exercise() -> None:
        circuit = _TransportCircuitBreaker(
            failure_threshold=1,
            recovery_timeout_sec=0.05,
            half_open_max_calls=1,
        )
        await circuit.record_failure(BrokerErrorCode.BROKER_REQUEST_INVALID)
        assert circuit.state == "closed"
        assert await circuit.before_call() is None

    asyncio.run(exercise())


def test_circuit_success_resets_consecutive_failures() -> None:
    """A success while closed clears the consecutive-failure counter."""

    async def exercise() -> None:
        circuit = _TransportCircuitBreaker(
            failure_threshold=2,
            recovery_timeout_sec=0.05,
            half_open_max_calls=1,
        )
        await circuit.record_failure(BrokerErrorCode.BROKER_TIMEOUT)
        await circuit.record_success()
        await circuit.record_failure(BrokerErrorCode.BROKER_TIMEOUT)
        assert circuit.state == "closed"

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "kwargs",
    [
        {"failure_threshold": 0, "recovery_timeout_sec": 1, "half_open_max_calls": 1},
        {"failure_threshold": 1, "recovery_timeout_sec": 0, "half_open_max_calls": 1},
        {"failure_threshold": 1, "recovery_timeout_sec": 1, "half_open_max_calls": 0},
    ],
)
def test_circuit_rejects_non_positive_bounds(kwargs: dict[str, float]) -> None:
    """Every circuit bound must be strictly positive."""
    with pytest.raises(ValueError, match="positive"):
        _TransportCircuitBreaker(**kwargs)
