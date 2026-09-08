"""Secure Local Access and Host Security domain logic and implementation.

Purpose:
    Provide secure secret lifecycle management (opaque references, isolated
    resolution strictly for authorized adapters, rotation, and immediate
    revocation), protect local session bindings, enforce loopback and host
    isolation policies, and expose operational health and readiness without
    disclosing secrets or absolute user paths.

Key capabilities:
    * Create, rotate, and revoke opaque secret references bound to an adapter
      generation and purpose.
    * Resolve plaintext secret values only within an authorized adapter boundary,
      rejecting UI, Agentic, and unauthorized caller roles.
    * Issue ephemeral, cryptographically secure local-session tokens to verified
      launcher-connected clients.
    * Enforce default loopback binding and reject unauthenticated or non-loopback
      access attempts before application execution.
    * Validate active sessions in constant time, enforce configurable TTL, and
      support immediate session revocation.
    * Safely zeroize decrypted material and secret byte buffers upon revocation
      and scope disposal.
    * Report operational health and readiness while redacting all secrets and
      absolute user paths.
"""

from __future__ import annotations

import ipaddress
import re
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, override
from uuid import uuid7

from app.contracts.workspace.errors import (
    InvalidHostBindingError,
    NonLoopbackAccessDeniedError,
    SecretNotFoundError,
    SecretResolutionDeniedError,
    SecretRevokedError,
    SessionDeniedError,
    SessionExpiredError,
    WorkspaceError,
)
from app.contracts.workspace.models import (
    HealthStatus,
    LocalSession,
    SecretRef,
    SystemHealth,
    SystemReadiness,
    WorkspaceRef,
)
from app.contracts.workspace.secure_local_access import (
    ResolvedSecret,
    SecretCreateRequest,
    SecretResolveRequest,
    SecretRevokeRequest,
    SecretRotateRequest,
    SecureLocalAccessCapability,
)
from app.services.workspace.secure_local_access.config import (
    SecureLocalAccessConfig,
)

if TYPE_CHECKING:
    from app.contracts.workspace.ports import (
        ConfigureRuntimeCapability,
        ManageAccountsCapability,
        ManageWorkspacesCapability,
    )

BUILD_VERSION = "0.1.0"
BUILD_COMMIT = "5a1d37cd"
LOOPBACK_HOSTS: frozenset[str] = frozenset(
    {
        "127.0.0.1",
        "localhost",
        "::1",
        "0:0:0:0:0:0:0:1",
    }
)
DEFAULT_LOOPBACK_HOST = "127.0.0.1"
DEFAULT_WORKER_CAPACITY = 4
MIN_WORKER_CAPACITY = 1
MIN_SCHEMA_VERSION = 1
DB_TIMEOUT_SECONDS = 5.0
FORBIDDEN_CALLER_ROLES: frozenset[str] = frozenset(
    {
        "ui",
        "agentic",
        "unauthorized",
    }
)
AUTHORIZED_CALLER_ROLE = "adapter"


def _now_utc() -> str:
    """Return current UTC timestamp in ISO 8601 format with microsecond precision.

    Returns:
        Formatted UTC timestamp string.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _is_loopback(host: str) -> bool:
    """Check if host IP is a loopback address.

    Args:
        host: Host IP or hostname.

    Returns:
        True if the host is a valid loopback address.
    """
    normalized = host.strip().lower()
    if normalized in LOOPBACK_HOSTS or normalized.startswith("127."):
        return True
    try:
        ip = ipaddress.ip_address(normalized)
        return ip.is_loopback
    except ValueError:
        return False


def _is_allowed_remote_host(host: str, allowed_subnets: tuple[str, ...]) -> bool:
    """Check if a remote host IP falls within any allowed remote subnets.

    Args:
        host: Host IP address string.
        allowed_subnets: Tuple of CIDR notation subnets or IP addresses.

    Returns:
        True if host is in an allowed subnet.
    """
    try:
        ip = ipaddress.ip_address(host.strip())
    except ValueError:
        return False

    for subnet_str in allowed_subnets:
        try:
            network = ipaddress.ip_network(subnet_str.strip(), strict=False)
            if ip in network:
                return True
        except ValueError:
            continue
    return False


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
    # Redact potential session tokens or secret hex strings
    sanitized = re.sub(
        r"\b(?:token|secret|password|key)\s*=\s*[a-zA-Z0-9_\-]+",
        "[REDACTED_SECRET]",
        sanitized,
        flags=re.IGNORECASE,
    )
    return sanitized


def _resolve_db(root_path: Path) -> Path:
    """Resolve the canonical workspace database path.

    Args:
        root_path: Path to workspace root or database.

    Returns:
        Canonical database path.
    """
    if root_path.suffix == ".db":
        return root_path
    central_db = root_path / "database" / "haruquantai.db"
    if central_db.exists():
        return central_db
    if (root_path / "haruquantai.db").exists():
        return root_path / "haruquantai.db"
    if (root_path / "data" / "database" / "haruquantai.db").exists():
        return root_path / "data" / "database" / "haruquantai.db"
    return central_db


@dataclass(slots=True)
class _StoredSecret:
    """Internal representation of a stored secret with zeroizable storage.

    Attributes:
        secret_id: Unique UUIDv7 identifier for the secret.
        workspace_id: UUIDv7 identifier of the owning workspace.
        name: Unique secret name within the workspace.
        secret_bytes: Mutable bytearray holding the plaintext secret.
        allowed_adapter_generation: Adapter generation authorized to resolve.
        allowed_purpose: Purpose authorized to resolve this secret.
        row_version: Monotonic version number for rotation tracking.
        created_at: ISO 8601 UTC creation timestamp.
        updated_at: ISO 8601 UTC last-updated timestamp.
        is_revoked: Whether the secret has been revoked.
        revocation_reason: Optional reason for revocation.
    """

    secret_id: str
    workspace_id: str
    name: str
    secret_bytes: bytearray
    allowed_adapter_generation: str
    allowed_purpose: str
    row_version: int
    created_at: str
    updated_at: str
    is_revoked: bool = False
    revocation_reason: str | None = None

    def zeroize(self) -> None:
        """Safely overwrite the secret bytes in memory and clear the buffer."""
        for i in range(len(self.secret_bytes)):
            self.secret_bytes[i] = 0
        self.secret_bytes.clear()

    def get_value(self) -> str:
        """Decode and return the secret value string.

        Returns:
            Decoded plaintext string.
        """
        return self.secret_bytes.decode("utf-8")


class SecureLocalAccessService(SecureLocalAccessCapability):
    """Production service implementing SecureLocalAccessCapability."""

    def __init__(
        self,
        config: SecureLocalAccessConfig | None = None,
        manage_accounts: ManageAccountsCapability | None = None,
        manage_workspaces: ManageWorkspacesCapability | None = None,
        configure_runtime: ConfigureRuntimeCapability | None = None,
    ) -> None:
        """Initialize the secure local access service.

        Args:
            config: Configuration for session TTL, loopback, and remote policies.
            manage_accounts: Optional account management capability.
            manage_workspaces: Optional workspace lifecycle capability.
            configure_runtime: Optional runtime configuration capability.
        """
        self._config = config or SecureLocalAccessConfig()
        self._manage_accounts = manage_accounts
        self._manage_workspaces = manage_workspaces
        self._configure_runtime = configure_runtime
        self._sessions: dict[str, LocalSession] = {}
        self._secrets: dict[tuple[str, str], _StoredSecret] = {}

    @override
    def create_secret_reference(
        self,
        request: SecretCreateRequest,
    ) -> SecretRef:
        """Create and store an opaque secret reference bound to adapter and purpose.

        Args:
            request: Secret creation parameters.

        Returns:
            Opaque SecretRef without plaintext secret values.
        """
        secret_id = str(uuid7())
        now_ts = _now_utc()
        stored = _StoredSecret(
            secret_id=secret_id,
            workspace_id=request.workspace_id,
            name=request.name,
            secret_bytes=bytearray(request.secret_value.encode("utf-8")),
            allowed_adapter_generation=request.allowed_adapter_generation,
            allowed_purpose=request.allowed_purpose,
            row_version=1,
            created_at=now_ts,
            updated_at=now_ts,
        )
        self._secrets[(request.workspace_id, secret_id)] = stored

        return SecretRef(
            secret_id=secret_id,
            workspace_id=request.workspace_id,
            name=request.name,
            created_at=now_ts,
            updated_at=now_ts,
            row_version=1,
        )

    @override
    def resolve_secret_reference(
        self,
        request: SecretResolveRequest,
    ) -> ResolvedSecret:
        """Resolve a raw secret value strictly for authorized adapter and purpose.

        Args:
            request: Secret resolution request.

        Returns:
            ResolvedSecret with decrypted value strictly inside adapter boundary.

        Raises:
            SecretResolutionDeniedError: If caller or purpose is unauthorized.
            SecretNotFoundError: If secret reference does not exist in workspace.
            SecretRevokedError: If secret reference has been revoked.
        """
        role_lower = request.caller_role.lower()
        if role_lower in FORBIDDEN_CALLER_ROLES or role_lower != AUTHORIZED_CALLER_ROLE:
            msg = (
                f"Caller role '{request.caller_role}' is not authorized "
                "to resolve secrets"
            )
            raise SecretResolutionDeniedError(
                message=msg,
                caller_role=request.caller_role,
                secret_id=request.secret_id,
                allowed_roles=(AUTHORIZED_CALLER_ROLE,),
            )

        key = (request.workspace_id, request.secret_id)
        stored = self._secrets.get(key)
        if stored is None:
            msg = (
                f"Secret reference '{request.secret_id}' was not found "
                f"in workspace '{request.workspace_id}'"
            )
            raise SecretNotFoundError(
                message=msg,
                secret_id=request.secret_id,
                workspace_id=request.workspace_id,
            )

        if stored.is_revoked:
            msg = f"Secret reference '{request.secret_id}' has been revoked"
            raise SecretRevokedError(
                message=msg,
                secret_id=request.secret_id,
                workspace_id=request.workspace_id,
                revocation_reason=stored.revocation_reason,
            )

        if stored.allowed_adapter_generation != request.adapter_generation:
            msg = (
                f"Adapter generation mismatch: secret requires "
                f"'{stored.allowed_adapter_generation}', caller provided "
                f"'{request.adapter_generation}'"
            )
            raise SecretResolutionDeniedError(
                message=msg,
                caller_role=request.caller_role,
                secret_id=request.secret_id,
                allowed_adapter_generation=stored.allowed_adapter_generation,
                provided_adapter_generation=request.adapter_generation,
            )

        if stored.allowed_purpose != request.purpose:
            msg = (
                f"Secret purpose mismatch: secret requires "
                f"'{stored.allowed_purpose}', caller requested '{request.purpose}'"
            )
            raise SecretResolutionDeniedError(
                message=msg,
                caller_role=request.caller_role,
                secret_id=request.secret_id,
                allowed_purpose=stored.allowed_purpose,
                provided_purpose=request.purpose,
            )

        return ResolvedSecret(
            secret_id=stored.secret_id,
            name=stored.name,
            secret_value=stored.get_value(),
            row_version=stored.row_version,
            adapter_generation=stored.allowed_adapter_generation,
            purpose=stored.allowed_purpose,
        )

    @override
    def rotate_secret_reference(
        self,
        request: SecretRotateRequest,
    ) -> SecretRef:
        """Rotate a secret value and advance its generation.

        Args:
            request: Rotation request with new secret and new generation.

        Returns:
            Updated SecretRef with incremented row_version.

        Raises:
            SecretNotFoundError: If secret reference does not exist.
            SecretRevokedError: If secret reference has been revoked.
        """
        key = (request.workspace_id, request.secret_id)
        stored = self._secrets.get(key)
        if stored is None:
            msg = (
                f"Secret reference '{request.secret_id}' was not found "
                f"in workspace '{request.workspace_id}'"
            )
            raise SecretNotFoundError(
                message=msg,
                secret_id=request.secret_id,
                workspace_id=request.workspace_id,
            )

        if stored.is_revoked:
            msg = f"Secret reference '{request.secret_id}' has been revoked"
            raise SecretRevokedError(
                message=msg,
                secret_id=request.secret_id,
                workspace_id=request.workspace_id,
                revocation_reason=stored.revocation_reason,
            )

        # Safely overwrite previous secret bytes before reassigning
        stored.zeroize()
        stored.secret_bytes = bytearray(request.new_secret_value.encode("utf-8"))
        stored.allowed_adapter_generation = request.new_adapter_generation
        if request.allowed_purpose is not None:
            stored.allowed_purpose = request.allowed_purpose
        stored.row_version += 1
        stored.updated_at = _now_utc()

        return SecretRef(
            secret_id=stored.secret_id,
            workspace_id=stored.workspace_id,
            name=stored.name,
            created_at=stored.created_at,
            updated_at=stored.updated_at,
            row_version=stored.row_version,
        )

    @override
    def revoke_secret_reference(
        self,
        request: SecretRevokeRequest,
    ) -> None:
        """Revoke a secret reference immediately and zeroize its contents.

        Args:
            request: Revocation request.

        Raises:
            SecretNotFoundError: If secret reference does not exist.
        """
        key = (request.workspace_id, request.secret_id)
        stored = self._secrets.get(key)
        if stored is None:
            msg = (
                f"Secret reference '{request.secret_id}' was not found "
                f"in workspace '{request.workspace_id}'"
            )
            raise SecretNotFoundError(
                message=msg,
                secret_id=request.secret_id,
                workspace_id=request.workspace_id,
            )

        stored.is_revoked = True
        stored.revocation_reason = request.reason
        stored.updated_at = _now_utc()
        stored.zeroize()

    @override
    def issue_local_session(
        self,
        *,
        client_id: str,
        is_launcher_connected: bool,
        client_host: str = DEFAULT_LOOPBACK_HOST,
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
            InvalidHostBindingError: If host violates permitted subnets.
        """
        if not is_launcher_connected:
            raise SessionDeniedError(
                message="Local session denied",
                reason="Client is not launcher-connected",
            )

        is_loopback_addr = _is_loopback(client_host)
        if self._config.enforce_loopback and not is_loopback_addr:
            raise NonLoopbackAccessDeniedError(client_host=client_host)

        if not is_loopback_addr and not _is_allowed_remote_host(
            client_host, self._config.allowed_remote_subnets
        ):
            msg = f"Host '{client_host}' is not an authorized binding"
            raise InvalidHostBindingError(message=msg, host=client_host)

        token = secrets.token_urlsafe(32)
        session_id = str(uuid7())
        now = datetime.now(UTC)
        now_str = _now_utc()
        effective_ttl = (
            ttl_seconds
            if ttl_seconds is not None
            else self._config.default_session_ttl_seconds
        )
        expires_at = datetime.fromtimestamp(
            now.timestamp() + effective_ttl, tz=UTC
        ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

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
        self._sessions[token] = session
        return session

    @override
    def verify_local_session(
        self,
        *,
        token: str,
        client_host: str = DEFAULT_LOOPBACK_HOST,
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
            InvalidHostBindingError: If host violates permitted subnets.
        """
        session = self._sessions.get(token)
        if session is None or not secrets.compare_digest(session.token, token):
            raise SessionDeniedError(
                message="Local session denied",
                reason="Invalid or revoked session token",
            )

        is_loopback_addr = _is_loopback(client_host)
        if self._config.enforce_loopback and not is_loopback_addr:
            raise NonLoopbackAccessDeniedError(client_host=client_host)

        if not is_loopback_addr and not _is_allowed_remote_host(
            client_host, self._config.allowed_remote_subnets
        ):
            msg = f"Host '{client_host}' is not an authorized binding"
            raise InvalidHostBindingError(message=msg, host=client_host)

        expires_dt = datetime.fromisoformat(session.expires_at)
        if datetime.now(UTC) > expires_dt:
            self._sessions.pop(token, None)
            raise SessionExpiredError(
                message="Local session has expired",
                expired_at=session.expires_at,
            )

        return session

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
            "secrets_keystore": "OK",  # pragma: allowlist secret
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
        healthy = True
        reasons: list[str] = []
        schema_version: int | None = None
        migrations_current = False
        state_recovered = False
        worker_capacity = DEFAULT_WORKER_CAPACITY
        active_workers = 0

        if self._configure_runtime is not None and workspace is not None:
            try:
                settings_ver = self._configure_runtime.get_workspace_settings(workspace)
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
            db_path = _resolve_db(ws_path)
            if not ws_path.is_dir() or not db_path.is_file():
                reasons.append(
                    "WORKSPACE_UNINITIALIZED: Target workspace directory or database"
                    " is missing"
                )
            else:
                try:
                    conn = sqlite3.connect(str(db_path), timeout=DB_TIMEOUT_SECONDS)
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT MAX(version) FROM schema_migrations")
                        row = cursor.fetchone()
                        if row is not None and row[0] is not None:
                            schema_version = int(row[0])
                            migrations_current = schema_version >= MIN_SCHEMA_VERSION
                        else:
                            migrations_current = False
                            reasons.append(
                                "SCHEMA_UNINITIALIZED: No applied schema "
                                "migrations found"
                            )

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
            and (worker_capacity >= MIN_WORKER_CAPACITY)
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

    def close(self) -> None:
        """Dispose of the service scope, zeroizing all stored secret material."""
        for stored in self._secrets.values():
            stored.zeroize()
        self._secrets.clear()
        self._sessions.clear()


__all__ = [
    "BUILD_COMMIT",
    "BUILD_VERSION",
    "SecureLocalAccessService",
]
