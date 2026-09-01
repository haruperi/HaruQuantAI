"""Normalized market-context evidence for Risk.

Data owns normalization and freshness; Risk owns interpretation. This module produces
``MarketContextEvidence`` â€” session, calendar, spread, liquidity, volatility,
correlation, and crisis observations â€” and never a verdict. Missing evidence is stated
explicitly rather than defaulted, because a Risk gate that cannot tell "absent" from
"benign" cannot fail closed.

The provider is injected by the caller. This module opens no connection and resolves no
credential.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from app.composition.logging import get_logger
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
    unwrap_data_response,
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.evidence.market_context_contracts import (
        MarketContextEvidence,
        MarketContextRequest,
    )


class MarketContextProvider(Protocol):
    """Read-only provider of normalized market-context observations."""

    def get_market_context(
        self,
        request: MarketContextRequest,
    ) -> StandardResponse[MarketContextEvidence]:
        """Return normalized context evidence for the exact request.

        Args:
            request: The ``request`` argument.
        """
        ...


def _get_market_context_evidence_raw(
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
    evidence = cast(
        "MarketContextEvidence",
        unwrap_data_response(
            provider.get_market_context(request),
            operation="data.evidence.get_market_context_evidence",
            request_id=request.request_id,
        ),
    )

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


def get_market_context_evidence(
    request: MarketContextRequest,
    provider: MarketContextProvider,
) -> StandardResponse[MarketContextEvidence]:
    """Acquire and verify requested market context without producing a Risk verdict.

    Args:
        request: Exact context scope and freshness requirement.
        provider: Caller-injected read-only context provider.

    Returns:
        Standard response carrying verified immutable market-context evidence.

    Raises:
        DataError: Never; failures surface as an error response. Cancellation and
            process-control exceptions propagate.
    """
    return run_data_operation(
        operation="data.evidence.get_market_context_evidence",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _get_market_context_evidence_raw(request, provider),
    )


__all__ = ["MarketContextProvider", "get_market_context_evidence"]
