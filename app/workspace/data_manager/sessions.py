r"""Market sessions, exchange clocks, and native session import service.

Description:
    ensure_defaults() owns baseline trading windows. Save/delete operations use
    atomic SessionStore CRUD in app.host.persistence; calendar, timezone and window
    interpretation remain here. No direct database handles or SQL are permitted.

    Market sessions, exchange clocks, DST transitions, and native session import
    service for the Data Manager workspace. Manages canonical trading sessions,
    day-of-week active windows, holiday schedules, and time zone transformations
    with IANA zoneinfo support. Imports NinjaTrader 8 TradingHours XML templates
    with configurable overwrite and skip conflict policies. Exports and imports
    native StrategyQuant X Sessions.xml templates with full parity.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Manage exchange trading hours, clocks, and holiday
    calendars in the Data Manager workspace.

Key Capabilities:
    - FR-DATA-SESSIONS-DEFAULTS: Initialize baseline trading windows idempotently.
      Associated: `SessionService.ensure_defaults()`
      Logging: INFO initialization; storage logs each upsert result.
    - FR-DATA-SESSIONS-TIMEZONES: Validate and resolve standard IANA timezones and DST.
    - FR-DATA-SESSIONS-WINDOWS: Represent and evaluate multi-window daily sessions.
    - FR-DATA-SESSIONS-IMPORT: Parse and import NinjaTrader 8 XML trading
      hours templates.
    - FR-DATA-SESSIONS-PERSISTENCE-CRUD: CRUD operations against datamgr_sessions table.
    - FR-DATA-SESSIONS-CLONE: Clone trading sessions with broker profile association.
    - FR-DATA-SESSIONS-XML-TRANSFER: Export and import native StrategyQuant X
      Sessions.xml templates.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.sessions import (
        SessionService,
        SessionWindow,
        TradingSessionDefinition,
    )

    db = DatabaseManager()
    db.initialize()
    service = SessionService(db)
    service.ensure_defaults()

    session = TradingSessionDefinition(
        name="US_Equities_RTH",
        timezone="America/New_York",
        windows=[
            SessionWindow(
                day_from="Mon",
                day_to="Mon",
                start_time="09:30",
                end_time="16:00",
                eod=True,
            )
            for _ in range(5)
        ],
    )
    service.save_session(session)
    is_open = service.is_market_open("US_Equities_RTH", dt_utc)
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.sessions --list
    python -m app.workspace.data_manager.sessions --check US_Equities_RTH \\
        --time 2026-10-07T14:30Z
    python -m app.workspace.data_manager.sessions \\
        --import-nt TradingHours.xml --policy overwrite
    ```
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zoneinfo
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager

logger = get_logger(__name__)

TIME_PARTS_HH_MM = 2
SQX_TUPLE_FIELD_COUNT = 5
DEFAULT_LIMIT = 1000

WEEKDAY_INT_TO_NAME: dict[int, str] = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}

DAY_NAME_TO_INT: dict[str, int] = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}

NT_TIMEZONE_MAP: dict[str, str] = {
    "Eastern Standard Time": "America/New_York",
    "Central Standard Time": "America/Chicago",
    "Mountain Standard Time": "America/Denver",
    "Pacific Standard Time": "America/Los_Angeles",
    "GMT Standard Time": "UTC",
    "UTC": "UTC",
    "EST": "America/New_York",
    "CST": "America/Chicago",
    "MST": "America/Denver",
    "PST": "America/Los_Angeles",
}


def _is_window_open(
    window: SessionWindow, current_day: int, current_time: time
) -> bool:
    """Determine if a single session window is active at day and time."""
    from_day = DAY_NAME_TO_INT.get(window.day_from.lower()[:3], window.day_of_week)
    to_day = DAY_NAME_TO_INT.get(window.day_to.lower()[:3], from_day)
    start_t = window.parse_start_time()
    end_t = window.parse_end_time()

    if from_day == to_day:
        if current_day == from_day:
            return (
                start_t <= current_time <= end_t
                if start_t <= end_t
                else (current_time >= start_t or current_time <= end_t)
            )
        return (
            current_time <= end_t
            if (start_t > end_t and current_day == (from_day + 1) % 7)
            else False
        )

    if current_day == from_day and current_time >= start_t:
        return True
    if current_day == to_day and current_time <= end_t:
        return True
    span = (to_day - from_day) % 7
    offset = (current_day - from_day) % 7
    return 0 < offset < span


def _normalize_window_days(d: dict[str, Any]) -> None:
    """Normalize day string names and indices in window dictionary."""
    if "day_from" in d and isinstance(d["day_from"], str):
        key = d["day_from"].strip().lower()[:3]
        if key in DAY_NAME_TO_INT:
            d["day_of_week"] = DAY_NAME_TO_INT[key]
            d["day_from"] = WEEKDAY_INT_TO_NAME[DAY_NAME_TO_INT[key]]
    elif "day_of_week" in d and isinstance(d["day_of_week"], int):
        d["day_from"] = WEEKDAY_INT_TO_NAME.get(d["day_of_week"], "Mon")

    if "day_to" in d and isinstance(d["day_to"], str):
        key_to = d["day_to"].strip().lower()[:3]
        if key_to in DAY_NAME_TO_INT:
            d["day_to"] = WEEKDAY_INT_TO_NAME[DAY_NAME_TO_INT[key_to]]
    else:
        d["day_to"] = d.get("day_from", "Mon")


class SessionWindow(BaseModel):
    """Trading session daily window specification with SQX multi-day and EOD parity."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    day_of_week: int = Field(
        default=0, ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)"
    )
    day_from: str = Field(
        default="Mon",
        description="Start day (Mon, Tue, Wed, Thu, Fri, Sat, Sun)",
    )
    day_to: str = Field(
        default="Mon",
        description="End day (Mon, Tue, Wed, Thu, Fri, Sat, Sun)",
    )
    start_time: str = Field(
        default="00:00",
        pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        description="Window start time HH:MM or HH:MM:SS",
    )
    end_time: str = Field(
        default="23:59",
        pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        description="Window end time HH:MM or HH:MM:SS",
    )
    eod: bool = Field(
        default=True,
        description="Session End Means EOD (SEOC)",
    )
    session_type: str = Field(
        default="Regular",
        description="Session type (e.g. Regular, Extended, PreMarket, PostMarket)",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_window_input(cls, data: Any) -> Any:
        """Harmonize camelCase, SQX tuple, and legacy inputs."""
        if not isinstance(data, dict):
            return data
        d = dict(data)
        if "dayFrom" in d and "day_from" not in d:
            d["day_from"] = str(d["dayFrom"])
        if "dayTo" in d and "day_to" not in d:
            d["day_to"] = str(d["dayTo"])
        if "timeFrom" in d and "start_time" not in d:
            d["start_time"] = str(d["timeFrom"])
        if "timeTo" in d and "end_time" not in d:
            d["end_time"] = str(d["timeTo"])
        if "seoc" in d and "eod" not in d:
            val = d["seoc"]
            d["eod"] = (
                val
                if isinstance(val, bool)
                else str(val).lower() in ("yes", "true", "1")
            )
        _normalize_window_days(d)
        return d

    @property
    def time_from(self) -> str:
        """Alias for start_time."""
        return self.start_time

    @property
    def time_to(self) -> str:
        """Alias for end_time."""
        return self.end_time

    @property
    def seoc(self) -> bool:
        """Alias for eod."""
        return self.eod

    def parse_start_time(self) -> time:
        """Parse start time string into datetime.time."""
        parts = [int(p) for p in self.start_time.split(":")]
        if len(parts) == TIME_PARTS_HH_MM:
            return time(hour=parts[0], minute=parts[1])
        return time(hour=parts[0], minute=parts[1], second=parts[2])

    def parse_end_time(self) -> time:
        """Parse end time string into datetime.time."""
        parts = [int(p) for p in self.end_time.split(":")]
        if len(parts) == TIME_PARTS_HH_MM:
            return time(hour=parts[0], minute=parts[1])
        return time(hour=parts[0], minute=parts[1], second=parts[2])

    def int_start_time(self) -> int:
        """Convert start time to SQX HHMM integer."""
        t = self.parse_start_time()
        return t.hour * 100 + t.minute

    def int_end_time(self) -> int:
        """Convert end time to SQX HHMM integer."""
        t = self.parse_end_time()
        return t.hour * 100 + t.minute

    def to_sqx_tuple(self) -> str:
        """Format as SQX 5-field string: startDay,startTime,endDay,endTime,seoc."""
        seoc_str = "Yes" if self.eod else "No"
        start_hhmm = self.start_time[:5]
        end_hhmm = self.end_time[:5]
        return f"{self.day_from},{start_hhmm},{self.day_to},{end_hhmm},{seoc_str}"

    @classmethod
    def from_sqx_tuple(cls, line: str) -> SessionWindow:
        """Parse SQX 5-field string into SessionWindow."""
        parts = line.split(",")
        if len(parts) != SQX_TUPLE_FIELD_COUNT:
            raise ValueError(
                "Invalid session data length. "
                f"Expected {SQX_TUPLE_FIELD_COUNT}, got {len(parts)}"
            )
        day_from, time_from, day_to, time_to, seoc_str = parts
        eod = seoc_str.strip().lower() in ("yes", "true", "1")
        return cls(
            day_from=day_from.strip(),
            day_to=day_to.strip(),
            start_time=time_from.strip(),
            end_time=time_to.strip(),
            eod=eod,
        )


class TradingHoliday(BaseModel):
    """Single trading holiday specification."""

    model_config = ConfigDict(frozen=True)

    date_str: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    description: str = Field(default="", description="Holiday name or reason")

    def parse_date(self) -> date:
        """Parse date string into datetime.date."""
        return date.fromisoformat(self.date_str)


class TradingSessionDefinition(BaseModel):
    """Authoritative domain specification of an exchange trading session."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    name: str = Field(
        min_length=1, max_length=128, description="Unique session identifier"
    )
    broker_id: int = Field(
        default=-1, description="Broker profile ID (-1 for SQ default)"
    )
    broker_name: str = Field(
        default="SQ default", description="Broker profile display name"
    )
    description: str = Field(default="", description="Descriptive name")
    timezone: str = Field(
        default="UTC",
        description="IANA standard timezone name (e.g. America/New_York)",
    )
    windows: list[SessionWindow] = Field(
        default_factory=list, description="Weekly trading windows"
    )
    holidays: list[TradingHoliday] = Field(
        default_factory=list, description="Specific closed holidays"
    )
    is_default: bool = Field(
        default=False, description="Whether this is the fallback session"
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_session_input(cls, data: Any) -> Any:
        """Accept SQX aliases (broker, elements)."""
        if not isinstance(data, dict):
            return data
        d = dict(data)
        if "broker" in d and "broker_id" not in d:
            try:
                d["broker_id"] = int(d["broker"])
            except ValueError, TypeError:
                d["broker_id"] = -1
        if "elements" in d and "windows" not in d:
            d["windows"] = d["elements"]
        return d

    @property
    def elements(self) -> list[SessionWindow]:
        """Alias for windows matching SQX terminology."""
        return self.windows

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate session name is non-empty string without illegal characters."""
        clean = v.strip()
        if not clean:
            raise ValueError("Session name cannot be empty.")
        if not re.match(r"^[a-zA-Z0-9_\-\s./]+$", clean):
            raise ValueError("Session name cannot contain any special characters!")
        return clean

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone against standard IANA database using zoneinfo.

        Fires FR-DATA-SESSIONS-TIMEZONES.
        """
        clean = v.strip()
        try:
            zoneinfo.ZoneInfo(clean)
        except (zoneinfo.ZoneInfoNotFoundError, ValueError) as exc:
            logger.exception(
                "FR-DATA-SESSIONS-TIMEZONES: Invalid IANA timezone '%s'",
                clean,
                extra={"timezone": clean, "fr_id": "FR-DATA-SESSIONS-TIMEZONES"},
            )
            raise ValueError(
                f"Invalid standard IANA timezone '{clean}': {exc}"
            ) from exc
        return clean


class SessionService:
    """Domain service managing trading sessions, clocks, and NT8 XML imports."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize session service with host database manager."""
        self._db = db

    def ensure_defaults(self) -> None:
        """Initialize baseline trading windows without replacing user definitions."""
        default_definitions = [
            (
                "24/7 Forex",
                "Continuous round-the-clock forex trading session",
                "UTC",
                [
                    {
                        "day_from": WEEKDAY_INT_TO_NAME[d],
                        "day_to": WEEKDAY_INT_TO_NAME[d],
                        "start_time": "00:00",
                        "end_time": "23:59:59",
                        "eod": True,
                    }
                    for d in range(7)
                ],
                1,
                -1,
            ),
            (
                "Forex_247",
                "Continuous round-the-clock forex trading session",
                "UTC",
                [
                    {
                        "day_from": WEEKDAY_INT_TO_NAME[d],
                        "day_to": WEEKDAY_INT_TO_NAME[d],
                        "start_time": "00:00",
                        "end_time": "23:59",
                        "eod": True,
                    }
                    for d in range(7)
                ],
                0,
                -1,
            ),
            (
                "Forex 24/5",
                "Continuous 24/5 forex trading session",
                "UTC",
                [
                    {
                        "day_from": WEEKDAY_INT_TO_NAME[d],
                        "day_to": WEEKDAY_INT_TO_NAME[d],
                        "start_time": "00:00",
                        "end_time": "23:59:59",
                        "eod": True,
                    }
                    for d in range(5)
                ],
                0,
                -1,
            ),
            (
                "Forex_245",
                "Continuous 24/5 forex trading session",
                "UTC",
                [
                    {
                        "day_from": WEEKDAY_INT_TO_NAME[d],
                        "day_to": WEEKDAY_INT_TO_NAME[d],
                        "start_time": "00:00",
                        "end_time": "23:59",
                        "eod": True,
                    }
                    for d in range(5)
                ],
                0,
                -1,
            ),
            (
                "US Equities RTH",
                "US Equities Regular Trading Hours",
                "America/New_York",
                [
                    {
                        "day_from": WEEKDAY_INT_TO_NAME[d],
                        "day_to": WEEKDAY_INT_TO_NAME[d],
                        "start_time": "09:30",
                        "end_time": "16:00",
                        "eod": True,
                    }
                    for d in range(5)
                ],
                0,
                -1,
            ),
            (
                "US_Stocks",
                "US Stocks Regular Trading Hours",
                "America/New_York",
                [
                    {
                        "day_from": WEEKDAY_INT_TO_NAME[d],
                        "day_to": WEEKDAY_INT_TO_NAME[d],
                        "start_time": "09:30",
                        "end_time": "16:00",
                        "eod": True,
                    }
                    for d in range(5)
                ],
                0,
                -1,
            ),
            (
                "US_Index_Futures",
                "US Index Futures Regular Trading Hours",
                "America/Chicago",
                [
                    {
                        "day_from": WEEKDAY_INT_TO_NAME[d],
                        "day_to": WEEKDAY_INT_TO_NAME[d],
                        "start_time": "08:30",
                        "end_time": "15:00",
                        "eod": True,
                    }
                    for d in range(5)
                ],
                0,
                -1,
            ),
        ]

        for (
            name,
            desc,
            tz,
            windows,
            is_def,
            broker_id,
        ) in default_definitions:
            self._db.sessions.upsert(
                {
                    "name": name,
                    "broker_id": broker_id,
                    "description": desc,
                    "timezone": tz,
                    "windows_json": json.dumps(windows),
                    "holidays_json": "[]",
                    "is_default": is_def,
                },
                only_if_absent=True,
            )
        logger.info(
            "Baseline trading sessions initialized",
            extra={"fr_id": "FR-DATA-SESSIONS-DEFAULTS"},
        )

    def save_session(self, session: TradingSessionDefinition) -> int:
        """Persist a supplied trading definition through one atomic upsert."""
        record = {
            "name": session.name,
            "broker_id": session.broker_id,
            "description": session.description,
            "timezone": session.timezone,
            "windows_json": json.dumps([w.model_dump() for w in session.windows]),
            "holidays_json": json.dumps([h.model_dump() for h in session.holidays]),
            "is_default": int(session.is_default),
        }
        session_id = self._db.sessions.upsert(record)
        logger.info(
            "Trading session saved",
            extra={
                "session_name": session.name,
                "broker_id": session.broker_id,
                "fr_id": "FR-DATA-SESSIONS-PERSISTENCE-CRUD",
            },
        )
        return session_id

    def get_session(self, name: str) -> TradingSessionDefinition | None:
        """Retrieve a trading session definition by unique name.

        Fires FR-DATA-SESSIONS-PERSISTENCE-CRUD.
        """
        row = self._db.sessions.get_by_name(name.strip())
        if row is None:
            logger.debug(
                "FR-DATA-SESSIONS-PERSISTENCE-CRUD: Session '%s' not found",
                name,
                extra={
                    "session_name": name,
                    "fr_id": "FR-DATA-SESSIONS-PERSISTENCE-CRUD",
                },
            )
            return None

        windows: list[SessionWindow] = []
        if row.get("windows_json"):
            try:
                raw_windows = json.loads(str(row["windows_json"]))
                windows = [SessionWindow.model_validate(w) for w in raw_windows]
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning(
                    "Failed parsing windows_json for session '%s': %s",
                    name,
                    exc,
                )

        holidays: list[TradingHoliday] = []
        if row.get("holidays_json"):
            try:
                raw_holidays = json.loads(str(row["holidays_json"]))
                holidays = [TradingHoliday.model_validate(h) for h in raw_holidays]
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning(
                    "Failed parsing holidays_json for session '%s': %s",
                    name,
                    exc,
                )

        broker_id = int(row.get("broker_id", -1))
        broker_name = "SQ default" if broker_id == -1 else f"Broker {broker_id}"

        return TradingSessionDefinition(
            name=str(row.get("name", "")),
            broker_id=broker_id,
            broker_name=broker_name,
            description=str(row.get("description", "")),
            timezone=str(row.get("timezone", "UTC")),
            windows=windows,
            holidays=holidays,
            is_default=bool(row.get("is_default", 0)),
        )

    def list_sessions(
        self,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        broker_id: int | None = None,
        search: str | None = None,
    ) -> list[TradingSessionDefinition]:
        """List defined trading sessions with optional broker and search filters."""
        if broker_id is not None:
            rows = self._db.sessions.list_by_broker(
                broker_id=broker_id, limit=limit, offset=offset
            )
        else:
            rows = self._db.sessions.list_sessions(limit=limit, offset=offset)

        result: list[TradingSessionDefinition] = []
        search_lower = search.strip().lower() if search and search.strip() else None

        for r in rows:
            sess = self.get_session(str(r.get("name", "")))
            if sess:
                if search_lower and (
                    search_lower not in sess.name.lower()
                    and search_lower not in sess.broker_name.lower()
                    and search_lower not in sess.description.lower()
                ):
                    continue
                result.append(sess)
        return result

    def delete_session(self, name: str) -> bool:
        """Delete a trading definition through storage CRUD."""
        deleted = self._db.sessions.delete(name.strip())
        logger.info(
            "Trading session delete completed",
            extra={
                "deleted": deleted,
                "fr_id": "FR-DATA-SESSIONS-PERSISTENCE-CRUD",
            },
        )
        return deleted

    def delete_sessions(self, names: list[str]) -> int:
        """Delete multiple trading definitions in one batch."""
        clean_names = [n.strip() for n in names if n.strip()]
        if not clean_names:
            return 0
        deleted_count = self._db.sessions.delete_many(clean_names)
        logger.info(
            "Batch session delete completed",
            extra={
                "deleted_count": deleted_count,
                "fr_id": "FR-DATA-SESSIONS-PERSISTENCE-CRUD",
            },
        )
        return deleted_count

    def clone_session(
        self,
        source_name: str,
        new_name: str,
        broker_id: int = -1,
        broker_postfix: str = "",
    ) -> TradingSessionDefinition:
        """Clone existing session definition with broker profile and postfix.

        Fires FR-DATA-SESSIONS-CLONE.
        """
        source = self.get_session(source_name.strip())
        if source is None:
            raise ValueError(f"Session with name '{source_name}' doesn't exist.")

        clean_new = new_name.strip()
        if broker_postfix and not clean_new.endswith(broker_postfix):
            target_name = clean_new + broker_postfix
        else:
            target_name = clean_new

        if self.get_session(target_name) is not None:
            raise ValueError(f"Session with name '{target_name}' already exists.")

        cloned = TradingSessionDefinition(
            name=target_name,
            broker_id=broker_id,
            broker_name=(f"Broker {broker_id}" if broker_id != -1 else "SQ default"),
            description=source.description,
            timezone=source.timezone,
            windows=[w.model_copy() for w in source.windows],
            holidays=[h.model_copy() for h in source.holidays],
            is_default=False,
        )
        self.save_session(cloned)
        logger.info(
            "FR-DATA-SESSIONS-CLONE: Cloned session '%s' -> '%s' (broker=%d)",
            source_name,
            target_name,
            broker_id,
            extra={
                "fr_id": "FR-DATA-SESSIONS-CLONE",
                "source": source_name,
                "target": target_name,
            },
        )
        return cloned

    def generate_mon_fri(self, elements: list[SessionWindow]) -> list[SessionWindow]:
        """Replicate Monday trading session definition across Tuesday to Friday."""
        if not elements:
            raise ValueError(
                "No session defined. Please define Monday session and try again"
            )

        monday_element = next(
            (e for e in elements if e.day_from.lower() == "mon"), None
        )
        if monday_element is None:
            raise ValueError("You have to create Monday session element")

        if monday_element.day_to.lower() not in ("mon", "tue"):
            raise ValueError(
                "No suitable Monday session found. "
                "Monday session must end on Monday or Tuesday"
            )

        cross_day = monday_element.day_to.lower() == "tue"
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        generated: list[SessionWindow] = []

        for idx, day in enumerate(weekdays):
            end_day = WEEKDAY_INT_TO_NAME[idx + 1] if cross_day else day
            generated.append(
                SessionWindow(
                    day_from=day,
                    day_to=end_day,
                    start_time=monday_element.start_time,
                    end_time=monday_element.end_time,
                    eod=monday_element.eod,
                    session_type=monday_element.session_type,
                )
            )

        # Preserve existing weekend definitions
        weekend = [e for e in elements if e.day_from.lower() in ("sat", "sun")]
        return generated + weekend

    def export_sqx_xml(self, names: list[str]) -> str:
        """Export session definitions into native StrategyQuant X Sessions.xml.

        Fires FR-DATA-SESSIONS-XML-TRANSFER.
        """
        root = ET.Element("Sessions")
        for name in names:
            sess = self.get_session(name.strip())
            if not sess:
                continue
            sess_elem = ET.SubElement(
                root,
                "Session",
                {
                    "name": sess.name,
                    "broker": str(sess.broker_id),
                    "timezone": sess.timezone,
                    "description": sess.description,
                },
            )
            for w in sess.windows:
                ET.SubElement(
                    sess_elem,
                    "SessionElement",
                    {
                        "startDay": w.day_from,
                        "startTime": w.start_time[:5],
                        "endDay": w.day_to,
                        "endTime": w.end_time[:5],
                        "seoc": "Yes" if w.eod else "No",
                        "type": w.session_type,
                    },
                )
        raw_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        return str(raw_bytes.decode("utf-8"))

    def import_sqx_xml(
        self, xml_source: str | Path, policy: str = "overwrite"
    ) -> tuple[list[TradingSessionDefinition], list[str]]:
        """Import session definitions from native StrategyQuant X Sessions.xml.

        Fires FR-DATA-SESSIONS-XML-TRANSFER.
        """
        xml_text = self._load_xml_text(xml_source)
        root = ET.fromstring(xml_text)  # noqa: S314
        session_nodes = root.findall(".//Session") if root.tag != "Session" else [root]

        imported: list[TradingSessionDefinition] = []
        skipped: list[str] = []

        for node in session_nodes:
            name = node.get("name") or (node.findtext("Name") or "").strip()
            if not name:
                continue
            broker_str = node.get("broker") or (node.findtext("Broker") or "-1").strip()
            try:
                broker_id = int(broker_str)
            except ValueError:
                broker_id = -1
            timezone = (
                node.get("timezone") or (node.findtext("TimeZone") or "UTC").strip()
            )
            description = (
                node.get("description") or (node.findtext("Description") or "").strip()
            )

            windows: list[SessionWindow] = []
            elements = node.findall(".//SessionElement") + node.findall(".//Session")
            for elem_node in elements:
                if elem_node is node:
                    continue
                d_from = (
                    elem_node.get("startDay")
                    or elem_node.get("dayFrom")
                    or elem_node.findtext("DayOfWeek")
                    or "Mon"
                )
                t_from = (
                    elem_node.get("startTime")
                    or elem_node.get("timeFrom")
                    or elem_node.findtext("StartTime")
                    or "00:00"
                )
                d_to = elem_node.get("endDay") or elem_node.get("dayTo") or d_from
                t_to = (
                    elem_node.get("endTime")
                    or elem_node.get("timeTo")
                    or elem_node.findtext("EndTime")
                    or "23:59"
                )
                seoc_raw = elem_node.get("seoc") or elem_node.get("eod") or "Yes"
                is_eod = seoc_raw.lower() in ("yes", "true", "1")
                windows.append(
                    SessionWindow(
                        day_from=d_from.strip()[:3],
                        day_to=d_to.strip()[:3],
                        start_time=t_from.strip()[:8],
                        end_time=t_to.strip()[:8],
                        eod=is_eod,
                    )
                )

            existing = self.get_session(name)
            if existing and policy == "skip":
                skipped.append(name)
                continue

            session_def = TradingSessionDefinition(
                name=name,
                broker_id=broker_id,
                description=description,
                timezone=self._normalize_timezone(timezone),
                windows=windows,
            )
            self.save_session(session_def)
            imported.append(session_def)

        return imported, skipped

    @staticmethod
    def default_nt_folder() -> Path:
        """Return default NinjaTrader 8 TradingHours templates directory."""
        return (
            Path.home() / "Documents" / "NinjaTrader 8" / "templates" / "TradingHours"
        )

    def list_ninjatrader_templates(
        self, folder_path: str | Path | None = None
    ) -> dict[str, Any]:
        """Scan and list NinjaTrader 8 TradingHours XML templates."""
        target_path = Path(folder_path) if folder_path else self.default_nt_folder()
        if not target_path.exists():
            return {
                "folder": str(target_path),
                "exists": False,
                "templates": [],
                "count": 0,
            }

        if target_path.is_file():
            templates: list[str] = (
                [target_path.name] if target_path.suffix.lower() == ".xml" else []
            )
            return {
                "folder": str(target_path.parent),
                "exists": True,
                "templates": templates,
                "count": len(templates),
            }

        xml_files = sorted(
            [
                f.name
                for f in target_path.iterdir()
                if f.is_file() and f.suffix.lower() == ".xml"
            ]
        )
        return {
            "folder": str(target_path),
            "exists": True,
            "templates": xml_files,
            "count": len(xml_files),
        }

    def _collect_nt_sources(self, xml_source: str | Path) -> list[Path | str]:
        """Gather list of NT XML file paths or inline strings to process."""
        is_path_like = isinstance(xml_source, Path) or (
            isinstance(xml_source, str) and not xml_source.strip().startswith("<")
        )
        if is_path_like:
            p = Path(xml_source)
            if p.exists():
                if p.is_dir():
                    return sorted(
                        [
                            f
                            for f in p.iterdir()
                            if f.is_file() and f.suffix.lower() == ".xml"
                        ]
                    )
                return [p]
        return [str(xml_source)]

    def import_ninjatrader_full(
        self, xml_source: str | Path, policy: str = "overwrite"
    ) -> dict[str, Any]:
        """Import NT8 TradingHours templates with comprehensive SQX statistics.

        Fires FR-DATA-SESSIONS-IMPORT.
        """
        files = self._collect_nt_sources(xml_source)
        imported: list[str] = []
        skipped: list[str] = []
        failed: list[dict[str, str]] = []
        dropped_holidays = 0
        dropped_partial_holidays = 0

        for item in files:
            item_name = item.name if isinstance(item, Path) else "inline.xml"
            try:
                xml_text = self._load_xml_text(item)
                root = ET.fromstring(xml_text)  # noqa: S314
                templates = (
                    root.findall(".//TradingHours")
                    if root.tag != "TradingHours"
                    else [root]
                )
                if not templates:
                    failed.append(
                        {
                            "template": item_name,
                            "reason": "No TradingHours tag found",
                        }
                    )
                    continue

                for node in templates:
                    sess_def = self._parse_nt_node(node)
                    if sess_def is None:
                        continue
                    h_node = node.find("Holidays")
                    if h_node is not None:
                        dropped_holidays += len(h_node.findall("Holiday"))
                    ph_node = node.find("PartialHolidays")
                    if ph_node is not None:
                        dropped_partial_holidays += len(
                            ph_node.findall("PartialHoliday")
                        )

                    existing = self.get_session(sess_def.name)
                    if existing is not None and policy == "skip":
                        skipped.append(sess_def.name)
                        continue

                    self.save_session(sess_def)
                    imported.append(sess_def.name)
            except (ET.ParseError, OSError, ValueError, KeyError) as exc:
                failed.append({"template": item_name, "reason": str(exc)})

        msg = (
            f"Imported {len(imported)} session(s), "
            f"skipped {len(skipped)} existing, {len(failed)} failed. "
            f"{dropped_holidays} holidays and {dropped_partial_holidays} "
            "partial holidays were NOT imported - SQX has no equivalent."
        )
        return {
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
            "dropped_holidays": dropped_holidays,
            "dropped_partial_holidays": dropped_partial_holidays,
            "success": msg,
        }

    def import_ninjatrader_xml(
        self, xml_source: str | Path, policy: str = "overwrite"
    ) -> list[TradingSessionDefinition]:
        """Import NinjaTrader 8 TradingHours XML templates.

        Maintains backwards compatibility returning parsed definitions.
        Fires FR-DATA-SESSIONS-IMPORT.
        """
        xml_text = self._load_xml_text(xml_source)
        root = ET.fromstring(xml_text)  # noqa: S314
        templates = (
            root.findall(".//TradingHours") if root.tag != "TradingHours" else [root]
        )

        imported: list[TradingSessionDefinition] = []
        for node in templates:
            session_def = self._parse_nt_node(node)
            if session_def is None:
                continue

            existing = self.get_session(session_def.name)
            if existing is not None and policy == "skip":
                logger.info(
                    "FR-DATA-SESSIONS-IMPORT: Skipped session '%s' under skip policy",
                    session_def.name,
                    extra={
                        "session": session_def.name,
                        "fr_id": "FR-DATA-SESSIONS-IMPORT",
                    },
                )
                continue

            self.save_session(session_def)
            imported.append(session_def)
            logger.info(
                "FR-DATA-SESSIONS-IMPORT: Imported session '%s' (windows=%d)",
                session_def.name,
                len(session_def.windows),
                extra={
                    "session": session_def.name,
                    "windows": len(session_def.windows),
                    "holidays": len(session_def.holidays),
                    "fr_id": "FR-DATA-SESSIONS-IMPORT",
                },
            )

        return imported

    def is_market_open(self, session_name: str, dt_utc: datetime) -> bool:
        """Evaluate if market is actively open at specified UTC datetime.

        Handles IANA timezone conversion, DST resolution, holiday matching,
        and multi-window session evaluation with cross-midnight support.

        Fires FR-DATA-SESSIONS-WINDOWS and FR-DATA-SESSIONS-TIMEZONES.
        """
        session = self.get_session(session_name)
        if session is None:
            logger.warning(
                "FR-DATA-SESSIONS-WINDOWS: Session '%s' not found for open check",
                session_name,
                extra={"session_name": session_name},
            )
            return False

        tz = zoneinfo.ZoneInfo(session.timezone)
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
        local_dt = dt_utc.astimezone(tz)

        local_date_str = local_dt.date().isoformat()
        for holiday in session.holidays:
            if holiday.date_str == local_date_str:
                logger.debug(
                    "FR-DATA-SESSIONS-WINDOWS: Market closed due to holiday %s (%s)",
                    holiday.date_str,
                    holiday.description,
                    extra={
                        "session": session_name,
                        "date": local_date_str,
                        "fr_id": "FR-DATA-SESSIONS-WINDOWS",
                    },
                )
                return False

        current_day_int = local_dt.weekday()
        current_time = local_dt.time()

        for window in session.windows:
            if _is_window_open(window, current_day_int, current_time):
                return True

        return False

    def _load_xml_text(self, xml_source: str | Path) -> str:
        """Read XML text from file path or return string directly."""
        if isinstance(xml_source, Path) or (
            isinstance(xml_source, str) and not xml_source.strip().startswith("<")
        ):
            source_path = Path(xml_source)
            if not source_path.exists():
                raise FileNotFoundError(f"XML path not found: {source_path}")
            return source_path.read_text(encoding="utf-8")
        return xml_source

    def _parse_nt_node(self, node: ET.Element) -> TradingSessionDefinition | None:
        """Parse a single TradingHours XML element."""
        name_elem = node.find("Name")
        name = (
            name_elem.text.strip() if name_elem is not None and name_elem.text else ""
        )
        if not name:
            return None

        desc_elem = node.find("Description")
        desc = (
            desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
        )

        tz_elem = node.find("TimeZone")
        tz_str = tz_elem.text.strip() if tz_elem is not None and tz_elem.text else "UTC"
        iana_tz = self._normalize_timezone(tz_str)

        windows = self._parse_nt_windows(node.find("Sessions"))
        holidays = self._parse_nt_holidays(node.find("Holidays"))

        return TradingSessionDefinition(
            name=name,
            broker_id=-1,
            description=desc,
            timezone=iana_tz,
            windows=windows,
            holidays=holidays,
        )

    def _parse_nt_windows(
        self, sessions_parent: ET.Element | None
    ) -> list[SessionWindow]:
        """Extract daily SessionWindow items from XML Sessions element."""
        if sessions_parent is None:
            return []
        windows: list[SessionWindow] = []
        for sess_node in sessions_parent.findall("Session"):
            day_elem = sess_node.find("DayOfWeek")
            day_val = 0
            day_name = "Mon"
            if day_elem is not None and day_elem.text:
                day_text = day_elem.text.strip().lower()
                day_val = (
                    int(day_text)
                    if day_text.isdigit()
                    else DAY_NAME_TO_INT.get(day_text[:3], 0)
                )
                day_name = WEEKDAY_INT_TO_NAME.get(day_val, "Mon")

            start_elem = sess_node.find("StartTime")
            start_str = (
                start_elem.text.strip()
                if start_elem is not None and start_elem.text
                else "00:00"
            )
            end_elem = sess_node.find("EndTime")
            end_str = (
                end_elem.text.strip()
                if end_elem is not None and end_elem.text
                else "23:59"
            )
            type_elem = sess_node.find("Type")
            stype = (
                type_elem.text.strip()
                if type_elem is not None and type_elem.text
                else "Regular"
            )

            # Check if times cross midnight
            day_to_name = day_name
            if start_str > end_str:
                day_to_name = WEEKDAY_INT_TO_NAME[(day_val + 1) % 7]

            windows.append(
                SessionWindow(
                    day_of_week=day_val,
                    day_from=day_name,
                    day_to=day_to_name,
                    start_time=start_str[:8],
                    end_time=end_str[:8],
                    eod=True,
                    session_type=stype,
                )
            )
        return windows

    def _parse_nt_holidays(
        self, holidays_parent: ET.Element | None
    ) -> list[TradingHoliday]:
        """Extract TradingHoliday items from XML Holidays element."""
        if holidays_parent is None:
            return []
        holidays: list[TradingHoliday] = []
        for hol_node in holidays_parent.findall("Holiday"):
            d_elem = hol_node.find("Date")
            if d_elem is not None and d_elem.text:
                h_date = d_elem.text.strip()[:10]
                h_desc_elem = hol_node.find("Description")
                h_desc = (
                    h_desc_elem.text.strip()
                    if h_desc_elem is not None and h_desc_elem.text
                    else ""
                )
                holidays.append(TradingHoliday(date_str=h_date, description=h_desc))
        return holidays

    @staticmethod
    def _normalize_timezone(tz_name: str) -> str:
        """Map common legacy or NinjaTrader timezone names to IANA standards."""
        resolved = NT_TIMEZONE_MAP.get(tz_name, tz_name)
        try:
            zoneinfo.ZoneInfo(resolved)
            return resolved
        except zoneinfo.ZoneInfoNotFoundError, ValueError:
            return "UTC"


def main() -> int:
    """CLI tool for managing and inspecting trading sessions."""
    parser = argparse.ArgumentParser(description="Manage market trading sessions")
    parser.add_argument("--list", action="store_true", help="List all sessions")
    parser.add_argument("--check", type=str, help="Check market open for session")
    parser.add_argument(
        "--time", type=str, help="ISO timestamp for check (default: now)"
    )
    parser.add_argument("--import-nt", type=str, help="Import NinjaTrader XML template")
    parser.add_argument(
        "--policy",
        choices=["overwrite", "skip"],
        default="overwrite",
        help="Conflict policy for import",
    )
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = SessionService(db)
    service.ensure_defaults()

    if args.import_nt:
        sessions = service.import_ninjatrader_xml(args.import_nt, policy=args.policy)
        print(f"Imported {len(sessions)} session(s) from {args.import_nt}.")
        return 0

    if args.check:
        dt = (
            datetime.fromisoformat(args.time)
            if args.time
            else datetime.now(zoneinfo.ZoneInfo("UTC"))
        )
        is_open = service.is_market_open(args.check, dt)
        print(f"Session '{args.check}' at {dt.isoformat()}: open={is_open}")
        return 0 if is_open else 1

    if args.list:
        sessions = service.list_sessions()
        print(f"Configured sessions ({len(sessions)}):")
        for s in sessions:
            print(
                f"  {s.name:25} Broker: {s.broker_id:<3} "
                f"TZ: {s.timezone:20} Windows: {len(s.windows):2} "
                f"Holidays: {len(s.holidays):2}"
            )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
