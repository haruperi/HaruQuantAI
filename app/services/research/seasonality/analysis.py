"""Canonical session/hour opportunity analysis for Research."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from app.services.research.contracts import ResearchWarning
from app.services.research.seasonality.sessions import tag_sessions
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.research.contracts import (
        PreparedDataset,
        ResearchResourceLimits,
        SessionConfig,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_ADR_PERIOD = 14
_MIN_BUCKET_SAMPLES = 2
_VALID_MONTHS = frozenset(range(1, 13))
_VALID_WEEKDAYS = frozenset(range(7))
_VALID_HOURS = frozenset(range(24))
_MIN_YEAR = 1970


@dataclass(frozen=True, slots=True)
class SeasonalityFilters:
    """Immutable optional calendar, session, symbol, and hour filters.

    These filters never embed session definitions; they only select rows.
    """

    years: tuple[int, ...] = ()
    months: tuple[int, ...] = ()
    weekdays: tuple[int, ...] = ()
    hours: tuple[int, ...] = ()
    sessions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate declared filter ranges.

        Raises:
            ValueError: If any declared range is invalid.
        """
        logger.debug("Validating Research seasonality filters")
        if self.years and any(y < _MIN_YEAR for y in self.years):
            raise ValueError("RES_INPUT_INVALID", "INVALID_YEAR_FILTER")
        if self.months and not set(self.months) <= _VALID_MONTHS:
            raise ValueError("RES_INPUT_INVALID", "INVALID_MONTH_FILTER")
        if self.weekdays and not set(self.weekdays) <= _VALID_WEEKDAYS:
            raise ValueError("RES_INPUT_INVALID", "INVALID_WEEKDAY_FILTER")
        if self.hours and not set(self.hours) <= _VALID_HOURS:
            raise ValueError("RES_INPUT_INVALID", "INVALID_HOUR_FILTER")
        if self.sessions and any(
            not s.strip() or s != s.strip() for s in self.sessions
        ):
            raise ValueError("RES_INPUT_INVALID", "INVALID_SESSION_FILTER")


def _apply_filters(tagged: pd.DataFrame, filters: SeasonalityFilters) -> pd.DataFrame:
    """Return a copy containing only rows passing the declared filters.

    Args:
        tagged: Frame already carrying a ``session`` column.
        filters: Immutable selection filters.

    Returns:
        A filtered frame copy.
    """
    logger.debug("Applying Research seasonality filters")
    mask = pd.Series(True, index=tagged.index)
    index_data = tagged.index
    if filters.years:
        mask &= pd.Series(index_data.year).isin(filters.years).to_numpy()
    if filters.months:
        mask &= pd.Series(index_data.month).isin(filters.months).to_numpy()
    if filters.weekdays:
        mask &= pd.Series(index_data.weekday).isin(filters.weekdays).to_numpy()
    if filters.hours:
        mask &= pd.Series(index_data.hour).isin(filters.hours).to_numpy()
    if filters.sessions:
        mask &= tagged["session"].isin(filters.sessions).to_numpy()
    return tagged[mask].copy()


def _session_summaries(
    filtered: pd.DataFrame, *, returns: pd.Series
) -> tuple[list[Mapping[str, JSONValue]], list[ResearchWarning]]:
    """Compute per-session mean return, win rate, and sample count.

    Args:
        filtered: Filtered frame carrying a ``session`` column.
        returns: Aligned log-return series.

    Returns:
        Per-session summary rows and sparse-bucket warnings.
    """
    logger.debug("Computing Research per-session seasonality summaries")
    rows: list[Mapping[str, JSONValue]] = []
    warnings: list[ResearchWarning] = []
    for name in sorted(set(filtered["session"].to_numpy())):
        session_returns = returns[filtered["session"] == name].dropna()
        sample = int(session_returns.size)
        if sample < _MIN_BUCKET_SAMPLES:
            warnings.append(
                ResearchWarning(
                    "SPARSE_BUCKET",
                    "Seasonality bucket has too few samples",
                    "warning",
                    f"session.{name}",
                    {"sample_count": sample},
                )
            )
            continue
        values = session_returns.to_numpy(dtype="float64")
        rows.append(
            {
                "session": name,
                "sample_count": sample,
                "mean_return": float(values.mean()),
                "win_rate": float(np.mean(values > 0)),
                "std_return": float(values.std(ddof=0)),
            }
        )
    return rows, warnings


def _bucket_row(
    label_key: str,
    label: JSONValue,
    frame: pd.DataFrame,
    returns: pd.Series,
) -> Mapping[str, JSONValue] | None:
    """Summarize one seasonality bucket.

    Args:
        label_key: Field name identifying the bucket.
        label: Bucket identity value.
        frame: Rows belonging to the bucket.
        returns: Aligned log-return series for the same rows.

    Returns:
        Bucket summary row, or ``None`` when the bucket is too sparse.
    """
    values = returns.dropna().to_numpy(dtype="float64")
    if values.size < _MIN_BUCKET_SAMPLES:
        return None
    row: dict[str, JSONValue] = {
        label_key: label,
        "sample_count": int(values.size),
        "mean_return": float(values.mean()),
        "win_rate": float(np.mean(values > 0)),
        "std_return": float(values.std(ddof=0)),
    }
    if "high" in frame and "low" in frame:
        span = (
            frame["high"].astype("float64") - frame["low"].astype("float64")
        ).dropna()
        row["mean_range"] = float(span.mean()) if not span.empty else None
    if "volume" in frame:
        volume = frame["volume"].astype("float64").dropna()
        row["mean_volume"] = float(volume.mean()) if not volume.empty else None
    if "spread" in frame:
        spread = frame["spread"].astype("float64").dropna()
        row["mean_spread"] = float(spread.mean()) if not spread.empty else None
    return row


def _grouped_rows(
    filtered: pd.DataFrame,
    returns: pd.Series,
    *,
    label_key: str,
    labels: np.ndarray,
) -> list[Mapping[str, JSONValue]]:
    """Summarize every bucket produced by one grouping key.

    Args:
        filtered: Filtered frame.
        returns: Aligned log-return series.
        label_key: Field name identifying each bucket.
        labels: Per-row bucket labels.

    Returns:
        Ordered bucket summaries; sparse buckets are omitted.
    """
    rows: list[Mapping[str, JSONValue]] = []
    for label in sorted({int(value) for value in labels}):
        mask = labels == label
        row = _bucket_row(label_key, label, filtered[mask], returns[mask])
        if row is not None:
            rows.append(row)
    return rows


def _hour_weekday_rows(
    filtered: pd.DataFrame, returns: pd.Series
) -> list[Mapping[str, JSONValue]]:
    """Summarize the hour-by-weekday matrix.

    Args:
        filtered: Filtered frame.
        returns: Aligned log-return series.

    Returns:
        One row per populated weekday/hour cell.
    """
    index = filtered.index
    weekdays = np.asarray(index.weekday)
    hours = np.asarray(index.hour)
    rows: list[Mapping[str, JSONValue]] = []
    for weekday in sorted(set(weekdays.tolist())):
        for hour in sorted(set(hours[weekdays == weekday].tolist())):
            mask = (weekdays == weekday) & (hours == hour)
            row = _bucket_row("hour", int(hour), filtered[mask], returns[mask])
            if row is not None:
                rows.append({**row, "weekday": int(weekday)})
    return rows


def _daily_extreme_rows(filtered: pd.DataFrame) -> Mapping[str, JSONValue]:
    """Compute which session owns each day's high and low.

    Args:
        filtered: Filtered frame carrying a ``session`` column.

    Returns:
        Session ownership counts for daily highs and lows.
    """
    if "high" not in filtered or "low" not in filtered or filtered.empty:
        return {"day_count": 0, "high_ownership": [], "low_ownership": []}
    frame = filtered.assign(
        _day=filtered.index.normalize(),
        _high=filtered["high"].astype("float64"),
        _low=filtered["low"].astype("float64"),
    )
    high_owner = frame.loc[frame.groupby("_day")["_high"].idxmax(), "session"]
    low_owner = frame.loc[frame.groupby("_day")["_low"].idxmin(), "session"]
    return {
        "day_count": int(frame["_day"].nunique()),
        "high_ownership": [
            {"session": str(name), "days": int(count)}
            for name, count in high_owner.value_counts().items()
        ],
        "low_ownership": [
            {"session": str(name), "days": int(count)}
            for name, count in low_owner.value_counts().items()
        ],
    }


def _warning_values(
    warnings: list[ResearchWarning],
) -> list[JSONValue]:
    """Project warnings into JSON-compatible evidence.

    Args:
        warnings: Structured Research warnings.

    Returns:
        Detached JSON-compatible warning mappings.
    """
    return [
        {
            "code": warning.code,
            "message": warning.message,
            "severity": warning.severity,
            "field_path": warning.field_path,
            "details": warning.details,
        }
        for warning in warnings
    ]


def _row_number(row: Mapping[str, JSONValue], key: str) -> float:
    """Return one required numeric seasonality summary field.

    Args:
        row: Seasonality summary row.
        key: Numeric field name.

    Returns:
        Numeric field coerced to float.

    Raises:
        ValueError: If the value is missing or non-numeric.
    """
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(  # noqa: TRY004 - Research validation taxonomy.
            "RES_INPUT_INVALID", "INVALID_SEASONALITY_SUMMARY"
        )
    return float(value)


def run_seasonality(
    prepared: PreparedDataset,
    *,
    sessions: SessionConfig,
    filters: SeasonalityFilters,
    limits: ResearchResourceLimits,
) -> Mapping[str, JSONValue]:
    """Compute calendar/session/hour seasonality summaries.

    Computes per-session mean return, win rate, sample counts, sparse-bucket
    warnings, opportunity windows, and extremes from supplied data and filters.

    Args:
        prepared: Prepared Research dataset.
        sessions: Canonical session windows and precedence.
        filters: Immutable row-selection filters.
        limits: Approved resource ceilings.

    Returns:
        Advisory seasonality evidence with warnings.

    Raises:
        ValueError: If data, session, filter, or resource inputs are invalid.
    """
    logger.info("Running Research seasonality analysis")
    if len(prepared.data) > limits.max_rows:
        raise ValueError("RES_RESOURCE_LIMIT_EXCEEDED", "ROW_LIMIT_EXCEEDED")
    if "close" not in prepared.data:
        raise ValueError("RES_INPUT_INVALID", "CLOSE_COLUMN_REQUIRED")
    tagged, tag_warnings = tag_sessions(prepared.data, config=sessions)
    if not isinstance(tagged.index, pd.DatetimeIndex) or tagged.index.tz is None:
        raise ValueError("RES_INPUT_INVALID", "NAIVE_INDEX_REJECTED")
    filtered = _apply_filters(tagged, filters)
    close = filtered["close"].astype("float64")
    if len(close) <= _ADR_PERIOD:
        warnings = list(tag_warnings)
        warnings.append(
            ResearchWarning(
                "INSUFFICIENT_SAMPLES",
                "Too few rows for declared ADR window",
                "warning",
                "adr",
                {"required": _ADR_PERIOD, "observed": len(close)},
            )
        )
        return {
            "schema_version": "v1",
            "adr_period": _ADR_PERIOD,
            "row_count": len(filtered),
            "sessions": [],
            "hours": [],
            "hour_by_weekday": [],
            "calendar": {
                "year": [],
                "month": [],
                "day_of_month": [],
                "day_of_week": [],
            },
            "daily_extremes": {
                "day_count": 0,
                "high_ownership": [],
                "low_ownership": [],
            },
            "opportunity": {},
            "extremes": {},
            "warnings": _warning_values(warnings),
        }
    returns = np.log(close / close.shift(1))
    session_rows, sparse_warnings = _session_summaries(filtered, returns=returns)
    warnings = list(tag_warnings) + sparse_warnings
    opportunity: JSONValue = {}
    if session_rows:
        best = max(session_rows, key=lambda row: _row_number(row, "mean_return"))
        opportunity = {"session": best["session"], "mean_return": best["mean_return"]}
    extremes: JSONValue = {
        "max_return": float(returns.max()) if len(returns) else None,
        "min_return": float(returns.min()) if len(returns) else None,
    }
    session_values: list[JSONValue] = [dict(row) for row in session_rows]
    index = filtered.index
    hour_rows = _grouped_rows(
        filtered, returns, label_key="hour", labels=np.asarray(index.hour)
    )
    calendar: Mapping[str, JSONValue] = {
        "year": _grouped_rows(
            filtered, returns, label_key="year", labels=np.asarray(index.year)
        ),
        "month": _grouped_rows(
            filtered, returns, label_key="month", labels=np.asarray(index.month)
        ),
        "day_of_month": _grouped_rows(
            filtered, returns, label_key="day_of_month", labels=np.asarray(index.day)
        ),
        "day_of_week": _grouped_rows(
            filtered,
            returns,
            label_key="day_of_week",
            labels=np.asarray(index.weekday),
        ),
    }
    if hour_rows:
        best_hour = max(hour_rows, key=lambda row: _row_number(row, "mean_return"))
        dead_hour = min(hour_rows, key=lambda row: _row_number(row, "mean_return"))
        opportunity = {
            **(opportunity if isinstance(opportunity, dict) else {}),
            "best_hour": best_hour["hour"],
            "best_hour_mean_return": best_hour["mean_return"],
            "dead_hour": dead_hour["hour"],
            "dead_hour_mean_return": dead_hour["mean_return"],
        }
    if session_rows:
        worst = min(session_rows, key=lambda row: _row_number(row, "mean_return"))
        opportunity = {
            **(opportunity if isinstance(opportunity, dict) else {}),
            "dead_session": worst["session"],
            "dead_session_mean_return": worst["mean_return"],
        }
    return {
        "schema_version": "v1",
        "adr_period": _ADR_PERIOD,
        "row_count": len(filtered),
        "sessions": session_values,
        "hours": hour_rows,
        "hour_by_weekday": _hour_weekday_rows(filtered, returns),
        "calendar": calendar,
        "daily_extremes": _daily_extreme_rows(filtered),
        "opportunity": opportunity,
        "extremes": extremes,
        "warnings": _warning_values(warnings),
    }


__all__ = ("SeasonalityFilters", "run_seasonality")
