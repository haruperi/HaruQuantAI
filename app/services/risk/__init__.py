"""Approved Risk domain package-root public API.

Every cross-domain consumer imports standalone functions from
``app.services.risk``. Classes, models, enums, protocols, and constants remain
internal implementation details.
"""

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
from app.services.risk.config import (
    compute_config_hash,
    create_firm_mandate,
    create_risk_config,
    get_drawdown_mode,
    load_firm_mandate,
    load_risk_config,
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
    review_trade_risk,
    run_portfolio_risk_governor,
)
from app.services.risk.kill_switch import (
    apply_kill_switch_command,
    check_risk_kill_switch,
)
from app.services.risk.limits import (
    evaluate_market_context,
    evaluate_portfolio_limits,
    evaluate_single_day_profit_share,
)
from app.services.risk.migrations.definitions import run_risk_migrations
from app.services.risk.portfolio import build_portfolio_risk_snapshot
from app.services.risk.regimes import assess_risk_regime
from app.services.risk.reporting import generate_risk_report
from app.services.risk.scenarios import run_risk_scenario_analysis
from app.services.risk.sizing import calculate_position_size
from app.services.risk.validity import revalidate_risk_decision

__all__ = (
    "activate_allocation_budget",
    "append_risk_audit_record",
    "append_risk_kill_switch_transition",
    "apply_kill_switch_command",
    "assess_risk_regime",
    "build_allocation_runtime_operation",
    "build_development_risk_config",
    "build_governance_runtime_operation",
    "build_portfolio_risk_snapshot",
    "build_risk_approval_state_store",
    "build_risk_state_store",
    "calculate_position_size",
    "check_risk_kill_switch",
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
    "evaluate_market_context",
    "evaluate_portfolio_limits",
    "evaluate_single_day_profit_share",
    "execute_risk_state_store_operation",
    "generate_risk_report",
    "get_decision_state",
    "get_drawdown_mode",
    "get_kill_switch_state",
    "get_limit_status",
    "get_risk_error_catalog",
    "get_risk_error_code",
    "is_risk_domain_error",
    "issue_risk_approval_token",
    "list_risk_decisions",
    "load_firm_mandate",
    "load_risk_config",
    "persist_risk_decision",
    "revalidate_risk_decision",
    "review_allocation_proposal",
    "review_strategy_admission",
    "review_trade_risk",
    "revoke_risk_approval_scope",
    "run_portfolio_risk_governor",
    "run_risk_migrations",
    "run_risk_scenario_analysis",
    "validate_market_context_evidence",
    "validate_risk_approval_token",
    "verify_risk_audit_chain",
)
