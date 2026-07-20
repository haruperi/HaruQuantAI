"""Governance policy orchestration for risk checks."""

from __future__ import annotations

from app.services.risk.regimes import RegimeState

from .events import PolicyDecision
from .models import CircuitBreakerState, OverrideRecord, RiskLimits, RiskPolicy
from .post_trade_checks import evaluate_post_trade
from .pre_trade_checks import evaluate_pre_trade


class PolicyEngine:
    """Apply effective policy and run governance checks."""

    def effective_policy(
        self,
        policy: RiskPolicy,
        regime: RegimeState | None = None,
    ) -> tuple[RiskPolicy, list[OverrideRecord]]:
        """Return the effective policy after regime-specific tightening."""
        regime_is_stress = False
        if regime is not None:
            regime_is_stress = (
                bool(getattr(regime, "is_stress", False))
                or str(getattr(regime, "name", "")).upper() == "STRESS"
            )
        if not regime_is_stress:
            return policy, []

        overrides = []
        effective = policy
        override_map = {
            "var_cap_frac": min(policy.var_cap_frac, 0.07),
            "es_cap_frac": min(policy.es_cap_frac, 0.10),
            "delta_var_cap_frac": min(policy.delta_var_cap_frac, 0.015),
            "delta_es_cap_frac": min(policy.delta_es_cap_frac, 0.02),
            "max_margin_used_frac": min(policy.max_margin_used_frac, 0.35),
            "min_pair_corr": max(policy.min_pair_corr, 0.35),
            "stressed_corr_floor": max(policy.stressed_corr_floor, 0.75),
            "use_stressed_corr": True,
            "max_single_rc_frac": min(policy.max_single_rc_frac, 0.12),
        }
        for field_name, new_value in override_map.items():
            previous_value = getattr(effective, field_name)
            if previous_value == new_value:
                continue
            effective = effective.with_updates(**{field_name: new_value})
            overrides.append(
                OverrideRecord(
                    field_name=field_name,
                    previous_value=previous_value,
                    new_value=new_value,
                    reason="STRESS regime tightening applied.",
                    source="regime",
                )
            )
        return effective, overrides

    def evaluate_pre_trade(
        self,
        *,
        equity: float,
        current_var: float,
        new_var: float,
        delta_var: float,
        current_es: float,
        new_es: float,
        delta_es: float,
        current_margin_used: float | None,
        new_margin_used: float | None,
        rc_map_new: dict[str, float] | None,
        currency_exposure: dict[str, float] | None,
        gross_portfolio_notional: float | None,
        cluster_metrics: dict[str, dict[str, float]] | None,
        policy: RiskPolicy,
        regime: RegimeState | None = None,
        peak_equity: float | None = None,
        breaker_state: CircuitBreakerState | None = None,
    ) -> PolicyDecision:
        """Evaluate pre-trade governance using the effective policy."""
        effective, overrides = self.effective_policy(policy, regime)
        decision = evaluate_pre_trade(
            equity=equity,
            current_var=current_var,
            new_var=new_var,
            delta_var=delta_var,
            current_es=current_es,
            new_es=new_es,
            delta_es=delta_es,
            current_margin_used=current_margin_used,
            new_margin_used=new_margin_used,
            rc_map_new=rc_map_new,
            currency_exposure=currency_exposure,
            gross_portfolio_notional=gross_portfolio_notional,
            cluster_metrics=cluster_metrics,
            policy=effective,
            peak_equity=peak_equity,
            breaker_state=breaker_state,
        )
        return PolicyDecision(
            decision=decision.decision,
            reason=decision.reason,
            breaches=decision.breaches,
            warnings=decision.warnings,
            overrides=overrides,
            governance_state=decision.governance_state,
            circuit_breaker_state=decision.circuit_breaker_state,
        )

    def evaluate_post_trade(
        self,
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
        regime: RegimeState | None = None,
        peak_equity: float | None = None,
        breaker_state: CircuitBreakerState | None = None,
    ) -> PolicyDecision:
        """Evaluate current portfolio compliance using the effective policy."""
        effective, overrides = self.effective_policy(policy, regime)
        decision = evaluate_post_trade(
            equity=equity,
            portfolio_var=portfolio_var,
            portfolio_es=portfolio_es,
            margin_used=margin_used,
            rc_map=rc_map,
            currency_exposure=currency_exposure,
            gross_portfolio_notional=gross_portfolio_notional,
            cluster_metrics=cluster_metrics,
            policy=effective,
            peak_equity=peak_equity,
            breaker_state=breaker_state,
        )
        return PolicyDecision(
            decision=decision.decision,
            reason=decision.reason,
            breaches=decision.breaches,
            warnings=decision.warnings,
            overrides=overrides,
            governance_state=decision.governance_state,
            circuit_breaker_state=decision.circuit_breaker_state,
        )


def as_policy(limits: RiskPolicy | None) -> RiskPolicy:
    """Normalize legacy RiskLimits-style input to RiskPolicy."""
    return limits if limits is not None else RiskLimits()
