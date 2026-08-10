"""Persistent route references and recovery cursors."""

from app.services.brokers._shared.state import _account_digest, _text
from app.utils import get_logger, utc_now

logger = get_logger(__name__)


def upsert_route_recovery_record(
    parameters: tuple[object, ...], *, request_id: str
) -> object:
    """Lazily delegate route recovery persistence.

    Args:
        parameters: Ordered route recovery values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction response.
    """
    from app.services.brokers.persistence import upsert_route_recovery_record as upsert

    return upsert(parameters, request_id=request_id)


def read_route_recovery(route_ref: str, *, request_id: str) -> object:
    """Lazily delegate route recovery reads.

    Args:
        route_ref: Stable route reference.
        request_id: Caller trace identity.

    Returns:
        Data-owned read response.
    """
    from app.services.brokers.persistence import read_route_recovery as read

    return read(route_ref, request_id=request_id)


def record_broker_route_recovery(
    route_ref: str,
    provider_code: str,
    account_reference: str,
    environment: str,
    recovery_cursor: str,
    uncertainty: str,
    *,
    request_id: str,
) -> object:
    """Atomically record an authoritative route recovery position.

    Args:
        route_ref: Stable route reference.
        provider_code: Exact provider identity.
        account_reference: Account reference, stored only as a digest.
        environment: Exact provider environment.
        recovery_cursor: Provider-authored recovery cursor.
        uncertainty: Current reconciliation uncertainty classification.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction response.

    Raises:
        ValueError: If an input is empty or unbounded.
    """
    normalized_request_id = _text(request_id, "request_id")
    logger.bind(
        route_ref=_text(route_ref, "route_ref"),
        provider_code=_text(provider_code, "provider_code"),
        environment=_text(environment, "environment").lower(),
        request_id=normalized_request_id,
    ).info("Recording authoritative broker route recovery")
    return upsert_route_recovery_record(
        (
            _text(route_ref, "route_ref"),
            _text(provider_code, "provider_code"),
            _account_digest(account_reference),
            _text(environment, "environment").lower(),
            _text(recovery_cursor, "recovery_cursor"),
            _text(uncertainty, "uncertainty"),
            normalized_request_id,
            utc_now().isoformat(),
        ),
        request_id=request_id,
    )


def get_broker_route_recovery(route_ref: str, *, request_id: str) -> object:
    """Read one authoritative route recovery position.

    Args:
        route_ref: Stable route reference.
        request_id: Caller trace identity.

    Returns:
        Data-owned response carrying at most one recovery row.

    Raises:
        ValueError: If an input is empty or unbounded.
    """
    normalized_route_ref = _text(route_ref, "route_ref")
    normalized_request_id = _text(request_id, "request_id")
    logger.bind(
        route_ref=normalized_route_ref,
        request_id=normalized_request_id,
    ).info("Reading authoritative broker route recovery")
    return read_route_recovery(normalized_route_ref, request_id=normalized_request_id)
