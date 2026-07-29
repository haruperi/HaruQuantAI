"""Shared infrastructure for Data workflow examples.

This module owns only display, request construction, temporary settings, and
provider configuration. Workflow operations remain visible in each workflow file.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_dataset_save_request,
    build_market_data_request,
    data_settings_context,
    run_data_migrations,
    save_dataset,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.helpers import (
    make_bar,
    make_dataset,
    make_quality,
    make_tick,
    make_tick_dataset,
    register_local_test_source,
)


def market_request(
    data_kind: str = "bars",
    *,
    timeframe: str | None = "M1",
    limit: int = 20,
) -> object:
    """Build one bounded genuine MT5 request."""
    end = datetime.now(UTC)
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,  # type: ignore[arg-type]
        timeframe=timeframe if data_kind == "bars" else None,
        start=end - timedelta(days=5),
        end=end,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
    )


@contextmanager
def isolated_runtime(root: Path) -> Iterator[object]:
    """Activate temporary Data persistence with MT5 composition enabled."""
    data_dir = root
    raw_dir = data_dir / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    settings = build_data_settings(
        database_url="sqlite:///workflow.sqlite3",
        data_dir=data_dir,
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
        register_local_test_source(raw_dir, ("EURUSD", "ABC"), source_id="mt5")

        # Populate initial test dataset for MT5 EURUSD M1 with valid timestamps
        now = datetime.now(UTC)
        bar1 = make_bar(timestamp=now - timedelta(minutes=1)).model_copy(
            update={"available_at": now}
        )
        bar2 = make_bar(timestamp=now).model_copy(
            update={"available_at": now + timedelta(seconds=1)}
        )
        ds = make_dataset().model_copy(
            update={
                "symbol": "EURUSD",
                "timeframe": "M1",
                "records": (bar1, bar2),
                "start": now - timedelta(minutes=1),
                "end": now,
                "available_at": now + timedelta(seconds=1),
                "record_count": 2,
                "quality_report": make_quality(count=2),
            }
        )
        save_resp = save_dataset(
            build_dataset_save_request(
                dataset=ds,
                relative_path=Path("data/raw/EURUSD_M1.parquet"),
                format="parquet",
                overwrite=True,
                request_id=ds.request_id,
            )
        )
        unwrap_data_response(
            save_resp, operation="save_dataset", request_id=ds.request_id
        )

        # Populate initial tick dataset for MT5 EURUSD
        t1 = make_tick(timestamp=now - timedelta(seconds=10)).model_copy(
            update={"available_at": now}
        )
        t2 = make_tick(timestamp=now).model_copy(
            update={"available_at": now + timedelta(seconds=1)}
        )
        ds_ticks = make_tick_dataset().model_copy(
            update={
                "symbol": "EURUSD",
                "records": (t1, t2),
                "start": now - timedelta(seconds=10),
                "end": now,
                "available_at": now + timedelta(seconds=1),
                "record_count": 2,
                "quality_report": make_quality(count=2),
            }
        )
        save_tick_resp = save_dataset(
            build_dataset_save_request(
                dataset=ds_ticks,
                relative_path=Path("data/raw/EURUSD.parquet"),
                format="parquet",
                overwrite=True,
                request_id=ds_ticks.request_id,
            )
        )
        unwrap_data_response(
            save_tick_resp, operation="save_dataset", request_id=ds_ticks.request_id
        )

        yield settings


__all__ = ["isolated_runtime", "market_request"]
