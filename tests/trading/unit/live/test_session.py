"""Unit tests for Trading live/paper session lifecycle."""

# ruff: noqa: ARG005, INP001
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.brokers import build_broker_connection_config
from app.services.trading.live import LiveSession
from app.services.trading.live.config import (
    _positive_decimal,
    _positive_int,
    _staleness_bounds,
    _validate_live_config,
)
from app.services.trading.monitoring import OperationalEvent
from app.services.trading.state import TradingStateStore
from app.utils import get_logger

logger = get_logger(__name__)

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def test_runtime_config_rejects_inexact_and_incomplete_bounds() -> None:
    """Runtime numeric and evidence policies accept no implicit coercion."""
    with pytest.raises(TypeError, match="exact Decimal"):
        _positive_decimal(1.5)
    with pytest.raises(ValueError, match="finite and positive"):
        _positive_decimal("0")
    with pytest.raises(TypeError, match="exact int"):
        _positive_int(True)
    with pytest.raises(ValueError, match="positive"):
        _positive_int(0)
    with pytest.raises(TypeError, match="must be a mapping"):
        _staleness_bounds(())
    with pytest.raises(ValueError, match="exact evidence classes"):
        _staleness_bounds({"route_snapshot": "1"})


def test_runtime_config_requires_matching_profile_and_authority() -> None:
    """Profile/route conflicts and blank authority identity fail closed."""
    config = _config()
    config["EXECUTION_ROUTE"] = "paper"
    with pytest.raises(Exception, match="CONFIGURATION_INVALID"):
        _validate_live_config(config)
    config = _config()
    config["DATA_AUTHORITY_ID"] = " "
    with pytest.raises(Exception, match="CONFIGURATION_INVALID"):
        _validate_live_config(config)


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend.

    Returns:
        Asyncio backend name.
    """
    logger.debug("Selecting asyncio for LiveSession tests")
    return "asyncio"


def _authority() -> tuple[object, object, object]:
    """Build minimal typed live authority test doubles.

    Returns:
        Connection, adapter, and feature-flag doubles.
    """
    logger.debug("Building LiveSession authority doubles")
    connection = build_broker_connection_config(
        broker_id="mt5",
        environment="live",
        provider_enabled=True,
    )
    adapter = cast(
        "object",
        SimpleNamespace(contract_version="v1", schema_id="brokers.adapter.v1"),
    )
    flags = cast(
        "object",
        SimpleNamespace(
            broker_id="mt5",
            environment="live",
        ),
    )
    return connection, adapter, flags


async def _passed() -> bool:
    """Return one successful async lifecycle step.

    Returns:
        Always ``True``.
    """
    logger.debug("Running successful lifecycle test step")
    return True


def _session(
    *,
    startup_reconcile=_passed,
    flush_evidence=_passed,
) -> LiveSession:
    """Build a dependency-injected session test fixture.

    Args:
        startup_reconcile: Startup reconciliation callback.
        flush_evidence: Shutdown evidence-flush callback.

    Returns:
        Unstarted LiveSession.
    """
    logger.debug("Building LiveSession test fixture")
    connection, adapter, flags = _authority()
    events: list[OperationalEvent] = []
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
        auth_context_source=lambda request: cast("object", None),
        pre_audit_sink=lambda evidence: None,
        event_sink=events.append,
        startup_reconcile=startup_reconcile,
        drain_in_flight=_passed,
        flush_evidence=flush_evidence,
        shutdown_reconcile=_passed,
        clock=lambda: NOW,
    )


def _config() -> dict[str, object]:
    """Build exact live package-only configuration.

    Returns:
        JSON-safe runtime settings.
    """
    logger.debug("Building LiveSession config fixture")
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
    """Build exact startup evidence.

    Returns:
        JSON-safe authority/security evidence.
    """
    logger.debug("Building LiveSession startup evidence")
    return {
        "data_authority_id": "data-authority-001",
        "adapter_security_profile": "approved",
        "startup_evidence_fresh": True,
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "required_setting",
    [
        "IDEMPOTENCY_RETENTION_SECONDS",
        "CONCURRENCY_LOCK_TIMEOUT_SECONDS",
        "MAX_STALENESS_SECONDS",
    ],
)
async def test_required_runtime_bound_cannot_be_omitted(
    required_setting: str,
) -> None:
    """Each required safety bound fails closed when omitted from configuration."""
    config = _config()
    del config[required_setting]
    result = await _session().start(config, _evidence())
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "CONFIGURATION_INVALID"


@pytest.mark.anyio
async def test_session_starts_package_only() -> None:
    """Keep live mutations disabled when the master switch is false."""
    logger.debug("Testing package-only LiveSession startup")
    result = await _session().start(_config(), _evidence())
    assert result.status == "success"
    assert result.metadata.extensions["legacy_status"] == "packaged"
    assert result.data is not None
    assert result.data["admission_enabled"] is False


@pytest.mark.anyio
async def test_start_never_enables_before_reconciliation() -> None:
    """Leave admission closed when startup reconciliation is incomplete."""
    logger.debug("Testing startup reconciliation gate")

    async def incomplete() -> bool:
        """Return incomplete reconciliation evidence.

        Returns:
            Always ``False``.
        """
        logger.debug("Returning incomplete startup reconciliation")
        return False

    session = _session(startup_reconcile=incomplete)
    result = await session.start(_config(), _evidence())
    assert result.status == "success"
    assert result.metadata.extensions["legacy_status"] == "blocked"
    assert session.admission_enabled is False


@pytest.mark.anyio
async def test_status_never_overstates_readiness() -> None:
    """Report actual package-only admission and reconciliation state."""
    logger.debug("Testing accurate LiveSession status")
    session = _session()
    await session.start(_config(), _evidence())
    result = session.status()
    assert result.data is not None
    assert result.data["health"] == "package_only"
    assert result.data["reconciliation_ready"] is True


@pytest.mark.anyio
async def test_stop_reports_flush_and_reconciliation_failure() -> None:
    """Return partial shutdown evidence when flush fails."""
    logger.debug("Testing incomplete LiveSession shutdown")

    async def failed_flush() -> bool:
        """Return failed evidence flush.

        Returns:
            Always ``False``.
        """
        logger.debug("Returning failed shutdown flush")
        return False

    session = _session(flush_evidence=failed_flush)
    await session.start(_config(), _evidence())
    result = await session.stop()
    assert result.status == "success"
    assert result.metadata.extensions["legacy_status"] == "partial"
    assert result.data is not None
    assert "flush_evidence" in result.data["unresolved_steps"]
