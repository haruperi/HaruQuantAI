"""Unit tests for bounded Analytics report serialization."""

# ruff: noqa: INP001

import json
from dataclasses import replace

import pytest
from app.services.analytics.contracts import AnalyticsValidationError
from app.services.analytics.reports.serialization import serialize_report
from app.utils import logger
from tests.analytics.usage.test_usage_reports import _report


def test_serialize_report_json_is_canonical() -> None:
    """Canonical JSON is stable and retains cross-domain schema identity."""
    logger.debug("Testing canonical Analytics report serialization")
    report, config = _report()
    first = serialize_report(report, format_name="json", config=config)
    second = serialize_report(report, format_name="json", config=config)
    assert first == second
    assert json.loads(first)["schema_id"] == "analytics.performance_report.v1"


def test_serialize_report_enforces_response_bound() -> None:
    """An undersized response bound fails before returning output."""
    logger.debug("Testing Analytics serialized response bound")
    report, config = _report()
    bounded = replace(config, max_response_bytes=1)
    with pytest.raises(AnalyticsValidationError, match="exceeds"):
        serialize_report(report, format_name="text", config=bounded)
