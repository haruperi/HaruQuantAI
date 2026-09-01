"""Read-only cross-account correlation and common-mode exposure evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from app.composition.logging import get_logger
from app.services.portfolio.contracts.errors import PortfolioError

logger = get_logger(__name__)

_MIN_OBSERVATIONS = 2


def _series(values: Sequence[Decimal], window: int) -> tuple[Decimal, ...]:
    """Validate and bound one rolling series.

    Args:
        values: Account-keyed measured observations.
        window: Maximum rolling observation count.

    Returns:
        The bounded finite observation series.

    Raises:
        PortfolioError: If the series has fewer than two finite observations.
    """
    sample = tuple(values)[-window:]
    if len(sample) < _MIN_OBSERVATIONS or any(
        not value.is_finite() for value in sample
    ):
        raise PortfolioError("PORT_EVIDENCE_INVALID", "CORRELATION_SERIES")
    return sample


def _correlation(left: Sequence[Decimal], right: Sequence[Decimal]) -> Decimal:
    """Calculate Pearson correlation with Decimal arithmetic.

    Args:
        left: First aligned observation series.
        right: Second aligned observation series.

    Returns:
        Exact Decimal Pearson correlation.

    Raises:
        PortfolioError: If series alignment or variance is invalid.
    """
    if len(left) != len(right) or len(left) < _MIN_OBSERVATIONS:
        raise PortfolioError("PORT_EVIDENCE_INVALID", "CORRELATION_ALIGNMENT")
    left_mean = sum(left, Decimal(0)) / Decimal(len(left))
    right_mean = sum(right, Decimal(0)) / Decimal(len(right))
    covariance = sum(
        (a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True)
    )
    left_variance = sum(((value - left_mean) ** 2 for value in left), Decimal(0))
    right_variance = sum(((value - right_mean) ** 2 for value in right), Decimal(0))
    if left_variance <= 0 or right_variance <= 0:
        raise PortfolioError("PORT_EVIDENCE_INVALID", "CORRELATION_CONSTANT_SERIES")
    return covariance / (left_variance * right_variance).sqrt()


@dataclass(frozen=True)
class CrossAccountCorrelationReport:
    """Rolling return/decision correlation evidence and alerts."""

    window: int
    alert_threshold: Decimal
    return_correlation: Mapping[str, Decimal]
    decision_correlation: Mapping[str, Decimal]
    alert_pairs: tuple[str, ...]
    counterparties: Mapping[str, str]


@dataclass(frozen=True)
class CommonModeExposureReport:
    """Loss-at-stop aggregation under one shared adverse scenario."""

    aggregate_loss_at_stop_by_factor: Mapping[str, Decimal]
    breached_accounts: Mapping[str, tuple[str, ...]]
    software_dependencies: Mapping[str, tuple[str, ...]]
    signal_dependencies: Mapping[str, tuple[str, ...]]


def measure_cross_account_correlation(
    return_series: Mapping[str, Sequence[Decimal]],
    decision_series: Mapping[str, Sequence[Decimal]],
    counterparties: Mapping[str, str],
    *,
    window: int = 20,
    alert_threshold: Decimal = Decimal("0.60"),
) -> CrossAccountCorrelationReport:
    """Measure rolling cross-account returns and decisions.

    Args:
        return_series: Account-keyed fractional return observations.
        decision_series: Account-keyed decision observations.
        counterparties: Account-keyed counterparty identifiers.
        window: Positive rolling observation window.
        alert_threshold: Absolute correlation threshold for alerts.

    Returns:
        Deterministic pairwise correlation report.

    Raises:
        PortfolioError: If account keys, evidence, or settings are invalid.
    """
    logger.info("Measuring Portfolio cross-account correlation")
    if window <= 1 or not 0 <= alert_threshold <= 1:
        raise PortfolioError("PORT_CONFIG_INVALID", "CORRELATION_POLICY")
    accounts = tuple(sorted(return_series))
    if (
        len(accounts) < _MIN_OBSERVATIONS
        or set(accounts) != set(decision_series)
        or set(accounts) != set(counterparties)
    ):
        raise PortfolioError("PORT_EVIDENCE_INVALID", "CORRELATION_ACCOUNT_SET")
    returns = {account: _series(return_series[account], window) for account in accounts}
    decisions = {
        account: _series(decision_series[account], window) for account in accounts
    }
    return_correlations: dict[str, Decimal] = {}
    decision_correlations: dict[str, Decimal] = {}
    alerts: set[str] = set()
    for index, left in enumerate(accounts):
        for right in accounts[index + 1 :]:
            if len(returns[left]) != len(returns[right]) or len(decisions[left]) != len(
                decisions[right]
            ):
                raise PortfolioError("PORT_EVIDENCE_INVALID", "CORRELATION_ALIGNMENT")
            pair = f"{left}:{right}"
            return_value = _correlation(returns[left], returns[right])
            decision_value = _correlation(decisions[left], decisions[right])
            return_correlations[pair] = return_value
            decision_correlations[pair] = decision_value
            if max(abs(return_value), abs(decision_value)) >= alert_threshold:
                alerts.add(pair)
    return CrossAccountCorrelationReport(
        window=window,
        alert_threshold=alert_threshold,
        return_correlation=MappingProxyType(return_correlations),
        decision_correlation=MappingProxyType(decision_correlations),
        alert_pairs=tuple(sorted(alerts)),
        counterparties=MappingProxyType(dict(sorted(counterparties.items()))),
    )


def assess_common_mode_exposure(
    loss_at_stop_by_account: Mapping[str, Mapping[str, Decimal]],
    account_headroom: Mapping[str, Decimal],
    shared_adverse_scenario: Mapping[str, Decimal],
    *,
    software_dependencies: Mapping[str, Sequence[str]],
    signal_dependencies: Mapping[str, Sequence[str]],
) -> CommonModeExposureReport:
    """Aggregate loss-at-stop exposure and identify shared-scenario breaches.

    Args:
        loss_at_stop_by_account: Account-keyed factor loss-at-stop amounts.
        account_headroom: Account-keyed absolute risk headroom.
        shared_adverse_scenario: Factor-keyed adverse scenario multipliers.
        software_dependencies: Account-keyed shared software dependencies.
        signal_dependencies: Account-keyed shared signal dependencies.

    Returns:
        Common-mode exposure report with aggregate factors and breaches.

    Raises:
        PortfolioError: If account keys or evidence values are invalid.
    """
    logger.info("Assessing Portfolio common-mode loss-at-stop exposure")
    accounts = set(loss_at_stop_by_account)
    if accounts != set(account_headroom):
        raise PortfolioError("PORT_EVIDENCE_INVALID", "COMMON_MODE_ACCOUNT_SET")
    if any(
        not value.is_finite() or value < 0
        for mapping in loss_at_stop_by_account.values()
        for value in mapping.values()
    ) or any(not value.is_finite() or value < 0 for value in account_headroom.values()):
        raise PortfolioError("PORT_EVIDENCE_INVALID", "COMMON_MODE_VALUES")
    aggregate: dict[str, Decimal] = {}
    breached: dict[str, tuple[str, ...]] = {}
    for account in sorted(accounts):
        exposure = loss_at_stop_by_account[account]
        factors = tuple(sorted(set(exposure) | set(shared_adverse_scenario)))
        scenario_loss = sum(
            exposure.get(factor, Decimal(0))
            * shared_adverse_scenario.get(factor, Decimal(0))
            for factor in factors
        )
        for factor in factors:
            aggregate[factor] = aggregate.get(factor, Decimal(0)) + exposure.get(
                factor, Decimal(0)
            )
        if scenario_loss > account_headroom[account]:
            breached[account] = factors
    return CommonModeExposureReport(
        aggregate_loss_at_stop_by_factor=MappingProxyType(
            dict(sorted(aggregate.items()))
        ),
        breached_accounts=MappingProxyType(breached),
        software_dependencies=MappingProxyType(
            {
                account: tuple(sorted(values))
                for account, values in sorted(software_dependencies.items())
            }
        ),
        signal_dependencies=MappingProxyType(
            {
                account: tuple(sorted(values))
                for account, values in sorted(signal_dependencies.items())
            }
        ),
    )


__all__ = [
    "CommonModeExposureReport",
    "CrossAccountCorrelationReport",
    "assess_common_mode_exposure",
    "measure_cross_account_correlation",
]
