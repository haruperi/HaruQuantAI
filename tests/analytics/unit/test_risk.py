"""Unit tests for Analytics risk evidence."""

from app.services.analytics.metrics.risk import calculate_risk_evidence
from app.utils import get_logger

logger = get_logger(__name__)

from tests.analytics.unit.test_results_adapter import _config  # noqa: E402


def test_risk_evidence_uses_cataloged_tail_convention() -> None:
    """Historical VaR and conditional VaR remain signed loss returns."""
    logger.debug("Testing Analytics historical tail convention")
    returns = (-0.20, -0.10, *([0.01] * 28))
    section = calculate_risk_evidence(returns, config=_config())
    metrics = {item.metric_key: item.value for item in section.metrics}
    assert metrics["value_at_risk"] < 0
    assert metrics["conditional_var"] <= metrics["value_at_risk"]
    assert metrics["volatility"] > 0
