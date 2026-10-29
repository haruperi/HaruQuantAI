"""Temporary migration bridge to app.core.data.market_storage."""

import sys

from app.core.data import market_storage as _implementation

sys.modules[__name__] = _implementation
