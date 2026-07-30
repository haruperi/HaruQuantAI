"""Unit tests for API metric snapshot and Prometheus exposition."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.api import (
    build_metric_snapshot,
    create_in_process_metric_sink,
    export_prometheus_metrics,
)
from app.services.api.observability.errors import ValidationError


def test_exposition_is_deterministic() -> None:
    """Snapshots and render one stable deterministic payload."""
    sink = create_in_process_metric_sink()
    sink.record(
        "http_requests_total",
        Decimal(2),
        labels={"status": "500", "service": "api"},
    )
    sink.record(
        "cache_hits_total",
        Decimal(1),
        labels={"cache": "l1"},
    )
    sink.record(
        "http_requests_total",
        Decimal(1),
        labels={"service": "api", "status": "200"},
    )

    payload = export_prometheus_metrics(build_metric_snapshot(sink))

    assert payload == (
        "# HELP cache_hits_total cache_hits_total metric\n"
        "# TYPE cache_hits_total gauge\n"
        'cache_hits_total{cache="l1"} 1\n'
        "# HELP http_requests_total http_requests_total metric\n"
        "# TYPE http_requests_total gauge\n"
        'http_requests_total{service="api",status="200"} 1\n'
        'http_requests_total{service="api",status="500"} 2\n'
    )


def test_snapshot_does_not_mutate_sink() -> None:
    """Snapshot rendering must never alter sink state."""
    sink = create_in_process_metric_sink()
    sink.record("api_metric_total", Decimal(3), labels={"service": "api"})
    baseline = sink.snapshot()

    snapshot = build_metric_snapshot(sink)

    assert baseline == sink.snapshot()
    assert len(snapshot.samples) == 1


def test_build_metric_snapshot_respects_series_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Snapshot validation should fail when a bound is exceeded."""
    sink = create_in_process_metric_sink()
    sink.record("api_metric_total", Decimal(1), labels={"service": "api"})
    sink.record("cache_hits_total", Decimal(1), labels={"cache": "local"})

    monkeypatch.setenv("METRICS_MAX_SERIES", "1")

    with pytest.raises(ValidationError, match="METRICS_MAX_SERIES_EXCEEDED"):
        build_metric_snapshot(sink)
