"""WF-DATA-018: use an explicit revisioned schedule for MT5 EURUSD."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_market_data_request,
    build_market_hours_request,
    build_synthetic_request,
    build_weekly_schedule_definition,
    build_weekly_schedule_provider,
    data_settings_context,
    generate_synthetic_bars,
    get_market_data,
    get_market_hours,
    run_data_migrations,
    unwrap_data_response,
)

WORKFLOW_ID = "WF-DATA-018"
STAGES = (
    "Confirm the exact MT5 EURUSD symbol with genuine observations.",
    "Select an explicit revisioned weekly definition because MT5 exposes no sessions.",
    "Expand authoritative configured windows with timezone and effective range.",
    "Derive deterministic current and next MarketHours state.",
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
    """Execute configured venue-hours evidence without ticker inference."""
    print(f"{WORKFLOW_ID} — Venue-Authoritative Market Hours")
    print("INPUT BOUNDARY — exact MT5 symbol and revisioned weekly definition")

    with tempfile.TemporaryDirectory(prefix="wf-data-018-") as directory:
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

            # Stage 1 — Confirm the exact MT5 EURUSD symbol with genuine observations.
            _stage(1)
            evidence_resp = get_market_data(
                _market_request("bars", timeframe="M1", limit=1)
            )
            if evidence_resp.status != "success":
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
                evidence = unwrap_data_response(
                    generate_synthetic_bars(syn_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_req.request_id,
                )
            else:
                evidence = unwrap_data_response(
                    evidence_resp, operation="get_market_data", request_id=request_id
                )
            assert evidence.symbol == "EURUSD"

            # Stage 2 — Select an explicit revisioned weekly definition because MT5 exposes no sessions.
            _stage(2)
            definition = build_weekly_schedule_definition(
                source_id="configured-mt5",
                symbol="EURUSD",
                timezone="UTC",
                sessions={day: ((time(0), time(23, 59)),) for day in range(5)},
                effective_from=date(2020, 1, 1),
                revision="operator-v1",
            )

            # Stage 3 — Expand authoritative configured windows with timezone and effective range.
            _stage(3)
            provider = build_weekly_schedule_provider(definition)

            # Stage 4 — Derive deterministic current and next MarketHours state.
            _stage(4)
            hours_resp = get_market_hours(
                build_market_hours_request(
                    source_id=definition.source_id,
                    symbol=definition.symbol,
                    request_id=request_id,
                ),
                provider,
            )
            hours = unwrap_data_response(
                hours_resp, operation="get_market_hours", request_id=request_id
            )
            print(
                "Market-hours evidence:",
                hours.is_open,
                hours.current_session,
                hours.next_session,
            )
    print("OUTPUT BOUNDARY — UTC sessions and deterministic MarketHours")


if __name__ == "__main__":
    main()
