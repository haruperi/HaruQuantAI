"""Unit tests for FEAT-WS-SECURE_LOCAL_ACCESS (Local Access and Health)."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.contracts.workspace.errors import (
    NonLoopbackAccessDeniedError,
    SessionDeniedError,
    SessionExpiredError,
)
from app.contracts.workspace.models import (
    HealthStatus,
    LocalSession,
    SystemHealth,
    SystemReadiness,
    WorkspaceRef,
    WorkspaceStatus,
)
from app.services.workspace.local_access_health.local_access_health import (
    BUILD_COMMIT,
    BUILD_VERSION,
    LocalAccessHealthService,
)
from app.services.workspace.workspace_lifecycle.workspace_lifecycle import (
    WorkspaceLifecycleService,
)


@pytest.fixture
def service() -> LocalAccessHealthService:
    """Fixture providing a fresh LocalAccessHealthService instance."""
    return LocalAccessHealthService()


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """Fixture providing an initialized workspace root."""
    lifecycle = WorkspaceLifecycleService()
    ref = lifecycle.initialize_workspace(
        tmp_path / "unit_ws",
        name="Local Access Test WS",
    )
    return ref.root_path


def test_ws_issue_local_session(service: LocalAccessHealthService) -> None:
    """Test FR-WS-ISSUE_LOCAL_SESSION: Token issuance, loopback binding, verification, expiry, and revocation."""
    # 1. Valid issuance on loopback addresses
    for host in ("127.0.0.1", "localhost", "::1", "127.0.0.2"):
        session = service.issue_local_session(
            client_id=f"client-{host}",
            is_launcher_connected=True,
            client_host=host,
            ttl_seconds=3600,
        )
        assert isinstance(session, LocalSession)
        assert session.session_id
        assert len(session.token) >= 32
        assert session.is_loopback is True
        assert session.is_launcher_connected is True
        assert session.client_id == f"client-{host}"

        # Verification on loopback succeeds
        verified = service.verify_local_session(
            token=session.token,
            client_host=host,
        )
        assert verified.session_id == session.session_id
        assert verified.token == session.token

    # 2. Deny non-launcher-connected caller
    with pytest.raises(SessionDeniedError) as exc_launcher:
        service.issue_local_session(
            client_id="external-app",
            is_launcher_connected=False,
            client_host="127.0.0.1",
        )
    assert exc_launcher.value.error_code == "SESSION_DENIED"

    # 3. Deny non-loopback issuance by default
    with pytest.raises(NonLoopbackAccessDeniedError) as exc_host:
        service.issue_local_session(
            client_id="remote-launcher",
            is_launcher_connected=True,
            client_host="192.168.1.100",
        )
    assert exc_host.value.error_code == "NON_LOOPBACK_ACCESS_DENIED"
    assert exc_host.value.client_host == "192.168.1.100"

    # 4. Deny verification from non-loopback address
    valid_session = service.issue_local_session(
        client_id="launcher-valid",
        is_launcher_connected=True,
        client_host="127.0.0.1",
    )
    with pytest.raises(NonLoopbackAccessDeniedError):
        service.verify_local_session(
            token=valid_session.token,
            client_host="10.0.0.5",
        )

    # 5. Deny unknown/invalid token
    with pytest.raises(SessionDeniedError) as exc_unknown:
        service.verify_local_session(
            token="invalid-token-value-12345",
            client_host="127.0.0.1",
        )
    assert exc_unknown.value.error_code == "SESSION_DENIED"

    # 6. Immediate revocation
    service.revoke_local_session(valid_session.token)
    with pytest.raises(SessionDeniedError):
        service.verify_local_session(
            token=valid_session.token,
            client_host="127.0.0.1",
        )

    # 7. Expiration
    expired_session = service.issue_local_session(
        client_id="launcher-short",
        is_launcher_connected=True,
        client_host="127.0.0.1",
        ttl_seconds=-1,
    )
    with pytest.raises(SessionExpiredError) as exc_expired:
        service.verify_local_session(
            token=expired_session.token,
            client_host="127.0.0.1",
        )
    assert exc_expired.value.error_code == "SESSION_EXPIRED"


def test_ws_report_system_readiness(
    service: LocalAccessHealthService,
    workspace_root: Path,
) -> None:
    """Test FR-WS-REPORT_SYSTEM_READINESS: Health, readiness, redaction, and secret omission."""
    # 1. Health check works before full readiness
    health = service.check_system_health()
    assert isinstance(health, SystemHealth)
    assert health.status == HealthStatus.HEALTHY
    assert health.healthy is True
    assert health.checked_at
    assert "runtime" in health.components
    assert "session_vault" in health.components
    assert "storage" in health.components

    # 2. Readiness when no workspace is loaded
    unloaded = service.report_system_readiness(workspace=None)
    assert isinstance(unloaded, SystemReadiness)
    assert unloaded.ready is False
    assert unloaded.healthy is True
    assert unloaded.build_version == BUILD_VERSION
    assert unloaded.build_commit == BUILD_COMMIT
    assert unloaded.schema_version is None
    assert unloaded.migrations_current is False
    assert any("NO_WORKSPACE_LOADED" in r for r in unloaded.reasons)

    # 3. Readiness on uninitialized / missing path
    missing = service.report_system_readiness(workspace=workspace_root / "nonexistent")
    assert missing.ready is False
    assert any("WORKSPACE_UNINITIALIZED" in r for r in missing.reasons)

    # 4. Readiness on initialized and migrated workspace
    ref = WorkspaceRef(
        workspace_id="test-ws-uuid",
        name="Local Access Test WS",
        root_path=workspace_root,
        status=WorkspaceStatus.READY,
        created_at="2026-01-01T00:00:00Z",
    )
    ready_status = service.report_system_readiness(workspace=ref)
    assert ready_status.ready is True
    assert ready_status.healthy is True
    assert ready_status.schema_version == 1
    assert ready_status.migrations_current is True
    assert ready_status.state_recovered is True
    assert ready_status.worker_capacity >= 1
    assert ready_status.checked_at

    # 5. Verify no secrets or absolute paths are disclosed in reasons
    # Issue a secret session token and ensure it never leaks
    secret_session = service.issue_local_session(
        client_id="launcher-sec",
        is_launcher_connected=True,
    )
    reasons_dump = " ".join(ready_status.reasons)
    assert workspace_root.as_posix() not in reasons_dump
    assert str(workspace_root) not in reasons_dump
    assert secret_session.token not in reasons_dump

    # 6. Database error handling
    # Corrupt the metadata database to verify failure isolation
    corrupt_ws = workspace_root.parent / "corrupt_ws"
    corrupt_meta = corrupt_ws / "metadata"
    corrupt_meta.mkdir(parents=True, exist_ok=True)
    (corrupt_meta / "workspace.db").write_text("not a valid sqlite database")

    corrupt_status = service.report_system_readiness(workspace=corrupt_ws)
    assert corrupt_status.ready is False
    assert corrupt_status.healthy is False
    assert any("DATABASE_ACCESS_ERROR" in r for r in corrupt_status.reasons)
    # Ensure raw user paths are not leaked in the database error reason
    corrupt_reasons_dump = " ".join(corrupt_status.reasons)
    assert corrupt_ws.as_posix() not in corrupt_reasons_dump


def test_local_access_health_usage_example() -> None:
    """Verify the __main__ usage scenarios run successfully."""
    from app.services.workspace.local_access_health.local_access_health import (
        _run_usage_example,
    )

    _run_usage_example()
