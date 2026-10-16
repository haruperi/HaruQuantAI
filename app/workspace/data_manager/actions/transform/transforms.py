"""Time-series transforms: resampling, timezone cloning, and session filtering.

Description:
    Provides time-series transformations for historical datasets including
    timeframe resampling (M1 to M5, M15, M30, H1, H4, D1, W1, MN1) with canonical
    OHLCV aggregation, timezone shifting and IANA conversion, weekend bar
    filtering, and trading session calendar schedule alignment without importing
    `sqlite3`.

Purpose:
    FEAT-DATAMGR-TRANSFORMS: Timeframe resampling, timezone cloning, and
    session filtering.

Key Capabilities:
    - FR-DATAMGR-TRANSFORMS-RESAMPLE: Resample lower-timeframe bars to
      higher timeframes.
      Associated: `SeriesTransformer.resample_dataframe()`,
      `SeriesTransformer.resample_dataset()`
      Logging: Emits INFO on dataset resampling with source and target
      timeframes.
    - FR-DATAMGR-TRANSFORMS-TIMEZONE-CLONE: Clone datasets with hour shifting
      and weekend filtering.
      Associated: `SeriesTransformer.clone_timezone()`
      Logging: Emits INFO on timezone cloning with shift hours and bar counts.
    - FR-DATAMGR-TRANSFORMS-SESSION-ALIGNMENT: Filter series to trading session
      windows.
      Associated: `SeriesTransformer.apply_session_filter()`
      Logging: Emits DEBUG when evaluating bars against session calendars.

Python API Usage:
    ```python
    from app.workspace.data_manager.actions.transform.transforms import (
        ResampleConfig,
        SeriesTransformer,
    )

    transformer = SeriesTransformer(data_service=service)
    res = transformer.resample_dataset(
        ResampleConfig(dataset_id="file:EURUSD", target_timeframe="H1")
    )
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.actions.transform.transforms
    ```
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.host.persistence.create import create_schema
from app.host.persistence.read import resolve_connection
from app.services.include.contracts import DataInfo
from app.workspace.data_manager.data import DataManagerDataService
from app.workspace.data_manager.log import DataManagerLogService
from app.workspace.data_manager.sessions import TradingSession

__all__ = [
    "CloneTimezoneConfig",
    "ResampleConfig",
    "SeriesTransformer",
]

logger = get_logger(__name__)

RESAMPLE_FR = "FR-DATAMGR-TRANSFORMS-RESAMPLE"
TIMEZONE_CLONE_FR = "FR-DATAMGR-TRANSFORMS-TIMEZONE-CLONE"
SESSION_ALIGN_FR = "FR-DATAMGR-TRANSFORMS-SESSION-ALIGNMENT"

SECONDS_PER_MINUTE = 60.0
SECONDS_PER_HOUR = 3600.0
SECONDS_PER_DAY = 86400.0
SECONDS_PER_WEEK = 604800.0
WEEKEND_SATURDAY = 5
WEEKEND_SUNDAY = 6
WEEKEND_DAYS = [WEEKEND_SATURDAY, WEEKEND_SUNDAY]
ISO_MIN_STR_LENGTH = 10

_TIMEFRAME_TO_FREQ: dict[str, str] = {
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


def _timeframe_to_seconds(tf: str) -> float:
    """Convert timeframe code to duration in seconds."""
    clean = tf.strip().upper()
    if not clean or clean == "TICK":
        return 0.0
    unit = clean[0]
    val_str = clean[1:]
    try:
        val = int(val_str) if val_str else 1
    except ValueError:
        val = 1
    multiplier = SECONDS_PER_MINUTE
    if unit == "S":
        multiplier = 1.0
    elif unit == "M":
        multiplier = SECONDS_PER_MINUTE
    elif unit == "H":
        multiplier = SECONDS_PER_HOUR
    elif unit == "D":
        multiplier = SECONDS_PER_DAY
    elif unit == "W":
        multiplier = SECONDS_PER_WEEK
    return float(val) * multiplier


@dataclass(frozen=True)
class CloneTimezoneConfig:
    """Configuration for timezone cloning and weekend removal."""

    dataset_id: str
    timezone_type: str = "shift"
    shift_hours: int = 0
    timezone: str = "UTC"
    remove_weekends: bool = False
    postfix: str = "_clone"


@dataclass(frozen=True)
class ResampleConfig:
    """Configuration for timeframe resampling."""

    dataset_id: str
    target_timeframe: str
    new_symbol: str | None = None


class SeriesTransformer:
    """Engine executing timeframe resampling and timezone cloning."""

    def __init__(
        self,
        data_service: DataManagerDataService,
        log_service: DataManagerLogService | None = None,
    ) -> None:
        """Initialize series transformer with data service and optional logger."""
        self.data_service = data_service
        self.log_service = log_service

    def resample_dataframe(
        self, df: pd.DataFrame, target_timeframe: str
    ) -> pd.DataFrame:
        """Resample OHLCV bars DataFrame into higher timeframe series."""
        clean_tf = target_timeframe.strip().upper()
        freq = _TIMEFRAME_TO_FREQ.get(clean_tf)
        if freq is None:
            raise ValueError(f"Unsupported target timeframe: '{target_timeframe}'")

        if df.empty:
            return df.copy()

        work_df = df.copy()
        work_df["dt"] = pd.to_datetime(work_df["timestamp"], utc=True)
        work_df = work_df.set_index("dt").sort_index()

        is_tick = (
            "bid" in work_df.columns
            and "ask" in work_df.columns
            and "open" not in work_df.columns
        )
        if is_tick:
            work_df["price"] = (work_df["bid"] + work_df["ask"]) / 2.0
            resampler = work_df.resample(freq, label="left", closed="left")
            volume_series = (
                resampler["volume"].sum()
                if "volume" in work_df.columns
                else resampler["price"].count().astype(float)
            )
            spread_series = (resampler["ask"].last() - resampler["bid"].last()).fillna(
                0.0
            )
            resampled_df = pd.DataFrame(
                {
                    "open": resampler["price"].first(),
                    "high": resampler["price"].max(),
                    "low": resampler["price"].min(),
                    "close": resampler["price"].last(),
                    "volume": volume_series,
                    "spread": spread_series,
                }
            ).dropna(subset=["open", "high", "low", "close"])
        else:
            resampler = work_df.resample(freq, label="left", closed="left")
            resampled_df = pd.DataFrame(
                {
                    "open": resampler["open"].first(),
                    "high": resampler["high"].max(),
                    "low": resampler["low"].min(),
                    "close": resampler["close"].last(),
                    "volume": resampler["volume"].sum()
                    if "volume" in work_df.columns
                    else 0.0,
                    "spread": resampler["spread"].max()
                    if "spread" in work_df.columns
                    else 0.0,
                }
            ).dropna(subset=["open", "high", "low", "close"])

        resampled_df = resampled_df.reset_index()
        resampled_df["timestamp"] = resampled_df["dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
        resampled_df = resampled_df.drop(columns=["dt"])
        logger.debug(
            "%s: Resampled %d bars to %d bars (%s)",
            RESAMPLE_FR,
            len(df),
            len(resampled_df),
            clean_tf,
            extra={
                "fr_id": RESAMPLE_FR,
                "input_bars": len(df),
                "output_bars": len(resampled_df),
                "target_timeframe": clean_tf,
            },
        )
        return resampled_df

    def resample_dataset(self, config: ResampleConfig) -> DataInfo:
        """Resample a registered historical dataset and persist new dataset record."""
        source_rec = self.data_service.get_dataset(config.dataset_id)
        if source_rec is None:
            raise KeyError(f"Source dataset '{config.dataset_id}' not found.")

        target_tf = config.target_timeframe.strip().upper()
        target_sec = _timeframe_to_seconds(target_tf)
        source_sec = _timeframe_to_seconds(source_rec.timeframe)
        if target_sec < source_sec:
            msg = (
                f"Cannot downsample higher timeframe '{source_rec.timeframe}' "
                f"to lower timeframe '{target_tf}'. Target timeframe must be coarser "
                f"than or equal to source timeframe."
            )
            raise ValueError(msg)

        symbol = (config.new_symbol or source_rec.symbol).strip().upper()
        target_id = f"{source_rec.source}:{symbol}_{target_tf}"

        df = self.data_service.read_bars_dataframe(str(source_rec.id))
        resampled_df = self.resample_dataframe(df, target_tf)

        new_rec = self.data_service.upsert_dataset(
            {
                "id": target_id,
                "source": source_rec.source,
                "symbol": symbol,
                "underlying": source_rec.underlying,
                "instrument": source_rec.instrument,
                "timeframe": target_tf,
                "category": source_rec.category,
                "timezone": source_rec.timezone,
                "broker": source_rec.broker,
            },
            bars_df=resampled_df,
        )

        if self.log_service:
            res_msg = (
                f"Resampled {source_rec.id} ({source_rec.timeframe}) -> "
                f"{new_rec.id} ({target_tf})"
            )
            self.log_service.append_log(
                action="RESAMPLE",
                message=res_msg,
                symbol=symbol,
                details={"source": source_rec.id, "target": new_rec.id},
            )
            self.log_service.record_operation(
                symbol=symbol,
                operation="RESAMPLE",
                status="SUCCESS",
                message=f"Resampled to {target_tf}",
                rows_affected=new_rec.bars,
            )

        logger.info(
            "%s: Resampled dataset %s -> %s (%d bars)",
            RESAMPLE_FR,
            source_rec.id,
            new_rec.id,
            new_rec.bars,
            extra={
                "fr_id": RESAMPLE_FR,
                "source_id": source_rec.id,
                "target_id": new_rec.id,
                "bars": new_rec.bars,
            },
        )
        return new_rec

    def clone_timezone(self, config: CloneTimezoneConfig) -> DataInfo:
        """Clone dataset series with hour offset and optional weekend bar stripping."""
        source_rec = self.data_service.get_dataset(config.dataset_id)
        if source_rec is None:
            raise KeyError(f"Source dataset '{config.dataset_id}' not found.")

        target_id = f"{source_rec.id}{config.postfix}"
        df = self.data_service.read_bars_dataframe(str(source_rec.id))
        if df.empty:
            raise ValueError(f"Source dataset '{source_rec.id}' contains no bars.")

        cloned_df = df.copy()
        dt_series = pd.to_datetime(cloned_df["timestamp"], utc=True)

        if config.timezone_type in ("convert", "iana"):
            try:
                target_tz_obj = ZoneInfo(config.timezone)
                dt_series = dt_series.dt.tz_convert(target_tz_obj)
            except (ZoneInfoNotFoundError, ValueError) as exc:
                logger.warning(
                    "%s: Invalid timezone %s: %s",
                    TIMEZONE_CLONE_FR,
                    config.timezone,
                    exc,
                )
                raise ValueError(
                    f"Unknown or invalid timezone '{config.timezone}'"
                ) from exc
        elif config.shift_hours != 0:
            dt_series = dt_series + pd.Timedelta(hours=config.shift_hours)

        cloned_df["dt"] = dt_series

        # Strip weekend bars if requested
        if config.remove_weekends:
            cloned_df = cloned_df[~cloned_df["dt"].dt.weekday.isin(WEEKEND_DAYS)].copy()

        cloned_df["timestamp"] = cloned_df["dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
        cloned_df = cloned_df.drop(columns=["dt"]).reset_index(drop=True)

        target_tz = (
            config.timezone
            if config.timezone_type == "convert"
            else f"UTC{config.shift_hours:+d}"
        )
        new_rec = self.data_service.upsert_dataset(
            {
                "id": target_id,
                "source": source_rec.source,
                "symbol": f"{source_rec.symbol}{config.postfix}",
                "underlying": source_rec.underlying,
                "instrument": source_rec.instrument,
                "timeframe": source_rec.timeframe,
                "category": source_rec.category,
                "timezone": target_tz,
                "broker": source_rec.broker,
            },
            bars_df=cloned_df,
        )

        if self.log_service:
            clone_msg = (
                f"Cloned timezone for {source_rec.id} -> {new_rec.id} "
                f"(shift={config.shift_hours}h)"
            )
            self.log_service.append_log(
                action="CLONE",
                message=clone_msg,
                symbol=new_rec.symbol,
            )

        logger.info(
            "%s: Cloned timezone for %s -> %s (shift=%dh, bars=%d)",
            TIMEZONE_CLONE_FR,
            source_rec.id,
            new_rec.id,
            config.shift_hours,
            new_rec.bars,
            extra={
                "fr_id": TIMEZONE_CLONE_FR,
                "source_id": source_rec.id,
                "target_id": new_rec.id,
                "shift_hours": config.shift_hours,
            },
        )
        return new_rec

    def apply_session_filter(
        self, df: pd.DataFrame, session: TradingSession
    ) -> pd.DataFrame:
        """Filter OHLCV bars against a TradingSession schedule."""
        if df.empty:
            return df.copy()

        keep_indices: list[int] = []
        for idx, ts in enumerate(df["timestamp"]):
            try:
                dt_val = (
                    datetime.fromisoformat(str(ts))
                    if "T" in str(ts) or len(str(ts)) > ISO_MIN_STR_LENGTH
                    else datetime.strptime(
                        str(ts)[:ISO_MIN_STR_LENGTH], "%Y-%m-%d"
                    ).replace(tzinfo=UTC)
                )
                if session.is_within_session(dt_val):
                    keep_indices.append(idx)
            except ValueError, TypeError:
                keep_indices.append(idx)

        filtered_df = df.iloc[keep_indices].reset_index(drop=True)
        logger.debug(
            "%s: Filtered %d bars to %d bars using session %s",
            SESSION_ALIGN_FR,
            len(df),
            len(filtered_df),
            session.name,
            extra={
                "fr_id": SESSION_ALIGN_FR,
                "input_bars": len(df),
                "output_bars": len(filtered_df),
                "session": session.name,
            },
        )
        return filtered_df


def main() -> None:
    """Execute real-usage demonstration of SeriesTransformer."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_transform.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        data_svc = DataManagerDataService(db_path=db_file, data_dir=temp_path / "data")
        transformer = SeriesTransformer(data_service=data_svc)

        sample_csv = "timestamp,open,high,low,close,volume,spread\n" + "\n".join(
            f"2026-01-01 {i // 60:02d}:{i % 60:02d}:00,"
            "1.1000,1.1005,1.0995,1.1002,150,1"
            for i in range(100)
        )
        source_rec = data_svc.import_dataset(
            {
                "symbol": "EURUSD",
                "timeframe": "M1",
                "source": "file",
                "csv_content": sample_csv,
            }
        )
        print(f"Loaded source dataset: {source_rec.id} ({source_rec.bars} bars)")

        resampled = transformer.resample_dataset(
            ResampleConfig(dataset_id=str(source_rec.id), target_timeframe="M5")
        )
        print(f"Resampled dataset: {resampled.id} ({resampled.bars} bars)")

        cloned = transformer.clone_timezone(
            CloneTimezoneConfig(
                dataset_id=str(source_rec.id),
                shift_hours=2,
                remove_weekends=True,
                postfix="_EET",
            )
        )
        print(
            f"Cloned timezone dataset: {cloned.id} "
            f"(tz={cloned.timezone}, bars={cloned.bars})"
        )


if __name__ == "__main__":
    main()
