"""Workflow integration for producer-neutral Analytics adaptation."""

# ruff: noqa: INP001

from tests.analytics.usage.test_usage_adapters import (
    test_usage_results_adapt_trading_result,
    test_usage_results_build_equity_curve,
)


def test_approved_sources_map_without_field_loss() -> None:
    """The canonical adapter workflow produces both result and curve evidence."""
    from app.utils import logger

    logger.debug("Running Analytics adapter workflow integration")
    test_usage_results_build_equity_curve()
    test_usage_results_adapt_trading_result()
