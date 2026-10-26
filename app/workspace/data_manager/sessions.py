"""Data Manager trading sessions catalog service.

Description:
    Provides trading session schedules, regular trading hours, and holiday
    calendars for the Data Manager workspace, reading catalog entries from
    the authoritative SQLite database (datamgr_sessions table).

Purpose:
    FEAT-DATAMGR-SESSIONS: Data Manager trading sessions catalog service.

Key Capabilities:
    - FR-DATAMGR-SESSIONS-CATALOG: List, add, edit, clone, and delete sessions.
    - Import and export structured session calendars as JSON.

Python API Usage:
    ```python
    from app.workspace.data_manager.sessions import Sessions

    sessions_svc = Sessions()
    sessions = sessions_svc.list()
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.sessions
    ```
"""

from __future__ import annotations

import json
import re
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.include.contracts import SessionWindow, TradingHoliday, TradingSession

__all__ = [
    "SessionWindow",
    "Sessions",
    "TradingHoliday",
    "TradingSession",
]

logger = get_logger(__name__)
persistence = HostPersistence()

MAX_SHIFT_MINUTES = 1440
MAX_WINDOWS = 100
MAX_HOLIDAYS = 1000

SESSIONS_CATALOG_FR = "FR-DATAMGR-SESSIONS-CATALOG"


class _SessionError(ValueError):
    def __init__(self, message: str, code: ErrorCode = ErrorCode.VALIDATION) -> None:
        super().__init__(message)
        self.code = code


def _records(response: dict[str, Any]) -> list[dict[str, Any]]:
    if not response["success"]:
        error = response.get("error") or {}
        raise _SessionError(
            response.get("message") or "Session storage failed",
            ErrorCode(error.get("code", "internal")),
        )
    return cast("list[dict[str, Any]]", response["data"]["records"])


def _names(names: str | Sequence[str]) -> list[str]:
    values = [names] if isinstance(names, str) else list(names)
    if not values or any(not isinstance(v, str) or not v.strip() for v in values):
        raise _SessionError("At least one non-empty session name is required")
    return list(dict.fromkeys(v.strip() for v in values))


def _validate_window(record: SessionWindow) -> None:
    days = {
        "mon",
        "monday",
        "tue",
        "tuesday",
        "wed",
        "wednesday",
        "thu",
        "thursday",
        "fri",
        "friday",
        "sat",
        "saturday",
        "sun",
        "sunday",
    }
    if any(
        not isinstance(d, str) or d.lower() not in days
        for d in (record.day_from, record.day_to)
    ):
        raise _SessionError("Invalid session weekday")
    for clock in (record.start_time, record.end_time):
        if not isinstance(clock, str) or not re.fullmatch(
            r"(?:[01][0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?", clock
        ):
            raise _SessionError("Session times must use HH:MM (00:00-23:59)")
    if (
        not isinstance(record.eod, bool)
        or not isinstance(record.session_type, str)
        or not record.session_type.strip()
    ):
        raise _SessionError("Invalid session window flags")
    if record.day_of_week is not None and (
        type(record.day_of_week) is not int or record.day_of_week not in range(7)
    ):
        raise _SessionError("day_of_week must be 0-6")


def _validate_holiday(record: TradingHoliday) -> None:
    try:
        parsed = date.fromisoformat(record.date_str)
    except (ValueError, TypeError) as error:
        raise _SessionError("Holiday dates must use YYYY-MM-DD") from error
    if parsed.isoformat() != record.date_str:
        raise _SessionError("Holiday dates must use YYYY-MM-DD")
    if not isinstance(record.description, str):
        raise _SessionError("Holiday description must be a string")


def _calendar_json(items: Any, kind: type[SessionWindow | TradingHoliday]) -> str:
    if not isinstance(items, (list, tuple)):
        raise _SessionError("Calendar entries must be a list")
    maximum = MAX_WINDOWS if kind is SessionWindow else MAX_HOLIDAYS
    if len(items) > maximum:
        raise _SessionError(f"At most {maximum} calendar entries are allowed")
    normalized = []
    for item in items:
        values = asdict(item) if isinstance(item, kind) else item
        if not isinstance(values, dict):
            raise _SessionError("Each calendar entry must be an object")
        try:
            record = kind(**values)
        except TypeError as error:
            raise _SessionError("Invalid calendar entry fields") from error
        if isinstance(record, SessionWindow):
            _validate_window(record)
            record = replace(
                record,
                day_from=record.day_from[:3].title(),
                day_to=record.day_to[:3].title(),
            )
            if record.day_of_week is not None:
                record = replace(
                    record,
                    day_of_week=("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun").index(
                        record.day_from
                    ),
                )
        else:
            _validate_holiday(record)
        normalized.append(asdict(record))
    if kind is TradingHoliday and len({item["date_str"] for item in normalized}) != len(
        normalized
    ):
        raise _SessionError("Duplicate holiday dates")
    return json.dumps(normalized, allow_nan=False)


def _row(values: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "name",
        "description",
        "timezone",
        "windows",
        "holidays",
        "is_default",
        "broker_id",
    }
    unknown = values.keys() - allowed
    if unknown:
        raise _SessionError(f"Unknown session fields: {', '.join(sorted(unknown))}")
    data = dict(values)
    for field, default in (("name", ""), ("description", ""), ("timezone", "UTC")):
        value = data.get(field, default)
        if not isinstance(value, str):
            raise _SessionError(f"{field} must be a string")
        data[field] = value.strip() if field != "description" else value
    if not data["name"]:
        raise _SessionError("Session name is required")
    try:
        ZoneInfo(data["timezone"])
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise _SessionError("Unknown session timezone") from error
    for field, kind in (("windows", SessionWindow), ("holidays", TradingHoliday)):
        data[field + "_json"] = _calendar_json(data.pop(field, []), kind)
    if not isinstance(data.get("is_default", False), bool):
        raise _SessionError("is_default must be a boolean")
    data["is_default"] = int(data.get("is_default", False))
    if type(data.get("broker_id", -1)) is not int:
        raise _SessionError("broker_id must be an integer")
    data.setdefault("broker_id", -1)
    return data


def _lookup(gateway: HostPersistence, name: str) -> dict[str, Any]:
    rows = _records(
        gateway.read_records("datamgr_sessions", filters={"name": name}, limit=1)
    )
    if not rows:
        raise _SessionError(f"Session '{name}' not found", ErrorCode.NOT_FOUND)
    return rows[0]


def _shift_window(window: dict[str, Any], minutes: int) -> dict[str, Any]:
    days = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    result = dict(window)
    for day_key, time_key in (("day_from", "start_time"), ("day_to", "end_time")):
        parts = list(map(int, window[time_key].split(":")))
        seconds = parts[2] if ":" in window[time_key][3:] else 0
        clock = (
            days.index(window[day_key]) * 86400
            + parts[0] * 3600
            + parts[1] * 60
            + seconds
            + minutes * 60
        ) % 604800
        result[day_key] = days[clock // 86400]
        result[time_key] = f"{clock % 86400 // 3600:02}:{clock % 3600 // 60:02}"
        if ":" in window[time_key][3:]:
            result[time_key] += f":{clock % 60:02}"
    if result.get("day_of_week") is not None:
        result["day_of_week"] = days.index(result["day_from"])
    return result


def _editable(row: Mapping[str, Any]) -> dict[str, Any]:
    data = TradingSession.from_dict(row).to_dict()
    data.pop("id")
    data.pop("broker_name")
    return data


class Sessions:
    """Service providing trading session calendar catalog presentation."""

    def __init__(self, gateway: HostPersistence | None = None) -> None:
        self.gateway = gateway if gateway is not None else persistence

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


if __name__ == "__main__":
    from app.workspace.data_manager.cli import format_session_table

    sessions_svc = Sessions()
    response = sessions_svc.list()
    if response["success"]:
        print(format_session_table(response))
    else:
        print(f"Failed: {response['message']}")
