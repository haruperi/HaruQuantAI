"""Unit tests for Analytics cost and efficiency evidence."""

# ruff: noqa: INP001

from decimal import Decimal

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.metrics.cost_efficiency import (
    calculate_cost_efficiency_evidence,
)
from app.utils import logger
from tests.analytics.unit.test_results_adapter import _config, _source


def test_cost_evidence_preserves_rebates_and_signs() -> None:
    """Signed commission and swap remain exact in cost-drag evidence."""
    logger.debug("Testing Analytics signed cost evidence")
    source = _source()
    row = dict(source["closed_trades"][0])
    row.update({"commission": Decimal(2), "swap": Decimal(-1)})
    source["closed_trades"] = (row,)
    result = adapt_trading_result(
        source,
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    section = calculate_cost_efficiency_evidence(result)
    metrics = {item.metric_key: item.value for item in section.metrics}
    assert metrics["total_commission"] == Decimal(2)
    assert metrics["total_swap"] == Decimal(-1)
    assert metrics["total_cost_drag"] == Decimal(1)
    assert metrics["gross_pnl_before_costs"] == Decimal(10)
