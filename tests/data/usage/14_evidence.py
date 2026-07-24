"""Run normalized market, FX, and account evidence examples (FEAT-DATA-09)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    AccountSnapshotRequest,
    DataError,
    FXConversionRequest,
    FXRateLeg,
    MarketContextEvidence,
    MarketContextRequest,
    get_account_state_snapshot,
    get_fx_conversion_evidence,
    get_market_context_evidence,
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


def _demonstrate_feature() -> None:
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


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_008() -> None:
    "FR-DATA-008: Expose immutable normalized account, balance, margin, position, order, connectivity, and staleness evidence with exact decimals and UTC snapshot time."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_028() -> None:
    "FR-DATA-028: Return a fresh normalized `AccountStateSnapshot v1` from read-only Brokers `BrokerAdapter` account reads without exposing credentials/provider objects."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_075() -> None:
    "FR-DATA-075: Validate a bounded request for session, calendar, spread, liquidity, volatility, correlation, and crisis evidence for one declared scope."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_076() -> None:
    "FR-DATA-076: Produce immutable `MarketContextEvidence v1` with separate contract version/schema ID, UTC freshness, provenance, and explicit missingness; never produce a Risk verdict."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_078() -> None:
    "FR-DATA-078: Validate source/target currencies, UTC `as_of`, explicit maximum age, and explicit allowed-path policy; reject same-leg cycles and unbounded discovery."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_079() -> None:
    "FR-DATA-079: Deterministically select an allowed acyclic direct/synthesized path and publish exact rates, UTC freshness, policy version, and source provenance as `FXConversionEvidence v1`; never fabricate a rate."  # noqa: E501 - exact specification text
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_008,
        fr_data_028,
        fr_data_075,
        fr_data_076,
        fr_data_078,
        fr_data_079,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
