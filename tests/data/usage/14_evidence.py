"""Run normalized market, FX, and account evidence examples (FEAT-DATA-09)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import DataError
from app.services.data.evidence import (
    get_account_state_snapshot,
    get_fx_conversion_evidence,
    get_market_context_evidence,
)
from app.services.data.evidence.account_contracts import (
    AccountSnapshotRequest,
)
from app.services.data.evidence.fx_contracts import (
    FXConversionRequest,
    FXRateLeg,
)
from app.services.data.evidence.market_context_contracts import (
    MarketContextEvidence,
    MarketContextRequest,
)
from app.utils import generate_id

_AS_OF = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


class _ContextProvider:
    """Deterministic read-only market-context provider."""

    def get_market_context(
        self,
        request: MarketContextRequest,
    ) -> MarketContextEvidence:
        """Return complete fresh evidence for the exact request."""
        return MarketContextEvidence(
            symbol=request.symbol,
            session_state="open",
            calendar_state="clear",
            spread=Decimal("0.0002"),
            spread_unit="USD",
            liquidity=Decimal(1000000),
            volatility=Decimal("0.01"),
            correlations={},
            crisis_flags=(),
            timezone=request.timezone,
            as_of=request.as_of,
            expires_at=request.as_of + timedelta(minutes=5),
            provenance={"source": "usage-fixture"},
            missing_fields=(),
            request_id=request.request_id,
        )


class _FXProvider:
    """Deterministic read-only direct FX provider."""

    def get_rate_leg(
        self,
        *,
        source_currency: str,
        target_currency: str,
        as_of: datetime,
        request_id: str,
    ) -> FXRateLeg:
        """Return one exact direct rate leg."""
        del request_id
        return FXRateLeg(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=Decimal("1.10"),
            source_id="usage-fixture",
            provider_symbol=f"{source_currency}{target_currency}",
            as_of=as_of - timedelta(seconds=1),
            provenance={"quote": "declared-fixture"},
        )


def main() -> None:
    """Call every FEAT-DATA-09 public evidence operation."""
    context_request = MarketContextRequest(
        symbol="EURUSD",
        as_of=_AS_OF,
        max_age_seconds=60,
        requested_evidence=("session", "calendar", "spread", "liquidity"),
        timezone="UTC",
        request_id=generate_id("req"),
    )
    context = get_market_context_evidence(context_request, _ContextProvider())
    print("get_market_context_evidence:", context.symbol, context.session_state)

    fx_request = FXConversionRequest(
        source_currency="EUR",
        target_currency="USD",
        as_of=_AS_OF,
        max_age_seconds=60,
        allowed_intermediates=("GBP",),
        max_legs=2,
        path_policy_id="usage-direct-first",
        path_policy_version="v1",
        request_id=generate_id("req"),
    )
    fx = get_fx_conversion_evidence(fx_request, _FXProvider())
    print("get_fx_conversion_evidence:", fx.composite_rate)

    account_request = AccountSnapshotRequest(
        source_id="usage-unavailable",
        account_id="account-1",
        max_age_seconds=60,
        request_id=generate_id("req"),
    )
    try:
        get_account_state_snapshot(account_request, object())  # type: ignore[arg-type]
    except DataError as error:
        print("get_account_state_snapshot: unavailable", error.code)


if __name__ == "__main__":
    main()
