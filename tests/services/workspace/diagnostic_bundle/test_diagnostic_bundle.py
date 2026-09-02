"""Unit tests for DiagnosticBundleService and FR-WS-BUILD_DIAGNOSTIC_BUNDLE."""

from __future__ import annotations

import sqlite3
import zipfile
from pathlib import Path

from app.contracts.workspace.models import WorkspaceRef
from app.services.workspace.diagnostic_bundle.config import (
    DiagnosticBundleConfig,
)
from app.services.workspace.diagnostic_bundle.diagnostic_bundle import (
    DiagnosticBundleService,
    _redact_data,
    _redact_text,
    fr_ws_build_diagnostic_bundle,
)


def _setup_test_workspace(root: Path) -> WorkspaceRef:
    """Create a fully-formed workspace directory and database for tests."""
    for sub in (
        "metadata",
        "logs",
        "staging",
        "cache",
        "exports",
        "artifacts/objects",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)

    db_path = root / "metadata" / "workspace.db"
    conn = sqlite3.connect(str(db_path))
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
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                checksum TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            INSERT INTO workspace (id, name, created_at, updated_at)
            VALUES ('test-ws-id', 'Test WS', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
            INSERT INTO schema_migrations (version, name, applied_at, checksum)
            VALUES (1, 'initial_schema', '2026-01-01T00:00:00Z', 'chk1');
            INSERT INTO jobs (id, kind, status, created_at, updated_at)
            VALUES ('job-100', 'BACKTEST', 'COMPLETED', '2026-01-01T00:00:00Z', '2026-01-01T00:01:00Z');
            """
        )
        conn.commit()
    finally:
        conn.close()

    log_file = root / "logs" / "engine.log"
    log_file.write_text(
        f"2026-01-01T00:00:00Z INFO Started at {root.as_posix()}\n"
        "2026-01-01T00:00:01Z DEBUG secret_token=abracadabra123456\n"
        "2026-01-01T00:00:02Z INFO Completed\n",
        encoding="utf-8",
    )

    return WorkspaceRef(
        workspace_id="test-ws-id",
        name="Test WS",
        root_path=root,
    )


def test_ws_build_diagnostic_bundle(tmp_path: Path) -> None:
    """Verify FR-WS-BUILD_DIAGNOSTIC_BUNDLE end-to-end functionality."""
    ws_root = tmp_path / "ws_target"
    ws_ref = _setup_test_workspace(ws_root)

    service = DiagnosticBundleService()
    bundle = service.build_diagnostic_bundle(
        workspace=ws_ref,
        include_logs=True,
    )

    assert bundle.bundle_id == bundle.manifest.bundle_id
    assert bundle.archive_path.is_file()
    assert bundle.file_size_bytes > 0
    assert len(bundle.checksum_sha256) == 64
    assert bundle.manifest.schema_version == 1
    assert bundle.manifest.workspace_id == "test-ws-id"
    assert bundle.manifest.log_entries_count == 3
    assert bundle.manifest.job_records_count == 1
    assert len(bundle.manifest.integrity_findings) == 0

    with zipfile.ZipFile(bundle.archive_path, "r") as zf:
        members = set(zf.namelist())
        assert {
            "manifest.json",
            "versions.json",
            "configuration.json",
            "job_states.json",
            "integrity.json",
            "recent_logs.jsonl",
        }.issubset(members)

        logs = zf.read("recent_logs.jsonl").decode("utf-8")
        assert ws_root.as_posix() not in logs
        assert "abracadabra123456" not in logs
        assert "[REDACTED_PATH]" in logs
        assert "[REDACTED_SECRET]" in logs


def test_diagnostic_bundle_custom_output_path(tmp_path: Path) -> None:
    """Verify bundle output to custom destination directory."""
    ws_root = tmp_path / "ws_custom"
    ws_ref = _setup_test_workspace(ws_root)

    custom_out = tmp_path / "custom_exports" / "my_bundle.zip"
    service = DiagnosticBundleService()
    bundle = service.build_diagnostic_bundle(
        workspace=ws_ref,
        output_path=custom_out,
    )

    assert bundle.archive_path == custom_out
    assert custom_out.is_file()


def test_diagnostic_bundle_missing_workspace(tmp_path: Path) -> None:
    """Verify bundle creation with nonexistent workspace path."""
    non_existent = tmp_path / "no_such_ws"
    bundle = fr_ws_build_diagnostic_bundle(workspace=non_existent)

    assert bundle.archive_path.is_file()
    assert "WORKSPACE_ROOT_NOT_DIRECTORY" in bundle.manifest.integrity_findings


def test_diagnostic_bundle_corrupt_database(tmp_path: Path) -> None:
    """Verify integrity findings when database is invalid."""
    ws_root = tmp_path / "ws_corrupt"
    for sub in ("metadata", "logs", "staging", "cache", "artifacts/objects"):
        (ws_root / sub).mkdir(parents=True, exist_ok=True)

    db_path = ws_root / "metadata" / "workspace.db"
    db_path.write_text("not a valid sqlite file", encoding="utf-8")

    bundle = fr_ws_build_diagnostic_bundle(workspace=ws_root)
    assert any("DATABASE" in f for f in bundle.manifest.integrity_findings)


def test_diagnostic_bundle_exclude_logs(tmp_path: Path) -> None:
    """Verify include_logs=False excludes recent logs."""
    ws_root = tmp_path / "ws_nologs"
    ws_ref = _setup_test_workspace(ws_root)

    cfg = DiagnosticBundleConfig()
    bundle = fr_ws_build_diagnostic_bundle(
        workspace=ws_ref,
        include_logs=False,
        config=cfg,
    )

    assert bundle.manifest.log_entries_count == 0


def test_redaction_helpers() -> None:
    """Verify _redact_text and _redact_data sanitize sensitive content."""
    sample_text = (
        "User at C:\\Users\\Administrator\\AppData\\Local\\Temp and "
        "/home/ubuntu/secret.key with api_key: secret_abc_123 and "
        "Bearer eyJhbGciOiJIUzI1NiJ9"
    )
    redacted, count = _redact_text(sample_text)
    assert count >= 3
    assert "Administrator" not in redacted
    assert "/home/ubuntu" not in redacted
    assert "secret_abc_123" not in redacted
    assert "eyJhbGciOiJIUzI1NiJ9" not in redacted

    data = {
        "auth_token": "supersecret123",  # pragma: allowlist secret
        "nested": {
            "password": "mypassword",  # pragma: allowlist secret
            "file": "C:\\Users\\Bob\\data.csv",
        },
        "items": ["token=abc999", "normal_value"],  # pragma: allowlist secret
    }

    red_data, r_count = _redact_data(data)
    assert r_count >= 3
    assert isinstance(red_data, dict)
    assert red_data["auth_token"] == "[REDACTED_SECRET]"
    assert isinstance(red_data["nested"], dict)
    assert red_data["nested"]["password"] == "[REDACTED_SECRET]"


def test_diagnostic_bundle_usage_example() -> None:
    """Verify the __main__ usage scenarios run successfully."""
    from app.services.workspace.diagnostic_bundle.diagnostic_bundle import (
        _run_usage_example,
    )

    _run_usage_example()
