"""Official risk tool registry and validation.

Defines the approved risk tool metadata contracts and catalog.
"""

from __future__ import annotations

from typing import Any, Literal

from app.services.risk.models import RiskContract
from app.services.risk.validations import ValidationResult, _fail, _ok
from pydantic import Field


class RiskToolDefinition(RiskContract):
    """Immutable official risk tool metadata."""

    name: str = Field(..., description="Unique tool name.")
    description: str = Field(..., description="Tool description.")
    request_schema: dict[str, Any] = Field(
        default_factory=dict, description="Expected JSON Schema for input."
    )
    response_schema: dict[str, Any] = Field(
        default_factory=dict, description="Expected JSON Schema for output."
    )
    places_trade: bool = Field(
        default=False, description="Whether the tool places live trades."
    )
    read_only: bool = Field(default=True, description="Whether the tool is read-only.")
    writes_file: bool = Field(
        default=False, description="Whether the tool writes files."
    )
    modifies_database: bool = Field(
        default=False, description="Whether the tool modifies state database."
    )
    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        default="low", description="Risk level classification."
    )


class RiskToolRegistry(RiskContract):
    """Catalog of approved risk tools."""

    tools: dict[str, RiskToolDefinition] = Field(
        default_factory=dict, description="Approved risk tool map."
    )


def validate_risk_tool_metadata(definition: RiskToolDefinition) -> ValidationResult:  # noqa: C901, PLR0911, PLR0912
    """Verifies that the side effects and security metadata of a tool are accurate.

    Args:
        definition: The risk tool definition to validate.

    Returns:
        ValidationResult: The validation outcome.
    """
    if definition.places_trade:
        return _fail(
            f"Tool '{definition.name}' has places_trade=True "
            "which is strictly forbidden.",
            code="INVALID_METADATA",
            details={"places_trade": definition.places_trade},
        )

    name = definition.name
    # Rules for generate_risk_report_tool
    if name == "generate_risk_report_tool":
        if not definition.writes_file:
            return _fail(
                f"Tool '{name}' must have writes_file=True.",
                code="INVALID_METADATA",
                details={"writes_file": definition.writes_file},
            )
        if definition.read_only:
            return _fail(
                f"Tool '{name}' must have read_only=False.",
                code="INVALID_METADATA",
                details={"read_only": definition.read_only},
            )
        if definition.modifies_database:
            return _fail(
                f"Tool '{name}' must have modifies_database=False.",
                code="INVALID_METADATA",
                details={"modifies_database": definition.modifies_database},
            )
        return _ok()

    # Rules for database-modifying (audit-writing) tools
    audit_writing_tools = {
        "review_trade_risk_tool",
        "review_strategy_admission_tool",
        "review_allocation_proposal_tool",
        "run_portfolio_risk_governor_tool",
    }
    if name in audit_writing_tools:
        if not definition.modifies_database:
            return _fail(
                f"Tool '{name}' must have modifies_database=True.",
                code="INVALID_METADATA",
                details={"modifies_database": definition.modifies_database},
            )
        if definition.read_only:
            return _fail(
                f"Tool '{name}' must have read_only=False.",
                code="INVALID_METADATA",
                details={"read_only": definition.read_only},
            )
        if definition.writes_file:
            return _fail(
                f"Tool '{name}' must have writes_file=False.",
                code="INVALID_METADATA",
                details={"writes_file": definition.writes_file},
            )
        return _ok()

    # Rules for read-only tools
    read_only_tools = {
        "build_portfolio_risk_snapshot_tool",
        "calculate_position_size_tool",
        "assess_risk_regime_tool",
        "validate_risk_approval_token_tool",
        "check_risk_kill_switch_tool",
        "run_risk_scenario_analysis_tool",
    }
    if name in read_only_tools:
        if not definition.read_only:
            return _fail(
                f"Tool '{name}' must be read_only=True.",
                code="INVALID_METADATA",
                details={"read_only": definition.read_only},
            )
        if definition.writes_file:
            return _fail(
                f"Tool '{name}' must have writes_file=False.",
                code="INVALID_METADATA",
                details={"writes_file": definition.writes_file},
            )
        if definition.modifies_database:
            return _fail(
                f"Tool '{name}' must have modifies_database=False.",
                code="INVALID_METADATA",
                details={"modifies_database": definition.modifies_database},
            )
        return _ok()

    # For any unrecognized tool, perform fallback basic validation:
    return _ok()


def build_risk_tool_registry() -> RiskToolRegistry:
    """Builds and returns the official, immutable risk tool catalog.

    Returns:
        RiskToolRegistry: Catalog of approved risk tools.
    """
    tools = {}

    # 1. build_portfolio_risk_snapshot_tool
    tools["build_portfolio_risk_snapshot_tool"] = RiskToolDefinition(
        name="build_portfolio_risk_snapshot_tool",
        description="Compiles an active portfolio risk snapshot and exposure metrics.",
        places_trade=False,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        risk_level="low",
    )

    # 2. review_trade_risk_tool
    tools["review_trade_risk_tool"] = RiskToolDefinition(
        name="review_trade_risk_tool",
        description="Checks proposed trade against active policy rules.",
        places_trade=False,
        read_only=False,
        writes_file=False,
        modifies_database=True,
        risk_level="high",
    )

    # 3. calculate_position_size_tool
    tools["calculate_position_size_tool"] = RiskToolDefinition(
        name="calculate_position_size_tool",
        description="Calculates policy-bounded volume for proposed position.",
        places_trade=False,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        risk_level="low",
    )

    # 4. assess_risk_regime_tool
    tools["assess_risk_regime_tool"] = RiskToolDefinition(
        name="assess_risk_regime_tool",
        description="Classifies active market conditions and regime risk status.",
        places_trade=False,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        risk_level="low",
    )

    # 5. review_strategy_admission_tool
    tools["review_strategy_admission_tool"] = RiskToolDefinition(
        name="review_strategy_admission_tool",
        description="Reviews strategy promotion lifecycle stage.",
        places_trade=False,
        read_only=False,
        writes_file=False,
        modifies_database=True,
        risk_level="medium",
    )

    # 6. review_allocation_proposal_tool
    tools["review_allocation_proposal_tool"] = RiskToolDefinition(
        name="review_allocation_proposal_tool",
        description="Reviews dynamic capital allocation adjustments.",
        places_trade=False,
        read_only=False,
        writes_file=False,
        modifies_database=True,
        risk_level="high",
    )

    # 7. run_portfolio_risk_governor_tool
    tools["run_portfolio_risk_governor_tool"] = RiskToolDefinition(
        name="run_portfolio_risk_governor_tool",
        description="Executes portfolio risk governor validation loop.",
        places_trade=False,
        read_only=False,
        writes_file=False,
        modifies_database=True,
        risk_level="critical",
    )

    # 8. validate_risk_approval_token_tool
    tools["validate_risk_approval_token_tool"] = RiskToolDefinition(
        name="validate_risk_approval_token_tool",
        description="Verifies the authenticity and state of an approval token.",
        places_trade=False,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        risk_level="medium",
    )

    # 9. check_risk_kill_switch_tool
    tools["check_risk_kill_switch_tool"] = RiskToolDefinition(
        name="check_risk_kill_switch_tool",
        description="Queries active global/portfolio/strategy kill switch status.",
        places_trade=False,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        risk_level="medium",
    )

    # 10. run_risk_scenario_analysis_tool
    tools["run_risk_scenario_analysis_tool"] = RiskToolDefinition(
        name="run_risk_scenario_analysis_tool",
        description="Runs stress scenario analysis against portfolio models.",
        places_trade=False,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        risk_level="high",
    )

    # 11. generate_risk_report_tool
    tools["generate_risk_report_tool"] = RiskToolDefinition(
        name="generate_risk_report_tool",
        description="Generates standard and redacted risk reports.",
        places_trade=False,
        read_only=False,
        writes_file=True,
        modifies_database=False,
        risk_level="medium",
    )

    # Validate all definitions upon registry build
    for definition in tools.values():
        res = validate_risk_tool_metadata(definition)
        if not res["valid"]:
            msg = f"Invalid tool definition metadata: {res['message']}"
            raise ValueError(msg)

    return RiskToolRegistry(tools=tools)


def list_risk_tools(registry: RiskToolRegistry) -> tuple[RiskToolDefinition, ...]:
    """Exposes deterministic public tool metadata.

    Args:
        registry: The active risk tool registry.

    Returns:
        tuple[RiskToolDefinition, ...]: Deterministic list of definitions.
    """
    return tuple(sorted(registry.tools.values(), key=lambda t: t.name))


def get_risk_tool_definition(
    name: str, registry: RiskToolRegistry
) -> RiskToolDefinition:
    """Resolves an approved tool metadata definition.

    Args:
        name: The tool name.
        registry: The active risk tool registry.

    Returns:
        RiskToolDefinition: Resolved tool definition.

    Raises:
        KeyError: If tool is not registered.
    """
    if name not in registry.tools:
        msg = f"Tool '{name}' not found in registry."
        raise KeyError(msg)
    return registry.tools[name]
