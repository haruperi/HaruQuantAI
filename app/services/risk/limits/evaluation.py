"""Deterministic portfolio and supplied market-context Risk limit evaluation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.risk.config import (
    DrawdownMode,
    FirmMandate,
    LossReferenceBasis,
    RiskConfig,
    compute_config_hash,
)
from app.services.risk.contracts import (
    LimitStatus,
    PortfolioRiskSnapshot,
    RiskDomainError,
    RiskErrorCode,
    RiskLimitResult,
    validate_market_context_evidence,
)
from app.services.risk.contracts.responses import (
    guard_risk_boundary,
    unwrap_risk_response,
)
from app.utils import get_logger

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.risk.contracts.evidence import _MarketContextEvidenceView


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If the timestamp is not aware UTC.
    """
    logger.debug("Validating Policy evaluation UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("policy evaluation time must be aware UTC")
    return value


def _result(
    limit_id: str,
    status: LimitStatus,
    observed: Decimal | None,
    threshold: Decimal | None,
    evidence_refs: tuple[str, ...],
    precedence: int,
    *,
    reason: RiskErrorCode | None = None,
    headroom: Decimal | None = None,
    reference_basis: str | None = None,
) -> RiskLimitResult:
    """Build one ordered limit result.

    Args:
        limit_id: Stable limit identity.
        status: Evaluation status.
        observed: Observed numeric value when applicable.
        threshold: Applied threshold when applicable.
        evidence_refs: Exact evidence references.
        precedence: Stable evaluation order.
        reason: Required failing reason code.
        headroom: Optional absolute monetary distance to the limit.
        reference_basis: Name of the balance basis used for evaluation.

    Returns:
        Immutable ordered limit result.
    """
    logger.debug("Building ordered Policy limit result: %s", limit_id)
    return RiskLimitResult(
        limit_id=limit_id,
        status=status,
        observed_value=observed,
        threshold_value=threshold,
        reason_code=reason,
        evidence_refs=evidence_refs,
        precedence=precedence,
        headroom_value=headroom,
        reference_basis=reference_basis,
    )


def _threshold_result(
    limit_id: str,
    observed: Decimal | None,
    threshold: Decimal | None,
    evidence_refs: tuple[str, ...],
    precedence: int,
) -> RiskLimitResult:
    """Evaluate an optional upper-bound threshold.

    Args:
        limit_id: Stable limit identity.
        observed: Observed value or None when evidence is missing.
        threshold: Applied upper bound or None when disabled.
        evidence_refs: Exact evidence references.
        precedence: Stable evaluation order.

    Returns:
        Pass, failure, or needs-evidence result.
    """
    logger.debug("Evaluating upper-bound Policy limit: %s", limit_id)
    if threshold is None:
        return _result(
            limit_id,
            LimitStatus.PASS,
            observed,
            None,
            evidence_refs,
            precedence,
        )
    if observed is None:
        return _result(
            limit_id,
            LimitStatus.NEEDS_MORE_EVIDENCE,
            None,
            threshold,
            evidence_refs,
            precedence,
            reason=RiskErrorCode.MISSING_EVIDENCE,
        )
    status = LimitStatus.FAIL if observed > threshold else LimitStatus.PASS
    return _result(
        limit_id,
        status,
        observed,
        threshold,
        evidence_refs,
        precedence,
        reason=RiskErrorCode.LIMIT_FAILED if status is LimitStatus.FAIL else None,
    )


def _loss_ratio(loss: Decimal, equity: Decimal) -> Decimal:
    """Calculate loss against its embedded reference equity.

    Args:
        loss: Non-negative monetary loss.
        equity: Current equity.

    Returns:
        Exact loss ratio, with depleted equity represented as one.
    """
    logger.debug("Calculating Policy loss ratio against reference equity")
    reference = equity + loss
    return Decimal(1) if reference <= 0 else loss / reference


def _reference_equity(
    snapshot: PortfolioRiskSnapshot,
    basis: LossReferenceBasis,
    *,
    loss: Decimal,
) -> Decimal | None:
    """Resolve one loss reference balance from supplied snapshot evidence.

    Args:
        snapshot: Portfolio evidence containing candidate reference balances.
        basis: Requested loss-reference basis.
        loss: Observed loss used for derived balance bases.

    Returns:
        Reference balance, or ``None`` when required evidence is unavailable.

    Raises:
        AssertionError: If an unsupported reference basis reaches this helper.
    """
    basis = LossReferenceBasis(basis)
    if basis is LossReferenceBasis.INITIAL_BALANCE:
        return snapshot.initial_balance
    if basis is LossReferenceBasis.CURRENT_BALANCE:
        return snapshot.equity
    if basis is LossReferenceBasis.EQUITY:
        return snapshot.equity
    if basis is LossReferenceBasis.DAY_START:
        return snapshot.equity + loss
    if basis is LossReferenceBasis.INCEPTION:
        return snapshot.equity + loss
    raise AssertionError("unsupported loss reference basis")


def _loss_limit_result(
    limit_id: str,
    loss: Decimal,
    configured_ratio: Decimal,
    snapshot: PortfolioRiskSnapshot,
    basis: LossReferenceBasis,
    evidence_refs: tuple[str, ...],
    precedence: int,
    *,
    absolute_limit: Decimal | None = None,
) -> RiskLimitResult:
    """Evaluate a loss limit while exposing absolute monetary headroom.

    Args:
        limit_id: Stable limit identity.
        loss: Observed non-negative loss.
        configured_ratio: Ratio limit when no absolute limit is supplied.
        snapshot: Portfolio evidence for reference-balance resolution.
        basis: Loss-reference basis.
        evidence_refs: Exact evidence references.
        precedence: Stable evaluation order.
        absolute_limit: Optional absolute limit override.

    Returns:
        Ordered result with ratio and absolute headroom evidence.
    """
    basis = LossReferenceBasis(basis)
    reference = _reference_equity(snapshot, basis, loss=loss)
    if reference is None or reference <= 0:
        return _result(
            limit_id,
            LimitStatus.NEEDS_MORE_EVIDENCE,
            None,
            absolute_limit or configured_ratio,
            evidence_refs,
            precedence,
            reason=RiskErrorCode.MISSING_EVIDENCE,
            reference_basis=basis.value,
        )
    threshold = (
        absolute_limit if absolute_limit is not None else reference * configured_ratio
    )
    observed_ratio = _loss_ratio(loss, reference - loss)
    threshold_ratio = threshold / reference if reference > 0 else Decimal(1)
    status = LimitStatus.FAIL if loss > threshold else LimitStatus.PASS
    return _result(
        limit_id,
        status,
        observed_ratio,
        threshold_ratio,
        evidence_refs,
        precedence,
        reason=RiskErrorCode.LIMIT_FAILED if status is LimitStatus.FAIL else None,
        headroom=threshold - loss,
        reference_basis=basis.value,
    )


def _drawdown_result(
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
    precedence: int,
    mandate: FirmMandate | None,
) -> RiskLimitResult:
    """Evaluate the configured drawdown floor in account currency.

    Args:
        snapshot: Portfolio evidence for initial, peak, and EOD balances.
        config: Active Risk configuration.
        evidence_refs: Exact evidence references.
        precedence: Stable evaluation order.
        mandate: Optional verified firm mandate.

    Returns:
        Ordered drawdown result with absolute monetary headroom.
    """
    mode = mandate.max_drawdown.mode if mandate is not None else config.drawdown_mode
    if mandate is not None:
        rule = mandate.max_drawdown
        limit = rule.value_absolute
        ratio = rule.value
        ratchet = rule.trail_stops_at_initial
    else:
        limit = None
        ratio = config.max_drawdown
        ratchet = config.drawdown_trail_stops_at_initial

    initial = snapshot.initial_balance
    if mandate is not None or mode is DrawdownMode.STATIC:
        reference = initial
    elif mode is DrawdownMode.TRAILING_EOD:
        reference = snapshot.highest_eod_balance
    else:
        reference = snapshot.peak_equity

    if reference is None or reference <= 0:
        if mandate is None and snapshot.peak_equity is None:
            return _threshold_result(
                "drawdown",
                snapshot.drawdown,
                config.max_drawdown,
                evidence_refs,
                precedence,
            )
        return _result(
            "drawdown",
            LimitStatus.NEEDS_MORE_EVIDENCE,
            None,
            limit or ratio,
            evidence_refs,
            precedence,
            reason=RiskErrorCode.MISSING_EVIDENCE,
            reference_basis=mode.value,
        )

    if limit is None:
        limit = reference * (ratio or Decimal(0))
    floor = reference - limit
    if ratchet and initial is not None:
        floor = min(floor, initial)
    headroom = snapshot.equity - floor
    consumed = max(Decimal(0), -headroom)
    status = LimitStatus.FAIL if headroom < 0 else LimitStatus.PASS
    return _result(
        "drawdown",
        status,
        consumed,
        limit,
        evidence_refs,
        precedence,
        reason=RiskErrorCode.LIMIT_FAILED if status is LimitStatus.FAIL else None,
        headroom=headroom,
        reference_basis=mode.value,
    )


_DRAWDOWN_STATE_NORMAL = "normal"
_DRAWDOWN_STATE_CAUTION = "caution"
_DRAWDOWN_STATE_RESTRICTED = "restricted"
_DRAWDOWN_STATE_CRITICAL = "critical"
_DRAWDOWN_STATE_LOCKED = "locked"


def _drawdown_state_result(
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
    precedence: int,
) -> RiskLimitResult:
    """Classify the drawdown state machine from configured ordered thresholds.

    Args:
        snapshot: Portfolio evidence carrying the current drawdown ratio.
        config: Active Risk configuration.
        evidence_refs: Exact evidence references.
        precedence: Stable evaluation order.

    Returns:
        Ordered drawdown-state result naming the classified state and headroom
        to the next stricter threshold; disabled (no configured thresholds)
        always passes.
    """
    logger.debug("Classifying Policy drawdown state")
    caution = config.drawdown_caution_threshold
    restricted = config.drawdown_restricted_threshold
    critical = config.drawdown_critical_threshold
    if caution is None or restricted is None or critical is None:
        return _result(
            "drawdown_state",
            LimitStatus.PASS,
            snapshot.drawdown,
            None,
            evidence_refs,
            precedence,
            reference_basis=_DRAWDOWN_STATE_NORMAL,
        )
    drawdown = snapshot.drawdown
    ordered = (
        (caution, _DRAWDOWN_STATE_CAUTION),
        (restricted, _DRAWDOWN_STATE_RESTRICTED),
        (critical, _DRAWDOWN_STATE_CRITICAL),
        (config.max_drawdown, _DRAWDOWN_STATE_LOCKED),
    )
    state = _DRAWDOWN_STATE_NORMAL
    next_threshold = caution
    for threshold, name in ordered:
        if drawdown >= threshold:
            state = name
        else:
            next_threshold = threshold
            break
    else:
        next_threshold = config.max_drawdown
    status = (
        LimitStatus.BLOCKED
        if state == _DRAWDOWN_STATE_LOCKED
        else LimitStatus.WARN
        if state != _DRAWDOWN_STATE_NORMAL
        else LimitStatus.PASS
    )
    return _result(
        "drawdown_state",
        status,
        drawdown,
        next_threshold,
        evidence_refs,
        precedence,
        reason=RiskErrorCode.LIMIT_FAILED if status is LimitStatus.BLOCKED else None,
        headroom=next_threshold - drawdown,
        reference_basis=state,
    )


def _freshness_result(
    as_of: datetime,
    now: datetime,
    max_age_seconds: int,
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate deterministic evidence freshness.

    Args:
        as_of: Evidence observation time.
        now: Injected evaluation time.
        max_age_seconds: Maximum permitted age.
        evidence_refs: Exact evidence references.

    Returns:
        Ordered freshness result.
    """
    logger.debug("Evaluating Policy evidence freshness")
    age = Decimal(str((now - as_of).total_seconds()))
    threshold = Decimal(max_age_seconds)
    if age < 0 or age > threshold:
        return _result(
            "freshness",
            LimitStatus.BLOCKED,
            age,
            threshold,
            evidence_refs,
            0,
            reason=RiskErrorCode.STALE_EVIDENCE,
        )
    return _result(
        "freshness",
        LimitStatus.PASS,
        age,
        threshold,
        evidence_refs,
        0,
    )


def _consistency_result(
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate snapshot gaps, embedded statuses, equity, and config binding.

    Args:
        snapshot: Immutable portfolio measurements.
        config: Active Risk policy.
        evidence_refs: Exact snapshot evidence references.

    Returns:
        Ordered consistency result.
    """
    logger.debug("Evaluating Policy snapshot consistency")
    failing_statuses = {LimitStatus.FAIL, LimitStatus.BLOCKED}
    inconsistent = (
        snapshot.equity <= 0
        or bool(snapshot.gaps)
        or any(item in failing_statuses for item in snapshot.limit_statuses.values())
        or snapshot.config_hash
        != unwrap_risk_response(
            compute_config_hash(config), operation="compute_config_hash"
        )
    )
    return _result(
        "consistency",
        LimitStatus.FAIL if inconsistent else LimitStatus.PASS,
        None,
        None,
        evidence_refs,
        1,
        reason=RiskErrorCode.LIMIT_FAILED if inconsistent else None,
    )


PortfolioViewProvider = Callable[[str], Mapping[str, Decimal] | None]
"""Injectable authoritative Portfolio exposure-view port.

Consumer port for the deferred Portfolio integration
(``feature``/``feature``, Phase 12): given an account
identity, returns the authoritative exposure-by-dimension mapping, or
``None`` when unavailable. Risk never implements the provider's business
logic here; it only calls an injected provider and fails closed to its own
snapshot-derived view.
"""


def _resolve_exposure_by_dimension(
    snapshot: PortfolioRiskSnapshot,
    portfolio_view_provider: PortfolioViewProvider | None,
) -> Mapping[str, Decimal]:
    """Resolve the authoritative exposure view or fail closed to Risk's own.

    Args:
        snapshot: Portfolio evidence carrying Risk's own exposure view.
        portfolio_view_provider: Optional injected authoritative Portfolio
            exposure-view port.

    Returns:
        The authoritative view when the provider is supplied and returns
        one; otherwise Risk's own snapshot-derived exposure view. Never an
        inferred or synthesized view.
    """
    if portfolio_view_provider is not None:
        view = portfolio_view_provider(snapshot.account_id)
        if view is not None:
            return view
    return snapshot.exposure_by_dimension


MarginViewProvider = Callable[[str], Mapping[str, Decimal] | None]
"""Injectable authoritative Portfolio margin/leverage-view port.

Consumer port for the deferred Portfolio integration (``feature``,
Phase 12 margin and buying power): given an account identity, returns a
mapping with optional ``margin_utilization``/``effective_leverage`` keys, or
``None`` when unavailable. Risk never implements the provider's business
logic here; it only calls an injected provider and fails closed to its own
static snapshot-derived checks — the check is never silently skipped.
"""


def _resolve_margin_view(
    snapshot: PortfolioRiskSnapshot,
    margin_view_provider: MarginViewProvider | None,
) -> tuple[Decimal | None, Decimal | None]:
    """Resolve authoritative margin utilization and leverage, or fail closed.

    Args:
        snapshot: Portfolio evidence carrying Risk's own static values.
        margin_view_provider: Optional injected authoritative Portfolio
            margin/leverage-view port.

    Returns:
        ``(margin_utilization, effective_leverage)``; each falls back
        independently to Risk's own snapshot value when the provider is
        absent or omits that key.
    """
    margin_utilization = snapshot.margin_utilization
    effective_leverage = snapshot.effective_leverage
    if margin_view_provider is not None:
        view = margin_view_provider(snapshot.account_id)
        if view is not None:
            margin_utilization = view.get("margin_utilization", margin_utilization)
            effective_leverage = view.get("effective_leverage", effective_leverage)
    return margin_utilization, effective_leverage


def _concentration_results(
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
    start_precedence: int,
    portfolio_view_provider: PortfolioViewProvider | None = None,
) -> tuple[RiskLimitResult, ...]:
    """Evaluate symbol then other-dimension concentration in stable key order.

    Args:
        snapshot: Immutable portfolio measurements.
        config: Active Risk policy.
        evidence_refs: Exact snapshot evidence references.
        start_precedence: First concentration precedence.
        portfolio_view_provider: Optional injected authoritative Portfolio
            exposure-view port (``feature``/``feature``);
            falls back to Risk's own snapshot exposure when absent.

    Returns:
        Ordered per-dimension concentration results.
    """
    logger.debug("Evaluating Policy concentration limits")
    exposure_by_dimension = _resolve_exposure_by_dimension(
        snapshot, portfolio_view_provider
    )
    symbols = sorted(key for key in exposure_by_dimension if key.startswith("symbol:"))
    others = sorted(
        key for key in exposure_by_dimension if not key.startswith("symbol:")
    )
    results: list[RiskLimitResult] = []
    for offset, key in enumerate((*symbols, *others)):
        default = (
            config.max_symbol_concentration
            if key.startswith("symbol:")
            else config.max_dimension_concentration
        )
        threshold = config.allocation_caps.get(key, default)
        observed = (
            Decimal(0)
            if snapshot.gross_exposure == 0
            else abs(exposure_by_dimension[key]) / snapshot.gross_exposure
        )
        results.append(
            _threshold_result(
                f"concentration:{key}",
                observed,
                threshold,
                evidence_refs,
                start_precedence + offset,
            )
        )
    return tuple(results)


@guard_risk_boundary(risk_level="medium", read_only=True)
def evaluate_portfolio_limits(
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    *,
    now: datetime,
    mandate: FirmMandate | None = None,
    portfolio_view_provider: PortfolioViewProvider | None = None,
    margin_view_provider: MarginViewProvider | None = None,
) -> tuple[RiskLimitResult, ...]:
    """Evaluate portfolio limits in the authoritative deterministic precedence.

    Args:
        snapshot: Immutable portfolio Risk measurements.
        config: Active validated Risk policy.
        now: Injected current UTC time.
        mandate: Optional verified firm mandate for account-specific limits.
        portfolio_view_provider: Optional injected authoritative Portfolio
            exposure-view port consumed by concentration checks
            (``feature``/``feature``, deferred integration);
            falls back to Risk's own snapshot exposure when absent.
        margin_view_provider: Optional injected authoritative Portfolio
            margin/leverage-view port (``feature``, deferred
            integration); falls back to Risk's own static snapshot checks
            when absent.

    Returns:
        Complete ordered limit results; the first failing item is primary.

    Raises:
        RiskDomainError: If required configuration or evaluation time is invalid.
    """
    logger.info("Evaluating deterministic portfolio Policy limits")
    try:
        checked_now = _utc(now)
        max_age = config.evidence_max_age_seconds["portfolio"]
        evidence_refs = tuple(snapshot.evidence_refs.values()) or (
            snapshot.snapshot_id,
        )
        if mandate is not None and (
            not mandate.verified or mandate.account_id != snapshot.account_id
        ):
            return (
                _result(
                    "mandate",
                    LimitStatus.BLOCKED,
                    None,
                    None,
                    evidence_refs,
                    0,
                    reason=RiskErrorCode.INVALID_RISK_CONFIG,
                    reference_basis="verified_firm_mandate",
                ),
            )
        daily_basis = (
            LossReferenceBasis(mandate.daily_loss.basis)
            if mandate is not None
            else config.daily_loss_basis
        )
        total_basis = (
            LossReferenceBasis.INITIAL_BALANCE
            if mandate is not None
            else config.total_loss_basis
        )
        daily_limit = mandate.daily_loss.value_absolute if mandate is not None else None
        daily_ratio = (
            mandate.daily_loss.value or config.max_daily_loss
            if mandate is not None
            else config.max_daily_loss
        )
        total_limit = None
        total_ratio = config.max_total_loss
        results = [
            _freshness_result(snapshot.as_of, checked_now, max_age, evidence_refs),
            _consistency_result(snapshot, config, evidence_refs),
            _loss_limit_result(
                "daily_loss",
                snapshot.daily_loss,
                daily_ratio,
                snapshot,
                daily_basis,
                evidence_refs,
                2,
                absolute_limit=daily_limit,
            ),
            _loss_limit_result(
                "total_loss",
                snapshot.total_loss,
                total_ratio,
                snapshot,
                total_basis,
                evidence_refs,
                3,
                absolute_limit=total_limit,
            ),
            _drawdown_result(
                snapshot,
                config,
                evidence_refs,
                4,
                mandate,
            ),
            _drawdown_state_result(snapshot, config, evidence_refs, 5),
        ]
        concentrations = _concentration_results(
            snapshot, config, evidence_refs, len(results), portfolio_view_provider
        )
        results.extend(concentrations)
        precedence = len(results)
        margin_utilization, effective_leverage = _resolve_margin_view(
            snapshot, margin_view_provider
        )
        results.extend(
            (
                _threshold_result(
                    "margin_utilization",
                    margin_utilization,
                    config.max_margin_utilization,
                    evidence_refs,
                    precedence,
                ),
                _threshold_result(
                    "effective_leverage",
                    effective_leverage,
                    config.max_effective_leverage,
                    evidence_refs,
                    precedence + 1,
                ),
                _threshold_result(
                    "historical_var",
                    None
                    if snapshot.historical_var is None or snapshot.equity <= 0
                    else snapshot.historical_var / snapshot.equity,
                    config.max_historical_var_ratio,
                    evidence_refs,
                    precedence + 2,
                ),
                _threshold_result(
                    "historical_cvar",
                    None
                    if snapshot.historical_cvar is None or snapshot.equity <= 0
                    else snapshot.historical_cvar / snapshot.equity,
                    config.max_historical_cvar_ratio,
                    evidence_refs,
                    precedence + 3,
                ),
                _threshold_result(
                    "correlation",
                    snapshot.portfolio_correlation,
                    config.max_correlation,
                    evidence_refs,
                    precedence + 4,
                ),
            )
        )
        return tuple(results)
    except RiskDomainError:
        logger.exception("Portfolio Policy limit evaluation failed closed")
        raise


RuleDirection = Literal["upper_bound", "lower_bound"]
"""Strictness direction for one named rule key.

``upper_bound`` rules (e.g. exposure/risk caps) tighten toward the minimum
across sources; ``lower_bound`` rules (e.g. minimum reward/risk) tighten
toward the maximum.
"""


@guard_risk_boundary(risk_level="medium", read_only=True)
def resolve_effective_rules(
    sources: Mapping[str, Mapping[str, Decimal]],
    directions: Mapping[str, RuleDirection],
) -> dict[str, Decimal]:
    """Resolve the effective rule set across sources via strictest-wins.

    Combines named rule sources (e.g. ``scenario``, ``account``,
    ``venue_instrument``, ``strategy``, ``simulator_default``) into one
    effective rule mapping. For every key present in at least one source,
    the resolved value is the strictest across every source that defines
    it — the minimum for an ``upper_bound`` rule, the maximum for a
    ``lower_bound`` rule. A key without a registered direction fails closed
    rather than guessing a strictness convention.

    Args:
        sources: Named rule-source mappings; a source may omit any key.
        directions: Registered strictness direction per rule key that
            appears in any source.

    Returns:
        Effective rule mapping containing every key present in any source.

    Raises:
        RiskDomainError: If a present key has no registered direction.
    """
    logger.info("Resolving effective Risk rules via strictest-wins")
    keys: set[str] = set()
    for source in sources.values():
        keys.update(source)
    resolved: dict[str, Decimal] = {}
    for key in sorted(keys):
        direction = directions.get(key)
        if direction is None:
            raise RiskDomainError(
                RiskErrorCode.INVALID_RISK_CONFIG,
                "effective rule key has no registered strictness direction",
            )
        values = [source[key] for source in sources.values() if key in source]
        resolved[key] = min(values) if direction == "upper_bound" else max(values)
    return resolved


ExpectancyProvider = Callable[[str], Decimal | None]
"""Injectable approved-expectancy-profile eligibility port.

Consumer port for the deferred Research integration
(``feature``/``feature``, Phase 11): given a strategy identity,
returns an eligible exactly-matched minimum reward/risk override, or
``None`` when no approved profile is eligible. Risk never implements the
provider's expectancy-eligibility logic here; an absent or ``None``
provider result falls back to the normal configured minimum reward/risk
gate — never an inferred approval.
"""


@guard_risk_boundary(risk_level="medium", read_only=True)
def evaluate_reward_risk_gate(
    strategy_id: str,
    reward_risk_ratio: Decimal,
    min_reward_risk_ratio: Decimal,
    evidence_refs: tuple[str, ...],
    *,
    expectancy_provider: ExpectancyProvider | None = None,
) -> RiskLimitResult:
    """Apply the minimum reward/risk gate, deferring to an eligible expectancy profile.

    Args:
        strategy_id: Identity used to look up an eligible expectancy
            profile.
        reward_risk_ratio: Planned reward/risk ratio (e.g. from
            :func:`app.services.risk.sizing.calculate_planned_risk_reward`).
        min_reward_risk_ratio: Configured baseline minimum ratio.
        evidence_refs: Exact evidence references.
        expectancy_provider: Optional injected approved-expectancy-profile
            eligibility port (``feature``/``feature``, deferred
            integration).

    Returns:
        Ordered reward/risk gate result.
    """
    logger.info("Evaluating Risk minimum reward/risk gate: %s", strategy_id)
    effective_min = min_reward_risk_ratio
    if expectancy_provider is not None:
        override = expectancy_provider(strategy_id)
        if override is not None:
            effective_min = override
    status = (
        LimitStatus.PASS if reward_risk_ratio >= effective_min else LimitStatus.FAIL
    )
    return _result(
        "reward_risk_ratio",
        status,
        reward_risk_ratio,
        effective_min,
        evidence_refs,
        0,
        reason=RiskErrorCode.LIMIT_FAILED if status is LimitStatus.FAIL else None,
    )


@guard_risk_boundary(risk_level="medium", read_only=True)
def evaluate_single_day_profit_share(
    snapshot: PortfolioRiskSnapshot,
    mandate: FirmMandate,
    *,
    now: datetime,
) -> RiskLimitResult:
    """Project today's best-case share of cumulative profit.

    Args:
        snapshot: Snapshot carrying cumulative, current-day, and proposal data.
        mandate: Verified account mandate containing the consistency rule.
        now: Injected current UTC time.

    Returns:
        A deterministic consistency limit result.

    Raises:
        RiskDomainError: If the mandate or required profit evidence is invalid.
    """
    logger.info("Evaluating forward single-day profit-share projection")
    checked_now = _utc(now)
    del checked_now
    evidence_refs = tuple(snapshot.evidence_refs.values()) or (snapshot.snapshot_id,)
    if not mandate.verified or mandate.account_id != snapshot.account_id:
        return _result(
            "single_day_profit_share",
            LimitStatus.BLOCKED,
            None,
            None,
            evidence_refs,
            0,
            reason=RiskErrorCode.INVALID_RISK_CONFIG,
            reference_basis="verified_firm_mandate",
        )
    rule = mandate.consistency_rule
    if rule is None or mandate.phase not in rule.applies_in_phase:
        return _result(
            "single_day_profit_share",
            LimitStatus.PASS,
            None,
            None,
            evidence_refs,
            0,
            reference_basis="not_applicable",
        )
    if snapshot.cumulative_profit is None or snapshot.current_day_profit is None:
        return _result(
            "single_day_profit_share",
            LimitStatus.NEEDS_MORE_EVIDENCE,
            None,
            rule.value,
            evidence_refs,
            0,
            reason=RiskErrorCode.MISSING_EVIDENCE,
            reference_basis="cumulative_profit",
        )
    projected_day = snapshot.proposal_best_case_profit or snapshot.current_day_profit
    projected_day = max(Decimal(0), projected_day)
    cumulative = max(Decimal(0), snapshot.cumulative_profit)
    denominator = cumulative + projected_day
    if denominator <= 0:
        return _result(
            "single_day_profit_share",
            LimitStatus.NEEDS_MORE_EVIDENCE,
            None,
            rule.value,
            evidence_refs,
            0,
            reason=RiskErrorCode.MISSING_EVIDENCE,
            reference_basis="positive_cumulative_profit",
        )
    share = projected_day / denominator
    status = LimitStatus.FAIL if share > rule.value else LimitStatus.PASS
    allowed_day_profit = (rule.value * cumulative) / (Decimal(1) - rule.value)
    return _result(
        "single_day_profit_share",
        status,
        share,
        rule.value,
        evidence_refs,
        0,
        reason=RiskErrorCode.LIMIT_FAILED if status is LimitStatus.FAIL else None,
        headroom=allowed_day_profit - projected_day,
        reference_basis="cumulative_profit_projection",
    )


def _calendar_missing_result(
    mode: str,
    evidence_refs: tuple[str, ...],
    precedence: int,
) -> RiskLimitResult:
    """Apply the configured missing-calendar mode.

    Args:
        mode: Configured missing-evidence behavior.
        evidence_refs: Exact market evidence references.
        precedence: Stable evaluation order.

    Returns:
        Configured calendar result.
    """
    logger.debug("Applying missing calendar Policy mode")
    status = {
        "ignore": LimitStatus.PASS,
        "warn": LimitStatus.WARN,
        "needs_more_evidence": LimitStatus.NEEDS_MORE_EVIDENCE,
        "block": LimitStatus.BLOCKED,
    }[mode]
    reason = (
        RiskErrorCode.MISSING_EVIDENCE
        if status is LimitStatus.NEEDS_MORE_EVIDENCE
        else RiskErrorCode.POLICY_BLOCKED
        if status is LimitStatus.BLOCKED
        else None
    )
    return _result(
        "calendar",
        status,
        None,
        None,
        evidence_refs,
        precedence,
        reason=reason,
    )


def _session_result(
    evidence: _MarketContextEvidenceView,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate exact timezone and normalized session state.

    Args:
        evidence: Supplied Data-owned context.
        config: Active Risk policy.
        evidence_refs: Exact evidence references.

    Returns:
        Ordered session result.
    """
    logger.debug("Evaluating normalized market session Policy")
    if config.session_timezone is None:
        return _result("session", LimitStatus.PASS, None, None, evidence_refs, 1)
    try:
        ZoneInfo(evidence.timezone)
    except ZoneInfoNotFoundError:
        return _result(
            "session",
            LimitStatus.BLOCKED,
            None,
            None,
            evidence_refs,
            1,
            reason=RiskErrorCode.POLICY_BLOCKED,
        )
    if evidence.session_state is None or evidence.session_state == "unknown":
        return _result(
            "session",
            LimitStatus.NEEDS_MORE_EVIDENCE,
            None,
            None,
            evidence_refs,
            1,
            reason=RiskErrorCode.MISSING_EVIDENCE,
        )
    allowed = (
        evidence.timezone == config.session_timezone
        and evidence.session_state in config.allowed_session_states
    )
    return _result(
        "session",
        LimitStatus.PASS if allowed else LimitStatus.BLOCKED,
        None,
        None,
        evidence_refs,
        1,
        reason=None if allowed else RiskErrorCode.POLICY_BLOCKED,
    )


def _calendar_result(
    evidence: _MarketContextEvidenceView,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate normalized calendar state and blackout provenance.

    Args:
        evidence: Supplied Data-owned context.
        config: Active Risk policy.
        evidence_refs: Exact evidence references.

    Returns:
        Ordered calendar result.
    """
    logger.debug("Evaluating normalized market calendar Policy")
    mode = config.missing_calendar_mode
    if mode is None:
        return _result("calendar", LimitStatus.PASS, None, None, evidence_refs, 2)
    provenance_matches = evidence.provenance.get("blackout_before_minutes") == str(
        config.news_blackout_before_minutes
    ) and evidence.provenance.get("blackout_after_minutes") == str(
        config.news_blackout_after_minutes
    )
    if (
        evidence.calendar_state is None
        or evidence.calendar_state == "unknown"
        or not provenance_matches
    ):
        return _calendar_missing_result(mode, evidence_refs, 2)
    blocked = evidence.calendar_state in config.blocked_calendar_states
    return _result(
        "calendar",
        LimitStatus.BLOCKED if blocked else LimitStatus.PASS,
        None,
        None,
        evidence_refs,
        2,
        reason=RiskErrorCode.POLICY_BLOCKED if blocked else None,
    )


def _spread_result(
    evidence: _MarketContextEvidenceView,
    caps: Mapping[str, Decimal],
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate an exact-unit spread cap without conversion.

    Args:
        evidence: Supplied Data-owned context.
        caps: Exact configured spread caps.
        evidence_refs: Exact evidence references.

    Returns:
        Ordered spread result.
    """
    logger.debug("Evaluating exact-unit market spread Policy")
    if evidence.spread_unit is None:
        return _result("spread", LimitStatus.PASS, None, None, evidence_refs, 3)
    threshold = caps.get(
        f"{evidence.symbol}@{evidence.spread_unit}",
        caps.get(f"*@{evidence.spread_unit}"),
    )
    return _threshold_result("spread", evidence.spread, threshold, evidence_refs, 3)


@guard_risk_boundary(risk_level="medium", read_only=True)
def evaluate_market_context(
    evidence: _MarketContextEvidenceView,
    config: RiskConfig,
    *,
    now: datetime,
) -> tuple[RiskLimitResult, ...]:
    """Evaluate only supplied V1 market context in deterministic precedence.

    Args:
        evidence: Data-owned immutable market context.
        config: Active validated Risk policy.
        now: Injected current UTC time.

    Returns:
        Ordered freshness, session, calendar, spread, and liquidity results.

    Raises:
        RiskDomainError: If evidence is incompatible, stale, or policy is invalid.
    """
    logger.info("Evaluating supplied market-context Policy limits")
    checked_now = _utc(now)
    unwrap_risk_response(
        validate_market_context_evidence(evidence, now=checked_now),
        operation="validate_market_context_evidence",
    )
    try:
        max_age = config.evidence_max_age_seconds["market"]
        evidence_refs = (evidence.request_id,)
        liquidity_status = (
            LimitStatus.NEEDS_MORE_EVIDENCE
            if evidence.liquidity is None
            else LimitStatus.PASS
        )
        return (
            _freshness_result(evidence.as_of, checked_now, max_age, evidence_refs),
            _session_result(evidence, config, evidence_refs),
            _calendar_result(evidence, config, evidence_refs),
            _spread_result(evidence, config.max_spread, evidence_refs),
            _result(
                "liquidity_availability",
                liquidity_status,
                evidence.liquidity,
                None,
                evidence_refs,
                4,
                reason=(
                    RiskErrorCode.MISSING_EVIDENCE
                    if liquidity_status is LimitStatus.NEEDS_MORE_EVIDENCE
                    else None
                ),
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        logger.exception("Market-context Policy configuration is incomplete")
        raise RiskDomainError(
            RiskErrorCode.INVALID_RISK_CONFIG,
            "market-context policy configuration invalid",
        ) from error


__all__ = ["evaluate_market_context", "evaluate_portfolio_limits"]
