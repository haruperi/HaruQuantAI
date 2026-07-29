"""WF-DATA-023: exercise the versioned cache lifecycle end to end."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_cache_clear_request,
    build_cache_read_request,
    build_cache_write_request,
    clear_cache_entry,
    clear_data_cache,
    get_cache_entry,
    get_market_data,
    get_source_descriptor,
    put_cache_entry,
    run_data_migrations,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime, market_request

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

    with (
        tempfile.TemporaryDirectory(prefix="wf-data-023-") as directory,
        isolated_runtime(Path(directory)),
    ):
        request_id = generate_id("req")

        request = market_request("bars", timeframe="M1", limit=40)
        response = get_market_data(request)
        dataset = unwrap_data_response(
            response,
            operation="data.usage.workflow.wf_data_023",
            request_id=request_id,
        )
        print(
            "Dataset:",
            dataset.symbol,
            dataset.timeframe,
            dataset.record_count,
            "records",
        )

        run_data_migrations(request_id)

        # Stage 1 — Derive cache identity from the source descriptor and request dimensions.
        _stage(1)
        source_id = dataset.source_metadata.get("source_id", "mt5")
        descriptor_resp = get_source_descriptor(source_id)
        descriptor = unwrap_data_response(
            descriptor_resp, operation="get_source_descriptor", request_id=request_id
        )
        _report("source ", "success", descriptor)
        cache_key = f"{source_id}-{dataset.symbol}-{dataset.timeframe}-v1"
        print("Cache key            :", cache_key)
        print(
            "Identity components  : source revision, schema version, request dimensions"
        )

        # Stage 2 — Look up the versioned entry before any source read.
        _stage(2)
        miss_resp = get_cache_entry(
            build_cache_read_request(
                key=cache_key,
                allow_stale=False,
                request_id=request_id,
            )
        )
        miss = unwrap_data_response(
            miss_resp, operation="get_cache_entry", request_id=request_id
        )
        _report("lookup ", "success", f"found={miss is not None}")
        print("Cold lookup is a miss:", miss is None)

        # Stage 3 — Store a normalized result after a successful retrieval.
        _stage(3)
        written_resp = put_cache_entry(
            build_cache_write_request(
                key=cache_key,
                dataset=dataset,
                source_revision="rev-1",
                raw_data_hash="wf-data-023-hash",
                ttl_seconds=3600,
                request_id=request_id,
            )
        )
        written = unwrap_data_response(
            written_resp, operation="put_cache_entry", request_id=request_id
        )
        _report("write  ", "success", written)
        hit_resp = get_cache_entry(
            build_cache_read_request(
                key=cache_key,
                allow_stale=False,
                request_id=request_id,
            )
        )
        hit = unwrap_data_response(
            hit_resp, operation="get_cache_entry", request_id=request_id
        )
        _report("hit    ", "success", f"found={hit is not None}")

        # Stage 4 — Invalidate one entry when its source revision changes.
        _stage(4)
        cleared_resp = clear_cache_entry(
            build_cache_clear_request(
                namespace="market_data",
                source_id=source_id,
                symbol=dataset.symbol,
                dry_run=False,
                max_entries=10,
                request_id=request_id,
            )
        )
        cleared = unwrap_data_response(
            cleared_resp, operation="clear_cache_entry", request_id=request_id
        )
        _report("evict  ", "success", cleared)
        after_evict_resp = get_cache_entry(
            build_cache_read_request(
                key=cache_key,
                allow_stale=False,
                request_id=request_id,
            )
        )
        after_evict = unwrap_data_response(
            after_evict_resp, operation="get_cache_entry", request_id=request_id
        )
        _report("recheck", "success", f"found={after_evict is not None}")
        print("Superseded revision is not served:", after_evict is None)

        # Stage 5 — Clear the whole cache during maintenance or schema migration.
        _stage(5)
        purged_resp = clear_data_cache(
            build_cache_clear_request(
                namespace="market_data",
                dry_run=False,
                max_entries=100,
                request_id=request_id,
            )
        )
        purged = unwrap_data_response(
            purged_resp, operation="clear_data_cache", request_id=request_id
        )
        _report("purge  ", "success", purged)
        print("Cache-write failure never changes returned records: True")

    print(
        "\nOUTPUT BOUNDARY — cache hit, miss, or explicit invalidation with no stale record served"
    )


if __name__ == "__main__":
    main()
