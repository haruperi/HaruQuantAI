"""Deterministic bounded FX path acquisition from an injected rate provider."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol

from app.services.data.contracts.errors import DataError
from app.services.data.contracts.fx import (
    FXConversionEvidence,
    FXConversionRequest,
    FXRateLeg,
)
from app.utils import logger

_SYNTHETIC_PATH_LEGS = 2


class FXRateProvider(Protocol):
    """Read-only provider of exact direct FX-rate legs."""

    def get_rate_leg(
        self,
        *,
        source_currency: str,
        target_currency: str,
        as_of: datetime,
        request_id: str,
    ) -> FXRateLeg:
        """Return one exact direct leg or raise a canonical DATA failure."""
        ...


def _read_leg(
    request: FXConversionRequest,
    provider: FXRateProvider,
    source_currency: str,
    target_currency: str,
) -> FXRateLeg | None:
    """Read and validate one exact direct rate leg."""
    logger.debug("Reading explicit FX leg %s/%s", source_currency, target_currency)
    try:
        leg = provider.get_rate_leg(
            source_currency=source_currency,
            target_currency=target_currency,
            as_of=request.as_of,
            request_id=request.request_id,
        )
    except DataError as error:
        if error.code in {"DATA_NOT_FOUND", "SOURCE_UNAVAILABLE"}:
            return None
        raise
    except Exception as error:
        logger.error("FX rate provider failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "fx_rate"},
            request_id=request.request_id,
        ) from error
    if (
        leg.source_currency != source_currency
        or leg.target_currency != target_currency
        or not leg.provenance
    ):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"operation": "fx_rate"},
            request_id=request.request_id,
        )
    age = request.as_of - leg.as_of
    if age.total_seconds() < 0 or age.total_seconds() >= request.max_age_seconds:
        raise DataError(
            "STALE_EVIDENCE",
            safe_details={"operation": "fx_rate"},
            request_id=request.request_id,
        )
    return leg


def _select_path(
    request: FXConversionRequest,
    provider: FXRateProvider,
) -> tuple[FXRateLeg, ...]:
    """Select direct first, then declared intermediates in caller order."""
    logger.info("Selecting deterministic FX path for request %s", request.request_id)
    direct = _read_leg(
        request,
        provider,
        request.source_currency,
        request.target_currency,
    )
    if direct is not None:
        return (direct,)
    if request.max_legs < _SYNTHETIC_PATH_LEGS:
        raise DataError("DATA_NOT_FOUND", request_id=request.request_id)
    for intermediate in request.allowed_intermediates:
        first = _read_leg(
            request,
            provider,
            request.source_currency,
            intermediate,
        )
        if first is None:
            continue
        second = _read_leg(
            request,
            provider,
            intermediate,
            request.target_currency,
        )
        if second is not None:
            return (first, second)
    raise DataError("DATA_NOT_FOUND", request_id=request.request_id)


def get_fx_conversion_evidence(
    request: FXConversionRequest,
    provider: FXRateProvider,
) -> FXConversionEvidence:
    """Acquire an exact bounded direct or two-leg FX conversion path.

    Args:
        request: Currency pair, freshness, and explicit path policy.
        provider: Caller-injected exact direct-rate provider.

    Returns:
        Immutable exact conversion evidence.

    Raises:
        DataError: If no allowed fresh path can be proven.
    """
    logger.info("Acquiring FX conversion evidence for request %s", request.request_id)
    legs = _select_path(request, provider)
    composite = Decimal(1)
    for leg in legs:
        composite *= leg.rate
    expires_at = min(
        leg.as_of + timedelta(seconds=request.max_age_seconds) for leg in legs
    )
    return FXConversionEvidence(
        source_currency=request.source_currency,
        target_currency=request.target_currency,
        legs=legs,
        composite_rate=composite,
        as_of=request.as_of,
        expires_at=expires_at,
        path_policy_id=request.path_policy_id,
        path_policy_version=request.path_policy_version,
        provenance={
            "selection": "direct" if len(legs) == 1 else "declared_intermediate",
            "sources": ",".join(leg.source_id for leg in legs),
            "provider_symbols": ",".join(leg.provider_symbol for leg in legs),
        },
        request_id=request.request_id,
    )


__all__ = ["FXRateProvider", "get_fx_conversion_evidence"]
