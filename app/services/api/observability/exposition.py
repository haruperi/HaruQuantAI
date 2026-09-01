"""Metric snapshot and Prometheus-text exposition helpers."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Final

from fastapi import HTTPException, status

from app.kernel.time import utc_now
from app.services.api.contracts.models import ApiMetadata, ApiResponse, ApiStatus
from app.services.api.identity import require_human_permission
from app.services.api.observability.errors import ValidationError
from app.services.api.observability.metrics import _metrics_enabled

if TYPE_CHECKING:
    from app.services.api.observability.sinks import MetricSample, MetricSink

type AuthContext = Any

_MAX_SERIES_DEFAULT: Final = 5000
_SNAPSHOT_ROUTE: Final = "/api/v1/metrics"
_SNAPSHOT_OPERATION: Final = "api.get_metrics"
_METRIC_NAME_PATTERN = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
_LABEL_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_LABEL_PAIR_SIZE: Final = 2
_METRIC_SAMPLE_SIZE: Final = 3


def _to_int_env(value: str, *, env_name: str) -> int:
    """Parse one strict positive integer setting.

    Returns:
        The validated, bounded result.

    Raises:
        ValidationError: If the declared validation fails.
    """
    try:
        parsed = int(value.strip())
    except ValueError as error:
        msg = f"{env_name}_INVALID"
        raise ValidationError(msg) from error
    if parsed < 1:
        msg = f"{env_name}_INVALID"
        raise ValidationError(msg)
    return parsed


def _max_series() -> int:
    """Return the configured snapshot series limit."""
    return _to_int_env(
        os.getenv("METRICS_MAX_SERIES", str(_MAX_SERIES_DEFAULT)),
        env_name="METRICS_MAX_SERIES",
    )


def _scrape_permission() -> str:
    """Return the configured scrape permission."""
    return os.getenv("METRICS_SCRAPE_PERMISSION", "ops:metrics:read")


def _escape_label(value: str) -> str:
    """Escape one Prometheus label value.

    Returns:
        The validated, bounded result.
    """
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
    """Render one deterministic label block.

    Returns:
        The validated, bounded result.
    """
    if not labels:
        return ""
    rendered = [f'{key}="{_escape_label(value)}"' for key, value in labels]
    return "{" + ",".join(rendered) + "}"


def _normalize_label_items(labels: object) -> tuple[tuple[str, str], ...]:
    """Normalize one canonical label tuple.

    Returns:
        The validated, bounded result.

    Raises:
        ValidationError: If the declared validation fails.
    """
    if isinstance(labels, tuple):
        normalized: list[tuple[str, str]] = []
        for item in labels:
            if not isinstance(item, tuple) or len(item) != _LABEL_PAIR_SIZE:
                raise ValidationError("METRICS_LABELS_MALFORMED")
            key, value = item
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValidationError("METRICS_LABELS_MALFORMED")
            normalized_key = key.strip()
            normalized_value = value.strip()
            if not normalized_key or not _LABEL_NAME_PATTERN.fullmatch(normalized_key):
                raise ValidationError("METRICS_LABEL_KEY_INVALID")
            if not normalized_value:
                raise ValidationError("METRICS_LABEL_VALUE_INVALID")
            normalized.append((normalized_key, normalized_value))
        return tuple(sorted(normalized))
    raise ValidationError("METRICS_LABELS_MALFORMED")


def _normalize_sample(
    sample: object,
) -> tuple[str, Decimal, tuple[tuple[str, str], ...]]:
    """Normalize one metric sample from a sink snapshot.

    Returns:
        The validated, bounded result.

    Raises:
        ValidationError: If the declared validation fails.
    """
    if not isinstance(sample, tuple) or len(sample) != _METRIC_SAMPLE_SIZE:
        raise ValidationError("METRICS_SNAPSHOT_INVALID")
    name, value, labels = sample
    if not isinstance(name, str) or not _METRIC_NAME_PATTERN.fullmatch(name):
        raise ValidationError("METRICS_NAME_INVALID")
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValidationError("METRICS_VALUE_INVALID")
    normalized_labels = _normalize_label_items(labels)
    return name, value, normalized_labels


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    """Immutable point-in-time metric snapshot."""

    samples: tuple[MetricSample, ...]


def build_metric_snapshot(sink: MetricSink) -> MetricSnapshot:
    """Build one bounded metric snapshot without mutating sink state.

    Returns:
        The validated, bounded result.

    Raises:
        ValidationError: If the declared validation fails.
    """
    samples = tuple(_normalize_sample(sample) for sample in sink.snapshot())
    if len(samples) > _max_series():
        raise ValidationError("METRICS_MAX_SERIES_EXCEEDED")
    return MetricSnapshot(samples=samples)


def export_prometheus_metrics(snapshot: MetricSnapshot) -> str:
    """Render one deterministic Prometheus text exposition.

    Returns:
        The validated, bounded result.
    """
    lines: list[str] = []
    rendered = sorted(snapshot.samples, key=lambda sample: (sample[0], sample[2]))
    current_metric: str | None = None
    for name, value, labels in rendered:
        if current_metric != name:
            lines.append(f"# HELP {name} {name} metric")
            lines.append(f"# TYPE {name} gauge")
            current_metric = name
        labels_block = _format_labels(labels)
        lines.append(f"{name}{labels_block} {value}")
    lines.append("")
    return "\n".join(lines)


def get_metrics(
    context: AuthContext,
    *,
    sink: MetricSink,
) -> ApiResponse[str]:
    """Build one read-only exposition response from a provided sink.

    Returns:
        The validated, bounded result.

    Raises:
        HTTPException: If the declared validation fails.
    """
    if not _metrics_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="METRICS_DISABLED",
        )
    require_human_permission(context, _scrape_permission())
    payload = export_prometheus_metrics(build_metric_snapshot(sink))
    metadata = ApiMetadata(
        request_id=context.request_id,
        route=_SNAPSHOT_ROUTE,
        operation=_SNAPSHOT_OPERATION,
        trace_id=context.correlation_id,
    )
    return ApiResponse(
        status=ApiStatus.SUCCESS,
        message="metrics exposition rendered",
        data=payload,
        metadata=metadata.model_copy(update={"timestamp": utc_now()}),
    )


__all__ = (
    "MetricSnapshot",
    "build_metric_snapshot",
    "export_prometheus_metrics",
    "get_metrics",
)
