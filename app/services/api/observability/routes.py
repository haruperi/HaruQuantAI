"""Metrics exposition HTTP boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, cast

from fastapi import APIRouter, Depends

from app.services.api import create_in_process_metric_sink
from app.services.api.identity import require_auth_context
from app.services.api.observability import get_metrics

if TYPE_CHECKING:
    from app.services.api.observability.sinks import MetricSink

type AuthContext = Any

router = APIRouter(prefix="/api/v1", tags=["observability"])


def _metrics_sink() -> object:
    """Return one boundary-default in-process metrics sink."""
    return create_in_process_metric_sink()


@router.get("/metrics")
def _get_metrics(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    sink: Annotated[object, Depends(_metrics_sink)],
) -> object:
    """Serve protected Prometheus exposition.

    Returns:
        The validated, bounded result.
    """
    return get_metrics(context, sink=cast("MetricSink", sink))


__all__ = ("router",)
