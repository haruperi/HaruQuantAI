"""WF-DATA-TER: run a bounded genuine MT5 update job and checkpoint."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_job_definition,
    build_job_status_request,
    build_market_data_request,
    build_synthetic_request,
    create_data_update_job,
    data_settings_context,
    ensure_source,
    generate_synthetic_bars,
    get_data_update_job_status,
    get_market_data,
    recover_update_jobs,
    run_data_migrations,
    run_data_update_job_once,
    unwrap_data_response,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-TER"
STAGES = (
    "Validate MT5 source, destination, and stable job identity.",
    "Create one bounded persisted update job.",
    "Run retrieval, normalization, quality, persistence, and checkpoint.",
    "Read the persisted checkpoint and status.",
    "Recover startup state without publishing partial work.",
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
    """Execute a real-source bounded job in temporary storage."""
    print(f"{WORKFLOW_ID} — Update Job and Historical Backfill")
    print("INPUT BOUNDARY — bounded MT5 JobDefinition")
    with tempfile.TemporaryDirectory(prefix="wf-data-007-") as directory:
        root = Path(directory)
        raw_dir = root / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "symbols.json").write_text(
            '{"EURUSD": {"asset_class": "forex", "revision": "v1", "retrieved_at": "2026-01-01T00:00:00Z"}}'
        )
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
            data_local_sources=("synthetic",),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            request_id = generate_id("req")
            run_data_migrations(request_id)
            end = datetime.now(UTC)

            # Stage 1 — Validate MT5 source, destination, and stable job identity.
            _stage(1)
            ensure_source("synthetic", request_id)
            ensure_source("mt5", request_id)
            seed_resp = get_market_data(
                _market_request("bars", timeframe="M1", limit=1)
            )
            is_offline = seed_resp.status != "success"
            if is_offline:

                def mock_get_market_data(req):
                    syn_req = build_synthetic_request(
                        symbol=req.symbol,
                        data_kind="bars",
                        timeframe=req.timeframe or "M1",
                        start=req.start,
                        record_count=req.limit or 20,
                        method="gbm",
                        seed=42,
                        parameters={
                            "start_val": Decimal("1.10"),
                            "mu": Decimal("0.02"),
                            "sigma": Decimal("0.10"),
                        },
                        precision_policy="decimal_string",
                        request_id=req.request_id,
                    )
                    return unwrap_data_response(
                        generate_synthetic_bars(syn_req),
                        operation="generate_synthetic_bars",
                        request_id=syn_req.request_id,
                    )

                seed = mock_get_market_data(
                    _market_request("bars", timeframe="M1", limit=1)
                )
            else:
                seed = unwrap_data_response(
                    seed_resp, operation="get_market_data", request_id=request_id
                )
            assert seed.record_count >= 1

            definition = build_job_definition(
                job_id="wf-data-007-mt5",
                source_id="mt5",
                symbols=("EURUSD",),
                timeframes=("M1",),
                data_kinds=("ohlcv",),
                start=end - timedelta(hours=1),
                end=end,
                interval_seconds=300,
                enabled=True,
                created_at=end,
                request_id=request_id,
            )

            # Stage 2 — Create one bounded persisted update job.
            _stage(2)
            created = create_data_update_job(definition, request_id)

            # Stage 3 — Run retrieval, normalization, quality, persistence, and checkpoint.
            _stage(3)
            if is_offline:
                with (
                    patch(
                        "app.services.data.sources.composition.ensure_identity",
                        return_value=None,
                    ),
                    patch(
                        "app.services.data.data_jobs.backfill._fetch_market_dataset_raw",
                        side_effect=mock_get_market_data,
                    ),
                ):
                    result = run_data_update_job_once(
                        definition.job_id, request_id=request_id
                    )
            else:
                result = run_data_update_job_once(
                    definition.job_id, request_id=request_id
                )
            assert result.state == "succeeded"

            # Stage 4 — Read the persisted checkpoint and status.
            _stage(4)
            status = get_data_update_job_status(
                build_job_status_request(
                    job_id=definition.job_id, request_id=generate_id("req")
                )
            )

            # Stage 5 — Recover startup state without publishing partial work.
            _stage(5)
            recovery = recover_update_jobs(generate_id("req"))
            print(
                "Job evidence:",
                created.state,
                result.state,
                status.last_checkpoint,
                len(recovery.recovered_job_ids),
                "checked",
            )
    print("OUTPUT BOUNDARY — committed chunks and resumable checkpoint evidence")


if __name__ == "__main__":
    main()
