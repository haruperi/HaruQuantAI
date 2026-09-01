"""Default-deny provider account and environment permissions."""

from __future__ import annotations

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.kernel.time import utc_now
from app.services.brokers._shared.state import _account_digest, _text

logger = get_logger(__name__)


def create_environment_permission_record(
    parameters: tuple[object, ...], *, request_id: str
) -> object:
    """Lazily delegate permission creation to Brokers persistence.

    Args:
        parameters: Ordered permission record values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction response.
    """
    from app.services.brokers.persistence import create_environment_permission_record

    return create_environment_permission_record(parameters, request_id=request_id)


def read_environment_permission(
    provider_code: str,
    account_digest: str,
    environment: str,
    as_of: str,
    *,
    request_id: str,
) -> object:
    """Lazily delegate permission reads to Brokers persistence.

    Args:
        provider_code: Exact provider identifier.
        account_digest: Redacted account identity.
        environment: Exact environment classification.
        as_of: Permission evaluation timestamp.
        request_id: Caller trace identity.

    Returns:
        Data-owned read response.
    """
    from app.services.brokers.persistence import read_environment_permission as read

    return read(
        provider_code,
        account_digest,
        environment,
        as_of,
        request_id=request_id,
    )


def register_broker_environment_permission(
    provider_code: str,
    account_reference: str,
    environment: str,
    *,
    allow_read: bool,
    allow_mutation: bool,
    effective_from: str,
    request_id: str,
) -> object:
    """Register one explicit environment/account permission.

    Args:
        provider_code: Exact provider identifier.
        account_reference: Provider account reference, stored only as a digest.
        environment: Exact environment classification.
        allow_read: Whether provider reads are admitted.
        allow_mutation: Whether provider mutations are technically admitted.
        effective_from: Inclusive permission timestamp.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction response.

    Raises:
        ValueError: If live mutation permission is requested through this
            administrative boundary or an input is invalid.
    """
    normalized_environment = _text(environment, "environment").lower()
    if allow_mutation and normalized_environment == "live":
        logger.bind(
            provider_code=_text(provider_code, "provider_code"),
            environment=normalized_environment,
            request_id=_text(request_id, "request_id"),
        ).warning("Rejected direct live broker mutation permission")
        raise ValueError("live mutation permission requires Trading admission")
    logger.bind(
        provider_code=_text(provider_code, "provider_code"),
        environment=normalized_environment,
        allow_read=allow_read,
        allow_mutation=allow_mutation,
        request_id=_text(request_id, "request_id"),
    ).info("Registering explicit broker environment permission")
    updated_at = utc_now().isoformat()
    return create_environment_permission_record(
        (
            generate_id("led"),
            _text(provider_code, "provider_code"),
            _account_digest(account_reference),
            normalized_environment,
            int(allow_read),
            int(allow_mutation),
            1,
            _text(effective_from, "effective_from"),
            None,
            _text(request_id, "request_id"),
            updated_at,
        ),
        request_id=request_id,
    )


def get_broker_environment_permission(
    provider_code: str,
    account_reference: str,
    environment: str,
    *,
    as_of: str,
    request_id: str,
) -> object:
    """Read one explicit permission; a missing row means deny.

    Args:
        provider_code: Exact provider identifier.
        account_reference: Provider account reference, used only for its digest.
        environment: Exact environment classification.
        as_of: Permission evaluation timestamp.
        request_id: Caller trace identity.

    Returns:
        Data-owned response carrying zero rows for default deny or one explicit
        permission row.
    """
    normalized_environment = _text(environment, "environment").lower()
    normalized_request_id = _text(request_id, "request_id")
    logger.bind(
        provider_code=_text(provider_code, "provider_code"),
        environment=normalized_environment,
        request_id=normalized_request_id,
    ).info("Reading explicit broker environment permission")
    return read_environment_permission(
        _text(provider_code, "provider_code"),
        _account_digest(account_reference),
        normalized_environment,
        _text(as_of, "as_of"),
        request_id=normalized_request_id,
    )
