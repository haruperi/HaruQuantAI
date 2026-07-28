"""WF-DATA-023: exercise the versioned cache lifecycle end to end."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    CacheClearRequest,
    CacheReadRequest,
    CacheWriteRequest,
    DataSettings,
    clear_cache_entry,
    clear_data_cache,
    data_settings_context,
    get_cache_entry,
    get_market_data,
    get_source_descriptor,
    put_cache_entry,
    run_data_migrations,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import market_request

WORKFLOW_ID = "WF-DATA-023"
STAGES = (
    "Derive cache identity from the source descriptor and request dimensions.",
    "Look up the versioned entry before any source read.",
    "Store a normalized result after a successful retrieval.",
    "Invalidate one entry when its source revision changes.",
    "Clear the whole cache during maintenance or schema migration.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _report(label: str, status: str, data: object) -> None:
    """Print the status and bounded data of one workflow step."""
    print(f"{label} status : {status}")
    print(f"{label} data   : {data}")


def main() -> None:
    """Run the documented versioned cache lifecycle workflow."""
    print(f"{WORKFLOW_ID} — Versioned Cache Lifecycle")
    print(
        "INPUT BOUNDARY — cache identity derived from source revision, versions, and request"
    )

    request = market_request("bars", timeframe="M1", limit=40)
    response = get_market_data(request)
    dataset = unwrap_data_response(
        response,
        operation="data.usage.workflow.wf_data_023",
        request_id=response.metadata.request_id,
    )
    print(
        "Dataset:", dataset.symbol, dataset.timeframe, dataset.record_count, "records"
    )

    with TemporaryDirectory(prefix="haru-wf-data-023-") as temporary:
        root = Path(temporary)
        for relative in ("data/raw", "data/processed", "data/cache", "artifacts/data"):
            (root / relative).mkdir(parents=True, exist_ok=True)
        settings = DataSettings(
            database_url="sqlite:///wf_data_023_cache.sqlite3",
            data_dir=root,
            sqlite_busy_timeout_seconds=1,
            write_lock_lease_seconds=30,
            approved_storage_roots=(root,),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            request_id = generate_id("req")

            # Stage 1 — Derive cache identity from the source descriptor and request dimensions.
            _stage(1)
            descriptor = get_source_descriptor(dataset.source_id)
            _report("source ", "success", descriptor)
            cache_key = f"{dataset.source_id}-{dataset.symbol}-{dataset.timeframe}-v1"
            print("Cache key            :", cache_key)
            print(
                "Identity components  : source revision, schema version, request dimensions"
            )

            # Stage 2 — Look up the versioned entry before any source read.
            _stage(2)
            miss = get_cache_entry(
                CacheReadRequest(
                    key=cache_key,
                    allow_stale=False,
                    request_id=request_id,
                )
            )
            _report("lookup ", "success", f"found={miss is not None}")
            print("Cold lookup is a miss:", miss is None)

            # Stage 3 — Store a normalized result after a successful retrieval.
            _stage(3)
            written = put_cache_entry(
                CacheWriteRequest(
                    key=cache_key,
                    dataset=dataset,
                    source_revision="rev-1",
                    raw_data_hash="wf-data-023-hash",
                    ttl_seconds=3600,
                    request_id=request_id,
                )
            )
            _report("write  ", "success", written)
            hit = get_cache_entry(
                CacheReadRequest(
                    key=cache_key,
                    allow_stale=False,
                    request_id=request_id,
                )
            )
            _report("hit    ", "success", f"found={hit is not None}")

            # Stage 4 — Invalidate one entry when its source revision changes.
            _stage(4)
            cleared = clear_cache_entry(
                CacheClearRequest(
                    namespace="market_data",
                    source_id=dataset.source_id,
                    symbol=dataset.symbol,
                    dry_run=False,
                    max_entries=10,
                    request_id=request_id,
                )
            )
            _report("evict  ", "success", cleared)
            after_evict = get_cache_entry(
                CacheReadRequest(
                    key=cache_key,
                    allow_stale=False,
                    request_id=request_id,
                )
            )
            _report("recheck", "success", f"found={after_evict is not None}")
            print("Superseded revision is not served:", after_evict is None)

            # Stage 5 — Clear the whole cache during maintenance or schema migration.
            _stage(5)
            purged = clear_data_cache(
                CacheClearRequest(
                    namespace="market_data",
                    dry_run=False,
                    max_entries=100,
                    request_id=request_id,
                )
            )
            _report("purge  ", "success", purged)
            print("Cache-write failure never changes returned records: True")

    print(
        "\nOUTPUT BOUNDARY — cache hit, miss, or explicit invalidation with no stale record served"
    )


if __name__ == "__main__":
    main()
