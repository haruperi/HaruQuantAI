"""HaruQuant streamlined permissions and policy gates.

Recommended path:
    runtime/permissions.py

This module is intentionally self-contained for the early simplified build.

Design goals:
- deny by default
- explicit allowed tools per agent
- tool class and approval metadata
- simple runtime condition checks
- fail closed for live/critical actions
- root-level tools/ folder remains the canonical tool location
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from fnmatch import fnmatch


class PermissionClass(str, Enum):
    """Permission/risk class for tools."""

    READ_ONLY = "read_only"
    WRITE_SAFE = "write_safe"
    WRITE_CONTROLLED = "write_controlled"
    CRITICAL = "critical"
    FORBIDDEN = "forbidden"


class ApprovalType(str, Enum):
    """Approval requirement for a tool/action."""

    NONE = "none"
    AUDIT_REQUIRED = "audit_required"
    RISK_GOVERNOR_REQUIRED = "risk_governor_required"
    HUMAN_REQUIRED = "human_required"
    HUMAN_AND_RISK_REQUIRED = "human_and_risk_required"
    FORBIDDEN = "forbidden"


class DecisionStatus(str, Enum):
    """Permission decision status."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ToolPolicy:
    """Policy metadata for one tool."""

    name: str
    permission_class: PermissionClass
    approval: ApprovalType
    audit_required: bool = True
    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False
    open_world: bool = False
    required_conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentPolicy:
    """Permission profile for one agent."""

    name: str
    department: str
    allowed_tools: frozenset[str] = field(default_factory=frozenset)
    forbidden_tools: frozenset[str] = field(default_factory=frozenset)
    required_conditions: tuple[str, ...] = ()
    can_trade_live: bool = False
    can_place_paper_orders: bool = False
    can_run_backtest: bool = False
    can_modify_risk: bool = False


@dataclass(frozen=True)
class PermissionDecision:
    """Result returned by permission checks."""

    status: DecisionStatus
    agent_name: str
    tool_name: str
    reason: str
    approval_required: ApprovalType = ApprovalType.NONE
    audit_required: bool = False
    missing_conditions: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.status == DecisionStatus.ALLOWED


# ---------------------------------------------------------------------------
# Tool catalog
# ---------------------------------------------------------------------------

READ_ONLY_TOOLS = frozenset(
    {
        "read_constitution",
        "read_risk_policy",
        "read_agent_permissions",
        "read_strategy_lifecycle_policy",
        "list_strategies",
        "read_strategy_spec",
        "read_strategy_code",
        "get_strategy_status",
        "get_historical_ohlcv",
        "get_tick_data",
        "get_symbol_info",
        "get_spread_snapshot",
        "get_economic_calendar",
        "get_news_context",
        "get_account_snapshot",
        "get_open_positions",
        "get_pending_orders",
        "get_backtest_result",
        "get_analytics_summary",
        "get_risk_snapshot",
        "get_correlation_matrix",
        "get_var_cvar_snapshot",
        "read_audit_log",
        "read_execution_log",
        "read_cost_log",
    }
)

WRITE_SAFE_TOOLS = frozenset(
    {
        "write_research_brief",
        "create_strategy_spec",
        "update_strategy_spec_draft",
        "save_strategy_code_draft",
        "save_strategy_tests_draft",
        "run_strategy_tests",
        "run_linter",
        "run_formatter",
        "create_strategy_review",
        "create_risk_memo",
        "create_portfolio_memo",
        "create_performance_report",
        "create_board_pack",
        "create_incident_report",
        "create_cost_report",
        "write_audit_event",
    }
)

WRITE_CONTROLLED_TOOLS = frozenset(
    {
        "submit_strategy_for_review",
        "mark_strategy_review_passed",
        "mark_strategy_review_failed",
        "submit_strategy_for_backtest",
        "run_backtest",
        "run_optimization",
        "run_robustness_test",
        "run_statistical_validation",
        "submit_strategy_for_robustness",
        "request_admit_to_paper",
        "start_paper_trading",
        "pause_paper_strategy",
        "retire_strategy",
        "request_live_activation",
        "request_allocation_change",
        "request_risk_approval",
        "place_paper_order",
        "close_paper_position",
    }
)

CRITICAL_TOOLS = frozenset(
    {
        "activate_live_trading_global",
        "deactivate_live_trading_global",
        "activate_live_strategy",
        "deactivate_live_strategy",
        "change_risk_thresholds",
        "change_prop_firm_profile",
        "change_agent_permissions",
        "change_tool_registry",
        "change_broker_credentials",
        "connect_live_broker",
        "disconnect_live_broker",
        "place_live_order",
        "close_live_position",
        "cancel_live_order",
        "emergency_flatten_all",
        "trigger_kill_switch",
        "reset_kill_switch",
        "override_news_block",
        "override_weekend_rule",
    }
)

FORBIDDEN_TOOLS = frozenset(
    {
        "delete_or_mutate_audit_log",
        "delete_or_mutate_backtest_evidence",
        "disable_audit_logger",
        "disable_risk_governor",
        "disable_kill_switch",
    }
)


def _tool_policy(tool_name: str) -> ToolPolicy:
    """Create default policy metadata for a known tool."""
    if tool_name in READ_ONLY_TOOLS:
        return ToolPolicy(
            name=tool_name,
            permission_class=PermissionClass.READ_ONLY,
            approval=ApprovalType.NONE,
            audit_required=False,
            read_only=True,
        )

    if tool_name in WRITE_SAFE_TOOLS:
        return ToolPolicy(
            name=tool_name,
            permission_class=PermissionClass.WRITE_SAFE,
            approval=ApprovalType.AUDIT_REQUIRED,
            audit_required=True,
            read_only=False,
        )

    if tool_name in WRITE_CONTROLLED_TOOLS:
        approval = ApprovalType.AUDIT_REQUIRED
        required_conditions: tuple[str, ...] = ()

        if tool_name in {"place_paper_order", "request_risk_approval"}:
            approval = ApprovalType.RISK_GOVERNOR_REQUIRED
            required_conditions = ("risk_governor_available", "audit_logger_healthy")

        if tool_name in {"start_paper_trading", "request_admit_to_paper"}:
            required_conditions = ("paper_trading_enabled", "audit_logger_healthy")

        return ToolPolicy(
            name=tool_name,
            permission_class=PermissionClass.WRITE_CONTROLLED,
            approval=approval,
            audit_required=True,
            read_only=False,
            required_conditions=required_conditions,
        )

    if tool_name in CRITICAL_TOOLS:
        approval = ApprovalType.HUMAN_REQUIRED
        required_conditions = ("audit_logger_healthy",)

        if tool_name in {
            "place_live_order",
            "close_live_position",
            "cancel_live_order",
        }:
            approval = ApprovalType.HUMAN_AND_RISK_REQUIRED
            required_conditions = (
                "global_live_trading_enabled",
                "strategy_live_approved",
                "human_board_approval_active",
                "risk_governor_token_valid",
                "kill_switch_healthy",
                "audit_logger_healthy",
                "broker_heartbeat_healthy",
                "prop_firm_rules_clear",
            )

        if tool_name == "trigger_kill_switch":
            approval = ApprovalType.AUDIT_REQUIRED
            required_conditions = ("audit_logger_healthy",)

        if tool_name == "emergency_flatten_all":
            approval = ApprovalType.HUMAN_AND_RISK_REQUIRED
            required_conditions = (
                "emergency_mode_active",
                "audit_logger_healthy",
                "kill_switch_healthy",
            )

        if tool_name == "reset_kill_switch":
            approval = ApprovalType.HUMAN_REQUIRED
            required_conditions = (
                "human_board_approval_active",
                "audit_logger_healthy",
            )

        return ToolPolicy(
            name=tool_name,
            permission_class=PermissionClass.CRITICAL,
            approval=approval,
            audit_required=True,
            read_only=False,
            destructive=tool_name
            in {
                "deactivate_live_strategy",
                "deactivate_live_trading_global",
                "close_live_position",
                "cancel_live_order",
                "emergency_flatten_all",
                "trigger_kill_switch",
                "reset_kill_switch",
            },
            open_world=tool_name
            in {
                "connect_live_broker",
                "disconnect_live_broker",
                "place_live_order",
                "close_live_position",
                "cancel_live_order",
                "emergency_flatten_all",
            },
            required_conditions=required_conditions,
        )

    if tool_name in FORBIDDEN_TOOLS:
        return ToolPolicy(
            name=tool_name,
            permission_class=PermissionClass.FORBIDDEN,
            approval=ApprovalType.FORBIDDEN,
            audit_required=True,
            destructive=True,
        )

    # Unknown tools are denied by default.
    return ToolPolicy(
        name=tool_name,
        permission_class=PermissionClass.FORBIDDEN,
        approval=ApprovalType.FORBIDDEN,
        audit_required=True,
    )


TOOL_REGISTRY: dict[str, ToolPolicy] = {
    tool: _tool_policy(tool)
    for tool in (
        set(READ_ONLY_TOOLS)
        | set(WRITE_SAFE_TOOLS)
        | set(WRITE_CONTROLLED_TOOLS)
        | set(CRITICAL_TOOLS)
        | set(FORBIDDEN_TOOLS)
    )
}


# ---------------------------------------------------------------------------
# Shared tool groups
# ---------------------------------------------------------------------------

POLICY_READ_TOOLS = frozenset(
    {
        "read_constitution",
        "read_risk_policy",
        "read_agent_permissions",
        "read_strategy_lifecycle_policy",
    }
)

MARKET_READ_TOOLS = frozenset(
    {
        "get_historical_ohlcv",
        "get_tick_data",
        "get_symbol_info",
        "get_spread_snapshot",
        "get_economic_calendar",
        "get_news_context",
    }
)

STRATEGY_READ_TOOLS = frozenset(
    {
        "list_strategies",
        "read_strategy_spec",
        "read_strategy_code",
        "get_strategy_status",
    }
)

BACKTEST_READ_TOOLS = frozenset({"get_backtest_result", "get_analytics_summary"})

RISK_READ_TOOLS = frozenset(
    {
        "read_risk_policy",
        "get_risk_snapshot",
        "get_correlation_matrix",
        "get_var_cvar_snapshot",
        "get_account_snapshot",
        "get_open_positions",
        "get_pending_orders",
    }
)

AUDIT_READ_TOOLS = frozenset(
    {
        "read_audit_log",
        "read_execution_log",
        "read_cost_log",
    }
)

AUDIT_WRITE_TOOLS = frozenset({"write_audit_event"})


# ---------------------------------------------------------------------------
# Agent policies
# ---------------------------------------------------------------------------

AGENT_POLICIES: dict[str, AgentPolicy] = {}


def _register(policy: AgentPolicy) -> None:
    AGENT_POLICIES[policy.name] = policy


# Executive & Control
_register(
    AgentPolicy(
        name="ceo_agent",
        department="executive_control",
        allowed_tools=frozenset(
            POLICY_READ_TOOLS
            | STRATEGY_READ_TOOLS
            | BACKTEST_READ_TOOLS
            | {"get_risk_snapshot"}
            | {
                "create_board_pack",
                "create_performance_report",
                "create_portfolio_memo",
                "create_risk_memo",
                "request_admit_to_paper",
                "request_live_activation",
                "request_allocation_change",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "place_live_order",
                "place_paper_order",
                "change_risk_thresholds",
                "change_agent_permissions",
                "change_tool_registry",
                "change_broker_credentials",
                "disable_risk_governor",
                "disable_audit_logger",
                "reset_kill_switch",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="planner_agent",
        department="executive_control",
        allowed_tools=frozenset(
            POLICY_READ_TOOLS | STRATEGY_READ_TOOLS | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            WRITE_CONTROLLED_TOOLS | CRITICAL_TOOLS | FORBIDDEN_TOOLS
        ),
    )
)

_register(
    AgentPolicy(
        name="control_plane",
        department="executive_control",
        allowed_tools=frozenset(
            POLICY_READ_TOOLS
            | STRATEGY_READ_TOOLS
            | {"get_risk_snapshot"}
            | AUDIT_READ_TOOLS
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(FORBIDDEN_TOOLS),
    )
)

# Research
for _agent_name in (
    "research_lead_agent",
    "market_intelligence_agent",
    "quant_research_agent",
    "research_validator_agent",
):
    _register(
        AgentPolicy(
            name=_agent_name,
            department="research",
            allowed_tools=frozenset(
                MARKET_READ_TOOLS
                | STRATEGY_READ_TOOLS
                | BACKTEST_READ_TOOLS
                | {"write_research_brief"}
                | AUDIT_WRITE_TOOLS
                | (
                    POLICY_READ_TOOLS
                    if _agent_name == "research_validator_agent"
                    else frozenset()
                )
            ),
            forbidden_tools=frozenset(
                {
                    "save_strategy_code_draft",
                    "run_backtest",
                    "run_optimization",
                    "run_robustness_test",
                    "start_paper_trading",
                    "place_paper_order",
                    "place_live_order",
                    "activate_live_strategy",
                    "change_risk_thresholds",
                }
            )
            | CRITICAL_TOOLS
            | FORBIDDEN_TOOLS,
        )
    )

# Strategy development
for _agent_name in ("strategy_lead_agent", "strategy_designer_agent"):
    _register(
        AgentPolicy(
            name=_agent_name,
            department="strategy_development",
            allowed_tools=frozenset(
                POLICY_READ_TOOLS
                | {"get_historical_ohlcv", "get_symbol_info"}
                | {
                    "create_strategy_spec",
                    "update_strategy_spec_draft",
                    "submit_strategy_for_review",
                }
                | AUDIT_WRITE_TOOLS
            ),
            forbidden_tools=frozenset(
                {
                    "save_strategy_code_draft",
                    "run_backtest",
                    "start_paper_trading",
                    "place_paper_order",
                    "place_live_order",
                    "activate_live_strategy",
                }
            )
            | CRITICAL_TOOLS
            | FORBIDDEN_TOOLS,
        )
    )

_register(
    AgentPolicy(
        name="strategy_engineer_agent",
        department="strategy_development",
        allowed_tools=frozenset(
            {
                "read_strategy_spec",
                "read_strategy_code",
                "save_strategy_code_draft",
                "save_strategy_tests_draft",
                "run_strategy_tests",
                "run_linter",
                "run_formatter",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "run_backtest",
                "place_paper_order",
                "place_live_order",
                "activate_live_strategy",
                "change_risk_thresholds",
                "change_broker_credentials",
                "disable_audit_logger",
                "disable_risk_governor",
                "disable_kill_switch",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="strategy_reviewer_agent",
        department="strategy_development",
        allowed_tools=frozenset(
            {
                "read_strategy_spec",
                "read_strategy_code",
                "get_historical_ohlcv",
                "create_strategy_review",
                "mark_strategy_review_passed",
                "mark_strategy_review_failed",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "save_strategy_code_draft",
                "place_paper_order",
                "place_live_order",
                "activate_live_strategy",
                "change_risk_thresholds",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="strategy_librarian_agent",
        department="strategy_development",
        allowed_tools=frozenset(
            STRATEGY_READ_TOOLS
            | {
                "create_strategy_spec",
                "update_strategy_spec_draft",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "activate_live_strategy",
                "start_paper_trading",
                "place_paper_order",
                "place_live_order",
                "change_risk_thresholds",
                "delete_or_mutate_backtest_evidence",
                "delete_or_mutate_audit_log",
            }
        ),
    )
)

# Simulation and validation
_register(
    AgentPolicy(
        name="simulation_lead_agent",
        department="simulation_validation",
        allowed_tools=frozenset(
            {
                "read_strategy_spec",
                "read_strategy_code",
                "get_historical_ohlcv",
                "get_tick_data",
                "run_backtest",
                "run_optimization",
                "run_robustness_test",
                "run_statistical_validation",
                "submit_strategy_for_robustness",
                "get_backtest_result",
                "get_analytics_summary",
                "create_performance_report",
            }
            | AUDIT_WRITE_TOOLS
        ),
        can_run_backtest=True,
        forbidden_tools=frozenset(
            {
                "place_paper_order",
                "place_live_order",
                "start_paper_trading",
                "activate_live_strategy",
                "change_risk_thresholds",
                "delete_or_mutate_backtest_evidence",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="backtest_analyst_agent",
        department="simulation_validation",
        allowed_tools=frozenset(
            BACKTEST_READ_TOOLS
            | {"read_strategy_spec", "create_performance_report"}
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "run_backtest",
                "place_paper_order",
                "place_live_order",
                "activate_live_strategy",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="optimization_agent",
        department="simulation_validation",
        allowed_tools=frozenset(
            {
                "read_strategy_spec",
                "read_strategy_code",
                "get_historical_ohlcv",
                "run_optimization",
                "get_backtest_result",
                "create_performance_report",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {"activate_live_strategy", "place_live_order", "change_risk_thresholds"}
        ),
    )
)

_register(
    AgentPolicy(
        name="robustness_validator_agent",
        department="simulation_validation",
        allowed_tools=frozenset(
            {
                "read_strategy_spec",
                "read_strategy_code",
                "get_backtest_result",
                "get_historical_ohlcv",
                "run_robustness_test",
                "run_statistical_validation",
                "create_performance_report",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {"start_paper_trading", "activate_live_strategy", "place_live_order"}
        ),
    )
)

_register(
    AgentPolicy(
        name="evidence_packager_agent",
        department="simulation_validation",
        allowed_tools=frozenset(
            BACKTEST_READ_TOOLS
            | {"read_strategy_spec", "create_performance_report"}
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {"place_paper_order", "place_live_order", "activate_live_strategy"}
        ),
    )
)

# Risk and portfolio
for _agent_name in ("risk_lead_agent", "risk_auditor_agent"):
    _register(
        AgentPolicy(
            name=_agent_name,
            department="risk_portfolio",
            allowed_tools=frozenset(
                RISK_READ_TOOLS
                | {"get_backtest_result", "create_risk_memo"}
                | AUDIT_WRITE_TOOLS
            ),
            forbidden_tools=frozenset(
                {
                    "change_risk_thresholds",
                    "place_live_order",
                    "activate_live_strategy",
                    "override_news_block",
                    "reset_kill_switch",
                }
            ),
        )
    )

_register(
    AgentPolicy(
        name="risk_governor_agent",
        department="risk_portfolio",
        allowed_tools=frozenset(
            RISK_READ_TOOLS
            | {
                "get_symbol_info",
                "get_spread_snapshot",
                "get_economic_calendar",
                "request_risk_approval",
                "trigger_kill_switch",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "change_risk_thresholds",
                "place_live_order",
                "reset_kill_switch",
                "disable_kill_switch",
                "disable_risk_governor",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="portfolio_manager_agent",
        department="risk_portfolio",
        allowed_tools=frozenset(
            STRATEGY_READ_TOOLS
            | BACKTEST_READ_TOOLS
            | {"get_risk_snapshot", "get_correlation_matrix"}
            | {
                "create_portfolio_memo",
                "request_admit_to_paper",
                "request_live_activation",
                "request_allocation_change",
                "retire_strategy",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "place_live_order",
                "activate_live_strategy",
                "change_risk_thresholds",
                "change_broker_credentials",
                "reset_kill_switch",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="allocation_agent",
        department="risk_portfolio",
        allowed_tools=frozenset(
            {
                "get_account_snapshot",
                "get_open_positions",
                "get_risk_snapshot",
                "get_correlation_matrix",
                "get_var_cvar_snapshot",
                "create_portfolio_memo",
                "request_allocation_change",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {"place_live_order", "activate_live_strategy", "change_risk_thresholds"}
        ),
    )
)

# Execution
_register(
    AgentPolicy(
        name="execution_lead_agent",
        department="execution",
        allowed_tools=frozenset(
            {
                "get_strategy_status",
                "get_account_snapshot",
                "get_open_positions",
                "get_pending_orders",
                "get_symbol_info",
                "get_spread_snapshot",
                "get_economic_calendar",
                "request_risk_approval",
                "create_incident_report",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "place_live_order",
                "place_paper_order",
                "activate_live_strategy",
                "change_risk_thresholds",
                "reset_kill_switch",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="execution_readiness_agent",
        department="execution",
        allowed_tools=frozenset(
            {
                "get_strategy_status",
                "get_account_snapshot",
                "get_open_positions",
                "get_pending_orders",
                "get_symbol_info",
                "get_spread_snapshot",
                "get_economic_calendar",
                "read_execution_log",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "place_live_order",
                "place_paper_order",
                "activate_live_strategy",
                "change_risk_thresholds",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="paper_trading_agent",
        department="execution",
        allowed_tools=frozenset(
            {
                "get_strategy_status",
                "get_symbol_info",
                "get_spread_snapshot",
                "request_risk_approval",
                "place_paper_order",
                "close_paper_position",
                "pause_paper_strategy",
            }
            | AUDIT_WRITE_TOOLS
        ),
        required_conditions=(
            "paper_trading_enabled",
            "risk_governor_available",
            "audit_logger_healthy",
        ),
        can_place_paper_orders=True,
        forbidden_tools=frozenset(
            {
                "place_live_order",
                "activate_live_trading_global",
                "activate_live_strategy",
                "change_risk_thresholds",
                "change_broker_credentials",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="live_execution_agent",
        department="execution",
        allowed_tools=frozenset(
            {
                "get_strategy_status",
                "get_account_snapshot",
                "get_open_positions",
                "get_pending_orders",
                "get_symbol_info",
                "get_spread_snapshot",
                "get_economic_calendar",
                "request_risk_approval",
                "place_live_order",
                "close_live_position",
                "cancel_live_order",
            }
            | AUDIT_WRITE_TOOLS
        ),
        required_conditions=(
            "global_live_trading_enabled",
            "strategy_live_approved",
            "human_board_approval_active",
            "risk_governor_token_valid",
            "kill_switch_healthy",
            "audit_logger_healthy",
            "broker_heartbeat_healthy",
            "prop_firm_rules_clear",
        ),
        can_trade_live=True,
        forbidden_tools=frozenset(
            {
                "change_risk_thresholds",
                "change_agent_permissions",
                "change_tool_registry",
                "change_broker_credentials",
                "reset_kill_switch",
                "override_news_block",
                "override_weekend_rule",
                "disable_audit_logger",
                "disable_risk_governor",
                "disable_kill_switch",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="kill_switch_agent",
        department="execution",
        allowed_tools=frozenset(
            {
                "get_account_snapshot",
                "get_open_positions",
                "get_pending_orders",
                "get_risk_snapshot",
                "read_execution_log",
                "read_audit_log",
                "trigger_kill_switch",
                "deactivate_live_strategy",
                "deactivate_live_trading_global",
                "emergency_flatten_all",
                "create_incident_report",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "reset_kill_switch",
                "activate_live_strategy",
                "activate_live_trading_global",
                "change_risk_thresholds",
                "delete_or_mutate_audit_log",
                "disable_kill_switch",
            }
        ),
    )
)

# Operations, audit, governance
_register(
    AgentPolicy(
        name="governance_agent",
        department="operations_governance",
        allowed_tools=frozenset(
            POLICY_READ_TOOLS
            | AUDIT_READ_TOOLS
            | {"create_board_pack", "create_incident_report"}
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {"place_live_order", "change_risk_thresholds", "reset_kill_switch"}
        ),
    )
)

_register(
    AgentPolicy(
        name="audit_agent",
        department="operations_governance",
        allowed_tools=frozenset(
            AUDIT_READ_TOOLS
            | {
                "get_strategy_status",
                "get_risk_snapshot",
                "get_account_snapshot",
                "get_open_positions",
                "create_incident_report",
                "trigger_kill_switch",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            {
                "delete_or_mutate_audit_log",
                "delete_or_mutate_backtest_evidence",
                "place_live_order",
                "change_risk_thresholds",
                "reset_kill_switch",
                "change_agent_permissions",
            }
        ),
    )
)

_register(
    AgentPolicy(
        name="performance_reporter_agent",
        department="operations_governance",
        allowed_tools=frozenset(
            BACKTEST_READ_TOOLS
            | {"get_account_snapshot", "get_open_positions"}
            | AUDIT_READ_TOOLS
            | {"create_performance_report", "create_board_pack"}
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            CRITICAL_TOOLS | {"place_paper_order", "start_paper_trading"}
        ),
    )
)

_register(
    AgentPolicy(
        name="cost_efficiency_agent",
        department="operations_governance",
        allowed_tools=frozenset(
            {
                "read_cost_log",
                "read_audit_log",
                "create_cost_report",
                "create_performance_report",
            }
            | AUDIT_WRITE_TOOLS
        ),
        forbidden_tools=frozenset(
            CRITICAL_TOOLS
            | {
                "place_paper_order",
                "request_risk_approval",
                "trigger_kill_switch",
                "change_agent_permissions",
                "change_tool_registry",
            }
        ),
    )
)


# Backward-compatible aliases for early simple department agents.
AGENT_ALIASES: dict[str, str] = {
    "research_agent": "research_lead_agent",
    "strategy_agent": "strategy_lead_agent",
    "validation_agent": "simulation_lead_agent",
    "risk_agent": "risk_lead_agent",
    "execution_agent": "execution_lead_agent",
    "operations_agent": "governance_agent",
}


def _high_level_permissions(policy: AgentPolicy) -> dict[str, bool]:
    """Return the simple Phase 2 permission flags for a policy."""
    return {
        "can_trade_live": policy.can_trade_live,
        "can_place_paper_orders": policy.can_place_paper_orders,
        "can_run_backtest": policy.can_run_backtest,
        "can_modify_risk": policy.can_modify_risk,
    }


AGENT_PERMISSIONS: dict[str, dict[str, bool]] = {
    agent_name: _high_level_permissions(policy)
    for agent_name, policy in AGENT_POLICIES.items()
}

AGENT_PERMISSIONS.update(
    {
        alias: _high_level_permissions(AGENT_POLICIES[canonical_name])
        for alias, canonical_name in AGENT_ALIASES.items()
        if canonical_name in AGENT_POLICIES
    }
)


# ---------------------------------------------------------------------------
# Runtime context defaults
# ---------------------------------------------------------------------------

DEFAULT_RUNTIME_CONTEXT: dict[str, bool] = {
    "live_trading_enabled": False,
    "paper_trading_enabled": True,
    "global_live_trading_enabled": False,
    "strategy_live_approved": False,
    "human_board_approval_active": False,
    "risk_governor_available": True,
    "risk_governor_token_valid": False,
    "kill_switch_healthy": True,
    "audit_logger_healthy": True,
    "broker_heartbeat_healthy": False,
    "prop_firm_rules_clear": False,
    "emergency_mode_active": False,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_agent_name(agent_name: str) -> str:
    """Return canonical agent name, supporting simple aliases."""
    return AGENT_ALIASES.get(agent_name, agent_name)


def get_agent_policy(agent_name: str) -> AgentPolicy | None:
    """Return policy for an agent if registered."""
    return AGENT_POLICIES.get(normalize_agent_name(agent_name))


def get_tool_policy(tool_name: str) -> ToolPolicy:
    """Return tool policy; unknown tools are forbidden by default."""
    return TOOL_REGISTRY.get(tool_name, _tool_policy(tool_name))


def is_pattern_match(patterns: Sequence[str], value: str) -> bool:
    """Return whether value matches any exact or wildcard pattern."""
    return any(pattern == value or fnmatch(value, pattern) for pattern in patterns)


def get_missing_conditions(
    required_conditions: Sequence[str],
    context: Mapping[str, bool] | None,
) -> tuple[str, ...]:
    """Return required conditions not satisfied by runtime context."""
    merged_context = {**DEFAULT_RUNTIME_CONTEXT, **dict(context or {})}
    return tuple(
        condition
        for condition in required_conditions
        if not merged_context.get(condition, False)
    )


def can_use_tool(
    agent_name: str,
    tool_name: str,
    context: Mapping[str, bool] | None = None,
) -> PermissionDecision:
    """Check whether an agent may call a tool.

    This function never raises. It returns a structured decision.
    Use require_tool_access() if you want a PermissionError on failure.
    """
    canonical_agent = normalize_agent_name(agent_name)
    agent_policy = AGENT_POLICIES.get(canonical_agent)
    tool_policy = get_tool_policy(tool_name)

    if agent_policy is None:
        return PermissionDecision(
            status=DecisionStatus.BLOCKED,
            agent_name=canonical_agent,
            tool_name=tool_name,
            reason="unknown_agent_denied_by_default",
            approval_required=tool_policy.approval,
            audit_required=True,
        )

    if tool_policy.permission_class == PermissionClass.FORBIDDEN:
        return PermissionDecision(
            status=DecisionStatus.BLOCKED,
            agent_name=canonical_agent,
            tool_name=tool_name,
            reason="tool_is_forbidden_or_unknown",
            approval_required=ApprovalType.FORBIDDEN,
            audit_required=True,
        )

    if tool_name in agent_policy.forbidden_tools or is_pattern_match(
        tuple(agent_policy.forbidden_tools), tool_name
    ):
        return PermissionDecision(
            status=DecisionStatus.BLOCKED,
            agent_name=canonical_agent,
            tool_name=tool_name,
            reason="tool_explicitly_forbidden_for_agent",
            approval_required=tool_policy.approval,
            audit_required=True,
        )

    if tool_name not in agent_policy.allowed_tools:
        return PermissionDecision(
            status=DecisionStatus.BLOCKED,
            agent_name=canonical_agent,
            tool_name=tool_name,
            reason="tool_not_in_agent_allowlist",
            approval_required=tool_policy.approval,
            audit_required=True,
        )

    required_conditions = tuple(
        dict.fromkeys(
            (*agent_policy.required_conditions, *tool_policy.required_conditions)
        )
    )
    missing_conditions = get_missing_conditions(required_conditions, context)

    if missing_conditions:
        return PermissionDecision(
            status=DecisionStatus.BLOCKED,
            agent_name=canonical_agent,
            tool_name=tool_name,
            reason="missing_required_runtime_conditions",
            approval_required=tool_policy.approval,
            audit_required=tool_policy.audit_required,
            missing_conditions=missing_conditions,
        )

    return PermissionDecision(
        status=DecisionStatus.ALLOWED,
        agent_name=canonical_agent,
        tool_name=tool_name,
        reason="allowed",
        approval_required=tool_policy.approval,
        audit_required=tool_policy.audit_required,
    )


def require_tool_access(
    agent_name: str,
    tool_name: str,
    context: Mapping[str, bool] | None = None,
) -> PermissionDecision:
    """Raise PermissionError if an agent may not use a tool."""
    decision = can_use_tool(agent_name, tool_name, context=context)

    if not decision.allowed:
        missing = (
            f" Missing conditions: {', '.join(decision.missing_conditions)}."
            if decision.missing_conditions
            else ""
        )
        raise PermissionError(
            f"Agent '{decision.agent_name}' cannot use tool '{tool_name}': "
            f"{decision.reason}.{missing}"
        )

    return decision


def has_permission(agent_name: str, permission: str) -> bool:
    """Backward-compatible high-level permission helper."""
    policy = get_agent_policy(agent_name)

    if policy is None:
        return False

    if permission == "can_trade_live":
        return policy.can_trade_live
    if permission == "can_place_paper_orders":
        return policy.can_place_paper_orders
    if permission == "can_run_backtest":
        return policy.can_run_backtest
    if permission == "can_modify_risk":
        return policy.can_modify_risk

    return False


def require_permission(agent_name: str, permission: str) -> None:
    """Raise when an agent does not have a named high-level permission."""
    if not has_permission(agent_name, permission):
        raise PermissionError(
            f"Agent '{normalize_agent_name(agent_name)}' does not have permission '{permission}'."
        )


def list_allowed_tools(agent_name: str) -> list[str]:
    """Return sorted allowed tools for an agent."""
    policy = get_agent_policy(agent_name)
    if policy is None:
        return []
    return sorted(policy.allowed_tools)


def list_registered_agents() -> list[str]:
    """Return registered canonical agent names."""
    return sorted(AGENT_POLICIES)


def list_registered_tools() -> list[str]:
    """Return registered tool names."""
    return sorted(TOOL_REGISTRY)


def validate_agent_tool_map() -> dict[str, object]:
    """Validate that all allowed/forbidden tools are registered.

    Returns a report instead of raising to make it easy to use in tests.
    """
    registered_tools = set(TOOL_REGISTRY)
    missing: dict[str, list[str]] = {}

    for agent_name, policy in AGENT_POLICIES.items():
        referenced = set(policy.allowed_tools) | {
            tool for tool in policy.forbidden_tools if "*" not in tool
        }
        unknown = sorted(tool for tool in referenced if tool not in registered_tools)
        if unknown:
            missing[agent_name] = unknown

    return {
        "valid": not missing,
        "missing_tools_by_agent": missing,
        "agent_count": len(AGENT_POLICIES),
        "tool_count": len(TOOL_REGISTRY),
    }


def approval_required_for_tool(tool_name: str) -> ApprovalType:
    """Return approval requirement for a tool."""
    return get_tool_policy(tool_name).approval


def audit_required_for_tool(tool_name: str) -> bool:
    """Return whether a tool requires audit logging."""
    return get_tool_policy(tool_name).audit_required
