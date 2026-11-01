"""Temporary migration bridge to app.core.trading.blocks.indicator."""

from __future__ import annotations

import sys

from app.core.trading.blocks import indicator as _implementation
from app.core.trading.blocks.indicator import BaseIndicator

__all__ = ["BaseIndicator"]

sys.modules[__name__] = _implementation
