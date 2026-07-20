"""Agent-facing execution readiness tools.

Purpose:
    Provide deterministic tools for validating execution requests, runtime
    environments, order sizing, pricing, stop-loss/take-profit relationships,
    cost estimates, slippage estimates, and execution-plan construction.

Classes and functions:
    run_execution_readiness_check: Function. Evaluate readiness check results.
    validate_order_request: Function. Validate a proposed order request.
    validate_strategy_runtime_config: Function. Package strategy runtime config validation.
    validate_broker_symbol_mapping: Function. Package broker symbol mapping validation.
    validate_execution_environment: Function. Validate target execution environment.
    validate_order_size: Function. Validate proposed order volume.
    validate_order_price: Function. Validate proposed order price.
    validate_stop_loss_take_profit: Function. Validate SL/TP placement.
    estimate_transaction_cost: Function. Estimate total transaction cost.
    estimate_slippage: Function. Estimate expected slippage.
    build_execution_plan: Function. Build a deterministic execution plan.
"""

from __future__ import annotations

from typing import Any

from ._common import (
    execution_tool_context,
    execution_tool_result,
    package_execution_request,
)


def validate_order_request(**kwargs: Any) -> dict[str, Any]:
    """Validate a proposed order request before execution planning.

    Purpose:
        Confirm the minimum fields needed to submit or simulate an order.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        risk_governor_required

    Side effects:
        None.

    Inputs:
        strategy_id: Strategy requesting execution.
        symbol: Trading symbol.
        side: Order side, either buy or sell.
        volume: Proposed order volume.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, validate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    required = ["strategy_id", "symbol", "side", "volume"]
    missing = [key for key in required if not kwargs.get(key)]
    errors = [f"missing required fields: {missing}"] if missing else []
    side = str(kwargs.get("side", "")).lower()
    if side and side not in {"buy", "sell"}:
        errors.append("side must be buy or sell")
    if float(kwargs.get("volume", 0.0) or 0.0) <= 0:
        errors.append("volume must be greater than 0")
    return execution_tool_result(
        "validate_order_request",
        status="rejected" if errors else "success",
        data={"valid": not errors},
        errors=errors,
        **execution_tool_context(kwargs),
    )


def validate_execution_environment(**kwargs: Any) -> dict[str, Any]:
    """Validate that execution is targeting an allowed environment.

    Purpose:
        Fail closed when an execution request targets an unsupported runtime.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        risk_governor_required

    Side effects:
        None.

    Inputs:
        target_environment: Target execution environment.
        environment: Calling runtime environment.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, validate only.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    target_environment = kwargs.get("target_environment") or kwargs.get(
        "environment", "development"
    )
    allowed = {"test", "paper", "live"}
    valid = target_environment in allowed
    return execution_tool_result(
        "validate_execution_environment",
        status="success" if valid else "blocked",
        data={"valid": valid, "target_environment": target_environment},
        errors=[] if valid else ["execution environment is not allowed"],
        **execution_tool_context(kwargs),
    )


def _check_positive(name: str, field: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Validate that a numeric execution field is positive."""
    value = float(kwargs.get(field, 0.0) or 0.0)
    valid = value > 0
    return execution_tool_result(
        name,
        status="success" if valid else "rejected",
        data={"valid": valid, field: value},
        errors=[] if valid else [f"{field} must be greater than 0"],
        **execution_tool_context(kwargs),
    )


def validate_order_size(**kwargs: Any) -> dict[str, Any]:
    """Validate that proposed order volume is positive.

    Purpose:
        Reject non-positive order volume before broker validation.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        risk_governor_required

    Side effects:
        None.

    Inputs:
        volume: Proposed order volume.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, validate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _check_positive("validate_order_size", "volume", kwargs)


def validate_order_price(**kwargs: Any) -> dict[str, Any]:
    """Validate that proposed order price is positive.

    Purpose:
        Reject non-positive order price before broker validation.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        risk_governor_required

    Side effects:
        None.

    Inputs:
        price: Proposed order price.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, validate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _check_positive("validate_order_price", "price", kwargs)


def validate_stop_loss_take_profit(**kwargs: Any) -> dict[str, Any]:
    """Validate stop-loss and take-profit placement relative to side and price.

    Purpose:
        Reject SL/TP values that are directionally invalid for the order side.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        risk_governor_required

    Side effects:
        None.

    Inputs:
        side: Order side, either buy or sell.
        price: Proposed order price.
        stop_loss: Optional stop-loss price.
        take_profit: Optional take-profit price.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, validate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    side = str(kwargs.get("side", "")).lower()
    price = float(kwargs.get("price", 0.0) or 0.0)
    stop_loss = kwargs.get("stop_loss")
    take_profit = kwargs.get("take_profit")
    errors: list[str] = []
    if side == "buy":
        if stop_loss is not None and float(stop_loss) >= price:
            errors.append("buy stop_loss must be below price")
        if take_profit is not None and float(take_profit) <= price:
            errors.append("buy take_profit must be above price")
    if side == "sell":
        if stop_loss is not None and float(stop_loss) <= price:
            errors.append("sell stop_loss must be above price")
        if take_profit is not None and float(take_profit) >= price:
            errors.append("sell take_profit must be below price")
    return execution_tool_result(
        "validate_stop_loss_take_profit",
        status="rejected" if errors else "success",
        data={"valid": not errors},
        errors=errors,
        **execution_tool_context(kwargs),
    )


def estimate_transaction_cost(**kwargs: Any) -> dict[str, Any]:
    """Estimate spread, commission, and slippage cost.

    Purpose:
        Produce a deterministic transaction-cost estimate for readiness and
        planning workflows.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        spread_cost: Estimated spread cost.
        commission: Estimated commission.
        slippage: Estimated slippage cost.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, simulate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    spread = float(kwargs.get("spread_cost", 0.0) or 0.0)
    commission = float(kwargs.get("commission", 0.0) or 0.0)
    slippage = float(kwargs.get("slippage", 0.0) or 0.0)
    return execution_tool_result(
        "estimate_transaction_cost",
        data={
            "total_cost": spread + commission + slippage,
            "spread_cost": spread,
            "commission": commission,
            "slippage": slippage,
        },
        risk_level="low",
        approval_required="none",
        **execution_tool_context(kwargs),
    )


def estimate_slippage(**kwargs: Any) -> dict[str, Any]:
    """Estimate expected slippage from spread and volatility.

    Purpose:
        Provide a deterministic slippage estimate for execution planning.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        spread: Current or expected spread.
        volatility: Current or expected volatility proxy.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, simulate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    spread = float(kwargs.get("spread", 0.0) or 0.0)
    volatility = float(kwargs.get("volatility", 0.0) or 0.0)
    return execution_tool_result(
        "estimate_slippage",
        data={"estimated_slippage": max(0.0, spread * 0.25 + volatility * 0.1)},
        risk_level="low",
        approval_required="none",
        **execution_tool_context(kwargs),
    )


def build_execution_plan(**kwargs: Any) -> dict[str, Any]:
    """Build a deterministic execution plan from a validated order request.

    Purpose:
        Convert an order request into the bounded plan shape used by execution
        agents.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        risk_governor_required

    Side effects:
        None.

    Inputs:
        strategy_id: Strategy requesting execution.
        symbol: Trading symbol.
        side: Order side.
        volume: Proposed order volume.
        price: Optional proposed price.
        stop_loss: Optional stop-loss price.
        take_profit: Optional take-profit price.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, build plan only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    validation = validate_order_request(**kwargs)
    if validation["status"] != "success":
        validation["tool_name"] = "build_execution_plan"
        return validation
    plan = {
        key: kwargs.get(key)
        for key in [
            "strategy_id",
            "symbol",
            "side",
            "volume",
            "price",
            "stop_loss",
            "take_profit",
        ]
    }
    return execution_tool_result(
        "build_execution_plan",
        data={"execution_plan": plan},
        **execution_tool_context(kwargs),
    )


def run_execution_readiness_check(**kwargs: Any) -> dict[str, Any]:
    """Evaluate a list of readiness checks before execution.

    Purpose:
        Fail closed when any supplied readiness check is not passed.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        risk_governor_required

    Side effects:
        None.

    Inputs:
        checks: Iterable of readiness check dictionaries with passed booleans.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, validate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    checks = kwargs.get("checks") or []
    failed = [check for check in checks if not bool(check.get("passed", False))]
    return execution_tool_result(
        "run_execution_readiness_check",
        status="blocked" if failed else "success",
        data={"passed": not failed, "failed_checks": failed},
        errors=["execution readiness failed"] if failed else [],
        **execution_tool_context(kwargs),
    )


def validate_strategy_runtime_config(**kwargs: Any) -> dict[str, Any]:
    """Validate a strategy runtime config request.

    Purpose:
        Package strategy runtime config validation for execution readiness.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None.

    Inputs:
        strategy_id: Optional strategy identifier.
        config: Optional runtime config payload.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, validate and package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("validate_strategy_runtime_config", kwargs)


def validate_broker_symbol_mapping(**kwargs: Any) -> dict[str, Any]:
    """Validate internal symbol to broker symbol mapping.

    Purpose:
        Package broker-symbol mapping validation for execution readiness.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None.

    Inputs:
        symbol: Internal symbol.
        broker_symbol: Broker-native symbol.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, validate and package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("validate_broker_symbol_mapping", kwargs)


__all__ = [
    "build_execution_plan",
    "estimate_slippage",
    "estimate_transaction_cost",
    "run_execution_readiness_check",
    "validate_broker_symbol_mapping",
    "validate_execution_environment",
    "validate_order_price",
    "validate_order_request",
    "validate_order_size",
    "validate_stop_loss_take_profit",
    "validate_strategy_runtime_config",
]
