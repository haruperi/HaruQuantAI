"""Internal export boundary for Analytics persistence.

Private support package. Nothing here is part of the Analytics public API;
callers reach it through ``app.services.analytics``.
"""

from app.services.analytics.persistence.create import (
    create_equity_curve_record,
    create_metric_definition_record,
    create_metric_value_record,
    create_pnl_attribution_record,
    create_report_record,
    create_trade_analysis_record,
)
from app.services.analytics.persistence.read import (
    read_metric_value,
    read_stale_metric_values,
    read_trades_for_strategy,
    read_worst_drawdowns,
)
from app.services.analytics.persistence.update import (
    mark_equity_curves_stale,
    update_report_state,
)

__all__ = [
    "create_equity_curve_record",
    "create_metric_definition_record",
    "create_metric_value_record",
    "create_pnl_attribution_record",
    "create_report_record",
    "create_trade_analysis_record",
    "mark_equity_curves_stale",
    "read_metric_value",
    "read_stale_metric_values",
    "read_trades_for_strategy",
    "read_worst_drawdowns",
    "update_report_state",
]
