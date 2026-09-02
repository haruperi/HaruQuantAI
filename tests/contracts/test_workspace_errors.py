"""Unit tests for workspace error hierarchy and wire failure models."""

from __future__ import annotations

from app.contracts.common.models import ProblemDetails
from app.contracts.workspace.errors import (
    WIRE_FAILURES,
    DiagnosticBundleError,
    LocalSessionError,
    NonLoopbackAccessDeniedError,
    ServerRuntimeValidationError,
    SessionDeniedError,
    SessionExpiredError,
    SettingsValidationError,
    SystemNotReadyError,
    UnsupportedRuntimeError,
    WorkspaceAlreadyOpenError,
    WorkspaceCorruptionError,
    WorkspaceError,
    WorkspaceFailure,
    WorkspaceMigrationError,
    WorkspaceNotFoundError,
    WorkspaceStorageError,
)


def test_workspace_errors_hierarchy() -> None:
    """Verify workspace error classes format messages and attributes properly."""
    e1 = WorkspaceError("base error", error_code="BASE_CODE")
    assert e1.error_code == "BASE_CODE"
    assert "[BASE_CODE] base error" in str(e1)

    e2 = WorkspaceAlreadyOpenError(holder_pid=1234, lock_file="/path/lock")
    assert e2.error_code == "WORKSPACE_ALREADY_OPEN"
    assert e2.holder_pid == 1234
    assert e2.lock_file == "/path/lock"
    assert "holder_pid=1234" in str(e2)

    e2_plain = WorkspaceAlreadyOpenError()
    assert "Workspace is already opened" in str(e2_plain)

    e3 = WorkspaceNotFoundError("/data/ws")
    assert e3.error_code == "WORKSPACE_NOT_FOUND"

    e4 = WorkspaceCorruptionError("checksum mismatch")
    assert e4.error_code == "WORKSPACE_CORRUPTED"

    e5 = WorkspaceMigrationError("failed table creation", version=3)
    assert e5.error_code == "WORKSPACE_MIGRATION_FAILED"
    assert e5.version == 3

    e5_no_ver = WorkspaceMigrationError("unversioned migration failed")
    assert "unversioned migration failed" in str(e5_no_ver)

    e6 = WorkspaceStorageError("disk full")
    assert e6.error_code == "WORKSPACE_STORAGE_ERROR"

    e7 = SettingsValidationError({"theme": "invalid color", "timeout": "must be > 0"})
    assert e7.error_code == "SETTINGS_VALIDATION_FAILED"
    assert e7.field_errors == {"theme": "invalid color", "timeout": "must be > 0"}

    e8 = ServerRuntimeValidationError(("port in use", "invalid host"))
    assert e8.error_code == "SERVER_RUNTIME_INVALID"
    assert e8.errors == ("port in use", "invalid host")

    e9 = UnsupportedRuntimeError("ARM32 architecture not supported")
    assert e9.error_code == "RUNTIME_UNSUPPORTED"

    e10 = LocalSessionError("auth failed", error_code="AUTH_FAIL")
    assert e10.error_code == "AUTH_FAIL"

    e11 = SessionDeniedError("Forbidden", reason="bad token")
    assert e11.error_code == "SESSION_DENIED"

    e11_plain = SessionDeniedError()
    assert "Session access denied" in str(e11_plain)

    e12 = SessionExpiredError("Token expired", expired_at="2026-09-01T12:00:00Z")
    assert e12.error_code == "SESSION_EXPIRED"

    e12_plain = SessionExpiredError()
    assert "Local session has expired" in str(e12_plain)

    e13 = NonLoopbackAccessDeniedError("192.168.1.100")
    assert e13.error_code == "NON_LOOPBACK_ACCESS_DENIED"
    assert e13.client_host == "192.168.1.100"

    e14 = SystemNotReadyError(("database starting", "worker registering"))
    assert e14.error_code == "SYSTEM_NOT_READY"
    assert e14.reasons == ("database starting", "worker registering")

    e15 = DiagnosticBundleError("tar write error", error_code="DIAG_TAR_ERR")
    assert e15.error_code == "DIAG_TAR_ERR"


def test_workspace_failure_wire_model() -> None:
    """Verify WorkspaceFailure WireModel structure and WIRE_FAILURES map."""
    assert WIRE_FAILURES["WorkspaceFailure"] == WorkspaceFailure

    problem = ProblemDetails(
        type="urn:error:workspace:not_found",
        title="Workspace Not Found",
        status=404,
        detail="Workspace path does not exist",
    )
    failure = WorkspaceFailure(
        request_id="01918a99-0000-7000-8000-000000000002",
        code="WORKSPACE_NOT_FOUND",
        problem=problem,
    )
    assert failure.outcome == "FAILURE"
    assert failure.code == "WORKSPACE_NOT_FOUND"
    assert failure.schema_version == 1
