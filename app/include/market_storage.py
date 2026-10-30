"""Temporary migration bridge to app.core.data.market_storage."""

from __future__ import annotations

import sys

from app.core.data import market_storage as _implementation
from app.core.data.market_storage import *  # noqa: F403

sys.modules[__name__] = _implementation
