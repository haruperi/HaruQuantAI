"""Temporary migration bridge to app.core.trading.blocks.base."""

import sys

from app.core.trading.blocks import base as _implementation

sys.modules[__name__] = _implementation
