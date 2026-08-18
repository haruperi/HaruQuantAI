"""Internal immutable Analytics workbench payload contracts (FEAT-ANLT-11).

These types are internal to the Analytics workbench feature. The domain
package root exposes only the standalone builder function; no class or
constant crosses the public boundary.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.services.analytics.contracts.errors import AnalyticsValidationError


@dataclass(frozen=True, slots=True)
class AnalyticsWorkbenchSection:
    """One finite owner-produced workbench section.

    Attributes:
        key: Stable workbench section identifier.
        status: Whether authoritative owner evidence is present.
        unit: Single section unit when every item shares one, else ``None``.
        source_context: Owner source context (``all``, ``long``, ``short``).
        sample_count: Number of retained items after truncation.
        reason: Unavailability reason when status is ``unavailable``.
        truncated: Whether items were cut to the section bound.
        total_count: Total available items before truncation.
        items: Ordered JSON-safe projection rows.
    """

    key: str
    status: Literal["completed", "unavailable"]
    unit: str | None
    source_context: str
    sample_count: int
    reason: str | None
    truncated: bool
    total_count: int
    items: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        """Validate section shape and status evidence.

        Raises:
            AnalyticsValidationError: If status, counts, or reasons conflict.
        """
        if self.status == "unavailable":
            if self.reason != "authoritative_evidence_unavailable":
                raise AnalyticsValidationError(
                    "unavailable workbench section requires the owner reason"
                )
            if self.items:
                raise AnalyticsValidationError(
                    "unavailable workbench section carries no items"
                )
        if self.status == "completed" and self.reason is not None:
            raise AnalyticsValidationError("completed section carries no reason")
        if self.sample_count != len(self.items):
            raise AnalyticsValidationError("section sample count disagrees")
        if self.sample_count > self.total_count:
            raise AnalyticsValidationError("section sample count exceeds total")
        if self.truncated and self.sample_count >= self.total_count:
            raise AnalyticsValidationError("truncation flag disagrees with counts")


@dataclass(frozen=True, slots=True)
class AnalyticsWorkbenchPayload:
    """Complete finite non-binding Analytics workbench payload v1.

    Attributes:
        contract_version: Compatibility identity.
        schema_id: Schema identity.
        payload_id: Stable payload identity derived from the report.
        report_id: Owning Analytics report identity.
        generated_at: UTC generation timestamp.
        summary: Metric summary section.
        equity_curve: Equity presentation series section.
        drawdown_curve: Drawdown series section.
        returns_series: Return series section.
        vami: VAMI series section.
        monthly_returns: Monthly returns section.
        period_tables: Period breakdown section.
        trade_calendar: Trade calendar section.
        streaks: Streak statistics section.
        distribution: Return-distribution metric section.
        histogram: Return histogram section.
        outliers: Outlier evidence section.
        excursions: MAE/MFE excursion section.
        duration: Trade-duration section.
        grouped_performance: Context-grouped performance section.
        benchmark: Benchmark metric section.
        costs: Cost-efficiency metric section.
        warnings: JSON-safe owner warning rows.
        quality_flags: JSON-safe owner quality-flag rows.
        lineage: JSON-safe owner lineage mapping.
        truncation: Truncation evidence rows.
        non_binding: Always true; the payload never governs behaviour.
    """

    contract_version: Literal["v1"]
    schema_id: Literal["analytics.workbench_payload.v1"]
    payload_id: str
    report_id: str
    generated_at: datetime
    summary: AnalyticsWorkbenchSection
    equity_curve: AnalyticsWorkbenchSection
    drawdown_curve: AnalyticsWorkbenchSection
    returns_series: AnalyticsWorkbenchSection
    vami: AnalyticsWorkbenchSection
    monthly_returns: AnalyticsWorkbenchSection
    period_tables: AnalyticsWorkbenchSection
    trade_calendar: AnalyticsWorkbenchSection
    streaks: AnalyticsWorkbenchSection
    distribution: AnalyticsWorkbenchSection
    histogram: AnalyticsWorkbenchSection
    outliers: AnalyticsWorkbenchSection
    excursions: AnalyticsWorkbenchSection
    duration: AnalyticsWorkbenchSection
    grouped_performance: AnalyticsWorkbenchSection
    benchmark: AnalyticsWorkbenchSection
    costs: AnalyticsWorkbenchSection
    warnings: tuple[Mapping[str, object], ...]
    quality_flags: tuple[Mapping[str, object], ...]
    lineage: Mapping[str, object]
    truncation: tuple[Mapping[str, object], ...]
    non_binding: Literal[True] = True

    def __post_init__(self) -> None:
        """Validate payload identity.

        Raises:
            AnalyticsValidationError: If identity fields are empty.
        """
        if not self.payload_id or not self.report_id:
            raise AnalyticsValidationError("workbench payload identity is invalid")


__all__ = ("AnalyticsWorkbenchPayload", "AnalyticsWorkbenchSection")
