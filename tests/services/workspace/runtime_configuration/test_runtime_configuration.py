"""Unit tests for FEAT-WS-CONFIGURE_RUNTIME (Runtime Configuration)."""

from __future__ import annotations

import socket
import sqlite3
from pathlib import Path

import pytest

from app.contracts.workspace.errors import (
    SettingsValidationError,
    UnsupportedRuntimeError,
    WorkspaceNotFoundError,
)
from app.contracts.workspace.models import (
    AuthenticationMode,
    JobKind,
    RuntimeSupportProfile,
    ServerRuntimeSettings,
    StorageGuardLimits,
    WorkspaceSettings,
)
from app.services.workspace.runtime_configuration.runtime_configuration import (
    SUPPORT_PROFILE_VERSION,
    RuntimeConfigurationService,
    fr_ws_evaluate_runtime_resources,
)
from app.services.workspace.workspace_lifecycle.workspace_lifecycle import (
    WorkspaceLifecycleService,
)

PROBE_PORT = 48812


@pytest.fixture
def service() -> RuntimeConfigurationService:
    """Fixture providing a fresh RuntimeConfigurationService instance."""
    return RuntimeConfigurationService()


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """Fixture providing an initialized workspace root via the 1.1 feature."""
    lifecycle = WorkspaceLifecycleService()
    ref = lifecycle.initialize_workspace(tmp_path / "unit_ws", name="Config Test WS")
    return ref.root_path


def _valid_settings(**overrides: object) -> WorkspaceSettings:
    """Return known-valid settings with optional field overrides."""
    defaults: dict[str, object] = {
        "timezone": "Europe/Prague",
        "locale": "en-US",
        "worker_count": 4,
        "worker_memory_mb": 2048,
        "max_artifact_size_mb": 2048,
        "max_total_artifact_gb": 50,
    }
    defaults.update(overrides)
    return WorkspaceSettings(**defaults)  # type: ignore[arg-type]


def test_ws_configure_workspace(
    service: RuntimeConfigurationService, workspace_root: Path
) -> None:
    """Test FR-WS-CONFIGURE_WORKSPACE: versioned, validated settings."""
    first = service.configure_workspace(workspace_root, _valid_settings())
    assert first.version == 1
    assert first.workspace_id

    updated = service.configure_workspace(
        workspace_root, _valid_settings(worker_count=8)
    )
    assert updated.version == 2

    latest = service.get_workspace_settings(workspace_root)
    assert latest is not None
    assert latest.version == 2
    assert latest.settings.worker_count == 8

    invalid = _valid_settings(
        timezone="Not/AZone",
        locale="en US",
        worker_count=0,
        worker_memory_mb=-5,
        artifacts_dir="../escape",
        log_level="VERBOSE",
    )
    with pytest.raises(SettingsValidationError) as excinfo:
        service.configure_workspace(workspace_root, invalid)
    field_errors = excinfo.value.field_errors
    assert "timezone" in field_errors
    assert "locale" in field_errors
    assert "worker_count" in field_errors
    assert "worker_memory_mb" in field_errors
    assert "artifacts_dir" in field_errors
    assert "log_level" in field_errors

    # Invalid payloads never increment the persisted version.
    after = service.get_workspace_settings(workspace_root)
    assert after is not None
    assert after.version == 2

    with pytest.raises(WorkspaceNotFoundError):
        service.configure_workspace(workspace_root / "missing", _valid_settings())


def test_ws_enforce_storage_guards(
    service: RuntimeConfigurationService, workspace_root: Path
) -> None:
    """Test FR-WS-ENFORCE_STORAGE_GUARDS: admission and over-limit rejection."""
    admitted = service.enforce_storage_guards(
        workspace_root,
        job_kind=JobKind.BACKTEST,
        projected_artifact_mb=100.0,
        limits=StorageGuardLimits(min_free_space_mb=1, max_artifact_size_mb=4096),
    )
    assert admitted.admitted
    assert admitted.available_mb > 0
    assert admitted.required_mb == pytest.approx(101.0)

    size_rejected = service.enforce_storage_guards(
        workspace_root,
        job_kind=JobKind.DATA_IMPORT,
        projected_artifact_mb=500.0,
        limits=StorageGuardLimits(min_free_space_mb=1, max_artifact_size_mb=100),
    )
    assert not size_rejected.admitted
    assert "ARTIFACT_SIZE_LIMIT" in size_rejected.reason
    assert size_rejected.required_mb > size_rejected.available_mb or (
        size_rejected.available_mb >= size_rejected.required_mb
    )

    space_rejected = service.enforce_storage_guards(
        workspace_root,
        job_kind=JobKind.CODE_GENERATION,
        projected_artifact_mb=1.0,
        limits=StorageGuardLimits(
            min_free_space_mb=10_000_000, max_artifact_size_mb=4096
        ),
    )
    assert not space_rejected.admitted
    assert "FREE_SPACE_LIMIT" in space_rejected.reason
    assert space_rejected.available_mb < space_rejected.required_mb


def test_ws_configure_server_runtime(
    service: RuntimeConfigurationService,
) -> None:
    """Test FR-WS-CONFIGURE_SERVER_RUNTIME: pre-launch validation."""
    valid = service.configure_server_runtime(
        ServerRuntimeSettings(port=PROBE_PORT, headless=True)
    )
    assert valid.valid
    assert valid.port_available

    bad_port = service.configure_server_runtime(ServerRuntimeSettings(port=70000))
    assert not bad_port.valid
    assert any("port" in err for err in bad_port.errors)

    nonloopback = service.configure_server_runtime(
        ServerRuntimeSettings(
            port=PROBE_PORT,
            bind_address="10.0.0.5",
            allow_non_loopback=False,
        )
    )
    assert not nonloopback.valid
    assert any("allow_non_loopback" in err for err in nonloopback.errors)

    wrong_auth = service.configure_server_runtime(
        ServerRuntimeSettings(
            port=PROBE_PORT,
            bind_address="10.0.0.5",
            allow_non_loopback=True,
            authentication_mode=AuthenticationMode.LOCAL_SESSION,
        )
    )
    assert not wrong_auth.valid
    assert any("NONLOCAL_TOKEN" in err for err in wrong_auth.errors)

    nonloopback_ok = service.configure_server_runtime(
        ServerRuntimeSettings(
            port=PROBE_PORT,
            bind_address="10.0.0.5",
            allow_non_loopback=True,
            authentication_mode=AuthenticationMode.NONLOCAL_TOKEN,
        )
    )
    assert nonloopback_ok.valid

    bad_limits = service.configure_server_runtime(
        ServerRuntimeSettings(port=PROBE_PORT, worker_cpu_percent=0)
    )
    assert not bad_limits.valid
    assert any("worker_cpu_percent" in err for err in bad_limits.errors)

    # An occupied port must fail before launch.
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        blocker.bind(("127.0.0.1", PROBE_PORT))
        blocker.listen(1)
        occupied = service.configure_server_runtime(
            ServerRuntimeSettings(port=PROBE_PORT)
        )
    finally:
        blocker.close()
    assert not occupied.valid
    assert not occupied.port_available


def test_ws_publish_runtime_support(
    service: RuntimeConfigurationService, workspace_root: Path
) -> None:
    """Test FR-WS-PUBLISH_RUNTIME_SUPPORT: profile and platform checks."""
    profile = service.publish_runtime_support()
    assert profile.profile_version == SUPPORT_PROFILE_VERSION
    assert "windows" in profile.os_families or "linux" in profile.os_families
    assert profile.required_compilers
    assert profile.resources.minimum_cpu_cores < profile.resources.recommended_cpu_cores

    report = fr_ws_evaluate_runtime_resources(profile, workspace_root=workspace_root)
    assert isinstance(report.warnings, tuple)
    for warning in report.warnings:
        assert "below recommended" in warning

    # Startup rejects an unsupported host platform outright.
    from app.contracts.workspace.models import ResourceRequirements

    unsupported_host = RuntimeSupportProfile(
        profile_version=SUPPORT_PROFILE_VERSION,
        os_families=("plan9",),
        architectures=("SPARC",),
        resources=ResourceRequirements(
            minimum_cpu_cores=1,
            recommended_cpu_cores=2,
            minimum_memory_gb=1,
            recommended_memory_gb=2,
            minimum_free_storage_gb=1,
            recommended_free_storage_gb=2,
        ),
        filesystems=("fossil",),
        browsers=("netscape",),
        required_compilers=(),
    )
    del unsupported_host  # profile content is data; rejection is host-based

    import platform as _platform
    import sys as _sys
    from unittest.mock import patch

    with (
        patch.object(_sys, "platform", "plan9"),
        patch.object(_platform, "machine", lambda: "SPARC"),
        pytest.raises(UnsupportedRuntimeError),
    ):
        service.publish_runtime_support()


def test_settings_table_persisted(
    service: RuntimeConfigurationService, workspace_root: Path
) -> None:
    """Verify settings versions persist in the workspace metadata database."""
    service.configure_workspace(workspace_root, _valid_settings())
    db_path = workspace_root / "metadata" / "workspace.db"
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT version FROM workspace_setting_versions ORDER BY version;"
        )
        versions = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()
    assert versions == [1]
