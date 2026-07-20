"""Allocation and position sizing tool functions for the risk service.

Purpose:
    Provide deterministic sizing and allocation proposal tools that do not
    mutate live or paper portfolio state.

Functions:
    calculate_fixed_fractional_size: Size a position from account risk.
    calculate_volatility_adjusted_size: Scale size by volatility.
    calculate_risk_parity_weights: Build inverse-volatility risk parity weights.
    calculate_correlation_adjusted_size: Reduce size by correlation pressure.
    calculate_margin_aware_size: Cap size by available margin.
    calculate_cost_adjusted_size: Reduce size for estimated transaction costs.
    calculate_max_safe_position_size: Return the minimum of sizing constraints.
    propose_strategy_allocation: Build a strategy allocation proposal.
    rebalance_strategy_allocations: Normalize desired allocation weights.
    validate_allocation_proposal: Validate allocation weights against policy.
"""

from __future__ import annotations

from typing import Any

from app.services.risk._common import risk_tool_result


def calculate_fixed_fractional_size(
    *,
    equity: float,
    risk_fraction: float,
    stop_loss_value: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate position size from fixed fractional account risk.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        equity: Account equity.
        risk_fraction: Fraction of equity to risk.
        stop_loss_value: Cash risk per one unit.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    errors = []
    if equity <= 0:
        errors.append("equity must be greater than 0")
    if risk_fraction < 0:
        errors.append("risk_fraction must be non-negative")
    if stop_loss_value <= 0:
        errors.append("stop_loss_value must be greater than 0")
    if errors:
        return risk_tool_result(
            "calculate_fixed_fractional_size",
            status="rejected",
            data=None,
            errors=errors,
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )
    size = float(equity) * float(risk_fraction) / float(stop_loss_value)
    return risk_tool_result(
        "calculate_fixed_fractional_size",
        data={
            "position_size": size,
            "risk_amount": float(equity) * float(risk_fraction),
        },
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def calculate_volatility_adjusted_size(
    *,
    base_size: float,
    target_volatility: float,
    observed_volatility: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Scale position size by target-to-observed volatility ratio.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        base_size: Unadjusted position size.
        target_volatility: Desired volatility.
        observed_volatility: Current observed volatility.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    adjusted = (
        0.0
        if observed_volatility <= 0
        else float(base_size) * float(target_volatility) / float(observed_volatility)
    )
    return risk_tool_result(
        "calculate_volatility_adjusted_size",
        data={"position_size": adjusted},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def calculate_risk_parity_weights(
    *,
    volatilities: dict[str, float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate inverse-volatility risk parity weights.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        volatilities: Mapping of asset or strategy ID to volatility.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    inverse = {
        key: 1.0 / float(value)
        for key, value in volatilities.items()
        if float(value) > 0
    }
    total = sum(inverse.values())
    weights = {key: value / total if total else 0.0 for key, value in inverse.items()}
    return risk_tool_result(
        "calculate_risk_parity_weights",
        data={"weights": weights},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def calculate_correlation_adjusted_size(
    *,
    base_size: float,
    max_correlation: float,
    correlation_limit: float = 0.8,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Reduce size when correlation exceeds the policy threshold.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        base_size: Unadjusted position size.
        max_correlation: Highest relevant portfolio correlation.
        correlation_limit: Threshold above which size is reduced.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    pressure = max(0.0, abs(float(max_correlation)) - abs(float(correlation_limit)))
    adjusted = max(0.0, float(base_size) * (1.0 - pressure))
    return risk_tool_result(
        "calculate_correlation_adjusted_size",
        data={"position_size": adjusted, "correlation_pressure": pressure},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def calculate_margin_aware_size(
    *,
    desired_size: float,
    free_margin: float,
    margin_per_unit: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Cap desired size by available free margin.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        desired_size: Requested position size.
        free_margin: Available account margin.
        margin_per_unit: Margin consumed by one unit.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    max_by_margin = (
        float(free_margin) / float(margin_per_unit) if margin_per_unit > 0 else 0.0
    )
    return risk_tool_result(
        "calculate_margin_aware_size",
        data={
            "position_size": min(float(desired_size), max_by_margin),
            "max_by_margin": max_by_margin,
        },
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def calculate_cost_adjusted_size(
    *,
    desired_size: float,
    transaction_cost_fraction: float,
    max_cost_fraction: float = 0.02,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Reduce desired size when transaction cost exceeds policy tolerance.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        desired_size: Requested position size.
        transaction_cost_fraction: Estimated cost fraction.
        max_cost_fraction: Cost tolerance before size reduction.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    excess = max(0.0, float(transaction_cost_fraction) - float(max_cost_fraction))
    adjusted = max(0.0, float(desired_size) * (1.0 - excess))
    return risk_tool_result(
        "calculate_cost_adjusted_size",
        data={"position_size": adjusted, "cost_excess": excess},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def calculate_max_safe_position_size(
    *,
    candidate_sizes: dict[str, float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Return the most restrictive non-negative position size.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        candidate_sizes: Mapping of constraint name to proposed maximum size.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    safe_values = [max(0.0, float(value)) for value in candidate_sizes.values()]
    safe_size = min(safe_values) if safe_values else 0.0
    return risk_tool_result(
        "calculate_max_safe_position_size",
        data={"position_size": safe_size, "constraints": candidate_sizes},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def propose_strategy_allocation(
    *,
    scores: dict[str, float],
    max_weight: float = 0.4,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a normalized strategy allocation proposal from scores.

    Tool class:
        write_controlled
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal proposal payload only.
    Inputs:
        scores: Mapping of strategy ID to non-negative score.
        max_weight: Maximum allowed strategy weight.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    positive = {key: max(0.0, float(value)) for key, value in scores.items()}
    total = sum(positive.values())
    raw = {key: value / total if total else 0.0 for key, value in positive.items()}
    capped = {key: min(float(max_weight), value) for key, value in raw.items()}
    capped_total = sum(capped.values())
    proposal = {
        key: value / capped_total if capped_total else 0.0
        for key, value in capped.items()
    }
    return risk_tool_result(
        "propose_strategy_allocation",
        data={"proposal": proposal},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        side_effects=[] if dry_run else ["created_allocation_proposal"],
    )


def rebalance_strategy_allocations(
    *,
    target_allocations: dict[str, float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Normalize target strategy allocations for a rebalance proposal.

    Tool class:
        write_controlled
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal rebalance proposal.
    Inputs:
        target_allocations: Mapping of strategy ID to desired weight.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    cleaned = {key: max(0.0, float(value)) for key, value in target_allocations.items()}
    total = sum(cleaned.values())
    normalized = {
        key: value / total if total else 0.0 for key, value in cleaned.items()
    }
    return risk_tool_result(
        "rebalance_strategy_allocations",
        data={"normalized_allocations": normalized},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        side_effects=[] if dry_run else ["created_rebalance_proposal"],
    )


def validate_allocation_proposal(
    *,
    allocations: dict[str, float],
    max_weight: float = 0.4,
    tolerance: float = 0.000001,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Validate allocation weights against sum and max-weight policy.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        allocations: Mapping of strategy ID to proposed allocation weight.
        max_weight: Maximum allowed single-strategy weight.
        tolerance: Allowed deviation from total weight of 1.0.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    total = sum(float(value) for value in allocations.values())
    errors = []
    if abs(total - 1.0) > float(tolerance):
        errors.append("allocation weights must sum to 1.0")
    oversized = {
        key: value
        for key, value in allocations.items()
        if float(value) > float(max_weight)
    }
    if oversized:
        errors.append("one or more allocation weights exceed max_weight")
    return risk_tool_result(
        "validate_allocation_proposal",
        status="success" if not errors else "rejected",
        data={"valid": not errors, "total_weight": total, "oversized": oversized},
        errors=errors,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


__all__ = [
    "calculate_correlation_adjusted_size",
    "calculate_cost_adjusted_size",
    "calculate_fixed_fractional_size",
    "calculate_margin_aware_size",
    "calculate_max_safe_position_size",
    "calculate_risk_parity_weights",
    "calculate_volatility_adjusted_size",
    "propose_strategy_allocation",
    "rebalance_strategy_allocations",
    "validate_allocation_proposal",
]
