"""Runnable usage examples for Trading live lifecycle requirements."""

# ruff: noqa: ARG005

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.brokers.contracts import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerFeatureFlags,
)
from app.services.trading.contracts import TradingRequest, TradingRoute
from app.services.trading.live import LiveSession, evaluate_live_gate
from app.services.trading.state import TradingStateStore
from app.utils import logger

NOW = datetime(2026, 7, 19, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend.

    Returns:
        Asyncio backend name.
    """
    logger.debug("Selecting asyncio for live usage examples")
    return "asyncio"


async def _passed() -> bool:
    """Return one successful usage lifecycle step.

    Returns:
        Always ``True``.
    """
    logger.debug("Running successful live usage lifecycle step")
    return True


def _session() -> LiveSession:
    """Build a package-only usage session.

    Returns:
        Dependency-injected session.
    """
    logger.debug("Building LiveSession usage fixture")
    connection = cast(
        "BrokerConnectionConfig",
        SimpleNamespace(
            broker_id="test-broker",
            environment=BrokerEnvironment.LIVE,
            provider_enabled=True,
        ),
    )
    adapter = cast(
        "BrokerAdapter",
        SimpleNamespace(contract_version="v1", schema_id="brokers.adapter.v1"),
    )
    flags = cast(
        "BrokerFeatureFlags",
        SimpleNamespace(
            broker_id="test-broker",
            environment=BrokerEnvironment.LIVE,
        ),
    )
    return LiveSession(
        store=cast("TradingStateStore", object()),
        connection=connection,
        broker_adapter=adapter,
        feature_flags=flags,
        risk_decision_source=lambda request: None,
        action_policy_source=lambda request: None,
        kill_switch_source=lambda request: (),
        readiness_source=lambda request, evidence: cast("object", None),
        adapter_capability_source=lambda request: {},
        pre_audit_sink=lambda evidence: None,
        event_sink=lambda event: None,
        startup_reconcile=_passed,
        drain_in_flight=_passed,
        flush_evidence=_passed,
        shutdown_reconcile=_passed,
        clock=lambda: NOW,
    )


def _config() -> dict[str, object]:
    """Return exact safe live usage config.

    Returns:
        Package-only runtime settings.
    """
    logger.debug("Building live usage config")
    return {
        "RUNTIME_PROFILE": "live",
        "EXECUTION_ROUTE": "live",
        "ALLOW_LIVE_MUTATIONS": False,
        "LIVE_WORKFLOW_TIMEOUT_SECONDS": "30",
        "SHUTDOWN_BUDGET_SECONDS": "5",
        "IDEMPOTENCY_RETENTION_SECONDS": 600,
        "CONCURRENCY_LOCK_TIMEOUT_SECONDS": "30",
        "MAX_STALENESS_SECONDS": {
            "route_snapshot": "30",
            "risk_decision": "30",
            "kill_switch": "30",
        },
        "DATA_AUTHORITY_ID": "data-authority-001",
    }


def _evidence() -> dict[str, object]:
    """Return exact safe startup evidence.

    Returns:
        JSON-safe authority/security facts.
    """
    logger.debug("Building live usage startup evidence")
    return {
        "data_authority_id": "data-authority-001",
        "adapter_security_profile": "approved",
        "startup_evidence_fresh": True,
    }


@pytest.mark.anyio
async def test_usage_session_live_session() -> None:
    """Construct one lifecycle owner with injected authority ports."""
    logger.debug("Running LiveSession construction usage example")
    assert _session().started is False


@pytest.mark.anyio
async def test_usage_session_start() -> None:
    """Start live safely in package-only mode."""
    logger.debug("Running LiveSession start usage example")
    assert (await _session().start(_config(), _evidence())).status == "packaged"


@pytest.mark.anyio
async def test_usage_session_status() -> None:
    """Read actual package-only session status."""
    logger.debug("Running LiveSession status usage example")
    session = _session()
    await session.start(_config(), _evidence())
    assert session.status().data["health"] == "package_only"


@pytest.mark.anyio
async def test_usage_session_stop() -> None:
    """Stop admission and complete all shutdown steps."""
    logger.debug("Running LiveSession stop usage example")
    session = _session()
    await session.start(_config(), _evidence())
    assert (await session.stop()).status == "success"


@pytest.mark.anyio
async def test_usage_gates_evaluate_live_gate() -> None:
    """Package a request when live mutation is disabled before authority gates."""
    logger.debug("Running live gate package-only usage example")
    session = _session()
    await session.start(_config(), _evidence())
    request = TradingRequest(
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
        route=TradingRoute.LIVE,
        action="submit_order",
        provider_id="test-broker",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="lots",
        quantity=Decimal(1),
        risk_decision_id="risk-decision-001",
        action_policy_verdict_id="policy-verdict-001",
        approval_token_ref="token-001",
        idempotency_key="usage-idempotency-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )
    result = await evaluate_live_gate(request, {}, session)
    assert result.status == "packaged"
