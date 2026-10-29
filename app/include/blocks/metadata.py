"""Temporary migration bridge to app.core.trading.blocks.metadata."""

import sys

from app.core.trading.blocks import metadata as _implementation

sys.modules[__name__] = _implementation
