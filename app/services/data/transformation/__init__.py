"""Deterministic reshaping of canonical datasets.

Pure functions over a ``MarketDataset``: no I/O, no clock, no lookahead. Every
operation propagates the source dataset's quality report with updated provenance
rather than recomputing it — a transform changes the shape of a series, not the
trustworthiness of the observations behind it. A caller needing post-transform
evidence asks ``quality`` for it explicitly.
"""

from app.services.data.transformation.alignment import (
    align_datasets,
    align_multitimeframe_data,
)
from app.services.data.transformation.resampling import resample_dataset, resample_ohlcv
from app.services.data.transformation.tabular import (
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.services.data.transformation.tick_aggregation import (
    aggregate_ticks,
    aggregate_ticks_to_bars,
)

__all__ = [
    "aggregate_ticks",
    "aggregate_ticks_to_bars",
    "align_datasets",
    "align_multitimeframe_data",
    "resample_dataset",
    "resample_ohlcv",
    "to_ohlcv_dataframe",
    "to_tick_dataframe",
]
