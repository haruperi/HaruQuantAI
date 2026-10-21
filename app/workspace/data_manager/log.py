"""Real-time WebSocket log viewer and operation tracker for Data Manager.

Description:
    Provides audit trail and live operation logging for download, import, and
    export workflows in Data Manager through HostPersistence and EventBus.

Purpose:
    FEAT-DATAMGR-LOG: Real-time WebSocket log viewer for data operations.

Key Capabilities:
    - FR-DATAMGR-LOG-STREAM: Live operation logs (DataLog.data_log -> INFO).
    - FR-DATAMGR-LOG-CLEAR: Log reset and progress clear (DataLog.clear_log -> INFO).

Python API Usage:
    ```python
    from app.workspace.data_manager.log import DataLog, DataLogCLI

    print(DataLogCLI.format_log_entries(DataLog().data_log(limit=100)))
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.log
    ```
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.host.events import EventBus
from app.host.logging import get_logger
from app.host.persistence import HostPersistence

__all__ = ["DataLog", "DataLogCLI"]

logger = get_logger(__name__)
STREAM_FR = "FR-DATAMGR-LOG-STREAM"
CLEAR_FR = "FR-DATAMGR-LOG-CLEAR"
_TEXT_KEYS = ("timestamp_utc", "symbol", "message", "details")


@dataclass(frozen=True)
class _Config:
    """Internal bounds and channel configuration for Data Manager logs."""

    default_limit: int = 100
    max_limit: int = 500
    channel: str = "logs"


def _normalize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    act = str(row.get("action") or row.get("operation") or "INFO").strip()
    low = str(row.get("status") or ("error" if "ERR" in act else "info")).lower()
    raw_pct = row.get("progress", -1 if low in ("error", "failed") else 0)
    pct = int(raw_pct) if isinstance(raw_pct, int) else 0
    base = {k: str(row.get(k) or "") for k in _TEXT_KEYS}
    meta = {"id": int(row.get("id") or 0), "action": act, "status": low}
    err, cancel = low in ("error", "failed") or pct < 0, low in ("running", "paused")
    return {**meta, "progress": pct, "is_error": err, "cancellable": cancel, **base}


class DataLog:
    """Service managing persisted data operation logs and WebSocket streaming."""

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        """Initialize log service with optional host EventBus."""
        self._event_bus = event_bus

    def data_log(
        self, limit: int = 100, entry: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Stream and return recent data download, import, and export log records."""
        if entry is not None:
            return [self._record_entry(entry)]
        if isinstance(limit, bool) or not (1 <= limit <= _Config.max_limit):
            logger.warning("%s: Invalid limit", STREAM_FR, extra={"fr_id": STREAM_FR})
            raise ValueError(f"limit must be an integer in 1..{_Config.max_limit}.")
        tbl = "datamgr_logs"
        rows = HostPersistence.read_records(tbl, limit=limit, order_by="id DESC")
        entries = [_normalize_row(row) for row in reversed(rows)]
        if self._event_bus is not None:
            res = {"entries": entries, "count": len(entries)}
            self._event_bus.publish(_Config.channel, "datamgr.log.stream", res)
        logger.info("%s: Streamed logs", STREAM_FR, extra={"fr_id": STREAM_FR})
        return entries

    def clear_log(self) -> dict[str, Any]:
        """Clear persisted data operation logs and reset active progress state."""
        audit = HostPersistence.read_records("datamgr_logs", limit=0)
        ops = HostPersistence.read_records("datamgr_operation_log", limit=0)
        for tbl, rows in (("datamgr_logs", audit), ("datamgr_operation_log", ops)):
            for row in rows:
                HostPersistence.delete_record(tbl, {"id": row["id"]})
        result = {"cleared": len(audit) + len(ops), "status": "idle", "progress": 0}
        if self._event_bus is not None:
            self._event_bus.publish(_Config.channel, "datamgr.log.cleared", result)
        logger.info("%s: Cleared logs", CLEAR_FR, extra={"fr_id": CLEAR_FR})
        return result

    def _record_entry(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Persist a new operation log entry and publish it to WebSocket listeners."""
        act = str(payload.get("action") or payload.get("operation") or "").strip()
        msg = str(payload.get("message") or "").strip()
        if not act or not msg:
            logger.warning("%s: Invalid entry", STREAM_FR, extra={"fr_id": STREAM_FR})
            raise ValueError("Log entry requires non-empty action and message.")
        ts = str(payload.get("timestamp_utc") or datetime.now(UTC).isoformat())
        sym = str(payload.get("symbol") or "").strip()
        det = str(payload.get("details") or "").strip()
        st = str(payload.get("status") or "info").strip().lower()
        audit_rec = dict(zip(_TEXT_KEYS, (ts, sym, msg, det), strict=True))
        audit_rec["action"] = act
        created = HostPersistence.create_record("datamgr_logs", audit_rec)["record"]
        if sym or st != "info":
            op_keys = ("timestamp_utc", "symbol", "operation", "status", "message")
            op_rec = dict(zip(op_keys, (ts, sym or "ALL", act, st, msg), strict=True))
            HostPersistence.create_record("datamgr_operation_log", op_rec)
        entry = _normalize_row({**created, **payload, "timestamp_utc": ts})
        if self._event_bus is not None:
            self._event_bus.publish(_Config.channel, "datamgr.log.entry", entry)
        logger.info("%s: Recorded log entry", STREAM_FR, extra={"fr_id": STREAM_FR})
        return entry


class DataLogCLI:
    """CLI presentation adapter for Data Manager operation logs."""

    @staticmethod
    def format_log_entries(entries: Sequence[Mapping[str, Any]]) -> str:
        """Format log entries into a human-readable summary."""
        lines = [f"=== Data Manager Log ({len(entries)} entries) ==="]
        for item in entries:
            sym = f" [{item['symbol']}]" if item.get("symbol") else ""
            ts, act = item.get("timestamp_utc", ""), item.get("action", "")
            lines.append(f"{ts} {act}{sym}: {item.get('message', '')}")
        return "\n".join(lines)


def main() -> None:
    """Execute standalone DataLog verification."""
    logger.info("%s", DataLogCLI.format_log_entries(DataLog().data_log(limit=10)))


if __name__ == "__main__":
    main()
