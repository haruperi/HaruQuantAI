"""Executable Portfolio rebalancing usage example.

Demonstrates constructing reduce-only exposure rebalance actions.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio.contracts import PortfolioRebalanceAction


def example_rebalancing() -> None:
    """Demonstrate portfolio reduce-only rebalance action."""
    print("=" * 80)
    print("Portfolio Example 3: Rebalance Action")
    print("=" * 80)

    action = PortfolioRebalanceAction(
        action_id="action-1",
        component_id="component-a",
        action="reduce_exposure",
        reduce_only=True,
        current_exposure=Decimal("0.6"),
        target_exposure=Decimal("0.5"),
        reduction_amount=Decimal("0.1"),
        eligibility_decision_id="eligibility-a",
    )

    print(f"Action ID: {action.action_id}")
    print(f"Component: {action.component_id}")
    print(f"Action: {action.action}, Reduce only: {action.reduce_only}")
    print(
        f"Current exposure: {action.current_exposure} -> Target: {action.target_exposure}"
    )


def main() -> None:
    """Run Portfolio rebalancing usage example."""
    example_rebalancing()


if __name__ == "__main__":
    main()
