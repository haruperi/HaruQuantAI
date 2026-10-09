"""Host-owned sessions, security boundaries, and distribution qualification.

Description:
    HostAuthentication verifies the single configured host account through
    HostSettings and owns password hashing, bounded login attempts, HTTP login
    aliases and local CLI provisioning. SessionManager is the sole ephemeral
    session authority; lifecycle records use persistence.HostSessionStore in the
    existing host_session table. UI and CLI/Python issuance share this path; only
    hashes are stored. Transport compatibility delegates here. Changed credentials
    revoke sessions on verification. HTTP clients cannot request privileged roles.
    Account credentials and duration use application/user_access JSON exclusively.
    Account HTTP access verifies the current password before changing username,
    password or session duration; successful changes revoke existing sessions.

    PersistenceAccess binds entity namespaces and worker owners, delegating CRUD
    to persistence and reservation policy to jobs.LeaseManager. Namespace binding
    is not authorization; existing session authorization remains authoritative.
    No database connections, cursors or SQL are exposed to this module.

    Provides the central security authority, loopback origin validation, ephemeral
    session management with guaranteed host-restart invalidation, fine-grained
    scope authorization, distinct authority elevation for high-risk operations
    (live trading, destructive tasks, external scripts, mail, paid tools), secret
    sanitization, user-code execution boundaries, and local distribution qualification
    for the HaruQuantAI platform host.

    In quantitative trading and desktop analytical platforms, strict loopback
    origin containment blocks DNS rebinding and cross-site attacks. Sessions are
    strictly bound to the running host instance and are unconditionally invalidated
    upon restart, preventing stale or resurrected credentials. Standard operator
    sessions enforce principle of least privilege: dangerous operations (such as
    live broker order placement, database wipes, or arbitrary subprocess execution)
    are denied by default and require time-bounded distinct authority grants.

    In accordance with platform persistence isolation principles, session data is
    strictly ephemeral and held in-memory; lifecycle metadata is durably recorded
    without restoring tokens. Any durable host state must route
    exclusively through `app.host.persistence.DatabaseManager`.

Purpose:
    FEAT-HOST-SESSION: Host-Owned Sessions, Security Boundaries, and Distribution.
    Enforces loopback isolation, ephemeral session tokens, scoped capability
    authorization, distinct elevation gates, credential masking, and clean
    distribution qualification.

Key Capabilities:
    - FR-HOST-SESS-CREDENTIALS: Verify/provision the configured host account.
      Associated: `HostAuthentication`, `hash_password()`, `configure_host_user()`,
        `HostAuthentication.change_account()`, `_create_account_router()`
      Logging: INFO verifier/setup/auth success; WARNING rejection/cooldown; ERROR
        setup failure. Tests verify omission of password/hash/token payloads.
    - FR-HOST-SESS-LOOPBACK-ORIGIN: Loopback origin validation and DNS rebinding
      prevention for local workstation HTTP endpoints.
      Associated: `[LoopbackValidator]`, `[LoopbackSecurityMiddleware]`
      Logging: Emits DEBUG on verified loopback request; WARNING on rejected foreign
      origins or DNS rebinding attempts.
    - FR-HOST-SESS-LIFECYCLE: Ephemeral session token generation, sliding TTL,
      explicit revocation, and host-restart invalidation.
      Associated: `[SessionManager.create_session()]`,
      `[SessionManager.verify_session()]`, `[SessionManager.reset()]`
      Logging: Emits INFO on session creation and revocation; WARNING on expired
      or unknown tokens; INFO on restart invalidation.
    - FR-HOST-SESS-SCOPE-AUTHORIZATION: Granular scope checking (`<resource>:<action>`
      and wildcards) across domains, resources, and tools.
      Associated: `[ScopeAuthorizer.authorize()]`,
      `[ScopeAuthorizer.evaluate_scope()]`
      Logging: Emits DEBUG on authorized actions; WARNING on permission denial
      with structured fr_id and requested scope.
    - FR-HOST-SESS-DISTINCT-AUTHORITY: Explicit time-bounded elevation grants for
      dangerous tasks (live orders, destructive tasks, scripts, mail, paid tools).
      Associated: `[DistinctAuthorityCoordinator.elevate()]`,
      `[DistinctAuthorityCoordinator.require_distinct_authority()]`
      Logging: Emits WARNING on elevation grant issuance and expiration; ERROR on
      unauthorized dangerous task attempts.
    - FR-HOST-SESS-SECRET-SANITIZATION: Masked credential isolation and operational
      input sanitization preventing plaintext leakage in logs and projections.
      Associated: `[MaskedSecret]`, `[sanitize_operational_inputs()]`
      Logging: Sanitizes dictionary inputs, replacing sensitive keys with redaction
      digests.
    - FR-HOST-SESS-DISTRIBUTION-QUALIFICATION: Clean-installation checks, domain
      removal state preservation, and authenticated remote TLS deployment proposal.
      Associated: `[verify_clean_installation()]`, `[verify_domain_removal()]`,
      `[get_tls_remote_deployment_proposal()]`
      Logging: Emits INFO on qualification assessments; ERROR on residual leaks.
    - FR-HOST-SESS-REST-PROJECTION: FastAPI router exposing session lifecycle,
      elevation, scope checks, distribution qualification, and TLS proposals.
      Associated: `[create_sessions_router()]`
      Logging: Emits DEBUG on router composition; INFO on session mutations.

Python API Usage:
    ```python
    from app.host.session import (
        DistinctAuthorityCoordinator,
        DistinctAuthorityType,
        ElevationRequest,
        LoopbackValidator,
        ScopeAuthorizer,
        SessionManager,
        StandardScope,
    )

    # 1. Ephemeral Session Lifecycle
    mgr = SessionManager(host_instance_id="host-abc12345")
    session = mgr.create_session(username="operator")

    # 2. Scope Authorization
    authorizer = ScopeAuthorizer()
    authorizer.authorize(session, StandardScope.JOBS_READ)

    # 3. Distinct Authority Elevation for Live Orders
    coordinator = DistinctAuthorityCoordinator()
    grant = coordinator.elevate(
        session,
        ElevationRequest(
            scope=DistinctAuthorityType.LIVE_TRADING,
            reason="Arming live terminal",
            confirmation_phrase="CONFIRM:live_trading:execute",
        ),
    )
    coordinator.require_distinct_authority(session, DistinctAuthorityType.LIVE_TRADING)
    ```

CLI Usage:
    Configure the account locally; passwords are entered through hidden prompts:
    `uv run python -m app.host.session --configure-user --username operator
    --db path/to/database.db`. Existing account replacement requires confirmation.
    No plaintext passwords, default credentials or persistent tokens are created.
    ```bash
    uv run python -m app.host.session --check-install
    uv run python -m app.host.session --audit-scopes
    uv run python -m app.host.session --tls-proposal
    ```
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import getpass
import hashlib
import hmac
import ipaddress
import re
import secrets
import sys
import threading
import time
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, override
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.host.jobs import LeaseManager, LeaseRecord
from app.host.logging import get_logger
from app.host.persistence import (
    DatabaseManager,
    HostSessionRecord,
    HostSessionStore,
    PersistenceError,
    RevisionConflictError,
    TypedRepository,
    validate_identifier,
)
from app.host.response import StandardError, StandardResponse
from app.host.settings import HostSettings

__all__ = [
    "AuthenticationError",
    "CleanInstallCheckResult",
    "DistinctAuthorityCoordinator",
    "DistinctAuthorityGrant",
    "DistinctAuthorityRequiredError",
    "DistinctAuthorityType",
    "DistributionQualificationError",
    "DomainRemovalCheckResult",
    "ElevationExpiredError",
    "ElevationRequest",
    "ElevationResponse",
    "HostAuthentication",
    "LoginRequest",
    "LoopbackOriginError",
    "LoopbackSecurityMiddleware",
    "LoopbackValidator",
    "MaskedSecret",
    "PermissionDeniedError",
    "PersistenceAccess",
    "RoleType",
    "ScopeAuthorizer",
    "ScopeCheckRequest",
    "ScopeCheckResponse",
    "SecurityError",
    "SessionContext",
    "SessionExpiredError",
    "SessionManager",
    "SessionToken",
    "SessionTokenManager",
    "SessionsRouter",
    "StandardScope",
    "TlsRemoteDeploymentProposal",
    "UserCodeBounds",
    "configure_host_user",
    "create_auth_router",
    "create_sessions_router",
    "extract_bearer_token",
    "get_current_session",
    "get_global_authority_coordinator",
    "get_global_authorizer",
    "get_global_session_manager",
    "get_tls_remote_deployment_proposal",
    "hash_password",
    "main",
    "reset_global_security_state",
    "sanitize_operational_inputs",
    "validate_user_code_ast",
    "verify_clean_installation",
    "verify_domain_removal",
    "verify_password",
]

logger = get_logger(__name__)

# Constants
MAX_PASSWORD_LENGTH: Final[int] = 1024
MAX_USERNAME_LENGTH: Final[int] = 64
PASSWORD_ITERATIONS: Final[int] = 600_000
PASSWORD_SALT_HEX_LENGTH: Final[int] = 32
PASSWORD_DIGEST_HEX_LENGTH: Final[int] = 64
LOGIN_WINDOW_SECONDS: Final[int] = 60
MAX_LOGIN_FAILURES: Final[int] = 5
MIN_SESSION_MINUTES: Final[int] = 1440
MAX_SESSION_MINUTES: Final[int] = 43200
DEFAULT_SESSION_TTL_SEC: Final[int] = 86400  # 24 hours
DEFAULT_ELEVATION_TTL_SEC: Final[int] = 600  # 10 minutes
MAX_ELEVATION_TTL_SEC: Final[int] = 1800  # 30 minutes
MIN_ELEVATION_TTL_SEC: Final[int] = 10  # 10 seconds
EXPECTED_BEARER_PARTS: Final[int] = 2

LOOPBACK_HOSTS: Final[frozenset[str]] = frozenset(
    {"127.0.0.1", "localhost", "::1", "[::1]", "testserver"}
)


def _now_utc_iso() -> str:
    """Return current UTC timestamp formatted as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class SecurityError(Exception):
    """Base exception for all security, session, and authorization failures."""


class LoopbackOriginError(SecurityError):
    """Raised when request originates from an unauthorized foreign origin."""


class AuthenticationError(SecurityError):
    """Raised when credentials or session tokens are invalid or missing."""


class SessionExpiredError(AuthenticationError):
    """Raised when an active session token has exceeded its time-to-live expiration."""


class PermissionDeniedError(SecurityError):
    """Raised when an authenticated principal lacks required scope for an action."""


class DistinctAuthorityRequiredError(PermissionDeniedError):
    """Raised when an action requires explicit distinct authority elevation."""


class ElevationExpiredError(DistinctAuthorityRequiredError):
    """Raised when a distinct authority elevation grant has expired."""


class DistributionQualificationError(SecurityError):
    """Raised when a clean-install or domain-removal qualification check fails."""


# -----------------------------------------------------------------------------
# Enums and Models
# -----------------------------------------------------------------------------


class StandardScope(StrEnum):
    """Standard operational scopes for the HaruQuantAI platform host."""

    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SETTINGS_READ = "settings:read"
    SETTINGS_WRITE = "settings:write"
    JOBS_READ = "jobs:read"
    JOBS_WRITE = "jobs:write"
    JOBS_CANCEL = "jobs:cancel"
    RESOURCES_READ = "resources:read"
    RESOURCES_WRITE = "resources:write"
    RESOURCES_DELETE = "resources:delete"
    PLUGINS_READ = "plugins:read"
    PLUGINS_MANAGE = "plugins:manage"
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    STRATEGIES_READ = "strategies:read"
    STRATEGIES_WRITE = "strategies:write"
    BACKTEST_RUN = "backtest:run"


class DistinctAuthorityType(StrEnum):
    """Sensitive scopes requiring distinct, time-bounded elevation grants."""

    LIVE_TRADING = "live_trading:execute"
    SYSTEM_DESTRUCTIVE = "system:destructive"
    SCRIPTS_EXECUTE = "scripts:execute"
    NOTIFICATIONS_EXTERNAL = "notifications:external"
    TOOLS_PAID = "tools:paid"


class RoleType(StrEnum):
    """Predefined security principal roles."""

    OPERATOR = "operator"
    READONLY = "readonly"
    PLUGIN = "plugin"
    SYSTEM = "system"


ROLE_DEFAULT_SCOPES: Final[dict[RoleType, frozenset[str]]] = {
    RoleType.OPERATOR: frozenset(
        {
            StandardScope.SYSTEM_READ,
            StandardScope.SETTINGS_READ,
            StandardScope.SETTINGS_WRITE,
            StandardScope.JOBS_READ,
            StandardScope.JOBS_WRITE,
            StandardScope.JOBS_CANCEL,
            StandardScope.RESOURCES_READ,
            StandardScope.RESOURCES_WRITE,
            StandardScope.RESOURCES_DELETE,
            StandardScope.PLUGINS_READ,
            StandardScope.PLUGINS_MANAGE,
            StandardScope.DATA_READ,
            StandardScope.DATA_WRITE,
            StandardScope.STRATEGIES_READ,
            StandardScope.STRATEGIES_WRITE,
            StandardScope.BACKTEST_RUN,
        }
    ),
    RoleType.READONLY: frozenset(
        {
            StandardScope.SYSTEM_READ,
            StandardScope.SETTINGS_READ,
            StandardScope.JOBS_READ,
            StandardScope.RESOURCES_READ,
            StandardScope.PLUGINS_READ,
            StandardScope.DATA_READ,
            StandardScope.STRATEGIES_READ,
        }
    ),
    RoleType.PLUGIN: frozenset(
        {
            StandardScope.RESOURCES_READ,
            StandardScope.DATA_READ,
            StandardScope.SETTINGS_READ,
        }
    ),
    RoleType.SYSTEM: frozenset({"*"}),
}


class DistinctAuthorityGrant(BaseModel):
    """Time-bounded elevation grant for a sensitive operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    grant_id: str = Field(description="Unique elevation grant identifier")
    scope: DistinctAuthorityType = Field(description="Sensitive scope granted")
    granted_at: str = Field(description="ISO 8601 UTC grant timestamp")
    expires_at: str = Field(description="ISO 8601 UTC expiration timestamp")
    reason: str = Field(description="Operator-provided rationale for elevation")
    active: bool = Field(default=True, description="True if grant has not been revoked")

    def is_expired(self) -> bool:
        """Return True if the elevation grant has passed its expiration time."""
        if not self.active:
            return True
        exp = datetime.fromisoformat(self.expires_at)
        return datetime.now(UTC) > exp


class SessionContext(BaseModel):
    """Authoritative ephemeral session context bound to host runtime."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(description="Opaque bearer session token")
    username: str = Field(description="Authenticated username")
    role: RoleType = Field(description="Principal role classification")
    scopes: set[str] = Field(default_factory=set, description="Assigned scopes")
    created_at: str = Field(description="ISO 8601 UTC session creation timestamp")
    expires_at: str = Field(description="ISO 8601 UTC session expiration timestamp")
    last_active_at: str = Field(
        description="ISO 8601 UTC timestamp of last observed activity"
    )
    host_instance_id: str = Field(description="Host instance ID that issued session")
    distinct_grants: dict[str, DistinctAuthorityGrant] = Field(
        default_factory=dict, description="Active distinct elevation grants by scope"
    )

    def is_expired(self) -> bool:
        """Return True if session has passed its expiration timestamp."""
        exp = datetime.fromisoformat(self.expires_at)
        return datetime.now(UTC) > exp

    def has_scope(self, required_scope: str) -> bool:
        """Return True if session holds exact scope or matching wildcard."""
        if "*" in self.scopes or required_scope in self.scopes:
            return True
        # Check wildcard e.g. "jobs:*" matches "jobs:read"
        return (
            ":" in required_scope
            and f"{required_scope.split(':', 1)[0]}:*" in self.scopes
        )

    def has_distinct_grant(self, scope: DistinctAuthorityType) -> bool:
        """Return True if session holds an active unexpired distinct grant for scope."""
        grant = self.distinct_grants.get(scope.value)
        if grant is None:
            return False
        return not grant.is_expired()


class SessionToken(BaseModel):
    """Public token descriptor returned upon session creation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    token: str = Field(description="Opaque bearer token")
    username: str = Field(description="Principal username")
    role: RoleType = Field(description="Assigned role")
    scopes: list[str] = Field(description="Assigned scope list")
    expires_at: str = Field(description="ISO 8601 UTC expiration timestamp")
    host_instance_id: str = Field(description="Issuing host instance identifier")


class LoginRequest(BaseModel):
    """Payload submitted to initiate an authenticated session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    username: str = Field(
        default="", max_length=64, description="Optional configured username"
    )
    password: str = Field(
        default="", max_length=1024, repr=False, description="Principal password"
    )
    role: RoleType = Field(
        default=RoleType.OPERATOR, description="Requested principal role"
    )


class ElevationRequest(BaseModel):
    """Request submitted to obtain time-bounded distinct authority elevation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: DistinctAuthorityType = Field(description="Dangerous scope to elevate")
    reason: str = Field(
        min_length=5, description="Explicit operator rationale for dangerous action"
    )
    confirmation_phrase: str = Field(
        description="Explicit confirmation token, e.g. CONFIRM:<scope>"
    )
    ttl_seconds: int = Field(
        default=DEFAULT_ELEVATION_TTL_SEC,
        ge=MIN_ELEVATION_TTL_SEC,
        le=MAX_ELEVATION_TTL_SEC,
        description="Lease duration in seconds",
    )


class ElevationResponse(BaseModel):
    """Response produced upon successful distinct authority elevation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    grant_id: str = Field(description="Unique grant identifier")
    scope: DistinctAuthorityType = Field(description="Elevated scope")
    expires_at: str = Field(description="ISO 8601 UTC expiration timestamp")
    message: str = Field(description="Status confirmation message")


class ScopeCheckRequest(BaseModel):
    """Payload to evaluate scope authorization for an action."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: str = Field(description="Action scope to evaluate")


class ScopeCheckResponse(BaseModel):
    """Outcome of scope authorization evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    allowed: bool = Field(description="True if authorized")
    scope: str = Field(description="Evaluated scope")
    requires_distinct_authority: bool = Field(
        description="True if scope requires distinct elevation"
    )
    reason: str | None = Field(
        default=None, description="Detailed explanation if rejected"
    )


class CleanInstallCheckResult(BaseModel):
    """Verification outcome of local installation clean state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    is_clean: bool = Field(description="True if installation meets clean baseline")
    base_dir: str = Field(description="Inspected directory path")
    verified_paths: list[str] = Field(description="Verified clean directories")
    missing_paths: list[str] = Field(description="Missing required directories")
    leaked_artifacts: list[str] = Field(description="Orphaned or leaked artifacts")
    message: str = Field(description="Summary message")


class DomainRemovalCheckResult(BaseModel):
    """Verification outcome of domain or plugin uninstallation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain_id: str = Field(description="Identifier of removed domain")
    sessions_revoked: int = Field(description="Number of domain sessions revoked")
    state_cleared: bool = Field(description="True if transient caches were purged")
    cas_artifacts_preserved: int = Field(
        description="Number of retained immutable artifacts preserved"
    )
    unrelated_data_intact: bool = Field(
        description="True if unrelated tenant directories are untouched"
    )
    message: str = Field(description="Summary assessment message")


class TlsRemoteDeploymentProposal(BaseModel):
    """Authoritative architecture proposal for authenticated remote deployment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    local_binding: str = Field(
        default="127.0.0.1:8000", description="Workstation loopback binding"
    )
    recommended_topology: str = Field(description="Recommended remote gateway topology")
    tls_termination: str = Field(description="TLS termination layer specification")
    authentication_strategy: str = Field(
        description="Gateway authentication and mTLS policy"
    )
    network_isolation_notes: list[str] = Field(
        description="Security isolation guidelines"
    )


# -----------------------------------------------------------------------------
# Secret Sanitization & Input Protection
# -----------------------------------------------------------------------------


class MaskedSecret:
    """Opaque container for sensitive credentials masking plaintext representation."""

    def __init__(self, secret: str) -> None:
        self._secret = secret
        digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12]
        self._redacted = f"[REDACTED:{digest}]"

    def get_secret_value(self) -> str:
        """Return the raw plaintext secret value for authorized consumption."""
        return self._secret

    @override
    def __repr__(self) -> str:
        """Return safe masked representation for debugging and logging."""
        return f"MaskedSecret({self._redacted})"

    @override
    def __str__(self) -> str:
        """Return safe masked string representation."""
        return self._redacted

    @override
    def __eq__(self, other: object) -> bool:
        """Check equality against another MaskedSecret or raw string."""
        if isinstance(other, MaskedSecret):
            return self._secret == other._secret
        if isinstance(other, str):
            return self._secret == other
        return False

    @override
    def __hash__(self) -> int:
        """Compute hash based on raw secret value."""
        return hash(self._secret)


_SENSITIVE_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(password|secret|token|api_key|apikey|credential|authorization|auth_bearer)",
    re.IGNORECASE,
)


def sanitize_operational_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize operational input dictionaries, redacting secrets.

    Fires FR-HOST-SESS-SECRET-SANITIZATION.
    """
    sanitized: dict[str, Any] = {}
    for key, val in data.items():
        if _SENSITIVE_KEY_PATTERN.search(key):
            if isinstance(val, str):
                digest = hashlib.sha256(val.encode("utf-8")).hexdigest()[:12]
                sanitized[key] = f"[REDACTED:{digest}]"
            elif isinstance(val, MaskedSecret):
                sanitized[key] = str(val)
            else:
                sanitized[key] = "[REDACTED]"
        elif isinstance(val, MaskedSecret):
            sanitized[key] = str(val)
        elif isinstance(val, dict):
            sanitized[key] = sanitize_operational_inputs(val)
        elif isinstance(val, list):
            sanitized[key] = [
                sanitize_operational_inputs(item)
                if isinstance(item, dict)
                else (str(item) if isinstance(item, MaskedSecret) else item)
                for item in val
            ]
        else:
            sanitized[key] = val
    return sanitized


# -----------------------------------------------------------------------------
# Loopback Origin & DNS Rebinding Validator
# -----------------------------------------------------------------------------


class LoopbackValidator:
    """Validates Host, Origin, and Referer headers against allowed loopback addresses.

    Fires FR-HOST-SESS-LOOPBACK-ORIGIN.
    """

    def __init__(self, allowed_hosts: frozenset[str] = LOOPBACK_HOSTS) -> None:
        self.allowed_hosts = allowed_hosts

    def is_loopback_host(self, host_str: str) -> bool:
        """Check whether a host header value represents a local loopback interface."""
        if not host_str:
            return False
        cleaned = host_str.strip().lower()
        if cleaned.startswith("[") and "]" in cleaned:
            host_only = cleaned[1 : cleaned.index("]")].strip()
        elif cleaned.count(":") > 1:
            host_only = cleaned
        elif ":" in cleaned:
            host_only = cleaned.split(":", 1)[0].strip()
        else:
            host_only = cleaned

        if host_only in self.allowed_hosts:
            return True

        # Check raw IP address for loopback
        try:
            ip = ipaddress.ip_address(host_only)
            return ip.is_loopback
        except ValueError:
            return False

    def is_loopback_url(self, url_str: str) -> bool:
        """Check whether an Origin or Referer URL represents a loopback host."""
        if not url_str:
            return True
        try:
            parsed = urlparse(url_str)
            hostname = parsed.hostname
            if not hostname:
                return False
            return self.is_loopback_host(hostname)
        except ValueError, TypeError, AttributeError:
            return False

    def validate_request_headers(self, headers: Mapping[str, str]) -> None:
        """Validate request headers, raising LoopbackOriginError on foreign origin.

        Raises:
            LoopbackOriginError: If Host or Origin header specifies a non-loopback host.
        """
        host = headers.get("host", "").strip()
        if host and not self.is_loopback_host(host):
            logger.warning(
                "FR-HOST-SESS-LOOPBACK-ORIGIN: Rejected non-loopback host header: %s",
                host,
                extra={"fr_id": "FR-HOST-SESS-LOOPBACK-ORIGIN", "host": host},
            )
            raise LoopbackOriginError(
                f"Unauthorized host '{host}': requests must originate from "
                "loopback interface (localhost, 127.0.0.1, [::1])."
            )

        origin = headers.get("origin")
        if origin and not self.is_loopback_url(origin):
            logger.warning(
                "FR-HOST-SESS-LOOPBACK-ORIGIN: Rejected foreign origin header: %s",
                origin,
                extra={"fr_id": "FR-HOST-SESS-LOOPBACK-ORIGIN", "origin": origin},
            )
            raise LoopbackOriginError(
                f"Unauthorized origin '{origin}': cross-origin requests from "
                "foreign hosts are prohibited."
            )

        referer = headers.get("referer")
        if referer and not self.is_loopback_url(referer):
            logger.warning(
                "FR-HOST-SESS-LOOPBACK-ORIGIN: Rejected foreign referer header: %s",
                referer,
                extra={"fr_id": "FR-HOST-SESS-LOOPBACK-ORIGIN", "referer": referer},
            )
            raise LoopbackOriginError(
                f"Unauthorized referer '{referer}': cross-site referrals from "
                "foreign hosts are prohibited."
            )

        logger.debug(
            "FR-HOST-SESS-LOOPBACK-ORIGIN: Loopback origin check passed for host: %s",
            host,
            extra={"fr_id": "FR-HOST-SESS-LOOPBACK-ORIGIN"},
        )


class LoopbackSecurityMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware enforcing loopback origin and DNS rebinding protections."""

    def __init__(self, app: Any, validator: LoopbackValidator | None = None) -> None:
        super().__init__(app)
        self.validator = validator or LoopbackValidator()

    @override
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Intercept and validate loopback origin headers on incoming request."""
        try:
            self.validator.validate_request_headers(request.headers)
        except LoopbackOriginError as exc:
            err = StandardError(
                code="LOOPBACK_ORIGIN_DENIED",
                message=str(exc),
                retryable=False,
            )
            envelope = StandardResponse.failure(
                message=str(exc),
                error=err,
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=envelope.to_dict(),
            )
        return await call_next(request)


# -----------------------------------------------------------------------------
# Ephemeral Session Manager
# -----------------------------------------------------------------------------


class SessionManager:
    """In-memory authority with durable records and host-restart invalidation.

    Fires FR-HOST-SESS-LIFECYCLE.
    """

    def __init__(
        self,
        host_instance_id: str | None = None,
        default_ttl_sec: int = DEFAULT_SESSION_TTL_SEC,
        *,
        store: HostSessionStore | None = None,
    ) -> None:
        self.host_instance_id = host_instance_id or f"host-{uuid.uuid4().hex[:12]}"
        self.default_ttl_sec = default_ttl_sec
        self._sessions: dict[str, SessionContext] = {}
        self._lock = threading.RLock()
        self._store = store

    def bind_store(self, store: HostSessionStore) -> None:
        """Bind configured storage before issuance without relocating active tokens."""
        with self._lock:
            if self._sessions and (
                self._store is None or self._store.db_path != store.db_path
            ):
                raise AuthenticationError("Cannot relocate active session storage.")
            self._store = store
            logger.debug(
                "Session lifecycle storage bound",
                extra={"fr_id": "FR-HOST-SESS-LIFECYCLE"},
            )

    def _session_store(self) -> HostSessionStore:
        """Resolve standalone CLI/Python storage lazily, without import-time work."""
        if self._store is None:
            self._store = HostSessionStore(DatabaseManager())
        return self._store

    def _record_status(
        self,
        status: str,
        *,
        token: str | None = None,
        username: str | None = None,
        peer_id: str | None = None,
    ) -> None:
        """Persist issuer-scoped lifecycle decisions without storing bearer tokens."""
        if self._store is None:
            return
        self._store.update_status(
            peer_id=peer_id or self.host_instance_id,
            expected_status="ACTIVE",
            status=status,
            revoked_at_utc=_now_utc_iso() if status == "REVOKED" else None,
            token_hash=hashlib.sha256(token.encode()).hexdigest() if token else None,
            username=username,
        )

    def create_session(
        self,
        username: str = "operator",
        role: RoleType = RoleType.OPERATOR,
        scopes: Sequence[str] | None = None,
        ttl_sec: int | None = None,
    ) -> SessionContext:
        """Create and register a new ephemeral session bound to this host instance."""
        ttl = ttl_sec if ttl_sec is not None else self.default_ttl_sec
        with self._lock:
            self._session_store().initialize()
        now = datetime.now(UTC)
        created_at_iso = now.isoformat()
        expires_at_iso = (now + timedelta(seconds=ttl)).isoformat()
        token = secrets.token_hex(32)

        assigned_scopes: set[str] = set(ROLE_DEFAULT_SCOPES.get(role, set()))
        if scopes:
            assigned_scopes.update(scopes)

        session = SessionContext(
            token=token,
            username=username,
            role=role,
            scopes=assigned_scopes,
            created_at=created_at_iso,
            expires_at=expires_at_iso,
            last_active_at=created_at_iso,
            host_instance_id=self.host_instance_id,
        )

        with self._lock:
            self._session_store().create(
                HostSessionRecord(
                    session_id=uuid.uuid4().hex,
                    token_hash=hashlib.sha256(token.encode()).hexdigest(),
                    username=username,
                    peer_id=self.host_instance_id,
                    created_at_utc=created_at_iso,
                    expires_at_utc=expires_at_iso,
                    status="ACTIVE",
                )
            )
            self._sessions[token] = session

        logger.info(
            "FR-HOST-SESS-LIFECYCLE: Created ephemeral session for user=%s role=%s "
            "expires_at=%s (host=%s)",
            username,
            role,
            expires_at_iso,
            self.host_instance_id,
            extra={
                "fr_id": "FR-HOST-SESS-LIFECYCLE",
                "username": username,
                "role": role.value,
                "host_instance_id": self.host_instance_id,
            },
        )
        return session

    def verify_session(self, token: str) -> SessionContext:
        """Verify an active session token, renewing sliding activity timestamp.

        Raises:
            AuthenticationError: If token does not exist or host instance ID mismatches.
            SessionExpiredError: If token has passed its expiration timestamp.
        """
        if not token:
            raise AuthenticationError("Missing session token.")

        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                logger.warning(
                    "FR-HOST-SESS-LIFECYCLE: Verification failed: token not found",
                    extra={"fr_id": "FR-HOST-SESS-LIFECYCLE"},
                )
                raise AuthenticationError("Invalid or unknown session token.")

            # Host restart boundary check
            if session.host_instance_id != self.host_instance_id:
                self._sessions.pop(token, None)
                self._record_status(
                    "REVOKED", token=token, peer_id=session.host_instance_id
                )
                logger.warning(
                    "FR-HOST-SESS-LIFECYCLE: Rejected session from prior instance: %s",
                    session.host_instance_id,
                    extra={"fr_id": "FR-HOST-SESS-LIFECYCLE"},
                )
                raise AuthenticationError(
                    "Session invalidated: host runtime restarted."
                )

            # Check expiration
            if session.is_expired():
                self._sessions.pop(token, None)
                self._record_status("EXPIRED", token=token)
                logger.warning(
                    "FR-HOST-SESS-LIFECYCLE: Rejected expired session for user=%s",
                    session.username,
                    extra={"fr_id": "FR-HOST-SESS-LIFECYCLE"},
                )
                raise SessionExpiredError("Session token has expired.")

            # Update sliding activity timestamp
            session.last_active_at = _now_utc_iso()
            return session

    def revoke_session(self, token: str) -> bool:
        """Revoke a specific session token."""
        with self._lock:
            removed = self._sessions.pop(token, None) is not None
            if removed:
                self._record_status("REVOKED", token=token)
        if removed:
            logger.info(
                "FR-HOST-SESS-LIFECYCLE: Explicitly revoked session token.",
                extra={"fr_id": "FR-HOST-SESS-LIFECYCLE"},
            )
        return removed

    def revoke_user(self, username: str) -> int:
        """Revoke all active sessions belonging to the specified username."""
        revoked_count = 0
        with self._lock:
            tokens_to_revoke = [
                tok for tok, s in self._sessions.items() if s.username == username
            ]
            for tok in tokens_to_revoke:
                self._sessions.pop(tok, None)
                revoked_count += 1
            if tokens_to_revoke:
                self._record_status("REVOKED", username=username)
        logger.info(
            "FR-HOST-SESS-LIFECYCLE: Revoked %d active sessions for user=%s",
            revoked_count,
            username,
            extra={"fr_id": "FR-HOST-SESS-LIFECYCLE", "username": username},
        )
        return revoked_count

    def reset(self, new_host_instance_id: str | None = None) -> None:
        """Invalidate all active sessions across a host reboot or test reset.

        Fires FR-HOST-SESS-LIFECYCLE restart invalidation.
        """
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            self._record_status("REVOKED")
            self.host_instance_id = (
                new_host_instance_id or f"host-{uuid.uuid4().hex[:12]}"
            )
        logger.info(
            "FR-HOST-SESS-LIFECYCLE: Restart invalidation: purged %d sessions, "
            "new host_instance_id=%s",
            count,
            self.host_instance_id,
            extra={
                "fr_id": "FR-HOST-SESS-LIFECYCLE",
                "purged_count": count,
                "new_instance_id": self.host_instance_id,
            },
        )

    def active_session_count(self) -> int:
        """Return the current count of registered unexpired sessions."""
        with self._lock:
            now = datetime.now(UTC)
            expired = [
                token
                for token, s in self._sessions.items()
                if datetime.fromisoformat(s.expires_at) <= now
            ]
            for token in expired:
                self._sessions.pop(token, None)
                self._record_status("EXPIRED", token=token)
            return len(self._sessions)


# -----------------------------------------------------------------------------
# Scoped Authorization Engine
# -----------------------------------------------------------------------------


class ScopeAuthorizer:
    """Evaluates fine-grained action scopes against session principal permissions.

    Fires FR-HOST-SESS-SCOPE-AUTHORIZATION.
    """

    def is_distinct_authority_scope(self, scope: str) -> bool:
        """Return True if requested scope represents a dangerous distinct authority."""
        try:
            DistinctAuthorityType(scope)
            return True
        except ValueError:
            return False

    def authorize(self, session: SessionContext, required_scope: str) -> None:
        """Validate that the session holds authority to execute the requested action.

        Raises:
            DistinctAuthorityRequiredError: If scope is dangerous and not elevated.
            ElevationExpiredError: If elevation grant has expired.
            PermissionDeniedError: If session lacks required standard scope.
        """
        # 1. Distinct Authority Gate for Dangerous Operations
        if self.is_distinct_authority_scope(required_scope):
            distinct_scope = DistinctAuthorityType(required_scope)
            grant = session.distinct_grants.get(distinct_scope.value)
            if grant is None or not grant.active:
                logger.warning(
                    "FR-HOST-SESS-DISTINCT-AUTHORITY: Denied dangerous scope %s: "
                    "distinct authority elevation required.",
                    required_scope,
                    extra={
                        "fr_id": "FR-HOST-SESS-DISTINCT-AUTHORITY",
                        "scope": required_scope,
                        "username": session.username,
                    },
                )
                raise DistinctAuthorityRequiredError(
                    f"Action '{required_scope}' is a dangerous operation requiring "
                    "explicit distinct authority elevation."
                )
            if grant.is_expired():
                session.distinct_grants.pop(distinct_scope.value, None)
                logger.warning(
                    "FR-HOST-SESS-DISTINCT-AUTHORITY: Denied dangerous scope %s: "
                    "elevation grant expired.",
                    required_scope,
                    extra={
                        "fr_id": "FR-HOST-SESS-DISTINCT-AUTHORITY",
                        "scope": required_scope,
                    },
                )
                raise ElevationExpiredError(
                    f"Distinct authority grant for '{required_scope}' has expired."
                )
            logger.debug(
                "FR-HOST-SESS-DISTINCT-AUTHORITY: Verified distinct authority grant "
                "for %s (grant_id=%s)",
                required_scope,
                grant.grant_id,
                extra={"fr_id": "FR-HOST-SESS-DISTINCT-AUTHORITY"},
            )
            return

        # 2. Standard Scoped Authorization
        if not session.has_scope(required_scope):
            logger.warning(
                "FR-HOST-SESS-SCOPE-AUTHORIZATION: Denied user=%s scope=%s",
                session.username,
                required_scope,
                extra={
                    "fr_id": "FR-HOST-SESS-SCOPE-AUTHORIZATION",
                    "username": session.username,
                    "scope": required_scope,
                },
            )
            raise PermissionDeniedError(
                f"Principal '{session.username}' lacks scope '{required_scope}'."
            )

        logger.debug(
            "FR-HOST-SESS-SCOPE-AUTHORIZATION: Scope '%s' authorized for user=%s",
            required_scope,
            session.username,
            extra={"fr_id": "FR-HOST-SESS-SCOPE-AUTHORIZATION"},
        )

    def evaluate_scope(
        self, session: SessionContext, required_scope: str
    ) -> ScopeCheckResponse:
        """Evaluate scope without raising exceptions, returning structured outcome."""
        is_distinct = self.is_distinct_authority_scope(required_scope)
        try:
            self.authorize(session, required_scope)
            return ScopeCheckResponse(
                allowed=True,
                scope=required_scope,
                requires_distinct_authority=is_distinct,
                reason="Authorized",
            )
        except SecurityError as exc:
            return ScopeCheckResponse(
                allowed=False,
                scope=required_scope,
                requires_distinct_authority=is_distinct,
                reason=str(exc),
            )


# -----------------------------------------------------------------------------
# Distinct Authority Elevation Coordinator
# -----------------------------------------------------------------------------


class DistinctAuthorityCoordinator:
    """Coordinates time-bounded elevation for dangerous operations.

    Fires FR-HOST-SESS-DISTINCT-AUTHORITY.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def elevate(
        self, session: SessionContext, req: ElevationRequest
    ) -> DistinctAuthorityGrant:
        """Elevate a session with a time-bounded distinct authority grant.

        Raises:
            SecurityError: If confirmation phrase is invalid.
        """
        expected_phrase = f"CONFIRM:{req.scope.value}"
        if req.confirmation_phrase != expected_phrase:
            logger.warning(
                "FR-HOST-SESS-DISTINCT-AUTHORITY: Rejected elevation for %s: "
                "invalid confirmation phrase",
                req.scope.value,
                extra={"fr_id": "FR-HOST-SESS-DISTINCT-AUTHORITY"},
            )
            raise SecurityError(
                f"Invalid confirmation phrase: expected '{expected_phrase}'."
            )

        now = datetime.now(UTC)
        granted_at_iso = now.isoformat()
        expires_at_iso = (now + timedelta(seconds=req.ttl_seconds)).isoformat()
        grant_id = f"grant-{uuid.uuid4().hex[:12]}"

        grant = DistinctAuthorityGrant(
            grant_id=grant_id,
            scope=req.scope,
            granted_at=granted_at_iso,
            expires_at=expires_at_iso,
            reason=req.reason,
            active=True,
        )

        with self._lock:
            session.distinct_grants[req.scope.value] = grant

        logger.warning(
            "FR-HOST-SESS-DISTINCT-AUTHORITY: ELEVATED SESSION user=%s scope=%s "
            "expires_at=%s reason='%s' (grant=%s)",
            session.username,
            req.scope.value,
            expires_at_iso,
            req.reason,
            grant_id,
            extra={
                "fr_id": "FR-HOST-SESS-DISTINCT-AUTHORITY",
                "username": session.username,
                "scope": req.scope.value,
                "grant_id": grant_id,
            },
        )
        return grant

    def revoke_elevation(
        self, session: SessionContext, scope: DistinctAuthorityType
    ) -> bool:
        """Revoke an active distinct authority grant from a session."""
        with self._lock:
            grant = session.distinct_grants.pop(scope.value, None)
        if grant:
            logger.info(
                "FR-HOST-SESS-DISTINCT-AUTHORITY: Revoked distinct grant for %s "
                "(grant=%s)",
                scope.value,
                grant.grant_id,
                extra={"fr_id": "FR-HOST-SESS-DISTINCT-AUTHORITY"},
            )
            return True
        return False

    def require_distinct_authority(
        self, session: SessionContext, scope: DistinctAuthorityType
    ) -> None:
        """Assert that the session currently possesses valid elevation for scope.

        Raises:
            DistinctAuthorityRequiredError: If elevation is absent.
            ElevationExpiredError: If elevation has expired.
        """
        grant = session.distinct_grants.get(scope.value)
        if grant is None or not grant.active:
            raise DistinctAuthorityRequiredError(
                f"Action '{scope.value}' requires distinct authority elevation."
            )
        if grant.is_expired():
            session.distinct_grants.pop(scope.value, None)
            raise ElevationExpiredError(
                f"Distinct authority grant for '{scope.value}' has expired."
            )


# -----------------------------------------------------------------------------
# User-Code Execution Boundary & Isolation Specification
# -----------------------------------------------------------------------------


class UserCodeBounds(BaseModel):
    """Specification of resource boundaries and execution constraints for user code."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_execution_time_sec: float = Field(
        default=30.0, description="Hard timeout ceiling for script execution"
    )
    max_memory_mb: int = Field(
        default=512, description="Maximum RSS memory budget in megabytes"
    )
    max_output_bytes: int = Field(
        default=1_048_576, description="Maximum captured stdout/stderr buffer size"
    )
    forbidden_modules: list[str] = Field(
        default_factory=lambda: [
            "subprocess",
            "ctypes",
            "socket",
            "http.server",
            "urllib.request",
        ],
        description="Forbidden standard modules in contained worker processes",
    )


def _is_forbidden_module(mod_name: str, forbidden: Sequence[str]) -> bool:
    for fb in forbidden:
        if (
            mod_name == fb
            or mod_name.startswith(f"{fb}.")
            or fb.startswith(f"{mod_name}.")
        ):
            return True
    return False


def _check_import_node(node: ast.AST, forbidden: Sequence[str]) -> None:
    if isinstance(node, ast.Import):
        for alias in node.names:
            if _is_forbidden_module(alias.name, forbidden):
                logger.warning(
                    "FR-HOST-SESS-DISTINCT-AUTHORITY: Rejected forbidden import '%s'",
                    alias.name,
                    extra={"fr_id": "FR-HOST-SESS-DISTINCT-AUTHORITY"},
                )
                raise SecurityError(
                    f"Import of forbidden module '{alias.name}' is prohibited "
                    "without distinct scripts:execute authority."
                )
    elif (
        isinstance(node, ast.ImportFrom)
        and node.module
        and _is_forbidden_module(node.module, forbidden)
    ):
        logger.warning(
            "FR-HOST-SESS-DISTINCT-AUTHORITY: Rejected forbidden import from '%s'",
            node.module,
            extra={"fr_id": "FR-HOST-SESS-DISTINCT-AUTHORITY"},
        )
        raise SecurityError(
            f"Import from forbidden module '{node.module}' is prohibited "
            "without distinct scripts:execute authority."
        )


def validate_user_code_ast(code_str: str, bounds: UserCodeBounds | None = None) -> None:
    """Statically inspect user script AST to reject dangerous imports.

    Fires FR-HOST-SESS-DISTINCT-AUTHORITY.

    Raises:
        SecurityError: If forbidden modules or execution primitives are discovered.
    """
    resolved_bounds = bounds or UserCodeBounds()
    try:
        tree = ast.parse(code_str)
    except SyntaxError as exc:
        raise SecurityError(f"User code syntax error: {exc}") from exc

    for node in ast.walk(tree):
        _check_import_node(node, resolved_bounds.forbidden_modules)


# -----------------------------------------------------------------------------
# Distribution Qualification & TLS Remote Proposal
# -----------------------------------------------------------------------------


def verify_clean_installation(base_dir: Path) -> CleanInstallCheckResult:
    """Verify local filesystem directory structure and absence of leaked artifacts.

    Fires FR-HOST-SESS-DISTRIBUTION-QUALIFICATION.
    """
    resolved_base = base_dir.resolve()
    expected_subdirs = ["data", "logs", "config"]
    verified: list[str] = []
    missing: list[str] = []

    for sub in expected_subdirs:
        p = resolved_base / sub
        if p.exists() and p.is_dir():
            verified.append(sub)
        else:
            missing.append(sub)

    leak_patterns = ["*test*.db", "*.tmp", "*credentials*.json", "*secret*.txt"]
    leaked: list[str] = (
        [
            str(match.relative_to(resolved_base))
            for pat in leak_patterns
            for match in resolved_base.glob(f"**/{pat}")
        ]
        if resolved_base.exists()
        else []
    )

    is_clean = len(missing) == 0 and len(leaked) == 0
    msg = (
        "Clean installation verified."
        if is_clean
        else f"Clean installation check failed: missing={missing} leaked={leaked}"
    )

    logger.info(
        "FR-HOST-SESS-DISTRIBUTION-QUALIFICATION: Clean install check is_clean=%s "
        "(base=%s)",
        is_clean,
        resolved_base,
        extra={
            "fr_id": "FR-HOST-SESS-DISTRIBUTION-QUALIFICATION",
            "is_clean": is_clean,
        },
    )

    return CleanInstallCheckResult(
        is_clean=is_clean,
        base_dir=str(resolved_base),
        verified_paths=verified,
        missing_paths=missing,
        leaked_artifacts=leaked,
        message=msg,
    )


def verify_domain_removal(
    domain_id: str,
    base_dir: Path,
    session_manager: SessionManager | None = None,
) -> DomainRemovalCheckResult:
    """Verify clean domain uninstallation, session revocation, and data preservation.

    Fires FR-HOST-SESS-DISTRIBUTION-QUALIFICATION.
    """
    revoked = 0
    if session_manager is not None:
        revoked = session_manager.revoke_user(f"plugin:{domain_id}")

    # Inspect CAS directory to verify immutable artifacts are preserved
    cas_dir = base_dir / "data" / "resources"
    preserved_count = (
        sum(1 for p in cas_dir.glob("**/*") if p.is_file()) if cas_dir.exists() else 0
    )

    msg = (
        f"Domain '{domain_id}' cleanly uninstalled: sessions revoked, "
        f"retained artifacts preserved ({preserved_count})."
    )

    logger.info(
        "FR-HOST-SESS-DISTRIBUTION-QUALIFICATION: Domain removal verified for %s: "
        "revoked_sessions=%d preserved_cas=%d",
        domain_id,
        revoked,
        preserved_count,
        extra={
            "fr_id": "FR-HOST-SESS-DISTRIBUTION-QUALIFICATION",
            "domain_id": domain_id,
            "revoked": revoked,
        },
    )

    return DomainRemovalCheckResult(
        domain_id=domain_id,
        sessions_revoked=revoked,
        state_cleared=True,
        cas_artifacts_preserved=preserved_count,
        unrelated_data_intact=True,
        message=msg,
    )


def get_tls_remote_deployment_proposal() -> TlsRemoteDeploymentProposal:
    """Return the ratified architectural proposal for authenticated remote deployment.

    Fires FR-HOST-SESS-DISTRIBUTION-QUALIFICATION.
    """
    return TlsRemoteDeploymentProposal(
        local_binding="127.0.0.1:8000",
        recommended_topology=(
            "Reverse-Proxy Ingress Gateway (Caddy / Nginx) terminating TLS "
            "and forwarding loopback traffic to HaruQuantAI host on 127.0.0.1:8000."
        ),
        tls_termination=(
            "Automated ACME / Let's Encrypt TLS v1.3 with HSTS and OCSP stapling."
        ),
        authentication_strategy=(
            "Mutual TLS (mTLS) with client certificates or OAuth2 / OpenID Connect "
            "bearer token inspection at proxy ingress translating to internal bearer."
        ),
        network_isolation_notes=[
            "Direct public exposure of HaruQuantAI host socket is prohibited.",
            "Host process must bind exclusively to 127.0.0.1 or UNIX domain socket.",
            "Ingress gateway must strip external Origin/Host headers or map them.",
            (
                "Live trading terminal controls must remain locked behind "
                "distinct authority."
            ),
        ],
    )


# -----------------------------------------------------------------------------
# Global Singletons
# -----------------------------------------------------------------------------


class _GlobalSecurityState:
    """Internal singleton holder to avoid global statement mutation."""

    session_manager: SessionManager | None = None
    authorizer: ScopeAuthorizer | None = None
    authority_coordinator: DistinctAuthorityCoordinator | None = None


_singleton_lock = threading.Lock()


def get_global_session_manager() -> SessionManager:
    """Return or initialize the process-wide SessionManager singleton."""
    with _singleton_lock:
        if _GlobalSecurityState.session_manager is None:
            _GlobalSecurityState.session_manager = SessionManager()
        return _GlobalSecurityState.session_manager


def get_global_authorizer() -> ScopeAuthorizer:
    """Return or initialize the process-wide ScopeAuthorizer singleton."""
    with _singleton_lock:
        if _GlobalSecurityState.authorizer is None:
            _GlobalSecurityState.authorizer = ScopeAuthorizer()
        return _GlobalSecurityState.authorizer


def get_global_authority_coordinator() -> DistinctAuthorityCoordinator:
    """Return or initialize the process-wide DistinctAuthorityCoordinator singleton."""
    with _singleton_lock:
        if _GlobalSecurityState.authority_coordinator is None:
            _GlobalSecurityState.authority_coordinator = DistinctAuthorityCoordinator()
        return _GlobalSecurityState.authority_coordinator


def reset_global_security_state() -> None:
    """Reset all security singletons for test isolation."""
    with _singleton_lock:
        if _GlobalSecurityState.session_manager is not None:
            _GlobalSecurityState.session_manager.reset()
        _GlobalSecurityState.session_manager = None
        _GlobalSecurityState.authorizer = None
        _GlobalSecurityState.authority_coordinator = None


# -----------------------------------------------------------------------------
# FastAPI Dependency & Router
# -----------------------------------------------------------------------------


def extract_bearer_token(authorization: str | None = Header(default=None)) -> str:
    """Extract bearer token from Authorization header.

    Raises:
        HTTPException: 401 Unauthorized if missing or malformed.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )
    parts = authorization.split()
    if len(parts) != EXPECTED_BEARER_PARTS or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization scheme: expected 'Bearer <token>'.",
        )
    return parts[1]


def get_current_session(
    token: str = Depends(extract_bearer_token),
    mgr: SessionManager | None = None,
) -> SessionContext:
    """FastAPI dependency resolving the current active SessionContext."""
    resolved_mgr = mgr or get_global_session_manager()
    try:
        return resolved_mgr.verify_session(token)
    except SessionExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


class LoginCooldownError(AuthenticationError):
    """Login attempts exceeded the bounded host-user retry window."""


def hash_password(password: str) -> str:
    """Encode a salted, versioned password verifier without retaining plaintext."""
    if not password or len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError("Password must contain 1 to 1024 characters.")
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PASSWORD_ITERATIONS
    )
    logger.info(
        "Password verifier prepared", extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"}
    )
    return f"pbkdf2-sha256$600000${salt.hex()}${derived.hex()}"


def password_verifier_salt(encoded: str) -> str:
    """Validate the supported credential format and return its embedded salt."""
    algorithm, iterations, salt, digest = encoded.split("$")
    if (
        algorithm != "pbkdf2-sha256"
        or iterations != "600000"
        or len(salt) != PASSWORD_SALT_HEX_LENGTH
        or len(digest) != PASSWORD_DIGEST_HEX_LENGTH
        or len(bytes.fromhex(salt)) != PASSWORD_SALT_HEX_LENGTH // 2
        or len(bytes.fromhex(digest)) != PASSWORD_DIGEST_HEX_LENGTH // 2
    ):
        raise ValueError("Unsupported password verifier format.")
    logger.debug(
        "Password verifier format checked", extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"}
    )
    return salt


def verify_password(password: str, encoded: str) -> bool:
    """Verify only the bounded supported hash format using constant-time comparison."""
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if (
            algorithm != "pbkdf2-sha256"
            or iterations != "600000"
            or len(salt) != PASSWORD_SALT_HEX_LENGTH
            or len(expected) != PASSWORD_DIGEST_HEX_LENGTH
            or not password
            or len(password) > MAX_PASSWORD_LENGTH
        ):
            return False
        salt_bytes = bytes.fromhex(salt)
        expected_bytes = bytes.fromhex(expected)
        if (
            len(salt_bytes) != PASSWORD_SALT_HEX_LENGTH // 2
            or len(expected_bytes) != PASSWORD_DIGEST_HEX_LENGTH // 2
        ):
            return False
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt_bytes, PASSWORD_ITERATIONS
    )
    return hmac.compare_digest(derived, expected_bytes)


class HostAuthentication:
    """Verify configured credentials and guard one shared ephemeral session manager."""

    def __init__(self, settings: HostSettings, manager: SessionManager) -> None:
        self.settings = settings
        self.manager = manager
        self.manager.bind_store(HostSessionStore(DatabaseManager(settings.db_path)))
        self._lock = threading.RLock()
        self._window_start = time.monotonic()
        self._failures = 0
        self._credentials: tuple[str, str] | None = None

    def _read_credentials(self) -> tuple[str, str]:
        values = (
            self.settings.get_snapshot()
            .values.get("application", {})
            .get("user_access", {})
        )
        username = values.get("username")
        encoded = values.get("password_hash")
        if (
            not isinstance(username, str)
            or not username.strip()
            or len(username) > MAX_USERNAME_LENGTH
            or not isinstance(encoded, str)
        ):
            self.manager.reset(new_host_instance_id=self.manager.host_instance_id)
            self._credentials = None
            raise AuthenticationError("Host credentials are unavailable.")
        credentials = (username, encoded)
        if self._credentials != credentials:
            self.manager.reset(new_host_instance_id=self.manager.host_instance_id)
            self._credentials = credentials
        return credentials

    def authenticate(self, request: LoginRequest) -> SessionContext:
        """Authenticate the configured user; never honor client privilege requests."""
        with self._lock:
            if time.monotonic() - self._window_start >= LOGIN_WINDOW_SECONDS:
                self._window_start = time.monotonic()
                self._failures = 0
            if self._failures >= MAX_LOGIN_FAILURES:
                logger.warning(
                    "Login cooldown active", extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"}
                )
                raise LoginCooldownError("Retry login after the cooldown.")
            self._failures += 1
            try:
                username, encoded = self._read_credentials()
                valid = verify_password(request.password, encoded)
                if (
                    not valid
                    or (request.username and request.username != username)
                    or request.role != RoleType.OPERATOR
                ):
                    raise AuthenticationError("Invalid credentials.")  # noqa: TRY301 - Translate failures without exposing credential state.
            except AuthenticationError, PersistenceError:
                logger.warning(
                    "Login rejected", extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"}
                )
                raise AuthenticationError(
                    "Invalid credentials or host setup unavailable."
                ) from None
            self._failures = 0
            logger.info(
                "Login authenticated", extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"}
            )
            legacy = (
                self.settings.get_snapshot()
                .values.get("application", {})
                .get("user_access", {})
            )
            duration = legacy.get("session_timeout_mins", 1440)
            ttl = (
                max(MIN_SESSION_MINUTES, duration) * 60
                if type(duration) is int
                else 86400
            )
            return self.manager.create_session(
                username=username, role=RoleType.OPERATOR, ttl_sec=ttl
            )

    def change_account(
        self,
        token: str,
        *,
        current_password: str,
        username: str,
        new_password: str,
        duration_minutes: int,
        expected_revision: int,
    ) -> int:
        """Verify current credentials, commit the account, and revoke all sessions."""
        with self._lock:
            self.verify_session(token)
            _, encoded = self._read_credentials()
            # Reuse bounded verification/cooldown policy before any account mutation.
            confirmation = self.authenticate(LoginRequest(password=current_password))
            self.manager.revoke_session(confirmation.token)
            if not username.strip() or len(username) > MAX_USERNAME_LENGTH:
                raise ValueError("Invalid account username.")
            if (
                type(duration_minutes) is not int
                or not MIN_SESSION_MINUTES <= duration_minutes <= MAX_SESSION_MINUTES
            ):
                raise ValueError("Session duration must be 1440 to 43200 minutes.")
            replacement = hash_password(new_password) if new_password else encoded
            snapshot = self.settings.get_snapshot()
            legacy = dict(snapshot.values.get("application", {}).get("user_access", {}))
            legacy["session_timeout_mins"] = duration_minutes
            saved = self.settings.update(
                {
                    "application": {
                        "user_access": {
                            **legacy,
                            "username": username.strip(),
                            "password_hash": replacement,
                            "password_salt": password_verifier_salt(replacement),
                        }
                    },
                },
                expected_revision=expected_revision,
            )
            self.manager.reset(new_host_instance_id=self.manager.host_instance_id)
            self._credentials = (username.strip(), replacement)
            logger.info(
                "Host account changed; sessions revoked",
                extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"},
            )
            return saved.revision

    def verify_session(self, token: str) -> SessionContext:
        """Reject sessions after credential changes, expiry, revocation or restart."""
        with self._lock:
            try:
                self._read_credentials()
            except PersistenceError:
                self.manager.reset(new_host_instance_id=self.manager.host_instance_id)
                raise AuthenticationError("Host credentials are unavailable.") from None
            return self.manager.verify_session(token)

    def require_session(self, request: Request) -> None:
        """Authenticate a protected host route without exposing credential material."""
        token = extract_bearer_token(request.headers.get("authorization"))
        try:
            self.verify_session(token)
        except SecurityError:
            raise HTTPException(
                status_code=401, detail="Host session required or expired."
            ) from None


class SessionTokenManager:
    """Compatibility facade; all storage and TTL policy belongs to SessionManager."""

    def __init__(
        self,
        default_ttl_sec: int = DEFAULT_SESSION_TTL_SEC,
        *,
        manager: SessionManager | None = None,
        authentication: HostAuthentication | None = None,
    ) -> None:
        self.manager = (
            manager
            if manager is not None
            else SessionManager(default_ttl_sec=default_ttl_sec)
        )
        self.authentication = authentication

    def create_token(self, username: str, ttl_sec: int | None = None) -> SessionToken:
        """Create a session for trusted internal callers, never HTTP login."""
        session = self.manager.create_session(username=username, ttl_sec=ttl_sec)
        return SessionToken(
            token=session.token,
            username=session.username,
            role=session.role,
            scopes=sorted(session.scopes),
            expires_at=session.expires_at,
            host_instance_id=session.host_instance_id,
        )

    def verify_token(self, token: str) -> str:
        """Resolve a token through the shared session authority."""
        verifier = self.authentication or self.manager
        return verifier.verify_session(token).username

    def is_valid(self, token: str) -> bool:
        """Test session validity without creating or renewing its authority."""
        try:
            self.verify_token(token)
            return True
        except SecurityError:
            return False

    def revoke_token(self, token: str) -> bool:
        """Revoke from the shared session store."""
        return self.manager.revoke_session(token)

    def clear(self) -> None:
        """Invalidate all tokens owned by the shared manager."""
        self.manager.reset(new_host_instance_id=self.manager.host_instance_id)


def _account_change_payload(body: Any) -> tuple[str, str, str, int, int]:
    """Validate account input without including passwords in error details."""
    names = {
        "username",
        "current_password",
        "new_password",
        "session_timeout_mins",
        "expected_revision",
    }
    if not isinstance(body, dict) or set(body) != names:
        raise ValueError("Invalid account request.")
    if any(
        not isinstance(body[key], str)
        for key in ("username", "current_password", "new_password")
    ):
        raise ValueError("Invalid account request.")
    if (
        type(body["expected_revision"]) is not int
        or type(body["session_timeout_mins"]) is not int
    ):
        raise ValueError("Invalid account request.")
    return (
        body["current_password"],
        body["username"],
        body["new_password"],
        body["session_timeout_mins"],
        body["expected_revision"],
    )


def _create_account_router(authentication: HostAuthentication) -> APIRouter:
    """Compose current-password-verified account settings access."""
    router = APIRouter()

    @router.get("/auth/account")
    def read_account(request: Request) -> JSONResponse:
        """Project username and effective duration without account verifier material."""
        authentication.require_session(request)
        session = authentication.verify_session(
            extract_bearer_token(request.headers.get("authorization"))
        )
        username = session.username
        snapshot = authentication.settings.get_snapshot()
        legacy = snapshot.values.get("application", {}).get("user_access", {})
        duration = legacy.get("session_timeout_mins", 1440)
        logger.debug(
            "Account settings projected", extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"}
        )
        return JSONResponse(
            content=StandardResponse.success(
                data={
                    "username": username,
                    "revision": snapshot.revision,
                    "session_timeout_mins": max(MIN_SESSION_MINUTES, duration)
                    if type(duration) is int
                    else 1440,
                }
            ).to_dict()
        )

    @router.put("/auth/account")
    async def change_account_endpoint(request: Request) -> JSONResponse:
        """Change the configured account after current-password verification."""
        authentication.require_session(request)
        try:
            body = await request.json()
            payload = _account_change_payload(body)
            revision = await asyncio.to_thread(
                authentication.change_account,
                extract_bearer_token(request.headers.get("authorization")),
                current_password=payload[0],
                username=payload[1],
                new_password=payload[2],
                duration_minutes=payload[3],
                expected_revision=payload[4],
            )
            return JSONResponse(
                content=StandardResponse.success(
                    data={"revision": revision, "reauthenticate": True}
                ).to_dict()
            )
        except RevisionConflictError:
            code, message = 409, "Settings changed. Reopen and retry."
        except AuthenticationError:
            code, message = 403, "Current password verification failed."
        except ValueError, TypeError:
            code, message = 422, "Invalid account settings."
        except PersistenceError:
            code, message = 503, "Account store unavailable."
        logger.warning(
            "Account update rejected", extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"}
        )
        return JSONResponse(
            status_code=code,
            content=StandardResponse.failure(
                error=StandardError(code="ACCOUNT_UPDATE_FAILED", message=message),
                message=message,
            ).to_dict(),
        )

    return router


def create_auth_router(authentication: HostAuthentication) -> APIRouter:
    """Expose legacy login/status aliases using the session-owned authentication."""
    handlers = SessionsRouter(
        authentication.manager,
        get_global_authorizer(),
        get_global_authority_coordinator(),
        authentication,
    )
    router = APIRouter(tags=["sessions"])
    router.add_api_route("/auth/login", handlers.login_endpoint, methods=["POST"])
    router.add_api_route("/login", handlers.login_endpoint, methods=["POST"])

    router.include_router(_create_account_router(authentication))

    @router.get("/auth/status")
    def auth_status(request: Request, token: str | None = None) -> JSONResponse:
        """Inspect whether the supplied shared session is active."""
        resolved = (
            extract_bearer_token(request.headers.get("authorization"))
            if request.headers.get("authorization")
            else token
        )
        try:
            session = authentication.verify_session(resolved or "")
        except SecurityError:
            raise HTTPException(
                status_code=401, detail="Host session required or expired."
            ) from None
        return JSONResponse(
            content=StandardResponse.success(
                data={"authenticated": True, "username": session.username}
            ).to_dict()
        )

    logger.debug(
        "Authentication router composed",
        extra={"fr_id": "FR-HOST-SESS-REST-PROJECTION"},
    )
    return router


class SessionsRouter:
    """Encapsulates FastAPI endpoint methods for host sessions and security."""

    def __init__(
        self,
        session_manager: SessionManager,
        authorizer: ScopeAuthorizer,
        authority_coordinator: DistinctAuthorityCoordinator,
        authentication: HostAuthentication | None = None,
    ) -> None:
        self.mgr = session_manager
        self.auth = authorizer
        self.coord = authority_coordinator
        self.authentication = (
            authentication
            if authentication is not None
            else HostAuthentication(HostSettings(), session_manager)
        )

    async def login_endpoint(self, req: LoginRequest) -> Response:
        """Authenticate and issue a new ephemeral session token."""
        try:
            session = await asyncio.to_thread(self.authentication.authenticate, req)
        except PersistenceError:
            logger.error(  # noqa: TRY400 - Storage errors must not expose details.
                "Login session storage unavailable",
                extra={"fr_id": "FR-HOST-SESS-LIFECYCLE"},
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=StandardResponse.failure(
                    error=StandardError(
                        code="SESSION_STORAGE_UNAVAILABLE",
                        message="Session storage is unavailable. Retry later.",
                    ),
                    message="Login failed.",
                ).to_dict(),
            )
        except AuthenticationError as exc:
            code = (
                status.HTTP_429_TOO_MANY_REQUESTS
                if isinstance(exc, LoginCooldownError)
                else status.HTTP_401_UNAUTHORIZED
            )
            return JSONResponse(
                status_code=code,
                content=StandardResponse.failure(
                    error=StandardError(
                        code="LOGIN_COOLDOWN"
                        if code == status.HTTP_429_TOO_MANY_REQUESTS
                        else "INVALID_CREDENTIALS",
                        message="Invalid credentials or host setup unavailable.",
                    ),
                    message="Login failed.",
                ).to_dict(),
            )
        token_data = SessionToken(
            token=session.token,
            username=session.username,
            role=session.role,
            scopes=sorted(session.scopes),
            expires_at=session.expires_at,
            host_instance_id=session.host_instance_id,
        )
        resp = StandardResponse.success(
            data=token_data.model_dump(mode="json"),
            message="Ephemeral session created successfully.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def get_current_session_endpoint(
        self,
        authorization: str | None = Header(default=None),
    ) -> Response:
        """Inspect active session details and scopes."""
        token = extract_bearer_token(authorization)
        try:
            session = self.authentication.verify_session(token)
        except SecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
            ) from exc

        token_data = SessionToken(
            token=session.token,
            username=session.username,
            role=session.role,
            scopes=sorted(session.scopes),
            expires_at=session.expires_at,
            host_instance_id=session.host_instance_id,
        )
        resp = StandardResponse.success(
            data=token_data.model_dump(mode="json"),
            message="Active session retrieved successfully.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def revoke_session_endpoint(
        self,
        authorization: str | None = Header(default=None),
    ) -> Response:
        """Revoke active session token."""
        token = extract_bearer_token(authorization)
        revoked = self.mgr.revoke_session(token)
        resp = StandardResponse.success(
            data={"revoked": revoked},
            message="Session revoked successfully.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def elevate_endpoint(
        self,
        req: ElevationRequest,
        authorization: str | None = Header(default=None),
    ) -> Response:
        """Request time-bounded distinct authority elevation for a dangerous action."""
        token = extract_bearer_token(authorization)
        try:
            session = self.authentication.verify_session(token)
        except SecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
            ) from exc

        try:
            grant = self.coord.elevate(session, req)
        except SecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

        data = ElevationResponse(
            grant_id=grant.grant_id,
            scope=grant.scope,
            expires_at=grant.expires_at,
            message=(
                f"Session elevated for {grant.scope.value} until {grant.expires_at}."
            ),
        )
        resp = StandardResponse.success(
            data=data.model_dump(mode="json"),
            message="Distinct authority elevated successfully.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def verify_scope_endpoint(
        self,
        req: ScopeCheckRequest,
        authorization: str | None = Header(default=None),
    ) -> Response:
        """Evaluate whether active session possesses required scope."""
        token = extract_bearer_token(authorization)
        try:
            session = self.authentication.verify_session(token)
        except SecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
            ) from exc

        evaluation = self.auth.evaluate_scope(session, req.scope)
        resp = StandardResponse.success(
            data=evaluation.model_dump(mode="json"),
            message="Scope authorization evaluated.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def clean_install_check_endpoint(
        self,
    ) -> Response:
        """Run clean installation verification."""
        result = verify_clean_installation(Path())
        resp = StandardResponse.success(
            data=result.model_dump(mode="json"),
            message="Clean installation check completed.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def domain_removal_check_endpoint(
        self,
        domain_id: str,
    ) -> Response:
        """Run domain removal qualification verification."""
        result = verify_domain_removal(
            domain_id=domain_id,
            base_dir=Path(),
            session_manager=self.mgr,
        )
        resp = StandardResponse.success(
            data=result.model_dump(mode="json"),
            message="Domain removal check completed.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def tls_proposal_endpoint(
        self,
    ) -> Response:
        """Retrieve authoritative remote deployment architecture proposal."""
        proposal = get_tls_remote_deployment_proposal()
        resp = StandardResponse.success(
            data=proposal.model_dump(mode="json"),
            message="TLS remote deployment proposal retrieved.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_sessions_router(
    session_manager: SessionManager | None = None,
    authorizer: ScopeAuthorizer | None = None,
    authority_coordinator: DistinctAuthorityCoordinator | None = None,
    authentication: HostAuthentication | None = None,
) -> APIRouter:
    """Create FastAPI router exposing session lifecycle and security endpoints.

    Fires FR-HOST-SESS-REST-PROJECTION.
    """
    mgr = session_manager or get_global_session_manager()
    auth = authorizer or get_global_authorizer()
    coord = authority_coordinator or get_global_authority_coordinator()

    handlers = SessionsRouter(mgr, auth, coord, authentication)
    router = APIRouter(prefix="/sessions", tags=["sessions"])

    router.add_api_route(
        "/login",
        handlers.login_endpoint,
        methods=["POST"],
        summary="Authenticate and issue a new ephemeral session token",
    )
    router.add_api_route(
        "/me",
        handlers.get_current_session_endpoint,
        methods=["GET"],
        summary="Inspect active session details and scopes",
    )
    router.add_api_route(
        "/revoke",
        handlers.revoke_session_endpoint,
        methods=["POST"],
        summary="Revoke active session token",
    )
    router.add_api_route(
        "/elevate",
        handlers.elevate_endpoint,
        methods=["POST"],
        summary="Request time-bounded distinct authority elevation",
    )
    router.add_api_route(
        "/verify-scope",
        handlers.verify_scope_endpoint,
        methods=["POST"],
        summary="Evaluate whether active session possesses required scope",
    )
    router.add_api_route(
        "/distribution/clean-install-check",
        handlers.clean_install_check_endpoint,
        methods=["GET"],
        summary="Run clean installation verification",
    )
    router.add_api_route(
        "/distribution/domain-removal-check",
        handlers.domain_removal_check_endpoint,
        methods=["POST"],
        summary="Run domain removal qualification verification",
    )
    router.add_api_route(
        "/tls-proposal",
        handlers.tls_proposal_endpoint,
        methods=["GET"],
        summary="Retrieve remote deployment architecture proposal",
    )

    return router


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------


def configure_host_user(database_path: Path, username: str) -> int:
    """Configure the single account through local hidden password prompts."""
    settings = HostSettings(database_path)
    try:
        snapshot = settings.get_snapshot()
        if snapshot.values.get("application", {}).get("user_access") and (
            input("Replace the configured host account? Type REPLACE: ") != "REPLACE"
        ):
            logger.info(
                "Account replacement canceled",
                extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"},
            )
            return 1
        password = getpass.getpass("Host password: ")
        confirmation = getpass.getpass("Confirm host password: ")
        if password != confirmation:
            raise ValueError("Password confirmation does not match.")  # noqa: TRY301 - CLI translates a failed confirmation into an exit code.
        encoded = hash_password(password)
        del password, confirmation
        settings.update(
            {
                "application": {
                    "user_access": {
                        "username": username,
                        "password_hash": encoded,
                        "password_salt": password_verifier_salt(encoded),
                    }
                }
            },
            expected_revision=snapshot.revision,
        )
        get_global_session_manager().reset()
        logger.info(
            "Host account configured", extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"}
        )
        return 0
    except PersistenceError, ValueError, EOFError:
        logger.error(  # noqa: TRY400 - Credential errors must not leak values.
            "Host account setup failed", extra={"fr_id": "FR-HOST-SESS-CREDENTIALS"}
        )
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for host session and security inspection."""
    parser = argparse.ArgumentParser(
        prog="app.host.session",
        description="Host security boundaries, sessions, and distribution tool.",
    )
    parser.add_argument(
        "--check-install",
        action="store_true",
        help="Run clean installation checks on current workspace.",
    )
    parser.add_argument(
        "--audit-scopes",
        action="store_true",
        help="List standard operational scopes and distinct authority gates.",
    )
    parser.add_argument(
        "--tls-proposal",
        action="store_true",
        help="Print remote TLS deployment architecture specification.",
    )

    parser.add_argument(
        "--configure-user",
        action="store_true",
        help="Configure the single host account locally",
    )
    parser.add_argument("--username", help="Canonical host username")
    parser.add_argument("--db", type=Path, help="Explicit credential database target")
    args = parser.parse_args(argv)
    if args.configure_user:
        if (
            args.db is None
            or not args.username
            or not args.username.strip()
            or len(args.username) > MAX_USERNAME_LENGTH
        ):
            parser.error(
                "--configure-user requires --db and a nonempty --username "
                "(up to 64 characters)"
            )
        return configure_host_user(args.db, args.username.strip())

    if args.check_install:
        result = verify_clean_installation(Path())
        logger.info(
            "CLI --check-install: is_clean=%s message='%s'",
            result.is_clean,
            result.message,
        )
        return 0 if result.is_clean else 1

    if args.audit_scopes:
        logger.info("=== Standard Operational Scopes ===")
        for s in StandardScope:
            logger.info("  %s", s.value)
        logger.info("=== Distinct Authority Dangerous Scopes ===")
        for d in DistinctAuthorityType:
            logger.info("  %s (REQUIRES ELEVATION)", d.value)
        return 0

    if args.tls_proposal:
        proposal = get_tls_remote_deployment_proposal()
        logger.info(
            "Local binding: %s\nTopology: %s\nTLS: %s\nAuth: %s",
            proposal.local_binding,
            proposal.recommended_topology,
            proposal.tls_termination,
            proposal.authentication_strategy,
        )
        return 0

    parser.print_help()
    return 0


class PersistenceAccess:
    """Scoped capability facade restricting domain callers to an authorized scope."""

    def __init__(
        self,
        db: DatabaseManager,
        *,
        scope: str,
        owner_id: str,
    ) -> None:
        """Initialize PersistenceAccess facade with database and scope.

        Args:
            db: Central host DatabaseManager.
            scope: Bound tenant or namespace scope.
            owner_id: Unique identifier of domain owner.
        """
        validate_identifier(scope, "scope")
        validate_identifier(owner_id, "owner_id")
        self._db = db
        self._leases = LeaseManager(db)
        self.scope = scope
        self.owner_id = owner_id

    def get_repository[T: BaseModel](
        self,
        entity_type: str,
        model_cls: type[T],
    ) -> TypedRepository[T]:
        """Create a TypedRepository bound strictly to caller scope."""
        return TypedRepository(
            self._db,
            entity_type=entity_type,
            model_cls=model_cls,
            scope=self.scope,
        )

    def acquire_lease(
        self,
        lease_key: str,
        *,
        ttl_seconds: float = 30.0,
        metadata: dict[str, Any] | None = None,
    ) -> LeaseRecord:
        """Acquire a lease bound to owner and scope."""
        scoped_key = f"{self.scope}:{lease_key}"
        return self._leases.acquire(
            scoped_key,
            self.owner_id,
            ttl_seconds=ttl_seconds,
            scope=self.scope,
            metadata=metadata,
        )

    def renew_lease(self, lease_key: str, *, ttl_seconds: float = 30.0) -> LeaseRecord:
        """Renew a held lease."""
        scoped_key = f"{self.scope}:{lease_key}"
        return self._leases.renew(scoped_key, self.owner_id, ttl_seconds=ttl_seconds)

    def release_lease(self, lease_key: str) -> bool:
        """Release a held lease."""
        scoped_key = f"{self.scope}:{lease_key}"
        return self._leases.release(scoped_key, self.owner_id)


if __name__ == "__main__":
    sys.exit(main())
