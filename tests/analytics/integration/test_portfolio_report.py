"""Integration evidence for Analytics portfolio composition."""

# ruff: noqa: INP001

import pytest
from app.services.analytics.contracts import AnalyticsValidationError
from app.services.analytics.reports.portfolio import build_portfolio_performance_report
from app.utils import logger
from tests.analytics._support import _report


def test_portfolio_report_fails_closed_without_fx() -> None:
    """The portfolio workflow returns no mixed-currency aggregate without FX."""
    logger.debug("Testing Analytics portfolio FX workflow")
    usd, config = _report(account_currency="USD")
    eur, _ = _report(account_currency="EUR")
    with pytest.raises(AnalyticsValidationError, match="FX"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=None, config=config
        )
