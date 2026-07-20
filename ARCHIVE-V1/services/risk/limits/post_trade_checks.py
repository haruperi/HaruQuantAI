"""Post-trade governance checks for existing portfolio state."""

from __future__ import annotations

from .events import PolicyDecision
from .models import CircuitBreakerState, RiskPolicy
from .pre_trade_checks import evaluate_pre_trade


def evaluate_post_trade(
    *,
    equity: float,
    portfolio_var: float,
    portfolio_es: float,
    margin_used: float | None,
    rc_map: dict[str, float] | None,
    currency_exposure: dict[str, float] | None,
    gross_portfolio_notional: float | None,
    cluster_metrics: dict[str, dict[str, float]] | None,
    policy: RiskPolicy,
    peak_equity: float | None = None,
    breaker_state: CircuitBreakerState | None = None,
) -> PolicyDecision:
    """Evaluate current portfolio compliance without a new candidate trade."""
    return evaluate_pre_trade(
        equity=equity,
        current_var=portfolio_var,
        new_var=portfolio_var,
        delta_var=0.0,
        current_es=portfolio_es,
        new_es=portfolio_es,
        delta_es=0.0,
        current_margin_used=margin_used,
        new_margin_used=margin_used,
        rc_map_new=rc_map,
        currency_exposure=currency_exposure,
        gross_portfolio_notional=gross_portfolio_notional,
        cluster_metrics=cluster_metrics,
        policy=policy,
        peak_equity=peak_equity,
        breaker_state=breaker_state,
    )
