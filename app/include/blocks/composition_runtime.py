"""Temporary migration bridge to app.core.trading.blocks.composition_runtime."""

from __future__ import annotations

import sys

from app.core.trading.blocks import composition_runtime as _implementation
from app.core.trading.blocks.composition_runtime import *  # noqa: F403
from app.core.trading.blocks.composition_runtime import CompositionExecutor

__all__ = ["CompositionExecutor"]

sys.modules[__name__] = _implementation
