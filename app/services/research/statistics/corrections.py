"""Multiple-comparison corrections for Research hypotheses."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from app.utils import logger
from app.utils.errors import ValidationError


def _p_values(values: Sequence[float], level: float) -> NDArray[np.float64]:
    """Validate p-values and a unit-interval control level.

    Args:
        values: Candidate p-values.
        level: FDR or family-wise level.

    Returns:
        Float64 p-value array.

    Raises:
        ValidationError: If values or level are invalid.
    """
    logger.debug("Validating Research multiple-comparison inputs")
    output = np.asarray(values, dtype="float64")
    if (
        output.size == 0
        or not np.isfinite(output).all()
        or bool(((output < 0) | (output > 1)).any())
    ):
        raise ValidationError("RES_INPUT_INVALID", "INVALID_P_VALUES")
    if not 0.0 < level < 1.0:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_CONTROL_LEVEL")
    return output


def benjamini_hochberg(p_values: Sequence[float], *, q: float) -> NDArray[np.float64]:
    """Return BH-adjusted p-values in original order.

    Args:
        p_values: Finite p-values in original order.
        q: FDR control level used for validation and downstream decisions.

    Returns:
        Monotone BH-adjusted p-values restored to original order.

    Raises:
        ValidationError: If p-values or q are invalid.
    """
    logger.info("Applying Benjamini-Hochberg Research correction")
    values = _p_values(p_values, q)
    order = np.argsort(values)
    ranked = values[order]
    adjusted = np.minimum.accumulate(
        (ranked * values.size / np.arange(1, values.size + 1))[::-1]
    )[::-1]
    output = np.empty_like(adjusted)
    output[order] = np.minimum(adjusted, 1.0)
    return output


def holm_bonferroni(p_values: Sequence[float], *, alpha: float) -> NDArray[np.float64]:
    """Return Holm-adjusted p-values in original order.

    Args:
        p_values: Finite p-values in original order.
        alpha: Family-wise control level used for validation and decisions.

    Returns:
        Holm-adjusted p-values restored to original order.

    Raises:
        ValidationError: If p-values or alpha are invalid.
    """
    logger.info("Applying Holm-Bonferroni Research correction")
    values = _p_values(p_values, alpha)
    order = np.argsort(values)
    ranked = values[order]
    adjusted = np.maximum.accumulate((values.size - np.arange(values.size)) * ranked)
    output = np.empty_like(adjusted)
    output[order] = np.minimum(adjusted, 1.0)
    return output


__all__ = ("benjamini_hochberg", "holm_bonferroni")
