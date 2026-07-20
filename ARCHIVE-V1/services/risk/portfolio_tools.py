"""Portfolio analytics tool functions for the risk service.

Purpose:
    Provide deterministic read-only portfolio state and analytics tools.

Functions:
    get_open_positions: Return supplied open position records.
    get_open_orders: Return supplied open order records.
    get_strategy_allocations: Return supplied strategy allocations.
    get_portfolio_equity_curve: Return supplied portfolio equity curve.
    calculate_portfolio_returns: Calculate period returns from an equity curve.
    calculate_portfolio_volatility: Calculate volatility from returns.
    calculate_portfolio_correlation: Calculate an asset return correlation matrix.
    calculate_portfolio_var: Calculate historical portfolio VaR.
    calculate_portfolio_cvar: Calculate historical portfolio CVaR.
    calculate_risk_contribution: Calculate normalized exposure contribution.
    calculate_margin_usage: Calculate used-margin fraction.
    calculate_currency_exposure: Calculate FX base/quote currency exposure.
    detect_strategy_overlap: Detect duplicated symbols between strategies.
    detect_symbol_cluster_risk: Detect over-concentrated symbol clusters.
    build_portfolio_risk_snapshot: Build a structured portfolio risk snapshot.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from app.services.risk._common import risk_business_payload, risk_tool_result


def _read_payload_tool(
    tool_name: str,
    *,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
    **payload: Any,
) -> dict[str, Any]:
    """Return a read-only payload in the standard risk tool envelope."""
    return risk_tool_result(
        tool_name,
        data={"request": risk_business_payload(payload), **payload},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="medium",
        approval_required="none",
    )


def get_open_positions(
    *,
    positions: list[dict[str, Any]] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Return current open positions supplied by the caller.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        positions: Normalized open position records.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _read_payload_tool(
        "get_open_positions",
        positions=positions or [],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def get_open_orders(
    *,
    orders: list[dict[str, Any]] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Return current open orders supplied by the caller.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        orders: Normalized open order records.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _read_payload_tool(
        "get_open_orders",
        orders=orders or [],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def get_strategy_allocations(
    *,
    allocations: dict[str, float] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Return current strategy capital allocations.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        allocations: Mapping of strategy ID to allocation weight.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _read_payload_tool(
        "get_strategy_allocations",
        allocations=allocations or {},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def get_portfolio_equity_curve(
    *,
    equity_curve: list[float] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Return a supplied portfolio equity curve.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity_curve: Ordered account equity values.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _read_payload_tool(
        "get_portfolio_equity_curve",
        equity_curve=equity_curve or [],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def calculate_portfolio_returns(
    *,
    equity_curve: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate period returns from a portfolio equity curve.

    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity_curve: Ordered account equity values.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    equity = pd.to_numeric(pd.Series(equity_curve), errors="coerce").dropna()
    returns = equity.pct_change().dropna().tolist()
    return risk_tool_result(
        "calculate_portfolio_returns",
        data={"returns": returns},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="low",
        approval_required="none",
    )


def calculate_portfolio_volatility(
    *,
    returns: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate sample volatility from portfolio returns.

    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns: Ordered portfolio return values.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    series = pd.to_numeric(pd.Series(returns), errors="coerce").dropna()
    return risk_tool_result(
        "calculate_portfolio_volatility",
        data={"volatility": float(series.std()) if len(series) else 0.0},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="low",
        approval_required="none",
    )


def calculate_portfolio_correlation(
    *,
    returns_by_asset: dict[str, list[float]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate a correlation matrix from asset returns.

    Tool class:
        read_only
    Risk level:
        low
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns_by_asset: Mapping of asset name to return series.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    matrix = pd.DataFrame(returns_by_asset).corr().fillna(0.0).to_dict()
    return risk_tool_result(
        "calculate_portfolio_correlation",
        data={"correlation_matrix": matrix},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="low",
        approval_required="none",
    )


def calculate_portfolio_var(
    *,
    returns: list[float],
    alpha: float = 0.05,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate historical portfolio value-at-risk.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns: Ordered portfolio return values.
        alpha: Lower-tail quantile.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    series = pd.to_numeric(pd.Series(returns), errors="coerce").dropna()
    value = float(series.quantile(float(alpha))) if len(series) else 0.0
    return risk_tool_result(
        "calculate_portfolio_var",
        data={"var": value},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="medium",
        approval_required="none",
    )


def calculate_portfolio_cvar(
    *,
    returns: list[float],
    alpha: float = 0.05,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate historical portfolio conditional value-at-risk.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        returns: Ordered portfolio return values.
        alpha: Lower-tail quantile.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    series = pd.to_numeric(pd.Series(returns), errors="coerce").dropna()
    var = float(series.quantile(float(alpha))) if len(series) else 0.0
    cvar = float(series[series <= var].mean()) if len(series[series <= var]) else 0.0
    return risk_tool_result(
        "calculate_portfolio_cvar",
        data={"cvar": cvar},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="medium",
        approval_required="none",
    )


def calculate_risk_contribution(
    *,
    exposures: dict[str, float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate normalized absolute exposure contribution.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        exposures: Mapping of asset or strategy name to exposure value.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    total = sum(abs(float(value)) for value in exposures.values())
    contribution = {
        key: abs(float(value)) / total if total else 0.0
        for key, value in exposures.items()
    }
    return risk_tool_result(
        "calculate_risk_contribution",
        data={"risk_contribution": contribution},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="medium",
        approval_required="none",
    )


def calculate_margin_usage(
    *,
    equity: float,
    used_margin: float,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate portfolio used-margin fraction.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        equity: Current account equity.
        used_margin: Current used margin.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    margin_usage = float(used_margin) / float(equity) if float(equity) else 0.0
    return risk_tool_result(
        "calculate_margin_usage",
        data={"margin_usage": margin_usage},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="medium",
        approval_required="none",
    )


def calculate_currency_exposure(
    *,
    positions: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Calculate base and quote currency exposure from FX positions.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        positions: Position records with symbol and notional fields.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    exposure: dict[str, float] = {}
    for position in positions:
        symbol = str(position.get("symbol", ""))
        value = float(position.get("notional", 0.0) or 0.0)
        if len(symbol) >= 6:
            exposure[symbol[:3]] = exposure.get(symbol[:3], 0.0) + value
            exposure[symbol[3:6]] = exposure.get(symbol[3:6], 0.0) - value
    return risk_tool_result(
        "calculate_currency_exposure",
        data={"currency_exposure": exposure},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="medium",
        approval_required="none",
    )


def detect_strategy_overlap(
    *,
    strategy_symbols: dict[str, list[str]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Detect symbols traded by more than one strategy.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        strategy_symbols: Mapping of strategy ID to traded symbols.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    symbol_to_strategies: dict[str, list[str]] = {}
    for strategy_id, symbols in strategy_symbols.items():
        for symbol in symbols:
            symbol_to_strategies.setdefault(symbol, []).append(strategy_id)
    overlap = {
        symbol: strategies
        for symbol, strategies in symbol_to_strategies.items()
        if len(strategies) > 1
    }
    return risk_tool_result(
        "detect_strategy_overlap",
        data={"overlap": overlap, "overlap_detected": bool(overlap)},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="medium",
        approval_required="none",
    )


def detect_symbol_cluster_risk(
    *,
    symbol_exposures: dict[str, float],
    cluster_limit: float = 0.5,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Detect symbols whose exposure exceeds a concentration threshold.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        symbol_exposures: Mapping of symbol to exposure ratio.
        cluster_limit: Maximum allowed exposure for one symbol cluster.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    clusters = {
        symbol: exposure
        for symbol, exposure in symbol_exposures.items()
        if abs(float(exposure)) > float(cluster_limit)
    }
    return risk_tool_result(
        "detect_symbol_cluster_risk",
        data={"cluster_risk": bool(clusters), "clusters": clusters},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="medium",
        approval_required="none",
    )


def build_portfolio_risk_snapshot(
    *,
    positions: list[dict[str, Any]] | None = None,
    equity_curve: list[float] | None = None,
    allocations: dict[str, float] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a compact portfolio risk snapshot from supplied state.

    Tool class:
        read_only
    Risk level:
        medium
    Approval required:
        none
    Side effects:
        None.
    Inputs:
        positions: Current normalized position records.
        equity_curve: Ordered account equity values.
        allocations: Current strategy allocation weights.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    position_list = positions or []
    equity_values = equity_curve or []
    allocation_map = allocations or {}
    gross_notional = sum(
        abs(float(pos.get("notional", 0.0) or 0.0)) for pos in position_list
    )
    snapshot = {
        "position_count": len(position_list),
        "gross_notional": gross_notional,
        "equity_points": len(equity_values),
        "strategy_count": len(allocation_map),
        "allocations": allocation_map,
    }
    return risk_tool_result(
        "build_portfolio_risk_snapshot",
        data={"snapshot": snapshot},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="medium",
        approval_required="none",
    )


__all__ = [
    "build_portfolio_risk_snapshot",
    "calculate_currency_exposure",
    "calculate_margin_usage",
    "calculate_portfolio_correlation",
    "calculate_portfolio_cvar",
    "calculate_portfolio_returns",
    "calculate_portfolio_var",
    "calculate_portfolio_volatility",
    "calculate_risk_contribution",
    "detect_strategy_overlap",
    "detect_symbol_cluster_risk",
    "get_open_orders",
    "get_open_positions",
    "get_portfolio_equity_curve",
    "get_strategy_allocations",
]
