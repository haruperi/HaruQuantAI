"""Simulation route lifecycle convergence tests."""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.brokers import build_broker_connection_config
from app.services.trading import (
    create_live_session,
    get_live_session_status,
    start_live_session,
    stop_live_session,
)

NOW = datetime(2026, 8, 16, tzinfo=UTC)


async def _passed() -> bool:
    """Return successful bounded lifecycle evidence."""
    return True


def _session() -> object:
    """Build one socket-free simulation lifecycle session."""
    return create_live_session(
        store=cast("object", object()),
        connection=build_broker_connection_config("sim", "simulation"),
        broker_adapter=SimpleNamespace(
            contract_version="v1", schema_id="brokers.adapter.v1"
        ),
        feature_flags=SimpleNamespace(broker_id="sim", environment="simulation"),
        risk_decision_source=lambda _request: None,
        action_policy_source=lambda _request: None,
        kill_switch_source=lambda _request: (),
        readiness_source=lambda _request, _evidence: None,
        adapter_capability_source=lambda _request: {},
        auth_context_source=lambda _request: None,
        pre_audit_sink=lambda _event: None,
        event_sink=lambda _event: None,
        startup_reconcile=_passed,
        drain_in_flight=_passed,
        flush_evidence=_passed,
        shutdown_reconcile=_passed,
        clock=lambda: NOW,
    )


def _config() -> dict[str, object]:
    """Return exact simulation-safe lifecycle configuration."""
    return {
        "RUNTIME_PROFILE": "sim",
        "EXECUTION_ROUTE": "sim",
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


@pytest.mark.anyio
async def test_simulation_lifecycle_shape_matches_live_fixture() -> None:
    """Simulation lifecycle admits mutations without live authorization or network."""
    session = _session()
    evidence = {
        "data_authority_id": "data-authority-001",
        "adapter_security_profile": "approved",
        "startup_evidence_fresh": True,
    }
    started = await start_live_session(session, _config(), evidence)
    assert started.data["admission_enabled"] is True
    assert started.metadata.requires_network is False
    status = get_live_session_status(session)
    assert status.data["mode"] == "sim"
    stopped = await stop_live_session(session)
    assert stopped.data["started"] is False
    assert stopped.metadata.requires_network is False
