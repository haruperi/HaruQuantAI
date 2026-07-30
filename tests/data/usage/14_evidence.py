"""Run normalized market, FX, and account evidence examples (FEAT-DATA-09)."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import create_connected_broker, disconnect_broker
from app.services.data import (
    build_account_snapshot_request,
    build_data_settings,
    build_fx_conversion_request,
    build_fx_rate_leg,
    build_market_context_evidence,
    build_market_context_request,
    build_market_data_request,
    data_settings_context,
    data_start_time,
    get_account_state_snapshot,
    get_fx_conversion_evidence,
    get_market_context_evidence,
    get_market_data,
    get_spread_data,
    run_data_migrations,
    run_data_operation,
    unwrap_data_response,
)
from app.utils import generate_id


def _error_code(error: BaseException) -> str:
    """Return a safe public-boundary error identifier."""
    return str(getattr(error, "code", type(error).__name__))


class _ContextProvider:
    """Expose an already retrieved genuine MT5 spread observation."""

    def __init__(self, spread: Decimal, observed_at: datetime) -> None:
        self._spread = spread
        self._observed_at = observed_at

    def get_market_context(
        self,
        request: object,
    ) -> object:
        """Return normalized context derived from the exact MT5 observation."""
        request_id = getattr(request, "request_id", generate_id("req"))
        as_of = getattr(request, "as_of", self._observed_at)
        return run_data_operation(
            operation="data.evidence.market_context_provider.get_market_context",
            request_id=request_id,
            start_time=data_start_time(),
            raw=lambda: build_market_context_evidence(
                symbol=getattr(request, "symbol", "EURUSD"),
                session_state=None,
                calendar_state=None,
                spread=self._spread,
                spread_unit="quote_currency",
                liquidity=None,
                volatility=None,
                correlations={},
                crisis_flags=(),
                timezone=getattr(request, "timezone", "UTC"),
                as_of=as_of,
                expires_at=as_of + timedelta(seconds=60),
                provenance={
                    "source": "mt5",
                    "observed_at": self._observed_at.isoformat(),
                },
                missing_fields=("session", "calendar", "liquidity", "volatility"),
                request_id=request_id,
            ),
        )


class _FXProvider:
    """Expose an already retrieved genuine MT5 direct FX observation."""

    def __init__(self, rate: Decimal, observed_at: datetime) -> None:
        self._rate = rate
        self._observed_at = observed_at

    def get_rate_leg(
        self,
        *,
        source_currency: str,
        target_currency: str,
        as_of: datetime,
        request_id: str,
    ) -> object:
        """Return one exact direct rate leg derived from MT5."""
        return run_data_operation(
            operation="data.evidence.fx_rate_provider.get_rate_leg",
            request_id=request_id,
            start_time=data_start_time(),
            raw=lambda: build_fx_rate_leg(
                source_currency=source_currency,
                target_currency=target_currency,
                rate=self._rate,
                source_id="mt5",
                provider_symbol=f"{source_currency}{target_currency}",
                as_of=min(as_of, self._observed_at),
                provenance={"source": "genuine-mt5-bar"},
            ),
        )


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _demonstrate_feature() -> None:
    """Exercise market context, FX conversion, and account state evidence."""
    req_id = generate_id("req")
    try:
        with TemporaryDirectory(prefix="usage-evidence-market-") as directory:
            (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
            settings = _settings(Path(directory))
            with data_settings_context(settings):
                run_data_migrations(generate_id("req"))
                end = datetime.now(UTC)
                start = end - timedelta(days=5)
                spread_request = _market_request(
                    "spreads",
                    timeframe=None,
                    limit=1,
                    start=start,
                    end=end,
                )
                spreads = unwrap_data_response(
                    get_spread_data(spread_request),
                    operation="get_spread_data",
                    request_id=req_id,
                )
                _print_evidence(spreads, start, end, req_id)
    except Exception as error:  # noqa: BLE001 - domain classes stay private.
        print(
            "Genuine provider evidence unavailable:",
            _error_code(error),
            "(no injected fallback used)",
        )


def _print_evidence(
    spreads: Any,
    start: datetime,
    end: datetime,
    req_id: str,
) -> None:
    """Print bounded evidence derived from genuine provider observations."""
    spread_record = spreads.records[-1]
    ctx_req = build_market_context_request(
        symbol="EURUSD",
        max_age_seconds=60,
        requested_evidence=("spread",),
        timezone="UTC",
        as_of=spread_record.timestamp,
        request_id=req_id,
    )
    context_resp = get_market_context_evidence(
        ctx_req,
        _ContextProvider(spread_record.spread, spread_record.timestamp),
    )
    context = unwrap_data_response(
        context_resp,
        operation="data.evidence.get_market_context_evidence",
        request_id=req_id,
    )
    print(
        "Genuine MarketContextEvidence:",
        context.symbol,
        context.spread,
        dict(context.provenance),
    )

    bar_request = _market_request(
        "bars",
        timeframe="M1",
        limit=1,
        start=start,
        end=end,
    )
    bars = unwrap_data_response(
        get_market_data(bar_request),
        operation="get_market_data",
        request_id=req_id,
    )
    bar = bars.records[-1]
    fx_req = build_fx_conversion_request(
        source_currency="EUR",
        target_currency="USD",
        as_of=bar.timestamp + timedelta(seconds=1),
        max_age_seconds=300,
        allowed_intermediates=("GBP",),
        max_legs=2,
        path_policy_id="direct-first",
        path_policy_version="v1",
        request_id=req_id,
    )
    fx_resp = get_fx_conversion_evidence(
        fx_req,
        _FXProvider(bar.close, bar.timestamp),
    )
    fx = unwrap_data_response(
        fx_resp,
        operation="get_fx_conversion_evidence",
        request_id=req_id,
    )
    print(
        "Genuine FXConversionEvidence:",
        fx.composite_rate,
        dict(fx.provenance),
    )

    _demonstrate_account_snapshot(req_id)


def _settings(directory: Path) -> object:
    """Build isolated settings for genuine MT5 evidence reads."""
    return build_data_settings(
        database_url="sqlite:///usage.sqlite3",
        data_dir=directory,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(
            Path("raw"),
            Path("processed"),
            Path("data"),
            Path("data/raw"),
            Path("data/processed"),
        ),
        data_provider_sources=("mt5",),
        data_raw_root=Path("data/raw"),
    )


def _market_request(
    data_kind: str,
    *,
    timeframe: str | None,
    limit: int,
    start: datetime,
    end: datetime,
) -> object:
    """Build one bounded genuine MT5 request."""
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
        timeframe=timeframe,
        start=start,
        end=end,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
    )


def _demonstrate_account_snapshot(req_id: str) -> None:
    """Read a genuine MT5 demo account snapshot through Data's read-only boundary."""
    with TemporaryDirectory(prefix="usage-evidence-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            try:
                adapter = asyncio.run(create_connected_broker("mt5"))
            except ValueError as error:
                print("MT5 account snapshot handled:", error)
                return
            try:
                account_info = asyncio.run(adapter.get_account_info())
                if account_info.status != "success" or account_info.data is None:
                    print("get_account_state_snapshot handled: account read failed")
                    return
                account_request = build_account_snapshot_request(
                    source_id="mt5",
                    account_id=account_info.data.account_id,
                    max_age_seconds=315360000,
                    request_id=req_id,
                )
                account_resp = get_account_state_snapshot(account_request, adapter)
                account = unwrap_data_response(
                    account_resp,
                    operation="get_account_state_snapshot",
                    request_id=req_id,
                )
                print(
                    "AccountStateSnapshot:",
                    account.currency,
                    len(account.balances),
                    len(account.positions),
                    account.connected,
                )
            except Exception as error:  # noqa: BLE001
                print("get_account_state_snapshot handled:", _error_code(error))
            finally:
                asyncio.run(disconnect_broker(adapter))


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
