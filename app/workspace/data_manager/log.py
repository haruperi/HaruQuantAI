"""Data Manager audit logging, historical activity, and operation traces.

Description:
    Provides structured activity logging and audit trail persistence for Data
    Manager operations (file ingestion, provider downloads, catalog mutations,
    and quality audits) within the Data Manager workspace, mirroring SQX DataManagerLog.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Track and query Data Manager operational audit logs.

Key Capabilities:
    - FR-WORKSPACE-DATAMGR-LOG: Record and query structured activity log entries.
      Associated: `[DataManagerLogService.log_activity()]`,
      `[DataManagerLogService.list_logs()]`
      Logging: Emits INFO on new activity entry recordings.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.log import DataManagerLogService, LogEntry

    db = DatabaseManager(":memory:")
    db.initialize()
    log_service = DataManagerLogService(db)
    log_service.log_activity("INGEST", "Imported 1000 bars for EURUSD", symbol="EURUSD")
    entries = log_service.list_logs(limit=10)
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.log --limit 20
    ```
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager

logger = get_logger(__name__)


class LogEntry(BaseModel):
    """Single Data Manager workspace activity log entry."""

    model_config = ConfigDict(frozen=True)

    timestamp_utc: str = Field(description="ISO 8601 UTC timestamp")
    action: str = Field(description="Action verb (e.g. INGEST, DOWNLOAD, DELETE)")
    message: str = Field(description="Human-readable event message")
    symbol: str | None = Field(default=None, description="Associated symbol")
    details: dict[str, Any] = Field(default_factory=dict, description="Metadata")


_MAX_LOG_ENTRIES: int = 1000


class DataManagerLogService:
    """Service managing Data Manager operational logs and history."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize log service with DatabaseManager."""
        self._db = db
        self._memory_entries: list[LogEntry] = []

    def log_activity(
        self,
        action: str,
        message: str,
        symbol: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> LogEntry:
        """Record an activity event into the workspace audit log.

        Fires FR-WORKSPACE-DATAMGR-LOG.
        """
        entry = LogEntry(
            timestamp_utc=datetime.now(UTC).isoformat(),
            action=action.upper(),
            message=message,
            symbol=symbol.upper() if symbol else None,
            details=details or {},
        )
        self._memory_entries.append(entry)
        if len(self._memory_entries) > _MAX_LOG_ENTRIES:
            self._memory_entries.pop(0)

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
    ) -> list[LogEntry]:
        """Query logged activity entries matching optional filters."""
        results = self._memory_entries
        if symbol:
            clean_sym = symbol.strip().upper()
            results = [e for e in results if e.symbol == clean_sym]
        if action:
            clean_act = action.strip().upper()
            results = [e for e in results if e.action == clean_act]
        return list(reversed(results[-limit:]))


def main() -> int:
    """CLI tool for querying Data Manager logs."""
    parser = argparse.ArgumentParser(description="Query Data Manager logs")
    parser.add_argument("--limit", type=int, default=20, help="Max entries to show")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = DataManagerLogService(db)
    entries = service.list_logs(limit=args.limit)
    print(f"Data Manager Audit Logs ({len(entries)} entries):")
    for e in entries:
        print(f"  {e.timestamp_utc} [{e.action:8}] {e.message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
