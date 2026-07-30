"""Shared, non-workflow infrastructure for Research workflow examples."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_market_data_request,
    build_market_dataset,
    data_settings_context,
    get_market_data,
    unwrap_data_response,
)
from app.services.research import (
    create_research_value,
    prepare_research_dataset,
)
from app.utils import generate_id

_DATASET_ENV = "HARU_WORKFLOW_MARKET_DATASET"


def market_request(data_kind, *, timeframe, limit):
    """Build one bounded genuine MT5 request inline."""
    end = datetime.now(UTC)
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
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


def live_market_dataset():
    """Return genuine bounded MT5 evidence, reusing runner-captured evidence."""
    captured = os.environ.get(_DATASET_ENV)
    if captured:
        payload = json.loads(Path(captured).read_text(encoding="utf-8"))
        return build_market_dataset(**payload)
    with tempfile.TemporaryDirectory(prefix="research-market-data-") as directory:
        settings = build_data_settings(
            database_url="sqlite:///data.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            return unwrap_data_response(
                get_market_data(market_request("bars", timeframe="M1", limit=40)),
                operation="research.workflow.market_data",
                request_id=generate_id("req"),
            )


def limits() -> object:
    """Return bounded Research resource limits."""
    return create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)


def prepared_dataset() -> object:
    """Prepare genuine MT5 evidence through the canonical Research boundary."""
    return prepare_research_dataset(
        live_market_dataset(),
        cleaning=create_research_value(
            "CleaningConfig", "UTC", "error", "none", "keep_warn", "error"
        ),
        enrichment=create_research_value(
            "EnrichmentConfig", "EURUSD", True, True, False, True
        ),
        limits=limits(),
    )


__all__ = [
    "_DATASET_ENV",
    "limits",
    "live_market_dataset",
    "prepared_dataset",
]
