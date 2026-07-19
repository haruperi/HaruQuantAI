"""Unit tests for Analytics return evidence."""

# ruff: noqa: INP001

from decimal import Decimal

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.metrics.returns import calculate_return_evidence
from app.utils import logger
from tests.analytics.unit.test_results_adapter import _config, _source


def test_return_evidence_sorts_utc_and_records_frequency() -> None:
    """Return evidence preserves exact PnL and explicit short-series semantics."""
    logger.debug("Testing Analytics return evidence")
    result = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    section = calculate_return_evidence(result)
    metrics = {item.metric_key: item for item in section.metrics}
    assert metrics["net_pnl"].value == Decimal(9)
    assert metrics["ending_equity"].value == Decimal(1009)
    assert metrics["period_returns"].status == "undefined"
    assert metrics["cagr"].status == "calculated"
