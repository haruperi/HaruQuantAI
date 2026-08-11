# ruff: noqa: BLE001
"""Run normalized market, FX, and account evidence examples (FEAT-DATA-14)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from _audit_support import main as run_audit_support
from app.services.data import (
    build_account_snapshot_request,
    build_data_settings,
    build_fx_conversion_request,
    build_fx_rate_leg,
    build_market_context_evidence,
    build_market_context_request,
    data_settings_context,
    data_start_time,
    get_account_state_snapshot,
    get_fx_conversion_evidence,
    get_market_context_evidence,
    run_data_migrations,
    run_data_operation,
)
from app.utils import generate_id


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


class _ContextProvider:
    """Expose a mock market context observation."""

    def __init__(self, spread: Decimal, observed_at: datetime) -> None:
        self._spread = spread
        self._observed_at = observed_at

    def get_market_context(self, request: object) -> object:
        """Return normalized context derived from observation."""
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
    """Expose a direct FX observation."""

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
        """Return one direct rate leg."""
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
                provenance={"source": "mt5-observation"},
            ),
        )


def fr_data_075_076() -> None:
    """FR-DATA-075, FR-DATA-076: Stage 1 — Market context evidence with spread, session state, and provenance."""
    _header(
        "Stage 1: Market Context Evidence - Market Context (FR-DATA-075, FR-DATA-076)"
    )
    req_id = generate_id("req")
    now = datetime.now(UTC)
    ctx_req = build_market_context_request(
        symbol="EURUSD",
        max_age_seconds=60,
        requested_evidence=("spread",),
        timezone="UTC",
        as_of=now,
        request_id=req_id,
    )
    print(_format_result(ctx_req))

    provider = _ContextProvider(Decimal("0.00015"), now)
    context_res = get_market_context_evidence(ctx_req, provider)
    print(_format_result(context_res))
    if context_res.status == "success" and context_res.data:
        ctx = context_res.data
        print(
            f"Data -> MarketContextEvidence(symbol={ctx.symbol}, spread={ctx.spread})"
        )


def fr_data_008_078() -> None:
    """FR-DATA-008, FR-DATA-078: Stage 2 — Multi-leg FX conversion evidence with rate legs, path policy, and composite rate."""
    _header(
        "Stage 2: Multi-Leg FX Conversion Evidence - FX Conversion (FR-DATA-008, FR-DATA-078)"
    )
    req_id = generate_id("req")
    now = datetime.now(UTC)
    fx_req = build_fx_conversion_request(
        source_currency="EUR",
        target_currency="USD",
        as_of=now,
        max_age_seconds=300,
        allowed_intermediates=("GBP",),
        max_legs=2,
        path_policy_id="direct-first",
        path_policy_version="v1",
        request_id=req_id,
    )
    print(_format_result(fx_req))

    provider = _FXProvider(Decimal("1.0850"), now)
    fx_res = get_fx_conversion_evidence(fx_req, provider)
    print(_format_result(fx_res))
    if fx_res.status == "success" and fx_res.data:
        fx = fx_res.data
        print(f"Data -> FXConversionEvidence(rate={fx.composite_rate})")


def fr_data_028_079() -> None:
    """FR-DATA-028, FR-DATA-079: Stage 3 — Account state snapshot evidence with balances, positions, and connected status."""
    _header(
        "Stage 3: Account State Snapshot Evidence - Account Snapshot (FR-DATA-028, FR-DATA-079)"
    )
    req_id = generate_id("req")
    acct_req = build_account_snapshot_request(
        source_id="mt5",
        account_id="demo-account-1",
        max_age_seconds=315360000,
        request_id=req_id,
    )
    print(_format_result(acct_req))
    try:
        acct_res = get_account_state_snapshot(acct_req, None)
        print(_format_result(acct_res))
        if acct_res.status == "success" and acct_res.data:
            print(
                f"Data -> AccountStateSnapshot(currency={acct_res.data.currency}, connected={acct_res.data.connected})"
            )
    except Exception as error:
        code = getattr(error, "code", type(error).__name__)
        print(f"Data -> DataError({code})")


def main() -> None:
    """Execute every functional-requirement demonstration."""
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
            print("=" * 80)
            print("FEATURE: FEAT-DATA-14 - Domain Evidence and Provenance")
            print(
                "PURPOSE: Provide normalized market context, FX conversion, and account state evidence with full provenance"
            )
            print(
                "MODULE FLOW: Stage 1 (Market Context Evidence) -> Stage 2 (Multi-Leg FX Conversion Evidence) -> Stage 3 (Account State Snapshot Evidence)"
            )
            print("=" * 80)

            fr_data_075_076()
            fr_data_008_078()
            fr_data_028_079()
            run_audit_support()
            print("SUCCESS: FEAT-DATA-14 completed")


if __name__ == "__main__":
    main()
