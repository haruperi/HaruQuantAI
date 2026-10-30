"""Temporary migration bridge to app.core.trading.blocks.composition."""

from __future__ import annotations

import sys

from app.core.trading.blocks import composition as _implementation
from app.core.trading.blocks.composition import *  # noqa: F403
from app.core.trading.blocks.composition import (
    CompositionSpec,
    bind_composition,
    composition_manifest,
    owned_compositions,
    owned_specializations,
)

__all__ = [
    "CompositionSpec",
    "bind_composition",
    "composition_manifest",
    "owned_compositions",
    "owned_specializations",
]

sys.modules[__name__] = _implementation
