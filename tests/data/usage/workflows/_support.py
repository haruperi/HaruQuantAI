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

from app.services.data import DataSettings, MarketDataRequest, data_settings_context
from app.utils import generate_id


def market_request(
    data_kind: str = "bars",
    *,
    timeframe: str | None = "M1",
    limit: int = 20,
) -> MarketDataRequest:
    """Build one bounded genuine MT5 request."""
    end = datetime.now(UTC)
    return MarketDataRequest(
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
def isolated_runtime(root: Path) -> Iterator[DataSettings]:
    """Activate temporary Data persistence with MT5 composition enabled."""
    settings = DataSettings(
        database_url="sqlite:///workflow.sqlite3",
        data_dir=root,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(
            Path("raw"),
            Path("processed"),
            Path("data/raw"),
        ),
        data_provider_sources=("mt5",),
        data_raw_root=Path("raw"),
    )
    with data_settings_context(settings):
        yield settings


__all__ = ["isolated_runtime", "market_request"]
