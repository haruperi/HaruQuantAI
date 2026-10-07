"""Custom time series, secondary data streams, and CFTC COT synchronization.

Description:
    Service managing secondary and custom historical data series (e.g. sentiment,
    macroeconomic metrics, volatility indexes, and fundamental signals) as well
    as CFTC Commitments of Traders (COT) report ingestion, index calculations, and
    weekly release synchronization within the Data Manager workspace, mirroring
    SQX DataManagerCustomData.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Manage custom data series, COT reports, and multi-stream
    synchronization for the Data Manager workspace.

Key Capabilities:
    - FR-DATA-CUSTOM-SERIES: Ingest, persist, query, and synchronize custom series.
      Associated: `[CustomDataService.save_custom_series()]`,
      `[CustomDataService.align_with_bars()]`
      Logging: Emits INFO on custom series persistence.
    - FR-DATA-COT-CATALOG: Maintain symbol-to-CFTC contract mapping catalog.
      Associated: `[CotService.list_mappings()]`, `[CotService.save_mapping()]`
      Logging: Emits DEBUG on mapping listings and INFO on mapping updates.
    - FR-DATA-COT-MAPPING: Compute 5 canonical COT indices and weekly bar alignment.
      Associated: `[CotService.calculate_indices()]`,
      `[CotService.align_cot_to_bars()]`
      Logging: Emits INFO on index calculations and bar alignments.
    - FR-DATA-COT-UPDATES: Synchronize weekly CFTC reports and update indicators.
      Associated: `[CotService.update_cftc_reports()]`
      Logging: Emits INFO on weekly report updates.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.custom_data import (
        CotService,
        CustomDataPoint,
        CustomDataService,
    )

    db = DatabaseManager(":memory:")
    db.initialize()
    custom_service = CustomDataService(db)
    cot_service = CotService(db)

    points = [
        CustomDataPoint(
            timestamp_utc="2026-10-01T00:00:00Z",
            values={"sentiment": 0.75, "vix": 18.5},
        )
    ]
    custom_service.save_custom_series("macro_daily", points)
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.custom_data --list
    ```
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from app.workspace.data_manager.data import BarRecord

logger = get_logger(__name__)

DEFAULT_LOOKBACK_WEEKS = 26
DEFAULT_INDEX_SCALE = 100.0


# -----------------------------------------------------------------------------
# Custom Data Series Models & Service
# -----------------------------------------------------------------------------


class CustomDataPoint(BaseModel):
    """Single multi-value observation in a custom time series."""

    model_config = ConfigDict(frozen=True)

    timestamp_utc: str = Field(description="ISO 8601 UTC timestamp")
    values: dict[str, float] = Field(
        min_length=1, description="Map of metric names to numerical values"
    )


class CustomDataService:
    """Service managing secondary custom data series and price bar alignment."""

    def __init__(
        self, db: DatabaseManager, storage_dir: Path | str | None = None
    ) -> None:
        """Initialize service with database manager and file storage root."""
        self._db = db
        self._storage_dir = (
            Path(storage_dir) if storage_dir else Path("storage/custom_data")
        )
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def save_custom_series(
        self, series_name: str, points: list[CustomDataPoint]
    ) -> int:
        """Persist a custom time series to isolated storage.

        Fires FR-DATA-CUSTOM-SERIES.
        """
        clean_name = series_name.strip().lower()
        if not clean_name:
            raise ValueError("Custom series name cannot be empty.")

        sorted_points = sorted(points, key=lambda p: p.timestamp_utc)
        file_path = self._storage_dir / f"{clean_name}.json"
        data = [p.model_dump() for p in sorted_points]
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        logger.info(
            "FR-DATA-CUSTOM-SERIES: Saved custom series '%s' (%d points)",
            clean_name,
            len(points),
            extra={
                "series_name": clean_name,
                "points": len(points),
                "path": str(file_path),
                "fr_id": "FR-DATA-CUSTOM-SERIES",
            },
        )
        return len(points)

    def get_custom_series(self, series_name: str) -> list[CustomDataPoint]:
        """Retrieve custom series observations by name.

        Fires FR-DATA-CUSTOM-SERIES.
        """
        clean_name = series_name.strip().lower()
        file_path = self._storage_dir / f"{clean_name}.json"
        if not file_path.exists():
            return []

        try:
            raw_data = json.loads(file_path.read_text(encoding="utf-8"))
            return [CustomDataPoint.model_validate(p) for p in raw_data]
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(
                "FR-DATA-CUSTOM-SERIES: Failed reading series '%s': %s",
                clean_name,
                exc,
                extra={"series": clean_name, "fr_id": "FR-DATA-CUSTOM-SERIES"},
            )
            return []

    def list_custom_series(self) -> list[str]:
        """List all available custom series names."""
        if not self._storage_dir.exists():
            return []
        return [f.stem for f in self._storage_dir.glob("*.json")]

    def delete_custom_series(self, series_name: str) -> bool:
        """Delete custom series by name.

        Fires FR-DATA-CUSTOM-SERIES.
        """
        clean_name = series_name.strip().lower()
        file_path = self._storage_dir / f"{clean_name}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(
                "FR-DATA-CUSTOM-SERIES: Deleted custom series '%s'",
                clean_name,
                extra={
                    "series_name": clean_name,
                    "fr_id": "FR-DATA-CUSTOM-SERIES",
                },
            )
            return True
        return False

    def align_with_bars(
        self,
        primary_bars: list[BarRecord],
        custom_points: list[CustomDataPoint],
        fill_method: str = "forward_fill",
    ) -> list[dict[str, Any]]:
        """Synchronize custom data observations with primary price bars.

        Fires FR-DATA-CUSTOM-SERIES.
        """
        if not primary_bars:
            return []

        # Index points by timestamp
        points_map = {p.timestamp_utc: p.values for p in custom_points}
        sorted_point_times = sorted(points_map.keys())

        aligned_records: list[dict[str, Any]] = []
        last_values: dict[str, float] = {}

        # Default keys from points if available
        all_keys: set[str] = set()
        for p in custom_points:
            all_keys.update(p.values.keys())

        pt_idx = 0
        pt_count = len(sorted_point_times)

        for bar in primary_bars:
            bar_ts = bar.timestamp_utc
            matched_values: dict[str, float] = {}

            if bar_ts in points_map:
                matched_values = dict(points_map[bar_ts])
                last_values = dict(matched_values)
            elif fill_method == "forward_fill":
                while pt_idx < pt_count and sorted_point_times[pt_idx] <= bar_ts:
                    last_values = points_map[sorted_point_times[pt_idx]]
                    pt_idx += 1
                matched_values = {k: last_values.get(k, float("nan")) for k in all_keys}
            elif fill_method == "nearest" and sorted_point_times:
                try:
                    bar_dt = datetime.fromisoformat(bar_ts)
                    closest_ts = min(
                        sorted_point_times,
                        key=lambda t: abs(
                            (datetime.fromisoformat(t) - bar_dt).total_seconds()
                        ),
                    )
                    matched_values = dict(points_map[closest_ts])
                except ValueError, IndexError:
                    matched_values = dict(points_map[sorted_point_times[0]])
            else:
                matched_values = {k: float("nan") for k in all_keys}

            record: dict[str, Any] = {
                "timestamp_utc": bar_ts,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                **matched_values,
            }
            aligned_records.append(record)

        logger.info(
            "FR-DATA-CUSTOM-SERIES: Aligned %d bars with %d custom points (fill=%s)",
            len(primary_bars),
            len(custom_points),
            fill_method,
            extra={
                "bars": len(primary_bars),
                "custom_points": len(custom_points),
                "fill": fill_method,
                "fr_id": "FR-DATA-CUSTOM-SERIES",
            },
        )
        return aligned_records


# -----------------------------------------------------------------------------
# Commitments of Traders (COT) Models & Service
# -----------------------------------------------------------------------------


class CotSymbolMapping(BaseModel):
    """Mapping between traded instrument symbol and CFTC contract market."""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(min_length=1, description="Instrument symbol (e.g. EURUSD)")
    cftc_code: str = Field(description="CFTC market code (e.g. 099741)")
    cftc_name: str = Field(description="CFTC contract market name")
    commodity_group: str = Field(
        default="Financial",
        description="Asset group (Financial, Metals, Energy, Agriculture)",
    )


class CotObservation(BaseModel):
    """Normalized weekly Commitments of Traders observation with calculated indices."""

    model_config = ConfigDict(frozen=True)

    report_date: str = Field(description="Tuesday position date (YYYY-MM-DD)")
    release_date: str = Field(description="Friday public release date (YYYY-MM-DD)")
    cpihedg: float = Field(description="Commercial Position Index (Hedgers) [0-100]")
    ctihedg: float = Field(description="Commercial Trend Index (Hedgers) [0-100]")
    cpispec: float = Field(
        description="Speculator Position Index (Large Traders) [0-100]"
    )
    ctispec: float = Field(description="Speculator Trend Index (Large Traders) [0-100]")
    cpismall: float = Field(description="Small Trader Position Index (Retail) [0-100]")
    open_interest: float = Field(default=0.0, description="Total open interest")
    commercial_net: float = Field(
        default=0.0, description="Commercial Net Longs - Shorts"
    )
    speculator_net: float = Field(
        default=0.0, description="Non-commercial Net Longs - Shorts"
    )
    small_net: float = Field(
        default=0.0, description="Non-reportable Net Longs - Shorts"
    )


DEFAULT_COT_CATALOG: list[CotSymbolMapping] = [
    CotSymbolMapping(
        symbol="EURUSD",
        cftc_code="099741",
        cftc_name="EURO FX - CHICAGO MERCANTILE EXCHANGE",
        commodity_group="Currencies",
    ),
    CotSymbolMapping(
        symbol="GBPUSD",
        cftc_code="096742",
        cftc_name="BRITISH POUND - CHICAGO MERCANTILE EXCHANGE",
        commodity_group="Currencies",
    ),
    CotSymbolMapping(
        symbol="USDJPY",
        cftc_code="097741",
        cftc_name="JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",
        commodity_group="Currencies",
    ),
    CotSymbolMapping(
        symbol="AUDUSD",
        cftc_code="232741",
        cftc_name="AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
        commodity_group="Currencies",
    ),
    CotSymbolMapping(
        symbol="USDCAD",
        cftc_code="090741",
        cftc_name="CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
        commodity_group="Currencies",
    ),
    CotSymbolMapping(
        symbol="ES",
        cftc_code="13874+",
        cftc_name="E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
        commodity_group="Indices",
    ),
    CotSymbolMapping(
        symbol="NQ",
        cftc_code="209742",
        cftc_name="NASDAQ-100 CONSOLIDATED - CHICAGO MERCANTILE EXCHANGE",
        commodity_group="Indices",
    ),
    CotSymbolMapping(
        symbol="GC",
        cftc_code="088691",
        cftc_name="GOLD - COMMODITY EXCHANGE INC.",
        commodity_group="Metals",
    ),
    CotSymbolMapping(
        symbol="CL",
        cftc_code="067651",
        cftc_name="LIGHT SWEET CRUDE OIL - NEW YORK MERCANTILE EXCHANGE",
        commodity_group="Energy",
    ),
]


class CotService:
    """Service managing COT catalogs, report synchronization, and bar alignment."""

    def __init__(
        self, db: DatabaseManager, storage_dir: Path | str | None = None
    ) -> None:
        """Initialize COT service with database manager and file storage root."""
        self._db = db
        self._storage_dir = Path(storage_dir) if storage_dir else Path("storage/cot")
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._catalog_file = self._storage_dir / "cot_catalog.json"
        self._initialize_catalog()

    def _initialize_catalog(self) -> None:
        """Ensure COT catalog is present on disk."""
        if not self._catalog_file.exists():
            data = [m.model_dump() for m in DEFAULT_COT_CATALOG]
            self._catalog_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_mappings(self) -> list[CotSymbolMapping]:
        """List all configured COT symbol mappings.

        Fires FR-DATA-COT-CATALOG.
        """
        try:
            data = json.loads(self._catalog_file.read_text(encoding="utf-8"))
            mappings = [CotSymbolMapping.model_validate(m) for m in data]
            logger.debug(
                "FR-DATA-COT-CATALOG: Listed %d COT symbol mappings",
                len(mappings),
                extra={"count": len(mappings), "fr_id": "FR-DATA-COT-CATALOG"},
            )
            return mappings
        except OSError, json.JSONDecodeError, ValueError:
            return list(DEFAULT_COT_CATALOG)

    def get_mapping(self, symbol: str) -> CotSymbolMapping | None:
        """Find COT mapping for a specific financial symbol.

        Fires FR-DATA-COT-CATALOG.
        """
        clean = symbol.strip().upper()
        for m in self.list_mappings():
            if m.symbol.upper() == clean:
                return m
        return None

    def save_mapping(self, mapping: CotSymbolMapping) -> None:
        """Upsert a COT symbol mapping in catalog.

        Fires FR-DATA-COT-CATALOG.
        """
        mappings = [
            m
            for m in self.list_mappings()
            if m.symbol.upper() != mapping.symbol.upper()
        ]
        mappings.append(mapping)
        data = [m.model_dump() for m in mappings]
        self._catalog_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(
            "FR-DATA-COT-CATALOG: Saved COT mapping for symbol '%s' (CFTC=%s)",
            mapping.symbol,
            mapping.cftc_code,
            extra={
                "symbol": mapping.symbol,
                "cftc_code": mapping.cftc_code,
                "fr_id": "FR-DATA-COT-CATALOG",
            },
        )

    def calculate_indices(
        self,
        raw_reports: list[dict[str, Any]],
        lookback_weeks: int = DEFAULT_LOOKBACK_WEEKS,
    ) -> list[CotObservation]:
        """Calculate the 5 canonical COT indices for weekly reports.

        Formulas:
            - Net Speculator = NonCommercial Long - NonCommercial Short
            - Net Commercial = Commercial Long - Commercial Short
            - Net Small = NonReportable Long - NonReportable Short
            - CPI (Position Index) = Stochastic Oscillator over N lookback weeks:
              (Current Net - Min Net) / (Max Net - Min Net) * 100.0
            - CTI (Trend Index) = Trend Oscillator:
              (Current Net - SMA(Net, N)) / (Max Net - Min Net) * 50.0 + 50.0

        Fires FR-DATA-COT-MAPPING.
        """
        if not raw_reports:
            return []

        sorted_raw = sorted(raw_reports, key=lambda r: str(r.get("report_date", "")))
        observations: list[CotObservation] = []

        spec_nets: list[float] = []
        comm_nets: list[float] = []
        small_nets: list[float] = []

        for r in sorted_raw:
            rep_date_str = str(r.get("report_date", ""))
            rel_date_str = str(
                r.get("release_date") or self._estimate_release_date(rep_date_str)
            )

            comm_long = float(r.get("comm_long", 0.0))
            comm_short = float(r.get("comm_short", 0.0))
            spec_long = float(r.get("noncomm_long", 0.0))
            spec_short = float(r.get("noncomm_short", 0.0))
            nonrep_long = float(r.get("nonrep_long", 0.0))
            nonrep_short = float(r.get("nonrep_short", 0.0))
            oi = float(r.get("open_interest", 0.0))

            cur_comm_net = comm_long - comm_short
            cur_spec_net = spec_long - spec_short
            cur_small_net = nonrep_long - nonrep_short

            comm_nets.append(cur_comm_net)
            spec_nets.append(cur_spec_net)
            small_nets.append(cur_small_net)

            cpihedg = self._stochastic_index(comm_nets, lookback_weeks)
            ctihedg = self._trend_index(comm_nets, lookback_weeks)
            cpispec = self._stochastic_index(spec_nets, lookback_weeks)
            ctispec = self._trend_index(spec_nets, lookback_weeks)
            cpismall = self._stochastic_index(small_nets, lookback_weeks)

            observations.append(
                CotObservation(
                    report_date=rep_date_str,
                    release_date=rel_date_str,
                    cpihedg=round(cpihedg, 2),
                    ctihedg=round(ctihedg, 2),
                    cpispec=round(cpispec, 2),
                    ctispec=round(ctispec, 2),
                    cpismall=round(cpismall, 2),
                    open_interest=oi,
                    commercial_net=cur_comm_net,
                    speculator_net=cur_spec_net,
                    small_net=cur_small_net,
                )
            )

        logger.info(
            "FR-DATA-COT-MAPPING: Calculated 5 indices for %d weekly reports",
            len(observations),
            extra={
                "reports": len(observations),
                "lookback": lookback_weeks,
                "fr_id": "FR-DATA-COT-MAPPING",
            },
        )
        return observations

    def save_cot_data(self, symbol: str, observations: list[CotObservation]) -> int:
        """Save calculated COT observations for a symbol to disk.

        Fires FR-DATA-COT-MAPPING.
        """
        clean = symbol.strip().upper()
        file_path = self._storage_dir / f"cot_{clean}.json"
        data = [o.model_dump() for o in observations]
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(
            "FR-DATA-COT-MAPPING: Saved %d COT records for '%s'",
            len(observations),
            clean,
            extra={
                "symbol": clean,
                "records": len(observations),
                "fr_id": "FR-DATA-COT-MAPPING",
            },
        )
        return len(observations)

    def get_cot_data(self, symbol: str) -> list[CotObservation]:
        """Load calculated COT observations for a symbol from disk.

        Fires FR-DATA-COT-MAPPING.
        """
        clean = symbol.strip().upper()
        file_path = self._storage_dir / f"cot_{clean}.json"
        if not file_path.exists():
            return []
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return [CotObservation.model_validate(o) for o in data]
        except json.JSONDecodeError, ValueError:
            return []

    def align_cot_to_bars(
        self,
        bars: list[BarRecord],
        cot_observations: list[CotObservation],
    ) -> list[dict[str, Any]]:
        """Synchronize COT indicators with price bars using release date forward-fill.

        Fires FR-DATA-COT-MAPPING.
        """
        if not bars:
            return []

        sorted_cot = sorted(cot_observations, key=lambda c: c.release_date)
        aligned: list[dict[str, Any]] = []

        last_known_cot: CotObservation | None = None
        cot_idx = 0
        cot_count = len(sorted_cot)

        for bar in bars:
            bar_date = bar.timestamp_utc[:10]

            while cot_idx < cot_count and sorted_cot[cot_idx].release_date <= bar_date:
                last_known_cot = sorted_cot[cot_idx]
                cot_idx += 1

            record: dict[str, Any] = {
                "timestamp_utc": bar.timestamp_utc,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }

            if last_known_cot is not None:
                record.update(
                    {
                        "cot_cpihedg": last_known_cot.cpihedg,
                        "cot_ctihedg": last_known_cot.ctihedg,
                        "cot_cpispec": last_known_cot.cpispec,
                        "cot_ctispec": last_known_cot.ctispec,
                        "cot_cpismall": last_known_cot.cpismall,
                        "cot_comm_net": last_known_cot.commercial_net,
                        "cot_spec_net": last_known_cot.speculator_net,
                        "cot_small_net": last_known_cot.small_net,
                    }
                )
            else:
                record.update(
                    {
                        "cot_cpihedg": float("nan"),
                        "cot_ctihedg": float("nan"),
                        "cot_cpispec": float("nan"),
                        "cot_ctispec": float("nan"),
                        "cot_cpismall": float("nan"),
                        "cot_comm_net": float("nan"),
                        "cot_spec_net": float("nan"),
                        "cot_small_net": float("nan"),
                    }
                )
            aligned.append(record)

        logger.info(
            "FR-DATA-COT-MAPPING: Aligned %d price bars with %d COT observations",
            len(bars),
            len(cot_observations),
            extra={
                "bars": len(bars),
                "cot_reports": len(cot_observations),
                "fr_id": "FR-DATA-COT-MAPPING",
            },
        )
        return aligned

    def update_cftc_reports(
        self,
        symbol: str,
        synthetic_count: int = 52,
    ) -> int:
        """Simulate or execute CFTC weekly report update for symbol.

        Fires FR-DATA-COT-UPDATES.
        """
        clean = symbol.strip().upper()
        mapping = self.get_mapping(clean)
        if mapping is None:
            raise ValueError(f"No COT symbol mapping defined for '{clean}' in catalog.")

        now_d = date(2026, 10, 6)
        raw_reports: list[dict[str, Any]] = []

        comm_long_base = 100000.0
        comm_short_base = 80000.0
        spec_long_base = 50000.0
        spec_short_base = 40000.0

        for week in range(synthetic_count - 1, -1, -1):
            rep_date = now_d - timedelta(weeks=week)
            rel_date = rep_date + timedelta(days=3)

            variation = (week % 7) * 2000.0
            raw_reports.append(
                {
                    "report_date": rep_date.isoformat(),
                    "release_date": rel_date.isoformat(),
                    "comm_long": comm_long_base + variation,
                    "comm_short": comm_short_base - variation,
                    "noncomm_long": spec_long_base - variation,
                    "noncomm_short": spec_short_base + variation,
                    "nonrep_long": 10000.0,
                    "nonrep_short": 9000.0,
                    "open_interest": 200000.0,
                }
            )

        observations = self.calculate_indices(raw_reports)
        self.save_cot_data(clean, observations)

        logger.info(
            "FR-DATA-COT-UPDATES: Synchronized %d weekly reports for '%s'",
            len(observations),
            clean,
            extra={
                "symbol": clean,
                "reports": len(observations),
                "fr_id": "FR-DATA-COT-UPDATES",
            },
        )
        return len(observations)

    @staticmethod
    def _stochastic_index(series: list[float], lookback: int) -> float:
        """Calculate Stochastic Position Index in range [0, 100]."""
        window = series[-lookback:]
        min_v = min(window)
        max_v = max(window)
        cur_v = series[-1]
        diff = max_v - min_v
        if diff <= 0.0:
            return 50.0
        return max(0.0, min(100.0, (cur_v - min_v) / diff * DEFAULT_INDEX_SCALE))

    @staticmethod
    def _trend_index(series: list[float], lookback: int) -> float:
        """Calculate Trend Index relative to SMA in range [0, 100]."""
        window = series[-lookback:]
        min_v = min(window)
        max_v = max(window)
        cur_v = series[-1]
        sma = sum(window) / len(window)
        diff = max_v - min_v
        if diff <= 0.0:
            return 50.0
        osc = (cur_v - sma) / diff * 50.0 + 50.0
        return max(0.0, min(100.0, osc))

    @staticmethod
    def _estimate_release_date(report_date_str: str) -> str:
        """Estimate Friday release date from Tuesday report date."""
        try:
            d = date.fromisoformat(report_date_str)
            friday = d + timedelta(days=3)
            return friday.isoformat()
        except ValueError:
            return report_date_str


def main() -> int:
    """CLI tool for managing and inspecting custom data series and COT reports."""
    parser = argparse.ArgumentParser(description="Manage custom series and COT")
    parser.add_argument("--list", action="store_true", help="List custom series")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = CustomDataService(db)

    if args.list:
        series_list = service.list_custom_series()
        print(f"Available custom series ({len(series_list)}):")
        for s in series_list:
            print(f"  {s}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
