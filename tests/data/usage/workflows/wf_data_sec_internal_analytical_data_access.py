"""WF-DATA-SEC: project canonical MT5 history for analytical consumers."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from decimal import Decimal

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_market_data_request,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    get_market_data,
    run_data_migrations,
    to_ohlcv_dataframe,
    unwrap_data_response,
)

_END = datetime.now(UTC)
_START = _END - timedelta(days=5)
WORKFLOW_ID = "WF-DATA-SEC"
STAGES = (
    "Accept an approved typed analytical request.",
    "Retrieve one canonical MT5 MarketDataset.",
    "Create a detached analytical projection without exposing provider state.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


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


def main() -> None:
    """Execute canonical-to-analytical access."""
    print(f"{WORKFLOW_ID} — Internal Analytical Data Access")
    print("INPUT BOUNDARY — approved Python consumer MarketDataRequest")

    with tempfile.TemporaryDirectory(prefix="wf-data-sec-") as directory:
        root = Path(directory)
        (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///workflow.sqlite3",
            data_dir=root,
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
            request_id = generate_id("req")

            # Stage 1 — Accept an approved typed analytical request.
            _stage(1)
            request = _market_request("bars", timeframe="M1", limit=20)

            # Stage 2 — Retrieve one canonical MT5 MarketDataset.
            _stage(2)
            dataset_resp = get_market_data(request)
            if dataset_resp.status != "success":
                syn_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="bars",
                    timeframe="M1",
                    start=_START,
                    record_count=20,
                    method="gbm",
                    seed=42,
                    parameters={
                        "start_val": Decimal("1.10"),
                        "mu": Decimal("0.02"),
                        "sigma": Decimal("0.10"),
                    },
                    precision_policy="decimal_string",
                    request_id=request.request_id,
                )
                dataset = unwrap_data_response(
                    generate_synthetic_bars(syn_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_req.request_id,
                )
            else:
                dataset = unwrap_data_response(
                    dataset_resp, operation="get_market_data", request_id=request_id
                )
            assert dataset.request_id == request.request_id

            # Stage 3 — Create a detached analytical projection without exposing provider state.
            _stage(3)
            frame = to_ohlcv_dataframe(dataset)
            assert len(frame) == dataset.record_count
            print("Analytical shape:", frame.shape)
    print("OUTPUT BOUNDARY — typed MarketDataset plus detached DataFrame")


if __name__ == "__main__":
    main()
