"""Analytics Workbench frozen request and query contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.services.api.contracts.models import _BaseApiContract
from app.services.api.widgets.simulator.workbench_schemas import (
    MAX_TAGS,
)

PeriodDimension = Literal[
    "year", "quarter", "month", "week", "day", "day_of_week", "hour"
]
ComparisonMetric = Literal["summary", "returns", "risk", "ratios", "costs"]


class AnalyticsPeriodsQuery(_BaseApiContract):
    """Exact period-table query dimensions."""

    dimension: PeriodDimension = "month"
    context: Literal["all", "long", "short"] = "all"


class AnalyticsTradesQuery(_BaseApiContract):
    """Bounded trade-ledger pagination query."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)
    sort: Literal["exit_time_asc", "exit_time_desc"] = "exit_time_desc"
    side: Literal["all", "buy", "sell"] = "all"
    symbol: str | None = Field(default=None, max_length=32)


class AnalyticsCompareRequest(_BaseApiContract):
    """Owner-delegated multi-run comparison request."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.analytics_compare_request.v1"] = (
        "api.analytics_compare_request.v1"
    )
    run_ids: tuple[str, ...] = Field(min_length=2, max_length=10)
    metric: ComparisonMetric = "summary"


class AnalyticsAnnotationRequest(_BaseApiContract):
    """Mutable principal-owned annotation for one catalogue run."""

    name: str | None = Field(default=None, max_length=2_000)
    alias: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=2_000)
    tags: tuple[str, ...] = Field(default=(), max_length=MAX_TAGS)
    run_reason: str | None = Field(default=None, max_length=2_000)


class AnalyticsArchiveRequest(_BaseApiContract):
    """Request to change one run's archive state; metadata only."""

    archive_state: Literal["active", "archived"]


__all__ = (
    "AnalyticsAnnotationRequest",
    "AnalyticsArchiveRequest",
    "AnalyticsCompareRequest",
    "AnalyticsPeriodsQuery",
    "AnalyticsTradesQuery",
    "ComparisonMetric",
    "PeriodDimension",
)
