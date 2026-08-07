"""Sequential replay and parallel determinism evidence for Analytics."""

from concurrent.futures import ThreadPoolExecutor

from app.utils import generate_id, get_logger

logger = get_logger(__name__)
from tests.analytics._support import _report  # noqa: E402


def test_identical_reports_are_equal_in_parallel() -> None:
    """Identical immutable inputs produce identical reports across threads."""
    logger.info("Testing Analytics parallel determinism")
    request_id = generate_id("req")
    with ThreadPoolExecutor(max_workers=4) as executor:
        reports = tuple(
            executor.map(
                lambda _index: _report(request_id=request_id)[0],
                range(8),
            )
        )
    assert all(report == reports[0] for report in reports[1:])
    assert all(
        report.hashes.report_hash == reports[0].hashes.report_hash
        for report in reports[1:]
    )
