"""Portfolio-owned risk health evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal


def build_portfolio_risk_health(
    values: Sequence[Decimal],
    *,
    confidence: Decimal,
    model: str,
    window: int,
    stress_losses: Mapping[str, Decimal],
    high_water_mark: Decimal,
) -> Mapping[str, object]:
    """Build explicit drawdown, VaR/CVaR, and stress evidence.

    Args:
        values: Sequence of portfolio value observations.
        confidence: Confidence level for VaR/CVaR calculation.
        model: Model name string.
        window: Historical window size.
        stress_losses: Mapping of scenario names to stress losses.
        high_water_mark: High-water mark value for drawdown calculation.

    Returns:
        Versioned Portfolio risk-health evidence.
    """
    if not values:
        return {
            "schema": "PortfolioRiskHealth",
            "version": "v1",
            "status": "unknown",
            "reason": "NO_OBSERVATIONS",
        }
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((Decimal(1) - confidence) * len(ordered))))
    var = ordered[index]
    tail = ordered[: index + 1]
    current = values[-1]
    drawdown = current - high_water_mark
    return {
        "schema": "PortfolioRiskHealth",
        "version": "v1",
        "status": "known",
        "model": model,
        "confidence": str(confidence),
        "window": window,
        "observations": len(values),
        "drawdown": str(drawdown),
        "var": str(var),
        "cvar": str(sum(tail, Decimal(0)) / len(tail)),
        "stress": {key: str(value) for key, value in stress_losses.items()},
    }
