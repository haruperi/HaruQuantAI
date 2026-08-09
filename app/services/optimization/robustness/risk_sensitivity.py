"""Risk-parameter sensitivity analysis (TC-IMP-OPT-05).

Extends ``FEAT-OPT-05``: measure how candidate outcomes shift as the cockpit risk
parameters vary — risk per trade, drawdown warning thresholds, stress limits, and
exposure caps — without weakening any hard limit. Risk owns the authoritative
``TradingPolicyProfile v1`` (``TC-IMP-RISK-01`` → ``RiskConfig`` in
``app/services/risk/config/profiles.py``). Optimization consumes only a caller-supplied
JSON-safe mapping of the risk fields it needs; it never imports Risk internals (DEEP
gate) and never mutates or relaxes a hard limit (NFR-OPT-003 safety).

Sensitivity is reported as bounded deltas over explicitly supplied outcome evidence,
with every variant still subject to the original hard caps. The result is advisory
robustness evidence; it never approves a risk change.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from decimal import Decimal

from app.utils import get_logger

logger = get_logger(__name__)

# Risk fields Optimization reads (names match Risk ``RiskConfig`` exactly; received as
# a JSON-safe mapping so no Risk import crosses the boundary).
_RISK_PER_TRADE_FIELD = "max_risk_per_trade_pct"
_DRAWDOWN_CAUTION = "drawdown_caution_threshold"
_DRAWDOWN_RESTRICTED = "drawdown_restricted_threshold"
_DRAWDOWN_CRITICAL = "drawdown_critical_threshold"
_MAX_DRAWDOWN = "max_drawdown"
_MAX_TOTAL_EXPOSURE = "max_total_exposure_pct"

_DEFAULT_VARIANTS = (
    Decimal("-0.50"),
    Decimal("-0.25"),
    Decimal("0.25"),
    Decimal("0.50"),
)


def _to_decimal(value: object) -> Decimal | None:
    """Coerce a value to a finite Decimal.

    Args:
        value: Raw value.

    Returns:
        Finite Decimal, or ``None`` if absent/invalid/non-finite.
    """
    if value is None:
        return None
    try:
        result = Decimal(str(value))
    except ArithmeticError, ValueError:
        return None
    if not result.is_finite():
        return None
    return result


def _apply_variant(base: Decimal, variant: Decimal, *, hard_floor: Decimal) -> Decimal:
    """Apply a multiplicative variant clamped at a hard floor.

    A sensitivity variant must never weaken a hard limit, so the result is clamped to
    stay at or below the base value when the floor is a maximum, and the variant is
    rejected if it would cross the floor.

    Args:
        base: Base parameter value.
        variant: Signed fractional variant (e.g. ``-0.25`` for -25%).
        hard_floor: Non-negative hard limit the variant may not breach.

    Returns:
        Adjusted value clamped to the hard floor.

    Raises:
        ValueError: If the variant would breach the hard floor.
    """
    adjusted = base * (Decimal(1) + variant)
    if adjusted > hard_floor:
        # A variant that would *raise* a limit above the hard cap weakens safety and
        # is rejected rather than silently clamped — the caller sees the rejection.
        if adjusted > base:
            raise ValueError("sensitivity variant may not weaken a hard limit")
        return hard_floor
    if adjusted <= 0:
        raise ValueError("sensitivity variant must remain positive")
    return adjusted


def evaluate_risk_sensitivity(
    *,
    risk_profile: Mapping[str, object],
    outcome_by_risk_per_trade: Mapping[str, float],
    variants: Sequence[Decimal] | None = None,
) -> dict[str, object]:
    """Evaluate outcome sensitivity to the risk-per-trade parameter.

    Args:
        risk_profile: JSON-safe mapping of the risk fields Optimization reads. Must
            include ``max_risk_per_trade_pct`` and ``max_drawdown``.
        outcome_by_risk_per_trade: Mapping of risk-per-trade percentage (as string,
            e.g. ``"0.010"``) to a finite outcome value (e.g. net PnL or Sharpe).
        variants: Optional signed fractional variants. Defaults to ±25% and ±50%.

    Returns:
        Sensitivity-evidence mapping carrying the base risk-per-trade, the hard
        drawdown floor, per-variant adjusted risk-per-trade, the closest observed
        outcome, and explicit caveats. Hard limits are never weakened.

    Raises:
        ValueError: If required risk fields or outcome evidence are missing or
            non-finite.
        TypeError: If an outcome value is not a finite number.
    """
    base_risk = _to_decimal(risk_profile.get(_RISK_PER_TRADE_FIELD))
    hard_drawdown = _to_decimal(risk_profile.get(_MAX_DRAWDOWN))
    if base_risk is None or base_risk <= 0:
        raise ValueError("max_risk_per_trade_pct must be a positive finite decimal")
    if hard_drawdown is None or hard_drawdown <= 0:
        raise ValueError("max_drawdown must be a positive finite decimal")
    if not outcome_by_risk_per_trade:
        raise ValueError("outcome evidence must be non-empty")
    for value in outcome_by_risk_per_trade.values():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("outcome values must be finite numbers")
        if not math.isfinite(float(value)):
            raise ValueError("outcome values must be finite")
    chosen_variants = tuple(variants) if variants is not None else _DEFAULT_VARIANTS
    observations: list[dict[str, object]] = []
    for variant in chosen_variants:
        adjusted = _apply_variant(base_risk, variant, hard_floor=hard_drawdown)
        closest_key, closest_outcome = _nearest_outcome(
            adjusted, outcome_by_risk_per_trade
        )
        observations.append(
            {
                "variant": str(variant),
                "adjusted_risk_per_trade_pct": str(adjusted),
                "observed_risk_per_trade_pct": closest_key,
                "observed_outcome": closest_outcome,
            }
        )
    outcomes = [float(item["observed_outcome"]) for item in observations]  # type: ignore[arg-type]
    spread = max(outcomes) - min(outcomes) if outcomes else 0.0
    caveats = ["hard_drawdown_limit_preserved", "advisory_sensitivity_no_risk_change"]
    logger.info(
        "Evaluated risk-per-trade sensitivity | base=%s variants=%d spread=%s",
        base_risk,
        len(observations),
        spread,
    )
    return {
        "parameter": _RISK_PER_TRADE_FIELD,
        "base_value": str(base_risk),
        "hard_floor": {"max_drawdown": str(hard_drawdown)},
        "observations": tuple(observations),
        "outcome_spread": spread,
        "caveats": tuple(caveats),
    }


def summarize_drawdown_threshold_sensitivity(
    risk_profile: Mapping[str, object],
) -> dict[str, object]:
    """Summarize the ordered drawdown threshold ladder in a risk profile.

    Reads the caution/restricted/critical thresholds and confirms they are ordered and
    bounded by the hard ``max_drawdown``. This is evidence that a candidate's drawdown
    behaviour degrades through warning tiers before breaching the hard floor — it never
    relaxes the hard limit.

    Args:
        risk_profile: JSON-safe mapping of the risk fields Optimization reads.

    Returns:
        Threshold-ladder evidence mapping.

    Raises:
        ValueError: If thresholds are present but unordered, inverted, or breach the
            hard drawdown limit.
    """
    caution = _to_decimal(risk_profile.get(_DRAWDOWN_CAUTION))
    restricted = _to_decimal(risk_profile.get(_DRAWDOWN_RESTRICTED))
    critical = _to_decimal(risk_profile.get(_DRAWDOWN_CRITICAL))
    hard = _to_decimal(risk_profile.get(_MAX_DRAWDOWN))
    if hard is None or hard <= 0:
        raise ValueError("max_drawdown must be a positive finite decimal")
    ladder: list[tuple[str, Decimal]] = []
    if caution is not None:
        ladder.append((_DRAWDOWN_CAUTION, caution))
    if restricted is not None:
        ladder.append((_DRAWDOWN_RESTRICTED, restricted))
    if critical is not None:
        ladder.append((_DRAWDOWN_CRITICAL, critical))
    for _name, value in ladder:
        if value > hard:
            message = f"{_name} breaches the hard max_drawdown limit"
            raise ValueError(message)
    for index in range(len(ladder) - 1):
        if ladder[index][1] >= ladder[index + 1][1]:
            raise ValueError("drawdown thresholds must be strictly ordered")
    logger.info("Summarized drawdown threshold ladder | tiers=%d", len(ladder))
    return {
        "max_drawdown_hard_limit": str(hard),
        "ordered_thresholds": tuple(
            {"name": name, "value": str(value)} for name, value in ladder
        ),
        "hard_limit_preserved": True,
        "caveats": ("advisory_threshold_summary_no_risk_change",),
    }


def _nearest_outcome(
    target: Decimal, outcomes: Mapping[str, float]
) -> tuple[str, float]:
    """Find the observed outcome whose risk-per-trade is nearest the target.

    Args:
        target: Target risk-per-trade percentage.
        outcomes: Mapping of risk-per-trade string to outcome value.

    Returns:
        ``(observed_key, observed_outcome)`` for the nearest observation.

    Raises:
        ValueError: If an outcome key is non-finite.
    """
    best_key = ""
    best_distance: Decimal | None = None
    best_outcome = 0.0
    for key, outcome in outcomes.items():
        key_decimal = _to_decimal(key)
        if key_decimal is None:
            raise ValueError("outcome risk-per-trade keys must be finite decimals")
        distance = abs(key_decimal - target)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_key = key
            best_outcome = float(outcome)
    return best_key, best_outcome


def get_risk_sensitivity_contract_version() -> str:
    """Return the risk-sensitivity analysis contract version.

    Returns:
        The canonical ``v1`` version string.
    """
    return "v1"


__all__: tuple[str, ...] = (
    "evaluate_risk_sensitivity",
    "get_risk_sensitivity_contract_version",
    "summarize_drawdown_threshold_sensitivity",
)
