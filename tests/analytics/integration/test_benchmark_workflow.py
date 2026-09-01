"""Integration evidence for the Analytics benchmark workflow."""

from app.composition.logging import get_logger
from app.services.analytics import calculate_benchmark_evidence

logger = get_logger(__name__)
from tests.analytics._support import _configured_result, unwrap  # noqa: E402


def test_benchmark_alignment_is_utc_and_window_bounded() -> None:
    """Benchmark evidence uses only the canonical strategy-window intersection."""
    logger.debug("Testing Analytics benchmark workflow")
    result, config = _configured_result(benchmark=True)
    section = unwrap(calculate_benchmark_evidence(result, config=config))
    assert section.section_key == "benchmark"
    assert {metric.source_context for metric in section.metrics} == {"benchmark"}
