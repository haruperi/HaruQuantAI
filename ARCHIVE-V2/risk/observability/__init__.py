"""Risk metrics and boundary decorators observability package."""

from __future__ import annotations

from app.services.risk.observability.decorators import (
    RiskBoundaryEvent,
    RiskLogger,
    log_risk_boundary_event,
    measure_risk_latency,
    risk_observed,
)
from app.services.risk.observability.metrics import (
    RISK_METRICS_REGISTRY,
    InMemoryRiskMetricsSink,
    MetricsSink,
    RiskObservabilityEvent,
    build_decision_metrics,
    build_latency_metric,
    emit_risk_metrics,
)

__all__ = [
    "RISK_METRICS_REGISTRY",
    "InMemoryRiskMetricsSink",
    "MetricsSink",
    "RiskBoundaryEvent",
    "RiskLogger",
    "RiskObservabilityEvent",
    "build_decision_metrics",
    "build_latency_metric",
    "emit_risk_metrics",
    "log_risk_boundary_event",
    "measure_risk_latency",
    "risk_observed",
]
