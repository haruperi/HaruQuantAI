"""Public observability boundary API."""

from app.services.api.observability.exposition import (
    build_metric_snapshot,
    export_prometheus_metrics,
    get_metrics,
)
from app.services.api.observability.metrics import (
    _metrics_enabled,
    record_metric,
    validate_metric_labels,
)
from app.services.api.observability.sinks import InProcessMetricSink, MetricSink


def create_in_process_metric_sink(
    *,
    max_series: int | None = None,
    max_label_cardinality: int | None = None,
) -> MetricSink:
    """Create one explicit in-process sink with optional limits.

    Returns:
        The validated, bounded result.
    """
    return InProcessMetricSink(
        max_series=max_series,
        max_label_cardinality=max_label_cardinality,
    )


def is_metrics_enabled() -> bool:
    """Return whether observability ingestion and exposition are enabled."""
    return _metrics_enabled()


__all__ = (
    "build_metric_snapshot",
    "create_in_process_metric_sink",
    "export_prometheus_metrics",
    "get_metrics",
    "is_metrics_enabled",
    "record_metric",
    "validate_metric_labels",
)
