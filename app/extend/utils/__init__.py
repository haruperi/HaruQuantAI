"""Utilities package conforming to StrategyQuant SQ.Utils snippets.

Description:
    Exports time difference calculations and date manipulation primitives
    matching StrategyQuant TimeDiffUtil and SQTime libraries.

Purpose:
    FEAT-UTILS: StrategyQuant donor-faithful utility modules.

Key Capabilities:
    - FR-UTILS-EXPORTS: Canonical package exports for SQ utilities.

Python API Usage:
    from app.extend.utils import SQTime, TimeDiffUtil
    diff = TimeDiffUtil.get_diff_in_days(chart, 5)

CLI Usage:
    uv run pytest tests/extend/test_utils.py --no-cov
"""

from __future__ import annotations

from app.extend.utils.sq_time import SQTime
from app.extend.utils.time_diff_util import TimeDiffUtil

__all__ = [
    "SQTime",
    "TimeDiffUtil",
]
