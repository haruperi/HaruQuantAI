"""Executable usage evidence for the Indicators Core feature."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

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


def _feature_header(title: str) -> None:
    """Print the feature banner and module flow."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one section heading."""
    print(f"\n{'-' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


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
    """FR-INDI-001: Stage 1 — Expose the exact approved Core MVP error-code contract."""
    _header(
        "Stage 1: Core Error Catalog - Enumerate Approved Error Contract (FR-INDI-001)"
    )
    failure = get_indicator("macd")
    print(_format_result(failure))
    codes = failure.error.code if failure.error else "unknown"
    print(f"Data -> failure_code={codes}")


def fr_indi_002() -> None:
    """FR-INDI-002: Stage 1 — Preserve deterministic redacted failure data."""
    _header(
        "Stage 1: Core Error Surface - Deterministic, Redacted Failure (FR-INDI-002)"
    )
    failure = get_indicator("macd")
    print(_format_result(failure))
    print(
        f"Data -> message={failure.message}, "
        f"error_code={failure.error.code if failure.error else 'unknown'}"
    )


def fr_indi_003() -> None:
    """FR-INDI-003: Stage 2 — Represent immutable batch calculation config."""
    _header("Stage 2: Immutable Config - Canonical Wrapper State (FR-INDI-003)")
    config = _config()
    print(_format_result(config))
    print(
        "Data -> ",
        f"indicator_id={config.indicator_id}, period={config.parameters[0][1]}, source={config.source}, version={config.formula_version}",
    )


def fr_indi_004() -> None:
    """FR-INDI-004: Stage 2 — Resolve and describe indicator specifications."""
    _header("Stage 2: Registry Discovery - Official Spec Representation (FR-INDI-004)")
    spec = unwrap_indicator_response(get_indicator("sma"))
    print(_format_result(spec))
    print(
        f"Data -> indicator_id={spec.indicator_id}, formula_version={spec.formula_version}"
    )


def fr_indi_005() -> None:
    """FR-INDI-005: Stage 2 — Resolve exact warmup requirement without fetching data."""
    _header("Stage 2: Warmup Resolution - Exact Requirement Contract (FR-INDI-005)")
    requirement = unwrap_indicator_response(get_warmup_requirement("sma", _config()))
    print(_format_result(requirement))
    print(
        "Data -> ",
        f"minimum_observations={requirement.minimum_observations}, "
        f"source_timeframe={requirement.source_timeframe}, "
        f"availability_basis={requirement.availability_basis}",
    )


def fr_indi_006() -> None:
    """FR-INDI-006: Stage 2 — Surface calculator protocol and callable compatibility."""
    _header(
        "Stage 2: Protocol Contract - Deterministic Calculation Signature (FR-INDI-006)"
    )
    main_data = callable(sma)
    print(_format_result(main_data))
    print(f"Data -> sma_is_callable={main_data}")


def fr_indi_007() -> None:
    """FR-INDI-007: Stage 3 — Emit deterministic manifest and identity material."""
    _header(
        "Stage 3: Manifest Integrity - Deterministic Identity Material (FR-INDI-007)"
    )
    manifest = get_indicator_result_metadata(_result())["manifest"]
    print(_format_result(manifest))
    print(
        f"Data -> checksum={manifest['output_checksum']}, rows={manifest['row_count']}"
    )


def fr_indi_008() -> None:
    """FR-INDI-008: Stage 3 — Return fully aligned indicator series."""
    _header("Stage 3: Aligned Result - IndicatorSeries with Evidence (FR-INDI-008)")
    result = _result()
    metadata = get_indicator_result_metadata(result)
    print(_format_result(result))
    print(
        f"Data -> schema={metadata['schema_id']}, columns={metadata['output_columns']}"
    )
    print_indicator_evidence(result, label="IndicatorSeries v1 rows")


def fr_indi_009() -> None:
    """FR-INDI-009: Stage 3 — Project copy-safe indicator output columns."""
    _header(
        "Stage 3: Projection Semantics - Generated Output-Only Columns (FR-INDI-009)"
    )
    result = _result()
    print(_format_result(result))
    print(
        f"Data -> projection_columns={list(get_indicator_result_metadata(result)['output_columns'])}"
    )
    print_indicator_evidence(result, label="Copy-safe generated values")


def fr_indi_010() -> None:
    """FR-INDI-010: Stage 3 — Join generated columns without mutating source data."""
    _header("Stage 3: Join Safety - Copy-Safe Source Enrichment (FR-INDI-010)")
    joined = unwrap_indicator_response(join_indicator_result(_result(), _dataset()))
    print(_format_result(joined))
    print(f"Data -> joined_shape={joined.shape}, columns={list(joined.columns)}")
    print("Joined source and generated columns:")
    print(joined.tail(8).to_string())


def fr_indi_011() -> None:
    """FR-INDI-011: Stage 3 — Resolve official indicator identity."""
    _header("Stage 3: Registry Resolution - Known ID Success Path (FR-INDI-011)")
    indicator = unwrap_indicator_response(get_indicator("rsi"))
    print(_format_result(indicator))
    print(f"Data -> resolved_indicator_id={indicator.indicator_id}")


def fr_indi_012() -> None:
    """FR-INDI-012: Stage 3 — List official indicators in deterministic order."""
    _header("Stage 3: Ordered Registry Snapshot - Stable ID Sequence (FR-INDI-012)")
    specs = unwrap_indicator_response(list_indicators())
    print(_format_result(specs))
    print(
        f"Data -> official_spec_count={len(specs)}, first_three={tuple(s.indicator_id for s in specs[:3])}"
    )


def fr_indi_013() -> None:
    """FR-INDI-013: Stage 3 — Emit capability matrix records for interoperability."""
    _header(
        "Stage 3: Capability Matrix - Contract and Eligibility Evidence (FR-INDI-013)"
    )
    matrix = unwrap_indicator_response(get_capability_matrix())
    print(_format_result(matrix))
    print(f"Data -> capability_rows={len(matrix)}")
    print(f"Data -> first_row={dict(matrix[0]) if matrix else {}}")


def fr_indi_014() -> None:
    """FR-INDI-014: Stage 2 — Validate indicator request atomically before calculation."""
    _header(
        "Stage 2: Atomic Validation - Deterministic Guardrail Enforcement (FR-INDI-014)"
    )
    validated = unwrap_indicator_response(
        validate_indicator("sma", _dataset(), _config())
    )
    print(_format_result(validated))
    print(
        f"Data -> validated_indicator_id={validated.indicator_id}, formula={validated.formula_version}"
    )


def main() -> None:
    """Run all feature requirements in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-INDI-01 — core/ — Indicator Contracts, Registry Discovery and Request Validation\n\n"
        "Purpose: Define the complete pure calculation boundary shared by every official built-in.\n\n"
        "Module flow:\n"
        "-> indicator id + normalized data + config\n"
        "-> registry.py\n"
        "-> validation.py\n"
        "-> feature calculation\n"
        "-> results.py\n"
        "-> IndicatorResult"
    )

    # Stage 1: authoritative error and catalog surface discovery.
    fr_indi_001()
    fr_indi_002()

    # Stage 2: config, registry, and strict input validation contracts.
    fr_indi_003()
    fr_indi_004()
    fr_indi_005()
    fr_indi_006()
    try:
        _dataset()
    except RuntimeError as unavailable:
        print(f"Skipping live examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None
    print_market_evidence(_dataset())
    fr_indi_014()

    # Stage 3: canonical result contracts and deterministic outputs.
    fr_indi_007()
    fr_indi_008()
    fr_indi_009()
    fr_indi_011()
    fr_indi_012()
    fr_indi_013()
    fr_indi_010()


if __name__ == "__main__":
    main()
