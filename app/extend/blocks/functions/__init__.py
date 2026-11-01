"""Quantitative arithmetic, math, temporal, ranking, and pip conversion blocks."""

from __future__ import annotations

from app.extend.blocks.functions._common import (
    DATE_MONTH_MULTIPLIER,
    DATE_YEAR_MULTIPLIER,
    DEFAULT_PIP_SIZE,
    FLOAT_MAX_VALUE,
    MIN_RANK_PERIOD,
    POINT_3_DIGIT,
    POINT_5_DIGIT,
    POINT_TO_PIP_MULTIPLIER,
    POINT_TOLERANCE,
    TIME_HOUR_MULTIPLIER,
    TIME_MINUTE_MULTIPLIER,
    register_custom_function,
    resolve_pip_size,
)
from app.extend.blocks.functions.abs_val import abs_val, abs_val_spec
from app.extend.blocks.functions.convert_pips_to_price import (
    convert_pips_to_price,
    convert_pips_to_price_spec,
    convert_pips_to_price_symbol,
)
from app.extend.blocks.functions.convert_price_to_pips import (
    convert_price_to_pips,
    convert_price_to_pips_spec,
    convert_price_to_pips_symbol,
)
from app.extend.blocks.functions.custom_function import (
    custom_function,
    custom_function_spec,
)
from app.extend.blocks.functions.division import division, division_spec
from app.extend.blocks.functions.exponential import exponential, exponential_spec
from app.extend.blocks.functions.facade import Functions
from app.extend.blocks.functions.get_date import get_date, get_date_spec
from app.extend.blocks.functions.get_time import get_time, get_time_spec
from app.extend.blocks.functions.indicator_highest import (
    indicator_highest,
    indicator_highest_spec,
)
from app.extend.blocks.functions.indicator_lowest import (
    indicator_lowest,
    indicator_lowest_spec,
)
from app.extend.blocks.functions.logarithm import logarithm, logarithm_spec
from app.extend.blocks.functions.maximum import maximum, maximum_spec
from app.extend.blocks.functions.minimum import minimum, minimum_spec
from app.extend.blocks.functions.minus import minus, minus_spec
from app.extend.blocks.functions.multiplication import (
    multiplication,
    multiplication_spec,
)
from app.extend.blocks.functions.plus import plus, plus_spec
from app.extend.blocks.functions.round_to_decimals import (
    round_to_decimals,
    round_to_decimals_spec,
)
from app.extend.blocks.functions.square_root import square_root, square_root_spec

__all__ = [
    "DATE_MONTH_MULTIPLIER",
    "DATE_YEAR_MULTIPLIER",
    "DEFAULT_PIP_SIZE",
    "FLOAT_MAX_VALUE",
    "MIN_RANK_PERIOD",
    "POINT_3_DIGIT",
    "POINT_5_DIGIT",
    "POINT_TOLERANCE",
    "POINT_TO_PIP_MULTIPLIER",
    "TIME_HOUR_MULTIPLIER",
    "TIME_MINUTE_MULTIPLIER",
    "Functions",
    "abs_val",
    "abs_val_spec",
    "convert_pips_to_price",
    "convert_pips_to_price_spec",
    "convert_pips_to_price_symbol",
    "convert_price_to_pips",
    "convert_price_to_pips_spec",
    "convert_price_to_pips_symbol",
    "custom_function",
    "custom_function_spec",
    "division",
    "division_spec",
    "exponential",
    "exponential_spec",
    "get_date",
    "get_date_spec",
    "get_time",
    "get_time_spec",
    "indicator_highest",
    "indicator_highest_spec",
    "indicator_lowest",
    "indicator_lowest_spec",
    "logarithm",
    "logarithm_spec",
    "maximum",
    "maximum_spec",
    "minimum",
    "minimum_spec",
    "minus",
    "minus_spec",
    "multiplication",
    "multiplication_spec",
    "plus",
    "plus_spec",
    "register_custom_function",
    "resolve_pip_size",
    "round_to_decimals",
    "round_to_decimals_spec",
    "square_root",
    "square_root_spec",
]
