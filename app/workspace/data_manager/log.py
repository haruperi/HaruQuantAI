"""Data Manager audit logging, historical activity, and operation traces.

Description:
    Provides structured activity logging, download progress streaming, and
    audit trail persistence for Data Manager operations (file ingestion,
    provider downloads, catalog mutations, and quality audits) within the
    Data Manager workspace, mirroring SQX DataManagerLog.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Track and persist Data Manager operational audit logs.

Key Capabilities:
    - FR-WORKSPACE-DATAMGR-LOG: Record, query, and clear structured activity logs.
      Associated: `[DataManagerLogService.log_activity()]`,
      `[DataManagerLogService.list_logs()]`, `[DataManagerLogService.clear_logs()]`
      Logging: Emits INFO on new activity entry recordings and log clear operations.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.log import DataManagerLogService, LogEntry

    db = DatabaseManager(":memory:")
    db.initialize()
    log_service = DataManagerLogService(db)
    log_service.log_activity("INGEST", "Imported 1000 bars for EURUSD", symbol="EURUSD")
    entries = log_service.list_logs(limit=10)
    cleared = log_service.clear_logs()
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.log --limit 20
    python -m app.workspace.data_manager.log --clear
    ```
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager, PersistenceError

logger = get_logger(__name__)


class LogEntry(BaseModel):
    """Single Data Manager workspace activity log entry with SQX parity."""

    model_config = ConfigDict(frozen=True)

    timestamp_utc: str = Field(description="ISO 8601 UTC timestamp")
    action: str = Field(description="Action verb (e.g. INGEST, DOWNLOAD, DELETE)")
    message: str = Field(description="Human-readable event message")
    symbol: str | None = Field(default=None, description="Associated symbol")
    details: dict[str, Any] = Field(default_factory=dict, description="Metadata")
    key: str | None = Field(
        default=None, description="Progress task or symbol key matching SQX"
    )
    pct: float | None = Field(
        default=None, description="Progress percentage 0-100 matching SQX"
    )
    log_str: str | None = Field(
        default=None, description="Formatted SQX progress detail"
    )

    def format_sqx_line(self) -> str:
        """Format entry matching SQX DMDataLogCtrl layout: YYYY.M.D HH:mm key logStr."""
        try:
            dt = datetime.fromisoformat(self.timestamp_utc)
            time_str = f"{dt.year}.{dt.month}.{dt.day} {dt.strftime('%H:%M')}"
        except ValueError, TypeError:
            time_str = self.timestamp_utc[:16]

        target_key = self.key or self.symbol or ""
        key_part = f" {target_key}" if target_key else ""
        content = self.log_str or self.message
        return f"{time_str}{key_part} {content}".strip()


_MAX_LOG_ENTRIES: int = 1000


class DataManagerLogService:
    """Service managing Data Manager operational logs and history with persistence."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """Initialize log service with optional DatabaseManager."""
        self._db = db
        self._memory_entries: list[LogEntry] = []

    def log_activity(
        self,
        action: str,
        message: str,
        symbol: str | None = None,
        details: dict[str, Any] | None = None,
        *,
        key: str | None = None,
        pct: float | None = None,
        log_str: str | None = None,
    ) -> LogEntry:
        """Record an activity event into the workspace audit log and database.

        Fires FR-WORKSPACE-DATAMGR-LOG.
        """
        clean_action = action.strip().upper()
        clean_symbol = symbol.strip().upper() if symbol else None
        clean_key = key.strip() if key else clean_symbol
        now_iso = datetime.now(UTC).isoformat()
        metadata = dict(details or {})

        if key is not None:
            metadata["key"] = clean_key
        if pct is not None:
            metadata["pct"] = pct
        if log_str is not None:
            metadata["log_str"] = log_str

        entry = LogEntry(
            timestamp_utc=now_iso,
            action=clean_action,
            message=message,
            symbol=clean_symbol,
            details=metadata,
            key=clean_key,
            pct=pct,
            log_str=log_str,
        )

        self._memory_entries.append(entry)
        if len(self._memory_entries) > _MAX_LOG_ENTRIES:
            self._memory_entries.pop(0)

        if self._db is not None:
            try:
                self._db.logs.create(
                    {
                        "timestamp_utc": entry.timestamp_utc,
                        "action": entry.action,
                        "message": entry.message,
                        "symbol": entry.symbol,
                        "details": entry.details,
                    }
                )
            except (PersistenceError, OSError, ValueError) as err:
                logger.warning(
                    "FR-WORKSPACE-DATAMGR-LOG: Failed to persist log entry: %s",
                    err,
                    extra={"fr_id": "FR-WORKSPACE-DATAMGR-LOG", "error": str(err)},
                )

        logger.info(
            "FR-WORKSPACE-DATAMGR-LOG: [%s] %s (%s)",
            entry.action,
            entry.message,
            entry.symbol or "-",
            extra={
                "action": entry.action,
                "log_message": entry.message,
                "symbol": entry.symbol,
                "fr_id": "FR-WORKSPACE-DATAMGR-LOG",
            },
        )
        return entry

    def list_logs(
        self,
        symbol: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LogEntry]:
        """Query logged activity entries matching optional filters."""
        clean_sym = symbol.strip().upper() if symbol else None
        clean_act = action.strip().upper() if action else None

        if self._db is not None:
            try:
                db_rows = self._db.logs.list_logs(
                    symbol=clean_sym,
                    action=clean_act,
                    limit=limit,
                    offset=offset,
                )
                return [
                    LogEntry(
                        timestamp_utc=row["timestamp_utc"],
                        action=row["action"],
                        message=row["message"],
                        symbol=row["symbol"],
                        details=row.get("details", {}),
                        key=row.get("details", {}).get("key") or row["symbol"],
                        pct=row.get("details", {}).get("pct"),
                        log_str=row.get("details", {}).get("log_str"),
                    )
                    for row in db_rows
                ]
            except (PersistenceError, OSError, ValueError) as err:
                logger.warning(
                    "FR-WORKSPACE-DATAMGR-LOG: Database query failed, using memory: %s",
                    err,
                    extra={"fr_id": "FR-WORKSPACE-DATAMGR-LOG", "error": str(err)},
                )

        results = self._memory_entries
        if clean_sym:
            results = [e for e in results if e.symbol == clean_sym]
        if clean_act:
            results = [e for e in results if e.action == clean_act]
        sliced = list(reversed(results))
        return sliced[offset : offset + limit]

    def clear_logs(self, symbol: str | None = None) -> int:
        """Delete log entries matching optional symbol filter.

        Fires FR-WORKSPACE-DATAMGR-LOG.
        """
        clean_sym = symbol.strip().upper() if symbol else None
        cleared_count = 0

        if clean_sym:
            initial = len(self._memory_entries)
            self._memory_entries = [
                e for e in self._memory_entries if e.symbol != clean_sym
            ]
            cleared_count = initial - len(self._memory_entries)
        else:
            cleared_count = len(self._memory_entries)
            self._memory_entries = []

        if self._db is not None:
            try:
                db_cleared = self._db.logs.clear(symbol=clean_sym)
                cleared_count = max(cleared_count, db_cleared)
            except (PersistenceError, OSError, ValueError) as err:
                logger.warning(
                    "FR-WORKSPACE-DATAMGR-LOG: Failed to clear database logs: %s",
                    err,
                    extra={"fr_id": "FR-WORKSPACE-DATAMGR-LOG", "error": str(err)},
                )

        logger.info(
            "FR-WORKSPACE-DATAMGR-LOG: Cleared %d logs (symbol=%s)",
            cleared_count,
            clean_sym or "all",
            extra={
                "action": "CLEAR",
                "cleared_count": cleared_count,
                "symbol": clean_sym,
                "fr_id": "FR-WORKSPACE-DATAMGR-LOG",
            },
        )
        return cleared_count

    def count_logs(self, symbol: str | None = None) -> int:
        """Return total count of logged entries."""
        clean_sym = symbol.strip().upper() if symbol else None
        if self._db is not None:
            try:
                return self._db.logs.count(symbol=clean_sym)
            except (PersistenceError, OSError, ValueError) as err:
                logger.debug("FR-WORKSPACE-DATAMGR-LOG: count_logs error: %s", err)
        if clean_sym:
            return sum(1 for e in self._memory_entries if e.symbol == clean_sym)
        return len(self._memory_entries)


def main() -> int:
    """CLI tool for querying and managing Data Manager logs."""
    parser = argparse.ArgumentParser(description="Query Data Manager logs")
    parser.add_argument("--limit", type=int, default=20, help="Max entries to show")
    parser.add_argument("--symbol", type=str, default=None, help="Filter by symbol")
    parser.add_argument(
        "--action", type=str, default=None, help="Filter by action verb"
    )
    parser.add_argument(
        "--clear", action="store_true", help="Clear logs instead of listing"
    )
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = DataManagerLogService(db)

    if args.clear:
        cleared = service.clear_logs(symbol=args.symbol)
        print(f"Cleared {cleared} Data Manager logs.")
        return 0

    entries = service.list_logs(
        symbol=args.symbol, action=args.action, limit=args.limit
    )
    print(f"Data Manager Audit Logs ({len(entries)} entries):")
    for e in entries:
        print(f"  {e.format_sqx_line()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
