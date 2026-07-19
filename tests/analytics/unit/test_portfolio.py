"""Unit tests for currency-safe Analytics portfolio composition."""

# ruff: noqa: INP001

import pytest
from app.services.analytics.contracts import AnalyticsValidationError
from app.services.analytics.reports.portfolio import build_portfolio_performance_report
from app.utils import logger
from tests.analytics.usage.test_usage_reports import _report


def test_portfolio_builder_never_sums_mixed_currency_raw_pnl() -> None:
    """Mixed component currencies block when exact FX evidence is absent."""
    logger.debug("Testing Analytics mixed-currency portfolio blocker")
    usd, config = _report(account_currency="USD")
    eur, _ = _report(account_currency="EUR")
    with pytest.raises(AnalyticsValidationError, match="FX"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=None, config=config
        )


def test_portfolio_builder_aggregates_actual_same_currency_pnl() -> None:
    """Same-currency component PnL is summed from actual report evidence."""
    logger.debug("Testing Analytics same-currency portfolio aggregation")
    first, config = _report()
    second, _ = _report(profit=10)
    portfolio = build_portfolio_performance_report(
        (first, second), base_currency="USD", fx_evidence=None, config=config
    )
    net = next(
        metric
        for metric in portfolio.sections[0].metrics
        if metric.metric_key == "net_pnl"
    )
    assert net.value == 18
