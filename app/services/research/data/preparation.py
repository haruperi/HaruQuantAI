"""Deterministic cleaning and enrichment for Research datasets."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from app.services.data import to_ohlcv_dataframe
from app.services.research.contracts import (
    CleaningConfig,
    DataQualityReport,
    EnrichmentConfig,
    PreparedDataset,
    ResearchResourceLimits,
    ResearchWarning,
)
from app.services.research.data.validation import validate_dataset
from app.utils import canonical_digest, canonical_json, logger
from app.utils.errors import ValidationError

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_WEEKEND_START = 5


def _quality_with(
    report: DataQualityReport,
    *,
    warnings: tuple[ResearchWarning, ...] = (),
    actions: tuple[Mapping[str, JSONValue], ...] = (),
) -> DataQualityReport:
    """Return quality evidence with appended warnings and actions.

    Args:
        report: Existing quality evidence.
        warnings: New warnings.
        actions: Explicit cleaning actions.

    Returns:
        New immutable quality report.
    """
    logger.debug("Appending Research quality evidence")
    return DataQualityReport(
        report.fatal_issues,
        (*report.warnings, *warnings),
        report.checks,
        (*report.cleaning_actions, *actions),
    )


def _clean_duplicates(
    frame: pd.DataFrame, strategy: str
) -> tuple[pd.DataFrame, tuple[Mapping[str, JSONValue], ...]]:
    """Apply the explicit duplicate policy.

    Args:
        frame: Detached frame.
        strategy: Approved duplicate policy.

    Returns:
        Updated frame and actions.

    Raises:
        ValidationError: If duplicates exist under the error policy.
    """
    logger.debug("Applying Research duplicate policy")
    if not frame.index.has_duplicates:
        return frame, ()
    if strategy == "error":
        raise ValidationError("RES_INPUT_INVALID", "DUPLICATE_TIMESTAMPS")
    keep = False if strategy == "drop" else strategy.removeprefix("keep_")
    cleaned = frame.loc[~frame.index.duplicated(keep=keep)]
    action: Mapping[str, JSONValue] = {
        "code": "DUPLICATES_REMOVED",
        "rows": len(frame) - len(cleaned),
    }
    return cleaned, (action,)


def _clean_calendar(
    frame: pd.DataFrame, strategy: str
) -> tuple[
    pd.DataFrame,
    tuple[ResearchWarning, ...],
    tuple[Mapping[str, JSONValue], ...],
]:
    """Apply the explicit non-trading-period policy.

    Args:
        frame: Detached frame.
        strategy: Approved calendar policy.

    Returns:
        Updated frame, warnings, and actions.
    """
    logger.debug("Applying Research calendar cleaning policy")
    weekend = frame.index.dayofweek >= _WEEKEND_START
    if strategy == "drop":
        cleaned = frame.loc[~weekend]
        action: Mapping[str, JSONValue] = {
            "code": "NON_TRADING_ROWS_REMOVED",
            "rows": len(frame) - len(cleaned),
        }
        return cleaned, (), (action,)
    if bool(weekend.any()):
        warning = ResearchWarning(
            "NON_TRADING_PERIOD", "Weekend rows retained", "warning", "timestamp"
        )
        return frame, (warning,), ()
    return frame, (), ()


def _clean_spreads(
    frame: pd.DataFrame, strategy: str
) -> tuple[
    pd.DataFrame,
    tuple[ResearchWarning, ...],
    tuple[Mapping[str, JSONValue], ...],
]:
    """Apply the explicit spread-quality policy.

    Args:
        frame: Detached frame.
        strategy: Approved spread policy.

    Returns:
        Updated frame, warnings, and actions.

    Raises:
        ValidationError: If invalid spreads exist under the error policy.
    """
    logger.debug("Applying Research spread cleaning policy")
    invalid = ~np.isfinite(frame["spread"]) | (frame["spread"] < 0)
    if not bool(invalid.any()):
        return frame, (), ()
    if strategy == "error":
        raise ValidationError("RES_INPUT_INVALID", "INVALID_SPREAD")
    if strategy == "drop_invalid":
        cleaned = frame.loc[~invalid]
        action: Mapping[str, JSONValue] = {
            "code": "INVALID_SPREAD_ROWS_REMOVED",
            "rows": int(invalid.sum()),
        }
        return cleaned, (), (action,)
    warning = ResearchWarning(
        "INVALID_SPREAD", "Invalid spreads retained", "warning", "spread"
    )
    return frame, (warning,), ()


def clean_dataset(
    dataset: MarketDataset,
    *,
    config: CleaningConfig,
    report: DataQualityReport,
    limits: ResearchResourceLimits,
) -> tuple[pd.DataFrame, DataQualityReport]:
    """Clean a detached frame using only explicit approved policies.

    Args:
        dataset: Canonical Data-owned bar dataset.
        config: Explicit cleaning actions.
        report: Validation evidence for the source dataset.
        limits: Approved Research resource ceilings.

    Returns:
        Cleaned detached frame and updated quality evidence.

    Raises:
        ValidationError: If fatal evidence or a resource/input failure exists.
    """
    logger.info("Cleaning Research dataset with explicit policies")
    if dataset.record_count > limits.max_rows:
        raise ValidationError("RES_RESOURCE_LIMIT_EXCEEDED", "ROW_LIMIT_EXCEEDED")
    if report.fatal_issues:
        raise ValidationError("RES_INPUT_INVALID", "FATAL_QUALITY_ISSUES")
    frame = to_ohlcv_dataframe(dataset).copy(deep=True)
    frame, duplicate_actions = _clean_duplicates(frame, config.duplicate_strategy)
    frame, calendar_warnings, calendar_actions = _clean_calendar(
        frame, config.non_trading_period_strategy
    )
    frame, spread_warnings, spread_actions = _clean_spreads(
        frame, config.spread_strategy
    )
    if frame.empty:
        raise ValidationError("RES_INSUFFICIENT_DATA", "NO_ROWS_AFTER_CLEANING")
    return frame, _quality_with(
        report,
        warnings=(*calendar_warnings, *spread_warnings),
        actions=(*duplicate_actions, *calendar_actions, *spread_actions),
    )


def enrich_dataset(
    data: pd.DataFrame,
    *,
    config: EnrichmentConfig,
    report: DataQualityReport,
) -> tuple[pd.DataFrame, DataQualityReport]:
    """Add explicitly selected Research enrichment fields to a copy.

    The UTC index and row order are preserved. The canonical forward label is the
    one-bar log return named ``forward_return_1``; its final row is explicit NaN and
    the column is marked research-only in frame attributes.

    Args:
        data: Clean detached OHLCV/spread frame.
        config: Explicit enrichment selection.
        report: Current quality evidence.

    Returns:
        Enriched detached frame and quality evidence.

    Raises:
        ValidationError: If required structural inputs are absent.
    """
    logger.info("Enriching Research dataset")
    required = {"open", "high", "low", "close", "volume", "spread"}
    if not required <= set(data.columns):
        raise ValidationError("RES_INPUT_INVALID", "OHLCVS_COLUMNS_REQUIRED")
    enriched = data.copy(deep=True)
    if config.include_geometry:
        enriched["candle_range"] = enriched["high"] - enriched["low"]
        enriched["candle_body"] = (enriched["close"] - enriched["open"]).abs()
        enriched["upper_wick"] = enriched["high"] - enriched[["open", "close"]].max(
            axis=1
        )
        enriched["lower_wick"] = (
            enriched[["open", "close"]].min(axis=1) - enriched["low"]
        )
    if config.include_returns:
        enriched["simple_return"] = enriched["close"].pct_change(fill_method=None)
        enriched["log_return"] = np.log(enriched["close"] / enriched["close"].shift(1))
    if config.include_forward_labels:
        enriched["forward_return_1"] = np.log(
            enriched["close"].shift(-1) / enriched["close"]
        )
        enriched.attrs["research_only_columns"] = ("forward_return_1",)
    if config.include_calendar:
        if (
            not isinstance(enriched.index, pd.DatetimeIndex)
            or enriched.index.tz is None
        ):
            raise ValidationError("RES_INPUT_INVALID", "UTC_TIME_INDEX_REQUIRED")
        enriched["calendar_year"] = enriched.index.year
        enriched["calendar_month"] = enriched.index.month
        enriched["calendar_weekday"] = enriched.index.dayofweek
        enriched["calendar_hour"] = enriched.index.hour
    enriched.attrs["symbol"] = config.symbol
    return enriched, report


def prepare_research_dataset(
    dataset: MarketDataset,
    *,
    cleaning: CleaningConfig,
    enrichment: EnrichmentConfig,
    limits: ResearchResourceLimits,
) -> PreparedDataset:
    """Run validate, clean, revalidate, and enrich deterministically.

    Args:
        dataset: Canonical Data-owned market dataset.
        cleaning: Explicit cleaning policy.
        enrichment: Explicit enrichment policy.
        limits: Approved resource ceilings.

    Returns:
        Detached prepared Research dataset with hashes and provenance.

    Raises:
        ValidationError: If validation, cleaning, or resource checks fail.
    """
    logger.info("Preparing canonical Research dataset")
    initial_report = validate_dataset(dataset, limits=limits)
    if initial_report.fatal_issues:
        raise ValidationError("RES_INPUT_INVALID", "FATAL_QUALITY_ISSUES")
    cleaned, cleaned_report = clean_dataset(
        dataset, config=cleaning, report=initial_report, limits=limits
    )
    enriched, final_report = enrich_dataset(
        cleaned, config=enrichment, report=cleaned_report
    )
    dataset_hash = canonical_digest(dataset.model_dump(mode="json"))
    config_payload = {
        "cleaning": {
            "timezone": cleaning.timezone,
            "duplicate_strategy": cleaning.duplicate_strategy,
            "missing_bar_strategy": cleaning.missing_bar_strategy,
            "non_trading_period_strategy": cleaning.non_trading_period_strategy,
            "spread_strategy": cleaning.spread_strategy,
        },
        "enrichment": {
            "symbol": enrichment.symbol,
            "include_geometry": enrichment.include_geometry,
            "include_returns": enrichment.include_returns,
            "include_forward_labels": enrichment.include_forward_labels,
            "include_calendar": enrichment.include_calendar,
        },
    }
    configuration_hash = hashlib.sha256(
        canonical_json(config_payload).encode()
    ).hexdigest()
    sources = tuple(sorted({dataset.request_id, *dataset.source_metadata.values()}))
    return PreparedDataset(
        enriched, "v1", final_report, dataset_hash, configuration_hash, sources
    )


__all__ = ("clean_dataset", "enrich_dataset", "prepare_research_dataset")
