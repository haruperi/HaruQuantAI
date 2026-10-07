"""Market sessions, exchange clocks, and native session import service.

Description:
    Market sessions, exchange clocks, DST transitions, and native session import
    service for the Data Manager subsystem. Manages canonical trading sessions,
    day-of-week active windows, holiday schedules, and time zone transformations
    with IANA zoneinfo support. Imports NinjaTrader 8 TradingHours XML templates
    with configurable overwrite and skip conflict policies.

Purpose:
    FEAT-DATA-SESSIONS: Manage exchange trading hours, clocks, and holiday calendars.

Key Capabilities:
    FR-DATA-SESSIONS-TIMEZONES: Validate and resolve standard IANA timezones and DST.
    FR-DATA-SESSIONS-WINDOWS: Represent and evaluate multi-window daily sessions.
    FR-DATA-SESSIONS-IMPORT: Parse and import NinjaTrader 8 XML trading hours templates.
    FR-DATA-SESSIONS-PERSISTENCE-CRUD: CRUD operations against datamgr_sessions table.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.plugins.data.sessions import (
        SessionService,
        SessionWindow,
        TradingSessionDefinition,
    )

    db = DatabaseManager()
    db.initialize()
    service = SessionService(db)

    session = TradingSessionDefinition(
        name="US_Equities_RTH",
        timezone="America/New_York",
        windows=[
            SessionWindow(day_of_week=d, start_time="09:30", end_time="16:00")
            for d in range(5)
        ],
    )
    service.save_session(session)
    is_open = service.is_market_open("US_Equities_RTH", dt_utc)
    ```

CLI Usage:
    ```bash
    python -m app.plugins.data.sessions --list
    python -m app.plugins.data.sessions --check US_Equities_RTH --time 2026-10-07T14:30Z
    python -m app.plugins.data.sessions --import-nt TradingHours.xml --policy overwrite
    ```
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
import zoneinfo
from datetime import date, datetime, time
from pathlib import Path

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = get_logger(__name__)

TIME_PARTS_HH_MM = 2
DEFAULT_LIMIT = 1000

DAY_NAMES_MAP: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
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


class SessionWindow(BaseModel):
    """Trading session daily window specification."""

    model_config = ConfigDict(frozen=True)

    day_of_week: int = Field(ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    start_time: str = Field(
        pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        description="Window start time HH:MM or HH:MM:SS",
    )
    end_time: str = Field(
        pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        description="Window end time HH:MM or HH:MM:SS",
    )
    session_type: str = Field(
        default="Regular",
        description="Session type (e.g. Regular, Extended, PreMarket, PostMarket)",
    )

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

    model_config = ConfigDict(frozen=True)

    name: str = Field(
        min_length=1, max_length=128, description="Unique session identifier"
    )
    description: str = Field(default="", description="Descriptive name")
    timezone: str = Field(
        default="UTC", description="IANA standard timezone name (e.g. America/New_York)"
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

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate session name is non-empty string."""
        clean = v.strip()
        if not clean:
            raise ValueError("Session name cannot be empty.")
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

    def save_session(self, session: TradingSessionDefinition) -> int:
        """Upsert a trading session definition into datamgr_sessions.

        Fires FR-DATA-SESSIONS-PERSISTENCE-CRUD.
        """
        windows_json = json.dumps([w.model_dump() for w in session.windows])
        holidays_json = json.dumps([h.model_dump() for h in session.holidays])

        existing = self._db.sessions.get_by_name(session.name)
        if existing is not None:
            sql = (
                "UPDATE datamgr_sessions SET description = ?, timezone = ?, "
                "windows_json = ?, holidays_json = ?, is_default = ? "
                "WHERE name = ?;"
            )
            with self._db.transaction() as conn:
                cur = conn.cursor()
                cur.execute(
                    sql,
                    (
                        session.description,
                        session.timezone,
                        windows_json,
                        holidays_json,
                        int(session.is_default),
                        session.name,
                    ),
                )
            logger.info(
                "FR-DATA-SESSIONS-PERSISTENCE-CRUD: Updated session '%s'",
                session.name,
                extra={
                    "session_name": session.name,
                    "timezone": session.timezone,
                    "fr_id": "FR-DATA-SESSIONS-PERSISTENCE-CRUD",
                },
            )
            return int(existing.get("id", 0))

        record = {
            "name": session.name,
            "description": session.description,
            "timezone": session.timezone,
            "windows_json": windows_json,
            "holidays_json": holidays_json,
            "is_default": int(session.is_default),
        }
        new_id = self._db.sessions.create(record)
        logger.info(
            "FR-DATA-SESSIONS-PERSISTENCE-CRUD: Created session '%s' (id=%d)",
            session.name,
            new_id,
            extra={
                "session_name": session.name,
                "session_id": new_id,
                "timezone": session.timezone,
                "fr_id": "FR-DATA-SESSIONS-PERSISTENCE-CRUD",
            },
        )
        return new_id

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

        windows = []
        if row.get("windows_json"):
            try:
                raw_windows = json.loads(str(row["windows_json"]))
                windows = [SessionWindow.model_validate(w) for w in raw_windows]
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning(
                    "Failed parsing windows_json for session '%s': %s", name, exc
                )

        holidays = []
        if row.get("holidays_json"):
            try:
                raw_holidays = json.loads(str(row["holidays_json"]))
                holidays = [TradingHoliday.model_validate(h) for h in raw_holidays]
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning(
                    "Failed parsing holidays_json for session '%s': %s", name, exc
                )

        return TradingSessionDefinition(
            name=str(row.get("name", "")),
            description=str(row.get("description", "")),
            timezone=str(row.get("timezone", "UTC")),
            windows=windows,
            holidays=holidays,
            is_default=bool(row.get("is_default", 0)),
        )

    def list_sessions(
        self, limit: int = DEFAULT_LIMIT, offset: int = 0
    ) -> list[TradingSessionDefinition]:
        """List all defined trading sessions in alphabetical order."""
        rows = self._db.sessions.list_sessions(limit=limit, offset=offset)
        result: list[TradingSessionDefinition] = []
        for r in rows:
            sess = self.get_session(str(r.get("name", "")))
            if sess:
                result.append(sess)
        return result

    def delete_session(self, name: str) -> bool:
        """Delete trading session by name.

        Fires FR-DATA-SESSIONS-PERSISTENCE-CRUD.
        """
        clean_name = name.strip()
        sql = "DELETE FROM datamgr_sessions WHERE name = ?;"
        with self._db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(sql, (clean_name,))
            deleted = cur.rowcount > 0
        if deleted:
            logger.info(
                "FR-DATA-SESSIONS-PERSISTENCE-CRUD: Deleted session '%s'",
                clean_name,
                extra={
                    "session_name": clean_name,
                    "fr_id": "FR-DATA-SESSIONS-PERSISTENCE-CRUD",
                },
            )
        return deleted

    def is_market_open(self, session_name: str, dt_utc: datetime) -> bool:
        """Evaluate if market is actively open at specified UTC datetime.

        Handles IANA timezone conversion, DST fold/gap resolution, holiday matching,
        and multi-window session evaluation.

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

        day_of_week = local_dt.weekday()
        current_time = local_dt.time()

        for window in session.windows:
            if window.day_of_week != day_of_week:
                continue
            start_t = window.parse_start_time()
            end_t = window.parse_end_time()
            if start_t <= end_t:
                if start_t <= current_time <= end_t:
                    return True
            elif current_time >= start_t or current_time <= end_t:
                return True

        return False

    def import_ninjatrader_xml(
        self, xml_source: str | Path, policy: str = "overwrite"
    ) -> list[TradingSessionDefinition]:
        """Import NinjaTrader 8 TradingHours XML templates.

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

    def _load_xml_text(self, xml_source: str | Path) -> str:
        """Read XML text from file path or return string directly."""
        if isinstance(xml_source, Path) or (
            isinstance(xml_source, str) and not xml_source.strip().startswith("<")
        ):
            source_path = Path(xml_source)
            if not source_path.exists():
                raise FileNotFoundError(f"XML path not found: {source_path}")
            return source_path.read_text(encoding="utf-8")
        return str(xml_source)

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
            if day_elem is not None and day_elem.text:
                day_text = day_elem.text.strip().lower()
                day_val = (
                    int(day_text)
                    if day_text.isdigit()
                    else DAY_NAMES_MAP.get(day_text, 0)
                )

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

            windows.append(
                SessionWindow(
                    day_of_week=day_val,
                    start_time=start_str[:8],
                    end_time=end_str[:8],
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
                f"  {s.name:25} TZ: {s.timezone:20} Windows: {len(s.windows):2} "
                f"Holidays: {len(s.holidays):2}"
            )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
