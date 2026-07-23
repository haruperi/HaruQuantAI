"""Integration evidence for deterministic grouped Analytics metrics."""

# ruff: noqa: INP001

from app.services.analytics.metrics.groups import calculate_grouped_evidence
from app.utils import logger
from tests.analytics._support import _configured_result


def test_grouped_evidence_preserves_source_context() -> None:
    """The composed trade section distinguishes all, long, and short evidence."""
    logger.debug("Testing Analytics grouped source contexts")
    result, config = _configured_result()
    trade_section = calculate_grouped_evidence(result, config=config)[0]
    contexts = {metric.source_context for metric in trade_section.metrics}
    assert contexts == {"all", "long", "short"}
