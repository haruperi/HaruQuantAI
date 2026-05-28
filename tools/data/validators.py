# mypy: disable-error-code=no-untyped-def
"""OHLCV market-data preparation and quality validation utilities.

Exported AI Tools:
    - validate_ohlcv_quality

Public Utility Helpers:
    - prepare_ohlcv_data
    - validate_price_sanity
    - validate_spread
    - validate_numeric_integrity
    - validate_missing_timestamps
    - validate_duplicates
    - validate_monotonic_timestamps
    - validate_zero_volume
    - validate_gaps
    - validate_spikes
    - validate_flatlines
    - validate_duplicate_ohlc_rows

Classes:
    - DataQualityReport
    - DataSource
    - OHLCVSchema
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol, cast

import numpy as np
import pandas as pd

from tools.utils.logger import logger

TOOL_NAME = "validate_ohlcv_quality"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False
VALIDATION_PROFILES = {
    "research": {
        "min_quality_score": 50.0,
        "min_coverage_ratio": 0.0,
        "allow_timezone_naive": True,
        "allow_zero_spread": True,
    },
    "backtest": {
        "min_quality_score": 80.0,
        "min_coverage_ratio": 0.95,
        "allow_timezone_naive": True,
        "allow_zero_spread": True,
    },
    "optimization": {
        "min_quality_score": 90.0,
        "min_coverage_ratio": 0.98,
        "allow_timezone_naive": False,
        "allow_zero_spread": False,
    },
    "live": {
        "min_quality_score": 95.0,
        "min_coverage_ratio": 0.99,
        "allow_timezone_naive": False,
        "allow_zero_spread": False,
    },
}


@dataclass(frozen=True)
class OHLCVSchema:
    """Expected OHLCVS column name mapping."""

    open: str = "Open"
    high: str = "High"
    low: str = "Low"
    close: str = "Close"
    volume: str = "Volume"
    spread: str = "Spread"


@dataclass(frozen=True)
class DataQualityReport:
    """Comprehensive OHLCV quality report container."""

    timestamp: datetime
    total_rows: int
    checks_performed: list[str]
    issues_found: list[dict[str, Any]]
    summary: dict[str, Any]
    quality_score: float
    is_valid: bool
    price_sanity_valid: bool = True
    gaps_count: int = 0
    anomalies_count: int = 0
    missing_timestamps_count: int = 0
    zero_volume_count: int = 0
    duplicates_count: int = 0
    spread_stats: dict[str, float] | None = None
    has_warnings: bool = False
    coverage_ratio: float | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class DataSource(Protocol):
    """Protocol for pluggable OHLCV data sources."""

    def fetch_data(
        self, symbol: str, timeframe: str, start_pos: int, end_pos: int
    ) -> pd.DataFrame | None:
        """Fetch source OHLCV data for validation."""
        ...


def _meta(request_id, ms):
    return {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_risk_level": TOOL_RISK_LEVEL,
        "request_id": request_id,
        "execution_ms": ms,
        "read_only": READ_ONLY,
        "writes_file": WRITES_FILE,
        "modifies_database": MODIFIES_DATABASE,
        "places_trade": PLACES_TRADE,
        "requires_network": REQUIRES_NETWORK,
    }


def _ok(msg, data, request_id, started):
    return {
        "status": "success",
        "message": msg,
        "data": data,
        "error": None,
        "metadata": _meta(request_id, round((time.perf_counter() - started) * 1000, 3)),
    }


def _err(msg, code, details, request_id, started):
    return {
        "status": "error",
        "message": msg,
        "data": None,
        "error": {"code": code, "details": details},
        "metadata": _meta(request_id, round((time.perf_counter() - started) * 1000, 3)),
    }


def validate_find_column(df: pd.DataFrame, target: str) -> str | None:
    """Return actual DataFrame column matching target case-insensitively."""
    for col in df.columns:
        if str(col).lower() == target.lower():
            return str(col)
    return None


def validate_find_columns(df: pd.DataFrame, targets: list[str]) -> dict[str, str]:
    """Return mapping of requested column names to actual names."""
    return {t: c for t in targets if (c := validate_find_column(df, t))}


def validate_get_time_series(df: pd.DataFrame) -> pd.Series | None:
    """Return datetime series from DatetimeIndex or common time columns."""
    if isinstance(df.index, pd.DatetimeIndex):
        return df.index.to_series()
    for name in ("datetime", "time", "timestamp", "date"):
        if col := validate_find_column(df, name):
            return pd.Series(pd.to_datetime(df[col]), index=df.index)
    return None


def prepare_ohlcv_data(
    df: pd.DataFrame, schema: OHLCVSchema | None = None
) -> pd.DataFrame:
    """Prepare OHLCVS data with standard columns and sorted DatetimeIndex."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")
    if df.empty:
        raise ValueError("df cannot be empty.")
    schema = schema or OHLCVSchema()
    out = df.copy()
    lower = {str(c).lower(): c for c in out.columns}
    if not isinstance(out.index, pd.DatetimeIndex):
        time_col = next(
            (lower[n] for n in ("datetime", "time", "timestamp", "date") if n in lower),
            None,
        )
        if time_col is None:
            raise ValueError(
                "Data must have a DatetimeIndex or one of: "
                "datetime, time, timestamp, date."
            )
        out.index = pd.DatetimeIndex(pd.to_datetime(out[time_col]))
        out = out.drop(columns=[time_col])
    aliases = {
        schema.open: {"open", "o"},
        schema.high: {"high", "h"},
        schema.low: {"low", "l"},
        schema.close: {"close", "c"},
        schema.volume: {"volume", "vol", "tick_volume", "tickvolume", "real_volume"},
        schema.spread: {"spread"},
    }
    rename = {
        col: canon
        for col in out.columns
        for canon, opts in aliases.items()
        if str(col).lower() in opts
    }
    out = out.rename(columns=rename)
    missing = [
        c
        for c in [schema.open, schema.high, schema.low, schema.close]
        if c not in out.columns
    ]
    if missing:
        raise ValueError(f"Missing required OHLC columns: {missing}.")
    if schema.volume not in out.columns:
        out[schema.volume] = 0.0
    if schema.spread not in out.columns:
        bid, ask = validate_find_column(out, "bid"), validate_find_column(out, "ask")
        out[schema.spread] = (
            pd.to_numeric(out[ask], errors="coerce")
            - pd.to_numeric(out[bid], errors="coerce")
            if bid and ask
            else 0.0
        )
    return out.sort_index()[
        [
            schema.open,
            schema.high,
            schema.low,
            schema.close,
            schema.volume,
            schema.spread,
        ]
    ]


def validate_numeric_integrity(data: pd.DataFrame, columns: list[str] | None = None):
    """Coerce numeric columns and report invalid values."""
    df = data.copy()
    cols = columns or list(
        validate_find_columns(
            df, ["Open", "High", "Low", "Close", "Volume", "Spread"]
        ).values()
    )
    issues = []
    for col in cols:
        original = df[col]
        coerced = pd.to_numeric(original, errors="coerce")
        non_numeric = coerced.isna() & original.notna()
        missing = original.isna()
        infinite = pd.Series(np.isinf(coerced), index=df.index).fillna(False)
        if non_numeric.any():
            issues.append(
                {
                    "type": "non_numeric",
                    "check": f"{col}_numeric",
                    "column": col,
                    "count": int(non_numeric.sum()),
                    "rows": df[non_numeric].index.tolist()[:100],
                }
            )
        if missing.any():
            issues.append(
                {
                    "type": "missing_values",
                    "check": f"{col}_not_null",
                    "column": col,
                    "count": int(missing.sum()),
                    "rows": df[missing].index.tolist()[:100],
                }
            )
        if infinite.any():
            issues.append(
                {
                    "type": "infinite_values",
                    "check": f"{col}_finite",
                    "column": col,
                    "count": int(infinite.sum()),
                    "rows": df[infinite].index.tolist()[:100],
                }
            )
        df[col] = coerced.replace([np.inf, -np.inf], np.nan)
    return df, issues


def validate_price_sanity(data: pd.DataFrame):
    """Validate OHLC relationships and non-negative/non-zero prices."""
    df = data.copy()
    m = validate_find_columns(df, ["Open", "High", "Low", "Close"])
    issues = []
    if len(m) < 4:
        return (
            False,
            df,
            [
                {
                    "type": "schema_validation",
                    "check": "ohlc_columns",
                    "count": max(len(df), 1),
                    "message": "Required OHLC columns are missing.",
                    "fatal": True,
                }
            ],
        )
    o, h, l, c = m["Open"], m["High"], m["Low"], m["Close"]
    checks = [
        ("high_low", df[h] < df[l]),
        ("open_range", (df[o] < df[l]) | (df[o] > df[h])),
        ("close_range", (df[c] < df[l]) | (df[c] > df[h])),
    ]
    for check, mask in checks:
        if mask.any():
            issues.append(
                {
                    "type": "price_sanity",
                    "check": check,
                    "count": int(mask.sum()),
                    "rows": df[mask].index.tolist()[:100],
                }
            )
    for col in (o, h, l, c):
        neg = df[col] < 0
        zero = df[col] == 0
        if neg.any():
            issues.append(
                {
                    "type": "price_sanity",
                    "check": f"{col}_non_negative",
                    "count": int(neg.sum()),
                    "rows": df[neg].index.tolist()[:100],
                }
            )
        if zero.any():
            issues.append(
                {
                    "type": "zero_price",
                    "check": f"{col}_non_zero",
                    "count": int(zero.sum()),
                    "rows": df[zero].index.tolist()[:100],
                }
            )
    return len(issues) == 0, df, issues


def validate_monotonic_timestamps(data: pd.DataFrame):
    """Check timestamps are monotonic increasing."""
    ts = validate_get_time_series(data)
    if ts is None or len(ts) <= 1:
        return pd.DataFrame(), []
    s = pd.Series(pd.to_datetime(ts.values))
    mask = s < s.shift(1)
    idx = mask[mask].index
    return (
        (
            data.iloc[idx],
            [
                {
                    "type": "monotonic_timestamps",
                    "check": "timestamps_increasing",
                    "count": len(idx),
                    "positions": idx.astype(int).tolist()[:100],
                }
            ],
        )
        if len(idx)
        else (pd.DataFrame(), [])
    )


def validate_duplicates(data: pd.DataFrame):
    """Detect duplicate timestamps."""
    ts = validate_get_time_series(data)
    if ts is None:
        return pd.DataFrame(), []
    dup = ts[ts.duplicated(keep=False)]
    return (
        (
            data.loc[dup.index],
            [
                {
                    "type": "duplicates",
                    "count": len(dup),
                    "timestamps": dup.unique().tolist()[:100],
                }
            ],
        )
        if not dup.empty
        else (pd.DataFrame(), [])
    )


def _expected_delta(data, expected_frequency=None):
    if expected_frequency is not None:
        return (
            pd.Timedelta(expected_frequency.replace("H", "h"))
            if isinstance(expected_frequency, str)
            else pd.Timedelta(expected_frequency)
        )
    ts = validate_get_time_series(data)
    if ts is None:
        return None
    diffs = pd.Series(pd.to_datetime(ts.values)).sort_values().diff().dropna()
    if diffs.empty:
        return None
    mode = diffs.mode()
    return pd.Timedelta(mode.iloc[0] if len(mode) else diffs.median())


def validate_gaps(
    data: pd.DataFrame,
    expected_frequency: str | timedelta | None = None,
    tolerance: float = 1.5,
):
    """Detect timestamp gaps larger than expected frequency times tolerance."""
    ts = validate_get_time_series(data)
    expected = _expected_delta(data, expected_frequency)
    if ts is None or expected is None or expected <= pd.Timedelta(0):
        return pd.DataFrame(), []
    tdf = pd.DataFrame({"Datetime": pd.to_datetime(ts.values)}).sort_values("Datetime")
    tdf["time_diff"] = tdf["Datetime"].diff()
    gaps = tdf[tdf["time_diff"] > expected * tolerance]
    issues = []
    for _, row in gaps.iterrows():
        issues.append(
            {
                "type": "gap",
                "check": "time_gap",
                "count": max(int(row["time_diff"] / expected) - 1, 1),
                "gap_start": row["Datetime"] - row["time_diff"],
                "gap_end": row["Datetime"],
                "expected_diff": expected,
                "actual_diff": row["time_diff"],
            }
        )
    return gaps, issues


def validate_missing_timestamps(
    data: pd.DataFrame, expected_frequency: str | timedelta | None = None
):
    """Detect missing timestamps in a regular time series."""
    ts = validate_get_time_series(data)
    expected = _expected_delta(data, expected_frequency)
    if ts is None or expected is None:
        return pd.DataFrame(), []
    timestamps = pd.DatetimeIndex(pd.to_datetime(ts.values)).sort_values()
    expected_range = pd.date_range(timestamps[0], timestamps[-1], freq=expected)
    missing = sorted(set(expected_range) - set(timestamps))
    return (
        (
            pd.DataFrame({"MissingTimestamp": missing}),
            [
                {
                    "type": "missing_timestamps",
                    "count": len(missing),
                    "expected_total": len(expected_range),
                    "actual_total": len(timestamps),
                    "coverage": len(set(timestamps) & set(expected_range))
                    / max(len(expected_range), 1),
                    "missing_timestamps": missing[:100],
                }
            ],
        )
        if missing
        else (pd.DataFrame(), [])
    )


def validate_zero_volume(data: pd.DataFrame, threshold: float = 0.0):
    """Detect rows where volume is less than or equal to threshold."""
    col = validate_find_column(data, "volume")
    if col is None:
        return pd.DataFrame(), []
    rows = data[pd.to_numeric(data[col], errors="coerce") <= threshold]
    return (
        (
            rows,
            [
                {
                    "type": "zero_volume",
                    "count": len(rows),
                    "rows": rows.index.tolist()[:100],
                    "threshold": threshold,
                }
            ],
        )
        if not rows.empty
        else (pd.DataFrame(), [])
    )


def validate_spread(
    data: pd.DataFrame,
    max_allowed_spread: float | None = None,
    z_score_threshold: float = 4.0,
):
    """Analyze spread statistics and anomalies."""
    df = data.copy()
    col = validate_find_column(df, "spread")
    if col is None:
        bid, ask = validate_find_column(df, "bid"), validate_find_column(df, "ask")
        if not bid or not ask:
            return {}, []
        df["_spread"] = pd.to_numeric(df[ask], errors="coerce") - pd.to_numeric(
            df[bid], errors="coerce"
        )
        col = "_spread"
    spread = pd.to_numeric(df[col], errors="coerce").dropna()
    if spread.empty:
        return {}, []
    stats = {
        "mean": float(spread.mean()),
        "median": float(spread.median()),
        "std": float(spread.std()),
        "min": float(spread.min()),
        "max": float(spread.max()),
        "p95": float(spread.quantile(0.95)),
        "zero_count": int((spread == 0).sum()),
    }
    issues = []
    if (spread < 0).any():
        issues.append(
            {
                "type": "spread_anomaly",
                "issue": "negative_spread",
                "count": int((spread < 0).sum()),
                "rows": spread[spread < 0].index.tolist()[:100],
                "fatal": True,
            }
        )
    if (spread == 0).any():
        issues.append(
            {
                "type": "spread_anomaly",
                "issue": "zero_spread",
                "count": int((spread == 0).sum()),
                "rows": spread[spread == 0].index.tolist()[:100],
            }
        )
    if max_allowed_spread is not None and (spread > max_allowed_spread).any():
        issues.append(
            {
                "type": "spread_anomaly",
                "issue": "max_allowed_spread",
                "count": int((spread > max_allowed_spread).sum()),
                "rows": spread[spread > max_allowed_spread].index.tolist()[:100],
            }
        )
    return stats, issues


def validate_duplicate_ohlc_rows(data):
    """Detect repeated identical OHLC rows."""
    cols = list(validate_find_columns(data, ["Open", "High", "Low", "Close"]).values())
    if len(cols) < 4:
        return pd.DataFrame(), []
    dup = data[data[cols].duplicated(keep=False)]
    return (
        (
            dup,
            [
                {
                    "type": "duplicate_ohlc_rows",
                    "check": "identical_ohlc_values",
                    "count": len(dup),
                    "rows": dup.index.tolist()[:100],
                }
            ],
        )
        if not dup.empty
        else (pd.DataFrame(), [])
    )


def validate_flatlines(data, min_run_length: int = 10):
    """Detect repeated close-price flatlines."""
    col = validate_find_column(data, "close")
    if col is None or len(data) < min_run_length:
        return pd.DataFrame(), []
    close = pd.to_numeric(data[col], errors="coerce")
    run_id = close.ne(close.shift()).cumsum()
    sizes = close.groupby(run_id).transform("size")
    rows = data[close.notna() & (sizes >= min_run_length)]
    return (
        (
            rows,
            [
                {
                    "type": "flatline",
                    "check": "stale_close_run",
                    "count": len(rows),
                    "rows": rows.index.tolist()[:100],
                    "min_run_length": min_run_length,
                }
            ],
        )
        if not rows.empty
        else (pd.DataFrame(), [])
    )


def validate_spikes(data, z_score_threshold: float = 3.0, iqr_multiplier: float = 1.5):
    """Detect return and range anomalies."""
    df = data.copy()
    m = validate_find_columns(df, ["High", "Low", "Close"])
    anomalies = []
    if "Close" not in m:
        return df, []
    close = pd.to_numeric(df[m["Close"]], errors="coerce")
    derived = {"close_return": close.pct_change()}
    if "High" in m and "Low" in m:
        derived["range_pct"] = (
            pd.to_numeric(df[m["High"]], errors="coerce")
            - pd.to_numeric(df[m["Low"]], errors="coerce")
        ) / close.replace(0, np.nan)
    df["is_anomaly"] = False
    for name, series in derived.items():
        clean = series.replace([np.inf, -np.inf], np.nan).dropna()
        std = clean.std()
        if std and not pd.isna(std):
            out = clean[np.abs((clean - clean.mean()) / std) > z_score_threshold]
            if not out.empty:
                anomalies.append(
                    {
                        "type": "spike",
                        "method": "zscore",
                        "check": name,
                        "count": len(out),
                        "rows": out.index.tolist()[:100],
                    }
                )
                df.loc[out.index, "is_anomaly"] = True
    return df, anomalies


def validate_timezone_awareness(data):
    """Check whether data has a timezone-aware DatetimeIndex."""
    return (
        [
            {
                "type": "timezone",
                "check": "timezone_aware_index",
                "count": len(data),
                "message": "DatetimeIndex is timezone-naive.",
            }
        ]
        if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is None
        else []
    )


def _issue_count(issue):
    try:
        return max(int(issue.get("count", 1)), 1)
    except Exception:
        return 1


def validate_issue_severity(issue):
    """Map issue to severity."""
    t = str(issue.get("type", "")).lower()
    i = str(issue.get("issue", "")).lower()
    if issue.get("fatal") or (t == "spread_anomaly" and i == "negative_spread"):
        return "critical"
    if t in {
        "schema_validation",
        "monotonic_timestamps",
        "duplicates",
        "price_sanity",
        "non_numeric",
        "missing_values",
        "infinite_values",
    }:
        return "high"
    if t in {"gap", "missing_timestamps", "zero_volume", "spread_anomaly", "spike"}:
        return "medium"
    return "low"


def validate_issue_remediation_action(issue):
    """Return recommended remediation action."""
    return {
        "schema_validation": "normalize_schema",
        "monotonic_timestamps": "sort_by_timestamp",
        "duplicates": "deduplicate_timestamps",
        "gap": "backfill_or_drop",
        "missing_timestamps": "backfill_or_drop",
        "spike": "review_or_filter",
        "zero_volume": "drop_zero_volume",
        "price_sanity": "drop_invalid_ohlc",
        "non_numeric": "coerce_or_drop_invalid_values",
        "missing_values": "backfill_or_drop",
        "infinite_values": "drop_or_replace_infinite_values",
        "spread_anomaly": "review_spread_source_or_filter",
        "timezone": "localize_or_convert_timezone",
        "duplicate_ohlc_rows": "review_vendor_duplication",
        "flatline": "review_feed_staleness",
    }.get(str(issue.get("type", "")).lower(), "review_manually")


def validate_annotate_issues(issues):
    """Return issues annotated with severity and remediation metadata."""
    out = []
    for issue in issues:
        item = dict(issue)
        item["severity"] = validate_issue_severity(item)
        item["remediation_action"] = validate_issue_remediation_action(item)
        item["remediation_required"] = item["severity"] in {"critical", "high"}
        out.append(item)
    return out


def validate_remediation_summary(issues):
    """Summarize issues by severity."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for issue in issues:
        counts[str(issue.get("severity", "low"))] += 1
    return {
        "severity_counts": counts,
        "needs_immediate_action": counts["critical"] > 0 or counts["high"] > 0,
    }


def _quality_score(issues, total_rows):
    if any(i.get("fatal") for i in issues):
        return 0.0
    weights = {"critical": 100, "high": 60, "medium": 25, "low": 10}
    penalty = sum(
        weights.get(i.get("severity", "low"), 10)
        * min(_issue_count(i) / max(total_rows, 1), 1)
        for i in issues
    )
    return round(max(0, 100 - min(penalty, 100)), 4)


def _decision(summary, issues, profile):
    settings = VALIDATION_PROFILES[profile]
    reasons = []
    score = float(summary["quality_score"])
    coverage = float(summary.get("coverage", {}).get("coverage_ratio", 1.0))
    if not summary["is_valid"]:
        reasons.append("critical_or_high_severity_issue")
    if score < float(settings["min_quality_score"]):
        reasons.append("quality_score_below_profile_threshold")
    if coverage < float(settings["min_coverage_ratio"]):
        reasons.append("coverage_below_profile_threshold")
    if not settings["allow_timezone_naive"] and any(
        i["type"] == "timezone" for i in issues
    ):
        reasons.append("timezone_naive_not_allowed")
    if not settings["allow_zero_spread"] and any(
        i.get("type") == "spread_anomaly" and i.get("issue") == "zero_spread"
        for i in issues
    ):
        reasons.append("zero_spread_not_allowed")
    return {
        "profile": profile,
        "profile_settings": settings,
        "admission": (
            "fail"
            if reasons
            else ("pass_with_warnings" if summary["has_warnings"] else "pass")
        ),
        "recommended_action": "repair_then_use" if reasons else "use",
        "reasons": reasons,
        "metrics": {"quality_score": score, "coverage_ratio": coverage},
    }


def validate_ohlcv_quality(
    data: pd.DataFrame,
    checks: list[str] | None = None,
    *,
    profile: str = "research",
    return_report: bool = False,
    request_id: str | None = None,
    expected_frequency: str | timedelta | None = None,
    minimum_rows: int | None = None,
    max_allowed_spread: float | None = None,
    z_score_threshold: float = 3.0,
    iqr_multiplier: float = 1.5,
):
    """Run comprehensive OHLCVS quality validation."""
    started = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | profile=%s", TOOL_NAME, request_id, profile
    )
    if not isinstance(data, pd.DataFrame):
        return _err(
            "Invalid input.",
            "INVALID_INPUT",
            "data must be a pandas DataFrame.",
            request_id,
            started,
        )
    if data.empty:
        return _err(
            "Invalid input.",
            "INVALID_INPUT",
            "data cannot be empty.",
            request_id,
            started,
        )
    profile = profile.lower().strip() if isinstance(profile, str) else "research"
    if profile not in VALIDATION_PROFILES:
        return _err(
            "Invalid input.",
            "INVALID_INPUT",
            f'profile must be one of: {", ".join(sorted(VALIDATION_PROFILES))}.',
            request_id,
            started,
        )
    checks = checks or [
        "normalized_schema",
        "numeric_integrity",
        "timezone",
        "price_sanity",
        "gaps",
        "missing_timestamps",
        "zero_volume",
        "duplicates",
        "monotonic_timestamps",
        "duplicate_ohlc_rows",
        "flatlines",
        "spikes",
        "spread",
    ]
    checked: list[str] = []
    issues: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    try:
        prepared = prepare_ohlcv_data(data)
        checked.append("normalized_schema")
        summary["normalized_schema"] = {
            "valid": True,
            "rows": len(prepared),
            "columns": list(prepared.columns),
        }
    except Exception as e:
        prepared = data.copy()
        checked.append("normalized_schema")
        issues.append(
            {
                "type": "schema_validation",
                "check": "prepare_ohlcv_data",
                "count": max(len(data), 1),
                "message": str(e),
                "fatal": True,
            }
        )
        summary["normalized_schema"] = {"valid": False, "message": str(e)}
    if not any(i.get("fatal") for i in issues):
        if "numeric_integrity" in checks:
            prepared, found = validate_numeric_integrity(prepared)
            checked.append("numeric_integrity")
            issues += found
        if "timezone" in checks:
            found = validate_timezone_awareness(prepared)
            checked.append("timezone")
            issues += found
        if "price_sanity" in checks:
            ok, _, found = validate_price_sanity(prepared)
            checked.append("price_sanity")
            summary["price_sanity"] = {"all_valid": ok, "issues_count": len(found)}
            issues += found
        if "gaps" in checks:
            _, found = validate_gaps(prepared, expected_frequency=expected_frequency)
            checked.append("gaps")
            issues += found
        if "missing_timestamps" in checks:
            _, found = validate_missing_timestamps(
                prepared, expected_frequency=expected_frequency
            )
            checked.append("missing_timestamps")
            summary["coverage"] = {
                "coverage_ratio": float(found[0]["coverage"]) if found else 1.0
            }
            issues += found
        if "zero_volume" in checks:
            _, found = validate_zero_volume(prepared)
            checked.append("zero_volume")
            issues += found
        if "duplicates" in checks:
            _, found = validate_duplicates(prepared)
            checked.append("duplicates")
            issues += found
        if "monotonic_timestamps" in checks:
            _, found = validate_monotonic_timestamps(prepared)
            checked.append("monotonic_timestamps")
            issues += found
        if "duplicate_ohlc_rows" in checks:
            _, found = validate_duplicate_ohlc_rows(prepared)
            checked.append("duplicate_ohlc_rows")
            issues += found
        if "flatlines" in checks:
            _, found = validate_flatlines(prepared)
            checked.append("flatlines")
            issues += found
        if "spikes" in checks:
            _, found = validate_spikes(
                prepared,
                z_score_threshold=z_score_threshold,
                iqr_multiplier=iqr_multiplier,
            )
            checked.append("spikes")
            issues += found
        if "spread" in checks:
            stats, found = validate_spread(
                prepared, max_allowed_spread=max_allowed_spread
            )
            checked.append("spread")
            summary["spread"] = {"spread_stats": stats, "issues_count": len(found)}
            issues += found
        if minimum_rows is not None and len(prepared) < minimum_rows:
            checked.append("minimum_history")
            issues.append(
                {
                    "type": "minimum_history",
                    "check": "minimum_rows",
                    "count": max(minimum_rows - len(prepared), 1),
                    "required_rows": minimum_rows,
                    "actual_rows": len(prepared),
                }
            )
    annotated = validate_annotate_issues(issues)
    remediation = validate_remediation_summary(annotated)
    quality = _quality_score(annotated, max(len(prepared), 1))
    summary.update(
        {
            "total_issues": len(annotated),
            "quality_score": quality,
            "is_valid": not remediation["needs_immediate_action"],
            "has_warnings": any(i["severity"] in {"medium", "low"} for i in annotated),
            "remediation": remediation,
        }
    )
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(prepared),
        "checks_performed": checked,
        "issues_found": annotated,
        "summary": summary,
        "decision": _decision(summary, annotated, profile),
    }
    if return_report:
        return DataQualityReport(
            datetime.now(timezone.utc),
            len(prepared),
            checked,
            annotated,
            summary,
            quality,
            bool(summary["is_valid"]),
            bool(summary.get("price_sanity", {}).get("all_valid", True)),
            sum(_issue_count(i) for i in annotated if i["type"] == "gap"),
            sum(_issue_count(i) for i in annotated if i["type"] == "spike"),
            sum(
                _issue_count(i) for i in annotated if i["type"] == "missing_timestamps"
            ),
            sum(_issue_count(i) for i in annotated if i["type"] == "zero_volume"),
            sum(_issue_count(i) for i in annotated if i["type"] == "duplicates"),
            cast(
                dict[str, float] | None, summary.get("spread", {}).get("spread_stats")
            ),
            bool(summary["has_warnings"]),
            cast(float | None, summary.get("coverage", {}).get("coverage_ratio")),
        )
    return _ok("OHLCV quality validation completed.", result, request_id, started)


__all__ = [
    "DataQualityReport",
    "DataSource",
    "OHLCVSchema",
    "prepare_ohlcv_data",
    "validate_annotate_issues",
    "validate_duplicate_ohlc_rows",
    "validate_duplicates",
    "validate_find_column",
    "validate_find_columns",
    "validate_flatlines",
    "validate_gaps",
    "validate_get_time_series",
    "validate_issue_remediation_action",
    "validate_issue_severity",
    "validate_missing_timestamps",
    "validate_monotonic_timestamps",
    "validate_numeric_integrity",
    "validate_ohlcv_quality",
    "validate_price_sanity",
    "validate_remediation_summary",
    "validate_spikes",
    "validate_spread",
    "validate_timezone_awareness",
    "validate_zero_volume",
]
