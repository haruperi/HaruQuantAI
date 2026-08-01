"""Secret-reference resolution at the Brokers composition boundary."""

from collections.abc import Mapping

from app.services.api.identity import resolve_credential_reference
from app.services.brokers import build_broker_connection_config as _build_broker_config
from app.utils import get_logger

logger = get_logger(__name__)


def build_broker_connection_config(
    *,
    credential_reference: str,
    owner_id: str,
    key_set: Mapping[str, bytes],
    request_id: str,
    broker_id: str,
    environment: str,
    account_reference: str | None = None,
    provider_enabled: bool = True,
) -> object:
    """Resolve an opaque credential and construct a Brokers-owned config.

    Args:
        credential_reference: UI/API-owned opaque secret reference.
        owner_id: Authenticated credential owner.
        key_set: Externally provisioned in-memory encryption keys.
        request_id: Canonical request identifier.
        broker_id: Brokers-owned provider identifier.
        environment: Brokers-owned target environment.
        account_reference: Optional non-secret account label.
        provider_enabled: Whether provider connections are enabled.

    Returns:
        Immutable Brokers-owned connection configuration.
    """
    logger.info("Resolving credential reference for Brokers composition")
    credentials = resolve_credential_reference(
        credential_reference,
        owner_id=owner_id,
        key_set=key_set,
        request_id=request_id,
    )
    return _build_broker_config(
        broker_id=broker_id,
        environment=environment,
        account_reference=account_reference,
        credentials=credentials,
        provider_enabled=provider_enabled,
    )


__all__ = ("build_broker_connection_config",)
