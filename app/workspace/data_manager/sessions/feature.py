"""Data Manager trading sessions catalog service.

Description:
    Provides trading session schedules, regular trading hours, and holiday
    calendars for the Data Manager workspace, reading catalog entries from
    the authoritative SQLite database (datamgr_sessions table).
"""

from __future__ import annotations

import json
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from app.core.data.contracts import TradingSession
from app.core.host.persistence import HostPersistence
from app.core.lib.responses import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

from ._helpers import (
    MAX_SHIFT_MINUTES,
    SESSIONS_CATALOG_FR,
    _editable,
    _lookup,
    _names,
    _records,
    _row,
    _SessionError,
    _shift_window,
    logger,
    persistence,
)

__all__ = ["Sessions"]


class Sessions:
    """Service providing trading session calendar catalog presentation."""

    def __init__(self, gateway: HostPersistence | None = None) -> None:
        import sys

        sessions_pkg = sys.modules.get(__package__)
        self.gateway = (
            gateway
            if gateway is not None
            else (
                getattr(sessions_pkg, "persistence", persistence)
                if sessions_pkg
                else persistence
            )
        )

    def _read_sessions(
        self, gateway: HostPersistence | None = None
    ) -> list[dict[str, Any]]:
        """Read all session catalog items from the datamgr_sessions table."""
        gateway = gateway if gateway is not None else self.gateway
        rows: list[dict[str, Any]] = []
        offset: int | None = 0
        while offset is not None:
            response = gateway.read_records(
                "datamgr_sessions", limit=1000, offset=offset
            )
            if not response["success"]:
                err = response.get("error") or {}
                msg = (
                    err.get("message")
                    or response.get("message")
                    or "Database read failure"
                )
                raise RuntimeError(msg)
            data = response.get("data") or {}
            rows.extend(data.get("records") or [])
            pagination = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return rows

    def _run(self, operation: str, action: Callable[[], Any]) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            data = action()
            return StandardResponse.success(
                message=f"Completed sessions.{operation}",
                metadata=ResponseMetadata(
                    operation=f"sessions.{operation}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data=data,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            return StandardResponse.failure(
                message=str(error) or "Session operation failed",
                metadata=ResponseMetadata(
                    operation=f"sessions.{operation}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=error.code
                    if isinstance(error, _SessionError)
                    else ErrorCode.INTERNAL,
                    message=str(error) or "Session operation failed",
                ),
            )

    def add(self, name: str = "", **kwargs: Any) -> dict[str, Any]:
        """Create a named session with structured windows and holidays."""

        def action() -> TradingSession:
            row = _row({"name": name, **kwargs})
            records = _records(self.gateway.create_records("datamgr_sessions", row))
            return TradingSession.from_dict(records[0])

        return self._run("add", action)

    def edit(
        self,
        sessions: str | Sequence[str],
        updates: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Atomically edit sessions; name changes require one target."""

        def action() -> list[TradingSession]:
            names = _names(sessions)
            changes = {**(updates or {}), **kwargs}
            if not changes:
                raise _SessionError("At least one field to edit is required")
            if "name" in changes and len(names) != 1:
                raise _SessionError("Rename requires exactly one session")
            result: list[TradingSession] = []
            with self.gateway.transaction() as tx:
                for name in names:
                    row = _row({**_editable(_lookup(tx, name)), **changes})
                    records = _records(
                        tx.update_record(
                            "datamgr_sessions", row, filters={"name": name}
                        )
                    )
                    result.append(TradingSession.from_dict(records[0]))
            return result

        return self._run("edit", action)

    def clone(self, session: str, new_name: str, minutes: int = 0) -> dict[str, Any]:
        """Copy a session into a new identity, preserving its schedule."""

        def action() -> TradingSession:
            name = _names(session)[0]
            if type(minutes) is not int or abs(minutes) > MAX_SHIFT_MINUTES:
                raise _SessionError("Shift requires integer minutes within +/-1440")
            with self.gateway.transaction() as tx:
                row = _row({**_editable(_lookup(tx, name)), "name": new_name})
                if minutes:
                    windows = json.loads(row["windows_json"])
                    row["windows_json"] = json.dumps(
                        [_shift_window(w, minutes) for w in windows]
                    )
                records = _records(tx.create_records("datamgr_sessions", row))
                return TradingSession.from_dict(records[0])

        return self._run("clone", action)

    def delete(self, sessions: str | Sequence[str]) -> dict[str, Any]:
        """Delete one or more named sessions atomically."""

        def action() -> list[TradingSession]:
            names = _names(sessions)
            result: list[TradingSession] = []
            with self.gateway.transaction() as tx:
                for name in names:
                    _lookup(tx, name)
                    records = _records(
                        tx.delete_record("datamgr_sessions", filters={"name": name})
                    )
                    result.extend(TradingSession.from_dict(row) for row in records)
            return result

        return self._run("delete", action)

    def load(self, json_path: str | Path) -> dict[str, Any]:
        """Atomically import a JSON array of sessions, rejecting duplicate names."""

        def action() -> list[TradingSession]:
            try:
                data = json.loads(Path(json_path).read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError as error:
                raise _SessionError("Invalid sessions JSON") from error
            if not isinstance(data, list) or any(
                not isinstance(item, dict) for item in data
            ):
                raise _SessionError("Sessions JSON must be an array of objects")
            rows = []
            for item in data:
                # Exported identifiers are local to the source database.
                values = {
                    k: v for k, v in item.items() if k not in {"id", "broker_name"}
                }
                rows.append(_row(values))
            result: list[TradingSession] = []
            with self.gateway.transaction() as tx:
                for start in range(0, len(rows), 1000):
                    records = _records(
                        tx.create_records(
                            "datamgr_sessions", rows[start : start + 1000]
                        )
                    )
                    result.extend(TradingSession.from_dict(row) for row in records)
            return result

        return self._run("load", action)

    def save(self, json_path: str | Path) -> dict[str, Any]:
        """Export all sessions to a UTF-8 JSON array using atomic replacement."""

        def action() -> dict[str, Any]:
            with self.gateway.transaction() as tx:
                sessions = self._read_sessions(tx)
            data = [_editable(row) for row in sessions]
            target = Path(json_path)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=target.parent,
                    prefix=f".{target.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as stream:
                    temporary = Path(stream.name)
                    json.dump(
                        data, stream, ensure_ascii=False, indent=2, allow_nan=False
                    )
                    stream.write("\n")
                Path(temporary).replace(target)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            return {"path": str(target), "count": len(data)}

        return self._run("save", action)

    def list(self) -> dict[str, Any]:
        """Retrieve trading session catalog items wrapped in StandardResponse."""
        start = time.perf_counter()
        try:
            rows = self._read_sessions()
            sessions = [TradingSession.from_dict(r) for r in rows]

            logger.debug(
                "%s: Retrieved %d trading session catalog items",
                SESSIONS_CATALOG_FR,
                len(sessions),
                extra={"fr_id": SESSIONS_CATALOG_FR, "count": len(sessions)},
            )
            return StandardResponse.success(
                message=f"Retrieved {len(sessions)} trading session catalog items",
                metadata=ResponseMetadata(
                    operation="sessions.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data=sessions,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("%s: Failed to list sessions", SESSIONS_CATALOG_FR)
            return StandardResponse.failure(
                message=str(error) or "Failed to retrieve sessions",
                metadata=ResponseMetadata(
                    operation="sessions.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error) or "Internal error listing sessions",
                ),
            )
