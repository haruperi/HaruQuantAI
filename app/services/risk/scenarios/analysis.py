"""Bounded deterministic advisory Risk scenario analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from app.services.risk.contracts import (
    LimitStatus,
    PortfolioRiskSnapshot,
    RiskDomainError,
    RiskErrorCode,
    RiskLimitResult,
    ScenarioDefinition,
    ScenarioResult,
)
from app.services.risk.contracts.responses import guard_risk_boundary
from app.utils import get_logger

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.risk.config import RiskConfig

_RELATIVE_METRICS = (
    "equity",
    "gross_exposure",
    "net_exposure",
    "historical_var",
    "historical_cvar",
)
_RATIO_METRICS = (
    "drawdown",
    "margin_utilization",
    "volatility",
    "portfolio_correlation",
)
_SUPPORTED_METRICS = frozenset((*_RELATIVE_METRICS, *_RATIO_METRICS))


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If timestamp is not aware UTC.
    """
    logger.debug("Validating Risk scenario UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("scenario time must be aware UTC")
    return value


def _baseline(snapshot: PortfolioRiskSnapshot) -> dict[str, Decimal]:
    """Extract exact available supported baseline metrics.

    Args:
        snapshot: Immutable portfolio Risk evidence.

    Returns:
        Supported finite baseline metrics.
    """
    logger.debug("Extracting supported Risk scenario baseline metrics")
    values: dict[str, Decimal] = {}
    for metric in (*_RELATIVE_METRICS, *_RATIO_METRICS):
        value = getattr(snapshot, metric)
        if value is not None:
            values[metric] = value
    return values


def _project(
    baseline: Mapping[str, Decimal], scenario: ScenarioDefinition
) -> dict[str, Decimal]:
    """Apply one exact bounded shock mapping deterministically.

    Args:
        baseline: Available supported baseline metrics.
        scenario: Exact advisory scenario definition.

    Returns:
        Projected metrics including unchanged supported baselines.

    Raises:
        ValueError: If a shock key or baseline is unsupported.
    """
    logger.debug("Applying one exact bounded advisory Risk scenario")
    unknown = set(scenario.shocks) - _SUPPORTED_METRICS
    unavailable = set(scenario.shocks) - set(baseline)
    if unknown or unavailable:
        raise ValueError("scenario shock metric is unsupported or unavailable")
    projected = dict(baseline)
    for metric, shock in scenario.shocks.items():
        value = baseline[metric]
        if metric in _RELATIVE_METRICS:
            projected[metric] = value * (Decimal(1) + shock)
        else:
            projected[metric] = min(Decimal(1), max(Decimal(0), value + shock))
    if projected["equity"] <= 0:
        raise ValueError("scenario projected equity must remain positive")
    if any(
        projected[metric] < 0
        for metric in (
            "gross_exposure",
            "historical_var",
            "historical_cvar",
        )
        if metric in projected
    ):
        raise ValueError("scenario projected magnitude cannot be negative")
    return projected


def _position_count(snapshot: PortfolioRiskSnapshot) -> int:
    """Count represented symbol positions without fetching external state.

    Args:
        snapshot: Immutable portfolio Risk evidence.

    Returns:
        Number of symbol-level exposure dimensions.
    """
    logger.debug("Counting represented positions for bounded scenario analysis")
    return sum(key.startswith("symbol:") for key in snapshot.exposure_by_dimension)


def _validate_bounds(
    snapshot: PortfolioRiskSnapshot,
    scenarios: Sequence[ScenarioDefinition],
    config: RiskConfig,
) -> None:
    """Validate scenario and represented-position workload bounds.

    Args:
        snapshot: Immutable portfolio evidence.
        scenarios: Requested scenario definitions.
        config: Active bounded workload policy.

    Raises:
        RiskDomainError: If either workload bound is exceeded.
    """
    logger.debug("Validating bounded Risk scenario workload")
    if len(scenarios) > config.max_scenarios_per_run:
        raise RiskDomainError(
            RiskErrorCode.PAYLOAD_TOO_LARGE, "scenario count exceeds configured bound"
        )
    if _position_count(snapshot) > config.max_positions_per_scenario_run:
        raise RiskDomainError(
            RiskErrorCode.PAYLOAD_TOO_LARGE,
            "scenario position count exceeds configured bound",
        )


@guard_risk_boundary(risk_level="medium", read_only=True)
def run_risk_scenario_analysis(
    snapshot: PortfolioRiskSnapshot,
    scenarios: Sequence[ScenarioDefinition],
    config: RiskConfig,
    *,
    now: datetime,
) -> tuple[ScenarioResult, ...]:
    """Run bounded immutable deterministic advisory scenario comparisons.

    Args:
        snapshot: Immutable portfolio Risk evidence.
        scenarios: Ordered bounded scenario definitions.
        config: Active immutable Risk policy.
        now: Caller-supplied UTC generation time.

    Returns:
        Ordered advisory-only baseline/projected comparisons.

    Raises:
        RiskDomainError: If workload bounds or deterministic calculation fails.
    """
    logger.info("Running bounded deterministic advisory Risk scenarios")
    try:
        checked_now = _utc(now)
        _validate_bounds(snapshot, scenarios, config)
        baseline = _baseline(snapshot)
        results = []
        for scenario in scenarios:
            projected = _project(baseline, scenario)
            differences = {
                metric: value - baseline[metric] for metric, value in projected.items()
            }
            results.append(
                ScenarioResult(
                    scenario_id=scenario.scenario_id,
                    baseline=baseline,
                    projected=projected,
                    differences=differences,
                    assumptions=scenario.assumptions,
                    seed=scenario.seed,
                    policy_version=config.policy_version,
                    evidence_refs=(
                        snapshot.snapshot_id,
                        *snapshot.evidence_refs.values(),
                    ),
                    warnings=("randomized_definition_applied_without_invented_path",)
                    if scenario.randomized
                    else (),
                    generated_at=checked_now,
                )
            )
        return tuple(results)
    except RiskDomainError:
        logger.exception("Risk scenario workload failed closed")
        raise
    except (ArithmeticError, KeyError, TypeError, ValueError) as error:
        raise RiskDomainError(
            RiskErrorCode.CALCULATION_FAILED,
            "scenario analysis calculation failed",
        ) from error


_STRESS_LAYERS = frozenset(
    {
        "nominal",
        "liquidity_adjusted",
        "gap",
        "event",
        "margin_liquidation",
        "portfolio_stress",
    }
)


@guard_risk_boundary(risk_level="medium", read_only=True)
def evaluate_stress_loss_gate(
    snapshot: PortfolioRiskSnapshot,
    layer_loss_ratios: Mapping[str, Decimal],
    max_stress_loss_ratio: Decimal,
    *,
    now: datetime,
) -> RiskLimitResult:
    """Evaluate a blocking stress-loss gate combining named stress layers.

    Distinct from the advisory :func:`run_risk_scenario_analysis`/
    ``ScenarioDefinition`` what-if analysis (``OD-RISK-01``): this is a
    separate, new, blocking check the governor precedence can consume,
    layering nominal, liquidity-adjusted, gap, event, margin-liquidation,
    and portfolio-stress loss ratios without touching or renaming Risk's
    existing advisory scenario model, pending the Simulator naming
    decision.

    Args:
        snapshot: Immutable portfolio Risk evidence.
        layer_loss_ratios: Non-negative equity-loss ratio per registered
            stress layer (``nominal``, ``liquidity_adjusted``, ``gap``,
            ``event``, ``margin_liquidation``, ``portfolio_stress``).
        max_stress_loss_ratio: Configured maximum combined stress-loss
            ratio.
        now: Caller-supplied UTC evaluation time.

    Returns:
        Ordered blocking stress-loss gate result.

    Raises:
        RiskDomainError: If a layer is unregistered or a ratio is negative.
    """
    logger.info("Evaluating blocking Risk stress-loss gate")
    checked_now = _utc(now)
    del checked_now
    unknown = set(layer_loss_ratios) - _STRESS_LAYERS
    if unknown or any(value < 0 for value in layer_loss_ratios.values()):
        raise RiskDomainError(
            RiskErrorCode.CALCULATION_FAILED,
            "stress layer identity or loss ratio is invalid",
        )
    total_loss_ratio = sum(layer_loss_ratios.values(), Decimal(0))
    status = (
        LimitStatus.FAIL
        if total_loss_ratio > max_stress_loss_ratio
        else LimitStatus.PASS
    )
    return RiskLimitResult(
        limit_id="stress_loss_gate",
        status=status,
        observed_value=total_loss_ratio,
        threshold_value=max_stress_loss_ratio,
        reason_code=RiskErrorCode.LIMIT_FAILED if status is LimitStatus.FAIL else None,
        evidence_refs=(snapshot.snapshot_id,),
        precedence=0,
        headroom_value=max_stress_loss_ratio - total_loss_ratio,
    )


__all__ = ["evaluate_stress_loss_gate", "run_risk_scenario_analysis"]
