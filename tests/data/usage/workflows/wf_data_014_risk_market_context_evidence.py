"""WF-DATA-014: normalize Risk context from genuine MT5 evidence."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_market_context_evidence,
    build_market_context_request,
    build_market_data_request,
    data_settings_context,
    data_start_time,
    get_market_context_evidence,
    get_spread_data,
    run_data_migrations,
    run_data_operation,
    unwrap_data_response,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-014"
STAGES = (
    "Retrieve current genuine MT5 spread evidence.",
    "Build a bounded Risk market-context request.",
    "Normalize provider facts with provenance and explicit missingness.",
    "Return evidence without producing a Risk verdict.",
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


class _MT5ContextProvider:
    """Expose already retrieved MT5 observations through the evidence protocol."""

    def __init__(self, spread: Decimal, as_of: object) -> None:
        self._spread = spread
        self._as_of = as_of

    def get_market_context(self, request: object) -> object:
        """Return normalized facts derived from genuine MT5 spread evidence."""
        req_symbol = getattr(request, "symbol", "EURUSD")
        req_tz = getattr(request, "timezone", "UTC")
        req_as_of = request.as_of
        req_id = getattr(request, "request_id", generate_id("req"))

        def _build() -> object:
            return build_market_context_evidence(
                symbol=req_symbol,
                session_state=None,
                calendar_state=None,
                spread=self._spread,
                spread_unit="USD",
                liquidity=None,
                volatility=None,
                correlations={},
                crisis_flags=(),
                timezone=req_tz,
                as_of=req_as_of,
                expires_at=req_as_of + timedelta(seconds=60),
                provenance={"source": "mt5", "observation": str(self._as_of)},
                missing_fields=("session", "calendar", "liquidity", "volatility"),
                request_id=req_id,
            )

        return run_data_operation(
            operation="data.evidence.market_context_provider.get_market_context",
            request_id=req_id,
            start_time=data_start_time(),
            raw=_build,
        )


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute genuine MT5 market-context normalization."""
    print(f"{WORKFLOW_ID} — Risk Market-Context Evidence")
    print("INPUT BOUNDARY — Risk requests declared EURUSD evidence")

    with tempfile.TemporaryDirectory(prefix="wf-data-014-") as directory:
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

            # Stage 1 — Retrieve current genuine MT5 spread evidence.
            _stage(1)
            spreads_resp = get_spread_data(
                _market_request("spreads", timeframe=None, limit=1)
            )
            spreads = unwrap_data_response(
                spreads_resp, operation="get_spread_data", request_id=request_id
            )
            record = spreads.records[-1]
            spread = record.spread
            assert spread is not None

            # Stage 2 — Build a bounded Risk market-context request.
            _stage(2)
            request = build_market_context_request(
                symbol="EURUSD",
                as_of=record.timestamp,
                max_age_seconds=60,
                requested_evidence=("spread",),
                timezone="UTC",
                request_id=request_id,
            )

            # Stage 3 — Normalize provider facts with provenance and explicit missingness.
            _stage(3)
            evidence_resp = get_market_context_evidence(
                request,
                _MT5ContextProvider(spread, record.timestamp),
            )
            evidence = unwrap_data_response(
                evidence_resp,
                operation="get_market_context_evidence",
                request_id=request_id,
            )

            # Stage 4 — Return evidence without producing a Risk verdict.
            _stage(4)
            print("Context evidence:", evidence.spread, evidence.missing_fields)
    print("OUTPUT BOUNDARY — MarketContextEvidence v1, never a policy verdict")


if __name__ == "__main__":
    main()
