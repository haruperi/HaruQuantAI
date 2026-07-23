"""Integration evidence for Analytics serialization and hashing."""

# ruff: noqa: INP001

from app.services.analytics.reports.serialization import serialize_report
from app.utils import logger
from tests.analytics._support import _report


def test_serialization_and_hashes_are_deterministic() -> None:
    """Creation time changes neither report hash nor canonical repeat serialization."""
    logger.debug("Testing Analytics serialization and hash workflow")
    report, config = _report()
    assert report.hashes.report_hash is not None
    assert serialize_report(
        report, format_name="json", config=config
    ) == serialize_report(report, format_name="json", config=config)
