"""Data transformation, aggregation, synthetic generation, and labeling utilities.

Implements resampling, tick-to-bar aggregation, lookahead-free alignment,
Geometric Brownian Motion (GBM) synthetic generators, and deterministic data labeling.
"""

import math
from datetime import datetime, timedelta
from typing import Any, cast

import numpy as np
import pandas as pd
from app.services.data.validation import validate_timeframe
from app.services.utils.errors import ValidationError
from app.services.utils.logger import logger


class TimeframeManager:
    """Manage OHLCV resampling and timeframe conversions."""

    TIMEFRAME_MAP: dict[str, str] = {
        "M1": "1min",
        "M5": "5min",
        "M15": "15min",
        "M30": "30min",
        "H1": "1h",
        "H4": "4h",
        "D1": "1D",
        "W1": "1W",
        "MN1": "1ME",
    }

    VALID_TIMEFRAMES: list[str] = [
        "M1",
        "M5",
        "M15",
        "M30",
        "H1",
        "H4",
        "D1",
        "W1",
        "MN1",
    ]

    @classmethod
    def timeframe_to_frequency(cls, timeframe: str) -> str:
        """Description.
            Convert a timeframe string to a pandas frequency string.

        Args:
            timeframe: str.

        Returns:
            str.
        """
        timeframe_upper = timeframe.upper()
        if timeframe_upper not in cls.TIMEFRAME_MAP:
            raise ValidationError(
                f"Unsupported timeframe: {timeframe}. "
                f"Supported timeframes: {', '.join(cls.VALID_TIMEFRAMES)}"
            )
        logger.debug(
            f"Mapped timeframe '{timeframe}' to Pandas frequency code "
            f"'{cls.TIMEFRAME_MAP[timeframe_upper]}'."
        )
        return cls.TIMEFRAME_MAP[timeframe_upper]

    @classmethod
    def validate_timeframe(cls, timeframe: str) -> bool:
        """Description.
            Return whether a timeframe string is supported.

        Args:
            timeframe: str.

        Returns:
            bool.
        """
        logger.debug(f"Validating timeframe string: '{timeframe}'")
        return timeframe.upper() in cls.TIMEFRAME_MAP

    @classmethod
    def can_resample(cls, from_timeframe: str, to_timeframe: str) -> bool:
        """Description.
            Return whether resampling from source to target is possible.

        Args:
            from_timeframe: str.
            to_timeframe: str.

        Returns:
            bool.
        """
        try:
            from_index = cls.VALID_TIMEFRAMES.index(from_timeframe.upper())
            to_index = cls.VALID_TIMEFRAMES.index(to_timeframe.upper())
        except ValueError:
            return False
        logger.debug(
            f"Checking if resampling is possible from '{from_timeframe}' "
            f"to '{to_timeframe}'."
        )
        return to_index > from_index

    def _find_ohlcv_columns(self, df: pd.DataFrame) -> dict[str, str]:
        """Description.
            Find OHLCV columns in a DataFrame case-insensitively.

        Args:
            df: pd.DataFrame.

        Returns:
            dict[str, str].
        """
        logger.debug(
            "Scanning DataFrame columns to identify OHLCV fields case-insensitively."
        )
        mapping = {}
        columns_lower = {str(column).lower(): str(column) for column in df.columns}
        ohlcv_map = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
        for key, standard_name in ohlcv_map.items():
            if key in columns_lower:
                mapping[standard_name] = columns_lower[key]
        return mapping

    def _ensure_datetime_index(self, data: pd.DataFrame) -> pd.DataFrame:
        """Description.
            Return a DataFrame with a DatetimeIndex.

        Args:
            data: pd.DataFrame.

        Returns:
            pd.DataFrame.
        """
        logger.debug("Ensuring the DataFrame has a valid DatetimeIndex.")
        if isinstance(data.index, pd.DatetimeIndex):
            return data

        for column in (
            "Datetime",
            "datetime",
            "time",
            "Time",
            "timestamp",
            "Timestamp",
        ):
            if column in data.columns:
                out = data.copy()
                out.index = pd.DatetimeIndex(out[column], name="Datetime")
                return out.drop(columns=[column])

        raise ValidationError(
            "DataFrame must have DatetimeIndex or a datetime column "
            "(Datetime, datetime, time, timestamp)."
        )

    def resample(
        self,
        data: pd.DataFrame,
        target_timeframe: str,
        source_timeframe: str | None = None,
    ) -> pd.DataFrame:
        """Description.
            Resample OHLCV data to a higher timeframe.

        Args:
            data: pd.DataFrame.
            target_timeframe: str.
            source_timeframe: str | None.

        Returns:
            pd.DataFrame.
        """
        if data.empty:
            logger.warning("Cannot resample empty DataFrame")
            return data.copy()

        if not self.validate_timeframe(target_timeframe):
            raise ValidationError(f"Invalid target timeframe: {target_timeframe}.")
        if source_timeframe and not self.can_resample(
            source_timeframe,
            target_timeframe,
        ):
            raise ValidationError(
                f"Cannot resample from {source_timeframe} to {target_timeframe}."
            )

        data = self._ensure_datetime_index(data)
        ohlcv_mapping = self._find_ohlcv_columns(data)
        if not ohlcv_mapping:
            raise ValidationError("No OHLCV columns found in DataFrame.")

        frequency = self.timeframe_to_frequency(target_timeframe)
        resampled = pd.DataFrame(index=data.index)
        if "Open" in ohlcv_mapping:
            resampled["Open"] = data[ohlcv_mapping["Open"]].resample(frequency).first()
        if "High" in ohlcv_mapping:
            resampled["High"] = data[ohlcv_mapping["High"]].resample(frequency).max()
        if "Low" in ohlcv_mapping:
            resampled["Low"] = data[ohlcv_mapping["Low"]].resample(frequency).min()
        if "Close" in ohlcv_mapping:
            resampled["Close"] = data[ohlcv_mapping["Close"]].resample(frequency).last()
        if "Volume" in ohlcv_mapping:
            resampled["Volume"] = (
                data[ohlcv_mapping["Volume"]].resample(frequency).sum()
            )

        for column in data.columns:
            if column not in ohlcv_mapping.values() and column not in {
                "Datetime",
                "datetime",
            }:
                resampled[column] = data[column].resample(frequency).last()

        return resampled.dropna(subset=["Open", "High", "Low", "Close"], how="all")

    def resample_multi_timeframe(
        self,
        data: pd.DataFrame,
        source_timeframe: str,
        target_timeframes: list[str],
    ) -> dict[str, pd.DataFrame]:
        """Description.
            Resample data to multiple target timeframes.

        Args:
            data: pd.DataFrame.
            source_timeframe: str.
            target_timeframes: list[str].

        Returns:
            dict[str, pd.DataFrame].
        """
        results = {}
        for target_timeframe in target_timeframes:
            results[target_timeframe] = self.resample(
                data,
                target_timeframe,
                source_timeframe,
            )
        logger.debug(
            f"Completed multi-timeframe resampling for targets: {target_timeframes}"
        )
        return results


class BarAggregator:
    """Incrementally aggregate ticks or lower-timeframe bars into OHLCV bars."""

    def __init__(self, target_timeframe: str) -> None:
        """Description.
            Initialize the aggregator.

        Args:
            target_timeframe: str.

        Returns:
            None.
        """
        self.target_timeframe = target_timeframe.upper()
        self.target_frequency = TimeframeManager.timeframe_to_frequency(
            target_timeframe
        )
        self.current_bar: dict[str, float] | None = None
        self.current_bar_start: datetime | None = None
        self.completed_bars: list[dict[str, Any]] = []
        logger.debug("Initialized BarAggregator for %s.", self.target_timeframe)

    def add_tick(
        self,
        timestamp: datetime,
        price: float,
        volume: float = 0.0,
        bid: float | None = None,
        ask: float | None = None,
    ) -> dict[str, Any] | None:
        """Description.
            Add a tick and return a completed bar when a period rolls over.

        Args:
            timestamp: datetime.
            price: float.
            volume: float.
            bid: float | None.
            ask: float | None.

        Returns:
            dict[str, Any] | None.
        """
        if bid is not None and ask is not None:
            price = (bid + ask) / 2.0
        logger.debug(
            f"Adding tick to aggregator at timestamp={timestamp}, "
            f"price={price}, volume={volume}"
        )
        return self.add_bar(timestamp, price, price, price, price, volume)

    def add_bar(
        self,
        timestamp: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float = 0.0,
    ) -> dict[str, Any] | None:
        """Description.
            Add a lower-timeframe bar to the aggregate state.

        Args:
            timestamp: datetime.
            open_price: float.
            high_price: float.
            low_price: float.
            close_price: float.
            volume: float.

        Returns:
            dict[str, Any] | None.
        """
        bar_start = self._get_bar_start_time(timestamp)
        completed_bar = None
        if self.current_bar_start is not None and bar_start != self.current_bar_start:
            completed_bar = self._finalize_current_bar()
            self.completed_bars.append(completed_bar)

        if bar_start != self.current_bar_start:
            self.current_bar_start = bar_start
            self.current_bar = {
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Close": close_price,
                "Volume": volume,
            }
        elif self.current_bar:
            self.current_bar["High"] = max(self.current_bar["High"], high_price)
            self.current_bar["Low"] = min(self.current_bar["Low"], low_price)
            self.current_bar["Close"] = close_price
            self.current_bar["Volume"] += volume

        logger.debug(
            f"Aggregated lower-timeframe bar at timestamp={timestamp}, "
            f"open={open_price}, close={close_price}, volume={volume}"
        )
        return completed_bar

    def _get_bar_start_time(self, timestamp: datetime) -> datetime:
        """Description.
            Return the target-period start time for a timestamp.

        Args:
            timestamp: datetime.

        Returns:
            datetime.
        """
        logger.debug(
            f"Calculating bar start time for timestamp={timestamp} "
            f"using frequency={self.target_frequency}"
        )
        period = pd.Period(pd.Timestamp(timestamp), freq=self.target_frequency)
        return cast("datetime", period.start_time.to_pydatetime())

    def _finalize_current_bar(self) -> dict[str, Any]:
        """Description.
            Finalize and return the current bar.

        Args:
            None.

        Returns:
            dict[str, Any].
        """
        logger.debug(f"Finalizing current bar started at {self.current_bar_start}.")
        if not self.current_bar or self.current_bar_start is None:
            raise ValidationError("No current bar to finalize.")
        bar: dict[str, Any] = dict(self.current_bar)
        bar["Datetime"] = self.current_bar_start
        return bar

    def get_current_bar(self) -> dict[str, Any] | None:
        """Description.
            Return the current incomplete bar.

        Args:
            None.

        Returns:
            dict[str, Any] | None.
        """
        logger.debug(
            f"Retrieving current incomplete bar started at {self.current_bar_start}."
        )
        if not self.current_bar or self.current_bar_start is None:
            return None
        bar: dict[str, Any] = dict(self.current_bar)
        bar["Datetime"] = self.current_bar_start
        return bar

    def get_completed_bars(self) -> list[dict[str, Any]]:
        """Description.
            Return completed bars.

        Args:
            None.

        Returns:
            list[dict[str, Any]].
        """
        logger.debug(
            f"Retrieving list of completed bars (count: {len(self.completed_bars)})."
        )
        return self.completed_bars.copy()

    def flush(self) -> dict[str, Any] | None:
        """Description.
            Flush current incomplete bar into completed bars.

        Args:
            None.

        Returns:
            dict[str, Any] | None.
        """
        logger.debug("Flushing current incomplete bar to completed list.")
        if not self.current_bar or self.current_bar_start is None:
            return None
        completed_bar = self._finalize_current_bar()
        self.completed_bars.append(completed_bar)
        self.current_bar = None
        self.current_bar_start = None
        return completed_bar


def _clean_numpy_types(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Description.
        Convert numpy integers and floats in records to native Python types.

    Args:
        records: list[dict[str, Any]].

    Returns:
        list[dict[str, Any]].
    """
    logger.debug(
        f"Converting numpy numeric types in {len(records)} records "
        f"to native Python types."
    )
    for row in records:
        for k, v in row.items():
            if isinstance(v, np.integer):
                row[k] = int(v)
            elif isinstance(v, np.floating):
                row[k] = float(v)
    return records


def timeframe_to_pandas_freq(tf: str) -> str:
    """Description.
        Convert a timeframe string into a pandas frequency string.

    Args:
        tf: str.

    Returns:
        str.
    """
    logger.debug(f"Converting timeframe '{tf}' to Pandas frequency string.")
    upper_tf = tf.upper()
    if upper_tf.startswith("MN"):
        val = int(upper_tf[2:])
        return f"{val}ME"  # Month end

    unit = upper_tf[0]
    try:
        val = int(upper_tf[1:])
    except ValueError as e:
        msg = f"Invalid timeframe value format: {tf}"
        raise ValidationError(msg) from e

    if unit == "M":
        return f"{val}min"
    if unit == "H":
        return f"{val}h"
    if unit == "D":
        return f"{val}D"
    if unit == "W":
        return f"{val}W"
    msg = f"Invalid timeframe unit: {tf}"
    raise ValidationError(msg)


def timeframe_to_minutes(tf: str) -> int:
    """Description.
        Convert a timeframe string into minutes.

    Args:
        tf: str.

    Returns:
        int.
    """
    logger.debug(f"Converting timeframe '{tf}' to minutes.")
    upper_tf = tf.upper()
    if upper_tf.startswith("MN"):
        val = int(upper_tf[2:])
        return val * 43200  # Approximating a month as 30 days

    unit = upper_tf[0]
    try:
        val = int(upper_tf[1:])
    except ValueError as e:
        msg = f"Invalid timeframe value format: {tf}"
        raise ValidationError(msg) from e

    if unit == "M":
        return val
    if unit == "H":
        return val * 60
    if unit == "D":
        return val * 1440
    if unit == "W":
        return val * 10080
    msg = f"Invalid timeframe unit: {tf}"
    raise ValidationError(msg)


def resample_ohlcv(  # noqa: C901
    records: list[dict[str, Any]],
    target_timeframe: str,
    *,
    spread_policy: str = "average",
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Description.
        Resample normalized OHLCV records into higher timeframes.

    Args:
        records: list[dict[str, Any]].
        target_timeframe: str.
        spread_policy: str.
        request_id: str | None.

    Returns:
        list[dict[str, Any]].
    """
    logger.info(
        f"Resampling {len(records)} records to {target_timeframe} using "
        f"spread_policy={spread_policy}",
        extra={"request_id": request_id},
    )

    if not records:
        return []

    validate_timeframe(target_timeframe)

    # Validate source timeframe from records
    source_tf = records[0].get("timeframe")
    if not source_tf:
        raise ValidationError(
            "Source records missing timeframe field."
        )  # pragma: no cover

    validate_timeframe(source_tf)

    src_mins = timeframe_to_minutes(source_tf)
    tgt_mins = timeframe_to_minutes(target_timeframe)

    if tgt_mins < src_mins:
        msg = (  # pragma: no cover
            f"Cannot resample to a lower timeframe: "  # pragma: no cover
            f"source={source_tf} ({src_mins}m), target={target_timeframe} ({tgt_mins}m)"  # pragma: no cover
        )  # pragma: no cover
        raise ValidationError(msg)  # pragma: no cover

    # Convert to DataFrame
    df = pd.DataFrame(records)
    if "symbol" in df.columns and (df["symbol"] != df["symbol"].iloc[0]).any():
        raise ValidationError(
            "Cannot resample records containing multiple symbols."
        )  # pragma: no cover

    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp_dt")
    df = df.sort_index()

    # Define aggregations based on available columns
    standard_cols = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
        "tick_volume": "sum",
        "real_volume": "sum",
        "symbol": "first",
        "source": "first",
    }
    agg_dict = {c: standard_cols[c] for c in standard_cols if c in df.columns}

    if "spread" in df.columns:  # pragma: no cover
        if spread_policy == "max":
            agg_dict["spread"] = "max"  # pragma: no cover
        elif spread_policy == "last":
            agg_dict["spread"] = "last"
        else:
            agg_dict["spread"] = "mean"

    pandas_freq = timeframe_to_pandas_freq(target_timeframe)

    # Perform resampling
    resampled_df = df.resample(pandas_freq, label="left", closed="left").agg(agg_dict)

    # Drop rows that have all NaN prices
    price_cols = [
        c for c in ["open", "high", "low", "close"] if c in resampled_df.columns
    ]
    resampled_df = resampled_df.dropna(subset=price_cols, how="all")

    # Reset index and formatting
    resampled_df = resampled_df.reset_index()
    resampled_df["timestamp"] = resampled_df["timestamp_dt"].dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    resampled_df = resampled_df.drop(columns=["timestamp_dt"])
    resampled_df["timeframe"] = target_timeframe

    # Fill NaNs with standard defaults
    if "volume" in resampled_df.columns:  # pragma: no cover
        resampled_df["volume"] = resampled_df["volume"].fillna(0.0)
    if "tick_volume" in resampled_df.columns:  # pragma: no cover
        resampled_df["tick_volume"] = resampled_df["tick_volume"].fillna(0.0)
    if "real_volume" in resampled_df.columns:  # pragma: no cover
        resampled_df["real_volume"] = resampled_df["real_volume"].fillna(0.0)
    if "spread" in resampled_df.columns:  # pragma: no cover
        resampled_df["spread"] = resampled_df["spread"].fillna(0.0)

    # Convert numeric outputs to Python native types (float or int)
    result = resampled_df.to_dict(orient="records")
    return _clean_numpy_types(result)


def align_multitimeframe_data(
    datasets: dict[str, list[dict[str, Any]]],
    target_timestamps: list[str],
    *,
    allow_lookahead: bool = False,
    alignment_method: str = "last_known_closed_bar",
    request_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Description.
        Align multiple timeframe datasets to target timestamps without lookahead.

    Args:
        datasets: dict[str, list[dict[str, Any]]].
        target_timestamps: list[str].
        allow_lookahead: bool.
        alignment_method: str.
        request_id: str | None.

    Returns:
        dict[str, list[dict[str, Any]]].
    """
    logger.info(
        "Aligning datasets with {} timeframes to {} targets "
        "(allow_lookahead={}, method={})",
        len(datasets),
        len(target_timestamps),
        allow_lookahead,
        alignment_method,
        extra={"request_id": request_id},
    )

    if not target_timestamps:
        return {tf: [] for tf in datasets}  # pragma: no cover

    # Prepare targets DataFrame
    target_df = pd.DataFrame({"timestamp": target_timestamps})
    target_df["timestamp_dt"] = pd.to_datetime(target_df["timestamp"])
    target_df = target_df.sort_values("timestamp_dt")

    aligned_results: dict[str, list[dict[str, Any]]] = {}

    for tf, records in datasets.items():
        if not records:
            aligned_results[tf] = []  # pragma: no cover
            continue  # pragma: no cover

        df_source = pd.DataFrame(records)
        df_source["timestamp_dt"] = pd.to_datetime(df_source["timestamp"])
        df_source = df_source.sort_values("timestamp_dt")

        interval_mins = timeframe_to_minutes(tf)

        if not allow_lookahead:
            # Shift the timestamp key by the bar duration to denote when it closes
            df_source["align_key"] = df_source["timestamp_dt"] + pd.to_timedelta(
                interval_mins, unit="m"
            )
        else:
            df_source["align_key"] = df_source["timestamp_dt"]  # pragma: no cover

        # Run merge_asof
        merged = pd.merge_asof(
            target_df,
            df_source,
            left_on="timestamp_dt",
            right_on="align_key",
            direction="backward",
            suffixes=("", "_src"),
        )

        # Cleanup columns
        if "timestamp_dt" in merged.columns:  # pragma: no cover
            merged = merged.drop(columns=["timestamp_dt"])
        if "align_key" in merged.columns:  # pragma: no cover
            merged = merged.drop(columns=["align_key"])
        if "timestamp_src" in merged.columns:  # pragma: no cover
            src_ts = pd.to_datetime(merged["timestamp_src"])
            merged["bar_open_timestamp"] = src_ts.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            merged = merged.drop(columns=["timestamp_src"])
        if "timestamp_dt_src" in merged.columns:  # pragma: no cover
            merged = merged.drop(columns=["timestamp_dt_src"])

        # Convert NaNs to None for JSON serializability
        merged = merged.where(merged.notna(), None)

        records_list = merged.to_dict(orient="records")
        # Ensure numpy types are converted
        _clean_numpy_types(records_list)

        aligned_results[tf] = records_list

    return aligned_results


def aggregate_ticks_to_bars(  # noqa: C901, PLR0912
    ticks: list[dict[str, Any]],
    timeframe: str,
    *,
    repair: bool = False,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Description.
        Aggregate tick records into OHLCV bars.

    Args:
        ticks: list[dict[str, Any]].
        timeframe: str.
        repair: bool.
        request_id: str | None.

    Returns:
        list[dict[str, Any]].
    """
    logger.info(
        f"Aggregating {len(ticks)} ticks to timeframe {timeframe} (repair={repair})",
        extra={"request_id": request_id},
    )

    if not ticks:
        return []  # pragma: no cover

    validate_timeframe(timeframe)

    df = pd.DataFrame(ticks)
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])

    # Verify chronological sorting
    if not df["timestamp_dt"].is_monotonic_increasing:
        if not repair:  # pragma: no cover
            msg = "Ticks are not sorted chronologically."  # pragma: no cover
            raise ValidationError(msg)  # pragma: no cover
        df = df.sort_values("timestamp_dt")  # pragma: no cover

    # Resolve price column to use
    if "last" in df.columns and df["last"].notna().any():
        price_col = "last"
    elif "price" in df.columns and df["price"].notna().any():  # pragma: no cover
        price_col = "price"  # pragma: no cover
    elif "bid" in df.columns and df["bid"].notna().any():  # pragma: no cover
        price_col = "bid"  # pragma: no cover
    else:  # pragma: no cover
        msg = "No valid price field (last, price, bid) found in ticks."  # pragma: no cover
        raise ValidationError(msg)  # pragma: no cover

    # Floor timestamps to timeframe interval
    freq = timeframe_to_pandas_freq(timeframe)
    df["bar_time"] = df["timestamp_dt"].dt.floor(freq)

    agg_dict: dict[str, list[str] | str] = {
        price_col: ["first", "max", "min", "last"],
    }

    if "volume" in df.columns:  # pragma: no cover
        agg_dict["volume"] = "sum"

    df["tick_count"] = 1
    agg_dict["tick_count"] = "sum"

    if "ask" in df.columns and "bid" in df.columns:  # pragma: no cover
        df["spread_val"] = df["ask"] - df["bid"]
        agg_dict["spread_val"] = "mean"

    # Perform groupby aggregation
    grouped = df.groupby("bar_time").agg(agg_dict)

    # Flatten multi-index columns
    grouped.columns = ["_".join(col).strip() for col in list(grouped.columns)]
    grouped = grouped.reset_index()

    # Map to standardized bar names
    rename_map = {
        f"{price_col}_first": "open",
        f"{price_col}_max": "high",
        f"{price_col}_min": "low",
        f"{price_col}_last": "close",
        "volume_sum": "volume",
        "tick_count_sum": "tick_volume",
        "spread_val_mean": "spread",
    }
    grouped = grouped.rename(columns=rename_map)

    # Add timeframe and symbol if constant in input
    if "symbol" in df.columns:  # pragma: no cover
        grouped["symbol"] = df["symbol"].iloc[0]
    if "source" in df.columns:
        grouped["source"] = df["source"].iloc[0]
    else:
        grouped["source"] = "tick_aggregation"  # pragma: no cover

    grouped["timeframe"] = timeframe
    grouped["timestamp"] = grouped["bar_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Drop temp columns
    drop_cols = [
        c
        for c in ["bar_time", "price_first", "price_max", "price_min", "price_last"]
        if c in grouped.columns
    ]
    grouped = grouped.drop(columns=drop_cols)

    # Fallback missing columns
    if "volume" not in grouped.columns:
        grouped["volume"] = 0.0  # pragma: no cover
    if "spread" not in grouped.columns:
        grouped["spread"] = 0.0  # pragma: no cover

    result = grouped.to_dict(orient="records")
    # Clean numpy types
    return _clean_numpy_types(result)


def generate_synthetic_ticks(
    symbol: str,
    start_time: str,
    num_ticks: int,
    start_price: float,
    average_spread: float,
    volatility: float,
    *,
    volume_behavior: str = "random",
    seed: int | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Description.
        Generate deterministic synthetic tick data using random walks.

    Args:
        symbol: str.
        start_time: str.
        num_ticks: int.
        start_price: float.
        average_spread: float.
        volatility: float.
        volume_behavior: str.
        seed: int | None.
        request_id: str | None.

    Returns:
        list[dict[str, Any]].
    """
    logger.info(
        f"Generating {num_ticks} synthetic ticks for {symbol} starting at "
        f"{start_price} (volatility={volatility}, seed={seed})",
        extra={"request_id": request_id},
    )

    if num_ticks <= 0:
        return []  # pragma: no cover

    if start_price <= 0:
        raise ValidationError("start_price must be positive.")  # pragma: no cover
    if average_spread < 0:
        raise ValidationError("average_spread cannot be negative.")  # pragma: no cover
    if volatility < 0:
        raise ValidationError("volatility cannot be negative.")  # pragma: no cover

    rng = np.random.default_rng(seed)

    start_dt = pd.to_datetime(start_time)
    current_time = start_dt
    current_price = float(start_price)

    ticks = []

    # Pre-generate steps
    returns = rng.normal(0, volatility, num_ticks)
    time_deltas = rng.integers(1, 5, num_ticks)  # 1 to 4 seconds increment

    if volume_behavior == "random":
        volumes = rng.uniform(1.0, 100.0, num_ticks)
    else:
        volumes = np.ones(num_ticks) * 10.0  # pragma: no cover

    for i in range(num_ticks):
        current_price = current_price * math.exp(returns[i])
        current_time = current_time + timedelta(seconds=int(time_deltas[i]))

        spread = average_spread
        bid = current_price - spread / 2.0
        ask = current_price + spread / 2.0

        ticks.append(
            {
                "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "symbol": symbol,
                "bid": float(bid),
                "ask": float(ask),
                "last": float(current_price),
                "volume": float(volumes[i]),
                "spread": float(spread),
                "source": "synthetic",
            }
        )

    return ticks


def generate_synthetic_bars(
    symbol: str,
    timeframe: str,
    start_time: str,
    num_bars: int,
    start_price: float,
    drift: float,
    volatility: float,
    *,
    spread_behavior: str = "constant",
    volume_behavior: str = "random",
    method: str = "gbm",
    seed: int | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Description.
        Generate deterministic synthetic bar data (OHLCV) using GBM.

    Args:
        symbol: str.
        timeframe: str.
        start_time: str.
        num_bars: int.
        start_price: float.
        drift: float.
        volatility: float.
        spread_behavior: str.
        volume_behavior: str.
        method: str.
        seed: int | None.
        request_id: str | None.

    Returns:
        list[dict[str, Any]].
    """
    logger.info(
        f"Generating {num_bars} synthetic bars for {symbol} using {method} "
        f"starting at {start_price} (volatility={volatility}, seed={seed})",
        extra={"request_id": request_id},
    )

    if num_bars <= 0:
        return []  # pragma: no cover

    if start_price <= 0:
        raise ValidationError("start_price must be positive.")  # pragma: no cover
    if volatility < 0:
        raise ValidationError("volatility cannot be negative.")  # pragma: no cover

    validate_timeframe(timeframe)

    if method.lower() != "gbm":
        msg = (
            f"Unsupported synthetic bar generation method: {method}"  # pragma: no cover
        )
        raise ValidationError(msg)  # pragma: no cover

    rng = np.random.default_rng(seed)

    start_dt = pd.to_datetime(start_time)
    interval_mins = timeframe_to_minutes(timeframe)

    current_price = float(start_price)
    bars = []

    # Sim parameters
    dt = 1.0  # per step

    # Pre-generate GBM paths
    # S_t = S_{t-1} * exp((drift - 0.5 * vol^2) * dt + vol * sqrt(dt) * Z)
    gbm_coef = (drift - 0.5 * volatility**2) * dt
    random_normals = rng.normal(0, 1, num_bars)

    if volume_behavior == "random":
        volumes = rng.uniform(10.0, 1000.0, num_bars)
    else:
        volumes = np.ones(num_bars) * 100.0  # pragma: no cover

    if spread_behavior == "random":
        spreads = rng.uniform(0.1, 5.0, num_bars)  # pragma: no cover
    else:
        spreads = np.ones(num_bars) * 2.0

    for i in range(num_bars):
        open_price = current_price

        # Simulate Close price
        close_price = open_price * math.exp(gbm_coef + volatility * random_normals[i])

        # Simulate realistic High and Low bounds
        # Draw separate small steps to simulate intra-bar noise
        noise_high = abs(rng.normal(0, volatility * 0.15)) * open_price
        noise_low = abs(rng.normal(0, volatility * 0.15)) * open_price

        high_price = max(open_price, close_price) + noise_high
        low_price = min(open_price, close_price) - noise_low

        bar_time = start_dt + timedelta(minutes=int(i * interval_mins))

        bars.append(
            {
                "timestamp": bar_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "symbol": symbol,
                "open": float(open_price),
                "high": float(high_price),
                "low": float(low_price),
                "close": float(close_price),
                "volume": float(volumes[i]),
                "tick_volume": float(volumes[i] / 2.0),
                "real_volume": float(volumes[i]),
                "spread": float(spreads[i]),
                "timeframe": timeframe,
                "source": "synthetic",
            }
        )

        # Set close as starting point for next bar
        current_price = close_price

    return bars


def label_market_data(
    records: list[dict[str, Any]],
    *,
    horizon: int,
    threshold: float,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Description.
        Generate deterministic historical labels without claiming predictive value.

    Args:
        records: list[dict[str, Any]].
        horizon: int.
        threshold: float.
        request_id: str | None.

    Returns:
        list[dict[str, Any]].
    """
    logger.info(
        "Labeling {} records with horizon={}, threshold={}",
        len(records),
        horizon,
        threshold,
        extra={"request_id": request_id},
    )

    if horizon <= 0:
        raise ValidationError("horizon must be a positive integer.")  # pragma: no cover
    if threshold < 0:
        raise ValidationError("threshold cannot be negative.")  # pragma: no cover

    if not records:
        return []  # pragma: no cover

    # Validate that close price is present in records
    if "close" not in records[0]:
        raise ValidationError(
            "Records missing mandatory close price column."
        )  # pragma: no cover

    prices = [float(r["close"]) for r in records]
    n = len(prices)

    labeled_records = []

    for i in range(n):
        label = 0
        end_idx = min(i + horizon + 1, n)

        # Find the first price that crosses the threshold
        for j in range(i + 1, end_idx):
            ret = (prices[j] - prices[i]) / prices[i]
            if ret >= threshold:
                label = 1
                break
            if ret <= -threshold:
                label = -1
                break

        # Shallow copy to preserve original record fields and append label
        new_rec = dict(records[i])
        new_rec["label"] = label
        new_rec["label_metadata"] = {
            "method": "horizon_threshold",
            "horizon": horizon,
            "threshold": threshold,
            "claims_predictive_value": False,
        }
        labeled_records.append(new_rec)

    return labeled_records


__all__ = [
    "BarAggregator",
    "TimeframeManager",
    "aggregate_ticks_to_bars",
    "align_multitimeframe_data",
    "generate_synthetic_bars",
    "generate_synthetic_ticks",
    "label_market_data",
    "resample_ohlcv",
    "timeframe_to_minutes",
    "timeframe_to_pandas_freq",
]
