"""Secret-reference resolution and rotation contracts."""
# ruff: noqa: ARG002

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import Field

from app.services.trading.config.models import SecretReference, TradingConfigModel
from app.services.trading.contracts import MutationCapability
from app.utils.logger import logger


class SecretResolutionResult(TradingConfigModel):
    """Redacted result of secret reference resolution."""

    reference: str
    version: str | None = None
    resolved: bool
    expires_at: str | None = None
    redacted_value: str = "[REDACTED]"


class CredentialRotationResult(TradingConfigModel):
    """Outcome of mid-session credential rotation."""

    reference: str
    status: str
    mutation_capability: MutationCapability
    severity: str
    message: str
    retry_with_stale_credentials: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)


@runtime_checkable
class SecretResolver(Protocol):
    """External secret resolver interface."""

    def resolve_metadata(self, reference: SecretReference) -> SecretResolutionResult:
        """Resolve secret metadata without returning raw secret values.

        Args:
            reference: Secret reference.

        Returns:
            SecretResolutionResult: Redacted resolution metadata.
        """
        logger.debug("SecretResolver.resolve_metadata protocol invoked.")
        raise NotImplementedError


@runtime_checkable
class ReauthenticationAdapter(Protocol):
    """Broker adapter re-authentication protocol."""

    def reauthenticate(self, reference: SecretReference) -> bool:
        """Re-authenticate using the adapter-owned secret path.

        Args:
            reference: Secret reference.

        Returns:
            bool: True when re-authentication succeeds.
        """
        logger.debug("ReauthenticationAdapter.reauthenticate protocol invoked.")
        raise NotImplementedError


def resolve_secret_reference(
    *,
    reference: SecretReference,
    resolver: SecretResolver,
) -> SecretResolutionResult:
    """Resolve a secret reference without exposing the raw value.

    Args:
        reference: Secret reference.
        resolver: External resolver dependency.

    Returns:
        SecretResolutionResult: Redacted resolution result.
    """
    logger.info("Resolving trading secret reference metadata.")
    result = resolver.resolve_metadata(reference)
    if result.redacted_value != "[REDACTED]":
        raise ValueError("secret resolver must not return raw secret values.")
    return result


def handle_credential_rotation(
    *,
    reference: SecretReference,
    adapter: ReauthenticationAdapter,
) -> CredentialRotationResult:
    """Handle mid-session credential rotation through adapter re-authentication.

    Args:
        reference: Rotated secret reference.
        adapter: Broker adapter re-authentication dependency.

    Returns:
        CredentialRotationResult: Rotation outcome. Failed rotation transitions
        capability to read-only and never retries stale credentials.
    """
    logger.info("Handling trading credential rotation.")
    try:
        if adapter.reauthenticate(reference):
            return CredentialRotationResult(
                reference=reference.reference,
                status="success",
                mutation_capability=MutationCapability.PACKAGED_ONLY,
                severity="info",
                message="Credential rotation completed via adapter re-authentication.",
            )
    except RuntimeError as exc:
        logger.error("Credential rotation failed: {}.", exc)
    return CredentialRotationResult(
        reference=reference.reference,
        status="error",
        mutation_capability=MutationCapability.READ_ONLY,
        severity="high",
        message="Credential rotation failed; session downgraded to read_only.",
        retry_with_stale_credentials=False,
    )
