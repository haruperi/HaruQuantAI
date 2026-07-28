"""Integration evidence for Analytics portfolio composition."""

# ruff: noqa: INP001
from app.services.analytics import (
    build_portfolio_performance_report,
)
from app.utils import logger
from tests.analytics._support import _report


def test_portfolio_report_fails_closed_without_fx() -> None:
    """The portfolio workflow returns no mixed-currency aggregate without FX."""
    logger.debug("Testing Analytics portfolio FX workflow")
    usd, config = _report(account_currency="USD")
    eur, _ = _report(account_currency="EUR")
    response = build_portfolio_performance_report(
        (usd, eur), base_currency="USD", fx_evidence=None, config=config
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "ANALYTICS_VALIDATION_FAILED"
