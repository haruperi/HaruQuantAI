"""Research dataset preparation pipeline."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.research.session_config import session_hours_payload
from app.services.utils.logger import logger
from app.services.utils.validators import (
    DEFAULT_SCHEMA,
    DataSource,
    OHLCVSchema,
    prepare_ohlcv_data,
)

from .cleaning import CleaningConfig, clean_dataset
from .enrichment import EnrichmentConfig, enrich_dataset
from .models import CanonicalOHLCVSSchema, PreparedDataset
from .validation import validate_dataset


def _fetch_source_ohlcv(
    *,
    source: DataSource,
    symbol: str,
    timeframe: str,
    start_pos: int,
    end_pos: int,
    exclude_last_bar: bool,
    schema: OHLCVSchema,
) -> pd.DataFrame:
    """Fetch and prepare OHLCV data from a route-provided data source."""
    logger.info(
        f"Loading OHLCV data for {symbol} {timeframe} (bars {start_pos}-{end_pos})"
    )
    df = source.fetch_data(
        symbol=symbol,
        timeframe=timeframe,
        start_pos=start_pos,
        end_pos=end_pos,
    )
    if df is None or df.empty:
        raise ValueError(f"No data returned for {symbol} {timeframe}")

    out = prepare_ohlcv_data(df, schema=schema)
    if exclude_last_bar and len(out) > 2:
        out = out.iloc[:-1]
    logger.info(
        f"Loaded {len(out)} bars for {symbol} {timeframe} ({out.index[0]} to {out.index[-1]})"
    )
    return out


def _synthesize_ohlcvs_columns(
    df: pd.DataFrame, schema: CanonicalOHLCVSSchema
) -> pd.DataFrame:
    """Ensure canonical volume and spread columns exist for analysis."""
    out = df.copy()
    if schema.volume not in out.columns:
        out[schema.volume] = 0.0
    if schema.spread not in out.columns:
        prepared = prepare_ohlcv_data(out, schema=schema)
        out[schema.spread] = prepared[schema.spread].to_numpy()
        if schema.volume in prepared.columns:
            out[schema.volume] = prepared[schema.volume].to_numpy()
    return out


def prepare_research_dataset(
    source: DataSource,
    symbol: str,
    timeframe: str,
    start_pos: int,
    end_pos: int,
    *,
    exclude_last_bar: bool = True,
    schema: OHLCVSchema | None = None,
    cleaning: Any | None = None,
    enrichment: Any | None = None,
) -> PreparedDataset:
    """Fetch, clean, validate, and enrich a research-ready OHLCVS dataset."""
    schema = schema or DEFAULT_SCHEMA
    canonical = CanonicalOHLCVSSchema(
        open=schema.open,
        high=schema.high,
        low=schema.low,
        close=schema.close,
        volume=schema.volume,
        spread="Spread",
    )
    raw = _fetch_source_ohlcv(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        start_pos=start_pos,
        end_pos=end_pos,
        exclude_last_bar=exclude_last_bar,
        schema=schema,
    )
    raw = _synthesize_ohlcvs_columns(raw, canonical)

    duplicate_rows = 0
    if raw.index.has_duplicates:
        duplicate_rows = int(raw.index.duplicated(keep="last").sum())
        raw = raw.loc[~raw.index.duplicated(keep="last")].sort_index()
        logger.warning(
            f"Dropped {duplicate_rows} duplicate timestamp rows for {symbol} {timeframe} before validation"
        )

    report = validate_dataset(raw, schema=canonical, timeframe=timeframe)
    if not report.is_valid:
        raise ValueError(
            f"Dataset validation failed for {symbol} {timeframe}: {len(report.fatal_errors)} fatal errors"
        )

    cleaning_config = cleaning or CleaningConfig(timeframe=timeframe)
    enrichment_config = enrichment or EnrichmentConfig(symbol=symbol)
    cleaned = clean_dataset(
        raw, report=report, schema=canonical, config=cleaning_config
    )
    enriched = enrich_dataset(cleaned, schema=canonical, config=enrichment_config)
    report.metadata.update(
        {
            "symbol": symbol,
            "timeframe": timeframe,
            "n_rows": len(enriched),
            "start": str(enriched.index.min()) if len(enriched) else None,
            "end": str(enriched.index.max()) if len(enriched) else None,
            "session_basis": enrichment_config.session_basis,
            "session_hours": session_hours_payload(),
            "deduplicated_rows": duplicate_rows,
        }
    )
    return PreparedDataset(data=enriched, report=report, schema=canonical)
