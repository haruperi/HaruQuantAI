"""Live broker connector adapters and registry.

Description:
    Exports thread-safe BrokerRegistry and live connector client adapters for
    MetaTrader 5, Spotware cTrader, and cryptocurrency exchanges.
Purpose:
    FEAT-LIVE-BROKERS: Live broker connector adapters and registry exports.
Key Capabilities:
    - FR-trading-broker-exports: Canonical exports for registry and broker adapters.
Python API Usage:
    from app.workspace.trading.brokers import (
        BrokerRegistry,
        MetaTraderClient,
        CTraderClient,
        CryptoBrokerClient,
        default_broker_registry,
    )
CLI Usage:
    uv run python -m pytest tests/workspace/trading/test_broker_registry.py -q
"""

from .crypto import CryptoBrokerClient
from .ctrader import CTraderClient
from .metatrader import MetaTraderClient
from .registry import BrokerRegistry, default_broker_registry

__all__ = [
    "BrokerRegistry",
    "CTraderClient",
    "CryptoBrokerClient",
    "MetaTraderClient",
    "default_broker_registry",
]
