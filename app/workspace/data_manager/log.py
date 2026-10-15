"""Audit and operational logging service for the Data Manager workspace.

Description:
    Provides structured audit trail logging (`datamgr_logs`) and long-running
    operation tracking (`datamgr_operation_log`) for all Data Manager actions,
    including historical imports, downloads, resampling, timezone clones, and
    catalog modifications. Supports StrategyQuant X line formatting (`sqx_line`),
    filtering by symbol and action, and scoped log clearing.

Purpose:
    FEAT-DATAMGR-LOG: Historical market data and workspace operation audit logging.

Key Capabilities:
    - FR-DATAMGR-LOG-AUDIT-ENTRIES: Append, filter, and format audit log entries.
      Associated: `DataManagerLogService.append_log()`,
      `DataManagerLogService.list_logs()`
      Logging: Emits INFO on log append with action and symbol metadata.
    - FR-DATAMGR-LOG-CLEAR: Clear audit log entries globally or scoped by symbol.
      Associated: `DataManagerLogService.clear_logs()`
      Logging: Emits INFO on log clear with affected record count.
    - FR-DATAMGR-LOG-OPERATION-TRACKING: Track structured data operations and statuses.
      Associated: `DataManagerLogService.record_operation()`,
      `DataManagerLogService.list_operations()`
      Logging: Emits INFO on recording operation lifecycle events.

Python API Usage:
    ```python
    from app.workspace.data_manager.log import DataManagerLogService

    service = DataManagerLogService()
    entry = service.append_log(
        action="IMPORT",
        message="Imported EURUSD M1 bars",
        symbol="EURUSD",
    )
    print(entry.sqx_line)
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.log
    ```
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.create import create_schema, insert_row
from app.host.persistence.delete import delete_rows
from app.host.persistence.read import read_rows, resolve_connection

__all__ = [
    "DataManagerLogEntry",
    "DataManagerLogService",
    "OperationLogEntry",
]

logger = get_logger(__name__)

AUDIT_ENTRIES_FR = "FR-DATAMGR-LOG-AUDIT-ENTRIES"
CLEAR_FR = "FR-DATAMGR-LOG-CLEAR"
OPERATION_TRACKING_FR = "FR-DATAMGR-LOG-OPERATION-TRACKING"


@dataclass(frozen=True)
class DataManagerLogEntry:
    """Represents a single audit log entry in the Data Manager."""

    id: int
    timestamp_utc: str
    symbol: str | None
    action: str
    message: str
    sqx_line: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert log entry to dictionary representation."""
        return {
            "id": self.id,
            "timestamp_utc": self.timestamp_utc,
            "symbol": self.symbol,
            "action": self.action,
            "message": self.message,
            "sqx_line": self.sqx_line,
            "details": self.details,
        }


@dataclass(frozen=True)
class OperationLogEntry:
    """Represents a structured operation execution record."""

    id: int
    timestamp_utc: str
    symbol: str
    operation: str
    status: str
    rows_affected: int
    duration_ms: float
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert operation log entry to dictionary representation."""
        return {
            "id": self.id,
            "timestamp_utc": self.timestamp_utc,
            "symbol": self.symbol,
            "operation": self.operation,
            "status": self.status,
            "rows_affected": self.rows_affected,
            "duration_ms": self.duration_ms,
            "message": self.message,
            "details": self.details,
        }


class DataManagerLogService:
    """Service governing audit logging and operation tracking."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        """Initialize log service with optional database path."""
        self.db_path = Path(db_path) if db_path is not None else None

    def append_log(
        self,
        action: str,
        message: str,
        symbol: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> DataManagerLogEntry:
        """Append an audit entry to `datamgr_logs`."""
        now_utc = datetime.now(UTC)
        timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        clean_symbol = symbol.strip() if symbol else None
        sqx_line = f"{timestamp_str} - {clean_symbol or 'SYSTEM'} - {message}"
        details_dict: dict[str, Any] = dict(details) if details else {}

        with resolve_connection(self.db_path) as conn:
            inserted = insert_row(
                conn,
                "datamgr_logs",
                {
                    "timestamp_utc": timestamp_str,
                    "action": action.upper(),
                    "message": message,
                    "symbol": clean_symbol,
                    "details": json.dumps(details_dict),
                },
            )

        log_id = int(inserted)
        entry = DataManagerLogEntry(
            id=log_id,
            timestamp_utc=timestamp_str,
            symbol=clean_symbol,
            action=action.upper(),
            message=message,
            sqx_line=sqx_line,
            details=details_dict,
        )
        logger.info(
            "%s: Appended audit log entry id=%d action=%s symbol=%s",
            AUDIT_ENTRIES_FR,
            log_id,
            entry.action,
            entry.symbol,
            extra={
                "fr_id": AUDIT_ENTRIES_FR,
                "log_id": log_id,
                "action": entry.action,
                "symbol": entry.symbol,
            },
        )
        return entry

    def list_logs(
        self,
        symbol: str | None = None,
        action: str | None = None,
        limit: int = 200,
    ) -> list[DataManagerLogEntry]:
        """List audit entries matching optional filters."""
        where: dict[str, Any] = {}
        if symbol:
            where["symbol"] = symbol.strip()
        if action:
            where["action"] = action.strip().upper()

        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_logs",
                where=where or None,
                order_by="id DESC",
                limit=limit,
            )

        entries: list[DataManagerLogEntry] = []
        for r in rows:
            ts = str(r.get("timestamp_utc", ""))
            sym = r.get("symbol")
            msg = str(r.get("message", ""))
            act = str(r.get("action", ""))
            sqx_line = f"{ts} - {sym or 'SYSTEM'} - {msg}"
            raw_details = r.get("details", "{}")
            det: dict[str, Any] = {}
            if isinstance(raw_details, str) and raw_details.strip():
                try:
                    det = json.loads(raw_details)
                except json.JSONDecodeError, ValueError:
                    det = {}
            elif isinstance(raw_details, dict):
                det = raw_details

            entries.append(
                DataManagerLogEntry(
                    id=int(r.get("id", 0)),
                    timestamp_utc=ts,
                    symbol=str(sym) if sym else None,
                    action=act,
                    message=msg,
                    sqx_line=sqx_line,
                    details=det,
                )
            )
        return entries

    def clear_logs(self, symbol: str | None = None) -> dict[str, Any]:
        """Clear audit logs globally or for a specific symbol."""
        clean_symbol = symbol.strip() if symbol else None
        where_clause: dict[str, Any] = {"symbol": clean_symbol} if clean_symbol else {}

        with resolve_connection(self.db_path) as conn:
            deleted_count = delete_rows(conn, "datamgr_logs", where=where_clause)

        logger.info(
            "%s: Cleared %d audit log rows (symbol=%s)",
            CLEAR_FR,
            deleted_count,
            clean_symbol,
            extra={
                "fr_id": CLEAR_FR,
                "deleted_count": deleted_count,
                "symbol": clean_symbol,
            },
        )
        return {"cleared_count": deleted_count, "symbol": clean_symbol}

    def record_operation(
        self,
        symbol: str,
        operation: str,
        *,
        status: str = "SUCCESS",
        message: str = "",
        rows_affected: int = 0,
        duration_ms: float = 0.0,
        details: Mapping[str, Any] | None = None,
    ) -> OperationLogEntry:
        """Record an operation in `datamgr_operation_log`."""
        now_utc = datetime.now(UTC)
        timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        clean_symbol = symbol.strip()
        details_dict: dict[str, Any] = dict(details) if details else {}

        meta_json = json.dumps(
            {
                "rows_affected": rows_affected,
                "duration_ms": duration_ms,
                "details": details_dict,
            }
        )
        combined_message = f"{meta_json}::{message}"

        with resolve_connection(self.db_path) as conn:
            inserted = insert_row(
                conn,
                "datamgr_operation_log",
                {
                    "timestamp_utc": timestamp_str,
                    "symbol": clean_symbol,
                    "operation": operation.upper(),
                    "status": status.upper(),
                    "message": combined_message,
                },
            )
            insert_row(
                conn,
                "datamgr_logs",
                {
                    "timestamp_utc": timestamp_str,
                    "action": f"OP_{operation.upper()}",
                    "message": message or f"Operation {operation.upper()}",
                    "symbol": clean_symbol,
                    "details": json.dumps(
                        {
                            "rows_affected": rows_affected,
                            "duration_ms": duration_ms,
                            **details_dict,
                        }
                    ),
                },
            )

        op_id = int(inserted)
        entry = OperationLogEntry(
            id=op_id,
            timestamp_utc=timestamp_str,
            symbol=clean_symbol,
            operation=operation.upper(),
            status=status.upper(),
            rows_affected=rows_affected,
            duration_ms=duration_ms,
            message=message,
            details=details_dict,
        )
        logger.info(
            "%s: Recorded operation id=%d op=%s status=%s symbol=%s",
            OPERATION_TRACKING_FR,
            op_id,
            entry.operation,
            entry.status,
            entry.symbol,
            extra={
                "fr_id": OPERATION_TRACKING_FR,
                "op_id": op_id,
                "operation": entry.operation,
                "status": entry.status,
            },
        )
        return entry

    def list_operations(
        self,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[OperationLogEntry]:
        """List operation records from `datamgr_operation_log`."""
        where: dict[str, Any] = {}
        if symbol:
            where["symbol"] = symbol.strip()

        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_operation_log",
                where=where or None,
                order_by="id DESC",
                limit=limit,
            )

        entries: list[OperationLogEntry] = []
        for r in rows:
            raw_msg = str(r.get("message", ""))
            parsed_rows = 0
            parsed_duration = 0.0
            parsed_details: dict[str, Any] = {}
            actual_msg = raw_msg

            if "::" in raw_msg:
                meta_part, actual_msg = raw_msg.split("::", maxsplit=1)
                try:
                    meta_dict = json.loads(meta_part)
                    if isinstance(meta_dict, dict):
                        parsed_rows = int(meta_dict.get("rows_affected", 0))
                        parsed_duration = float(meta_dict.get("duration_ms", 0.0))
                        parsed_details = meta_dict.get("details", {})
                except ValueError, TypeError, json.JSONDecodeError:
                    pass

            entries.append(
                OperationLogEntry(
                    id=int(r.get("id", 0)),
                    timestamp_utc=str(r.get("timestamp_utc", "")),
                    symbol=str(r.get("symbol", "")),
                    operation=str(r.get("operation", "")),
                    status=str(r.get("status", "")),
                    rows_affected=parsed_rows,
                    duration_ms=parsed_duration,
                    message=actual_msg,
                    details=parsed_details,
                )
            )
        return entries


def main() -> None:
    """Execute real-usage demonstration of DataManagerLogService."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        db_file = Path(temp_dir) / "test_log.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        service = DataManagerLogService(db_path=db_file)
        entry = service.append_log(
            action="IMPORT",
            message="Imported EURUSD M1 bars (10,000 records)",
            symbol="EURUSD",
            details={"bars": 10000},
        )
        print(f"Appended log: {entry.sqx_line}")

        logs = service.list_logs(symbol="EURUSD")
        print(f"Retrieved {len(logs)} log entries")

        op = service.record_operation(
            symbol="EURUSD",
            operation="IMPORT",
            status="SUCCESS",
            message="Parquet bars persisted",
            rows_affected=10000,
            duration_ms=124.5,
        )
        print(f"Recorded operation: {op.operation} status={op.status}")

        cleared = service.clear_logs(symbol="EURUSD")
        print(f"Cleared logs result: {cleared}")


if __name__ == "__main__":
    main()
