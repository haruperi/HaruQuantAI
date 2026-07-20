"""Helpers to read MT5 client/account/symbol objects with wrapper compatibility.

Classes and functions:
    account_balance: Function. Provides account_balance behavior for execution workflows.
    account_equity: Function. Provides account_equity behavior for execution workflows.
    account_margin: Function. Provides account_margin behavior for execution workflows.
    account_free_margin: Function. Provides account_free_margin behavior for execution workflows.
    account_margin_level: Function. Provides account_margin_level behavior for execution workflows.
    account_profit: Function. Provides account_profit behavior for execution workflows.
    account_currency: Function. Provides account_currency behavior for execution workflows.
    account_leverage: Function. Provides account_leverage behavior for execution workflows.
    account_trade_allowed: Function. Provides account_trade_allowed behavior for execution workflows.
    account_trade_expert: Function. Provides account_trade_expert behavior for execution workflows.
    symbol_bid: Function. Provides symbol_bid behavior for execution workflows.
    symbol_ask: Function. Provides symbol_ask behavior for execution workflows.
    symbol_name: Function. Provides symbol_name behavior for execution workflows.
    symbol_trade_mode_description: Function. Provides symbol_trade_mode_description behavior for execution workflows.
    symbol_volume_min: Function. Provides symbol_volume_min behavior for execution workflows.
    symbol_volume_max: Function. Provides symbol_volume_max behavior for execution workflows.
    symbol_volume_step: Function. Provides symbol_volume_step behavior for execution workflows.
"""

from __future__ import annotations

from typing import Any


def _call_or_attr(
    obj: Any, method_name: str, attr_name: str, default: Any = None
) -> Any:
    if obj is None:
        return default
    method = getattr(obj, method_name, None)
    if callable(method):
        try:
            return method()
        except Exception:
            return default
    return getattr(obj, attr_name, default)


def account_balance(account: Any) -> float:
    """Perform the account_balance execution service operation."""
    return float(_call_or_attr(account, "Balance", "balance", 0.0) or 0.0)


def account_equity(account: Any) -> float:
    """Perform the account_equity execution service operation."""
    return float(_call_or_attr(account, "Equity", "equity", 0.0) or 0.0)


def account_margin(account: Any) -> float:
    """Perform the account_margin execution service operation."""
    return float(_call_or_attr(account, "Margin", "margin", 0.0) or 0.0)


def account_free_margin(account: Any) -> float:
    """Perform the account_free_margin execution service operation."""
    return float(_call_or_attr(account, "FreeMargin", "margin_free", 0.0) or 0.0)


def account_margin_level(account: Any) -> float:
    """Perform the account_margin_level execution service operation."""
    return float(_call_or_attr(account, "MarginLevel", "margin_level", 0.0) or 0.0)


def account_profit(account: Any) -> float:
    """Perform the account_profit execution service operation."""
    return float(_call_or_attr(account, "Profit", "profit", 0.0) or 0.0)


def account_currency(account: Any) -> str:
    """Perform the account_currency execution service operation."""
    return str(_call_or_attr(account, "Currency", "currency", "") or "")


def account_leverage(account: Any) -> int:
    """Perform the account_leverage execution service operation."""
    return int(_call_or_attr(account, "Leverage", "leverage", 1) or 1)


def account_trade_allowed(account: Any) -> bool:
    """Perform the account_trade_allowed execution service operation."""
    return bool(_call_or_attr(account, "TradeAllowed", "trade_allowed", True))


def account_trade_expert(account: Any) -> bool:
    """Perform the account_trade_expert execution service operation."""
    return bool(_call_or_attr(account, "TradeExpert", "trade_expert", True))


def symbol_bid(symbol_info: Any) -> float:
    """Perform the symbol_bid execution service operation."""
    return float(_call_or_attr(symbol_info, "Bid", "bid", 0.0) or 0.0)


def symbol_ask(symbol_info: Any) -> float:
    """Perform the symbol_ask execution service operation."""
    return float(_call_or_attr(symbol_info, "Ask", "ask", 0.0) or 0.0)


def symbol_name(symbol_info: Any) -> str:
    """Perform the symbol_name execution service operation."""
    return str(_call_or_attr(symbol_info, "Name", "name", "") or "")


def symbol_trade_mode_description(symbol_info: Any) -> str:
    """Perform the symbol_trade_mode_description execution service operation."""
    raw = _call_or_attr(symbol_info, "TradeModeDescription", "trade_mode", "")
    return str(raw or "")


def symbol_volume_min(symbol_info: Any) -> float:
    """Perform the symbol_volume_min execution service operation."""
    return float(_call_or_attr(symbol_info, "LotsMin", "volume_min", 0.0) or 0.0)


def symbol_volume_max(symbol_info: Any) -> float:
    """Perform the symbol_volume_max execution service operation."""
    return float(_call_or_attr(symbol_info, "LotsMax", "volume_max", 0.0) or 0.0)


def symbol_volume_step(symbol_info: Any) -> float:
    """Perform the symbol_volume_step execution service operation."""
    return float(_call_or_attr(symbol_info, "LotsStep", "volume_step", 0.0) or 0.0)
