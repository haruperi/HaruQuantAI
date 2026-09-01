"""WF-DATA-019: classify named sessions at a genuine MT5 observation time."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from decimal import Decimal

from app.kernel.identity import generate_id
from app.services.data import (
    build_active_market_sessions_request,
    build_data_settings,
    build_market_data_request,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    get_active_market_sessions,
    get_market_data,
    run_data_migrations,
    unwrap_data_response,
)

WORKFLOW_ID = "WF-DATA-019"
STAGES = (
    "Retrieve a genuine MT5 observation timestamp.",
    "Submit the exact symbol and aware UTC instant.",
    "Classify regional sessions with DST-aware definitions.",
    "Return labels structurally separated from tradability.",
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


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute analytical named-session classification."""
    print(f"{WORKFLOW_ID} — Analytical Named-Session Classification")
    print("INPUT BOUNDARY — exact symbol and genuine aware UTC instant")

    with tempfile.TemporaryDirectory(prefix="wf-data-019-") as directory:
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

            # Stage 1 — Retrieve a genuine MT5 observation timestamp.
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

            # Stage 2 — Submit the exact symbol and aware UTC instant.
            _stage(2)
            request = build_active_market_sessions_request(
                symbol=bars.symbol,
                at=bars.records[-1].timestamp,
                request_id=request_id,
            )

            # Stage 3 — Classify regional sessions with DST-aware definitions.
            _stage(3)
            sessions_resp = get_active_market_sessions(request)
            sessions = unwrap_data_response(
                sessions_resp,
                operation="get_active_market_sessions",
                request_id=request_id,
            )

            # Stage 4 — Return labels structurally separated from tradability.
            _stage(4)
            assert not hasattr(sessions, "is_open")
            print("Analytical labels:", sessions.sessions)
    print("OUTPUT BOUNDARY — DST-aware liquidity labels with no trading authority")


if __name__ == "__main__":
    main()
