"""Bounded reference performance evidence for Analytics reporting."""

import time
import tracemalloc

from app.composition.logging import get_logger

logger = get_logger(__name__)

from tests.analytics._support import _report  # noqa: E402

_MAX_REFERENCE_SECONDS = 5.0
_MAX_REFERENCE_PEAK_BYTES = 64 * 1024 * 1024


def test_reference_report_runtime_and_memory_are_bounded() -> None:
    """A canonical bounded report stays within the documented local baseline."""
    logger.info("Testing Analytics reference runtime and memory bounds")
    tracemalloc.start()
    started = time.perf_counter()
    try:
        report, _ = _report()
        elapsed = time.perf_counter() - started
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert report.sections
    assert elapsed < _MAX_REFERENCE_SECONDS
    assert peak_bytes < _MAX_REFERENCE_PEAK_BYTES
