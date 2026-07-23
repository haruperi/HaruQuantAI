"""Executable Research metrics usage example.

Demonstrates metric registry creation, resolution, calculator computation, and metric profile building.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research.metrics import (
    MetricRegistry,
    build_default_registry,
)
from app.services.research.metrics.registry import MetricContext, MetricValue


@dataclass(frozen=True)
class _ExampleCalculator:
    """Usage calculator satisfying the public metric protocol."""

    family: str

    def compute(self, context: MetricContext) -> tuple[MetricValue, ...]:
        """Compute one example metric."""
        return (MetricValue(self.family, 1.0, "ratio", len(context.data)),)


def example_metrics() -> None:
    """Demonstrate research metric registry and calculations."""
    print("=" * 80)
    print("Research Example 5: Metric Registry and Computation")
    print("=" * 80)

    calc = _ExampleCalculator("returns")
    ctx = MetricContext(pd.DataFrame({"value": [1.0]}))

    # 1. Compute metric value
    val = calc.compute(ctx)[0]
    print(f"Computed metric name: {val.name}, value: {val.value}, unit: {val.unit}")

    # 2. Custom metric registry
    custom_reg = MetricRegistry.from_calculators((calc,))
    print(f"Custom registry calculators count: {len(custom_reg.all())}")

    # 3. Default seven-family registry
    default_reg = build_default_registry()
    families = [c.family for c in default_reg.all()]
    print(f"Default registry contains {len(families)} metric families: {families}")


def main() -> None:
    """Run Research metrics usage example."""
    example_metrics()


if __name__ == "__main__":
    main()
