"""Market data series resampling, timezone transformation, and multi-format export.

Description:
    Transformation and export engine for market data series. Provides timeframe
    resampling (M1 to M5, M15, M30, H1, H4, D1) with accurate OHLCV aggregation
    and bucket boundary alignment. Supports timezone shifting to broker server
    timezones, trading session filtering (excluding weekends and holidays), and
    multi-format export to standard CSV, MetaTrader 4 (MT4), and MetaTrader 5 (MT5).

Purpose:
    FEAT-DATA-QUALITY: Resample, transform, filter, and export market data series.

Key Capabilities:
    FR-DATA-QUALITY-TRANSFORMS: Timeframe resampling and timezone shifting.
    FR-DATA-QUALITY-EXPORT: Export datasets to CSV, MT4, and MT5 formats.

Python API Usage:
    ```python
    from app.plugins.data.ingestion import BarRecord
    from app.plugins.data.transforms import SeriesTransformer

    transformer = SeriesTransformer()
    m5_bars = transformer.resample(m1_bars, target_timeframe="M5")
    shifted = transformer.shift_timezone(m5_bars, target_timezone="Europe/Athens")
    out_file = transformer.export_mt4(shifted, "output/EURUSD_M5_MT4.csv")
    ```

CLI Usage:
    ```bash
    python -m app.plugins.data.transforms --file m1.csv --resample M5
    ```
"""

from __future__ import annotations

import argparse
import csv
import sys
import zoneinfo
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from app.host.logging import get_logger
from app.plugins.data.ingestion import BarRecord
from app.plugins.data.sessions import TradingSessionDefinition

logger = get_logger(__name__)

MINUTES_IN_HOUR = 60
MINUTES_IN_DAY = 1440

TIMEFRAME_MINUTES: dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


class SeriesTransformer:
    """Transforms, resamples, filters, and exports market data bar series."""

    def resample(
        self,
        bars: list[BarRecord],
        target_timeframe: str,
    ) -> list[BarRecord]:
        """Resample a series of lower-timeframe bars (e.g. M1) into target timeframe.

        Fires FR-DATA-QUALITY-TRANSFORMS.
        """
        tf_upper = target_timeframe.strip().upper()
        if tf_upper not in TIMEFRAME_MINUTES:
            raise ValueError(
                f"Unsupported target timeframe '{target_timeframe}'. "
                f"Supported: {list(TIMEFRAME_MINUTES.keys())}"
            )

        step_minutes = TIMEFRAME_MINUTES[tf_upper]
        if step_minutes == 1:
            return list(bars)

        if not bars:
            return []

        buckets: dict[datetime, list[BarRecord]] = defaultdict(list)
        for bar in bars:
            dt = datetime.fromisoformat(bar.timestamp_utc)
            bucket_dt = self._calculate_bucket_start(dt, step_minutes)
            buckets[bucket_dt].append(bar)

        resampled_bars: list[BarRecord] = []
        for bucket_dt in sorted(buckets.keys()):
            bucket_bars = buckets[bucket_dt]
            first = bucket_bars[0]
            last = bucket_bars[-1]
            open_p = first.open
            high_p = max(b.high for b in bucket_bars)
            low_p = min(b.low for b in bucket_bars)
            close_p = last.close
            total_vol = sum(b.volume for b in bucket_bars)
            last_oi = last.open_interest

            resampled_bars.append(
                BarRecord(
                    timestamp_utc=bucket_dt.isoformat(),
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=round(total_vol, 2),
                    open_interest=last_oi,
                )
            )

        logger.info(
            "FR-DATA-QUALITY-TRANSFORMS: Resampled %d bars to %s (%d output bars)",
            len(bars),
            tf_upper,
            len(resampled_bars),
            extra={
                "input_bars": len(bars),
                "target_timeframe": tf_upper,
                "output_bars": len(resampled_bars),
                "fr_id": "FR-DATA-QUALITY-TRANSFORMS",
            },
        )
        return resampled_bars

    def shift_timezone(
        self,
        bars: list[BarRecord],
        target_timezone: str,
    ) -> list[BarRecord]:
        """Convert bar timestamps from UTC into target IANA timezone.

        Fires FR-DATA-QUALITY-TRANSFORMS.
        """
        tz = zoneinfo.ZoneInfo(target_timezone)
        shifted: list[BarRecord] = []
        for bar in bars:
            dt_utc = datetime.fromisoformat(bar.timestamp_utc)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=UTC)
            dt_local = dt_utc.astimezone(tz)
            shifted.append(
                bar.model_copy(update={"timestamp_utc": dt_local.isoformat()})
            )

        logger.info(
            "FR-DATA-QUALITY-TRANSFORMS: Shifted %d bars to timezone '%s'",
            len(bars),
            target_timezone,
            extra={
                "bar_count": len(bars),
                "target_timezone": target_timezone,
                "fr_id": "FR-DATA-QUALITY-TRANSFORMS",
            },
        )
        return shifted

    def filter_by_session(
        self,
        bars: list[BarRecord],
        session: TradingSessionDefinition,
    ) -> list[BarRecord]:
        """Filter out bars that fall outside active trading session or on holidays.

        Fires FR-DATA-QUALITY-TRANSFORMS.
        """
        filtered: list[BarRecord] = []
        tz = zoneinfo.ZoneInfo(session.timezone)
        holiday_dates = {h.date_str for h in session.holidays}

        for bar in bars:
            dt = datetime.fromisoformat(bar.timestamp_utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            local_dt = dt.astimezone(tz)
            date_str = local_dt.date().isoformat()
            if date_str in holiday_dates:
                continue

            day_of_week = local_dt.weekday()
            cur_time = local_dt.time()
            in_window = False
            for w in session.windows:
                if w.day_of_week == day_of_week:
                    start_t = w.parse_start_time()
                    end_t = w.parse_end_time()
                    if start_t <= end_t:
                        if start_t <= cur_time <= end_t:
                            in_window = True
                            break
                    elif cur_time >= start_t or cur_time <= end_t:
                        in_window = True
                        break
            if in_window or not session.windows:
                filtered.append(bar)

        logger.info(
            "FR-DATA-QUALITY-TRANSFORMS: Session filtering kept %d of %d bars",
            len(filtered),
            len(bars),
            extra={
                "kept_bars": len(filtered),
                "total_bars": len(bars),
                "session": session.name,
                "fr_id": "FR-DATA-QUALITY-TRANSFORMS",
            },
        )
        return filtered

    def export_csv(
        self,
        bars: list[BarRecord],
        output_path: Path | str,
        include_header: bool = True,
    ) -> Path:
        """Export bars to standard CSV format.

        Fires FR-DATA-QUALITY-EXPORT.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if include_header:
                writer.writerow(
                    ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]
                )
            for bar in bars:
                dt = datetime.fromisoformat(bar.timestamp_utc)
                date_part = dt.strftime("%Y.%m.%d")
                time_part = dt.strftime("%H:%M:%S")
                writer.writerow(
                    [
                        date_part,
                        time_part,
                        f"{bar.open:.5f}",
                        f"{bar.high:.5f}",
                        f"{bar.low:.5f}",
                        f"{bar.close:.5f}",
                        f"{bar.volume:.0f}",
                    ]
                )

        logger.info(
            "FR-DATA-QUALITY-EXPORT: Exported %d bars to CSV: %s",
            len(bars),
            out,
            extra={
                "bar_count": len(bars),
                "format": "CSV",
                "path": str(out),
                "fr_id": "FR-DATA-QUALITY-EXPORT",
            },
        )
        return out

    def export_mt4(
        self,
        bars: list[BarRecord],
        output_path: Path | str,
    ) -> Path:
        """Export bars to MetaTrader 4 HST/CSV format (YYYY.MM.DD,HH:MM,O,H,L,C,V).

        Fires FR-DATA-QUALITY-EXPORT.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for bar in bars:
                dt = datetime.fromisoformat(bar.timestamp_utc)
                date_part = dt.strftime("%Y.%m.%d")
                time_part = dt.strftime("%H:%M")
                writer.writerow(
                    [
                        date_part,
                        time_part,
                        f"{bar.open:.5f}",
                        f"{bar.high:.5f}",
                        f"{bar.low:.5f}",
                        f"{bar.close:.5f}",
                        f"{int(bar.volume)}",
                    ]
                )

        logger.info(
            "FR-DATA-QUALITY-EXPORT: Exported %d bars to MT4 format: %s",
            len(bars),
            out,
            extra={
                "bar_count": len(bars),
                "format": "MT4",
                "path": str(out),
                "fr_id": "FR-DATA-QUALITY-EXPORT",
            },
        )
        return out

    def export_mt5(
        self,
        bars: list[BarRecord],
        output_path: Path | str,
        default_spread: int = 10,
    ) -> Path:
        r"""Export bars to MetaTrader 5 tab-delimited format.

        Format:
        <DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>

        Fires FR-DATA-QUALITY-EXPORT.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as f:
            f.write(
                "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n"
            )
            for bar in bars:
                dt = datetime.fromisoformat(bar.timestamp_utc)
                date_part = dt.strftime("%Y.%m.%d")
                time_part = dt.strftime("%H:%M:%S")
                tick_vol = int(bar.volume)
                real_vol = int(bar.open_interest)
                f.write(
                    f"{date_part}\t{time_part}\t{bar.open:.5f}\t{bar.high:.5f}\t"
                    f"{bar.low:.5f}\t{bar.close:.5f}\t{tick_vol}\t{real_vol}\t{default_spread}\n"
                )

        logger.info(
            "FR-DATA-QUALITY-EXPORT: Exported %d bars to MT5 format: %s",
            len(bars),
            out,
            extra={
                "bar_count": len(bars),
                "format": "MT5",
                "path": str(out),
                "fr_id": "FR-DATA-QUALITY-EXPORT",
            },
        )
        return out

    @staticmethod
    def _calculate_bucket_start(dt: datetime, step_minutes: int) -> datetime:
        """Calculate start of interval bucket for resampling."""
        if step_minutes < MINUTES_IN_HOUR:
            minute_bucket = (dt.minute // step_minutes) * step_minutes
            return dt.replace(minute=minute_bucket, second=0, microsecond=0)
        if step_minutes < MINUTES_IN_DAY:
            hours_step = step_minutes // MINUTES_IN_HOUR
            hour_bucket = (dt.hour // hours_step) * hours_step
            return dt.replace(hour=hour_bucket, minute=0, second=0, microsecond=0)
        # Daily
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def main() -> int:
    """CLI tool for resampling and exporting market data files."""
    parser = argparse.ArgumentParser(description="Resample and export market data")
    parser.add_argument("--file", required=True, help="Input CSV data file")
    parser.add_argument("--resample", type=str, help="Target timeframe (e.g. M5, H1)")
    parser.add_argument("--export-mt4", type=str, help="Export to MT4 CSV path")
    parser.add_argument("--export-mt5", type=str, help="Export to MT5 TXT path")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: file not found: {file_path}")
        return 1

    bars: list[BarRecord] = []
    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                bars.append(
                    BarRecord(
                        timestamp_utc=r["timestamp"],
                        open=float(r["open"]),
                        high=float(r["high"]),
                        low=float(r["low"]),
                        close=float(r["close"]),
                        volume=float(r.get("volume", 0.0)),
                    )
                )
            except KeyError, ValueError:
                continue

    transformer = SeriesTransformer()
    processed_bars = bars
    if args.resample:
        processed_bars = transformer.resample(bars, args.resample)
        print(
            f"Resampled {len(bars)} bars to {len(processed_bars)} {args.resample} bars."
        )

    if args.export_mt4:
        out = transformer.export_mt4(processed_bars, args.export_mt4)
        print(f"Exported to MT4: {out}")
    if args.export_mt5:
        out = transformer.export_mt5(processed_bars, args.export_mt5)
        print(f"Exported to MT5: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
