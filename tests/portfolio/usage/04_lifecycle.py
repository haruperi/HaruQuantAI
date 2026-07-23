"""Executable Portfolio lifecycle usage example.

Demonstrates PortfolioService import from package root and service instantiation.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio import PortfolioService as PublicPortfolioService
from app.services.portfolio.api import PortfolioService


def example_lifecycle() -> None:
    """Demonstrate portfolio service export and lifecycle availability."""
    print("=" * 80)
    print("Portfolio Example 4: Package-Root Service Lifecycle Export")
    print("=" * 80)

    is_identical = PublicPortfolioService is PortfolioService
    print(f"Public PortfolioService matches internal PortfolioService: {is_identical}")


def main() -> None:
    """Run Portfolio lifecycle usage example."""
    example_lifecycle()


if __name__ == "__main__":
    main()
