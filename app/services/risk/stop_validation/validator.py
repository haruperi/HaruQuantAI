"""Deterministic stop-loss validity, distance, loss, and widening checks."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from app.composition.logging import get_logger
from app.services.risk.contracts import LimitStatus, RiskErrorCode, RiskLimitResult
from app.services.risk.contracts.responses import guard_risk_boundary
from app.services.risk.stop_validation.models import parse_stop_validation

logger = get_logger(__name__)


def _limit(
    limit_id: str,
    status: LimitStatus,
    precedence: int,
    evidence_refs: tuple[str, ...],
    *,
    observed: Decimal | None = None,
    threshold: Decimal | None = None,
    reason: RiskErrorCode | None = None,
) -> RiskLimitResult:
    """Build one ordered stop-validation check.

    Args:
        limit_id: Stable check identity.
        status: Deterministic result status.
        precedence: Fixed order index.
        evidence_refs: Exact evidence references.
        observed: Optional observed value.
        threshold: Optional configured threshold.
        reason: Required stable reason for failing states.

    Returns:
        Immutable ordered check.
    """
    logger.debug("Building one ordered Risk stop-validation check: %s", limit_id)
    return RiskLimitResult(
        limit_id=limit_id,
        status=status,
        observed_value=observed,
        threshold_value=threshold,
        reason_code=reason,
        evidence_refs=evidence_refs,
        precedence=precedence,
    )


@guard_risk_boundary(risk_level="medium", read_only=True)
def validate_stop_loss(
    validation: Mapping[str, object],
) -> tuple[RiskLimitResult, ...]:
    """Evaluate side, tick, invalidation, noise, loss, and widening checks.

    Args:
        validation: JSON-safe ``StopValidation v1`` mapping built by
            :func:`build_stop_validation`.

    Returns:
        Ordered results: ``stop_side``, ``stop_tick``,
        ``stop_invalidation_distance``, ``stop_noise_distance``,
        ``stop_projected_loss`` (informational), and
        ``stop_widening_permission``.

    Raises:
        RiskDomainError: If the supplied mapping fails ``StopValidation v1``
            validation.
    """
    logger.info("Validating stop-loss placement")
    parsed = parse_stop_validation(validation)
    symbol = str(parsed["symbol"])
    side = str(parsed["side"])
    entry_price = Decimal(str(parsed["entry_price"]))
    stop_price = Decimal(str(parsed["stop_price"]))
    tick_size = Decimal(str(parsed["tick_size"]))
    min_stop_distance = Decimal(str(parsed["min_stop_distance"]))
    contract_value = Decimal(str(parsed["contract_value"]))
    quantity = Decimal(str(parsed["quantity"]))
    invalidation_price = (
        Decimal(str(parsed["invalidation_price"]))
        if parsed.get("invalidation_price") is not None
        else None
    )
    previous_stop_price = (
        Decimal(str(parsed["previous_stop_price"]))
        if parsed.get("previous_stop_price") is not None
        else None
    )
    allow_widening = bool(parsed["allow_widening"])
    evidence_refs = (symbol,)

    correct_side = (
        stop_price < entry_price if side == "BUY" else stop_price > entry_price
    )
    results = [
        _limit(
            "stop_side",
            LimitStatus.PASS if correct_side else LimitStatus.FAIL,
            0,
            evidence_refs,
            reason=None if correct_side else RiskErrorCode.LIMIT_FAILED,
        )
    ]

    tick_remainder = abs(stop_price - entry_price) % tick_size
    tick_valid = tick_remainder == 0
    results.append(
        _limit(
            "stop_tick",
            LimitStatus.PASS if tick_valid else LimitStatus.FAIL,
            1,
            evidence_refs,
            observed=tick_remainder,
            threshold=tick_size,
            reason=None if tick_valid else RiskErrorCode.LIMIT_FAILED,
        )
    )

    stop_distance = abs(entry_price - stop_price)
    if invalidation_price is None:
        results.append(
            _limit("stop_invalidation_distance", LimitStatus.PASS, 2, evidence_refs)
        )
    else:
        invalidation_distance = abs(entry_price - invalidation_price)
        beyond_invalidation = stop_distance >= invalidation_distance
        results.append(
            _limit(
                "stop_invalidation_distance",
                LimitStatus.PASS if beyond_invalidation else LimitStatus.FAIL,
                2,
                evidence_refs,
                observed=stop_distance,
                threshold=invalidation_distance,
                reason=None if beyond_invalidation else RiskErrorCode.LIMIT_FAILED,
            )
        )

    noise_ok = stop_distance >= min_stop_distance
    results.append(
        _limit(
            "stop_noise_distance",
            LimitStatus.PASS if noise_ok else LimitStatus.FAIL,
            3,
            evidence_refs,
            observed=stop_distance,
            threshold=min_stop_distance,
            reason=None if noise_ok else RiskErrorCode.LIMIT_FAILED,
        )
    )

    projected_loss = stop_distance * contract_value * quantity
    results.append(
        _limit(
            "stop_projected_loss",
            LimitStatus.PASS,
            4,
            evidence_refs,
            observed=projected_loss,
        )
    )

    if previous_stop_price is None or allow_widening:
        results.append(
            _limit("stop_widening_permission", LimitStatus.PASS, 5, evidence_refs)
        )
    else:
        reduces_risk = (
            stop_price >= previous_stop_price
            if side == "BUY"
            else stop_price <= previous_stop_price
        )
        results.append(
            _limit(
                "stop_widening_permission",
                LimitStatus.PASS if reduces_risk else LimitStatus.FAIL,
                5,
                evidence_refs,
                observed=stop_price,
                threshold=previous_stop_price,
                reason=None if reduces_risk else RiskErrorCode.LIMIT_FAILED,
            )
        )

    return tuple(results)


__all__ = ["validate_stop_loss"]
