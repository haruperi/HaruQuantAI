"""Executable Research metrics usage example.

Demonstrates the metric calculator protocol, registry membership and
resolution, the default seven-family registry, and core metric profile
assembly.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research import (
    build_core_metric_profile,
    build_default_registry,
    create_research_metric_registry,
    create_research_value,
)


@dataclass(frozen=True)
class _ExampleCalculator:
    """Usage calculator satisfying the public metric protocol."""

    family: str

    def compute(self, context: object) -> tuple[object, ...]:
        """Compute one example metric.

        Args:
            context: Detached metric inputs.

        Returns:
            One normalized metric value.
        """
        return (
            create_research_value(
                "MetricValue", self.family, 1.0, "ratio", len(context.data)
            ),
        )


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _prepared() -> object:
    """Build a small two-row prepared Research dataset.

    The frame includes the OHLCV columns plus the spread column required by
    the retained metric calculators.

    Returns:
        A detached prepared dataset with SHA-256 hash evidence.
    """
    frame = pd.DataFrame(
        {
            "open": [100.0, 101.0],
            "high": [101.0, 102.0],
            "low": [99.0, 100.0],
            "close": [100.5, 101.5],
            "volume": [1000.0, 1200.0],
            "spread": [0.1, 0.2],
        }
    )
    quality = create_research_value(
        "DataQualityReport",
        fatal_issues=(),
        warnings=(),
        checks=("schema",),
        cleaning_actions=(),
    )
    return create_research_value(
        "PreparedDataset",
        data=frame,
        schema_version="v1",
        quality=quality,
        dataset_hash="e" * 64,
        configuration_hash="e" * 64,
        source_references=("research-ohlcv",),
    )


def fr_res_042() -> None:
    """FR-RES-042.

    Define the read-only contract implemented by one named metric-family
    calculator.
    """
    _header(
        "FR-RES-042. Define the read-only contract implemented by one named metric-family calculator."
    )
    calc = _ExampleCalculator("returns")
    print(f"FR-RES-042 family={calc.family}")


def fr_res_043() -> None:
    """FR-RES-043.

    Compute normalized values for one family from an immutable metric context.
    """
    _header(
        "FR-RES-043. Compute normalized values for one family from an immutable metric context."
    )
    calc = _ExampleCalculator("returns")
    value = calc.compute(
        create_research_value("MetricContext", pd.DataFrame({"value": [1.0]}))
    )[0]
    print(f"FR-RES-043 name={value.name} unit={value.unit}")


def fr_res_044() -> None:
    """FR-RES-044.

    Own unique bounded calculator membership without global mutable defaults.
    """
    _header(
        "FR-RES-044. Own unique bounded calculator membership without global mutable defaults."
    )
    registry = create_research_metric_registry((_ExampleCalculator("returns"),))
    print(f"FR-RES-044 calculators={len(registry.all())}")


def fr_res_045() -> None:
    """FR-RES-045.

    Construct an isolated registry from a bounded calculator iterable.
    """
    _header(
        "FR-RES-045. Construct an isolated registry from a bounded calculator iterable."
    )
    registry = create_research_metric_registry((_ExampleCalculator("returns"),))
    print(f"FR-RES-045 calculators={len(registry.all())}")


def fr_res_046() -> None:
    """FR-RES-046.

    Resolve a calculator by exact family name.
    """
    _header("FR-RES-046. Resolve a calculator by exact family name.")
    registry = create_research_metric_registry((_ExampleCalculator("returns"),))
    resolved = registry.resolve("returns")
    print(f"FR-RES-046 resolved_family={resolved.family}")


def fr_res_047() -> None:
    """FR-RES-047.

    Return calculators in deterministic registration order without exposing
    mutable storage.
    """
    _header(
        "FR-RES-047. Return calculators in deterministic registration order without exposing mutable storage."
    )
    registry = create_research_metric_registry(
        (_ExampleCalculator("returns"), _ExampleCalculator("activity"))
    )
    calculators = registry.all()
    families = [calc.family for calc in calculators]
    print(f"FR-RES-047 count={len(calculators)} families={families}")


def fr_res_048() -> None:
    """FR-RES-048.

    Build a new default registry containing the seven retained metric families.
    """
    _header(
        "FR-RES-048. Build a new default registry containing the seven retained metric families."
    )
    registry = build_default_registry()
    families = [calc.family for calc in registry.all()]
    print(f"FR-RES-048 count={len(families)} families={families}")


def fr_res_049() -> None:
    """FR-RES-049.

    Build a deterministic profile with units, samples, undefined reasons,
    hashes, warnings, and duration from a prepared dataset.
    """
    _header(
        "FR-RES-049. Build a deterministic profile with units, samples, undefined reasons, hashes, warnings, and duration from a prepared dataset."
    )
    profile = build_core_metric_profile(
        _prepared(),
        limits=create_research_value("ResearchResourceLimits", 10, 10.0, 1024),
    )
    print(f"FR-RES-049 metric_count={len(profile.metrics)}")


def main() -> None:
    """Run every Research metrics requirement demonstration in order."""
    print("Research Example 5: Metric Registry and Profile")
    fr_res_042()
    fr_res_043()
    fr_res_044()
    fr_res_045()
    fr_res_046()
    fr_res_047()
    fr_res_048()
    fr_res_049()


if __name__ == "__main__":
    main()
