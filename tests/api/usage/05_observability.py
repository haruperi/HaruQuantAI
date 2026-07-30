"""Usage examples for operational telemetry and exposition."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace

from app.services.api import (
    build_metric_snapshot,
    create_in_process_metric_sink,
    export_prometheus_metrics,
    get_metrics,
    record_metric,
    validate_metric_labels,
)


@contextmanager
def _metrics_enabled() -> Iterator[None]:
    """Temporarily enable metrics for usage script execution."""
    previous = os.environ.get("METRICS_ENABLED")
    os.environ["METRICS_ENABLED"] = "true"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("METRICS_ENABLED", None)
        else:
            os.environ["METRICS_ENABLED"] = previous


def _context() -> object:
    """Build one synthetic auth context for scrape examples."""
    return SimpleNamespace(
        principal_type="USER",
        permissions=("ops:metrics:read",),
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def fr_api_060() -> dict[str, object]:
    """Record a metric through an explicitly injected sink."""
    with _metrics_enabled():
        sink = create_in_process_metric_sink()
        record_metric(
            "api_requests_total",
            Decimal(1),
            labels={"service": "api", "endpoint": "/api/metrics"},
            sink=sink,
        )
        return {"samples": len(sink.snapshot())}


def fr_api_061() -> dict[str, object]:
    """Validate sensitive-key rejection and cardinality limits."""
    sensitive_rejected = False
    cardinality_rejected = False

    try:
        with _metrics_enabled():
            validate_metric_labels(
                {"api_key": "redacted-value"},  # pragma: allowlist secret
            )
    except ValueError:
        sensitive_rejected = True

    sink = create_in_process_metric_sink(max_label_cardinality=1)
    with _metrics_enabled():
        record_metric(
            "api_requests_total",
            Decimal(1),
            labels={"service": "api", "environment": "prod"},
            sink=sink,
        )
        try:
            record_metric(
                "api_requests_total",
                Decimal(1),
                labels={"service": "api", "environment": "staging"},
                sink=sink,
            )
        except ValueError:
            cardinality_rejected = True

    return {
        "sensitive_rejected": sensitive_rejected,
        "cardinality_rejected": cardinality_rejected,
    }


def fr_api_062() -> dict[str, object]:
    """Build one bounded snapshot and render Prometheus exposition."""
    sink = create_in_process_metric_sink()
    sink.record("api_requests_total", Decimal(2), labels={"service": "api"})
    snapshot = build_metric_snapshot(sink)
    payload = export_prometheus_metrics(snapshot)
    return {"line_count": payload.count("\n"), "has_payload": bool(payload)}


def fr_api_063() -> dict[str, object]:
    """Expose protected scrape payload through explicit-sink `get_metrics`."""
    with _metrics_enabled():
        sink = create_in_process_metric_sink()
        record_metric(
            "api_requests_total",
            Decimal(1),
            labels={"service": "api"},
            sink=sink,
        )
        response = get_metrics(_context(), sink=sink)
        return {
            "status": response.status,
            "route": response.metadata.route,
            "payload_has_metric": "api_requests_total" in str(response.data),
        }


def main() -> None:
    """Run observability usage scenarios."""
    print(fr_api_060())
    print(fr_api_061())
    print(fr_api_062())
    print(fr_api_063())


if __name__ == "__main__":
    main()
