"""Risk governor tool functions.

Purpose:
    Provide deterministic, single-purpose policy gate checks used before
    portfolio, strategy, or execution decisions.

Functions:
    check_max_drawdown_limit: Check account or strategy drawdown against a cap.
    check_daily_loss_limit: Check daily realized/unrealized loss against a cap.
    check_strategy_loss_limit: Check strategy-specific loss against a cap.
    check_portfolio_exposure_limit: Check total portfolio exposure.
    check_symbol_exposure_limit: Check single-symbol exposure.
    check_currency_exposure_limit: Check FX currency basket exposure.
    check_correlation_limit: Check correlation against a maximum threshold.
    check_var_limit: Check value-at-risk against a maximum threshold.
    check_cvar_limit: Check conditional value-at-risk against a maximum threshold.
    check_leverage_limit: Check gross leverage against a maximum threshold.
    check_margin_limit: Check margin usage against a maximum threshold.
    check_news_blackout: Block trading during active news blackout windows.
    check_spread_limit: Check current spread against a maximum threshold.
    check_slippage_limit: Check expected or observed slippage against a cap.
    check_trade_frequency_limit: Check trade frequency against a cap.
    check_kill_switch_state: Block when a kill switch is active.
    run_risk_governor_checks: Aggregate individual gate results.
"""

from __future__ import annotations

from typing import Any

from app.services.risk._common import (
    risk_limit_check,
    risk_tool_result,
)


def check_max_drawdown_limit(
    *,
    max_drawdown: float,
    limit: float = 0.2,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check account or strategy drawdown against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        max_drawdown: Absolute or signed drawdown value.
        limit: Maximum allowed absolute drawdown.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_max_drawdown_limit",
        value=abs(float(max_drawdown)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_daily_loss_limit(
    *,
    daily_loss: float,
    limit: float = 0.03,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check daily portfolio loss against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        daily_loss: Absolute or signed daily loss value.
        limit: Maximum allowed absolute daily loss.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_daily_loss_limit",
        value=abs(float(daily_loss)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_strategy_loss_limit(
    *,
    strategy_loss: float,
    limit: float = 0.05,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check strategy-specific loss against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        strategy_loss: Absolute or signed loss for one strategy.
        limit: Maximum allowed absolute strategy loss.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_strategy_loss_limit",
        value=abs(float(strategy_loss)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_portfolio_exposure_limit(
    *,
    exposure: float,
    limit: float = 1.0,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check total portfolio exposure against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        exposure: Portfolio exposure ratio or normalized notional.
        limit: Maximum allowed exposure.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_portfolio_exposure_limit",
        value=abs(float(exposure)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_symbol_exposure_limit(
    *,
    symbol_exposure: float,
    limit: float = 0.25,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check single-symbol exposure against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        symbol_exposure: Exposure for one symbol.
        limit: Maximum allowed symbol exposure.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_symbol_exposure_limit",
        value=abs(float(symbol_exposure)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_currency_exposure_limit(
    *,
    currency_exposure: float,
    limit: float = 0.4,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check FX currency basket exposure against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        currency_exposure: Exposure for one currency basket.
        limit: Maximum allowed currency exposure.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_currency_exposure_limit",
        value=abs(float(currency_exposure)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_correlation_limit(
    *,
    correlation: float,
    limit: float = 0.8,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check correlation against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        correlation: Correlation coefficient to evaluate.
        limit: Maximum allowed absolute correlation.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_correlation_limit",
        value=abs(float(correlation)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_var_limit(
    *,
    var: float,
    limit: float = 0.05,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check portfolio value-at-risk against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        var: Value-at-risk estimate.
        limit: Maximum allowed absolute VaR.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_var_limit",
        value=abs(float(var)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_cvar_limit(
    *,
    cvar: float,
    limit: float = 0.08,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check conditional value-at-risk against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        cvar: Conditional value-at-risk estimate.
        limit: Maximum allowed absolute CVaR.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_cvar_limit",
        value=abs(float(cvar)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_leverage_limit(
    *,
    leverage: float,
    limit: float = 10.0,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check gross leverage against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        leverage: Current or proposed leverage value.
        limit: Maximum allowed leverage.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_leverage_limit",
        value=abs(float(leverage)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_margin_limit(
    *,
    margin_usage: float,
    limit: float = 0.5,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check margin usage against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        margin_usage: Current or projected margin usage ratio.
        limit: Maximum allowed margin usage.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_margin_limit",
        value=abs(float(margin_usage)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_news_blackout(
    *,
    blackout_active: bool,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Block trading when a news blackout window is active.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        blackout_active: Whether the current symbol/time is in blackout.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_tool_result(
        "check_news_blackout",
        status="success" if not blackout_active else "rejected",
        data={"passed": not blackout_active, "blackout_active": blackout_active},
        errors=[] if not blackout_active else ["news blackout active"],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_spread_limit(
    *,
    spread: float,
    limit: float = 3.0,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check current spread against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        spread: Current spread in caller-defined units.
        limit: Maximum allowed spread in the same units.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_spread_limit",
        value=float(spread),
        limit=float(limit),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_slippage_limit(
    *,
    slippage: float,
    limit: float = 2.0,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check expected or observed slippage against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        slippage: Expected or observed slippage.
        limit: Maximum allowed absolute slippage.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_slippage_limit",
        value=abs(float(slippage)),
        limit=abs(float(limit)),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_trade_frequency_limit(
    *,
    trade_count: int,
    limit: int = 20,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Check trade frequency against a configured maximum.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        trade_count: Number of trades in the evaluated window.
        limit: Maximum allowed trades in that window.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_limit_check(
        "check_trade_frequency_limit",
        value=float(trade_count),
        limit=float(limit),
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def check_kill_switch_state(
    *,
    kill_switch_active: bool,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Block trading when the kill switch is active.

    Tool class:
        read_only
    Risk level:
        critical
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        kill_switch_active: Whether the relevant kill switch is active.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return risk_tool_result(
        "check_kill_switch_state",
        status="success" if not kill_switch_active else "blocked",
        data={
            "passed": not kill_switch_active,
            "kill_switch_active": kill_switch_active,
        },
        errors=[] if not kill_switch_active else ["kill switch active"],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        risk_level="critical",
    )


def run_risk_governor_checks(
    *,
    checks: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Aggregate deterministic risk governor check results.

    Tool class:
        read_only
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None.
    Inputs:
        checks: List of result dictionaries containing a boolean passed field.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    failed = [check for check in checks if not bool(check.get("passed", False))]
    return risk_tool_result(
        "run_risk_governor_checks",
        status="success" if not failed else "rejected",
        data={
            "passed": not failed,
            "failed_checks": failed,
            "check_count": len(checks),
        },
        errors=[] if not failed else ["one or more risk checks failed"],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


__all__ = [
    "check_correlation_limit",
    "check_currency_exposure_limit",
    "check_cvar_limit",
    "check_daily_loss_limit",
    "check_kill_switch_state",
    "check_leverage_limit",
    "check_margin_limit",
    "check_max_drawdown_limit",
    "check_news_blackout",
    "check_portfolio_exposure_limit",
    "check_slippage_limit",
    "check_spread_limit",
    "check_strategy_loss_limit",
    "check_symbol_exposure_limit",
    "check_trade_frequency_limit",
    "check_var_limit",
    "run_risk_governor_checks",
]
