"""Approved Risk domain package-root public API.

Every cross-domain consumer imports standalone functions from
``app.services.risk``. Classes, models, enums, protocols, and constants remain
internal implementation details.
"""

import typing

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.risk.admission import review_strategy_admission
    from app.services.risk.allocation import (
        activate_allocation_budget,
        build_allocation_runtime_operation,
        review_allocation_proposal,
    )
    from app.services.risk.approvals import (
        build_risk_approval_state_store,
        create_approval_token_service,
        issue_risk_approval_token,
        revoke_risk_approval_scope,
        validate_risk_approval_token,
    )
    from app.services.risk.audit import (
        append_risk_audit_record,
        append_risk_kill_switch_transition,
        build_risk_state_store,
        create_risk_audit_chain,
        execute_risk_state_store_operation,
        get_kill_switch_state,
        list_risk_decisions,
        persist_risk_decision,
        verify_risk_audit_chain,
    )
    from app.services.risk.capacity import build_risk_capacity_guard
    from app.services.risk.config import (
        build_personal_account_risk_config,
        build_prop_firm_risk_config,
        compute_config_hash,
        create_firm_mandate,
        create_risk_config,
        get_drawdown_mode,
        get_risk_policy,
        load_firm_mandate,
        load_risk_config,
        register_default_risk_policies,
        register_risk_policy,
    )
    from app.services.risk.config.development import build_development_risk_config
    from app.services.risk.contracts import (
        create_action_policy_verdict,
        create_allocation_budget_activation_request,
        create_allocation_review_request,
        create_allocation_risk_decision,
        create_approval_attestation,
        create_approval_validation_result,
        create_decision_reuse_validation_result,
        create_kill_switch_command,
        create_kill_switch_state,
        create_portfolio_budget_execution_verdict,
        create_portfolio_risk_snapshot,
        create_portfolio_state,
        create_position_sizing_request,
        create_position_sizing_result,
        create_proposed_trade,
        create_regime_assessment,
        create_risk_approval_token,
        create_risk_audit_record,
        create_risk_decision_package,
        create_risk_domain_error,
        create_risk_limit_result,
        create_risk_report,
        create_scenario_definition,
        create_scenario_result,
        create_strategy_operational_eligibility_decision,
        create_strategy_operational_eligibility_request,
        get_decision_state,
        get_limit_status,
        get_risk_error_catalog,
        get_risk_error_code,
        is_risk_domain_error,
        validate_market_context_evidence,
    )
    from app.services.risk.governor import (
        build_governance_runtime_operation,
        create_risk_governor,
        evaluate_emergency_state,
        evaluate_trade_readiness,
        review_trade_risk,
        run_portfolio_risk_governor,
    )
    from app.services.risk.governor.manual_preflight import (
        review_cancel_authorization,
        review_manual_order,
    )
    from app.services.risk.kill_switch import (
        apply_kill_switch_command,
        check_risk_kill_switch,
        permits_risk_action,
    )
    from app.services.risk.limits import (
        evaluate_market_context,
        evaluate_portfolio_limits,
        evaluate_reward_risk_gate,
        evaluate_single_day_profit_share,
        resolve_effective_rules,
    )
    from app.services.risk.migrations.definitions import run_risk_migrations
    from app.services.risk.no_trade_state import (
        build_no_trade_outcome,
        classify_no_trade_outcome,
        parse_no_trade_outcome,
    )
    from app.services.risk.portfolio import build_portfolio_risk_snapshot
    from app.services.risk.regimes import assess_risk_regime
    from app.services.risk.reporting import (
        classify_decision_outcome,
        generate_risk_report,
    )
    from app.services.risk.scenarios import (
        evaluate_stress_loss_gate,
        run_risk_scenario_analysis,
    )
    from app.services.risk.sizing import (
        calculate_planned_risk_reward,
        calculate_position_size,
    )
    from app.services.risk.stop_validation import (
        build_stop_validation,
        parse_stop_validation,
        validate_stop_loss,
    )
    from app.services.risk.validity import (
        requires_risk_recalculation,
        revalidate_risk_decision,
    )

# Public export name to the module and attribute that owns it. Resolved on
# first access so importing this boundary never loads every feature.
_EXPORTS: dict[str, tuple[str, str]] = {
    "activate_allocation_budget": (
        "app.services.risk.allocation",
        "activate_allocation_budget",
    ),
    "append_risk_audit_record": ("app.services.risk.audit", "append_risk_audit_record"),
    "append_risk_kill_switch_transition": (
        "app.services.risk.audit",
        "append_risk_kill_switch_transition",
    ),
    "apply_kill_switch_command": (
        "app.services.risk.kill_switch",
        "apply_kill_switch_command",
    ),
    "assess_risk_regime": ("app.services.risk.regimes", "assess_risk_regime"),
    "build_allocation_runtime_operation": (
        "app.services.risk.allocation",
        "build_allocation_runtime_operation",
    ),
    "build_development_risk_config": (
        "app.services.risk.config.development",
        "build_development_risk_config",
    ),
    "build_governance_runtime_operation": (
        "app.services.risk.governor",
        "build_governance_runtime_operation",
    ),
    "build_no_trade_outcome": (
        "app.services.risk.no_trade_state",
        "build_no_trade_outcome",
    ),
    "build_personal_account_risk_config": (
        "app.services.risk.config",
        "build_personal_account_risk_config",
    ),
    "build_portfolio_risk_snapshot": (
        "app.services.risk.portfolio",
        "build_portfolio_risk_snapshot",
    ),
    "build_prop_firm_risk_config": (
        "app.services.risk.config",
        "build_prop_firm_risk_config",
    ),
    "build_risk_approval_state_store": (
        "app.services.risk.approvals",
        "build_risk_approval_state_store",
    ),
    "build_risk_capacity_guard": (
        "app.services.risk.capacity",
        "build_risk_capacity_guard",
    ),
    "build_risk_state_store": ("app.services.risk.audit", "build_risk_state_store"),
    "build_stop_validation": (
        "app.services.risk.stop_validation",
        "build_stop_validation",
    ),
    "calculate_planned_risk_reward": (
        "app.services.risk.sizing",
        "calculate_planned_risk_reward",
    ),
    "calculate_position_size": ("app.services.risk.sizing", "calculate_position_size"),
    "check_risk_kill_switch": (
        "app.services.risk.kill_switch",
        "check_risk_kill_switch",
    ),
    "classify_decision_outcome": (
        "app.services.risk.reporting",
        "classify_decision_outcome",
    ),
    "classify_no_trade_outcome": (
        "app.services.risk.no_trade_state",
        "classify_no_trade_outcome",
    ),
    "compute_config_hash": ("app.services.risk.config", "compute_config_hash"),
    "create_action_policy_verdict": (
        "app.services.risk.contracts",
        "create_action_policy_verdict",
    ),
    "create_allocation_budget_activation_request": (
        "app.services.risk.contracts",
        "create_allocation_budget_activation_request",
    ),
    "create_allocation_review_request": (
        "app.services.risk.contracts",
        "create_allocation_review_request",
    ),
    "create_allocation_risk_decision": (
        "app.services.risk.contracts",
        "create_allocation_risk_decision",
    ),
    "create_approval_attestation": (
        "app.services.risk.contracts",
        "create_approval_attestation",
    ),
    "create_approval_token_service": (
        "app.services.risk.approvals",
        "create_approval_token_service",
    ),
    "create_approval_validation_result": (
        "app.services.risk.contracts",
        "create_approval_validation_result",
    ),
    "create_decision_reuse_validation_result": (
        "app.services.risk.contracts",
        "create_decision_reuse_validation_result",
    ),
    "create_firm_mandate": ("app.services.risk.config", "create_firm_mandate"),
    "create_kill_switch_command": (
        "app.services.risk.contracts",
        "create_kill_switch_command",
    ),
    "create_kill_switch_state": (
        "app.services.risk.contracts",
        "create_kill_switch_state",
    ),
    "create_portfolio_budget_execution_verdict": (
        "app.services.risk.contracts",
        "create_portfolio_budget_execution_verdict",
    ),
    "create_portfolio_risk_snapshot": (
        "app.services.risk.contracts",
        "create_portfolio_risk_snapshot",
    ),
    "create_portfolio_state": ("app.services.risk.contracts", "create_portfolio_state"),
    "create_position_sizing_request": (
        "app.services.risk.contracts",
        "create_position_sizing_request",
    ),
    "create_position_sizing_result": (
        "app.services.risk.contracts",
        "create_position_sizing_result",
    ),
    "create_proposed_trade": ("app.services.risk.contracts", "create_proposed_trade"),
    "create_regime_assessment": (
        "app.services.risk.contracts",
        "create_regime_assessment",
    ),
    "create_risk_approval_token": (
        "app.services.risk.contracts",
        "create_risk_approval_token",
    ),
    "create_risk_audit_chain": ("app.services.risk.audit", "create_risk_audit_chain"),
    "create_risk_audit_record": (
        "app.services.risk.contracts",
        "create_risk_audit_record",
    ),
    "create_risk_config": ("app.services.risk.config", "create_risk_config"),
    "create_risk_decision_package": (
        "app.services.risk.contracts",
        "create_risk_decision_package",
    ),
    "create_risk_domain_error": (
        "app.services.risk.contracts",
        "create_risk_domain_error",
    ),
    "create_risk_governor": ("app.services.risk.governor", "create_risk_governor"),
    "create_risk_limit_result": (
        "app.services.risk.contracts",
        "create_risk_limit_result",
    ),
    "create_risk_report": ("app.services.risk.contracts", "create_risk_report"),
    "create_scenario_definition": (
        "app.services.risk.contracts",
        "create_scenario_definition",
    ),
    "create_scenario_result": ("app.services.risk.contracts", "create_scenario_result"),
    "create_strategy_operational_eligibility_decision": (
        "app.services.risk.contracts",
        "create_strategy_operational_eligibility_decision",
    ),
    "create_strategy_operational_eligibility_request": (
        "app.services.risk.contracts",
        "create_strategy_operational_eligibility_request",
    ),
    "evaluate_emergency_state": (
        "app.services.risk.governor",
        "evaluate_emergency_state",
    ),
    "evaluate_market_context": ("app.services.risk.limits", "evaluate_market_context"),
    "evaluate_portfolio_limits": (
        "app.services.risk.limits",
        "evaluate_portfolio_limits",
    ),
    "evaluate_reward_risk_gate": (
        "app.services.risk.limits",
        "evaluate_reward_risk_gate",
    ),
    "evaluate_single_day_profit_share": (
        "app.services.risk.limits",
        "evaluate_single_day_profit_share",
    ),
    "evaluate_stress_loss_gate": (
        "app.services.risk.scenarios",
        "evaluate_stress_loss_gate",
    ),
    "evaluate_trade_readiness": (
        "app.services.risk.governor",
        "evaluate_trade_readiness",
    ),
    "execute_risk_state_store_operation": (
        "app.services.risk.audit",
        "execute_risk_state_store_operation",
    ),
    "generate_risk_report": ("app.services.risk.reporting", "generate_risk_report"),
    "get_decision_state": ("app.services.risk.contracts", "get_decision_state"),
    "get_drawdown_mode": ("app.services.risk.config", "get_drawdown_mode"),
    "get_kill_switch_state": ("app.services.risk.audit", "get_kill_switch_state"),
    "get_limit_status": ("app.services.risk.contracts", "get_limit_status"),
    "get_risk_error_catalog": ("app.services.risk.contracts", "get_risk_error_catalog"),
    "get_risk_error_code": ("app.services.risk.contracts", "get_risk_error_code"),
    "get_risk_policy": ("app.services.risk.config", "get_risk_policy"),
    "is_risk_domain_error": ("app.services.risk.contracts", "is_risk_domain_error"),
    "issue_risk_approval_token": (
        "app.services.risk.approvals",
        "issue_risk_approval_token",
    ),
    "list_risk_decisions": ("app.services.risk.audit", "list_risk_decisions"),
    "load_firm_mandate": ("app.services.risk.config", "load_firm_mandate"),
    "load_risk_config": ("app.services.risk.config", "load_risk_config"),
    "parse_no_trade_outcome": (
        "app.services.risk.no_trade_state",
        "parse_no_trade_outcome",
    ),
    "parse_stop_validation": (
        "app.services.risk.stop_validation",
        "parse_stop_validation",
    ),
    "permits_risk_action": ("app.services.risk.kill_switch", "permits_risk_action"),
    "persist_risk_decision": ("app.services.risk.audit", "persist_risk_decision"),
    "register_default_risk_policies": (
        "app.services.risk.config",
        "register_default_risk_policies",
    ),
    "register_risk_policy": ("app.services.risk.config", "register_risk_policy"),
    "requires_risk_recalculation": (
        "app.services.risk.validity",
        "requires_risk_recalculation",
    ),
    "resolve_effective_rules": ("app.services.risk.limits", "resolve_effective_rules"),
    "revalidate_risk_decision": (
        "app.services.risk.validity",
        "revalidate_risk_decision",
    ),
    "review_allocation_proposal": (
        "app.services.risk.allocation",
        "review_allocation_proposal",
    ),
    "review_cancel_authorization": (
        "app.services.risk.governor.manual_preflight",
        "review_cancel_authorization",
    ),
    "review_manual_order": (
        "app.services.risk.governor.manual_preflight",
        "review_manual_order",
    ),
    "review_strategy_admission": (
        "app.services.risk.admission",
        "review_strategy_admission",
    ),
    "review_trade_risk": ("app.services.risk.governor", "review_trade_risk"),
    "revoke_risk_approval_scope": (
        "app.services.risk.approvals",
        "revoke_risk_approval_scope",
    ),
    "run_portfolio_risk_governor": (
        "app.services.risk.governor",
        "run_portfolio_risk_governor",
    ),
    "run_risk_migrations": (
        "app.services.risk.migrations.definitions",
        "run_risk_migrations",
    ),
    "run_risk_scenario_analysis": (
        "app.services.risk.scenarios",
        "run_risk_scenario_analysis",
    ),
    "validate_market_context_evidence": (
        "app.services.risk.contracts",
        "validate_market_context_evidence",
    ),
    "validate_risk_approval_token": (
        "app.services.risk.approvals",
        "validate_risk_approval_token",
    ),
    "validate_stop_loss": ("app.services.risk.stop_validation", "validate_stop_loss"),
    "verify_risk_audit_chain": ("app.services.risk.audit", "verify_risk_audit_chain"),
}


def __getattr__(name: str) -> object:
    """Resolve one public export on first access.

    Args:
        name: Public export name.

    Returns:
        The resolved public function.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the public export surface.

    Returns:
        Sorted public export names.
    """
    return sorted(_EXPORTS)


__all__ = (
    "activate_allocation_budget",
    "append_risk_audit_record",
    "append_risk_kill_switch_transition",
    "apply_kill_switch_command",
    "assess_risk_regime",
    "build_allocation_runtime_operation",
    "build_development_risk_config",
    "build_governance_runtime_operation",
    "build_no_trade_outcome",
    "build_personal_account_risk_config",
    "build_portfolio_risk_snapshot",
    "build_prop_firm_risk_config",
    "build_risk_approval_state_store",
    "build_risk_capacity_guard",
    "build_risk_state_store",
    "build_stop_validation",
    "calculate_planned_risk_reward",
    "calculate_position_size",
    "check_risk_kill_switch",
    "classify_decision_outcome",
    "classify_no_trade_outcome",
    "compute_config_hash",
    "create_action_policy_verdict",
    "create_allocation_budget_activation_request",
    "create_allocation_review_request",
    "create_allocation_risk_decision",
    "create_approval_attestation",
    "create_approval_token_service",
    "create_approval_validation_result",
    "create_decision_reuse_validation_result",
    "create_firm_mandate",
    "create_kill_switch_command",
    "create_kill_switch_state",
    "create_portfolio_budget_execution_verdict",
    "create_portfolio_risk_snapshot",
    "create_portfolio_state",
    "create_position_sizing_request",
    "create_position_sizing_result",
    "create_proposed_trade",
    "create_regime_assessment",
    "create_risk_approval_token",
    "create_risk_audit_chain",
    "create_risk_audit_record",
    "create_risk_config",
    "create_risk_decision_package",
    "create_risk_domain_error",
    "create_risk_governor",
    "create_risk_limit_result",
    "create_risk_report",
    "create_scenario_definition",
    "create_scenario_result",
    "create_strategy_operational_eligibility_decision",
    "create_strategy_operational_eligibility_request",
    "evaluate_emergency_state",
    "evaluate_market_context",
    "evaluate_portfolio_limits",
    "evaluate_reward_risk_gate",
    "evaluate_single_day_profit_share",
    "evaluate_stress_loss_gate",
    "evaluate_trade_readiness",
    "execute_risk_state_store_operation",
    "generate_risk_report",
    "get_decision_state",
    "get_drawdown_mode",
    "get_kill_switch_state",
    "get_limit_status",
    "get_risk_error_catalog",
    "get_risk_error_code",
    "get_risk_policy",
    "is_risk_domain_error",
    "issue_risk_approval_token",
    "list_risk_decisions",
    "load_firm_mandate",
    "load_risk_config",
    "parse_no_trade_outcome",
    "parse_stop_validation",
    "permits_risk_action",
    "persist_risk_decision",
    "register_default_risk_policies",
    "register_risk_policy",
    "requires_risk_recalculation",
    "resolve_effective_rules",
    "revalidate_risk_decision",
    "review_allocation_proposal",
    "review_cancel_authorization",
    "review_manual_order",
    "review_strategy_admission",
    "review_trade_risk",
    "revoke_risk_approval_scope",
    "run_portfolio_risk_governor",
    "run_risk_migrations",
    "run_risk_scenario_analysis",
    "validate_market_context_evidence",
    "validate_risk_approval_token",
    "validate_stop_loss",
    "verify_risk_audit_chain",
)
