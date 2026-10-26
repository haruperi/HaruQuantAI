"""Data manager workspace package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.workspace.data_manager.baskets import Baskets
    from app.workspace.data_manager.brokers import Brokers
    from app.workspace.data_manager.cli import (
        BasketsCLI,
        BrokersCLI,
        CustomDataCLI,
        DataCLI,
        SessionsCLI,
        SymbolsCLI,
        format_basket_table,
        format_broker_table,
        format_custom_table,
        format_data_dashboard,
        format_dataset_table,
        format_review_table,
        format_session_table,
        format_symbol_table,
    )
    from app.workspace.data_manager.custom import CustomData
    from app.workspace.data_manager.data import Data
    from app.workspace.data_manager.dukascopy import Dukascopy
    from app.workspace.data_manager.help import Help
    from app.workspace.data_manager.logs import Logs
    from app.workspace.data_manager.sessions import Sessions
    from app.workspace.data_manager.sources import Sources
    from app.workspace.data_manager.symbols import Symbols


def __getattr__(name: str) -> Any:
    """Lazily import data manager classes and functions on demand."""
    services = {
        "Data": "data",
        "Symbols": "symbols",
        "Sessions": "sessions",
        "Brokers": "brokers",
        "Baskets": "baskets",
        "Logs": "logs",
        "CustomData": "custom",
        "Help": "help",
        "Dukascopy": "dukascopy",
        "Sources": "sources",
    }
    if name in services:
        return getattr(import_module(f"{__name__}.{services[name]}"), name)
    if name in {
        "BasketsCLI",
        "BrokersCLI",
        "CustomDataCLI",
        "DataCLI",
        "SessionsCLI",
        "SymbolsCLI",
        "format_basket_table",
        "format_broker_table",
        "format_custom_table",
        "format_data_dashboard",
        "format_dataset_table",
        "format_review_table",
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
    "CustomData",
    "CustomDataCLI",
    "Data",
    "DataCLI",
    "Dukascopy",
    "Help",
    "Logs",
    "Sessions",
    "SessionsCLI",
    "Sources",
    "Symbols",
    "SymbolsCLI",
    "format_basket_table",
    "format_broker_table",
    "format_custom_table",
    "format_data_dashboard",
    "format_dataset_table",
    "format_review_table",
    "format_session_table",
    "format_symbol_table",
]
