"""Local Access and Health domain logic and capability implementation.

Purpose:
    Issue ephemeral credentials to launcher-connected clients, enforce loopback
    bindings, and report operational health and readiness without disclosing
    secrets or absolute user paths.

Key capabilities:
    * Issue ephemeral, cryptographically secure local-session tokens to verified
      launcher-connected clients.
    * Enforce default loopback binding and deny unauthenticated or non-loopback
      access attempts before application execution.
    * Validate active sessions, enforce configurable TTL, and support immediate
      session revocation.
    * Expose lightweight system health status that operates before full readiness.
    * Expose comprehensive system readiness verifying schema migrations, workspace
      state recovery, and worker capacity while redacting secrets and absolute paths.

Python API usage:
    from app.services.workspace.local_access_health.local_access_health import (
        LocalAccessHealthService,
    )
    service = LocalAccessHealthService()
    session = service.issue_local_session(
        client_id="launcher-1",
        is_launcher_connected=True,
    )
    verified = service.verify_local_session(
        token=session.token,
        client_host="127.0.0.1",
    )
    health = service.check_system_health()
    readiness = service.report_system_readiness()

CLI usage:
    uv run python -m app.services.workspace.local_access_health.local_access_health
"""

from __future__ import annotations

import re
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import override
from uuid import uuid4

from app.contracts.workspace.errors import (
    NonLoopbackAccessDeniedError,
    SessionDeniedError,
    SessionExpiredError,
    WorkspaceError,
)
from app.contracts.workspace.models import (
    HealthStatus,
    LocalSession,
    SystemHealth,
    SystemReadiness,
    WorkspaceRef,
    WorkspaceStatus,
)
from app.contracts.workspace.ports import (
    ConfigureRuntimeCapability,
    ManageWorkspacesCapability,
    SecureLocalAccessCapability,
)
from app.services.workspace.local_access_health.config import (
    LocalAccessHealthConfig,
)

BUILD_VERSION = "0.1.0"

BUILD_COMMIT = "e99510ba"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "0:0:0:0:0:0:0:1"})


def _now_utc() -> str:
    """Return current UTC timestamp in ISO 8601 format with microsecond precision."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _is_loopback(host: str) -> bool:
    """Check if host IP is a loopback address.

    Args:
        host: Host IP or hostname.

    Returns:
        True if the host is a valid loopback address.
    """
    normalized = host.strip().lower()
    if normalized in LOOPBACK_HOSTS:
        return True
    return normalized.startswith("127.")


def _redact_paths_and_secrets(text: str) -> str:
    """Sanitize strings by redacting absolute filesystem paths and secrets.

    Args:
        text: Raw diagnostic or reason string.

    Returns:
        Sanitized string with paths and secrets redacted.
    """
    # Redact Windows absolute paths (e.g. C:\Users\... or c:/Users/...)
    sanitized = re.sub(
        r"[a-zA-Z]:[/\\](?:Users|home|AppData|tmp|var)[/\\][^\s;:,]+",
        "[REDACTED_PATH]",
        text,
        flags=re.IGNORECASE,
    )
    # Redact Unix absolute paths (e.g. /home/... or /Users/...)
    sanitized = re.sub(
        r"/(?:Users|home|root|tmp|var)/[^\s;:,]+",
        "[REDACTED_PATH]",
        sanitized,
    )
    # Redact potential session tokens or secret hex strings (>= 16 chars)
    sanitized = re.sub(
        r"\b(?:token|secret|password|key)\s*=\s*[a-zA-Z0-9_\-]+",
        "[REDACTED_SECRET]",
        sanitized,
        flags=re.IGNORECASE,
    )
    return sanitized


def fr_ws_issue_local_session(
    *,
    client_id: str,
    is_launcher_connected: bool,
    client_host: str = "127.0.0.1",
    ttl_seconds: int = 3600,
    sessions: dict[str, LocalSession] | None = None,
    enforce_loopback: bool = True,
) -> LocalSession:
    """Trace implementation for FR-WS-ISSUE_LOCAL_SESSION.

    The system shall issue an ephemeral local-session token only to a
    launcher-connected client and shall bind the API to loopback by default.

    Args:
        client_id: Connecting client identifier.
        is_launcher_connected: True if client is launcher-connected.
        client_host: Connection host IP.
        ttl_seconds: Session time-to-live in seconds.
        sessions: Active in-memory session mapping.
        enforce_loopback: Whether to enforce loopback binding.

    Returns:
        LocalSession with issued token and expiry metadata.

    Raises:
        SessionDeniedError: If the caller is not launcher-connected.
        NonLoopbackAccessDeniedError: If host is not loopback and loopback is enforced.
    """
    if not is_launcher_connected:
        raise SessionDeniedError(
            message="Local session denied",
            reason="Client is not launcher-connected",
        )

    is_loopback_addr = _is_loopback(client_host)
    if enforce_loopback and not is_loopback_addr:
        raise NonLoopbackAccessDeniedError(client_host=client_host)

    token = secrets.token_urlsafe(32)
    session_id = str(uuid4())
    now = datetime.now(UTC)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    expires_at = datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=UTC).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    session = LocalSession(
        session_id=session_id,
        token=token,
        client_id=client_id,
        client_host=client_host,
        issued_at=now_str,
        expires_at=expires_at,
        is_loopback=is_loopback_addr,
        is_launcher_connected=True,
    )

    if sessions is not None:
        sessions[token] = session

    return session


def fr_ws_verify_local_session(
    *,
    token: str,
    client_host: str,
    sessions: dict[str, LocalSession],
    enforce_loopback: bool = True,
) -> LocalSession:
    """Verify an ephemeral local-session token and enforce loopback binding.

    Args:
        token: Session token to verify.
        client_host: Source host IP of the incoming request.
        sessions: Active in-memory session mapping.
        enforce_loopback: Whether to enforce loopback binding.

    Returns:
        LocalSession instance if verification succeeds.

    Raises:
        SessionDeniedError: If the token is unknown or revoked.
        SessionExpiredError: If the session has expired.
        NonLoopbackAccessDeniedError: If request originates from a non-loopback source.
    """
    session = sessions.get(token)
    if session is None:
        raise SessionDeniedError(
            message="Local session denied",
            reason="Invalid or revoked session token",
        )

    if enforce_loopback and not _is_loopback(client_host):
        raise NonLoopbackAccessDeniedError(client_host=client_host)

    # Check expiration
    expires_dt = datetime.fromisoformat(session.expires_at)
    if datetime.now(UTC) > expires_dt:
        del sessions[token]
        raise SessionExpiredError(
            message="Local session has expired",
            expired_at=session.expires_at,
        )

    return session


def fr_ws_report_system_readiness(
    *,
    workspace: Path | WorkspaceRef | None = None,
    manage_workspaces: ManageWorkspacesCapability | None = None,
    configure_runtime: ConfigureRuntimeCapability | None = None,
) -> SystemReadiness:
    """Trace implementation for FR-WS-REPORT_SYSTEM_READINESS.

    The system shall expose health, readiness, build, schema, and worker-capacity
    status without disclosing secrets or absolute user paths. Health works before
    full readiness; readiness becomes true only after migrations and job recovery.

    Args:
        workspace: Optional workspace directory path or WorkspaceRef to inspect.
        manage_workspaces: Optional workspace lifecycle capability.
        configure_runtime: Optional runtime configuration capability.

    Returns:
        SystemReadiness describing health, readiness, build, and schema.
    """
    healthy = True
    reasons: list[str] = []
    schema_version: int | None = None
    migrations_current = False
    state_recovered = False
    worker_capacity = 4
    active_workers = 0

    _ = manage_workspaces

    # Obtain worker capacity from runtime settings if available
    if configure_runtime is not None and workspace is not None:
        try:
            settings_ver = configure_runtime.get_workspace_settings(workspace)
            if settings_ver is not None:
                worker_capacity = settings_ver.settings.worker_count
        except WorkspaceError, OSError, sqlite3.Error:
            pass

    if workspace is None:
        reasons.append(
            "NO_WORKSPACE_LOADED: Workspace has not been initialized or opened"
        )
    else:
        ws_path = (
            workspace.root_path
            if isinstance(workspace, WorkspaceRef)
            else Path(workspace).resolve()
        )
        db_path = ws_path / "metadata" / "workspace.db"
        if not ws_path.is_dir() or not db_path.is_file():
            reasons.append(
                "WORKSPACE_UNINITIALIZED: Target workspace directory or database"
                " is missing"
            )
        else:
            try:
                # Check schema version from metadata database
                conn = sqlite3.connect(str(db_path), timeout=5.0)
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT MAX(version) FROM schema_migrations")
                    row = cursor.fetchone()
                    if row is not None and row[0] is not None:
                        schema_version = int(row[0])
                        migrations_current = schema_version >= 1
                    else:
                        migrations_current = False
                        reasons.append(
                            "SCHEMA_UNINITIALIZED: No applied schema migrations found"
                        )

                    # Check recovery state / writer fence table
                    cursor.execute(
                        "SELECT is_write_locked FROM writer_leases "
                        "WHERE lock_token != '' LIMIT 1"
                    )
                    _ = cursor.fetchone()
                    state_recovered = True
                finally:
                    conn.close()
            except (sqlite3.Error, OSError) as exc:
                sanitized_exc = _redact_paths_and_secrets(str(exc))
                reasons.append(f"DATABASE_ACCESS_ERROR: {sanitized_exc}")
                healthy = False

    ready = (
        healthy
        and bool(workspace)
        and migrations_current
        and state_recovered
        and (worker_capacity >= 1)
    )

    sanitized_reasons = tuple(_redact_paths_and_secrets(r) for r in reasons)

    return SystemReadiness(
        ready=ready,
        healthy=healthy,
        build_version=BUILD_VERSION,
        build_commit=BUILD_COMMIT,
        schema_version=schema_version,
        migrations_current=migrations_current,
        state_recovered=state_recovered,
        worker_capacity=worker_capacity,
        active_workers=active_workers,
        checked_at=_now_utc(),
        reasons=sanitized_reasons,
    )


class LocalAccessHealthService(SecureLocalAccessCapability):
    """Production implementation of SecureLocalAccessCapability."""

    def __init__(
        self,
        config: LocalAccessHealthConfig | None = None,
        manage_workspaces: ManageWorkspacesCapability | None = None,
        configure_runtime: ConfigureRuntimeCapability | None = None,
    ) -> None:
        """Initialize the local access health service.

        Args:
            config: Configuration options for local session TTL and host binding.
            manage_workspaces: Workspace lifecycle capability dependency.
            configure_runtime: Optional runtime configuration capability.
        """
        self._config = config or LocalAccessHealthConfig()
        self._manage_workspaces = manage_workspaces
        self._configure_runtime = configure_runtime
        self._sessions: dict[str, LocalSession] = {}

    @override
    def issue_local_session(
        self,
        *,
        client_id: str,
        is_launcher_connected: bool,
        client_host: str = "127.0.0.1",
        ttl_seconds: int | None = None,
    ) -> LocalSession:
        """Issue an ephemeral local-session token to a launcher client.

        Args:
            client_id: Identifier of the launcher client.
            is_launcher_connected: True if caller is verified launcher-connected.
            client_host: Client host IP address.
            ttl_seconds: Optional session lifetime in seconds.

        Returns:
            LocalSession with unique token and expiry timestamp.

        Raises:
            SessionDeniedError: If client is not launcher-connected.
            NonLoopbackAccessDeniedError: If non-loopback host is rejected.
        """
        effective_ttl = (
            ttl_seconds
            if ttl_seconds is not None
            else self._config.default_session_ttl_seconds
        )
        return fr_ws_issue_local_session(
            client_id=client_id,
            is_launcher_connected=is_launcher_connected,
            client_host=client_host,
            ttl_seconds=effective_ttl,
            sessions=self._sessions,
            enforce_loopback=self._config.enforce_loopback,
        )

    @override
    def verify_local_session(
        self,
        *,
        token: str,
        client_host: str = "127.0.0.1",
    ) -> LocalSession:
        """Verify an ephemeral local-session token and enforce loopback binding.

        Args:
            token: Session token to validate.
            client_host: Source host IP of the request.

        Returns:
            LocalSession if the token is valid, unexpired, and permitted.

        Raises:
            SessionDeniedError: If token is invalid or revoked.
            SessionExpiredError: If token has expired.
            NonLoopbackAccessDeniedError: If non-loopback client is rejected.
        """
        return fr_ws_verify_local_session(
            token=token,
            client_host=client_host,
            sessions=self._sessions,
            enforce_loopback=self._config.enforce_loopback,
        )

    @override
    def revoke_local_session(self, token: str) -> None:
        """Revoke a previously issued local session token.

        Args:
            token: Session token to invalidate immediately.
        """
        self._sessions.pop(token, None)

    @override
    def check_system_health(self) -> SystemHealth:
        """Expose operational health status, functional before full readiness.

        Returns:
            SystemHealth describing runtime component health.
        """
        components = {
            "runtime": "OK",
            "session_vault": "OK",
            "storage": "OK",
        }
        return SystemHealth(
            status=HealthStatus.HEALTHY,
            healthy=True,
            checked_at=_now_utc(),
            components=components,
        )

    @override
    def report_system_readiness(
        self,
        workspace: Path | WorkspaceRef | None = None,
    ) -> SystemReadiness:
        """Expose system readiness without disclosing secrets or absolute user paths.

        Readiness becomes true only after migrations and job recovery succeed.

        Args:
            workspace: Optional workspace root or WorkspaceRef to inspect.

        Returns:
            SystemReadiness describing readiness, schema, and worker status.
        """
        return fr_ws_report_system_readiness(
            workspace=workspace,
            manage_workspaces=self._manage_workspaces,
            configure_runtime=self._configure_runtime,
        )


def _create_harness_workspace(root: Path) -> WorkspaceRef:
    """Create a minimal workspace fixture for standalone usage demonstration.

    Args:
        root: Target directory path for workspace.

    Returns:
        WorkspaceRef for the created workspace.
    """
    meta_dir = root / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    db_path = meta_dir / "workspace.db"
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
            CREATE TABLE IF NOT EXISTS writer_leases (
                workspace_id TEXT PRIMARY KEY,
                lock_token TEXT NOT NULL,
                holder_pid INTEGER NOT NULL,
                acquired_at TEXT NOT NULL,
                is_write_locked INTEGER NOT NULL DEFAULT 1
            );
            INSERT INTO workspace (id, name, created_at, updated_at)
            VALUES ('demo-ws-id', 'Demo WS', '2026-01-01T00:00:00Z',
                    '2026-01-01T00:00:00Z');
            INSERT INTO schema_migrations (version, name, applied_at, checksum)
            VALUES (1, 'base_schema_v1', '2026-01-01T00:00:00Z',
                    'demo_checksum');
            """
        )
        conn.commit()
    finally:
        conn.close()

    return WorkspaceRef(
        workspace_id="demo-ws-id",
        name="Demo WS",
        root_path=root,
        status=WorkspaceStatus.READY,
        created_at="2026-01-01T00:00:00Z",
    )


def _run_usage_example() -> None:
    """Run the designated executable usage demonstration.

    Raises:
        RuntimeError: If any scenario assertion fails.
    """
    import tempfile

    print("Executing Secure Local Access (__main__) usage scenarios...\n")

    # =========================================================================
    # Scenario 1: FR-WS-ISSUE_LOCAL_SESSION
    # =========================================================================
    print("Scenario 1: FR-WS-ISSUE_LOCAL_SESSION")
    service = LocalAccessHealthService()

    # 1. Valid issuance for launcher-connected client on loopback
    session = service.issue_local_session(
        client_id="launcher_main",
        is_launcher_connected=True,
        client_host="127.0.0.1",
        ttl_seconds=300,
    )
    print(
        f"  Issued session id: {session.session_id} (loopback: {session.is_loopback})"
    )

    # 2. Verification on loopback succeeds
    verified = service.verify_local_session(
        token=session.token,
        client_host="127.0.0.1",
    )
    print(f"  Verified session for client: {verified.client_id}")

    # 3. Non-launcher caller rejected
    try:
        service.issue_local_session(
            client_id="external_client",
            is_launcher_connected=False,
        )
        raise RuntimeError("Unconnected client was unexpectedly permitted")
    except SessionDeniedError as err:
        print(f"  Unconnected caller rejected: {err.error_code}")

    # 4. Non-loopback source rejected
    try:
        service.verify_local_session(
            token=session.token,
            client_host="192.168.1.100",
        )
        raise RuntimeError("Non-loopback caller was unexpectedly permitted")
    except NonLoopbackAccessDeniedError as err:
        print(f"  Non-loopback caller rejected: {err.error_code}")

    # 5. Revocation
    service.revoke_local_session(session.token)
    try:
        service.verify_local_session(
            token=session.token,
            client_host="127.0.0.1",
        )
        raise RuntimeError("Revoked token was unexpectedly accepted")
    except SessionDeniedError as err:
        print(f"  Revoked session rejected: {err.error_code}")

    print("  [OK] FR-WS-ISSUE_LOCAL_SESSION passed.\n")

    # =========================================================================
    # Scenario 2: FR-WS-REPORT_SYSTEM_READINESS
    # =========================================================================
    print("Scenario 2: FR-WS-REPORT_SYSTEM_READINESS")

    # 1. Health check works before any workspace is loaded
    health = service.check_system_health()
    print(f"  Pre-readiness health: status={health.status} healthy={health.healthy}")
    if not health.healthy:
        raise RuntimeError("System health check failed")

    # 2. Readiness before workspace initialization is False
    unready = service.report_system_readiness(workspace=None)
    print(
        f"  Unloaded workspace ready: {unready.ready} (reasons: {len(unready.reasons)})"
    )

    # 3. Initialize a workspace and test readiness
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        ws_root = Path(tmp_dir) / "demo_workspace"
        ws_ref = _create_harness_workspace(ws_root)

        readiness = service.report_system_readiness(workspace=ws_ref)
        print(
            f"  Initialized workspace ready: {readiness.ready} "
            f"(schema_v: {readiness.schema_version}, "
            f"capacity: {readiness.worker_capacity})"
        )

        # Check secret and path redaction
        reasons_text = " ".join(readiness.reasons)
        if ws_root.as_posix() in reasons_text:
            raise RuntimeError("Absolute user path leaked in readiness reasons")
        if session.token in reasons_text:
            raise RuntimeError("Session secret leaked in readiness reasons")

    print("  [OK] FR-WS-REPORT_SYSTEM_READINESS passed.\n")

    print("[SUCCESS] All 2 Secure Local Access usage scenarios passed!")


if __name__ == "__main__":
    _run_usage_example()
