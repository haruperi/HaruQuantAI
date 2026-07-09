"""Risk metrics and observability event sinks.

Defines protocols, event structures, and builders for recording risk decision
telemetry, latency metrics, and audit/persistence health indicators.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

from app.utils.logger import logger
from app.utils.observability import MetricRegistry

if TYPE_CHECKING:
    from app.services.risk.models import RiskDecisionPackage

# Global metric registry for risk events and performance
RISK_METRICS_REGISTRY = MetricRegistry()


class MetricsSink(Protocol):
    """Protocol for recording risk metrics to external sinks."""

    def record(
        self,
        *,
        name: str,
        kind: str,
        value: float,
        labels: Mapping[str, object] | None = None,
    ) -> None:
        """Record a single metric sample.

        Args:
            name: The metric identifier.
            kind: The metric type ('counter', 'gauge', 'histogram').
            value: The numeric metric value.
            labels: Metadata key-value labels.
        """
        ...


class InMemoryRiskMetricsSink:
    """In-memory metrics sink for testing and offline environments."""

    def __init__(self) -> None:
        """Initialize in-memory records storage."""
        self.records: list[dict[str, Any]] = []
        logger.debug("InMemoryRiskMetricsSink initialized.")

    def record(
        self,
        *,
        name: str,
        kind: str,
        value: float,
        labels: Mapping[str, object] | None = None,
    ) -> None:
        """Record a metric event in memory.

        Args:
            name: The metric identifier.
            kind: The metric type.
            value: The numeric value.
            labels: Metadata key-value labels.
        """
        self.records.append(
            {
                "name": name,
                "kind": kind,
                "value": value,
                "labels": labels or {},
            }
        )
        logger.debug(
            f"InMemoryRiskMetricsSink recorded metric: name={name}, "
            f"kind={kind}, value={value}, labels={labels}"
        )


@dataclass(frozen=True)
class RiskObservabilityEvent:
    """Observability event mapping to a structured metric.

    Args:
        name: The metric name.
        kind: The metric kind (counter, gauge, histogram).
        value: The numeric value.
        labels: String key-value tags.
    """

    name: str
    kind: str
    value: float
    labels: dict[str, str]


def emit_risk_metrics(event: RiskObservabilityEvent, sink: MetricsSink) -> None:
    """Emit an observability event to the metric sink.

    Args:
        event: The event to emit.
        sink: The destination metric sink.
    """
    logger.info(f"Emitting risk metric event: {event.name} = {event.value}")
    sink.record(
        name=event.name,
        kind=event.kind,
        value=event.value,
        labels=event.labels,
    )


def build_decision_metrics(
    decision: RiskDecisionPackage,
) -> tuple[RiskObservabilityEvent, ...]:
    """Produce count/rate/reason-code events from a decision.

    Args:
        decision: The decision package to process.

    Returns:
        tuple[RiskObservabilityEvent, ...]: The derived events.
    """
    logger.debug(f"Building decision metrics for decision ID: {decision.decision_id}")
    details = decision.details or {}
    policy_profile = details.get("policy_profile") or "unknown"
    mode = details.get("mode") or "unknown"

    status_str = (
        decision.status.value
        if hasattr(decision.status, "value")
        else str(decision.status)
    )

    labels = {
        "status": status_str,
        "reason_code": decision.rule_key or "unknown",
        "policy_profile": policy_profile,
        "mode": mode,
    }

    event = RiskObservabilityEvent(
        name="haruquant_risk_decision_total",
        kind="counter",
        value=1.0,
        labels=labels,
    )
    return (event,)


def build_latency_metric(
    operation: str,
    duration_ms: Decimal,
) -> RiskObservabilityEvent:
    """Produce a latency metric event.

    Args:
        operation: The name of the operation (e.g. 'governor', 'correlation').
        duration_ms: The duration in milliseconds.

    Returns:
        RiskObservabilityEvent: The latency event.
    """
    logger.debug(
        f"Building latency metric for operation: {operation}, duration={duration_ms} ms"
    )
    metric_name = f"haruquant_risk_{operation}_latency_ms"
    return RiskObservabilityEvent(
        name=metric_name,
        kind="histogram",
        value=float(duration_ms),
        labels={"operation": operation},
    )
