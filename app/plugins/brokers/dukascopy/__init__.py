"""Dukascopy broker plugin package."""

from .adapter import DukascopyBroker, DukascopyProvider, create_adapter

__all__ = ["DukascopyBroker", "DukascopyProvider", "create_adapter"]
