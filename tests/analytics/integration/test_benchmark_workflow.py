"""Integration evidence for the Analytics benchmark workflow."""

# ruff: noqa: INP001

from app.services.analytics.metrics.benchmarks import calculate_benchmark_evidence
from app.utils import logger
from tests.analytics._support import _configured_result


def test_benchmark_alignment_is_utc_and_window_bounded() -> None:
    """Benchmark evidence uses only the canonical strategy-window intersection."""
    logger.debug("Testing Analytics benchmark workflow")
    result, config = _configured_result(benchmark=True)
    section = calculate_benchmark_evidence(result, config=config)
    assert section.section_key == "benchmark"
    assert {metric.source_context for metric in section.metrics} == {"benchmark"}
