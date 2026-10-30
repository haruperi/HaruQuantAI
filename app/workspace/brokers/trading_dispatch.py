"""Migration bridge for TradingDispatcher to app.core.trading.connection.trading_dispatch."""

import sys

from app.core.trading.connection import trading_dispatch as _implementation
from app.core.trading.connection.trading_dispatch import *  # noqa: F403

sys.modules[__name__] = _implementation
