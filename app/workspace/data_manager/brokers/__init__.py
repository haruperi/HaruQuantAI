"""Data Manager broker profiles catalog service package.

Description:
    Provides broker profiles, connectivity metadata, timezones, and postfixes
    for the Data Manager workspace, reading catalog entries from the
    authoritative SQLite database (datamgr_broker table).
"""

from __future__ import annotations

from ._cli import (
    register_broker_commands,
    run_broker_command,
)
from ._helpers import (
    BROKERS_CATALOG_FR,
    BrokerInfo,
    BrokersCLI,
    format_broker_table,
    persistence,
)
from .feature import Brokers
from .http import register_broker_routes

__all__ = [
    "BROKERS_CATALOG_FR",
    "BrokerInfo",
    "Brokers",
    "BrokersCLI",
    "format_broker_table",
    "persistence",
    "register_broker_commands",
    "register_broker_routes",
    "run_broker_command",
]
