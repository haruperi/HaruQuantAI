"""Read real Data Manager history and adapt indicator calculation contracts."""

from __future__ import annotations

from collections.abc import Mapping
from itertools import pairwise
from typing import Any

import numpy as np

from app.include.blocks.price import BarPrice
from app.include.blocks.series import BarData
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.data_manager.data.review import DatasetReview
from app.workspace.data_manager.data.storage import require_data


def historical_bars(
    gateway: Any, symbol: str, timeframe: str, count: int
) -> tuple[BarPrice, list[int]]:
    """Read the latest requested bars from one matching stored dataset."""
    rows = require_data(
        gateway.read_records(
            "datamgr_datasets",
            filters={"symbol": symbol, "timeframe": timeframe},
            limit=1000,
        )
    )["records"]
    rows = [
        row
        for row in rows
        if row["bars"] >= count and row.get("data_kind", "bars") == "bars"
    ]
    if not rows:
        raise CodeEditorError(
            f"No stored {symbol} {timeframe} history with {count} bars. Import history in Data Manager first."
        )
    if len(rows) != 1:
        raise CodeEditorError(
            f"Multiple datasets match {symbol} {timeframe}; keep one source for this test"
        )
    review = DatasetReview(gateway, rows[0]["id"])
    if review.calendar() is None:
        # Keep large histories lazy; materialize only the test window.
        from app.include.market_storage import scan_catalog

        lazy = scan_catalog(review.record, decode=True)
        frame = (
            lazy.sort("DateTime")
            .tail(count)
            .collect()
            .to_pandas()
            .set_index("DateTime")
        )
    else:
        frame = review.frame().tail(count)
    if len(frame) < count:
        raise CodeEditorError(
            "Stored history is shorter than the requested test window"
        )
    arrays = {
        name: frame[name.title()].to_numpy(dtype=np.float64)
        for name in ("open", "high", "low", "close", "volume")
    }
    if any(not np.isfinite(values).all() for values in arrays.values()):
        raise CodeEditorError("Historical bars contain missing or non-finite prices")
    timestamps = [int(stamp.timestamp()) for stamp in frame.index]
    if any(right <= left for left, right in pairwise(timestamps)):
        raise CodeEditorError("Historical bar timestamps must be strictly increasing")
    return BarPrice(
        **{name + "_data": value for name, value in arrays.items()}
    ), timestamps


def indicator_defaults(cls: Any) -> dict[str, Any]:
    """Read configuration defaults from the canonical indicator model."""
    return {
        name: field.default
        for name, field in cls.model_fields.items()
        if not field.is_required()
    }


def calculate_indicator(
    cls: Any,
    bars: BarPrice | BarData,
    params: Mapping[str, Any],
    timestamps: list[int] | None = None,
) -> Any:
    """Instantiate validated configuration and execute the canonical contract once."""
    context = (
        bars
        if isinstance(bars, BarData)
        else BarData(
            prices=bars,
            timestamps=(
                np.asarray(timestamps, dtype=np.int64)
                if timestamps is not None
                else np.array([], dtype=np.int64)
            ),
        )
    )
    try:
        return cls(**params).calculate(context)
    except Exception as exc:
        raise CodeEditorError(f"Indicator calculation failed: {exc}") from exc


def output_series(result: Any, count: int) -> dict[str, np.ndarray[Any, Any]]:
    """Normalize scalar and multi-output indicators without fabricating values."""
    outputs = result if isinstance(result, dict) else {"value": result}
    series = {}
    for name, value in outputs.items():
        values = np.asarray(getattr(value, "values", value), dtype=np.float64)
        if values.ndim != 1 or len(values) != count:
            raise CodeEditorError(
                f"Indicator output '{name}' must contain one value per historical bar"
            )
        series[str(name)] = values
    if not series:
        raise CodeEditorError("Indicator returned no output series")
    return series
