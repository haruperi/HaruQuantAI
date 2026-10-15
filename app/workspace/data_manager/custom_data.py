"""External indicators, custom macroeconomic series, and MQ4 recognizer.

Description:
    Provides domain logic for external indicators, COT time series, and custom
    macroeconomic indicators (`ExternalIndicatorDefinition`). Persists metadata
    in SQLite (`host_entities`) and time-series value vectors in partitioned
    Parquet files (`{data_dir}/custom_data/{name}.parquet`). Recognizes MetaTrader 4
    `.mq4` indicator source code and parses multi-column CSV time-series data.

Purpose:
    FEAT-DATAMGR-CUSTOM-DATA: External indicator management and MQ4 buffer recognition.

Key Capabilities:
    - FR-DATAMGR-CUSTOM-DATA-CRUD: Manage custom indicator definitions and storage.
      Associated: `CustomDataService.list_definitions()`,
      `CustomDataService.save_definition()`,
      `CustomDataService.delete_definition()`
      Logging: Emits INFO on definition creation, clearance, and deletion.
    - FR-DATAMGR-CUSTOM-DATA-CSV-IMPORT: Parse delimited external indicator CSV records.
      Associated: `CustomDataService.import_csv_records()`
      Logging: Emits INFO on parsing CSV rows with record count and timeframe.
    - FR-DATAMGR-CUSTOM-DATA-MQ4-RECOGNIZER: Parse MetaTrader 4 .mq4 indicator buffers.
      Associated: `CustomDataService.recognize_mq4()`
      Logging: Emits INFO on analyzing .mq4 source and extracting buffer lines.

Python API Usage:
    ```python
    from app.workspace.data_manager.custom_data import CustomDataService

    service = CustomDataService()
    defs = service.list_definitions()
    defn = service.recognize_mq4("MACD.mq4", source_code)
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.custom_data
    ```
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import re
import statistics
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.host.persistence.create import create_schema, insert_row
from app.host.persistence.delete import delete_rows
from app.host.persistence.read import read_rows, resolve_connection

__all__ = [
    "CustomDataService",
    "ExternalIndicatorDefinition",
    "ExternalIndicatorRecord",
]

logger = get_logger(__name__)

CUSTOM_DATA_CRUD_FR = "FR-DATAMGR-CUSTOM-DATA-CRUD"
CSV_IMPORT_FR = "FR-DATAMGR-CUSTOM-DATA-CSV-IMPORT"
MQ4_RECOGNIZER_FR = "FR-DATAMGR-CUSTOM-DATA-MQ4-RECOGNIZER"


@dataclass(frozen=True)
class ExternalIndicatorLine:
    """Represents a single indicator plot or buffer line."""

    name: str
    mt4: str = ""
    mt5: str = ""
    el: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert line definition to dictionary representation."""
        return {
            "name": self.name,
            "mt4": self.mt4,
            "mt5": self.mt5,
            "el": self.el,
        }


@dataclass(frozen=True)
class ExternalIndicatorRecord:
    """Represents a timestamped vector of indicator values."""

    timestamp: int
    values: list[float]

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "values": self.values,
        }


@dataclass
class ExternalIndicatorDefinition:
    """Represents a custom data / external indicator definition."""

    name: str
    type: int = 2
    values: list[ExternalIndicatorLine] = field(default_factory=list)
    timeframe: str = "—"
    date_from: str = ""
    date_to: str = ""
    total_days: int = 0
    records: list[ExternalIndicatorRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert indicator definition to dictionary representation."""
        return {
            "name": self.name,
            "type": self.type,
            "values": [v.to_dict() for v in self.values],
            "timeframe": self.timeframe,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "total_days": self.total_days,
            "records": [r.to_dict() for r in self.records],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExternalIndicatorDefinition:
        """Construct definition from dictionary representation."""
        raw_lines = data.get("values", [])
        lines = [
            ExternalIndicatorLine(**v) if isinstance(v, dict) else v for v in raw_lines
        ]
        raw_recs = data.get("records", [])
        recs = [
            ExternalIndicatorRecord(**r) if isinstance(r, dict) else r for r in raw_recs
        ]
        return cls(
            name=str(data.get("name", "")),
            type=int(data.get("type", 2)),
            values=lines,
            timeframe=str(data.get("timeframe", "—")),
            date_from=str(data.get("date_from", "")),
            date_to=str(data.get("date_to", "")),
            total_days=int(data.get("total_days", 0)),
            records=recs,
        )


MIN_RECORDS_FOR_CADENCE = 2
SECONDS_PER_MINUTE = 60.0
SECONDS_PER_HOUR = 3600.0
SECONDS_PER_DAY = 86400.0
SECONDS_PER_WEEK = 604800.0


def _parse_finite_float(val_str: str) -> float:
    """Parse and validate finite float."""
    v = float(val_str.strip())
    if math.isnan(v) or math.isinf(v):
        msg = f"Non-finite numeric value: {val_str}"
        raise ValueError(msg)
    return v


def _infer_cadence_timeframe(
    raw_records: Sequence[ExternalIndicatorRecord],
) -> str:
    """Infer timeframe from median timestamp difference in records."""
    if len(raw_records) < MIN_RECORDS_FOR_CADENCE:
        return "D1"
    deltas = [
        raw_records[i].timestamp - raw_records[i - 1].timestamp
        for i in range(1, len(raw_records))
        if raw_records[i].timestamp > raw_records[i - 1].timestamp
    ]
    if not deltas:
        return "D1"
    median_sec = statistics.median(deltas) / 1000.0
    cadence = "W1"
    if median_sec <= 0:
        cadence = "TICK"
    elif median_sec < SECONDS_PER_MINUTE:
        cadence = f"S{max(1, round(median_sec))}"
    elif median_sec < SECONDS_PER_HOUR:
        cadence = f"M{max(1, round(median_sec / SECONDS_PER_MINUTE))}"
    elif median_sec < SECONDS_PER_DAY:
        cadence = f"H{max(1, round(median_sec / SECONDS_PER_HOUR))}"
    elif median_sec < SECONDS_PER_WEEK:
        cadence = f"D{max(1, round(median_sec / SECONDS_PER_DAY))}"
    return cadence


def _parse_csv_row(
    row: Sequence[str], min_cols: int
) -> tuple[ExternalIndicatorRecord, dict[str, Any]] | None:
    """Parse a single CSV row into record and dictionary representation."""
    if not row or len(row) < min_cols:
        return None
    ts_str = row[0].strip()
    try:
        try:
            dt = datetime.fromisoformat(ts_str)
            dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
            ts_ms = int(dt.timestamp() * 1000)
        except ValueError:
            ts_ms = int(ts_str)

        vals = [_parse_finite_float(val) for val in row[1:]]

        record = ExternalIndicatorRecord(timestamp=ts_ms, values=vals)
        row_dict: dict[str, Any] = {"timestamp": ts_str}
        for i, v in enumerate(vals):
            row_dict[f"val_{i}"] = v
        return record, row_dict
    except (ValueError, TypeError, OverflowError) as exc:
        logger.debug("%s: Skipping malformed row: %s", CSV_IMPORT_FR, exc)
        return None


class CustomDataService:
    """Service governing external indicators, CSV imports, and MQ4 recognition."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        data_dir: Path | str | None = None,
    ) -> None:
        """Initialize custom data service with database path and storage directory."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.data_dir = Path(data_dir) if data_dir is not None else Path("data")

    def _parquet_path(self, name: str) -> Path:
        clean_name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
        return self.data_dir / "custom_data" / f"{clean_name}.parquet"

    def list_definitions(self) -> list[ExternalIndicatorDefinition]:
        """List all external indicator definitions stored in host_entities."""
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "host_entities",
                where={"entity_type": "datamgr_custom_data"},
                order_by="entity_id ASC",
            )

        definitions: list[ExternalIndicatorDefinition] = []
        for r in rows:
            try:
                payload = json.loads(str(r.get("payload", "{}")))
                defn = ExternalIndicatorDefinition.from_dict(payload)
                # Load parquet record count if file exists
                pq_file = self._parquet_path(defn.name)
                if pq_file.is_file():
                    with contextlib.suppress(OSError, ValueError):
                        df = pd.read_parquet(pq_file)
                        defn.total_days = len(df)
                definitions.append(defn)
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                logger.debug(
                    "%s: Skipping malformed indicator payload: %s",
                    CUSTOM_DATA_CRUD_FR,
                    exc,
                )
        return definitions

    def get_definition(self, name: str) -> ExternalIndicatorDefinition | None:
        """Retrieve an indicator definition by name."""
        clean = name.strip()
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "host_entities",
                where={
                    "entity_id": clean,
                    "entity_type": "datamgr_custom_data",
                },
                limit=1,
            )
        if not rows:
            return None
        payload = json.loads(str(rows[0].get("payload", "{}")))
        defn = ExternalIndicatorDefinition.from_dict(payload)
        pq_file = self._parquet_path(defn.name)
        if pq_file.is_file():
            with contextlib.suppress(OSError, ValueError):
                df = pd.read_parquet(pq_file)
                defn.total_days = len(df)
                if not df.empty and "timestamp" in df.columns:
                    defn.date_from = str(df["timestamp"].iloc[0])
                    defn.date_to = str(df["timestamp"].iloc[-1])
        return defn

    def save_definition(
        self, payload: Mapping[str, Any]
    ) -> ExternalIndicatorDefinition:
        """Save indicator definition in host_entities."""
        clean_name = str(payload.get("name", "")).strip()
        if not clean_name:
            raise ValueError("Indicator name is required.")

        defn = ExternalIndicatorDefinition.from_dict(payload)
        now_iso = datetime.now(UTC).isoformat()
        payload_json = json.dumps(defn.to_dict())

        with resolve_connection(self.db_path) as conn:
            delete_rows(
                conn,
                "host_entities",
                where={
                    "entity_id": clean_name,
                    "entity_type": "datamgr_custom_data",
                },
            )
            insert_row(
                conn,
                "host_entities",
                {
                    "entity_id": clean_name,
                    "entity_type": "datamgr_custom_data",
                    "scope": "workspace",
                    "payload": payload_json,
                    "revision": 1,
                    "created_at_utc": now_iso,
                    "updated_at_utc": now_iso,
                },
            )

        logger.info(
            "%s: Saved custom indicator definition '%s'",
            CUSTOM_DATA_CRUD_FR,
            defn.name,
            extra={"fr_id": CUSTOM_DATA_CRUD_FR, "indicator_name": defn.name},
        )
        return defn

    def clear_definition(self, name: str) -> ExternalIndicatorDefinition:
        """Clear time-series records for an indicator while preserving schema."""
        defn = self.get_definition(name)
        if defn is None:
            raise KeyError(f"Custom data '{name}' not found.")

        pq_file = self._parquet_path(name)
        if pq_file.is_file():
            try:
                pq_file.unlink(missing_ok=True)
            except OSError:
                logger.exception(
                    "%s: Failed to unlink parquet file %s",
                    CUSTOM_DATA_CRUD_FR,
                    pq_file,
                )
                raise

        defn.records = []
        defn.total_days = 0
        defn.date_from = ""
        defn.date_to = ""
        saved = self.save_definition(defn.to_dict())
        logger.info(
            "%s: Cleared records for indicator '%s'",
            CUSTOM_DATA_CRUD_FR,
            name,
            extra={"fr_id": CUSTOM_DATA_CRUD_FR, "indicator_name": name},
        )
        return saved

    def delete_definition(self, name: str) -> bool:
        """Delete an indicator definition and associated Parquet file."""
        clean = name.strip()
        pq_file = self._parquet_path(clean)
        if pq_file.is_file():
            try:
                pq_file.unlink(missing_ok=True)
            except OSError:
                logger.exception(
                    "%s: Failed to unlink parquet file %s",
                    CUSTOM_DATA_CRUD_FR,
                    pq_file,
                )
                raise

        with resolve_connection(self.db_path) as conn:
            count = delete_rows(
                conn,
                "host_entities",
                where={
                    "entity_id": clean,
                    "entity_type": "datamgr_custom_data",
                },
            )
        deleted = count > 0
        logger.info(
            "%s: Deleted indicator '%s' (deleted=%s)",
            CUSTOM_DATA_CRUD_FR,
            clean,
            deleted,
            extra={
                "fr_id": CUSTOM_DATA_CRUD_FR,
                "indicator_name": clean,
                "deleted": deleted,
            },
        )
        return deleted

    def import_csv_records(
        self,
        name: str,
        csv_text: str,
        separator: str = ",",
        skip_rows: int = 0,
    ) -> ExternalIndicatorDefinition:
        """Parse time series from CSV text into Parquet and update definition."""
        defn = self.get_definition(name)
        if defn is None:
            defn = self.save_definition({"name": name})

        lines = csv_text.strip().splitlines()
        if skip_rows > 0 and len(lines) > skip_rows:
            lines = lines[skip_rows:]

        reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=separator)
        parsed_records: list[dict[str, Any]] = []
        raw_records: list[ExternalIndicatorRecord] = []
        min_row_cols = 2

        for row in reader:
            parsed = _parse_csv_row(row, min_row_cols)
            if parsed is not None:
                rec, r_dict = parsed
                raw_records.append(rec)
                parsed_records.append(r_dict)

        if parsed_records:
            df = pd.DataFrame(parsed_records)
            pq_file = self._parquet_path(name)
            pq_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(pq_file, index=False)

            preview_record_limit = 100
            defn.records = raw_records[:preview_record_limit]
            defn.total_days = len(parsed_records)
            defn.date_from = str(parsed_records[0]["timestamp"])
            defn.date_to = str(parsed_records[-1]["timestamp"])
            defn.timeframe = _infer_cadence_timeframe(raw_records)
            defn = self.save_definition(defn.to_dict())

        logger.info(
            "%s: Imported %d custom data records for '%s'",
            CSV_IMPORT_FR,
            len(parsed_records),
            name,
            extra={
                "fr_id": CSV_IMPORT_FR,
                "indicator_name": name,
                "count": len(parsed_records),
            },
        )
        return defn

    def recognize_mq4(
        self, filename: str, source_code: str
    ) -> ExternalIndicatorDefinition:
        """Parse MetaTrader 4 .mq4 source code to extract indicator buffers."""
        stem = Path(filename).stem
        buffers_count = 1
        buff_match = re.search(r"#property\s+indicator_buffers\s+(\d+)", source_code)
        if buff_match:
            buffers_count = int(buff_match.group(1))

        labels: dict[int, str] = {}
        for m in re.finditer(
            r"SetIndexLabel\s*\(\s*(\d+)\s*,\s*\"([^\"]+)\"\s*\)", source_code
        ):
            labels[int(m.group(1))] = m.group(2)

        lines: list[ExternalIndicatorLine] = []
        for i in range(buffers_count):
            label = labels.get(i, f"Buffer_{i}")
            icustom_mt4 = f'iCustom(NULL, 0, "{stem}", {i}, bar)'
            icustom_mt5 = f'iCustom(_Symbol, _Period, "{stem}", {i}, bar)'
            lines.append(
                ExternalIndicatorLine(
                    name=label,
                    mt4=icustom_mt4,
                    mt5=icustom_mt5,
                    el=f"CustomIndicator({i})",
                )
            )

        defn = ExternalIndicatorDefinition(
            name=stem,
            type=2,
            values=lines,
            timeframe="—",
        )
        saved = self.save_definition(defn.to_dict())
        logger.info(
            "%s: Recognized MQ4 indicator '%s' (%d buffers)",
            MQ4_RECOGNIZER_FR,
            stem,
            len(lines),
            extra={
                "fr_id": MQ4_RECOGNIZER_FR,
                "indicator_name": stem,
                "buffers": len(lines),
            },
        )
        return saved


def main() -> None:
    """Execute real-usage demonstration of CustomDataService."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_custom.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        service = CustomDataService(db_path=db_file, data_dir=temp_path / "data")
        defn = service.save_definition(
            {
                "name": "US_CPI",
                "values": [{"name": "CPI_YoY", "mt4": "", "mt5": "", "el": ""}],
            }
        )
        print(f"Created custom indicator: {defn.name}")

        csv_content = "2026-01-01,3.1\n2026-02-01,3.2\n2026-03-01,3.0\n2026-04-01,2.9\n"
        imported = service.import_csv_records("US_CPI", csv_content)
        print(
            f"Imported records for {imported.name}: "
            f"total={imported.total_days}, from={imported.date_from}"
        )

        mq4_src = """
        #property indicator_buffers 2
        void init() {
            SetIndexBuffer(0, ExtBuffer1);
            SetIndexLabel(0, "MainSignal");
            SetIndexBuffer(1, ExtBuffer2);
            SetIndexLabel(1, "TriggerLine");
        }
        """
        mq4_defn = service.recognize_mq4("CustomOscillator.mq4", mq4_src)
        print(f"Parsed MQ4 indicator: {mq4_defn.name} ({len(mq4_defn.values)} lines)")
        for line in mq4_defn.values:
            print(f" - {line.name}: {line.mt4}")


if __name__ == "__main__":
    main()
