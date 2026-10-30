"""Stable metric dependency resolution and DAG ordering."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.core.lib.errors import DomainError, JSONValue


@dataclass(frozen=True, slots=True)
class MetricDependency:
    """Descriptor defining metric identifier and its prerequisite dependencies."""

    metric_id: str
    depends_on: tuple[str, ...] = ()


def order_metrics(
    metrics: Sequence[MetricDependency],
) -> tuple[MetricDependency, ...]:
    """Order metric descriptors before evaluation according to dependency graph.

    Performs stable multi-pass scanning over a detached copy of pending descriptors.
    Dependencies resolved earlier in the same scan are immediately visible to subsequent
    descriptors.

    Args:
        metrics: Sequence of MetricDependency descriptors to order.

    Returns:
        Tuple of MetricDependency descriptors sorted in topological dependency order.

    Raises:
        DomainError:
            - With code 'INVALID_METRIC_REGISTRY' if any metric identifier is empty
              or duplicate.
            - With code 'UNRESOLVED_METRIC_DEPENDENCY' and details containing
              unresolved pending IDs if a cycle or missing dependency prevents progress.
    """
    seen_ids: set[str] = set()
    for item in metrics:
        if not isinstance(item.metric_id, str) or not item.metric_id:
            raise DomainError(
                code="INVALID_METRIC_REGISTRY",
                message="Metric identifiers must be unique and non-empty",
            )
        if item.metric_id in seen_ids:
            raise DomainError(
                code="INVALID_METRIC_REGISTRY",
                message="Metric identifiers must be unique and non-empty",
            )
        seen_ids.add(item.metric_id)

    ordered: list[MetricDependency] = []
    resolved_ids: set[str] = set()
    pending: list[MetricDependency] = list(metrics)

    while pending:
        made_progress = False
        next_pending: list[MetricDependency] = []

        for item in pending:
            if all(dep in resolved_ids for dep in item.depends_on):
                ordered.append(item)
                resolved_ids.add(item.metric_id)
                made_progress = True
            else:
                next_pending.append(item)

        if not made_progress:
            pending_ids: list[JSONValue] = [item.metric_id for item in next_pending]
            raise DomainError(
                code="UNRESOLVED_METRIC_DEPENDENCY",
                message="Metric dependencies cannot be resolved",
                details={"pending_ids": pending_ids},
            )

        pending = next_pending

    return tuple(ordered)


__all__ = ["MetricDependency", "order_metrics"]
