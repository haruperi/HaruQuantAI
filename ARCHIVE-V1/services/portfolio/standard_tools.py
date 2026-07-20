"""Standardized Portfolio Department tools for HaruQuant agents.

Purpose:
    Standardized Portfolio Department tools for HaruQuant agents.

Classes:
    None.

Functions:
    get_open_positions: Public function defined by this module.
    get_open_orders: Public function defined by this module.
    get_strategy_allocations: Public function defined by this module.
    get_portfolio_equity_curve: Public function defined by this module.
    calculate_portfolio_returns: Public function defined by this module.
    calculate_portfolio_volatility: Public function defined by this module.
    calculate_portfolio_correlation: Public function defined by this module.
    calculate_portfolio_var: Public function defined by this module.
    calculate_portfolio_cvar: Public function defined by this module.
    calculate_risk_contribution: Public function defined by this module.
    calculate_margin_usage: Public function defined by this module.
    calculate_currency_exposure: Public function defined by this module.
    detect_strategy_overlap: Public function defined by this module.
    detect_symbol_cluster_risk: Public function defined by this module.
    build_portfolio_risk_snapshot: Public function defined by this module.
    calculate_fixed_fractional_size: Public function defined by this module.
    calculate_volatility_adjusted_size: Public function defined by this module.
    calculate_risk_parity_weights: Public function defined by this module.
    calculate_correlation_adjusted_size: Public function defined by this module.
    calculate_margin_aware_size: Public function defined by this module.
    calculate_cost_adjusted_size: Public function defined by this module.
    calculate_max_safe_position_size: Public function defined by this module.
    propose_strategy_allocation: Public function defined by this module.
    rebalance_strategy_allocations: Public function defined by this module.
    validate_allocation_proposal: Public function defined by this module.
    admit_strategy_to_portfolio: Public function defined by this module.
    promote_strategy_to_paper: Public function defined by this module.
    promote_strategy_to_live_candidate: Public function defined by this module.
    suspend_strategy: Public function defined by this module.
    retire_strategy: Public function defined by this module.
    demote_strategy_to_paper: Public function defined by this module.
    update_strategy_status: Public function defined by this module.
    build_risk_decision_package: Public function defined by this module.
    _result: Internal helper function defined by this module.
    _ctx: Internal helper function defined by this module.
    _business: Internal helper function defined by this module.
    _package: Internal helper function defined by this module.

Notes:
    External-facing exports are collected in app/services/portfolio/__init__.py;
    private underscore helpers remain implementation details.
"""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import Any
from uuid import uuid4

import pandas as pd
from app.services.utils.standard import ToolStandardSpec, standard_tool_response


def _result(
    tool_name: str,
    *,
    status: str = "success",
    data: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
    risk_level: str = "medium",
    approval_required: str = "audit_required",
) -> dict[str, Any]:
    """Internal function for standard_tools._result."""
    _ = agent_name, environment, dry_run, approval_required, uuid4, datetime, timezone
    error_list = errors or []
    normalized_status = "success" if status == "success" and not error_list else "error"
    return standard_tool_response(
        spec=ToolStandardSpec(
            tool_name=tool_name,
            tool_category="portfolio",
            tool_risk_level=risk_level,
            read_only=risk_level == "low",
        ),
        status=normalized_status,
        message=(
            "Portfolio tool executed successfully."
            if normalized_status == "success"
            else "Portfolio tool execution failed."
        ),
        data=data,
        error=None
        if normalized_status == "success"
        else {
            "code": "TOOL_EXECUTION_FAILED",
            "details": "; ".join(error_list) or "Portfolio tool failed.",
        },
        request_id=request_id,
        execution_ms=0.0,
    )


def _ctx(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Internal function for standard_tools._ctx."""
    return {
        "request_id": kwargs.get("request_id"),
        "agent_name": kwargs.get("agent_name"),
        "environment": kwargs.get("environment", "development"),
        "dry_run": kwargs.get("dry_run", True),
    }


def _business(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Internal function for standard_tools._business."""
    return {
        key: value
        for key, value in kwargs.items()
        if key not in {"request_id", "agent_name", "environment", "dry_run"}
    }


def _package(tool_name: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Internal function for standard_tools._package."""
    return _result(
        tool_name,
        data={
            "request": _business(kwargs),
            "created_at": datetime.now(UTC).isoformat(),
        },
        **_ctx(kwargs),
    )


def get_open_positions(**kwargs: Any) -> dict[str, Any]:
    """Return current open positions supplied by the caller/context.

    Purpose:
        Return current open positions supplied by the caller/context.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    positions = kwargs.get("positions") or []
    return _result(
        "get_open_positions",
        data={"positions": positions, "count": len(positions)},
        risk_level="low",
        approval_required="none",
        **_ctx(kwargs),
    )


def get_open_orders(**kwargs: Any) -> dict[str, Any]:
    """Return current open orders supplied by the caller/context.

    Purpose:
        Return current open orders supplied by the caller/context.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    orders = kwargs.get("orders") or []
    return _result(
        "get_open_orders",
        data={"orders": orders, "count": len(orders)},
        risk_level="low",
        approval_required="none",
        **_ctx(kwargs),
    )


def get_strategy_allocations(**kwargs: Any) -> dict[str, Any]:
    """Return current strategy allocation weights.

    Purpose:
        Return current strategy allocation weights.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    allocations = kwargs.get("allocations") or {}
    return _result(
        "get_strategy_allocations",
        data={"allocations": allocations},
        risk_level="low",
        approval_required="none",
        **_ctx(kwargs),
    )


def get_portfolio_equity_curve(**kwargs: Any) -> dict[str, Any]:
    """Return portfolio equity curve from supplied state.

    Purpose:
        Return portfolio equity curve from supplied state.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    equity_curve = kwargs.get("equity_curve") or []
    return _result(
        "get_portfolio_equity_curve",
        data={"equity_curve": equity_curve, "points": len(equity_curve)},
        risk_level="low",
        approval_required="none",
        **_ctx(kwargs),
    )


def calculate_portfolio_returns(**kwargs: Any) -> dict[str, Any]:
    """Calculate portfolio returns from an equity curve.

    Purpose:
        Calculate portfolio returns from an equity curve.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    equity = pd.to_numeric(pd.Series(kwargs.get("equity_curve") or []), errors="coerce")
    returns = equity.dropna().pct_change().dropna().tolist()
    return _result(
        "calculate_portfolio_returns",
        data={"returns": returns},
        risk_level="low",
        approval_required="none",
        **_ctx(kwargs),
    )


def calculate_portfolio_volatility(**kwargs: Any) -> dict[str, Any]:
    """Calculate portfolio return volatility.

    Purpose:
        Calculate portfolio return volatility.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    returns = pd.to_numeric(pd.Series(kwargs.get("returns") or []), errors="coerce")
    returns = returns.dropna()
    volatility = float(returns.std()) if len(returns) else 0.0
    return _result(
        "calculate_portfolio_volatility",
        data={"volatility": volatility},
        risk_level="low",
        approval_required="none",
        **_ctx(kwargs),
    )


def calculate_portfolio_correlation(**kwargs: Any) -> dict[str, Any]:
    """Calculate correlation matrix for portfolio return series.

    Purpose:
        Calculate correlation matrix for portfolio return series.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    frame = pd.DataFrame(kwargs.get("returns_by_asset") or {})
    matrix = frame.corr().fillna(0.0).to_dict() if not frame.empty else {}
    return _result(
        "calculate_portfolio_correlation",
        data={"correlation_matrix": matrix},
        risk_level="low",
        approval_required="none",
        **_ctx(kwargs),
    )


def calculate_portfolio_var(**kwargs: Any) -> dict[str, Any]:
    """Calculate historical portfolio VaR.

    Purpose:
        Calculate historical portfolio VaR.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    returns = pd.to_numeric(pd.Series(kwargs.get("returns") or []), errors="coerce")
    returns = returns.dropna()
    alpha = float(kwargs.get("alpha", 0.05))
    var = float(returns.quantile(alpha)) if len(returns) else 0.0
    return _result("calculate_portfolio_var", data={"var": var}, **_ctx(kwargs))


def calculate_portfolio_cvar(**kwargs: Any) -> dict[str, Any]:
    """Calculate historical portfolio CVaR.

    Purpose:
        Calculate historical portfolio CVaR.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    returns = pd.to_numeric(pd.Series(kwargs.get("returns") or []), errors="coerce")
    returns = returns.dropna()
    alpha = float(kwargs.get("alpha", 0.05))
    var = float(returns.quantile(alpha)) if len(returns) else 0.0
    cvar = (
        float(returns[returns <= var].mean()) if len(returns[returns <= var]) else 0.0
    )
    return _result("calculate_portfolio_cvar", data={"cvar": cvar}, **_ctx(kwargs))


def calculate_risk_contribution(**kwargs: Any) -> dict[str, Any]:
    """Calculate per-strategy or per-symbol risk contribution.

    Purpose:
        Calculate per-strategy or per-symbol risk contribution.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    exposures = kwargs.get("exposures") or {}
    total = sum(abs(float(value)) for value in exposures.values())
    contribution = {
        key: abs(float(value)) / total if total else 0.0
        for key, value in exposures.items()
    }
    return _result(
        "calculate_risk_contribution",
        data={"risk_contribution": contribution},
        **_ctx(kwargs),
    )


def calculate_margin_usage(**kwargs: Any) -> dict[str, Any]:
    """Calculate margin utilization.

    Purpose:
        Calculate margin utilization.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    equity = float(kwargs.get("equity", 0.0) or 0.0)
    used_margin = float(kwargs.get("used_margin", 0.0) or 0.0)
    usage = used_margin / equity if equity else 0.0
    return _result(
        "calculate_margin_usage", data={"margin_usage": usage}, **_ctx(kwargs)
    )


def calculate_currency_exposure(**kwargs: Any) -> dict[str, Any]:
    """Calculate FX currency basket exposure.

    Purpose:
        Calculate FX currency basket exposure.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    positions = kwargs.get("positions") or []
    exposure: dict[str, float] = {}
    for position in positions:
        symbol = str(position.get("symbol", ""))
        notional = float(position.get("notional", 0.0) or 0.0)
        if len(symbol) >= 6:
            exposure[symbol[:3].upper()] = (
                exposure.get(symbol[:3].upper(), 0.0) + notional
            )
            exposure[symbol[3:6].upper()] = (
                exposure.get(symbol[3:6].upper(), 0.0) - notional
            )
    return _result(
        "calculate_currency_exposure",
        data={"currency_exposure": exposure},
        **_ctx(kwargs),
    )


def detect_strategy_overlap(**kwargs: Any) -> dict[str, Any]:
    """Detect duplicate or overlapping strategy symbols/types.

    Purpose:
        Detect duplicate or overlapping strategy symbols/types.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    strategies = kwargs.get("strategies") or []
    seen = set()
    overlaps = []
    for strategy in strategies:
        key = (strategy.get("symbol"), strategy.get("strategy_type"))
        if key in seen:
            overlaps.append(strategy)
        seen.add(key)
    return _result(
        "detect_strategy_overlap",
        data={"overlap_detected": bool(overlaps), "overlaps": overlaps},
        **_ctx(kwargs),
    )


def detect_symbol_cluster_risk(**kwargs: Any) -> dict[str, Any]:
    """Detect concentrated symbol cluster exposure.

    Purpose:
        Detect concentrated symbol cluster exposure.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    exposures = kwargs.get("symbol_exposures") or {}
    total = sum(abs(float(value)) for value in exposures.values())
    threshold = float(kwargs.get("threshold", 0.4))
    clusters = {
        symbol: abs(float(value)) / total
        for symbol, value in exposures.items()
        if total and abs(float(value)) / total > threshold
    }
    return _result(
        "detect_symbol_cluster_risk",
        data={"cluster_risk_detected": bool(clusters), "clusters": clusters},
        **_ctx(kwargs),
    )


def build_portfolio_risk_snapshot(**kwargs: Any) -> dict[str, Any]:
    """Build current portfolio risk package.

    Purpose:
        Build current portfolio risk package.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("build_portfolio_risk_snapshot", kwargs)


def calculate_fixed_fractional_size(**kwargs: Any) -> dict[str, Any]:
    """Calculate fixed fractional position size.

    Purpose:
        Calculate fixed fractional position size.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    equity = float(kwargs.get("equity", 0.0) or 0.0)
    risk_fraction = float(kwargs.get("risk_fraction", 0.01) or 0.01)
    stop_distance = abs(float(kwargs.get("stop_distance", 0.0) or 0.0))
    pip_value = float(kwargs.get("pip_value", 1.0) or 1.0)
    size = (
        equity * risk_fraction / (stop_distance * pip_value) if stop_distance else 0.0
    )
    return _result(
        "calculate_fixed_fractional_size", data={"position_size": size}, **_ctx(kwargs)
    )


def calculate_volatility_adjusted_size(**kwargs: Any) -> dict[str, Any]:
    """Calculate volatility-adjusted position size.

    Purpose:
        Calculate volatility-adjusted position size.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    base_size = float(kwargs.get("base_size", 0.0) or 0.0)
    target_volatility = float(kwargs.get("target_volatility", 1.0) or 1.0)
    observed_volatility = float(kwargs.get("observed_volatility", 1.0) or 1.0)
    size = (
        base_size * target_volatility / observed_volatility
        if observed_volatility
        else 0.0
    )
    return _result(
        "calculate_volatility_adjusted_size",
        data={"position_size": size},
        **_ctx(kwargs),
    )


def calculate_risk_parity_weights(**kwargs: Any) -> dict[str, Any]:
    """Calculate inverse-volatility risk parity weights.

    Purpose:
        Calculate inverse-volatility risk parity weights.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    volatilities = kwargs.get("volatilities") or {}
    inverse = {
        key: 1.0 / float(value)
        for key, value in volatilities.items()
        if float(value) > 0
    }
    total = sum(inverse.values())
    weights = {key: value / total if total else 0.0 for key, value in inverse.items()}
    return _result(
        "calculate_risk_parity_weights", data={"weights": weights}, **_ctx(kwargs)
    )


def calculate_correlation_adjusted_size(**kwargs: Any) -> dict[str, Any]:
    """Reduce size for correlated exposure.

    Purpose:
        Reduce size for correlated exposure.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    base_size = float(kwargs.get("base_size", 0.0) or 0.0)
    correlation = min(1.0, max(0.0, abs(float(kwargs.get("correlation", 0.0) or 0.0))))
    return _result(
        "calculate_correlation_adjusted_size",
        data={"position_size": base_size * (1.0 - correlation)},
        **_ctx(kwargs),
    )


def calculate_margin_aware_size(**kwargs: Any) -> dict[str, Any]:
    """Calculate broker margin-aware size.

    Purpose:
        Calculate broker margin-aware size.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    requested_size = float(kwargs.get("requested_size", 0.0) or 0.0)
    free_margin = float(kwargs.get("free_margin", 0.0) or 0.0)
    margin_per_unit = float(kwargs.get("margin_per_unit", 1.0) or 1.0)
    max_size = free_margin / margin_per_unit if margin_per_unit else 0.0
    return _result(
        "calculate_margin_aware_size",
        data={"position_size": min(requested_size, max_size), "max_size": max_size},
        **_ctx(kwargs),
    )


def calculate_cost_adjusted_size(**kwargs: Any) -> dict[str, Any]:
    """Calculate cost-aware size.

    Purpose:
        Calculate cost-aware size.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    base_size = float(kwargs.get("base_size", 0.0) or 0.0)
    cost_ratio = min(1.0, max(0.0, float(kwargs.get("cost_ratio", 0.0) or 0.0)))
    return _result(
        "calculate_cost_adjusted_size",
        data={"position_size": base_size * (1.0 - cost_ratio)},
        **_ctx(kwargs),
    )


def calculate_max_safe_position_size(**kwargs: Any) -> dict[str, Any]:
    """Calculate hard-cap position size.

    Purpose:
        Calculate hard-cap position size.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    candidates = [
        float(kwargs.get("risk_size", 0.0) or 0.0),
        float(kwargs.get("margin_size", 0.0) or 0.0),
        float(kwargs.get("policy_cap", 0.0) or 0.0),
    ]
    positive = [value for value in candidates if value > 0]
    return _result(
        "calculate_max_safe_position_size",
        data={"position_size": min(positive) if positive else 0.0},
        **_ctx(kwargs),
    )


def propose_strategy_allocation(**kwargs: Any) -> dict[str, Any]:
    """Propose strategy capital allocation.

    Purpose:
        Propose strategy capital allocation.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("propose_strategy_allocation", kwargs)


def rebalance_strategy_allocations(**kwargs: Any) -> dict[str, Any]:
    """Rebalance strategy allocation weights.

    Purpose:
        Rebalance strategy allocation weights.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("rebalance_strategy_allocations", kwargs)


def validate_allocation_proposal(**kwargs: Any) -> dict[str, Any]:
    """Check allocation proposal against policy.

    Purpose:
        Check allocation proposal against policy.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; reads supplied state or calculates derived metrics only.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    weights = kwargs.get("weights") or {}
    total = sum(float(value) for value in weights.values())
    max_weight = max([float(value) for value in weights.values()] or [0.0])
    max_allowed = float(kwargs.get("max_weight", 1.0))
    errors = []
    if abs(total - 1.0) > 0.001:
        errors.append("allocation weights must sum to 1.0")
    if max_weight > max_allowed:
        errors.append("allocation exceeds max_weight")
    return _result(
        "validate_allocation_proposal",
        status="rejected" if errors else "success",
        data={"valid": not errors, "total_weight": total, "max_weight": max_weight},
        errors=errors,
        **_ctx(kwargs),
    )


def admit_strategy_to_portfolio(**kwargs: Any) -> dict[str, Any]:
    """Add a strategy candidate to portfolio.

    Purpose:
        Add a strategy candidate to portfolio.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("admit_strategy_to_portfolio", kwargs)


def promote_strategy_to_paper(**kwargs: Any) -> dict[str, Any]:
    """Move a strategy to paper trading.

    Purpose:
        Move a strategy to paper trading.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("promote_strategy_to_paper", kwargs)


def promote_strategy_to_live_candidate(**kwargs: Any) -> dict[str, Any]:
    """Prepare a strategy for live approval.

    Purpose:
        Prepare a strategy for live approval.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("promote_strategy_to_live_candidate", kwargs)


def suspend_strategy(**kwargs: Any) -> dict[str, Any]:
    """Temporarily pause a strategy.

    Purpose:
        Temporarily pause a strategy.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("suspend_strategy", kwargs)


def retire_strategy(**kwargs: Any) -> dict[str, Any]:
    """Remove a strategy from active portfolio.

    Purpose:
        Remove a strategy from active portfolio.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("retire_strategy", kwargs)


def demote_strategy_to_paper(**kwargs: Any) -> dict[str, Any]:
    """Demote a live strategy to paper trading.

    Purpose:
        Demote a live strategy to paper trading.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("demote_strategy_to_paper", kwargs)


def update_strategy_status(**kwargs: Any) -> dict[str, Any]:
    """Update portfolio strategy lifecycle status.

    Purpose:
        Update portfolio strategy lifecycle status.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("update_strategy_status", kwargs)


def build_risk_decision_package(**kwargs: Any) -> dict[str, Any]:
    """Build final risk decision package.

    Purpose:
        Build final risk decision package.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        Packages a portfolio lifecycle/allocation decision request; no durable state is changed by this helper.

    Inputs:
        Accepts keyword arguments for business inputs plus optional request_id,
        agent_name, dry_run, and environment controls.

    Returns:
        Standard HaruQuant tool result dictionary with status, tool_name,
        tool_call_id, request_id, agent_name, environment, dry_run, data,
        errors, warnings, and audit metadata.

    Raises:
        Avoids raising for normal validation failures; returns rejected, blocked,
        or failed status in the result envelope instead.
    """
    return _package("build_risk_decision_package", kwargs)
