"""Unit tests for API workstation routes, schemas, event delivery, and observability metrics."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from app.services.api.observability.errors import SecurityError, ValidationError
from app.services.api.observability.metrics import (
    _validate_metric_name,
    _validate_metric_value,
    record_metric,
    validate_metric_labels,
)
from app.services.api.workstation.agentic.schemas import (
    AgenticRunSubmitRequest,
)
from app.services.api.workstation.event_delivery.events import (
    StreamValidationError,
    _assert_secret_free,
)
from app.services.api.workstation.indicators.schemas import (
    _json_value,
)


def test_agentic_run_submit_request_schema() -> None:
    """Verify AgenticRunSubmitRequest schema validation."""
    req = AgenticRunSubmitRequest(
        workflow_name="fundamental_analysis",
        objective="Evaluate AAPL filings and earnings report",
        input_refs=("doc-1", "doc-2"),
        deadline_seconds=3600,
    )
    assert req.workflow_name == "fundamental_analysis"
    assert req.deadline_seconds == 3600


def test_indicator_schemas_json_value() -> None:
    """Verify _json_value converts floats and handles NaN/None."""
    assert _json_value(10.5) == 10.5
    assert _json_value(None) is None
    assert _json_value(float("nan")) is None


def test_event_delivery_events_validation() -> None:
    """Verify build_stream_event secret-free check and nesting assertion."""
    with pytest.raises(StreamValidationError, match="contains a forbidden key"):
        _assert_secret_free({"api_key": "secret"})  # pragma: allowlist secret

    nested = {
        "level1": {
            "level2": {
                "level3": {
                    "level4": {
                        "level5": {"level6": {"level7": {"level8": {"level9": 1}}}}
                    }
                }
            }
        }
    }
    with pytest.raises(StreamValidationError, match="exceeds nesting limit"):
        _assert_secret_free(nested)


def test_observability_metrics_validation() -> None:
    """Verify metric name, value, label validation, and record_metric."""
    assert _validate_metric_name("http_requests_total") == "http_requests_total"
    with pytest.raises(ValidationError):
        _validate_metric_name("123_invalid_name!")

    assert _validate_metric_value(Decimal("1.5")) == Decimal("1.5")
    with pytest.raises(ValidationError):
        _validate_metric_value(Decimal("NaN"))

    validate_metric_labels({"env": "sandbox"})
    with pytest.raises(SecurityError):
        validate_metric_labels({"api_key": "secret"})  # pragma: allowlist secret

    mock_sink = MagicMock()
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("METRICS_ENABLED", "true")
        record_metric(
            "test_metric", Decimal(10), labels={"route": "/test"}, sink=mock_sink
        )
    mock_sink.record.assert_called_once()
