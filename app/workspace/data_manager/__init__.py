"""Data manager workspace package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.workspace.data_manager.cli import (
        DataCLI,
        format_data_dashboard,
        format_dataset_table,
    )
    from app.workspace.data_manager.data import Data
    from app.workspace.data_manager.dukascopy import Dukascopy
    from app.workspace.data_manager.help import Help
    from app.workspace.data_manager.logs import Logs
    from app.workspace.data_manager.sources import Sources


def __getattr__(name: str) -> Any:
    """Lazily import data manager classes and functions on demand."""
    services = {
        "Data": "data",
        "Logs": "logs",
        "Help": "help",
        "Dukascopy": "dukascopy",
        "Sources": "sources",
    }
    if name in services:
        return getattr(import_module(f"{__name__}.{services[name]}"), name)
    if name in {
        "DataCLI",
        "format_data_dashboard",
        "format_dataset_table",
    }:
        from app.workspace.data_manager import cli

        return getattr(cli, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Data",
    "DataCLI",
    "Dukascopy",
    "Help",
    "Logs",
    "Sources",
    "format_data_dashboard",
    "format_dataset_table",
]
