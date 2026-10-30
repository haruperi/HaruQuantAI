"""Temporary migration bridge to app.core.trading.blocks.registry."""

from __future__ import annotations

import sys

from app.core.trading.blocks import registry as _implementation
from app.core.trading.blocks.registry import *  # noqa: F403
from app.core.trading.blocks.registry import (
    BlockDescriptor,
    BlockRegistry,
    BlockRegistryError,
    CatalogSnapshot,
    block_registry,
)

__all__ = [
    "BlockDescriptor",
    "BlockRegistry",
    "BlockRegistryError",
    "CatalogSnapshot",
    "block_registry",
]

sys.modules[__name__] = _implementation
