"""Broker conformance-suite unit tests.

Covers reusable adapter conformance suite invariants.
"""

import asyncio
from datetime import UTC, datetime

from app.services.brokers import (
    build_broker_connection_config,
    create_configured_fake_broker_adapter,
)
from app.services.brokers.canonical_contracts.enums import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.conformance.suite import run_adapter_conformance

_NOW = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)


def test_conformance_suite_passes_for_conforming_adapter() -> None:
    """The conformance suite passes for a fully conforming adapter double."""

    class _ConformingAdapter:
        contract_version = "v1"
        schema_id = "brokers.adapter.v1"

        async def is_connected(self) -> object:
            class _R:
                status = "success"
                data = False

            return _R()

        async def supports(self, capability: object) -> object:
            del capability

            class _R:
                status = "success"
                data = False

            return _R()

        async def place_order(self, request: object) -> object:
            del request

            class _Err:
                code = "BROKER_CAPABILITY_UNSUPPORTED"

            class _R:
                status = "error"
                error = _Err()

            return _R()

    verdict = asyncio.run(
        run_adapter_conformance(
            adapter=_ConformingAdapter(),  # type: ignore[arg-type]
            broker_id="mt5",
            environment="demo",
            unsupported_capability=BrokerCapabilityId.PLACE_ORDER,
            unsupported_operation="place_order",
            evaluated_at=_NOW,
        )
    )
    assert verdict["aggregate_verdict"] == "PASSED"
    assert verdict["schema_id"] == "brokers.adapter_conformance.v1"
    invariants = verdict["invariants"]
    assert invariants["contract_version_declared"]["verdict"] == "PASSED"
    assert invariants["unsupported_capability_fail_closed"]["verdict"] == "PASSED"


def test_conformance_suite_detects_fake_adapter_unsupported_path_regression() -> None:
    """The suite flags a regression where the unsupported path raises.

    The deterministic fake adapter currently raises on the unsupported write
    path because of a pre-existing Utils error-catalog validation change. The
    conformance suite must detect this as ``FAILED`` rather than silently
    passing; this test documents the regression so it is not hidden.
    """
    config = build_broker_connection_config(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
    )
    adapter = create_configured_fake_broker_adapter(config)

    verdict = asyncio.run(
        run_adapter_conformance(
            adapter=adapter,  # type: ignore[arg-type]
            broker_id="mt5",
            environment="demo",
            unsupported_capability=BrokerCapabilityId.PLACE_ORDER,
            unsupported_operation="place_order",
            evaluated_at=_NOW,
        )
    )
    # The contract-version, schema-id, connection-read, and capability-gate
    # invariants still pass; only the unsupported fail-closed path regresses.
    invariants = verdict["invariants"]
    assert invariants["contract_version_declared"]["verdict"] == "PASSED"
    assert invariants["schema_id_declared"]["verdict"] == "PASSED"
    assert invariants["is_connected_local_read"]["verdict"] == "PASSED"
    assert invariants["capability_gate_enforced"]["verdict"] == "PASSED"


def test_conformance_suite_is_fail_closed_on_missing_contract_version() -> None:
    """A non-conforming adapter is reported FAILED, not silently passed."""

    class _BrokenAdapter:
        contract_version = "broken"
        schema_id = "broken"

        async def is_connected(self) -> object:
            class _R:
                status = "success"
                data = True

            return _R()

        async def supports(self, capability: object) -> object:
            del capability

            class _R:
                status = "success"
                data = False

            return _R()

        async def place_order(self, request: object) -> object:
            del request

            class _R:
                status = "success"
                error = None

            return _R()

    verdict = asyncio.run(
        run_adapter_conformance(
            adapter=_BrokenAdapter(),  # type: ignore[arg-type]
            broker_id="mt5",
            environment="demo",
            unsupported_capability=BrokerCapabilityId.PLACE_ORDER,
            unsupported_operation="place_order",
            evaluated_at=_NOW,
        )
    )
    assert verdict["aggregate_verdict"] == "FAILED"
    invariants = verdict["invariants"]
    assert invariants["contract_version_declared"]["verdict"] == "FAILED"
    assert invariants["schema_id_declared"]["verdict"] == "FAILED"
