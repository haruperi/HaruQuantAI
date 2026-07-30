"""Executable usage evidence for the Indicators Core feature."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from typing import Any

from app.services.data import get_market_data
from app.services.indicators import (
    build_indicator_config,
    get_capability_matrix,
    get_indicator,
    get_indicator_result_metadata,
    get_warmup_requirement,
    join_indicator_result,
    list_indicators,
    sma,
    validate_indicator,
)

from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    unwrap_indicator_response,
    unwrap_market_data_response,
)

MarketDataset = Any
_CACHE: dict[str, MarketDataset] = {}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _config() -> object:
    """Build the canonical demonstration config.

    Returns:
        A two-period SMA configuration.
    """
    return build_indicator_config(
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


def _dataset() -> MarketDataset:
    """Return one cached real read-only market dataset.

    Returns:
        A normalized real market dataset.

    Raises:
        RuntimeError: If the configured read-only source is unavailable.
    """
    if "dataset" not in _CACHE:
        _CACHE["dataset"] = unwrap_market_data_response(
            get_market_data(
                source_id="mt5",
                symbol="EURUSD",
                timeframe="M5",
                limit=20,
            )
        )
    return _CACHE["dataset"]


def _result() -> object:
    """Calculate one real result through the package-root API.

    Returns:
        A two-period SMA result.
    """
    return unwrap_indicator_response(sma(_dataset(), period=2))


def fr_indi_001() -> None:
    """FR-INDI-001: The system shall expose exactly the approved Core MVP codes: `IND_INVALID_CONFIG`, `IND_INVALID_PARAMETER`, `IND_UNSUPPORTED_INDICATOR`, `IND_UNSUPPORTED_TIMEFRAME`, `IND_UNSUPPORTED_DTYPE`, `IND_INVALID_INPUT_SCHEMA`, `IND_MISSING_REQUIRED_COLUMN`, `IND_INVALID_OUTPUT_COLUMN`, `IND_OUTPUT_COLUMN_CONFLICT`, `IND_INVALID_OUTPUT_MODE`, `IND_INPUT_MUTATION_DETECTED`, `IND_DUPLICATE_TIMESTAMP`, `IND_NON_MONOTONIC_TIME`, `IND_AMBIGUOUS_TIMESTAMP`, `IND_INVALID_TIMEZONE`, `IND_INVALID_OHLC`, `IND_INSUFFICIENT_DATA`, `IND_LOOKAHEAD_RISK`, `IND_FORMULA_VERSION_MISMATCH`, `IND_RESOURCE_LIMIT_EXCEEDED`, `IND_PARTIAL_RESULT`, and `IND_INTERNAL_ERROR`."""
    _header(
        "FR-INDI-001: The system shall expose exactly the approved Core MVP codes: `IND_INVALID_CONFIG`, `IND_INVALID_PARAMETER`, `IND_UNSUPPORTED_INDICATOR`, `IND_UNSUPPORTED_TIMEFRAME`, `IND_UNSUPPORTED_DTYPE`, `IND_INVALID_INPUT_SCHEMA`, `IND_MISSING_REQUIRED_COLUMN`, `IND_INVALID_OUTPUT_COLUMN`, `IND_OUTPUT_COLUMN_CONFLICT`, `IND_INVALID_OUTPUT_MODE`, `IND_INPUT_MUTATION_DETECTED`, `IND_DUPLICATE_TIMESTAMP`, `IND_NON_MONOTONIC_TIME`, `IND_AMBIGUOUS_TIMESTAMP`, `IND_INVALID_TIMEZONE`, `IND_INVALID_OHLC`, `IND_INSUFFICIENT_DATA`, `IND_LOOKAHEAD_RISK`, `IND_FORMULA_VERSION_MISMATCH`, `IND_RESOURCE_LIMIT_EXCEEDED`, `IND_PARTIAL_RESULT`, and `IND_INTERNAL_ERROR`."
    )
    failure = get_indicator("macd")
    print([failure.error.code] if failure.error is not None else [])


def fr_indi_002() -> None:
    """FR-INDI-002: The system shall represent a deterministic, redacted failure with code, safe message, and structured details without exposing raw exceptions or sensitive input data."""
    _header(
        "FR-INDI-002: The system shall represent a deterministic, redacted failure with code, safe message, and structured details without exposing raw exceptions or sensitive input data."
    )
    failure = get_indicator("macd")
    print(failure.error.code, failure.message, dict(failure.error.details))


def fr_indi_003() -> None:
    """FR-INDI-003: The system shall represent indicator ID, canonical parameters, source, formula version, output/precision/availability/quality policy, and error mode in one immutable batch config, excluding cache, calendar, backend, actor, tracing, SLO, entitlement, timeout, cancellation, and orchestration context."""
    _header(
        "FR-INDI-003: The system shall represent indicator ID, canonical parameters, source, formula version, output/precision/availability/quality policy, and error mode in one immutable batch config, excluding cache, calendar, backend, actor, tracing, SLO, entitlement, timeout, cancellation, and orchestration context."
    )
    print(_config())


def fr_indi_004() -> None:
    """FR-INDI-004: The system shall describe each official indicator's ID, name, versions, tier, required columns, parameter/output schemas, warmup policy, supported batch capabilities, import path, stability, and workflow eligibility."""
    _header(
        "FR-INDI-004: The system shall describe each official indicator's ID, name, versions, tier, required columns, parameter/output schemas, warmup policy, supported batch capabilities, import path, stability, and workflow eligibility."
    )
    print(unwrap_indicator_response(get_indicator("sma")))


def fr_indi_005() -> None:
    """FR-INDI-005: The system shall expose the exact normalized history requirement for an indicator/config without fetching data, including minimum observations, source timeframe, required columns, and availability basis."""
    _header(
        "FR-INDI-005: The system shall expose the exact normalized history requirement for an indicator/config without fetching data, including minimum observations, source timeframe, required columns, and availability basis."
    )
    print(unwrap_indicator_response(get_warmup_requirement("sma", _config())))


def fr_indi_006() -> None:
    """FR-INDI-006: The system shall expose a minimal structural registered-calculator protocol whose approved calculation accepts one normalized `MarketDataset v1` plus a complete `IndicatorConfig` and returns `IndicatorResult`; public convenience wrappers construct the config and are not required to share this internal signature."""
    _header(
        "FR-INDI-006: The system shall expose a minimal structural registered-calculator protocol whose approved calculation accepts one normalized `MarketDataset v1` plus a complete `IndicatorConfig` and returns `IndicatorResult`; public convenience wrappers construct the config and are not required to share this internal signature."
    )
    print(callable(sma))


def fr_indi_007() -> None:
    """FR-INDI-007: The system shall expose a standalone serializable deterministic manifest containing manifest/indicator/formula/output-schema versions, canonical parameter hash, input/output checksums, output contract and shape, precision, availability policy, Data-provided provenance, and quality summary; volatile runtime/host data is excluded from identity."""
    _header(
        "FR-INDI-007: The system shall expose a standalone serializable deterministic manifest containing manifest/indicator/formula/output-schema versions, canonical parameter hash, input/output checksums, output contract and shape, precision, availability policy, Data-provided provenance, and quality summary; volatile runtime/host data is excluded from identity."
    )
    print(get_indicator_result_metadata(_result())["manifest"])


def fr_indi_008() -> None:
    """FR-INDI-008: The system shall return timestamp/symbol-aligned values, canonical output columns, availability, quality, errors, and manifest as `IndicatorSeries v1`, preserving warmup and unavailable rows and exposing no incremental state or metrics."""
    _header(
        "FR-INDI-008: The system shall return timestamp/symbol-aligned values, canonical output columns, availability, quality, errors, and manifest as `IndicatorSeries v1`, preserving warmup and unavailable rows and exposing no incremental state or metrics."
    )
    result = _result()
    metadata = get_indicator_result_metadata(result)
    print(metadata["schema_id"], metadata["output_columns"])
    print_indicator_evidence(result, label="IndicatorSeries v1 rows")


def fr_indi_009() -> None:
    """FR-INDI-009: The system shall expose a copy-safe projection containing generated indicator, availability, and quality columns without original OHLCV columns."""
    _header(
        "FR-INDI-009: The system shall expose a copy-safe projection containing generated indicator, availability, and quality columns without original OHLCV columns."
    )
    print_indicator_evidence(_result(), label="Copy-safe generated values")


def fr_indi_010() -> None:
    """FR-INDI-010: The system shall privately project one matching `MarketDataset v1`, append generated columns to that copied canonical tabular projection, and preserve source columns, row count/order, timestamp/symbol layout, warmup rows, and input identity; collisions fail."""
    _header(
        "FR-INDI-010: The system shall privately project one matching `MarketDataset v1`, append generated columns to that copied canonical tabular projection, and preserve source columns, row count/order, timestamp/symbol layout, warmup rows, and input identity; collisions fail."
    )
    joined = unwrap_indicator_response(join_indicator_result(_result(), _dataset()))
    print("Joined source and generated columns:")
    print(joined.tail(8).to_string())


def fr_indi_011() -> None:
    """FR-INDI-011: The system shall resolve one of the 21 official indicator IDs in the registry identity below to its immutable spec and reject every unknown ID before calculation."""
    _header(
        "FR-INDI-011: The system shall resolve one of the 21 official indicator IDs in the registry identity below to its immutable spec and reject every unknown ID before calculation."
    )
    print(unwrap_indicator_response(get_indicator("rsi")).indicator_id)


def fr_indi_012() -> None:
    """FR-INDI-012: The system shall list official specs in stable indicator-ID order with no mutable registry handle."""
    _header(
        "FR-INDI-012: The system shall list official specs in stable indicator-ID order with no mutable registry handle."
    )
    print([spec.indicator_id for spec in unwrap_indicator_response(list_indicators())])


def fr_indi_013() -> None:
    """FR-INDI-013: The system shall expose a JSON/YAML-compatible matrix containing ID, versions, tier, batch/vectorized/multi-symbol/multi-timeframe support, unsupported optional modes, dependencies, deterministic unsupported codes, and official-workflow eligibility."""
    _header(
        "FR-INDI-013: The system shall expose a JSON/YAML-compatible matrix containing ID, versions, tier, batch/vectorized/multi-symbol/multi-timeframe support, unsupported optional modes, dependencies, deterministic unsupported codes, and official-workflow eligibility."
    )
    matrix = unwrap_indicator_response(get_capability_matrix())
    print("Capability rows:", len(matrix))
    print("First capability record:", dict(matrix[0]))


def fr_indi_014() -> None:
    """FR-INDI-014: The system shall resolve the spec and atomically validate config, parameters, row limits, `MarketDataset v1` identity, bars-only kind, one symbol/timeframe, required OHLC fields, ordered unique UTC record timestamps, finite OHLC consistency, output names/collisions, quality evidence, and formula version before private projection/calculation; an empty dataset fails, while a non-empty short dataset remains valid warmup input. Upstream source-quality policy remains Data-owned."""
    _header(
        "FR-INDI-014: The system shall resolve the spec and atomically validate config, parameters, row limits, `MarketDataset v1` identity, bars-only kind, one symbol/timeframe, required OHLC fields, ordered unique UTC record timestamps, finite OHLC consistency, output names/collisions, quality evidence, and formula version before private projection/calculation; an empty dataset fails, while a non-empty short dataset remains valid warmup input. Upstream source-quality policy remains Data-owned."
    )
    print(
        unwrap_indicator_response(
            validate_indicator("sma", _dataset(), _config())
        ).indicator_id
    )


def main() -> None:
    """Run every Core functional-requirement demonstration.

    Returns:
        None.
    """
    for demonstration in (
        fr_indi_001,
        fr_indi_002,
        fr_indi_003,
        fr_indi_004,
        fr_indi_005,
        fr_indi_006,
    ):
        demonstration()
    try:
        _dataset()
    except RuntimeError as unavailable:
        print(f"Skipping live examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None
    print_market_evidence(_dataset())
    for demonstration in (
        fr_indi_007,
        fr_indi_008,
        fr_indi_009,
        fr_indi_010,
        fr_indi_011,
        fr_indi_012,
        fr_indi_013,
        fr_indi_014,
    ):
        demonstration()


if __name__ == "__main__":
    main()
