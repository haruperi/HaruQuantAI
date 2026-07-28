"""Integration evidence for Analytics serialization and hashing."""

# ruff: noqa: INP001
from app.services.analytics import serialize_report
from app.utils import generate_id, logger
from tests.analytics._support import _report, unwrap


def test_serialization_and_hashes_are_deterministic() -> None:
    """Independent identical builds produce identical reports and serialization."""
    logger.debug("Testing Analytics serialization and hash workflow")
    request_id = generate_id("req")
    first, config = _report(request_id=request_id)
    second, _ = _report(request_id=request_id)
    assert first == second
    assert first.hashes.report_hash is not None
    assert unwrap(serialize_report(first, format_name="json", config=config)) == unwrap(
        serialize_report(second, format_name="json", config=config)
    )
