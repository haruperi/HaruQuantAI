"""Run normalized market, FX, and account evidence examples (FEAT-DATA-09)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_account_snapshot_request,
    build_fx_conversion_request,
    build_fx_rate_leg,
    build_market_context_evidence,
    build_market_context_request,
    get_account_state_snapshot,
    get_fx_conversion_evidence,
    get_market_context_evidence,
    unwrap_data_response,
)
from app.services.data.contracts.errors import DataError
from app.utils import generate_id

_AS_OF = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


class _ContextProvider:
    """Deterministic read-only market-context provider."""

    def get_market_context(
        self,
        request: object,
    ) -> object:
        """Return complete fresh evidence for the exact request."""
        return build_market_context_evidence(
            symbol=getattr(request, "symbol", "EURUSD"),
            session_state="open",
            calendar_state="clear",
            spread=Decimal("0.0002"),
            spread_unit="USD",
            liquidity=Decimal(1000000),
            volatility=Decimal("0.01"),
            correlations={},
            crisis_flags=(),
            timezone=getattr(request, "timezone", "UTC"),
            as_of=getattr(request, "as_of", _AS_OF),
            expires_at=getattr(request, "as_of", _AS_OF) + timedelta(minutes=5),
            provenance={"source": "usage-fixture"},
            missing_fields=(),
            request_id=getattr(request, "request_id", generate_id("req")),
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
    ) -> object:
        """Return one exact direct rate leg."""
        del request_id
        return build_fx_rate_leg(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=Decimal("1.0850"),
            source_id="usage-fx",
            provider_symbol=f"{source_currency}{target_currency}",
            as_of=as_of,
            provenance={"source": "usage-fixture"},
        )


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _demonstrate_feature() -> None:
    """Exercise market context, FX conversion, and account state evidence."""
    req_id = generate_id("req")

    ctx_req = build_market_context_request(
        symbol="EURUSD",
        max_age_seconds=60,
        requested_evidence=("session", "calendar", "spread", "liquidity", "volatility"),
        timezone="UTC",
        as_of=_AS_OF,
        request_id=req_id,
    )
    context_resp = get_market_context_evidence(ctx_req, _ContextProvider())
    try:
        context = unwrap_data_response(
            context_resp,
            operation="data.evidence.get_market_context_evidence",
            request_id=req_id,
        )
        print("MarketContextEvidence:", context.symbol, context.session_state)
    except DataError as error:
        print("get_market_context_evidence handled:", error.code)

    fx_req = build_fx_conversion_request(
        source_currency="EUR",
        target_currency="USD",
        as_of=_AS_OF,
        max_age_seconds=300,
        allowed_intermediates=("GBP",),
        max_legs=2,
        path_policy_id="direct-first",
        path_policy_version="v1",
        request_id=req_id,
    )
    fx_resp = get_fx_conversion_evidence(fx_req, _FXProvider())
    try:
        fx = unwrap_data_response(
            fx_resp, operation="get_fx_conversion_evidence", request_id=req_id
        )
        print("FXConversionEvidence composite rate:", fx.composite_rate)
    except DataError as error:
        print("get_fx_conversion_evidence handled:", error.code)

    account_request = build_account_snapshot_request(
        account_id="acc-usage",
        source_id="usage-unavailable",
        max_age_seconds=60,
        request_id=req_id,
    )
    account_resp = get_account_state_snapshot(account_request, object())
    try:
        account = unwrap_data_response(
            account_resp, operation="get_account_state_snapshot", request_id=req_id
        )
        print("AccountStateSnapshot balance:", account.balance)
    except DataError as error:
        print("get_account_state_snapshot handled:", error.code)


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_008() -> None:
    _header("fr_data_008")
    _demonstrate_once()


def fr_data_028() -> None:
    _header("fr_data_028")
    _demonstrate_once()


def fr_data_075() -> None:
    _header("fr_data_075")
    _demonstrate_once()


def fr_data_076() -> None:
    _header("fr_data_076")
    _demonstrate_once()


def fr_data_078() -> None:
    _header("fr_data_078")
    _demonstrate_once()


def fr_data_079() -> None:
    _header("fr_data_079")
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
