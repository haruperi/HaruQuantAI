"""Transport authentication and network origin authorization feature.

Feature:
    FEAT-GATEWAY-AUTH

Purpose:
    Provides transport identity validation, bearer/API token verification
    (matching SQX BrowserToken, sq-auth-token, and Bearer tokens), loopback
    origin enforcement, and remote access gating under capability
    `gateway.authorization@1`.

Key capabilities:
    * Loopback address validation (localhost, 127.0.0.1, ::1).
    * Remote connection gating (rejects non-loopback requests unless enabled).
    * Token and Bearer credential verification.

Python API usage:
    auth_service = ctx.require(GATEWAY_AUTHORIZATION)
    ctx_info = auth_service.authenticate_request(headers, client_host="127.0.0.1")

CLI usage:
    uv run python -m tests.examples.05_gateway
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from app.contracts.gateway import (
    GATEWAY_AUTHORIZATION,
    GATEWAY_PERSISTENCE,
    AuthContext,
    AuthenticationError,
    GatewayError,
    GatewayPersistenceService,
)
from app.contracts.gateway import (
    GatewayAuthorization as IGatewayAuthorization,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

_DEFAULT_LOOPBACK_HOSTS: frozenset[str] = frozenset({"127.0.0.1", "::1", "localhost"})


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AuthorizationConfig:
    """Runtime configuration for transport authorization."""

    token_auth_enabled: bool = False
    remote_access_allowed: bool = False
    static_tokens: tuple[str, ...] = ()
    auth_header_name: str = "X-API-Key"
    loopback_hosts: frozenset[str] = _DEFAULT_LOOPBACK_HOSTS

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not self.auth_header_name or not self.auth_header_name.strip():
            msg = "auth_header_name cannot be empty"
            raise ValueError(msg)
        if not self.loopback_hosts:
            msg = "loopback_hosts cannot be empty"
            raise ValueError(msg)


# ---------------------------------------------------------------------------
# Service Implementation
# ---------------------------------------------------------------------------


class AuthorizationService(IGatewayAuthorization):
    """Implement transport security and origin gating."""

    def __init__(
        self,
        config: AuthorizationConfig,
        persistence: GatewayPersistenceService | None = None,
    ) -> None:
        """Initialize the authorization service.

        Args:
            config: Runtime configuration.
            persistence: Optional persistence service for dynamic settings/tokens.
        """
        self._config = config
        self._persistence = persistence
        self._remote_allowed = config.remote_access_allowed

        # If persistence is present and has stored remote_access setting, sync it
        if self._persistence is not None:
            val = self._persistence.get_setting("remote_access")
            if val is not None:
                self._remote_allowed = val.lower() in {"1", "true", "yes"}

    @override
    def authenticate_request(
        self,
        headers: Mapping[str, str],
        client_host: str,
    ) -> AuthContext:
        """Validate request headers and origin against transport security policy.

        Args:
            headers: HTTP request headers dictionary.
            client_host: Client IP address or hostname.

        Returns:
            Validated `AuthContext`.

        Raises:
            AuthenticationError: If credentials or origin fail validation.
        """
        is_loopback = client_host in self._config.loopback_hosts

        # 1. Origin check: non-loopback requires remote access enabled
        if not is_loopback and not self.is_remote_access_enabled():
            logger.warning(
                "remote_access_denied",
                client_host=client_host,
            )
            msg = "Remote access is disabled; only loopback requests are accepted"
            raise AuthenticationError(msg)

        # 2. Token authentication check (if enabled)
        if self._config.token_auth_enabled:
            token = self._extract_token(headers)
            if not token:
                logger.warning("auth_token_missing", client_host=client_host)
                msg = "Missing required authentication credentials"
                raise AuthenticationError(msg)

            if not self._is_token_valid(token):
                logger.warning("auth_token_invalid", client_host=client_host)
                msg = "Invalid authentication token"
                raise AuthenticationError(msg)

            client_id = f"token-client-{client_host}"
        else:
            client_id = f"loopback-{client_host}" if is_loopback else client_host

        return AuthContext(
            client_id=client_id,
            authenticated=True,
            is_loopback=is_loopback,
            scopes=("read", "write") if is_loopback else ("read",),
        )

    def _extract_token(self, headers: Mapping[str, str]) -> str | None:
        """Extract auth token from headers (X-API-Key, sq-auth-token, or Bearer)."""
        # Case-insensitive header matching
        normalized = {k.lower(): v for k, v in headers.items()}

        # 1. Check custom configured header (e.g. x-api-key)
        custom_key = self._config.auth_header_name.lower()
        if custom_key in normalized:
            return normalized[custom_key]

        # 2. Check SQX reference token header (sq-auth-token)
        if "sq-auth-token" in normalized:
            return normalized["sq-auth-token"]

        # 3. Check Authorization header
        auth_header = normalized.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:].strip()

        return None

    def _is_token_valid(self, token: str) -> bool:
        """Validate token against static tokens and persistent storage."""
        if token in self._config.static_tokens:
            return True
        return self._persistence is not None and self._persistence.verify_token(token)

    @override
    def is_remote_access_enabled(self) -> bool:
        """Return whether remote (non-loopback) connections are permitted.

        Returns:
            True if remote access is enabled, False if loopback-only.
        """
        return self._remote_allowed

    @override
    def set_remote_access(self, enabled: bool) -> None:
        """Toggle remote (non-loopback) access permission.

        Args:
            enabled: Desired remote access status.
        """
        self._remote_allowed = enabled
        if self._persistence is not None:
            self._persistence.set_setting(
                "remote_access", "true" if enabled else "false"
            )
        logger.info("remote_access_updated", enabled=enabled)

    @override
    def issue_token(
        self,
        name: str,
        scopes: Sequence[str] = ("read",),
    ) -> str:
        """Generate, persist, and return a new cryptographically secure token.

        Args:
            name: Human-readable token name or description.
            scopes: Allowed scopes.

        Returns:
            Plaintext token string.

        Raises:
            GatewayError: If persistence capability is not available.
        """
        if self._persistence is None:
            msg = "Cannot issue token: persistence capability is not available"
            raise GatewayError(msg)
        token = secrets.token_urlsafe(32)
        self._persistence.store_token(token, name)
        logger.info("token_issued", name=name)
        return token


# ---------------------------------------------------------------------------
# Feature Specification and Wiring
# ---------------------------------------------------------------------------

SPEC = FeatureSpec(
    name="gateway.authorization",
    provides=frozenset({GATEWAY_AUTHORIZATION}),
    requires=frozenset(),
    optional=frozenset({GATEWAY_PERSISTENCE}),
    description="Transport authentication and loopback/remote origin security.",
)


class AuthorizationFeature:
    """Composition feature wiring for gateway authorization."""

    def __init__(self, config: AuthorizationConfig | None = None) -> None:
        """Initialize the feature with optional configuration.

        Args:
            config: Optional runtime configuration.
        """
        self._config = config or AuthorizationConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the authorization feature and publish capability.

        Args:
            context: Feature composition context.
        """
        persistence = context.optional(GATEWAY_PERSISTENCE)
        service = AuthorizationService(self._config, persistence=persistence)
        context.provide(GATEWAY_AUTHORIZATION, service)

    async def stop(self) -> None:
        """Stop feature and clean up resources."""


def feature() -> AuthorizationFeature:
    """Factory creating the default AuthorizationFeature.

    Returns:
        Configured feature instance.
    """
    return AuthorizationFeature()
