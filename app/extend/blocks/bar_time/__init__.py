"""Bar and Time strategy blocks and temporal calculation facades.

Description:
    Implements all 37 StrategyQuant BarAndTime snippet classes as modular
    typed blocks and facades for rule generation, builder integration, and
    backtesting execution.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarAndTime building blocks.
Key Capabilities:
    - FR-bar-time-discrete: All 37 discrete temporal value and condition blocks.
    - FR-bar-time-facades: BarTime and TimeConditions object-oriented facades.
    - FR-bar-time-registration: BlockSpec descriptors for algo generation.
Python API Usage:
    from app.extend.blocks.bar_time import BarTime, bar_date, bar_hour_is
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.bar_time._common import (
    DateTime,
    format_timestamp,
    normalize_timestamps,
)
from app.extend.blocks.bar_time.always_false import always_false, always_false_spec
from app.extend.blocks.bar_time.always_true import always_true, always_true_spec
from app.extend.blocks.bar_time.bar_date import bar_date, bar_date_spec
from app.extend.blocks.bar_time.bar_day_of_month import (
    bar_day_of_month,
    bar_day_of_month_spec,
)
from app.extend.blocks.bar_time.bar_day_of_week import (
    bar_day_of_week,
    bar_day_of_week_spec,
)
from app.extend.blocks.bar_time.bar_day_of_week_is import (
    bar_day_of_week_is,
    bar_day_of_week_is_spec,
)
from app.extend.blocks.bar_time.bar_day_of_week_is_not import (
    bar_day_of_week_is_not,
    bar_day_of_week_is_not_spec,
)
from app.extend.blocks.bar_time.bar_hour import bar_hour, bar_hour_spec
from app.extend.blocks.bar_time.bar_hour_is import bar_hour_is, bar_hour_is_spec
from app.extend.blocks.bar_time.bar_hour_is_bigger import (
    bar_hour_is_bigger,
    bar_hour_is_bigger_spec,
)
from app.extend.blocks.bar_time.bar_hour_is_smaller import (
    bar_hour_is_smaller,
    bar_hour_is_smaller_spec,
)
from app.extend.blocks.bar_time.bar_minute import bar_minute, bar_minute_spec
from app.extend.blocks.bar_time.bar_minute_is import (
    bar_minute_is,
    bar_minute_is_spec,
)
from app.extend.blocks.bar_time.bar_month import bar_month, bar_month_spec
from app.extend.blocks.bar_time.bar_month_is import (
    bar_month_is,
    bar_month_is_spec,
)
from app.extend.blocks.bar_time.bar_month_is_not import (
    bar_month_is_not,
    bar_month_is_not_spec,
)
from app.extend.blocks.bar_time.bar_time import bar_time, bar_time_spec
from app.extend.blocks.bar_time.bar_time_is import bar_time_is, bar_time_is_spec
from app.extend.blocks.bar_time.bar_week_of_month import (
    bar_week_of_month,
    bar_week_of_month_spec,
)
from app.extend.blocks.bar_time.current_bar import current_bar, current_bar_spec
from app.extend.blocks.bar_time.current_date import (
    current_date,
    current_date_spec,
)
from app.extend.blocks.bar_time.current_day_of_week import (
    current_day_of_week,
    current_day_of_week_spec,
)
from app.extend.blocks.bar_time.current_day_of_week_is import (
    current_day_of_week_is,
    current_day_of_week_is_spec,
)
from app.extend.blocks.bar_time.current_hour import (
    current_hour,
    current_hour_spec,
)
from app.extend.blocks.bar_time.current_hour_is import (
    current_hour_is,
    current_hour_is_spec,
)
from app.extend.blocks.bar_time.current_minute import (
    current_minute,
    current_minute_spec,
)
from app.extend.blocks.bar_time.current_minute_is import (
    current_minute_is,
    current_minute_is_spec,
)
from app.extend.blocks.bar_time.current_month import (
    current_month,
    current_month_spec,
)
from app.extend.blocks.bar_time.current_month_is import (
    current_month_is,
    current_month_is_spec,
)
from app.extend.blocks.bar_time.current_time import (
    current_time,
    current_time_spec,
)
from app.extend.blocks.bar_time.current_time_is import (
    current_time_is,
    current_time_is_spec,
)
from app.extend.blocks.bar_time.current_week_of_month import (
    current_week_of_month,
    current_week_of_month_spec,
)
from app.extend.blocks.bar_time.facade import BarTime, TimeConditions
from app.extend.blocks.bar_time.first_week_of_month import (
    first_week_of_month,
    first_week_of_month_spec,
)
from app.extend.blocks.bar_time.is_bar_open import is_bar_open, is_bar_open_spec
from app.extend.blocks.bar_time.is_month_first_trading_day import (
    is_month_first_trading_day,
    is_month_first_trading_day_spec,
)
from app.extend.blocks.bar_time.is_month_last_trading_day import (
    is_month_last_trading_day,
    is_month_last_trading_day_spec,
)
from app.extend.blocks.bar_time.last_week_of_month import (
    last_week_of_month,
    last_week_of_month_spec,
)

__all__ = [
    "BarTime",
    "DateTime",
    "TimeConditions",
    "always_false",
    "always_false_spec",
    "always_true",
    "always_true_spec",
    "bar_date",
    "bar_date_spec",
    "bar_day_of_month",
    "bar_day_of_month_spec",
    "bar_day_of_week",
    "bar_day_of_week_is",
    "bar_day_of_week_is_not",
    "bar_day_of_week_is_not_spec",
    "bar_day_of_week_is_spec",
    "bar_day_of_week_spec",
    "bar_hour",
    "bar_hour_is",
    "bar_hour_is_bigger",
    "bar_hour_is_bigger_spec",
    "bar_hour_is_smaller",
    "bar_hour_is_smaller_spec",
    "bar_hour_is_spec",
    "bar_hour_spec",
    "bar_minute",
    "bar_minute_is",
    "bar_minute_is_spec",
    "bar_minute_spec",
    "bar_month",
    "bar_month_is",
    "bar_month_is_not",
    "bar_month_is_not_spec",
    "bar_month_is_spec",
    "bar_month_spec",
    "bar_time",
    "bar_time_is",
    "bar_time_is_spec",
    "bar_time_spec",
    "bar_week_of_month",
    "bar_week_of_month_spec",
    "current_bar",
    "current_bar_spec",
    "current_date",
    "current_date_spec",
    "current_day_of_week",
    "current_day_of_week_is",
    "current_day_of_week_is_spec",
    "current_day_of_week_spec",
    "current_hour",
    "current_hour_is",
    "current_hour_is_spec",
    "current_hour_spec",
    "current_minute",
    "current_minute_is",
    "current_minute_is_spec",
    "current_minute_spec",
    "current_month",
    "current_month_is",
    "current_month_is_spec",
    "current_month_spec",
    "current_time",
    "current_time_is",
    "current_time_is_spec",
    "current_time_spec",
    "current_week_of_month",
    "current_week_of_month_spec",
    "first_week_of_month",
    "first_week_of_month_spec",
    "format_timestamp",
    "is_bar_open",
    "is_bar_open_spec",
    "is_month_first_trading_day",
    "is_month_first_trading_day_spec",
    "is_month_last_trading_day",
    "is_month_last_trading_day_spec",
    "last_week_of_month",
    "last_week_of_month_spec",
    "normalize_timestamps",
]
