"""Helper utilities and validation for Data Manager sessions catalog service."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, replace
from datetime import date
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import ErrorCode
from app.include.contracts import SessionWindow, TradingHoliday, TradingSession

logger = get_logger(__name__)
persistence = HostPersistence()

MAX_SHIFT_MINUTES = 1440
MAX_WINDOWS = 100
MAX_HOLIDAYS = 1000

SESSIONS_CATALOG_FR = "FR-DATAMGR-SESSIONS-CATALOG"

__all__ = [
    "MAX_HOLIDAYS",
    "MAX_SHIFT_MINUTES",
    "MAX_WINDOWS",
    "SESSIONS_CATALOG_FR",
    "SessionWindow",
    "TradingHoliday",
    "TradingSession",
    "_SessionError",
    "_calendar_json",
    "_editable",
    "_lookup",
    "_names",
    "_records",
    "_row",
    "_shift_window",
    "_validate_holiday",
    "_validate_window",
    "logger",
    "persistence",
]


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
