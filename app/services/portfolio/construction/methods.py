"""Approved deterministic Portfolio construction methods."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import TYPE_CHECKING

from app.services.portfolio.exceptions import PortfolioError
from app.utils import logger

if TYPE_CHECKING:
    from app.services.portfolio.contracts import FixedWeightInput

type WeightRow = tuple[str, Decimal, Decimal]


def _normalize(
    raw: Sequence[tuple[str, Decimal]],
    *,
    tolerance: Decimal,
    minimum: Decimal,
    maximum: Decimal,
) -> tuple[tuple[str, Decimal], ...]:
    """Normalize positive ordered values to an exact bounded unit total.

    Args:
        raw: Ordered component and raw value pairs.
        tolerance: Explicit accepted unit-total variance.
        minimum: Inclusive normalized weight floor.
        maximum: Inclusive normalized weight ceiling.

    Returns:
        Ordered normalized values totaling exactly one.

    Raises:
        PortfolioError: If values, total, or bounds are invalid.
    """
    logger.debug("Normalizing deterministic Portfolio weights")
    if not raw or tuple(item[0] for item in raw) != tuple(
        sorted(item[0] for item in raw)
    ):
        raise PortfolioError("PORT_WEIGHT_INVALID", "ORDER_OR_EMPTY")
    if any(not value.is_finite() or value < 0 for _, value in raw):
        raise PortfolioError("PORT_WEIGHT_INVALID", "NONFINITE_OR_NEGATIVE")
    total = sum((value for _, value in raw), Decimal(0))
    if total <= 0:
        raise PortfolioError("PORT_WEIGHT_INVALID", "ZERO_TOTAL")
    with localcontext() as context:
        context.prec = 50
        normalized = [(component_id, value / total) for component_id, value in raw[:-1]]
        last_value = Decimal(1) - sum(
            (value for _, value in normalized),
            Decimal(0),
        )
        normalized.append((raw[-1][0], last_value))
    if any(value < minimum or value > maximum for _, value in normalized):
        raise PortfolioError("PORT_WEIGHT_INVALID", "BOUND")
    if abs(total - Decimal(1)) > tolerance and all(
        value <= Decimal(1) for _, value in raw
    ):
        raise PortfolioError("PORT_WEIGHT_INVALID", "TOTAL")
    return tuple(normalized)


def fixed_weights(
    values: Sequence[FixedWeightInput],
    *,
    tolerance: Decimal,
    minimum: Decimal,
    maximum: Decimal,
) -> tuple[WeightRow, ...]:
    """Validate and return explicit fixed capital and proposed Risk weights.

    Args:
        values: Ordered explicit component weights.
        tolerance: Explicit accepted unit-total variance.
        minimum: Inclusive weight floor.
        maximum: Inclusive weight ceiling.

    Returns:
        Ordered exact fixed weight rows.

    Raises:
        PortfolioError: If either weight basis is invalid.
    """
    logger.info("Calculating fixed Portfolio weights")
    capital = _normalize(
        tuple((item.component_id, item.capital_weight) for item in values),
        tolerance=tolerance,
        minimum=minimum,
        maximum=maximum,
    )
    proposed = _normalize(
        tuple((item.component_id, item.proposed_risk_budget_weight) for item in values),
        tolerance=tolerance,
        minimum=minimum,
        maximum=maximum,
    )
    return tuple(
        (component_id, capital_weight, proposed[index][1])
        for index, (component_id, capital_weight) in enumerate(capital)
    )


def equal_weights(
    component_ids: Sequence[str],
    *,
    minimum: Decimal,
    maximum: Decimal,
) -> tuple[WeightRow, ...]:
    """Return deterministic equal capital and proposed Risk weights.

    Args:
        component_ids: Ordered unique component identities.
        minimum: Inclusive weight floor.
        maximum: Inclusive weight ceiling.

    Returns:
        Ordered equal-basis weight rows totaling exactly one.

    Raises:
        PortfolioError: If component identities or bounds are invalid.
    """
    logger.info("Calculating equal Portfolio weights")
    if not component_ids or len(set(component_ids)) != len(component_ids):
        raise PortfolioError("PORT_WEIGHT_INVALID", "COMPONENT_SET")
    raw = tuple((component_id, Decimal(1)) for component_id in component_ids)
    normalized = _normalize(
        raw,
        tolerance=Decimal(len(component_ids)),
        minimum=minimum,
        maximum=maximum,
    )
    return tuple((component_id, value, value) for component_id, value in normalized)


def inverse_volatility_weights(
    volatilities: Mapping[str, Decimal],
    observations: Mapping[str, int],
    *,
    minimum_observations: int,
    minimum: Decimal,
    maximum: Decimal,
) -> tuple[WeightRow, ...]:
    """Return deterministic weights from resolved Analytics volatility only.

    Args:
        volatilities: Component-keyed positive finite volatility values.
        observations: Component-keyed Analytics sample counts.
        minimum_observations: Explicit minimum accepted sample count.
        minimum: Inclusive weight floor.
        maximum: Inclusive weight ceiling.

    Returns:
        Ordered inverse-volatility capital and proposed Risk weight rows.

    Raises:
        PortfolioError: If evidence sets, values, counts, or bounds are invalid.
    """
    logger.info("Calculating inverse-volatility Portfolio weights")
    if set(volatilities) != set(observations) or not volatilities:
        raise PortfolioError("PORT_EVIDENCE_INVALID", "VOLATILITY_SET")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < minimum_observations
        for value in observations.values()
    ):
        raise PortfolioError("PORT_EVIDENCE_INVALID", "OBSERVATIONS")
    ordered = tuple(sorted(volatilities.items()))
    if any(not value.is_finite() or value <= 0 for _, value in ordered):
        raise PortfolioError("PORT_EVIDENCE_INVALID", "VOLATILITY")
    with localcontext() as context:
        context.prec = 50
        raw = tuple(
            (component_id, Decimal(1) / value) for component_id, value in ordered
        )
    normalized = _normalize(
        raw,
        tolerance=sum((value for _, value in raw), Decimal(0)),
        minimum=minimum,
        maximum=maximum,
    )
    return tuple((component_id, value, value) for component_id, value in normalized)


__all__: tuple[str, ...] = (
    "WeightRow",
    "equal_weights",
    "fixed_weights",
    "inverse_volatility_weights",
)
