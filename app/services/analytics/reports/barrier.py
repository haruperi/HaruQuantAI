"""Analytics barrier-tail evidence and report section builders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from types import MappingProxyType

from app.services.analytics.contracts import (
    AnalyticsValidationError,
    ClosedTradeLedger,
    MetricEvidence,
    ReportSection,
)
from app.utils import get_logger

logger = get_logger(__name__)

_MIN_DAILY_OBSERVATIONS = 2


class _FirstPassageLike:
    """Structural type for first-passage report fixtures and contracts."""

    mandate_version: str
    probability_target: Decimal
    probability_daily_breach: Decimal
    probability_drawdown_breach: Decimal
    probability_expired: Decimal
    median_termination_day: Decimal | None


class _JointFirstPassageLike:
    """Structural type for joint first-passage report fixtures and contracts."""

    surviving_accounts_distribution: Mapping[int, Decimal]
    probability_none_survive: Decimal


def _quantile(values: Sequence[Decimal], probability: Decimal) -> Decimal:
    """Calculate a deterministic type-seven Decimal quantile.

    Args:
        values: Ordered or unordered finite observations.
        probability: Quantile probability in the inclusive unit interval.

    Returns:
        Interpolated Decimal quantile.
    """
    ordered = sorted(values)
    position = probability * Decimal(len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (
        position - Decimal(lower)
    )


def _daily_losses(ledger: object) -> tuple[Decimal, ...]:
    """Extract positive daily losses from either supported ledger shape.

    Args:
        ledger: Closed-trade daily P&L or canonical Analytics result.

    Returns:
        Non-negative daily loss observations.

    Raises:
        AnalyticsValidationError: If the ledger lacks finite aligned evidence.
    """
    if isinstance(ledger, ClosedTradeLedger):
        return tuple(max(Decimal(0), -value) for value in ledger.daily_pnl)
    daily = getattr(ledger, "daily_equity_curve", None)
    previous = getattr(ledger, "initial_balance", None)
    if not isinstance(daily, Sequence) or not isinstance(previous, Decimal):
        raise AnalyticsValidationError(
            "trading result ledger does not expose required fields"
        )
    if len(daily) < _MIN_DAILY_OBSERVATIONS:
        raise AnalyticsValidationError("daily equity ledger needs two observations")
    losses: list[Decimal] = []
    for point in daily:
        if not isinstance(point, Mapping):
            raise AnalyticsValidationError("equity points must be mapping records")
        value = point.get("equity")
        if not isinstance(value, Decimal) or not value.is_finite():
            raise AnalyticsValidationError(
                "daily equity must be finite Decimal evidence"
            )
        losses.append(max(Decimal(0), previous - value))
        previous = value
    return tuple(losses)


def build_worst_day_distribution(
    ledger: object,
    *,
    percentiles: Sequence[Decimal],
) -> object:
    """Build ordered percentiles of positive worst-single-day loss.

    Args:
        ledger: Closed-trade daily P&L or canonical Analytics result.
        percentiles: Strictly increasing probabilities in ``[0, 1]``.

    Returns:
        Immutable ``WorstDayDistribution``-compatible evidence object.

    Raises:
        AnalyticsValidationError: If observations or percentiles are invalid.
    """
    logger.info("Building Analytics worst-single-day loss distribution")
    losses = _daily_losses(ledger)
    checked = tuple(percentiles)
    if not checked or any(
        not value.is_finite() or value < 0 or value > 1 for value in checked
    ):
        raise AnalyticsValidationError("worst-day percentiles are invalid")
    if checked != tuple(sorted(set(checked))):
        raise AnalyticsValidationError("worst-day percentiles must be ordered")
    values = MappingProxyType(
        {str(value): _quantile(losses, value) for value in checked}
    )
    return WorstDayDistribution(
        percentiles=values,
        observations=len(losses),
        maximum_loss=max(losses),
    )


class WorstDayDistribution:
    """Small immutable-like Analytics barrier distribution contract."""

    __slots__ = ("maximum_loss", "observations", "percentiles")

    def __init__(
        self,
        *,
        percentiles: Mapping[str, Decimal],
        observations: int,
        maximum_loss: Decimal,
    ) -> None:
        """Initialize validated distribution evidence.

        Args:
            percentiles: Named non-empty percentile values.
            observations: Number of source observations.
            maximum_loss: Maximum observed non-negative loss.

        Raises:
            AnalyticsValidationError: If the distribution is incomplete.
        """
        if observations <= 0 or not percentiles or not maximum_loss.is_finite():
            raise AnalyticsValidationError("worst-day distribution is incomplete")
        self.percentiles = MappingProxyType(dict(percentiles))
        self.observations = observations
        self.maximum_loss = maximum_loss


def _probability_metrics(first_passage: object) -> tuple[MetricEvidence, ...]:
    """Convert first-passage report probabilities to Analytics metrics.

    Args:
        first_passage: First-passage report-like object.

    Returns:
        Validated Analytics metrics.

    Raises:
        AnalyticsValidationError: If a probability or median is invalid.
    """
    names = (
        "probability_target",
        "probability_daily_breach",
        "probability_drawdown_breach",
        "probability_expired",
    )
    metrics: list[MetricEvidence] = []
    for name in names:
        value = getattr(first_passage, name, None)
        if not isinstance(value, Decimal) or not 0 <= value <= 1:
            raise AnalyticsValidationError("barrier probability is invalid")
        metrics.append(MetricEvidence(name, "calculated", value, "probability"))
    median = getattr(first_passage, "median_termination_day", None)
    if median is not None and (
        not isinstance(median, Decimal) or not median.is_finite()
    ):
        raise AnalyticsValidationError("barrier median day is invalid")
    metrics.append(
        MetricEvidence(
            "median_termination_day",
            "calculated" if median is not None else "undefined",
            median,
            "day",
        )
    )
    return tuple(metrics)


def build_barrier_section(
    first_passage: _FirstPassageLike | None,
    joint: _JointFirstPassageLike | None,
    worst_day: WorstDayDistribution | None,
    *,
    mandate_version: str,
    mode_sensitivity: Mapping[object, _FirstPassageLike] | None = None,
) -> ReportSection:
    """Assemble barrier evidence or explicitly skip when evidence is absent.

    Args:
        first_passage: Single-account first-passage evidence.
        joint: Joint-account survival evidence.
        worst_day: Worst-day percentile distribution.
        mandate_version: Mandate version bound to the report.
        mode_sensitivity: Optional same-path drawdown-mode reports.

    Returns:
        Completed or skipped barrier report section.

    Raises:
        AnalyticsValidationError: If supplied barrier evidence is incompatible.
    """
    logger.info("Building Analytics barrier report section")
    if not mandate_version.strip():
        raise AnalyticsValidationError("mandate version is required")
    if (
        first_passage is None
        or joint is None
        or worst_day is None
        or mode_sensitivity is None
    ):
        return ReportSection(
            section_key="barrier",
            criticality="optional",
            metrics=(),
            status="skipped",
            reason="barrier evidence is incomplete",
        )
    metrics = list(_probability_metrics(first_passage))
    distribution = getattr(joint, "surviving_accounts_distribution", None)
    none_survive = getattr(joint, "probability_none_survive", None)
    if (
        not isinstance(distribution, Mapping)
        or not isinstance(none_survive, Decimal)
        or not 0 <= none_survive <= 1
        or any(
            not isinstance(value, Decimal) or not 0 <= value <= 1
            for value in distribution.values()
        )
    ):
        raise AnalyticsValidationError("joint barrier evidence is incomplete")
    metrics.append(
        MetricEvidence(
            "probability_none_survive", "calculated", none_survive, "probability"
        )
    )
    metrics.append(
        MetricEvidence(
            "surviving_accounts_distribution",
            "calculated",
            {str(key): value for key, value in distribution.items()},
            "probability",
        )
    )
    metrics.extend(
        MetricEvidence(f"worst_day_percentile_{key}", "calculated", value, "currency")
        for key, value in worst_day.percentiles.items()
    )
    metrics.append(
        MetricEvidence(
            "worst_day_maximum_loss", "calculated", worst_day.maximum_loss, "currency"
        )
    )
    mode_values: dict[str, Decimal] = {}
    for mode, report in mode_sensitivity.items():
        value = getattr(report, "probability_target", None)
        if not isinstance(value, Decimal) or not 0 <= value <= 1:
            raise AnalyticsValidationError(
                "drawdown sensitivity probability is invalid"
            )
        mode_values[str(mode)] = value
    metrics.append(
        MetricEvidence(
            "drawdown_mode_sensitivity", "calculated", mode_values, "probability"
        )
    )
    metrics.append(
        MetricEvidence("mandate_version", "calculated", mandate_version, "identifier")
    )
    return ReportSection(
        section_key="barrier",
        criticality="optional",
        metrics=tuple(metrics),
        status="completed",
    )


__all__ = [
    "WorstDayDistribution",
    "build_barrier_section",
    "build_worst_day_distribution",
]
