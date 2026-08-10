"""Shared persistence delegation for provider-owned health checkpoints."""

from __future__ import annotations

from decimal import Decimal

from app.services.brokers._shared.state import (
    _account_digest,
    _optional_decimal,
    _text,
)
from app.utils import generate_id, get_logger, utc_now

logger = get_logger(__name__)


def create_health_record(parameters: tuple[object, ...], *, request_id: str) -> object:
    """Lazily delegate health persistence to avoid Data initialization cycles.

    Args:
        parameters: Ordered health record values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction response.
    """
    from app.services.brokers.persistence import create_health_record as create_record

    return create_record(parameters, request_id=request_id)


def _record_health_checkpoint(
    provider_code: str,
    account_reference: str,
    environment: str,
    health_status: str,
    *,
    latency_ms: Decimal | str | None,
    error_rate: Decimal | str | None,
    maintenance: bool,
    route_ready: bool,
    observed_at: str,
    request_id: str,
) -> object:
    """Persist one redacted provider health checkpoint.

    Args:
        provider_code: Exact provider identifier.
        account_reference: Provider account reference, stored only as a digest.
        environment: Exact provider environment.
        health_status: Provider health classification.
        latency_ms: Optional measured latency.
        error_rate: Optional measured error rate.
        maintenance: Whether provider maintenance is reported.
        route_ready: Whether the channel is technically ready.
        observed_at: Provider observation timestamp.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction response.

    Raises:
        ValueError: If any input is invalid or unbounded.
    """
    created_at = utc_now().isoformat()
    logger.bind(
        provider_code=_text(provider_code, "provider_code"),
        environment=_text(environment, "environment"),
        request_id=_text(request_id, "request_id"),
    ).info("Recording redacted broker health checkpoint")
    return create_health_record(
        (
            generate_id("led"),
            _text(provider_code, "provider_code"),
            _account_digest(account_reference),
            _text(environment, "environment"),
            _text(health_status, "health_status"),
            _optional_decimal(latency_ms, "latency_ms"),
            _optional_decimal(error_rate, "error_rate"),
            int(maintenance),
            int(route_ready),
            _text(observed_at, "observed_at"),
            _text(request_id, "request_id"),
            created_at,
        ),
        request_id=request_id,
    )
