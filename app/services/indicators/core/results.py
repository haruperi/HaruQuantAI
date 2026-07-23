"""Deterministic ``IndicatorSeries v1`` manifest and result behavior.

Builds and exposes the immutable ``IndicatorResult``/``IndicatorManifest``
pair returned by every official calculation, without mutating the supplied
``MarketDataset``. This module also hosts the internal (non-public) result
assembly helper shared by the trend, volatility, and momentum feature
modules so identity/checksum/finalization logic is defined exactly once.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal, cast

import pandas as pd

from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.utils import canonical_json, logger

# ``app.utils.canonical_json`` rejects any traversal exceeding 10,000 cumulative
# items. One OHLCV record contributes roughly fifteen, so this chunk size keeps
# each call near 3,750 items — a wide margin that survives future record fields
# while still amortizing call overhead across long histories.
_CHECKSUM_CHUNK_RECORDS: Final[int] = 250

if TYPE_CHECKING:
    from app.services.data.contracts import (
        MarketDataset,
        OHLCVRecord,
    )
    from app.services.indicators.core.contracts import IndicatorConfig


@dataclass(frozen=True, slots=True)
class IndicatorManifest:
    """Deterministic, serializable identity and evidence manifest.

    Attributes:
        manifest_version: Manifest contract version; always ``"v1"``.
        contract_version: Indicator contract version; always ``"v1"``.
        indicator_id: Stable lowercase official registry identifier.
        indicator_version: Public implementation version.
        formula_version: Version of the approved mathematical convention.
        output_schema_version: ``IndicatorSeries`` values-schema version;
            always ``"v1"``.
        parameter_hash: Lowercase 64-character SHA-256 digest of the
            canonical parameter material.
        input_checksum: Lowercase 64-character SHA-256 digest of the input
            ``MarketDataset``.
        output_checksum: Lowercase 64-character SHA-256 digest of the
            produced output values.
        output_columns: Deterministic output columns in canonical order.
        row_count: Non-negative number of result rows.
        symbol: Non-empty dataset symbol.
        source_timeframe: Non-empty source timeframe.
        precision_dtype: Numerical output dtype; always ``"float64"``.
        availability_policy: Availability basis; always
            ``"source_available_at"``.
        normalization_version: Data-owned normalization version.
        source_metadata: Immutable Data-owned source provenance.
        license_metadata: Immutable Data-owned license provenance.
        quality_status: Data-owned dataset quality status, excluding
            ``"failed"``.
        quality_score: Canonical finite decimal quality score string.
        quality_schema_version: Data-owned quality schema version.
    """

    indicator_id: str
    indicator_version: str
    formula_version: str
    parameter_hash: str
    input_checksum: str
    output_checksum: str
    output_columns: tuple[str, ...]
    row_count: int
    symbol: str
    source_timeframe: str
    normalization_version: str
    source_metadata: Mapping[str, str]
    license_metadata: Mapping[str, str]
    quality_status: Literal["passed", "passed_with_warnings", "not_checked"]
    quality_score: str
    quality_schema_version: str
    manifest_version: Literal["v1"] = "v1"
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["indicators.indicator_manifest.v1"] = (
        "indicators.indicator_manifest.v1"
    )
    output_schema_version: Literal["v1"] = "v1"
    precision_dtype: Literal["float64"] = "float64"
    availability_policy: Literal["source_available_at"] = "source_available_at"


@dataclass(frozen=True, slots=True)
class IndicatorResult:
    """Frozen, deterministic ``IndicatorSeries v1`` result container.

    Attributes:
        indicator_id: Stable lowercase official registry identifier.
        indicator_version: Public implementation version.
        formula_version: Version of the approved mathematical convention.
        parameter_hash: Lowercase 64-character SHA-256 parameter digest.
        values: Indicator-owned tabular result following the exact
            values-column contract; construction deep-copies this frame.
        output_columns: Deterministic output columns in canonical order.
        manifest: Deterministic identity, checksum, and evidence manifest.
        contract_version: Series contract version; always ``"v1"``.
        schema_id: Stable namespaced schema identity.
        errors: Unused in v1; public failures raise deterministic
            exceptions instead of a partial result.
    """

    indicator_id: str
    indicator_version: str
    formula_version: str
    parameter_hash: str
    values: pd.DataFrame
    output_columns: tuple[str, ...]
    manifest: IndicatorManifest
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["indicators.indicator_series.v1"] = (
        "indicators.indicator_series.v1"
    )
    errors: tuple[IndicatorError, ...] = ()

    def __post_init__(self) -> None:
        """Defensively deep-copy the stored values frame.

        Raises:
            IndicatorError: Never raised; present for interface symmetry
                with other public Core operations.
        """
        logger.debug("Deep-copying IndicatorResult values on construction")
        object.__setattr__(self, "values", self.values.copy(deep=True))

    @property
    def values_only(self) -> pd.DataFrame:
        """Return a copy-safe projection excluding original OHLCV columns.

        Returns:
            A deep copy of the generated indicator, availability, and
            quality columns. The stored ``values`` frame never carries
            original OHLCV columns, so this is a defensive full copy.
        """
        logger.debug("Building values_only projection for %s", self.indicator_id)
        return self.values.copy(deep=True)

    def join_to(
        self, data: MarketDataset, mode: Literal["copy"] = "copy"
    ) -> pd.DataFrame:
        """Join generated columns onto a copied projection of one dataset.

        Args:
            data: The exact ``MarketDataset v1`` whose canonical checksum
                matches this result's manifest.
            mode: Join mode; only ``"copy"`` is supported.

        Returns:
            A new deep copy preserving source columns, row order, and
            warmup rows, with generated columns appended.

        Raises:
            IndicatorError: If the mode is unsupported, the dataset does
                not match this result's input checksum, or an output
                collision is detected.
        """
        logger.info("Joining IndicatorResult %s to source dataset", self.indicator_id)
        if mode != "copy":
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_OUTPUT_MODE,
                "join_to supports only the copy mode",
                {"mode": str(mode)},
            )
        if _input_checksum(data) != self.manifest.input_checksum:
            raise IndicatorError(
                IndicatorErrorCode.IND_INPUT_MUTATION_DETECTED,
                "dataset does not match the result's input checksum",
                {"indicator_id": self.indicator_id},
            )
        source_frame = _project_source_frame(data)
        generated = self.values.drop(columns=["symbol"])
        colliding = tuple(
            column for column in generated.columns if column in source_frame.columns
        )
        if colliding:
            raise IndicatorError(
                IndicatorErrorCode.IND_OUTPUT_COLUMN_CONFLICT,
                "generated columns collide with source columns",
                {"columns": colliding},
            )
        joined = source_frame.join(generated, how="left")
        return joined.copy(deep=True)


def _parameter_hash(config: IndicatorConfig) -> str:
    """Compute the canonical SHA-256 parameter-hash digest.

    Args:
        config: The complete, validated calculation configuration.

    Returns:
        Lowercase 64-character SHA-256 hexadecimal digest.
    """
    logger.debug("Computing canonical parameter hash for %s", config.indicator_id)
    material = {
        "indicator_id": config.indicator_id,
        "formula_version": config.formula_version,
        "parameters": dict(config.parameters),
        "source": config.source,
    }
    encoded = canonical_json(material).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _input_checksum(data: MarketDataset) -> str:
    """Compute the canonical SHA-256 input-dataset digest.

    The digest folds one ``canonical_json`` call for the dataset-level fields
    and one per fixed-size record chunk, in exact record order, rather than
    canonicalizing the whole dataset in a single call.
    ``app.utils.canonical_json`` enforces a cumulative 10,000-item traversal
    bound, so a single-call implementation failed for any dataset beyond 664
    records. Chunking keeps every call bounded well under that limit
    regardless of history length, while keeping the digest deterministic and
    order-sensitive.

    Args:
        data: One normalized ``MarketDataset v1``.

    Returns:
        Lowercase 64-character SHA-256 hexadecimal digest.
    """
    logger.debug("Computing canonical input checksum for %s", data.symbol)
    payload = data.model_dump(mode="json")
    records = payload.pop("records")
    digest = hashlib.sha256()
    digest.update(canonical_json(payload).encode("utf-8"))
    for start in range(0, len(records), _CHECKSUM_CHUNK_RECORDS):
        # ASCII record separator cannot appear unescaped inside JSON text, so
        # concatenated chunk payloads stay unambiguous.
        digest.update(b"\x1e")
        chunk = records[start : start + _CHECKSUM_CHUNK_RECORDS]
        digest.update(canonical_json(chunk).encode("utf-8"))
    return digest.hexdigest()


def _serialize_output_cell(value: object) -> object:
    """Serialize one output cell to its canonical checksum representation.

    Args:
        value: One cell value from the assembled output frame.

    Returns:
        A JSON-safe representation: ``None`` for missing values, a ``Z``
        UTC ISO string for timestamps, a ``float.hex()`` string for finite
        floats (normalizing negative zero), or the original value.
    """
    logger.debug("Serializing one output cell to canonical checksum form")
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.tz_convert("UTC").isoformat().replace("+00:00", "Z")
    if isinstance(value, float):
        normalized = 0.0 if value == 0.0 else value
        return float.hex(normalized)
    return value


def _output_checksum(frame: pd.DataFrame) -> str:
    """Compute the canonical SHA-256 output-values digest.

    Args:
        frame: The fully assembled result values frame, in exact row and
            column order.

    Returns:
        Lowercase 64-character SHA-256 hexadecimal digest.
    """
    logger.debug("Computing canonical output checksum over %d rows", len(frame))
    rows = [
        [_serialize_output_cell(cell) for cell in row]
        for row in frame.itertuples(index=False, name=None)
    ]
    encoded = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _project_source_frame(data: MarketDataset) -> pd.DataFrame:
    """Privately project one ``MarketDataset`` into its canonical columns.

    Args:
        data: One normalized ``MarketDataset v1`` of bar records.

    Returns:
        A UTC-indexed DataFrame with the dataset's symbol and OHLCV
        columns, in dataset row order.
    """
    logger.debug("Projecting source MarketDataset for join_to (%s)", data.symbol)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    frame = pd.DataFrame(index=index)
    frame["symbol"] = data.symbol
    frame["open"] = [float(record.open) for record in records]
    frame["high"] = [float(record.high) for record in records]
    frame["low"] = [float(record.low) for record in records]
    frame["close"] = [float(record.close) for record in records]
    frame["volume"] = [float(record.volume) for record in records]
    return frame


def _validate_finalization_shape(
    data: MarketDataset,
    output_columns: tuple[str, ...],
    output_values: pd.DataFrame,
    unavailable_reason: pd.Series,
) -> str:
    """Validate atomic row/column completeness and resolve the timeframe.

    Args:
        data: One normalized ``MarketDataset v1``.
        output_columns: Deterministic output columns in canonical order.
        output_values: The computed indicator output columns.
        unavailable_reason: Per-row warmup marker aligned to the output.

    Returns:
        The dataset's non-empty source timeframe.

    Raises:
        IndicatorError: If rows/columns are incomplete (``IND_PARTIAL_RESULT``)
            or the dataset timeframe is unexpectedly missing
            (``IND_INTERNAL_ERROR``).
    """
    logger.debug("Validating finalization shape for %s", data.symbol)
    if len(output_values) != data.record_count:
        raise IndicatorError(
            IndicatorErrorCode.IND_PARTIAL_RESULT,
            "result row count does not match the input dataset",
        )
    missing_columns = tuple(
        column for column in output_columns if column not in output_values.columns
    )
    if missing_columns:
        raise IndicatorError(
            IndicatorErrorCode.IND_PARTIAL_RESULT,
            "one or more official output columns are missing",
            {"columns": missing_columns},
        )
    is_warmup = unavailable_reason.notna()
    for column in output_columns:
        column_is_nan = output_values[column].isna()
        if (column_is_nan != is_warmup).any():
            raise IndicatorError(
                IndicatorErrorCode.IND_PARTIAL_RESULT,
                "output values are not atomically consistent with warmup rows",
                {"column": column},
            )
    if data.timeframe is None:
        raise IndicatorError(
            IndicatorErrorCode.IND_INTERNAL_ERROR,
            "dataset timeframe was missing after validation",
        )
    return data.timeframe


def _validate_finalization_causality(
    computed_from_start: pd.Series,
    computed_from_end: pd.Series,
    available_at: pd.Series,
    unavailable_reason: pd.Series,
    timestamps: pd.Index,
) -> None:
    """Validate causal, internally consistent availability metadata.

    Args:
        computed_from_start: Per-row inclusive dependency start.
        computed_from_end: Per-row inclusive dependency end.
        available_at: Per-row earliest safe decision time.
        unavailable_reason: Per-row warmup marker.
        timestamps: The result's UTC row timestamps.

    Raises:
        IndicatorError: If a valid row's causal bounds are inconsistent
            (``IND_LOOKAHEAD_RISK``).
    """
    logger.debug("Validating finalization causality for %d rows", len(timestamps))
    is_valid = unavailable_reason.isna()
    if not is_valid.any():
        return
    start = pd.Series(computed_from_start).to_numpy()
    end = pd.Series(computed_from_end).to_numpy()
    at = pd.Series(available_at).to_numpy()
    row_time = pd.Series(timestamps).to_numpy()
    valid_mask = is_valid.to_numpy()
    if (
        (start[valid_mask] > end[valid_mask]).any()
        or (end[valid_mask] != row_time[valid_mask]).any()
        or (at[valid_mask] < end[valid_mask]).any()
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_LOOKAHEAD_RISK,
            "availability or dependency-window bounds are not causal",
        )


def _validate_finalization_values(
    output_values: pd.DataFrame, unavailable_reason: pd.Series
) -> None:
    """Validate that every non-warmup output value is finite.

    Args:
        output_values: The computed indicator output columns.
        unavailable_reason: Per-row warmup marker aligned to the output.

    Raises:
        IndicatorError: If a non-warmup output value is not finite
            (``IND_INTERNAL_ERROR``).
    """
    logger.debug("Validating finalization output value finiteness")
    is_valid = unavailable_reason.isna()
    for column in output_values.columns:
        values = output_values.loc[is_valid, column].to_numpy(dtype="float64")
        if values.size and not bool(pd.Series(values).apply(math.isfinite).all()):
            raise IndicatorError(
                IndicatorErrorCode.IND_INTERNAL_ERROR,
                "a non-warmup output value is not finite",
                {"column": column},
            )


def build_indicator_result(
    *,
    data: MarketDataset,
    config: IndicatorConfig,
    indicator_version: str,
    output_columns: tuple[str, ...],
    output_values: pd.DataFrame,
    available_at: pd.Series,
    computed_from_start: pd.Series,
    computed_from_end: pd.Series,
    unavailable_reason: pd.Series,
) -> IndicatorResult:
    """Assemble the deterministic ``IndicatorResult`` for one calculation.

    This internal helper is shared by all twenty official trend, volatility,
    momentum, volume, and candle calculators so identity, checksum, and
    finalization logic is implemented exactly once, per ``FR-INDI-007``
    through ``FR-INDI-010``.

    It is deliberately not part of the package's public API: it appears in no
    ``__all__`` and is not a documented import for callers outside this
    package. Public consumers construct results only by calling an official
    indicator convenience function.

    Args:
        data: One normalized, validated ``MarketDataset v1``.
        config: The complete, validated calculation configuration.
        indicator_version: The official implementation version.
        output_columns: Deterministic output columns in canonical order.
        output_values: The computed indicator output columns, indexed by
            the dataset's UTC timestamps, with ``NaN`` warmup values.
        available_at: Per-row earliest safe decision time.
        computed_from_start: Per-row inclusive dependency start
            (``NaT`` during warmup).
        computed_from_end: Per-row inclusive dependency end
            (``NaT`` during warmup).
        unavailable_reason: Per-row marker: ``"warmup"`` or ``pandas.NA``.

    Returns:
        The atomic, deterministic ``IndicatorResult``.

    Raises:
        IndicatorError: On any finalization invariant violation.
    """
    logger.info(
        "Building IndicatorResult for indicator_id=%s symbol=%s",
        config.indicator_id,
        data.symbol,
    )
    # Finalization step 1: snapshot the input identity before finalization so
    # any mutation of the (immutable) dataset during result assembly is caught
    # deterministically rather than silently overwriting data.
    input_checksum = _input_checksum(data)
    source_timeframe = _validate_finalization_shape(
        data, output_columns, output_values, unavailable_reason
    )
    _validate_finalization_causality(
        computed_from_start,
        computed_from_end,
        available_at,
        unavailable_reason,
        output_values.index,
    )
    _validate_finalization_values(output_values, unavailable_reason)

    frame = pd.DataFrame(index=output_values.index.copy())
    frame.index.name = "timestamp"
    frame["symbol"] = data.symbol
    for column in output_columns:
        frame[column] = output_values[column].to_numpy(dtype="float64", copy=True)
    frame["available_at"] = pd.Series(available_at).to_numpy(copy=True)
    frame["computed_from_start"] = pd.Series(computed_from_start).to_numpy(copy=True)
    frame["computed_from_end"] = pd.Series(computed_from_end).to_numpy(copy=True)
    frame["source_timeframe"] = source_timeframe
    frame["data_quality_status"] = data.quality_report.quality_status
    frame["data_quality_score"] = float(data.quality_report.quality_score)
    frame["unavailable_reason"] = pd.Series(unavailable_reason).to_numpy(copy=True)

    if _input_checksum(data) != input_checksum:
        raise IndicatorError(
            IndicatorErrorCode.IND_INPUT_MUTATION_DETECTED,
            "input dataset changed during result finalization",
            {"indicator_id": config.indicator_id},
        )
    parameter_hash = _parameter_hash(config)
    output_checksum = _output_checksum(frame)

    manifest = IndicatorManifest(
        indicator_id=config.indicator_id,
        indicator_version=indicator_version,
        formula_version=config.formula_version,
        parameter_hash=parameter_hash,
        input_checksum=input_checksum,
        output_checksum=output_checksum,
        output_columns=output_columns,
        row_count=len(frame),
        symbol=data.symbol,
        source_timeframe=source_timeframe,
        normalization_version=data.normalization_version,
        source_metadata=dict(data.source_metadata),
        license_metadata=dict(data.license_metadata),
        quality_status=data.quality_report.quality_status,  # type: ignore[arg-type]
        quality_score=str(data.quality_report.quality_score),
        quality_schema_version=data.quality_report.schema_version,
    )

    return IndicatorResult(
        indicator_id=config.indicator_id,
        indicator_version=indicator_version,
        formula_version=config.formula_version,
        parameter_hash=parameter_hash,
        values=frame,
        output_columns=output_columns,
        manifest=manifest,
    )


__all__ = ["IndicatorManifest", "IndicatorResult"]
