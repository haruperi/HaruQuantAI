"""Broker connectivity execution tools.

Purpose:
    Provide agent-facing tools for broker connection status, account metadata,
    symbol metadata, current pricing, trading permissions, market status, lot
    rules, stop distance, and free-margin checks.

Classes and functions:
    check_broker_connection: Function. Check broker connectivity.
    get_account_info: Function. Retrieve account information.
    get_symbol_info: Function. Retrieve broker symbol information.
    get_current_bid_ask: Function. Retrieve current bid and ask prices.
    get_current_spread: Function. Retrieve current spread.
    get_trade_permissions: Function. Retrieve trade permission status.
    get_broker_time: Function. Retrieve broker timestamp.
    check_market_open: Function. Check whether market is open.
    check_min_lot: Function. Check minimum lot rule.
    check_max_lot: Function. Check maximum lot rule.
    check_lot_step: Function. Check lot step rule.
    check_stop_distance: Function. Check minimum stop distance rule.
    check_free_margin: Function. Check free margin availability.
"""

from __future__ import annotations

from typing import Any

from ._common import package_execution_request


def check_broker_connection(**kwargs: Any) -> dict[str, Any]:
    """Check MT5 or cTrader broker connection status.

    Purpose:
        Package a broker connection status request for deterministic execution
        readiness workflows.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        No broker state changes; this tool packages/reads connection context.

    Inputs:
        broker:
            Optional broker identifier such as mt5 or ctrader.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("check_broker_connection", kwargs)


def get_account_info(**kwargs: Any) -> dict[str, Any]:
    """Retrieve account balance, equity, margin, and leverage context.

    Purpose:
        Package an account information request for execution readiness checks.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads account context only.

    Inputs:
        account_id:
            Optional account identifier.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("get_account_info", kwargs)


def get_symbol_info(**kwargs: Any) -> dict[str, Any]:
    """Retrieve broker metadata for one symbol.

    Purpose:
        Package a broker symbol metadata request.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads broker symbol context only.

    Inputs:
        symbol:
            Trading symbol.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("get_symbol_info", kwargs)


def get_current_bid_ask(**kwargs: Any) -> dict[str, Any]:
    """Retrieve current bid and ask prices.

    Purpose:
        Package a current quote request for an execution decision.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads market quote context only.

    Inputs:
        symbol:
            Trading symbol.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("get_current_bid_ask", kwargs)


def get_current_spread(**kwargs: Any) -> dict[str, Any]:
    """Retrieve current spread for one symbol.

    Purpose:
        Package a current spread request for cost and readiness checks.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads spread context only.

    Inputs:
        symbol:
            Trading symbol.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("get_current_spread", kwargs)


def get_trade_permissions(**kwargs: Any) -> dict[str, Any]:
    """Retrieve whether trading is allowed for the account and symbol.

    Purpose:
        Package a trade permission request before order submission.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads permission state only.

    Inputs:
        symbol:
            Optional trading symbol.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("get_trade_permissions", kwargs)


def get_broker_time(**kwargs: Any) -> dict[str, Any]:
    """Retrieve broker timestamp.

    Purpose:
        Package a broker clock request for freshness checks.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads broker clock context only.

    Inputs:
        broker:
            Optional broker identifier.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("get_broker_time", kwargs)


def check_market_open(**kwargs: Any) -> dict[str, Any]:
    """Check whether a symbol can be traded now.

    Purpose:
        Package a market-open check for execution readiness.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads market session context only.

    Inputs:
        symbol:
            Trading symbol.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("check_market_open", kwargs)


def check_min_lot(**kwargs: Any) -> dict[str, Any]:
    """Check broker minimum lot rule.

    Purpose:
        Package a minimum lot validation request.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads broker symbol rule context only.

    Inputs:
        symbol:
            Trading symbol.
        volume:
            Proposed order volume.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("check_min_lot", kwargs)


def check_max_lot(**kwargs: Any) -> dict[str, Any]:
    """Check broker maximum lot rule.

    Purpose:
        Package a maximum lot validation request.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads broker symbol rule context only.

    Inputs:
        symbol:
            Trading symbol.
        volume:
            Proposed order volume.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("check_max_lot", kwargs)


def check_lot_step(**kwargs: Any) -> dict[str, Any]:
    """Check broker lot step rule.

    Purpose:
        Package a lot-step validation request.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads broker symbol rule context only.

    Inputs:
        symbol:
            Trading symbol.
        volume:
            Proposed order volume.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("check_lot_step", kwargs)


def check_stop_distance(**kwargs: Any) -> dict[str, Any]:
    """Check broker minimum stop distance.

    Purpose:
        Package a stop-distance validation request.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads broker symbol rule context only.

    Inputs:
        symbol:
            Trading symbol.
        price:
            Proposed order price.
        stop_loss:
            Proposed stop-loss price.
        take_profit:
            Proposed take-profit price.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("check_stop_distance", kwargs)


def check_free_margin(**kwargs: Any) -> dict[str, Any]:
    """Check free margin availability.

    Purpose:
        Package a free-margin validation request before execution.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        Reads account margin context only.

    Inputs:
        symbol:
            Trading symbol.
        volume:
            Proposed order volume.
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the calling agent.
        dry_run:
            If True, validate and package only.
        environment:
            Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("check_free_margin", kwargs)


__all__ = [
    "check_broker_connection",
    "check_free_margin",
    "check_lot_step",
    "check_market_open",
    "check_max_lot",
    "check_min_lot",
    "check_stop_distance",
    "get_account_info",
    "get_broker_time",
    "get_current_bid_ask",
    "get_current_spread",
    "get_symbol_info",
    "get_trade_permissions",
]
