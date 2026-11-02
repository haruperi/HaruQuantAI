"""Indicator package module: base.py.

Description:
    Base indicator contract re-export for modular extension blocks.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative indicator library.
Key Capabilities:
    - FR-indicator-core: Base indicator abstract contract.
Python API Usage:
    from app.extend.blocks.indicators import *
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

import sys

from app.core.trading.blocks import indicator as _implementation
from app.core.trading.blocks.indicator import BaseIndicator

__all__ = ["BaseIndicator"]

sys.modules[__name__] = _implementation
