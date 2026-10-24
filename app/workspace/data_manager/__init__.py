"""Data manager workspace package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.workspace.data_manager.baskets import Baskets
    from app.workspace.data_manager.brokers import Brokers
    from app.workspace.data_manager.cli import (
        BasketsCLI,
        BrokersCLI,
        DataCLI,
        SessionsCLI,
        SymbolsCLI,
        format_basket_table,
        format_broker_table,
        format_data_dashboard,
        format_dataset_table,
        format_session_table,
        format_symbol_table,
    )
    from app.workspace.data_manager.data import Data
    from app.workspace.data_manager.sessions import Sessions
    from app.workspace.data_manager.symbols import Symbols


def __getattr__(name: str) -> Any:
    """Lazily import data manager classes and functions on demand."""
    if name == "Data":
        from app.workspace.data_manager import data

        return getattr(data, name)
    if name == "Symbols":
        from app.workspace.data_manager import symbols

        return getattr(symbols, name)
    if name == "Sessions":
        from app.workspace.data_manager import sessions

        return getattr(sessions, name)
    if name == "Brokers":
        from app.workspace.data_manager import brokers

        return getattr(brokers, name)
    if name == "Baskets":
        from app.workspace.data_manager import baskets

        return getattr(baskets, name)
    if name in {
        "BasketsCLI",
        "BrokersCLI",
        "DataCLI",
        "SessionsCLI",
        "SymbolsCLI",
        "format_basket_table",
        "format_broker_table",
        "format_data_dashboard",
        "format_dataset_table",
        "format_session_table",
        "format_symbol_table",
    }:
        from app.workspace.data_manager import cli

        return getattr(cli, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Baskets",
    "BasketsCLI",
    "Brokers",
    "BrokersCLI",
    "Data",
    "DataCLI",
    "Sessions",
    "SessionsCLI",
    "Symbols",
    "SymbolsCLI",
    "format_basket_table",
    "format_broker_table",
    "format_data_dashboard",
    "format_dataset_table",
    "format_session_table",
    "format_symbol_table",
]
