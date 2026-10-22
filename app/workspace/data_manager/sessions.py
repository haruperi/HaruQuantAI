"""Persist recurring session profiles, intervals and holiday calendars.

Description:
    Owns configured session profiles through HostPersistence. Validates explicit
    weekly intervals and local holiday dates, copies schedules with deliberate
    wall-clock shifts and saves reusable profiles without browser fallbacks.
Purpose:
    FEAT-DATAMGR-SESSIONS: Trading session profiles and reusable schedules.
Key Capabilities:
    - FR-DATAMGR-SESS-LIST: Profiles [Sessions.sessions()] (INFO).
    - FR-DATAMGR-SESS-CLONE: Create/copy/delete [Sessions.clone_session()] (INFO).
    - FR-DATAMGR-SESS-ELEMENT: Intervals [Sessions.session_element()] (INFO).
    - FR-DATAMGR-SESS-TEMPLATE: Save profiles [Sessions.session_template()] (INFO).
Python API Usage:
    from app.workspace.data_manager.sessions import Sessions
    profiles = Sessions().sessions()
CLI Usage:
    uv run python -m app.workspace.data_manager.sessions
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from itertools import pairwise
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.services.include.bar_time import DateTime

__all__ = ["Sessions"]

logger = get_logger(__name__)
_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_WEEK = 604800
_DAY = 86400
_TEXT_LIMIT = 8000
_MAX_OFFSET = 1440
_MAX_WINDOWS = 100
_MAX_HOLIDAYS = 1000
_ID_DIGITS = 19
_CONTROL_START = 32
_HMS_PARTS = 3
_FIELDS = frozenset(
    {
        "name",
        "description",
        "timezone",
        "windows",
        "holidays",
        "is_default",
        "broker_id",
    }
)


@dataclass(frozen=True)
class _Config:
    table: str = "datamgr_sessions"


@contextmanager
def _operation(fr_id: str) -> Iterator[None]:
    try:
        yield
    except ValueError, LookupError, FileExistsError:
        logger.warning("Session request rejected", extra={"fr_id": fr_id})
        raise
    except RuntimeError:
        logger.error("Session persistence failed", extra={"fr_id": fr_id})  # noqa: TRY400
        raise
    else:
        logger.info("Session operation completed", extra={"fr_id": fr_id})


def _text(value: Any, label: str, *, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > _TEXT_LIMIT:
        raise ValueError(f"{label} must be text of at most {_TEXT_LIMIT} characters.")
    if required and (not value.strip() or value != value.strip()):
        raise ValueError(f"{label} is required without leading or trailing spaces.")
    if any(ord(char) < _CONTROL_START for char in value):
        raise ValueError(f"{label} contains control characters.")
    return value


def _zone(value: Any) -> str:
    name = _text(value, "timezone", required=True)
    try:
        ZoneInfo(name)
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise ValueError("Choose a valid IANA timezone.") from error
    return name


def _seconds(value: Any) -> int:
    if not isinstance(value, str) or not re.fullmatch(
        r"(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", value
    ):
        raise ValueError("Times require HH:MM or HH:MM:SS in 24-hour format.")
    parts = [int(part) for part in value.split(":")]
    return (
        parts[0] * 3600 + parts[1] * 60 + (parts[2] if len(parts) == _HMS_PARTS else 0)
    )


def _window(value: Any) -> dict[str, Any]:
    required = {"day_from", "day_to", "start_time", "end_time", "eod"}
    if (
        not isinstance(value, Mapping)
        or set(value) - required - {"session_type", "day_of_week"}
        or not required <= set(value)
    ):
        raise ValueError("Invalid session window fields.")
    if value["day_from"] not in _DAYS or value["day_to"] not in _DAYS:
        raise ValueError("Choose valid session weekdays.")
    if type(value["eod"]) is not bool:
        raise ValueError("eod must be boolean.")
    dow = value.get("day_of_week")
    if dow is not None and (
        type(dow) is not int or dow != _DAYS.index(value["day_from"])
    ):
        raise ValueError("day_of_week must match the start day.")
    result = {
        **value,
        "session_type": _text(
            value.get("session_type", "Regular"), "session_type", required=True
        ),
    }
    _bounds(result)
    return result


def _bounds(window: Mapping[str, Any]) -> tuple[int, int]:
    start = _DAYS.index(window["day_from"]) * _DAY + _seconds(window["start_time"])
    end = _DAYS.index(window["day_to"]) * _DAY + _seconds(window["end_time"])
    if window["day_from"] == window["day_to"] and end <= start:
        raise ValueError(
            "End time must be later than start time; "
            "use the next day for overnight intervals."
        )
    if end < start:
        end += _WEEK
    return start, end


def _windows(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list) or len(values) > _MAX_WINDOWS:
        raise ValueError(f"Supply at most {_MAX_WINDOWS} session intervals.")
    result = [_window(value) for value in values]
    segments: list[tuple[int, int]] = []
    for window in result:
        start, end = _bounds(window)
        segments.append((start, min(end, _WEEK)))
        if end > _WEEK:
            segments.append((0, end - _WEEK))
    segments.sort()
    if any(left[1] > right[0] for left, right in pairwise(segments)):
        raise ValueError("Session intervals overlap; lunch pauses must be gaps.")
    return result


def _stored_aliases(window: dict[str, Any], warnings: list[str]) -> None:
    for alias, canonical in (("open_time", "start_time"), ("close_time", "end_time")):
        if alias not in window:
            continue
        if canonical in window and window[canonical] != window[alias]:
            raise ValueError("Conflicting stored session time aliases.")
        window[canonical] = window.pop(alias)
        warnings.append("Legacy open/close time fields were read as start/end times.")


def _stored_window(value: Any, warnings: list[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("Invalid stored session window.")  # noqa: TRY004
    window = dict(value)
    _stored_aliases(window, warnings)
    if "day_from" not in window and "day_to" not in window:
        dow = window.get("day_of_week")
        if type(dow) is not int or not 0 <= dow < len(_DAYS):
            raise ValueError("Invalid stored numeric session weekday.")
        window.update(day_from=_DAYS[dow], day_to=_DAYS[dow])
        warnings.append("Legacy numeric weekdays use 0=Monday through 6=Sunday.")
    if "eod" not in window:
        window["eod"] = False
        warnings.append("EOD was not stored; the historical default False is used.")
    return window


def _stored_windows(values: Any) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(values, list) or len(values) > _MAX_WINDOWS:
        raise ValueError("Invalid stored session intervals.")
    warnings: list[str] = []
    windows = [_stored_window(value, warnings) for value in values]
    return windows, list(dict.fromkeys(warnings))


def _holidays(values: Any) -> list[dict[str, str]]:
    if not isinstance(values, list) or len(values) > _MAX_HOLIDAYS:
        raise ValueError(f"Supply at most {_MAX_HOLIDAYS} holidays.")
    result: list[dict[str, str]] = []
    for value in values:
        if (
            not isinstance(value, Mapping)
            or set(value) - {"date_str", "description"}
            or "date_str" not in value
        ):
            raise ValueError("Invalid holiday fields.")
        day = _text(value["date_str"], "holiday date", required=True)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            raise ValueError("Holidays require YYYY-MM-DD dates.")
        date.fromisoformat(day)
        result.append(
            {
                "date_str": day,
                "description": _text(
                    value.get("description", ""), "holiday description"
                ),
            }
        )
    if len({value["date_str"] for value in result}) != len(result):
        raise ValueError("Holiday dates must be unique.")
    return result


def _shift(window: Mapping[str, Any], offset: int) -> dict[str, Any]:
    result = dict(window)
    for day_key, time_key in (("day_from", "start_time"), ("day_to", "end_time")):
        original = _DAYS.index(window[day_key]) * _DAY + _seconds(window[time_key])
        shifted = (DateTime.add_minutes(original * 1000, offset) // 1000) % _WEEK
        result[day_key] = _DAYS[shifted // _DAY]
        clock = shifted % _DAY
        result[time_key] = f"{clock // 3600:02}:{clock % 3600 // 60:02}"
        if len(window[time_key].split(":")) == _HMS_PARTS:
            result[time_key] += f":{clock % 60:02}"
    if result.get("day_of_week") is not None:
        result["day_of_week"] = _DAYS.index(result["day_from"])
    return result


class Sessions:
    """Own the saved session catalog and reusable schedule operations."""

    def __init__(self) -> None:
        self._config = _Config()

    def sessions(
        self, filters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """List every configured profile and its complete holiday calendar."""
        with _operation("FR-DATAMGR-SESS-LIST"):
            query = self._filters(filters)
            search = query.pop("search", "").casefold()
            rows = [
                self._decode(row)
                for row in HostPersistence.read_records(
                    self._config.table, query, limit=0
                )
            ]
            return sorted(
                (
                    row
                    for row in rows
                    if search in (row["name"] + " " + row["description"]).casefold()
                ),
                key=lambda row: (row["name"].casefold(), int(row["id"])),
            )

    def clone_session(
        self,
        session_id: str,
        new_name: str,
        *,
        timezone_offset: int = 0,
        delete: bool = False,
    ) -> dict[str, Any]:
        """Explicitly create a draft, copy a schedule, or delete an existing row."""
        with _operation("FR-DATAMGR-SESS-CLONE"):
            if (
                type(delete) is not bool
                or type(timezone_offset) is not int
                or abs(timezone_offset) > _MAX_OFFSET
            ):
                raise ValueError(
                    "Use boolean delete and an integer shift within +/-1440 minutes."
                )
            if delete:
                if new_name != "" or timezone_offset:
                    raise ValueError("Delete does not accept a new name or shift.")
                row = self._get(session_id)
                self._commit(
                    {
                        "op": "delete",
                        "table": self._config.table,
                        "key_columns": {"id": int(row["id"])},
                    }
                )
                return {"id": row["id"], "name": row["name"], "deleted": True}
            source = self._get(session_id) if session_id != "" else self._defaults()
            if session_id == "" and timezone_offset:
                raise ValueError("An empty draft does not accept a schedule shift.")
            values = {key: source[key] for key in _FIELDS}
            values.update(
                name=new_name,
                is_default=False,
                windows=[
                    _shift(window, timezone_offset) for window in source["windows"]
                ],
            )
            self._validate(values)
            self._unique(values["name"])
            return self._create(values)

    def session_element(
        self, session_id: str, element: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Add, replace or remove an interval after validating the full schedule."""
        with _operation("FR-DATAMGR-SESS-ELEMENT"):
            row = self._get(session_id)
            if not isinstance(element, Mapping):
                raise ValueError("Supply an interval command.")  # noqa: TRY004
            action = element.get("action")
            allowed = {
                "add": {"action", "window"},
                "update": {"action", "index", "window"},
                "remove": {"action", "index"},
            }
            if (
                not isinstance(action, str)
                or action not in allowed
                or set(element) != allowed[action]
            ):
                raise ValueError(
                    "Choose add, update or remove with the required fields."
                )
            windows = list(row["windows"])
            index = element.get("index", 0)
            if action != "add" and (
                type(index) is not int or not 0 <= index < len(windows)
            ):
                raise ValueError("Session element index is outside the saved schedule.")
            if action == "add":
                windows.append(_window(element["window"]))
            elif action == "update":
                windows[index] = _window(element["window"])
            else:
                windows.pop(index)
            row["windows"] = _windows(windows)
            return self._update(row, {"windows_json": json.dumps(row["windows"])})

    def session_template(self, template: Mapping[str, Any]) -> dict[str, Any]:
        """Create or update a reusable profile with its intervals and holidays."""
        with _operation("FR-DATAMGR-SESS-TEMPLATE"):
            if not isinstance(template, Mapping) or set(template) - _FIELDS - {"id"}:
                raise ValueError("Unknown session template fields.")
            original = self._get(template["id"]) if "id" in template else None
            if (
                original is not None
                and "name" in template
                and template["name"] != original["name"]
            ):
                raise ValueError("Session identity cannot be changed while editing.")
            values = {**(original or self._defaults()), **template}
            self._validate(values)
            if original is None:
                self._unique(values["name"])
                return self._create(values)
            return self._update(values, self._columns(values))

    def _defaults(self) -> dict[str, Any]:
        return {
            "name": "",
            "description": "",
            "timezone": "UTC",
            "windows": [],
            "holidays": [],
            "is_default": False,
            "broker_id": -1,
        }

    def _validate(self, values: dict[str, Any]) -> None:
        values["name"] = _text(values["name"], "name", required=True)
        _text(values["description"], "description")
        _zone(values["timezone"])
        if (
            type(values["is_default"]) is not bool
            or type(values["broker_id"]) is not int
        ):
            raise ValueError("Use a boolean default flag and integer broker ID.")
        broker = values["broker_id"]
        if broker not in (-1, 0) and (
            not 0 < broker < 2**63
            or not HostPersistence.read_records(
                "datamgr_broker", {"id": broker}, limit=1
            )
        ):
            raise ValueError("Choose a configured broker ID.")
        values["windows"] = _windows(values["windows"])
        values["holidays"] = _holidays(values["holidays"])

    def _decode(self, row: Mapping[str, Any]) -> dict[str, Any]:
        try:
            self._stored_flag(row["is_default"])
            windows, warnings = _stored_windows(json.loads(row["windows_json"]))
            values = {
                **row,
                "id": str(row["id"]),
                "is_default": bool(row["is_default"]),
                "windows": windows,
                "holidays": json.loads(row["holidays_json"]),
            }
            self._validate(values)
        except (ValueError, TypeError, KeyError) as error:
            raise RuntimeError("Stored session calendar is invalid.") from error
        result = {key: values[key] for key in (*_FIELDS, "id")}
        if warnings:
            result["normalization_warnings"] = warnings
        return result

    def _stored_flag(self, value: Any) -> None:
        if type(value) is not int or value not in (0, 1):
            raise ValueError("Stored default flag must be zero or one.")

    def _get(self, identifier: Any) -> dict[str, Any]:
        if (
            not isinstance(identifier, str)
            or not re.fullmatch(r"[1-9]\d*", identifier)
            or len(identifier) > _ID_DIGITS
            or int(identifier) >= 2**63
        ):
            raise ValueError("Session ID must be a positive integer string.")
        rows = HostPersistence.read_records(
            self._config.table, {"id": int(identifier)}, limit=1
        )
        if not rows:
            raise LookupError("Session is no longer in the catalog.")
        return self._decode(rows[0])

    def _unique(self, name: str) -> None:
        if any(
            row["name"].casefold() == name.casefold()
            for row in HostPersistence.read_records(self._config.table, limit=0)
        ):
            raise FileExistsError("A session with this name already exists.")

    def _filters(self, filters: Mapping[str, Any] | None) -> dict[str, Any]:
        if filters is None:
            return {}
        if not isinstance(filters, Mapping) or set(filters) - {
            "search",
            "broker_id",
            "timezone",
        }:
            raise ValueError("Unsupported session filters.")
        query = dict(filters)
        for key in set(query) - {"broker_id"}:
            _text(query[key], key)
        if "timezone" in query:
            _zone(query["timezone"])
        if "broker_id" in query:
            value = query["broker_id"]
            if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
                value = int(value)
            if type(value) is not int or not -1 <= value < 2**63:
                raise ValueError("broker_id must be an integer.")
            query["broker_id"] = value
        return query

    def _columns(self, values: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "name": values["name"],
            "description": values["description"],
            "timezone": values["timezone"],
            "broker_id": values["broker_id"],
            "is_default": int(values["is_default"]),
            "windows_json": json.dumps(values["windows"]),
            "holidays_json": json.dumps(values["holidays"]),
        }

    def _commit(self, operation: Mapping[str, Any]) -> None:
        try:
            result = HostPersistence.apply_batch([operation])
        except RuntimeError as error:
            raise RuntimeError("Session changes could not be saved.") from error
        if result["affected_rows"] != 1:
            raise LookupError("Session is no longer in the catalog.")

    def _create(self, values: Mapping[str, Any]) -> dict[str, Any]:
        self._commit(
            {
                "op": "create",
                "table": self._config.table,
                "values": self._columns(values),
            }
        )
        row = HostPersistence.read_records(
            self._config.table, {"name": values["name"]}, limit=1
        )[0]
        return self._decode(row)

    def _update(
        self, values: Mapping[str, Any], updates: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._commit(
            {
                "op": "update",
                "table": self._config.table,
                "key_columns": {"id": int(values["id"])},
                "values": updates,
            }
        )
        return self._get(values["id"])


if __name__ == "__main__":
    logger.info("Configured session count: %d", len(Sessions().sessions()))
