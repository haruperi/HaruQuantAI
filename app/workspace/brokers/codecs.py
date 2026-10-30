"""Migration bridge for market data binary stream codecs to app.core.trading.connection.codecs."""

import sys

from app.core.trading.connection import codecs as _implementation
from app.core.trading.connection.codecs import *  # noqa: F403

sys.modules[__name__] = _implementation
