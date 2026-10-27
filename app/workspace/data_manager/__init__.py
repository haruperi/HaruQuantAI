"""Data manager workspace package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.workspace.data_manager.dukascopy import Dukascopy
    from app.workspace.data_manager.sources import Sources


def __getattr__(name: str) -> Any:
    """Lazily import data manager classes and functions on demand."""
    services = {
        "Dukascopy": "dukascopy",
        "Sources": "sources",
    }
    if name in services:
        return getattr(import_module(f"{__name__}.{services[name]}"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Dukascopy",
    "Sources",
]
