"""Shared services utility modules for temporal, price, and blocks.

Description:
    Consolidates utility primitives and feature extractors consumed by trading
    strategies, indicators, and broker services:
    - BarAndTime primitives: DateTimeSeries, BarTime, TimeConditions,
      normalize_timestamps, and format_timestamp.
    - Price primitives: BarPrice, QuotePrice, MTFPrice, SessionPrice,
      and HeikenAshiPrice.
    - Comparison primitives: Comparisons facade, MAType, arithmetic comparisons,
      bar-to-bar crossovers, trend/count persistence, percentile rankings,
      indicator-to-MA conditions, and compound boolean combinators.
    - Function primitives: Functions facade, arithmetic operators (plus, minus,
      multiplication, division), math functions (abs, round, exp, log, sqrt,
      min/max), temporal builders (get_date, get_time), rolling rank extractors
      (indicator_highest, indicator_lowest), and MT5 broker symbol-integrated
      pip conversions (convert_price_to_pips, convert_pips_to_price).
    - Type primitives: Types facade, Variable generic container, BooleanConstant,
      BooleanVariable, DoubleVariable, IntVariable, and NumberConstant.
    - Action primitives: Actions facade, ActionRecord, variable assignments,
      chart annotations (arrows, vertical line), logging (journal, file), and
      email notifications.
    - Data primitives: bars_to_dataframe, bars_to_df, ticks_to_dataframe,
      and ticks_to_df converting market data collections to pandas DataFrames.

Purpose:
    FEAT-SERVICES-UTILS: Re-export temporal, price, comparison, function, type,
    action, and data utility building blocks.

Key Capabilities:
    - FR-SERVICES-UTILS-EXPORTS: Provide centralized public access to utilities.
      Associated: `format_timestamp()`, `BarTime`, `BarPrice`, `Comparisons`,
        `Functions`, `Types`, `Actions`.
      Logging: Re-export namespace declarations; operational logging occurs
        in component modules.

Python API Usage:
    ```python
    from app.services.utils import (
        Actions,
        BarPrice,
        BarTime,
        Comparisons,
        Functions,
        Types,
        Variable,
    )

    var = Types.create_variable("threshold", "float", 1.25)
    Actions.assign(var, 1.30)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_types.py --no-cov
    ```
"""

from __future__ import annotations

from app.services.libs.bar_time import (
    BarTime,
    DateTimeSeries,
    TimeConditions,
    format_timestamp,
    normalize_timestamps,
)
from app.services.utils.actions import (
    ActionRecord,
    Actions,
    AssignVariableAction,
    CustomAction,
    DrawDownArrowAction,
    DrawUpArrowAction,
    DrawVerticalLineAction,
    LogToFileAction,
    LogToJournalAction,
    SendEmailAction,
    assign_variable,
    custom_action,
    draw_down_arrow,
    draw_up_arrow,
    draw_vertical_line,
    log_to_file,
    log_to_journal,
    send_email,
)
from app.services.utils.comparisons import (
    Comparisons,
    MAType,
    calculate_ma,
    calculate_wma,
    condition_and,
    condition_not,
    condition_or,
    crosses_above,
    crosses_below,
    equals,
    indicator_above_ma,
    indicator_below_ma,
    indicator_crosses_above_ma,
    indicator_crosses_below_ma,
    is_falling,
    is_greater,
    is_greater_count,
    is_greater_or_equal,
    is_greater_percentile,
    is_lower,
    is_lower_count,
    is_lower_or_equal,
    is_lower_percentile,
    is_rising,
    not_equals,
    resolve_shift_value,
    round_value,
)
from app.services.utils.functions import (
    Functions,
    abs_val,
    convert_pips_to_price,
    convert_pips_to_price_symbol,
    convert_price_to_pips,
    convert_price_to_pips_symbol,
    custom_function,
    division,
    exponential,
    get_date,
    get_time,
    indicator_highest,
    indicator_lowest,
    logarithm,
    maximum,
    minimum,
    minus,
    multiplication,
    plus,
    register_custom_function,
    round_to_decimals,
    square_root,
)
from app.services.utils.price import (
    BarPrice,
    HeikenAshiPrice,
    MTFPrice,
    QuotePrice,
    SessionPrice,
)
from app.services.utils.types import (
    BooleanConstant,
    BooleanVariable,
    DoubleVariable,
    IntVariable,
    NumberConstant,
    Types,
    Variable,
    boolean_constant,
    boolean_variable,
    double_variable,
    int_variable,
    number_constant,
)
from app.workspace.data_manager.history import (
    bars_to_dataframe,
    bars_to_df,
    ticks_to_dataframe,
    ticks_to_df,
)

__all__ = [
    "ActionRecord",
    "Actions",
    "AssignVariableAction",
    "BarPrice",
    "BarTime",
    "BooleanConstant",
    "BooleanVariable",
    "Comparisons",
    "CustomAction",
    "DateTimeSeries",
    "DoubleVariable",
    "DrawDownArrowAction",
    "DrawUpArrowAction",
    "DrawVerticalLineAction",
    "Functions",
    "HeikenAshiPrice",
    "IntVariable",
    "LogToFileAction",
    "LogToJournalAction",
    "MAType",
    "MTFPrice",
    "NumberConstant",
    "QuotePrice",
    "SendEmailAction",
    "SessionPrice",
    "TimeConditions",
    "Types",
    "Variable",
    "abs_val",
    "assign_variable",
    "bars_to_dataframe",
    "bars_to_df",
    "boolean_constant",
    "boolean_variable",
    "calculate_ma",
    "calculate_wma",
    "condition_and",
    "condition_not",
    "condition_or",
    "convert_pips_to_price",
    "convert_pips_to_price_symbol",
    "convert_price_to_pips",
    "convert_price_to_pips_symbol",
    "crosses_above",
    "crosses_below",
    "custom_action",
    "custom_function",
    "division",
    "double_variable",
    "draw_down_arrow",
    "draw_up_arrow",
    "draw_vertical_line",
    "equals",
    "exponential",
    "format_timestamp",
    "get_date",
    "get_time",
    "indicator_above_ma",
    "indicator_below_ma",
    "indicator_crosses_above_ma",
    "indicator_crosses_below_ma",
    "indicator_highest",
    "indicator_lowest",
    "int_variable",
    "is_falling",
    "is_greater",
    "is_greater_count",
    "is_greater_or_equal",
    "is_greater_percentile",
    "is_lower",
    "is_lower_count",
    "is_lower_or_equal",
    "is_lower_percentile",
    "is_rising",
    "log_to_file",
    "log_to_journal",
    "logarithm",
    "maximum",
    "minimum",
    "minus",
    "multiplication",
    "normalize_timestamps",
    "not_equals",
    "number_constant",
    "plus",
    "register_custom_function",
    "resolve_shift_value",
    "round_to_decimals",
    "round_value",
    "send_email",
    "square_root",
    "ticks_to_dataframe",
    "ticks_to_df",
]
