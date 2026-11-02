"""Data Manager historical data sources package.

Description:
    Provides registration, ingestion, and downloading of historical market data
    from broker clients and external data feeds, including Dukascopy Bank SA,
    Crypto exchanges (Binance, Bitfinex, Coinbase, Poloniex), Darwinex,
    Yahoo Finance, StrategyQuant Equity/Futures, and MetaTrader 5.
"""

from __future__ import annotations

from app.core.data.market_storage import M1_SCHEMA, TICK_SCHEMA
from app.workspace.brokers.dukascopy import DukascopyClient

from ._base import BaseSource, Sources
from ._cli import (
    register_dukascopy_commands,
    register_source_commands,
    run_dukascopy_command,
    run_source_command,
)
from ._helpers import (
    CRYPTO,
    DEFAULT_CATALOG_PATH,
    DEFAULT_STORAGE_ROOT,
    DISCLAIMER_PARAGRAPHS,
    MIN_CATALOG_PARTS,
    PROVIDERS,
    capabilities,
    intervals,
    make_client,
    provider_id,
)
from .crypto import Crypto
from .darwinex import Darwinex
from .download_jobs import manager, register_download_jobs
from .dukascopy import Dukascopy
from .http import (
    bridge_action,
    register_dukascopy_routes,
    register_source_routes,
    start_download,
    start_source_download,
)
from .metatrader import MT5, MetaTrader
from .sq_data import SQData
from .sq_equity import SQEquity
from .sq_futures import SQFutures
from .yahoo import Yahoo

__all__ = [
    "CRYPTO",
    "DEFAULT_CATALOG_PATH",
    "DEFAULT_STORAGE_ROOT",
    "DISCLAIMER_PARAGRAPHS",
    "M1_SCHEMA",
    "MIN_CATALOG_PARTS",
    "MT5",
    "PROVIDERS",
    "TICK_SCHEMA",
    "BaseSource",
    "Crypto",
    "Darwinex",
    "Dukascopy",
    "DukascopyClient",
    "MetaTrader",
    "SQData",
    "SQEquity",
    "SQFutures",
    "Sources",
    "Yahoo",
    "bridge_action",
    "capabilities",
    "intervals",
    "make_client",
    "manager",
    "provider_id",
    "register_download_jobs",
    "register_dukascopy_commands",
    "register_dukascopy_routes",
    "register_source_commands",
    "register_source_routes",
    "run_dukascopy_command",
    "run_source_command",
    "start_download",
    "start_source_download",
]
