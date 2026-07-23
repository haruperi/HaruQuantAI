"""Executable indicators core feature examples."""

import sys
from pathlib import Path
from typing import cast

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data
from app.services.data.contracts import DataError, MarketDataset
from app.services.indicators import sma
from app.services.indicators.core import (
    IndicatorConfig,
    IndicatorError,
    IndicatorErrorCode,
    IndicatorProtocol,
    IndicatorResult,
    WarmupRequirement,
    get_capability_matrix,
    get_indicator,
    list_indicators,
    validate_indicator,
)


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


def _demo_config() -> IndicatorConfig:
    """Build one demonstration ``IndicatorConfig`` for a two-period SMA.

    Returns:
        One demo indicator configuration.
    """
    return IndicatorConfig(
        indicator_id="sma",
        parameters=(("period", 2),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )


_CACHE: dict[str, MarketDataset] = {}


def _get_dataset() -> MarketDataset:
    """Retrieve real market dataset.

    Returns:
        A MarketDataset instance.
    """
    if "dataset" in _CACHE:
        return _CACHE["dataset"]
    dataset = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=20,
    )
    print("Using real MT5 EURUSD market data.")
    _CACHE["dataset"] = dataset
    return dataset


def _demo_result() -> IndicatorResult:
    """Compute one demonstration ``IndicatorResult`` via the public SMA API.

    Uses the real public ``sma`` convenience function against real market
    data, so the manifest, values-only projection, and join examples below
    demonstrate genuine end-to-end usage rather than a hand-assembled result.

    Returns:
        One real two-period SMA indicator result.
    """
    return sma(_get_dataset(), period=2)


class _DemoCalculator:
    """Minimal stand-in satisfying ``IndicatorProtocol`` structurally."""

    def calculate(
        self, _data: MarketDataset, _config: IndicatorConfig
    ) -> IndicatorResult:
        """Return a placeholder demonstration result.

        Args:
            _data: Dataset placeholder.
            _config: Config placeholder.

        Returns:
            A placeholder object.
        """
        return cast("IndicatorResult", object())


def example_contracts() -> None:
    """Demonstrate the Core error, config, spec, warmup, and protocol contracts.

    Covers ``FR-INDI-001`` through ``FR-INDI-006``. These examples need no
    market data, so they run before the live-data availability check.
    """
    _header("Example 1: List all approved Core MVP error codes")
    print("Indicators Core error codes:")
    for code in IndicatorErrorCode:
        print(f"  {code.value}")

    _header("Example 2: Construct and inspect a redacted IndicatorError")
    error = IndicatorError(
        IndicatorErrorCode.IND_UNSUPPORTED_INDICATOR,
        "requested indicator is not in the official registry",
        {"indicator_id": "macd"},
    )
    print(f"Code: {error.code.value}")
    print(f"Message: {error.message}")
    print(f"Details: {dict(error.details)}")

    _header("Example 3: Build an immutable batch calculation configuration")
    config = _demo_config()
    print(f"Indicator ID: {config.indicator_id}")
    print(f"Parameters: {config.parameters}")
    print(f"Output Mode: {config.output_mode}")

    _header("Example 4: Inspect one official indicator's public metadata")
    spec = get_indicator("sma")
    print(f"IndicatorSpec: {spec.indicator_id} v{spec.indicator_version}")
    print(f"Tier: {spec.tier}")

    _header("Example 5: Describe the exact history requirement without fetching data")
    requirement = WarmupRequirement(
        indicator_id="sma",
        formula_version="1.0.0",
        minimum_observations=14,
        source_timeframe=None,
        required_columns=("source",),
        availability_basis="source_available_at",
    )
    print(f"Warmup minimum observations: {requirement.minimum_observations}")

    _header("Example 6: Satisfy the calculator protocol structurally")
    calculator = _DemoCalculator()
    is_instance = isinstance(calculator, IndicatorProtocol)
    print(f"Is IndicatorProtocol structural instance: {is_instance}")


def example_results_and_registry() -> None:
    """Demonstrate manifests, results, projections, joins, and registry reads.

    Covers ``FR-INDI-007`` through ``FR-INDI-014`` against real market data.
    """
    _header("Example 7: Inspect the deterministic identity/checksum manifest")
    result = _demo_result()
    manifest = result.manifest
    print(f"Manifest Indicator ID: {manifest.indicator_id}")
    print(f"Manifest Parameter Hash: {manifest.parameter_hash[:8]}...")
    print(f"Checksum length: {len(manifest.output_checksum)}")

    _header("Example 8: Inspect the full IndicatorSeries v1 result shape")
    result = _demo_result()
    print(f"Schema ID: {result.schema_id}")
    print(f"Output columns: {list(result.values.columns)}")

    _header("Example 9: Project only generated/availability/quality columns")
    result = _demo_result()
    projection = result.values_only
    print(f"Values-only columns: {list(projection.columns)}")

    _header("Example 10: Join generated columns onto a copied source projection")
    data = _get_dataset()
    result = _demo_result()
    joined = result.join_to(data)
    print(f"Joined columns: {list(joined.columns)}")

    _header("Example 11: Resolve one official indicator ID to its immutable spec")
    spec = get_indicator("rsi")
    print(f"Resolved indicator: {spec.name} ({spec.indicator_id})")

    _header("Example 12: List all official specs in stable ID order")
    specs = list_indicators()
    print(f"Official indicators: {[spec.indicator_id for spec in specs]}")

    _header("Example 13: Build the JSON-compatible official capability matrix")
    matrix = get_capability_matrix()
    print(f"Capability matrix size: {len(matrix)}")

    _header("Example 14: Validate indicator config before doing formula work")
    validated_spec = validate_indicator("sma", _get_dataset(), _demo_config())
    print(f"Validated indicator spec: {validated_spec.indicator_id}")


def main() -> None:
    """Run the Indicators Core feature usage examples.

    Demonstrates ``FR-INDI-001`` through ``FR-INDI-014`` end-to-end against
    real market data using only documented public exports. Exits with status
    ``3`` when the live market-data source is unavailable, which the
    integration runner treats as a skip rather than a failure.
    """
    example_contracts()
    try:
        _get_dataset()
    except DataError as unavailable:
        print(f"Skipping remaining examples: MT5 data unavailable ({unavailable.code})")
        sys.exit(3)
    example_results_and_registry()


if __name__ == "__main__":
    main()
