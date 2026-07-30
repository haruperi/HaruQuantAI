"""Unit tests for API metric recording and label hygiene."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.api import (
    create_in_process_metric_sink,
    record_metric,
    validate_metric_labels,
)
from app.services.api.observability.errors import SecurityError, ValidationError


class _CountingSink:
    """Sink that records validation and record invocations."""

    def __init__(self) -> None:
        self.validate_calls = 0
        self.record_calls = 0
        self.records: list[tuple[str, Decimal, tuple[tuple[str, str], ...]]] = []

    def validate_labels(self, labels: object) -> None:
        """Record one validation request."""
        self.validate_calls += 1
        del labels

    def record(
        self,
        name: str,
        value: Decimal,
        *,
        labels: object,
    ) -> None:
        """Record one validated sample."""
        self.record_calls += 1
        self.records.append((name, value, tuple(sorted(labels.items()))))

    def snapshot(self) -> tuple[tuple[str, Decimal, tuple[tuple[str, str], ...]], ...]:
        """Expose recorded tuples in sink shape."""
        return tuple((name, value, labels) for name, value, labels in self.records)


def _context_labels() -> dict[str, str]:
    """Return one stable label mapping."""
    return {"service": "api", "endpoint": "/api/metrics"}


def test_record_metric_uses_injected_sink_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify record_metric mutates only the explicitly injected sink."""
    monkeypatch.setenv("METRICS_ENABLED", "true")
    sink = _CountingSink()

    record_metric(
        "api_metric_total",
        Decimal(1),
        labels=_context_labels(),
        sink=sink,
    )

    assert sink.validate_calls == 1
    assert sink.record_calls == 1
    assert sink.records == [
        (
            "api_metric_total",
            Decimal(1),
            (("endpoint", "/api/metrics"), ("service", "api")),
        ),
    ]


def test_disabled_metrics_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify disabled metrics does not touch the injected sink."""
    monkeypatch.setenv("METRICS_ENABLED", "false")
    sink = _CountingSink()
    record_metric(
        "api_metric_total",
        Decimal(1),
        labels=_context_labels(),
        sink=sink,
    )
    assert sink.validate_calls == 0
    assert sink.record_calls == 0


def test_secret_bearing_label_rejected() -> None:
    """Verify label keys matching denylist fail before sink mutation."""
    with pytest.raises(SecurityError, match="METRICS_LABEL_INVALID"):
        validate_metric_labels(
            {"api_key": "redacted-value"},  # pragma: allowlist secret
        )


def test_high_cardinality_label_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify cardinality bound is enforced before writing a second unseen value."""
    monkeypatch.setenv("METRICS_ENABLED", "true")
    sink = create_in_process_metric_sink(max_label_cardinality=1)
    record_metric(
        "api_metric_total",
        Decimal(1),
        labels={"service": "api", "env": "prod"},
        sink=sink,
    )

    with pytest.raises(ValidationError, match="METRICS_LABEL_CARDINALITY_EXCEEDED"):
        record_metric(
            "api_metric_total",
            Decimal(1),
            labels={"service": "api", "env": "staging"},
            sink=sink,
        )
