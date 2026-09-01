"""Integration evidence for deterministic grouped Analytics metrics."""

from app.composition.logging import get_logger
from app.services.analytics import calculate_grouped_evidence

logger = get_logger(__name__)
from tests.analytics._support import _configured_result, unwrap  # noqa: E402


def test_grouped_evidence_preserves_source_context() -> None:
    """The composed trade section distinguishes all, long, and short evidence."""
    logger.debug("Testing Analytics grouped source contexts")
    result, config = _configured_result()
    trade_section = unwrap(calculate_grouped_evidence(result, config=config))[0]
    contexts = {metric.source_context for metric in trade_section.metrics}
    assert contexts == {"all", "long", "short"}
