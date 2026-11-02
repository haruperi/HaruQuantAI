"""Functions extension package conforming to StrategyQuant SQ.Functions snippets.

Description:
    Exports core calculation and domain utility functions including order
    identification and tick normalization.
Purpose:
    FEAT-FUNCTIONS: StrategyQuant donor-faithful functions.
Key Capabilities:
    - FR-FUNCTIONS-EXPORTS: Canonical functions module exports.
Python API Usage:
    from app.extend.functions import TradeFilter, normalize_price
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.extend.functions.order_functions import (
    TradeFilter,
    aware_timestamp,
    bars_since,
    normalize_price,
    pip_size,
)

__all__ = [
    "TradeFilter",
    "aware_timestamp",
    "bars_since",
    "normalize_price",
    "pip_size",
]
