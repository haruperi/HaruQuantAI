"""Unit tests for the Risk Governance observability module."""

from decimal import Decimal

import pytest
from app.services.risk.models import RiskDecisionPackage
from app.services.risk.models.enums import RiskDecisionStatus
from app.services.risk.observability.decorators import (
    RiskBoundaryEvent,
    log_risk_boundary_event,
    measure_risk_latency,
    risk_observed,
)
from app.services.risk.observability.metrics import (
    InMemoryRiskMetricsSink,
    RiskObservabilityEvent,
    build_decision_metrics,
    build_latency_metric,
    emit_risk_metrics,
)


class DummyLogger:
    """Mock logger to capture logging statements."""

    def __init__(self):
        self.infos = []
        self.debugs = []
        self.errors = []
        self.warnings = []

    def info(self, msg, *args, **kwargs):
        self.infos.append(msg)

    def debug(self, msg, *args, **kwargs):
        self.debugs.append(msg)

    def error(self, msg, *args, **kwargs):
        self.errors.append(msg)

    def warning(self, msg, *args, **kwargs):
        self.warnings.append(msg)


def test_metrics_sink_and_emit():
    """Verify that InMemoryRiskMetricsSink correctly stores metrics and emit helper works."""
    sink = InMemoryRiskMetricsSink()
    event = RiskObservabilityEvent(
        name="test_metric",
        kind="counter",
        value=1.5,
        labels={"lbl": "val"},
    )
    emit_risk_metrics(event, sink)
    assert len(sink.records) == 1
    assert sink.records[0]["name"] == "test_metric"
    assert sink.records[0]["value"] == 1.5
    assert sink.records[0]["labels"]["lbl"] == "val"


def test_build_decision_metrics():
    """Verify that decision metrics are built correctly from a RiskDecisionPackage."""
    decision = RiskDecisionPackage(
        decision_id="dec_123",
        request_id="req_123",
        workflow_id="wf_123",
        status=RiskDecisionStatus.APPROVE,
        rule_key="news_blackout",
        snapshot_as_of="2026-07-08T12:00:00Z",
        config_hash="cfg_hash",
        reason="Test reason",
        details={"policy_profile": "paper", "mode": "simulation"},
    )
    events = build_decision_metrics(decision)
    assert len(events) == 1
    assert events[0].name == "haruquant_risk_decision_total"
    assert events[0].labels["status"] == "approve"
    assert events[0].labels["policy_profile"] == "paper"
    assert events[0].labels["mode"] == "simulation"


def test_build_latency_metric():
    """Verify latency metric creation."""
    event = build_latency_metric("test_op", Decimal("150.5"))
    assert event.name == "haruquant_risk_test_op_latency_ms"
    assert event.value == 150.5
    assert event.labels["operation"] == "test_op"


def test_risk_observed_decorator():
    """Verify that the risk_observed decorator records metrics, logs start/end and catches errors."""
    sink = InMemoryRiskMetricsSink()
    dlogger = DummyLogger()

    @risk_observed("dummy_op", sink, dlogger)
    def dummy_func(x: int) -> int:
        return x + 1

    @risk_observed("failing_op", sink, dlogger)
    def failing_func():
        raise ValueError("failing func error")

    # Success case
    res = dummy_func(10)
    assert res == 11
    assert len(sink.records) == 1
    assert sink.records[0]["name"] == "haruquant_risk_dummy_op_latency_ms"
    assert len(dlogger.infos) == 2
    assert "Starting risk" in dlogger.infos[0]
    assert "completed in" in dlogger.infos[1]

    # Failure case
    with pytest.raises(ValueError, match="failing func error"):
        failing_func()

    assert len(sink.records) == 2
    assert sink.records[1]["name"] == "haruquant_risk_failing_op_latency_ms"
    assert len(dlogger.errors) == 1
    assert "failed in" in dlogger.errors[0]


def test_measure_risk_latency_decorator():
    """Verify measure_risk_latency decorator."""
    sink = InMemoryRiskMetricsSink()

    @measure_risk_latency("latency_op", sink)
    def timed_func():
        return 42

    res = timed_func()
    assert res == 42
    assert len(sink.records) == 1
    assert sink.records[0]["name"] == "haruquant_risk_latency_op_latency_ms"


def test_log_risk_boundary_event():
    """Verify log_risk_boundary_event function writes to logger."""
    dlogger = DummyLogger()
    event = RiskBoundaryEvent("ev_1", "message info", {"meta": "val"})
    log_risk_boundary_event(event, dlogger)
    assert len(dlogger.infos) == 1
    assert "[ev_1]" in dlogger.infos[0]
    assert "message info" in dlogger.infos[0]
