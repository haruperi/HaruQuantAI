"""Unit tests for closed-trade Analytics evidence."""

# ruff: noqa: INP001

from decimal import Decimal

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.metrics.trades import calculate_trade_evidence
from app.utils import logger
from tests.analytics.unit.test_results_adapter import _config, _source


def test_trade_evidence_filters_open_and_placeholder_trades() -> None:
    """Canonical adaptation leaves only closed ledger rows for classification."""
    logger.debug("Testing Analytics closed-trade classification")
    result = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    section = calculate_trade_evidence(result, config=_config())
    metrics = {item.metric_key: item.value for item in section.metrics}
    assert metrics["trade_count"] == 1
    assert metrics["win_count"] == 1
    assert metrics["r_multiple"] == 1.0


def test_trade_evidence_preserves_direction_context() -> None:
    """A missing short side is explicit undefined evidence rather than fabrication."""
    logger.debug("Testing Analytics direction source context")
    result = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    section = calculate_trade_evidence(result, config=_config(), source_context="short")
    metrics = {item.metric_key: item for item in section.metrics}
    assert metrics["trade_count"].value == 0
    assert metrics["win_rate"].status == "undefined"
