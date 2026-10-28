"""Shared quantitative numerical kernels.

These are high-performance computational kernels (pure NumPy / vectorized algorithms).
They are infrastructure primitives, not catalog blocks.
"""

from app.include.numerical.ma import sma_kernel

__all__ = ["sma_kernel"]
