"""Freshness-bound market-context acquisition from an injected provider."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.services.data.contracts.errors import DataError
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.contracts.market_context import (
        MarketContextEvidence,
        MarketContextRequest,
    )


class MarketContextProvider(Protocol):
    """Read-only provider of normalized market-context observations."""

    def get_market_context(
        self,
        request: MarketContextRequest,
    ) -> MarketContextEvidence:
        """Return normalized context evidence for the exact request."""
        ...


def get_market_context_evidence(
    request: MarketContextRequest,
    provider: MarketContextProvider,
) -> MarketContextEvidence:
    """Acquire and verify requested market context without producing a Risk verdict.

    Args:
        request: Exact context scope and freshness requirement.
        provider: Caller-injected read-only context provider.

    Returns:
        Verified immutable market-context evidence.

    Raises:
        DataError: If the provider fails or mandatory evidence is stale or absent.
    """
    logger.info("Acquiring market context for request %s", request.request_id)
    try:
        evidence = provider.get_market_context(request)
    except DataError:
        raise
    except Exception as error:
        logger.error("Market-context provider failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "market_context"},
            request_id=request.request_id,
        ) from error

    if (
        evidence.symbol != request.symbol
        or evidence.timezone != request.timezone
        or evidence.request_id != request.request_id
        or not evidence.provenance
    ):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"operation": "market_context"},
            request_id=request.request_id,
        )
    age = request.as_of - evidence.as_of
    if (
        age.total_seconds() < 0
        or age.total_seconds() > request.max_age_seconds
        or evidence.expires_at <= request.as_of
    ):
        raise DataError(
            "STALE_EVIDENCE",
            safe_details={"operation": "market_context"},
            request_id=request.request_id,
        )

    values = {
        "session": evidence.session_state,
        "calendar": evidence.calendar_state,
        "spread": evidence.spread,
        "liquidity": evidence.liquidity,
        "volatility": evidence.volatility,
        "correlation": evidence.correlations or None,
        "crisis": (True if "crisis" in evidence.provenance else None),
    }
    missing = tuple(
        kind
        for kind in request.requested_evidence
        if kind in evidence.missing_fields or values[kind] is None
    )
    if missing:
        raise DataError(
            "STALE_EVIDENCE",
            safe_details={"missing_count": len(missing)},
            request_id=request.request_id,
        )
    return evidence


__all__ = ["MarketContextProvider", "get_market_context_evidence"]
