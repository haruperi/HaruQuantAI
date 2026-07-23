"""Executable Portfolio construction usage example.

Demonstrates calculating equal weights for portfolio components.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio.construction.methods import equal_weights


def example_construction() -> None:
    """Demonstrate equal weights portfolio construction."""
    print("=" * 80)
    print("Portfolio Example 2: Equal Weights Construction")
    print("=" * 80)

    components = ("component-a", "component-b")
    weights = equal_weights(
        components,
        minimum=Decimal(0),
        maximum=Decimal(1),
    )

    print(f"Calculated equal weights for {len(components)} components:")
    for comp_id, target, current in weights:
        print(f"  Component: {comp_id}, target: {target}, current: {current}")


def main() -> None:
    """Run Portfolio construction usage example."""
    example_construction()


if __name__ == "__main__":
    main()
