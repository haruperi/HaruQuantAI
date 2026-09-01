"""Diagnostic Bundle domain logic and capability implementation.

Purpose:
    Produce a redacted diagnostic bundle containing versions, configuration shape,
    recent structured logs, job states, and integrity findings.

Key capabilities:
    * Capture application build versions, runtime platform, and schema version.
    * Export workspace configuration shape while omitting sensitive secret values.
    * Extract recent structured log entries with deterministic secret redaction.
    * Inspect database integrity and record directory validation findings.
    * Assemble findings into a verified, checksummed zip bundle archive.

Python API usage:
    from app.services.workspace.diagnostic_bundle.diagnostic_bundle import (
        DiagnosticBundleService,
    )
    service = DiagnosticBundleService()
    bundle_ref = service.build_diagnostic_bundle(workspace=workspace_ref)
    print(f"Created bundle at: {bundle_ref.archive_path}")

CLI usage:
    uv run python -m app.services.workspace.diagnostic_bundle.diagnostic_bundle
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import override
from uuid import uuid4

from app.contracts.workspace.errors import (
    DiagnosticBundleError,
    WorkspaceError,
)
from app.contracts.workspace.models import (
    DiagnosticBundleManifest,
    DiagnosticBundleRef,
    WorkspaceRef,
)
from app.contracts.workspace.ports import (
    BuildDiagnosticsCapability,
    ConfigureRuntimeCapability,
    ManageWorkspacesCapability,
    SecureLocalAccessCapability,
)
from app.services.workspace.diagnostic_bundle.config import (
    DiagnosticBundleConfig,
)

BUILD_VERSION = "0.1.0"
BUILD_COMMIT = "90b002c"


def _now_utc() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _redact_text(text: str) -> tuple[str, int]:
    """Sanitize strings by redacting absolute filesystem paths and secrets.

    Args:
        text: Raw text string.

    Returns:
        Tuple of (sanitized_text, count_of_redactions).
    """
    redaction_count = 0

    def _replace_path(match: re.Match[str]) -> str:
        _ = match
        nonlocal redaction_count
        redaction_count += 1
        return "[REDACTED_PATH]"

    def _replace_secret(match: re.Match[str]) -> str:
        _ = match
        nonlocal redaction_count
        redaction_count += 1
        return "[REDACTED_SECRET]"

    # Redact Windows absolute paths
    sanitized = re.sub(
        r"[a-zA-Z]:[/\\](?:Users|home|AppData|tmp|var|Local)[/\\][^\s;:,]+",
        _replace_path,
        text,
        flags=re.IGNORECASE,
    )
    # Redact Unix absolute paths
    sanitized = re.sub(
        r"/(?:Users|home|root|tmp|var)/[^\s;:,]+",
        _replace_path,
        sanitized,
    )
    # Redact explicit tokens, keys, secrets, passwords
    sanitized = re.sub(
        r"(?i)\b[a-z0-9_\-]*(?:token|secret|password|key|auth|cred|pwd)"
        r"[a-z0-9_\-]*\s*[:=]\s*[^\s,;'\"]+",
        _replace_secret,
        sanitized,
    )
    # Redact Bearer / Basic tokens
    sanitized = re.sub(
        r"(?i)\b(?:bearer|basic)\s+[a-zA-Z0-9_\-\.]+",
        _replace_secret,
        sanitized,
    )
    return sanitized, redaction_count


def _redact_data(data: object) -> tuple[object, int]:
    """Recursively redact dictionary or list structures.

    Args:
        data: Arbitrary serializable object.

    Returns:
        Tuple of (sanitized_data, count_of_redactions).
    """
    total_redactions = 0
    if isinstance(data, str):
        return _redact_text(data)
    if isinstance(data, dict):
        new_dict: dict[str, object] = {}
        for k, v in data.items():
            if any(
                secret_word in str(k).lower()
                for secret_word in ("secret", "token", "password", "key", "auth")
            ):
                new_dict[str(k)] = "[REDACTED_SECRET]"
                total_redactions += 1
            else:
                redacted_val, count = _redact_data(v)
                new_dict[str(k)] = redacted_val
                total_redactions += count
        return new_dict, total_redactions
    if isinstance(data, (list, tuple)):
        new_list: list[object] = []
        for item in data:
            redacted_item, count = _redact_data(item)
            new_list.append(redacted_item)
            total_redactions += count
        return (
            (tuple(new_list) if isinstance(data, tuple) else new_list),
            total_redactions,
        )
    return data, 0


def _collect_versions(created_at: str) -> tuple[dict[str, object], int]:
    """Collect runtime environment and build version metadata.

    Args:
        created_at: ISO 8601 UTC timestamp string.

    Returns:
        Tuple of (redacted_versions_dict, count_of_redactions).
    """
    versions_data = {
        "build_version": BUILD_VERSION,
        "build_commit": BUILD_COMMIT,
        "python_version": sys.version,
        "platform": sys.platform,
        "created_at": created_at,
    }
    redacted_data, count = _redact_data(versions_data)
    versions_dict = redacted_data if isinstance(redacted_data, dict) else {}
    return (
        {str(k): v for k, v in versions_dict.items()},
        count,
    )


def _check_db_integrity(conn: sqlite3.Connection) -> list[str]:
    """Verify SQLite database integrity.

    Args:
        conn: Open SQLite database connection.

    Returns:
        List of integrity finding strings if problems exist.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    if cursor.fetchall() != [("ok",)]:
        return ["DATABASE_CORRUPTION_DETECTED"]
    return []


def _read_db_schema_version(conn: sqlite3.Connection) -> tuple[int | None, list[str]]:
    """Read current schema version from schema_migrations table.

    Args:
        conn: Open SQLite database connection.

    Returns:
        Tuple of (schema_version_int_or_none, findings_list).
    """
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(version) FROM schema_migrations;")
        row = cursor.fetchone()
        if row and row[0] is not None:
            return int(row[0]), []
    except sqlite3.Error:
        return None, ["SCHEMA_MIGRATIONS_TABLE_MISSING"]
    return None, []


def _read_recent_jobs(conn: sqlite3.Connection) -> list[dict[str, object]]:
    """Read recent jobs from the jobs table if it exists.

    Args:
        conn: Open SQLite database connection.

    Returns:
        List of job records.
    """
    cursor = conn.cursor()
    job_states: list[dict[str, object]] = []
    try:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs';"
        )
        if cursor.fetchone():
            cursor.execute(
                "SELECT id, kind, status, created_at, updated_at "
                "FROM jobs ORDER BY updated_at DESC LIMIT 50;"
            )
            for j_row in cursor.fetchall():
                job_states.append(
                    {
                        "job_id": j_row[0],
                        "kind": j_row[1],
                        "status": j_row[2],
                        "created_at": j_row[3],
                        "updated_at": j_row[4],
                    }
                )
    except sqlite3.Error:
        pass
    return job_states


def _inspect_workspace_db(
    ws_root: Path,
) -> tuple[int | None, str | None, list[dict[str, object]], list[str]]:
    """Inspect workspace database for schema version, ID, and jobs.

    Args:
        ws_root: Workspace root directory path.

    Returns:
        Tuple of (schema_version, workspace_id, job_states, integrity_findings).
    """
    db_path = ws_root / "metadata" / "workspace.db"
    if not db_path.is_file():
        return None, None, [], ["DATABASE_FILE_MISSING: metadata/workspace.db"]

    findings: list[str] = []
    schema_version: int | None = None
    ws_id: str | None = None
    job_states: list[dict[str, object]] = []

    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        try:
            findings.extend(_check_db_integrity(conn))
            s_ver, s_findings = _read_db_schema_version(conn)
            schema_version = s_ver
            findings.extend(s_findings)

            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id FROM workspace LIMIT 1;")
                row = cursor.fetchone()
                if row:
                    ws_id = str(row[0])
            except sqlite3.Error:
                pass

            job_states = _read_recent_jobs(conn)
        finally:
            conn.close()
    except (sqlite3.Error, OSError) as exc:
        sanitized_err, _ = _redact_text(str(exc))
        findings.append(f"DATABASE_READ_ERROR: {sanitized_err}")

    return schema_version, ws_id, job_states, findings


def _collect_recent_logs(ws_root: Path, max_records: int) -> tuple[list[str], int]:
    """Read and redact recent log records from workspace logs directory.

    Args:
        ws_root: Workspace root directory path.
        max_records: Maximum count of log lines to collect.

    Returns:
        Tuple of (redacted_log_lines, count_of_redactions).
    """
    logs_dir = ws_root / "logs"
    if not logs_dir.is_dir():
        return [], 0

    log_files = sorted(
        logs_dir.glob("*.log"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )
    collected_lines: list[str] = []
    for lf in log_files:
        try:
            lines = lf.read_text(encoding="utf-8", errors="replace").splitlines()
            collected_lines.extend(lines)
            if len(collected_lines) >= max_records:
                break
        except OSError:
            pass

    log_entries: list[str] = []
    redaction_count = 0
    for line in collected_lines[:max_records]:
        redacted_line, l_count = _redact_text(line)
        log_entries.append(redacted_line)
        redaction_count += l_count

    return log_entries, redaction_count


def _collect_configuration(
    ws_root: Path,
    configure_runtime: ConfigureRuntimeCapability | None,
) -> tuple[dict[str, object], int]:
    """Extract and redact workspace runtime configuration.

    Args:
        ws_root: Workspace root directory path.
        configure_runtime: Runtime configuration capability.

    Returns:
        Tuple of (redacted_config_dict, count_of_redactions).
    """
    if configure_runtime is None:
        return {}, 0

    try:
        settings_ver = configure_runtime.get_workspace_settings(ws_root)
        if settings_ver is None:
            return {}, 0

        config_data = {
            "version": settings_ver.version,
            "worker_count": settings_ver.settings.worker_count,
            "worker_memory_mb": settings_ver.settings.worker_memory_mb,
            "max_artifact_size_mb": settings_ver.settings.max_artifact_size_mb,
            "max_total_artifact_gb": settings_ver.settings.max_total_artifact_gb,
            "timezone": settings_ver.settings.timezone,
            "locale": settings_ver.settings.locale,
            "log_level": settings_ver.settings.log_level,
            "log_retention_days": settings_ver.settings.log_retention_days,
            "retention_days": settings_ver.settings.retention_days,
        }
        redacted, count = _redact_data(config_data)
        config_dict = redacted if isinstance(redacted, dict) else {}
        return (
            {str(k): v for k, v in config_dict.items()},
            count,
        )
    except WorkspaceError, OSError:
        return {}, 0


def _resolve_output_file(
    ws_root: Path | None,
    output_path: Path | None,
    bundle_id: str,
) -> Path:
    """Determine destination file path for diagnostic archive.

    Args:
        ws_root: Workspace root path if available.
        output_path: Requested destination path.
        bundle_id: Generated bundle UUID string.

    Returns:
        Path to the target archive zip file.
    """
    if output_path is not None:
        target_path = Path(output_path).resolve()
        if target_path.is_dir():
            return target_path / f"diagnostic_bundle_{bundle_id}.zip"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return target_path

    if ws_root is not None and (ws_root / "exports").is_dir():
        return ws_root / "exports" / f"diagnostic_bundle_{bundle_id}.zip"

    import tempfile

    tmp_dir = Path(tempfile.gettempdir()) / "haru_diagnostics"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir / f"diagnostic_bundle_{bundle_id}.zip"


def _assemble_zip(
    *,
    archive_file: Path,
    manifest: DiagnosticBundleManifest,
    versions: dict[str, object],
    configuration: dict[str, object],
    job_states: list[dict[str, object]],
    integrity_findings: tuple[str, ...],
    log_entries: list[str],
) -> None:
    """Write bundle contents into a zip archive.

    Args:
        archive_file: Destination path for the zip archive.
        manifest: Diagnostic manifest object.
        versions: Application versions dictionary.
        configuration: Workspace configuration dictionary.
        job_states: Job execution history records.
        integrity_findings: Integrity check finding tokens.
        log_entries: Redacted structured log lines.

    Raises:
        DiagnosticBundleError: If zip compression or filesystem write fails.
    """
    try:
        with zipfile.ZipFile(archive_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "manifest.json",
                json.dumps(
                    {
                        "bundle_id": manifest.bundle_id,
                        "created_at": manifest.created_at,
                        "build_version": manifest.build_version,
                        "build_commit": manifest.build_commit,
                        "schema_version": manifest.schema_version,
                        "workspace_id": manifest.workspace_id,
                        "log_entries_count": manifest.log_entries_count,
                        "job_records_count": manifest.job_records_count,
                        "integrity_findings": list(manifest.integrity_findings),
                        "redaction_summary": manifest.redaction_summary,
                    },
                    indent=2,
                ),
            )
            zf.writestr("versions.json", json.dumps(versions, indent=2))
            zf.writestr("configuration.json", json.dumps(configuration, indent=2))
            zf.writestr("job_states.json", json.dumps(job_states, indent=2))
            zf.writestr(
                "integrity.json",
                json.dumps(
                    {
                        "findings": list(integrity_findings),
                        "healthy": len(integrity_findings) == 0,
                    },
                    indent=2,
                ),
            )
            zf.writestr("recent_logs.jsonl", "\n".join(log_entries))
    except (OSError, zipfile.BadZipFile) as exc:
        err_msg = f"Failed to create diagnostic zip archive: {exc}"
        raise DiagnosticBundleError(err_msg) from exc


def _inspect_workspace(
    ws_root: Path,
    cfg: DiagnosticBundleConfig,
    include_logs: bool,
    configure_runtime: ConfigureRuntimeCapability | None,
) -> tuple[
    int | None,
    str | None,
    dict[str, object],
    list[dict[str, object]],
    list[str],
    list[str],
    int,
]:
    """Inspect workspace directories, database, logs, and configuration.

    Args:
        ws_root: Workspace root directory path.
        cfg: Configuration options for bundle construction.
        include_logs: Whether to collect recent structured log entries.
        configure_runtime: Optional runtime configuration capability.

    Returns:
        Tuple of (schema_version, detected_id, configuration_data, job_states,
        log_entries, integrity_findings, total_redactions).
    """
    integrity_findings: list[str] = []
    redaction_count = 0

    for sub in ("metadata", "logs", "staging", "cache", "artifacts/objects"):
        if not (ws_root / sub).exists():
            integrity_findings.append(f"MISSING_DIRECTORY: {sub}")

    s_ver, detected_id, raw_jobs, db_findings = _inspect_workspace_db(ws_root)
    integrity_findings.extend(db_findings)

    red_jobs_obj, j_count = _redact_data(raw_jobs)
    job_states_data: list[dict[str, object]] = []
    if isinstance(red_jobs_obj, (list, tuple)):
        for item in red_jobs_obj:
            if isinstance(item, dict):
                job_states_data.append({str(k): v for k, v in item.items()})
    redaction_count += j_count

    red_config, c_count = _collect_configuration(ws_root, configure_runtime)
    redaction_count += c_count

    log_entries: list[str] = []
    if include_logs:
        logs, l_count = _collect_recent_logs(ws_root, cfg.max_log_records)
        log_entries = logs
        redaction_count += l_count

    return (
        s_ver,
        detected_id,
        red_config,
        job_states_data,
        log_entries,
        integrity_findings,
        redaction_count,
    )


def fr_ws_build_diagnostic_bundle(
    *,
    workspace: Path | WorkspaceRef | None = None,
    include_logs: bool = True,
    output_path: Path | None = None,
    config: DiagnosticBundleConfig | None = None,
    manage_workspaces: ManageWorkspacesCapability | None = None,
    configure_runtime: ConfigureRuntimeCapability | None = None,
    secure_local_access: SecureLocalAccessCapability | None = None,
) -> DiagnosticBundleRef:
    """Trace implementation for FR-WS-BUILD_DIAGNOSTIC_BUNDLE.

    Args:
        workspace: Optional workspace directory path or WorkspaceRef to inspect.
        include_logs: Whether to collect recent structured log entries.
        output_path: Optional destination file or directory path for the archive.
        config: Configuration options for bundle construction.
        manage_workspaces: Workspace lifecycle capability.
        configure_runtime: Runtime configuration capability.
        secure_local_access: Local access security capability.

    Returns:
        DiagnosticBundleRef with archive details and manifest.

    Raises:
        DiagnosticBundleError: If bundle construction or packaging fails.
    """
    cfg = config or DiagnosticBundleConfig()
    bundle_id = str(uuid4())
    created_at = _now_utc()
    total_redactions = 0
    integrity_findings: list[str] = []

    _ = manage_workspaces
    _ = secure_local_access

    redacted_versions, v_count = _collect_versions(created_at)
    total_redactions += v_count

    ws_id: str | None = None
    schema_version: int | None = None
    configuration_data: dict[str, object] = {}
    job_states_data: list[dict[str, object]] = []
    log_entries: list[str] = []

    ws_root: Path | None = None
    if workspace is not None:
        ws_root = (
            workspace.root_path
            if isinstance(workspace, WorkspaceRef)
            else Path(workspace).resolve()
        )
        if isinstance(workspace, WorkspaceRef):
            ws_id = workspace.workspace_id

    if ws_root is not None and ws_root.is_dir():
        (
            s_ver,
            detected_id,
            configuration_data,
            job_states_data,
            log_entries,
            ws_findings,
            ws_redactions,
        ) = _inspect_workspace(ws_root, cfg, include_logs, configure_runtime)
        schema_version = s_ver
        if ws_id is None:
            ws_id = detected_id
        integrity_findings.extend(ws_findings)
        total_redactions += ws_redactions
    elif ws_root is not None:
        integrity_findings.append("WORKSPACE_ROOT_NOT_DIRECTORY")
    else:
        integrity_findings.append("NO_WORKSPACE_SPECIFIED")

    archive_file = _resolve_output_file(ws_root, output_path, bundle_id)
    manifest = DiagnosticBundleManifest(
        bundle_id=bundle_id,
        created_at=created_at,
        build_version=BUILD_VERSION,
        build_commit=BUILD_COMMIT,
        schema_version=schema_version,
        workspace_id=ws_id,
        log_entries_count=len(log_entries),
        job_records_count=len(job_states_data),
        integrity_findings=tuple(integrity_findings),
        redaction_summary={"redacted_items": total_redactions},
    )

    _assemble_zip(
        archive_file=archive_file,
        manifest=manifest,
        versions=redacted_versions,
        configuration=configuration_data,
        job_states=job_states_data,
        integrity_findings=manifest.integrity_findings,
        log_entries=log_entries,
    )

    try:
        archive_bytes = archive_file.read_bytes()
        checksum = hashlib.sha256(archive_bytes).hexdigest()
        file_size = len(archive_bytes)
    except OSError as exc:
        err_msg = f"Failed to read generated diagnostic archive: {exc}"
        raise DiagnosticBundleError(err_msg) from exc

    return DiagnosticBundleRef(
        bundle_id=bundle_id,
        archive_path=archive_file,
        checksum_sha256=checksum,
        file_size_bytes=file_size,
        manifest=manifest,
    )


class DiagnosticBundleService(BuildDiagnosticsCapability):
    """Production implementation of BuildDiagnosticsCapability."""

    def __init__(
        self,
        config: DiagnosticBundleConfig | None = None,
        manage_workspaces: ManageWorkspacesCapability | None = None,
        configure_runtime: ConfigureRuntimeCapability | None = None,
        secure_local_access: SecureLocalAccessCapability | None = None,
    ) -> None:
        """Initialize the diagnostic bundle service.

        Args:
            config: Configuration options for diagnostic bundle construction.
            manage_workspaces: Workspace lifecycle capability.
            configure_runtime: Runtime configuration capability.
            secure_local_access: Optional local access security capability.
        """
        self._config = config or DiagnosticBundleConfig()
        self._manage_workspaces = manage_workspaces
        self._configure_runtime = configure_runtime
        self._secure_local_access = secure_local_access

    @override
    def build_diagnostic_bundle(
        self,
        *,
        workspace: Path | WorkspaceRef | None = None,
        include_logs: bool = True,
        output_path: Path | None = None,
    ) -> DiagnosticBundleRef:
        """Produce a redacted diagnostic bundle for troubleshooting.

        Args:
            workspace: Optional workspace root or WorkspaceRef to inspect.
            include_logs: Whether to collect recent structured log entries.
            output_path: Optional destination directory or file path for the archive.

        Returns:
            DiagnosticBundleRef containing the archive path, checksum, and manifest.

        Raises:
            DiagnosticBundleError: If bundle construction or packaging fails.
        """
        return fr_ws_build_diagnostic_bundle(
            workspace=workspace,
            include_logs=include_logs,
            output_path=output_path,
            config=self._config,
            manage_workspaces=self._manage_workspaces,
            configure_runtime=self._configure_runtime,
            secure_local_access=self._secure_local_access,
        )


def _create_harness_workspace(root: Path) -> WorkspaceRef:
    """Create a minimal self-contained workspace fixture for usage harness.

    Args:
        root: Workspace root directory path.

    Returns:
        WorkspaceRef for the created workspace.
    """
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
            VALUES ('diag-ws-id', 'Diagnostics WS', '2026-01-01T00:00:00Z',
                    '2026-01-01T00:00:00Z');
            INSERT INTO schema_migrations (version, name, applied_at, checksum)
            VALUES (1, 'base_schema_v1', '2026-01-01T00:00:00Z', 'checksum_v1');
            INSERT INTO jobs (id, kind, status, created_at, updated_at)
            VALUES ('job-1', 'BACKTEST', 'COMPLETED', '2026-01-01T01:00:00Z',
                    '2026-01-01T01:05:00Z');
            """
        )
        conn.commit()
    finally:
        conn.close()

    # Write sample log file containing potential secrets to test redaction
    log_file = root / "logs" / "app.log"
    log_file.write_text(
        f"2026-01-01T00:00:00Z INFO Initialized at path: {root.as_posix()}\n"
        "2026-01-01T00:01:00Z DEBUG Auth with secret_token=super_secret_token_123456\n"
        "2026-01-01T00:02:00Z INFO Completed job-1\n",
        encoding="utf-8",
    )

    return WorkspaceRef(
        workspace_id="diag-ws-id",
        name="Diagnostics WS",
        root_path=root,
    )


def _run_usage_example() -> None:
    """Run the designated executable usage demonstration.

    Raises:
        RuntimeError: If any scenario assertion fails.
    """
    import tempfile

    print("Executing Diagnostic Bundle (__main__) usage scenarios...\n")

    # =========================================================================
    # Scenario 1: FR-WS-BUILD_DIAGNOSTIC_BUNDLE
    # =========================================================================
    print("Scenario 1: FR-WS-BUILD_DIAGNOSTIC_BUNDLE")
    service = DiagnosticBundleService()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        ws_root = Path(tmp_dir) / "demo_diagnostic_ws"
        ws_ref = _create_harness_workspace(ws_root)

        bundle = service.build_diagnostic_bundle(
            workspace=ws_ref,
            include_logs=True,
        )
        print(f"  Generated bundle ID: {bundle.bundle_id}")
        print(f"  Archive path: {bundle.archive_path.name}")
        print(f"  Archive size: {bundle.file_size_bytes} bytes")
        print(f"  SHA-256 digest: {bundle.checksum_sha256[:16]}...")
        print(f"  Logs captured: {bundle.manifest.log_entries_count}")
        redactions = bundle.manifest.redaction_summary.get("redacted_items", 0)
        print(f"  Redactions performed: {redactions}")

        # Verify archive exists and contains required members
        if not bundle.archive_path.is_file():
            err_not_found = "Bundle archive was not written to filesystem"
            raise RuntimeError(err_not_found)

        with zipfile.ZipFile(bundle.archive_path, "r") as zf:
            member_names = set(zf.namelist())
            expected_members = {
                "manifest.json",
                "versions.json",
                "configuration.json",
                "job_states.json",
                "integrity.json",
                "recent_logs.jsonl",
            }
            if not expected_members.issubset(member_names):
                missing_members = expected_members - member_names
                err_missing = f"Missing expected archive members: {missing_members}"
                raise RuntimeError(err_missing)

            # Verify redaction inside archive
            logs_content = zf.read("recent_logs.jsonl").decode("utf-8")
            if ws_root.as_posix() in logs_content:
                err_path_leak = "Absolute user filesystem path leaked in logs"
                raise RuntimeError(err_path_leak)
            if (
                "super_secret_token_123456" in logs_content  # pragma: allowlist secret
            ):
                err_token_leak = (  # pragma: allowlist secret
                    "Unredacted secret token leaked in logs"  # noqa: S105
                )
                raise RuntimeError(err_token_leak)

    print("  [OK] FR-WS-BUILD_DIAGNOSTIC_BUNDLE passed.\n")
    print("[SUCCESS] All 1 Diagnostic Bundle usage scenarios passed!")


if __name__ == "__main__":
    _run_usage_example()
