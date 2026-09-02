"""Executable usage demonstration harness for Runtime Configuration feature."""

from __future__ import annotations

import socket
import sqlite3
import tempfile
from pathlib import Path

from app.contracts.workspace.errors import SettingsValidationError
from app.contracts.workspace.models import (
    JobKind,
    ServerRuntimeSettings,
    StorageGuardLimits,
    WorkspaceSettings,
)
from app.services.workspace.runtime_configuration._persistence import (
    get_category_settings,
    get_setting,
    init_central_database,
    set_setting,
)
from app.services.workspace.runtime_configuration.runtime_configuration import (
    SUPPORT_PROFILE_VERSION,
    RuntimeConfigurationService,
    fr_ws_evaluate_runtime_resources,
)


def _create_fixture_workspace(root: Path) -> None:
    """Create a minimal initialized workspace for the usage harness.

    The harness must stay import-pure toward other features, so it creates
    only the two database tables this feature consumes.

    Args:
        root: Workspace root directory to create.
    """
    for sub in ("metadata", "artifacts/objects", "staging", "logs", "cache"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(root / "metadata" / "workspace.db"))
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workspace (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                row_version INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS workspace_setting_versions (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                settings_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                row_version INTEGER NOT NULL DEFAULT 1,
                UNIQUE(workspace_id, version)
            );
            INSERT INTO workspace (id, name, created_at, updated_at)
            VALUES ('usage-harness', 'Usage Harness', '2026-01-01T00:00:00Z',
                    '2026-01-01T00:00:00Z');
            """
        )
        conn.commit()
    finally:
        conn.close()


def _valid_settings() -> WorkspaceSettings:
    """Return a known-valid settings payload for harness scenarios.

    Returns:
        A valid WorkspaceSettings instance.
    """
    return WorkspaceSettings(
        timezone="UTC",
        locale="en-US",
        worker_count=4,
        worker_memory_mb=2048,
        max_artifact_size_mb=2048,
        max_total_artifact_gb=50,
    )


def _run_configure_workspace_scenario(
    service: RuntimeConfigurationService, ws_root: Path
) -> None:
    """Run the FR-WS-CONFIGURE_WORKSPACE usage scenario.

    Args:
        service: RuntimeConfigurationService instance.
        ws_root: Path to test workspace root.

    Raises:
        RuntimeError: If any scenario expectation fails.
    """
    print("Scenario 1: FR-WS-CONFIGURE_WORKSPACE")
    first = service.configure_workspace(ws_root, _valid_settings())
    print(f"  Persisted settings version: {first.version}")
    if first.version != 1:
        msg = "expected first settings version to be 1"
        raise RuntimeError(msg)
    invalid = WorkspaceSettings(
        timezone="Not/AZone",
        locale="en US",
        worker_count=0,
        worker_memory_mb=-1,
        max_artifact_size_mb=10,
        max_total_artifact_gb=10,
        artifacts_dir="../escape",
    )
    try:
        service.configure_workspace(ws_root, invalid)
    except SettingsValidationError as exc:
        print(f"  Invalid payload rejected with {len(exc.field_errors)} field errors")
        latest = service.get_workspace_settings(ws_root)
        if latest is None or latest.version != 1:
            msg = "invalid payload must not increment the settings version"
            raise RuntimeError(msg) from exc
    else:
        msg = "expected SettingsValidationError for invalid payload"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-CONFIGURE_WORKSPACE passed.\n")


def _run_storage_guards_scenario(
    service: RuntimeConfigurationService, ws_root: Path
) -> None:
    """Run the FR-WS-ENFORCE_STORAGE_GUARDS usage scenario.

    Args:
        service: RuntimeConfigurationService instance.
        ws_root: Path to test workspace root.

    Raises:
        RuntimeError: If any scenario expectation fails.
    """
    print("Scenario 2: FR-WS-ENFORCE_STORAGE_GUARDS")
    admitted = service.enforce_storage_guards(
        ws_root,
        job_kind=JobKind.BACKTEST,
        projected_artifact_mb=10.0,
        limits=StorageGuardLimits(
            min_free_space_mb=1,
            max_artifact_size_mb=4096,
        ),
    )
    print(
        f"  Backtest admitted: {admitted.admitted} "
        f"(required {admitted.required_mb:.1f} MiB / "
        f"available {admitted.available_mb:.1f} MiB)"
    )
    if not admitted.admitted:
        msg = "expected small backtest to be admitted"
        raise RuntimeError(msg)
    rejected = service.enforce_storage_guards(
        ws_root,
        job_kind=JobKind.DATA_IMPORT,
        projected_artifact_mb=50.0,
        limits=StorageGuardLimits(
            min_free_space_mb=1,
            max_artifact_size_mb=10,
        ),
    )
    print(f"  Oversized import rejected: {rejected.reason}")
    if rejected.admitted or "ARTIFACT_SIZE_LIMIT" not in rejected.reason:
        msg = "expected over-limit import to be rejected with size reason"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-ENFORCE_STORAGE_GUARDS passed.\n")


def _run_server_runtime_scenario(
    service: RuntimeConfigurationService,
) -> None:
    """Run the FR-WS-CONFIGURE_SERVER_RUNTIME usage scenario.

    Args:
        service: RuntimeConfigurationService instance.

    Raises:
        RuntimeError: If any scenario expectation fails.
    """
    print("Scenario 3: FR-WS-CONFIGURE_SERVER_RUNTIME")
    probe_port = 48765
    valid = service.configure_server_runtime(
        ServerRuntimeSettings(port=probe_port, headless=True)
    )
    print(
        f"  Headless loopback runtime valid: {valid.valid} "
        f"(port available: {valid.port_available})"
    )
    if not valid.valid or not valid.port_available:
        msg = f"expected valid loopback runtime: {valid.errors}"
        raise RuntimeError(msg)
    bad = service.configure_server_runtime(
        ServerRuntimeSettings(
            port=70000,
            bind_address="10.0.0.5",
            allow_non_loopback=False,
        )
    )
    print(f"  Invalid runtime rejected with {len(bad.errors)} errors")
    min_expected_errors = 2
    if bad.valid or len(bad.errors) < min_expected_errors:
        msg = "expected port and non-loopback opt-in errors"
        raise RuntimeError(msg)
    occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        occupied.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        occupied.bind(("127.0.0.1", probe_port))
        occupied.listen(1)
        unavailable = service.configure_server_runtime(
            ServerRuntimeSettings(port=probe_port)
        )
    finally:
        occupied.close()
    print(f"  Occupied port available: {unavailable.port_available}")
    if unavailable.valid or unavailable.port_available:
        msg = "expected occupied port to fail before launch"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-CONFIGURE_SERVER_RUNTIME passed.\n")


def _run_support_profile_scenario(
    service: RuntimeConfigurationService, ws_root: Path
) -> None:
    """Run the FR-WS-PUBLISH_RUNTIME_SUPPORT usage scenario.

    Args:
        service: RuntimeConfigurationService instance.
        ws_root: Path to test workspace root.

    Raises:
        RuntimeError: If any scenario expectation fails.
    """
    print("Scenario 4: FR-WS-PUBLISH_RUNTIME_SUPPORT")
    profile = service.publish_runtime_support()
    print(
        f"  Profile v{profile.profile_version}: "
        f"os={profile.os_families} arch={profile.architectures}"
    )
    if profile.profile_version != SUPPORT_PROFILE_VERSION:
        msg = "expected current support profile version"
        raise RuntimeError(msg)
    report = fr_ws_evaluate_runtime_resources(profile, workspace_root=ws_root)
    for warning in report.warnings:
        print(f"  below-recommended: {warning}")
    print("  [OK] FR-WS-PUBLISH_RUNTIME_SUPPORT passed.\n")


def _run_central_settings_scenario(temp_dir: Path) -> None:
    """Run the central database settings usage scenario.

    Args:
        temp_dir: Temporary directory for testing database.
    """
    print("Scenario 5: Central Database Settings Store")
    db_file = temp_dir / "usage_settings.db"
    init_central_database(db_file)
    app_name = get_setting("system.app_name", db_path=db_file)
    print(f"  Read default app name: {app_name}")
    set_setting(
        "system.app_name", "haruquant-custom", changed_by="demo", db_path=db_file
    )
    updated = get_setting("system.app_name", db_path=db_file)
    print(f"  Updated app name: {updated}")
    ai_settings = get_category_settings("ai", db_path=db_file)
    print(f"  AI Category settings count: {len(ai_settings)}")
    print("  [OK] Central Database Settings Store passed.\n")


def run_usage_scenarios() -> None:
    """Execute all functional requirement and database usage scenarios."""
    print("Executing Runtime Configuration (__main__) usage scenarios...\n")
    service = RuntimeConfigurationService()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        ws_root = temp_path / "harness_workspace"
        _create_fixture_workspace(ws_root)
        _run_configure_workspace_scenario(service, ws_root)
        _run_storage_guards_scenario(service, ws_root)
        _run_server_runtime_scenario(service)
        _run_support_profile_scenario(service, ws_root)
        _run_central_settings_scenario(temp_path)

    print("[SUCCESS] All Runtime Configuration usage scenarios passed!")


if __name__ == "__main__":
    run_usage_scenarios()
