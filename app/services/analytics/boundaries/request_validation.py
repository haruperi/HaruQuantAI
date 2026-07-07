"""Request schema and ID validations for Analytics boundaries.

All calculations are stateless pure functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.utils.errors import ValidationError

if TYPE_CHECKING:
    from app.services.analytics.boundaries.limits import AnalyticsLimits


def request_id(
    input_value: object,
    config: MetricConfig,  # noqa: ARG001
) -> MetricResult[object]:
    """Validate and wrap request ID into a MetricResult wrapper."""
    if input_value is not None and (
        not isinstance(input_value, str) or not input_value.strip()
    ):
        msg = "request_id must be a non-empty string when supplied."
        raise ValidationError(msg)
    return MetricResult(value=input_value)


def float64(
    input_value: object,
    config: MetricConfig,  # noqa: ARG001
) -> MetricResult[object]:
    """Float64 validation and casting boundary wrapper."""
    try:
        val = float(input_value)  # type: ignore[arg-type]
        return MetricResult(value=val)
    except (TypeError, ValueError) as e:
        msg = f"Value {input_value} is not a valid float."
        raise ValidationError(msg) from e


def validate_request(
    request: object,
    request_id_val: str,
    limits: AnalyticsLimits,
) -> None:
    """Validate request trace ID and workload limits shape before processing."""
    if not isinstance(request_id_val, str) or not request_id_val.strip():
        msg = "request_id must be a non-empty string."
        raise ValidationError(msg)

    if request is not None and isinstance(request, dict):
        trades = request.get("trades") or []
        if len(trades) > limits.max_trades:
            msg = f"Trades count {len(trades)} exceeds limit {limits.max_trades}."
            raise ValidationError(msg)

        equity_curve = request.get("equity_curve") or []
        if len(equity_curve) > limits.max_equity_points:
            msg = (
                f"Equity curve points {len(equity_curve)} "
                f"exceeds limit {limits.max_equity_points}."
            )
            raise ValidationError(msg)
