"""WF-RISK-002 integration test for snapshot-backed position sizing."""

from tests.risk.usage.test_usage_sizing import test_usage_calculator_position_size


def test_position_sizing_uses_current_portfolio_snapshot() -> None:
    """Run the complete snapshot-to-sizing workflow without approval."""
    test_usage_calculator_position_size()
