"""Integration test for WF-WS-004 (Diagnostics Workflow)."""

from __future__ import annotations

import zipfile
from pathlib import Path

from app.contracts.workspace.models import WorkspaceSettings
from app.services.workspace.diagnostic_bundle.diagnostic_bundle import (
    DiagnosticBundleService,
)
from app.services.workspace.local_access_health.local_access_health import (
    LocalAccessHealthService,
)
from app.services.workspace.runtime_configuration.runtime_configuration import (
    RuntimeConfigurationService,
)
from app.services.workspace.workspace_lifecycle.workspace_lifecycle import (
    WorkspaceLifecycleService,
)


def test_wf_ws_004_diagnostics_integration(tmp_path: Path) -> None:
    """Verify WF-WS-004 end-to-end integration workflow.

    Workflow Sequence:
        1. Initialize workspace with schema migrations.
        2. Configure workspace runtime settings.
        3. Issue local access session and record system readiness.
        4. Trigger diagnostic bundle generation.
        5. Verify exported bundle integrity, checksum, and zero secret disclosure.
    """
    ws_root = tmp_path / "integrated_ws"
    lifecycle_service = WorkspaceLifecycleService()
    runtime_service = RuntimeConfigurationService()
    health_service = LocalAccessHealthService(
        manage_workspaces=lifecycle_service,
    )
    diagnostics_service = DiagnosticBundleService(
        manage_workspaces=lifecycle_service,
        configure_runtime=runtime_service,
        secure_local_access=health_service,
    )

    # 1. Initialize workspace
    ws_ref = lifecycle_service.initialize_workspace(
        ws_root,
        name="Integrated Diagnostic Test WS",
    )
    assert ws_ref.root_path.is_dir()

    # 2. Configure workspace runtime settings
    settings = WorkspaceSettings(
        timezone="UTC",
        locale="en_US",
        worker_count=4,
        worker_memory_mb=1024,
        max_artifact_size_mb=128,
        max_total_artifact_gb=10,
    )
    runtime_service.configure_workspace(ws_ref, settings)

    # 3. Issue local session and check readiness
    session = health_service.issue_local_session(
        client_id="test_launcher",
        client_host="127.0.0.1",
        is_launcher_connected=True,
        ttl_seconds=3600,
    )

    readiness = health_service.report_system_readiness(ws_ref)
    assert readiness.ready is True
    assert readiness.healthy is True

    # Add log entry with session token
    log_file = ws_root / "logs" / "session.log"
    log_file.write_text(
        f"2026-01-01T12:00:00Z INFO Session issued: token={session.token}\n"
        f"2026-01-01T12:00:01Z INFO Working directory: {ws_root.as_posix()}\n",
        encoding="utf-8",
    )

    # 4. Generate diagnostic bundle
    bundle_ref = diagnostics_service.build_diagnostic_bundle(
        workspace=ws_ref,
        include_logs=True,
    )

    # 5. Verify bundle artifact and manifest
    assert bundle_ref.archive_path.is_file()
    assert bundle_ref.file_size_bytes > 0
    assert len(bundle_ref.checksum_sha256) == 64
    assert bundle_ref.manifest.workspace_id == ws_ref.workspace_id
    assert bundle_ref.manifest.log_entries_count == 2
    assert len(bundle_ref.manifest.integrity_findings) == 0

    # Unpack and verify zero leakage
    with zipfile.ZipFile(bundle_ref.archive_path, "r") as zf:
        logs_str = zf.read("recent_logs.jsonl").decode("utf-8")
        assert session.token not in logs_str
        assert ws_root.as_posix() not in logs_str
        assert "[REDACTED_SECRET]" in logs_str
        assert "[REDACTED_PATH]" in logs_str
