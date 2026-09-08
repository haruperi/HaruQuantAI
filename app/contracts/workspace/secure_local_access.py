"""Public contract for secure local access, secrets, and host security."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from pydantic import Field

from app.contracts.common.models import Uuid7, WireModel
from app.contracts.workspace.models import (
    LocalSession,
    SecretName,
    SecretRef,
    SystemHealth,
    SystemReadiness,
    WorkspaceRef,
)


class SecretCreateRequest(WireModel):
    """Request to create an opaque secret reference bound to an adapter and purpose."""

    workspace_id: Uuid7
    name: SecretName
    secret_value: str
    allowed_adapter_generation: str
    allowed_purpose: str
    schema_version: Literal[1] = 1


class SecretResolveRequest(WireModel):
    """Request to resolve an opaque secret reference by an authorized caller."""

    workspace_id: Uuid7
    secret_id: Uuid7
    adapter_generation: str
    purpose: str
    caller_role: str = Field(default="adapter")
    schema_version: Literal[1] = 1


class SecretRotateRequest(WireModel):
    """Request to rotate an existing secret value and advance generation."""

    workspace_id: Uuid7
    secret_id: Uuid7
    new_secret_value: str
    new_adapter_generation: str
    allowed_purpose: str | None = None
    schema_version: Literal[1] = 1


class SecretRevokeRequest(WireModel):
    """Request to revoke a secret reference immediately."""

    workspace_id: Uuid7
    secret_id: Uuid7
    reason: str | None = None
    schema_version: Literal[1] = 1


class ResolvedSecret(WireModel):
    """Decrypted/resolved secret returned exclusively to an authorized adapter."""

    secret_id: Uuid7
    name: SecretName
    secret_value: str
    row_version: int = Field(default=1, ge=1)
    adapter_generation: str
    purpose: str
    schema_version: Literal[1] = 1


@runtime_checkable
class SecureLocalAccessCapability(Protocol):
    """Capability protocol for local access security, host policies, and secrets."""

    def create_secret_reference(
        self,
        request: SecretCreateRequest,
    ) -> SecretRef:
        """Create and store an opaque secret reference bound to adapter and purpose.

        Args:
            request: Secret creation parameters.

        Returns:
            Opaque SecretRef without secret values.
        """
        ...

    def resolve_secret_reference(
        self,
        request: SecretResolveRequest,
    ) -> ResolvedSecret:
        """Resolve a raw secret value strictly for authorized adapter and purpose.

        Args:
            request: Secret resolution request.

        Returns:
            ResolvedSecret with secret value inside adapter boundary.

        Raises:
            SecretResolutionDeniedError: If caller or purpose is unauthorized.
            SecretNotFoundError: If secret reference does not exist.
            SecretRevokedError: If secret reference has been revoked.
        """
        ...

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
        ...

    def revoke_secret_reference(
        self,
        request: SecretRevokeRequest,
    ) -> None:
        """Revoke a secret reference immediately.

        Args:
            request: Revocation request.

        Raises:
            SecretNotFoundError: If secret reference does not exist.
        """
        ...

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
            client_id: Identifier of the launcher client requesting the session.
            is_launcher_connected: True if caller is launcher-connected.
            client_host: Host IP of the client connection (loopback by default).
            ttl_seconds: Optional session lifetime in seconds.

        Returns:
            LocalSession with unique token and expiry timestamp.
        """
        ...

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
        """
        ...

    def revoke_local_session(self, token: str) -> None:
        """Revoke a previously issued local session token.

        Args:
            token: Session token to invalidate immediately.
        """
        ...

    def check_system_health(self) -> SystemHealth:
        """Expose operational health status, functional before full readiness.

        Returns:
            SystemHealth describing runtime component health.
        """
        ...

    def report_system_readiness(
        self,
        workspace: Path | WorkspaceRef | None = None,
    ) -> SystemReadiness:
        """Expose system readiness without disclosing secrets or absolute user paths.

        Args:
            workspace: Optional workspace root or WorkspaceRef to verify.

        Returns:
            SystemReadiness describing readiness, schema, and worker status.
        """
        ...


__all__ = [
    "ResolvedSecret",
    "SecretCreateRequest",
    "SecretRef",
    "SecretResolveRequest",
    "SecretRevokeRequest",
    "SecretRotateRequest",
    "SecureLocalAccessCapability",
]
