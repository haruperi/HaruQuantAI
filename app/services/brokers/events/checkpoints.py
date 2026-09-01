"""Persistent broker event source and deduplication checkpoints."""

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.kernel.time import utc_now
from app.services.brokers._shared.state import _account_digest, _text

logger = get_logger(__name__)


def upsert_event_checkpoint_record(
    parameters: tuple[object, ...], *, request_id: str
) -> object:
    """Lazily delegate event checkpoint persistence.

    Args:
        parameters: Ordered event checkpoint values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction response.
    """
    from app.services.brokers.persistence import (
        upsert_event_checkpoint_record as upsert,
    )

    return upsert(parameters, request_id=request_id)


def read_event_checkpoint(
    provider_code: str,
    account_digest: str,
    source_stream: str,
    *,
    request_id: str,
) -> object:
    """Lazily delegate event checkpoint reads.

    Args:
        provider_code: Exact provider identifier.
        account_digest: Redacted account identity.
        source_stream: Exact provider source stream.
        request_id: Caller trace identity.

    Returns:
        Data-owned read response.
    """
    from app.services.brokers.persistence import read_event_checkpoint as read

    return read(
        provider_code,
        account_digest,
        source_stream,
        request_id=request_id,
    )


def record_broker_event_checkpoint(
    provider_code: str,
    account_reference: str,
    source_stream: str,
    source_cursor: str,
    event_digest: str,
    *,
    source_sequence: int | None = None,
    request_id: str,
) -> object:
    """Atomically advance one accepted broker event checkpoint.

    Args:
        provider_code: Exact provider identity.
        account_reference: Account reference, stored only as a digest.
        source_stream: Exact provider source stream.
        source_cursor: Provider-authored source cursor.
        event_digest: Canonical digest of the accepted event.
        source_sequence: Optional provider-authored sequence number.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction response.

    Raises:
        ValueError: If text is invalid or sequence is negative.
    """
    if source_sequence is not None and source_sequence < 0:
        logger.bind(
            provider_code=_text(provider_code, "provider_code"),
            source_stream=_text(source_stream, "source_stream"),
            request_id=_text(request_id, "request_id"),
        ).warning("Rejected invalid broker event checkpoint sequence")
        raise ValueError("source_sequence must be non-negative")
    logger.bind(
        provider_code=_text(provider_code, "provider_code"),
        source_stream=_text(source_stream, "source_stream"),
        request_id=_text(request_id, "request_id"),
    ).info("Advancing broker event checkpoint")
    return upsert_event_checkpoint_record(
        (
            generate_id("led"),
            _text(provider_code, "provider_code"),
            _account_digest(account_reference),
            _text(source_stream, "source_stream"),
            _text(source_cursor, "source_cursor"),
            source_sequence,
            _text(event_digest, "event_digest"),
            _text(request_id, "request_id"),
            utc_now().isoformat(),
        ),
        request_id=request_id,
    )


def get_broker_event_checkpoint(
    provider_code: str,
    account_reference: str,
    source_stream: str,
    *,
    request_id: str,
) -> object:
    """Read one broker event source checkpoint.

    Args:
        provider_code: Exact provider identity.
        account_reference: Account reference, used only for its digest.
        source_stream: Exact provider source stream.
        request_id: Caller trace identity.

    Returns:
        Data-owned response carrying at most one checkpoint row.

    Raises:
        ValueError: If an input is empty or unbounded.
    """
    normalized_request_id = _text(request_id, "request_id")
    logger.bind(
        provider_code=_text(provider_code, "provider_code"),
        source_stream=_text(source_stream, "source_stream"),
        request_id=normalized_request_id,
    ).info("Reading broker event checkpoint")
    return read_event_checkpoint(
        _text(provider_code, "provider_code"),
        _account_digest(account_reference),
        _text(source_stream, "source_stream"),
        request_id=normalized_request_id,
    )
