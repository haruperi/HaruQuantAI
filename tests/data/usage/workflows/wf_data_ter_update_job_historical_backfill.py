"""WF-DATA-TER: run a bounded genuine MT5 update job and checkpoint."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_job_definition,
    build_job_status_request,
    create_data_update_job,
    ensure_source,
    get_data_update_job_status,
    get_market_data,
    recover_update_jobs,
    run_data_migrations,
    run_data_update_job_once,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import (
    isolated_runtime,
    market_request,
)

WORKFLOW_ID = "WF-DATA-TER"
STAGES = (
    "Validate MT5 source, destination, and stable job identity.",
    "Create one bounded persisted update job.",
    "Run retrieval, normalization, quality, persistence, and checkpoint.",
    "Read the persisted checkpoint and status.",
    "Recover startup state without publishing partial work.",
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
        with isolated_runtime(root):
            request_id = generate_id("req")
            run_data_migrations(request_id)
            end = datetime.now(UTC)

            # Stage 1 — Validate MT5 source, destination, and stable job identity.
            _stage(1)
            ensure_source("mt5", request_id)
            seed_resp = get_market_data(market_request("bars", timeframe="M1", limit=1))
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
            result = run_data_update_job_once(definition.job_id, request_id=request_id)
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
            recovery_resp = recover_update_jobs(generate_id("req"))
            recovery = unwrap_data_response(
                recovery_resp, operation="recover_update_jobs", request_id=request_id
            )
            print(
                "Job evidence:",
                created.state,
                result.state,
                status.last_checkpoint,
                len(recovery),
                "checked",
            )
    print("OUTPUT BOUNDARY — committed chunks and resumable checkpoint evidence")


if __name__ == "__main__":
    main()
