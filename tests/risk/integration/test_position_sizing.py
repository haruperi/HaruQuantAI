"""WF-RISK-002 integration test for snapshot-backed position sizing."""

from tests.risk._support import run_position_size_test


def test_position_sizing_uses_current_portfolio_snapshot() -> None:
    """Run the complete snapshot-to-sizing workflow without approval."""
    run_position_size_test()
