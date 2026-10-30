"""Temporary migration bridge to app.core.trading.blocks.base."""

from __future__ import annotations

import sys

from app.core.trading.blocks.base import BaseBlock, block

__all__ = ["BaseBlock", "block"]

from app.core.trading.blocks import base as _implementation

sys.modules[__name__] = _implementation
