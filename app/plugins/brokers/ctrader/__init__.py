"""cTrader Open API broker plugin package."""

from .adapter import CTraderBroker, create_adapter

__all__ = ["CTraderBroker", "create_adapter"]
