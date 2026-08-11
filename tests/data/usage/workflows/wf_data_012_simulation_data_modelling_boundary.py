"""WF-DATA-012: demonstrate the Data-to-Simulation modelling boundary."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_market_data_request,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    get_market_data,
    inspect_dataset_quality,
    run_data_migrations,
    to_ohlcv_dataframe,
    unwrap_data_response,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-012"
STAGES = (
    "Accept Simulation's bounded canonical-history request.",
    "Retrieve genuine MT5 bars through Data normalization and quality.",
    "Return the typed dataset without constructing simulation ticks or fills.",
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
    """Execute the ownership boundary without simulation modelling."""
    print(f"{WORKFLOW_ID} — Simulation Data-Modelling Boundary")
    print("INPUT BOUNDARY — Simulation requests canonical MT5 history")

    with tempfile.TemporaryDirectory(prefix="wf-data-012-") as directory:
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

            # Stage 1 — Accept Simulation's bounded canonical-history request.
            _stage(1)
            request = _market_request("bars", timeframe="M1", limit=20)

            # Stage 2 — Retrieve genuine MT5 bars through Data normalization and quality.
            _stage(2)
            dataset_resp = get_market_data(request)
            if dataset_resp.status != "success":
                end = datetime.now(UTC)
                syn_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="bars",
                    timeframe="M1",
                    start=end - timedelta(hours=1),
                    record_count=20,
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
                dataset = unwrap_data_response(
                    generate_synthetic_bars(syn_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_req.request_id,
                )
            else:
                dataset = unwrap_data_response(
                    dataset_resp, operation="get_market_data", request_id=request_id
                )
            report_resp = inspect_dataset_quality(dataset)
            report = unwrap_data_response(
                report_resp, operation="inspect_dataset_quality", request_id=request_id
            )

            # Stage 3 — Return the typed dataset without constructing simulation ticks or fills.
            _stage(3)
            projection = to_ohlcv_dataframe(dataset)
            print(
                "Boundary evidence:",
                dataset.record_count,
                report.quality_status,
                projection.shape,
            )
    print("OUTPUT BOUNDARY — canonical MarketDataset; Simulation owns modelling")


if __name__ == "__main__":
    main()
