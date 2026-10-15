"""Exchange-specific historical market data adapters for cryptocurrency venues.

Description:
    Exposes read-only historical market data adapters for major cryptocurrency
    venues (Bitfinex, Coinbase, Poloniex). Conforms to the standard historical
    data retrieval contract without eager connections or order execution authority.
"""

from __future__ import annotations

from app.services.brokers.exchanges.bitfinex import BitfinexExchangeAdapter
from app.services.brokers.exchanges.coinbase import CoinbaseExchangeAdapter
from app.services.brokers.exchanges.poloniex import PoloniexExchangeAdapter

__all__ = [
    "BitfinexExchangeAdapter",
    "CoinbaseExchangeAdapter",
    "PoloniexExchangeAdapter",
]
