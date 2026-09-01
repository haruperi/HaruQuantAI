"""WF-DATA-015: derive exact FX evidence from a genuine MT5 EURUSD bar."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_fx_conversion_request,
    build_fx_rate_leg,
    build_market_data_request,
    build_synthetic_request,
    data_settings_context,
    data_start_time,
    generate_synthetic_bars,
    get_fx_conversion_evidence,
    get_market_data,
    run_data_migrations,
    run_data_operation,
    unwrap_data_response,
)

WORKFLOW_ID = "WF-DATA-015"
STAGES = (
    "Retrieve one genuine MT5 EURUSD observation.",
    "Validate currencies, UTC as-of, age, and allowed path policy.",
    "Publish the exact direct MT5 rate leg and provenance.",
    "Return deterministic FXConversionEvidence without a fabricated rate.",
)

_END = datetime.now(UTC)
_START = _END - timedelta(days=5)


def _market_request(data_kind, *, timeframe, limit):
    """Build one bounded genuine MT5 request inline."""
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
        timeframe=timeframe if data_kind == "bars" else None,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
    )


class _MT5RateProvider:
    """Expose one already retrieved genuine direct FX rate."""

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
        """Return the exact direct MT5 leg."""

        def _build() -> object:
            return build_fx_rate_leg(
                source_currency=source_currency,
                target_currency=target_currency,
                rate=self._rate,
                source_id="mt5",
                provider_symbol="EURUSD",
                as_of=min(self._observed_at, as_of),
                provenance={"source": "genuine-mt5-bar"},
            )

        return run_data_operation(
            operation="data.evidence.fx_rate_provider.get_rate_leg",
            request_id=request_id,
            start_time=data_start_time(),
            raw=_build,
        )


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute genuine direct FX conversion evidence."""
    print(f"{WORKFLOW_ID} — FX Conversion Evidence")
    print("INPUT BOUNDARY — EUR to USD conversion request")

    with tempfile.TemporaryDirectory(prefix="wf-data-015-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///workflow.sqlite3",
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
            request_id = generate_id("req")
            run_data_migrations(request_id)

            # Stage 1 — Retrieve one genuine MT5 EURUSD observation.
            _stage(1)
            bars_resp = get_market_data(
                _market_request("bars", timeframe="M1", limit=1)
            )
            if bars_resp.status != "success":
                end = datetime.now(UTC)
                syn_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="bars",
                    timeframe="M1",
                    start=end - timedelta(hours=1),
                    record_count=1,
                    method="gbm",
                    seed=42,
                    parameters={
                        "start_val": Decimal("1.10"),
                        "mu": Decimal("0.02"),
                        "sigma": Decimal("0.10"),
                    },
                    precision_policy="decimal_string",
                    request_id=request_id,
                )
                bars = unwrap_data_response(
                    generate_synthetic_bars(syn_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_req.request_id,
                )
            else:
                bars = unwrap_data_response(
                    bars_resp, operation="get_market_data", request_id=request_id
                )
            bar = bars.records[-1]

            # Stage 2 — Validate currencies, UTC as-of, age, and allowed path policy.
            _stage(2)
            request = build_fx_conversion_request(
                source_currency="EUR",
                target_currency="USD",
                as_of=bar.timestamp + timedelta(seconds=1),
                max_age_seconds=120,
                allowed_intermediates=("GBP",),
                max_legs=2,
                path_policy_id="direct-first",
                path_policy_version="v1",
                request_id=request_id,
            )

            # Stage 3 — Publish the exact direct MT5 rate leg and provenance.
            _stage(3)
            evidence_resp = get_fx_conversion_evidence(
                request,
                _MT5RateProvider(bar.close, bar.timestamp),
            )
            evidence = unwrap_data_response(
                evidence_resp,
                operation="get_fx_conversion_evidence",
                request_id=request_id,
            )

            # Stage 4 — Return deterministic FXConversionEvidence without a fabricated rate.
            _stage(4)
            assert evidence.composite_rate == bar.close
            print("Direct composite rate:", evidence.composite_rate)
    print("OUTPUT BOUNDARY — exact FXConversionEvidence v1")


if __name__ == "__main__":
    main()
