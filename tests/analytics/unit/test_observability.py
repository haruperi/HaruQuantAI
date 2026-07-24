"""Structured boundary-observability tests for Analytics."""

# ruff: noqa: INP001
import logging
from decimal import Decimal

import pytest
from app.services.analytics import AnalyticsValidationError, build_performance_report
from app.utils import generate_id, logger
from tests.analytics._support import NOW, _configured, _source


class _RecordCollector(logging.Handler):
    """Collect emitted standard-library log records."""

    def __init__(self) -> None:
        """Initialize the empty record collection."""
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Collect one log record.

        Args:
            record: Emitted record.
        """
        self.records.append(record)


def test_report_boundary_logs_identifiers_and_validation_failure() -> None:
    """The public report boundary logs safe IDs and a controlled failure."""
    logger.info("Testing Analytics structured boundary logging")
    collector = _RecordCollector()
    domain_logger = logging.getLogger("haruquant")
    previous_level = domain_logger.level
    domain_logger.setLevel(logging.DEBUG)
    domain_logger.addHandler(collector)
    request_id = generate_id("req")
    correlation_id = generate_id("cor")
    try:
        with pytest.raises(AnalyticsValidationError):
            build_performance_report(
                _source(),
                source_contract="simulation.result",
                request_id=request_id,
                correlation_id=correlation_id,
                created_at=NOW,
                initial_balance=Decimal(0),
                account_currency="USD",
                config=_configured(),
            )
    finally:
        domain_logger.removeHandler(collector)
        domain_logger.setLevel(previous_level)
    boundary_records = [
        record
        for record in collector.records
        if getattr(record, "operation", None) == "build_performance_report"
    ]
    assert [record.getMessage() for record in boundary_records] == [
        "Analytics public operation started",
        "Analytics public operation validation failed",
    ]
    assert all(
        getattr(record, "request_id", None) == request_id for record in boundary_records
    )
    assert all(
        getattr(record, "correlation_id", None) == correlation_id
        for record in boundary_records
    )
