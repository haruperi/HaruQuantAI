"""Trading session calendar engine, holiday management, and XML templates.

Description:
    Provides calendar evaluation logic (`TradingSession`, `SessionWindow`),
    exchange holiday handling, regular and electronic trading hours schedule
    filtering, SQX Sessions XML serialization/deserialization, and NinjaTrader 8
    TradingHours XML template import. Governs the `datamgr_sessions` database
    table without direct `sqlite3` imports.

Purpose:
    FEAT-DATAMGR-SESSIONS: Trading session calendars and exchange holiday governance.

Key Capabilities:
    - FR-DATAMGR-SESSIONS-CALENDAR-MODEL: Session windows and holiday schedule.
      Associated: `TradingSession.is_within_session()`
      Logging: Emits DEBUG when evaluating datetime against session schedule.
    - FR-DATAMGR-SESSIONS-CATALOG-CRUD: Manage session calendar records in
      `datamgr_sessions`.
      Associated: `SessionsCatalogService.list_sessions()`,
      `SessionsCatalogService.save_session()`
      Logging: Emits INFO on creation, cloning, and deletion of session
      schedules.
    - FR-DATAMGR-SESSIONS-SQX-XML: Native SQX Sessions XML import and export.
      Associated: `SessionsCatalogService.export_sqx_xml()`,
      `SessionsCatalogService.import_sqx_xml()`
      Logging: Emits INFO on XML export and import with parsed session count.
    - FR-DATAMGR-SESSIONS-NT8-IMPORT: Discover and import NinjaTrader 8
      TradingHours templates.
      Associated: `SessionsCatalogService.list_nt_templates()`,
      `SessionsCatalogService.import_nt_sessions()`
      Logging: Emits INFO on NinjaTrader 8 template import.

Python API Usage:
    ```python
    from datetime import datetime
    from app.workspace.data_manager.sessions import SessionsCatalogService

    service = SessionsCatalogService()
    session = service.get_session("Forex 24/5")
    if session:
        is_open = session.is_within_session(datetime(2026, 10, 15, 14, 30))
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.sessions
    ```
"""

from __future__ import annotations

import json
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import defusedxml.ElementTree as DefusedET  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.host.persistence.create import create_schema, insert_row
from app.host.persistence.delete import delete_row_by_pk
from app.host.persistence.read import count_rows, read_rows, resolve_connection
from app.host.persistence.update import update_row_by_pk
from defusedxml.common import DefusedXmlException  # type: ignore[import-untyped]

__all__ = [
    "SessionWindow",
    "SessionsCatalogService",
    "TradingHoliday",
    "TradingSession",
]

logger = get_logger(__name__)

CALENDAR_MODEL_FR = "FR-DATAMGR-SESSIONS-CALENDAR-MODEL"
CATALOG_CRUD_FR = "FR-DATAMGR-SESSIONS-CATALOG-CRUD"
SQX_XML_FR = "FR-DATAMGR-SESSIONS-SQX-XML"
NT8_IMPORT_FR = "FR-DATAMGR-SESSIONS-NT8-IMPORT"

_DAY_NAME_TO_INT: dict[str, int] = {
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


@dataclass(frozen=True)
class SessionWindow:
    """Represents a continuous trading interval on specific days of week."""

    day_from: str = "Mon"
    day_to: str = "Mon"
    start_time: str = "00:00"
    end_time: str = "23:59"
    eod: bool = False
    session_type: str = "Regular"
    day_of_week: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert session window to dictionary representation."""
        return {
            "day_from": self.day_from,
            "day_to": self.day_to,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "eod": self.eod,
            "session_type": self.session_type,
            "day_of_week": self.day_of_week,
        }


@dataclass(frozen=True)
class TradingHoliday:
    """Represents a date when markets are closed."""

    date_str: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert holiday to dictionary representation."""
        return {
            "date_str": self.date_str,
            "description": self.description,
        }


def _window_intervals(w: SessionWindow) -> list[tuple[int, int]]:
    """Derive list of (start_minute, end_minute) weekly intervals for window."""
    try:
        start_day = _DAY_NAME_TO_INT.get(w.day_from.lower(), w.day_of_week or 0)
        end_day = _DAY_NAME_TO_INT.get(w.day_to.lower(), start_day)
        sh, sm = (int(x) for x in w.start_time.split(":")[:2])
        eh, em = (int(x) for x in w.end_time.split(":")[:2])
        s_min = sh * 60 + sm
        e_min = eh * 60 + em

        if (end_day - start_day) % 7 == 1 and s_min > e_min:
            return [(start_day * 1440 + s_min, end_day * 1440 + e_min)]

        if start_day == end_day and s_min > e_min:
            return [(start_day * 1440 + s_min, ((start_day + 1) % 7) * 1440 + e_min)]

        days: list[int] = []
        curr = start_day
        for _ in range(7):
            days.append(curr)
            if curr == end_day:
                break
            curr = (curr + 1) % 7

        intervals: list[tuple[int, int]] = []
        for d in days:
            if s_min <= e_min:
                intervals.append((d * 1440 + s_min, d * 1440 + e_min))
            else:
                intervals.append((d * 1440 + s_min, ((d + 1) % 7) * 1440 + e_min))
        return intervals
    except ValueError, TypeError, AttributeError:
        return []


def _is_window_active(w: SessionWindow, minute_of_week: int) -> bool:
    """Check if session window covers the specified minute of week (0..10079)."""
    for s, e in _window_intervals(w):
        if s <= e and s <= minute_of_week <= e:
            return True
        if s > e and (minute_of_week >= s or minute_of_week <= e):
            return True
    return False


@dataclass
class TradingSession:
    """Represents an authoritative trading session calendar."""

    id: int | None = None
    name: str = ""
    broker_id: int = -1
    broker_name: str = "SQ default"
    description: str = ""
    timezone: str = "UTC"
    windows: list[SessionWindow] = field(default_factory=list)
    holidays: list[TradingHoliday] = field(default_factory=list)
    is_default: bool = False

    def is_within_session(self, dt: datetime) -> bool:
        """Evaluate if datetime falls within active trading schedule."""
        try:
            target_tz = ZoneInfo(self.timezone)
        except KeyError, ValueError, ZoneInfoNotFoundError:
            target_tz = ZoneInfo("UTC")

        if dt.tzinfo is not None:
            dt_tz = dt.astimezone(target_tz)
        else:
            dt_tz = dt.replace(tzinfo=UTC).astimezone(target_tz)

        date_iso = dt_tz.strftime("%Y-%m-%d")
        for h in self.holidays:
            if h.date_str == date_iso:
                logger.debug(
                    "%s: Date %s falls on holiday %s",
                    CALENDAR_MODEL_FR,
                    date_iso,
                    h.description,
                    extra={
                        "fr_id": CALENDAR_MODEL_FR,
                        "date": date_iso,
                        "holiday": h.description,
                    },
                )
                return False

        if not self.windows:
            return False

        minute_of_week = dt_tz.weekday() * 1440 + dt_tz.hour * 60 + dt_tz.minute

        for w in self.windows:
            if _is_window_active(w, minute_of_week):
                return True

        logger.debug(
            "%s: %s outside session windows for %s",
            CALENDAR_MODEL_FR,
            dt.isoformat(),
            self.name,
            extra={
                "fr_id": CALENDAR_MODEL_FR,
                "dt": dt.isoformat(),
                "session": self.name,
            },
        )
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert trading session to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "broker_id": self.broker_id,
            "broker_name": self.broker_name,
            "description": self.description,
            "timezone": self.timezone,
            "windows": [w.to_dict() for w in self.windows],
            "holidays": [h.to_dict() for h in self.holidays],
            "is_default": self.is_default,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TradingSession:
        """Construct TradingSession from dictionary or database row."""
        raw_windows = data.get("windows_json", "[]")
        windows: list[SessionWindow] = []
        if isinstance(raw_windows, str):
            try:
                parsed_w = json.loads(raw_windows)
                windows = [
                    SessionWindow(
                        day_from=str(w.get("day_from", "Mon")),
                        day_to=str(w.get("day_to", "Mon")),
                        start_time=str(w.get("start_time", "00:00")),
                        end_time=str(w.get("end_time", "23:59")),
                        eod=bool(w.get("eod", False)),
                        session_type=str(w.get("session_type", "Regular")),
                        day_of_week=w.get("day_of_week"),
                    )
                    for w in parsed_w
                ]
            except json.JSONDecodeError, TypeError, KeyError:
                windows = []
        elif isinstance(raw_windows, list):
            windows = [
                SessionWindow(**w) if isinstance(w, dict) else w for w in raw_windows
            ]

        raw_holidays = data.get("holidays_json", "[]")
        holidays: list[TradingHoliday] = []
        if isinstance(raw_holidays, str):
            try:
                parsed_h = json.loads(raw_holidays)
                holidays = [
                    TradingHoliday(
                        date_str=str(h.get("date_str", "")),
                        description=str(h.get("description", "")),
                    )
                    for h in parsed_h
                ]
            except json.JSONDecodeError, TypeError, KeyError:
                holidays = []
        elif isinstance(raw_holidays, list):
            holidays = [
                TradingHoliday(**h) if isinstance(h, dict) else h for h in raw_holidays
            ]

        return cls(
            id=data.get("id"),
            name=str(data.get("name", "")),
            broker_id=int(data.get("broker_id", -1)),
            broker_name=str(data.get("broker_name", "SQ default")),
            description=str(data.get("description", "")),
            timezone=str(data.get("timezone", "UTC")),
            windows=windows,
            holidays=holidays,
            is_default=bool(data.get("is_default", 0)),
        )


_DEFAULT_SEEDED_SESSIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "24/7",
        "description": "Continuous 24/7 trading for Crypto markets",
        "timezone": "UTC",
        "is_default": 1,
        "windows_json": json.dumps(
            [
                {
                    "day_from": "Mon",
                    "day_to": "Sun",
                    "start_time": "00:00",
                    "end_time": "23:59",
                    "session_type": "Regular",
                }
            ]
        ),
        "holidays_json": "[]",
    },
    {
        "name": "Forex 24/5",
        "description": "Standard Forex trading from Sunday 22:00 to Friday 22:00 UTC",
        "timezone": "UTC",
        "is_default": 0,
        "windows_json": json.dumps(
            [
                {
                    "day_from": "Mon",
                    "day_to": "Thu",
                    "start_time": "00:00",
                    "end_time": "23:59",
                    "session_type": "Regular",
                },
                {
                    "day_from": "Fri",
                    "day_to": "Fri",
                    "start_time": "00:00",
                    "end_time": "22:00",
                    "session_type": "Regular",
                },
                {
                    "day_from": "Sun",
                    "day_to": "Sun",
                    "start_time": "22:00",
                    "end_time": "23:59",
                    "session_type": "Regular",
                },
            ]
        ),
        "holidays_json": "[]",
    },
    {
        "name": "US Equities RTH",
        "description": "US Stock Market Regular Trading Hours (09:30 - 16:00 EST)",
        "timezone": "America/New_York",
        "is_default": 0,
        "windows_json": json.dumps(
            [
                {
                    "day_from": "Mon",
                    "day_to": "Fri",
                    "start_time": "09:30",
                    "end_time": "16:00",
                    "session_type": "Regular",
                }
            ]
        ),
        "holidays_json": json.dumps(
            [
                {"date_str": "2026-01-01", "description": "New Year's Day"},
                {
                    "date_str": "2026-07-04",
                    "description": "Independence Day",
                },
                {"date_str": "2026-12-25", "description": "Christmas Day"},
            ]
        ),
    },
    {
        "name": "CME Futures Globex",
        "description": "CME Index Futures electronic trading hours",
        "timezone": "America/Chicago",
        "is_default": 0,
        "windows_json": json.dumps(
            [
                {
                    "day_from": "Mon",
                    "day_to": "Fri",
                    "start_time": "17:00",
                    "end_time": "16:00",
                    "session_type": "Regular",
                }
            ]
        ),
        "holidays_json": "[]",
    },
)


class SessionsCatalogService:
    """Service governing session calendar CRUD, NT8 import, and XML transfer."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        data_dir: Path | str | None = None,
    ) -> None:
        """Initialize session service with database and templates directories."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.data_dir = Path(data_dir) if data_dir is not None else Path("data")

    def ensure_default_sessions(self) -> int:
        """Seed default canonical trading sessions if table is empty."""
        with resolve_connection(self.db_path) as conn:
            existing = count_rows(conn, "datamgr_sessions")
            if existing > 0:
                return 0

            seeded = 0
            for item in _DEFAULT_SEEDED_SESSIONS:
                insert_row(conn, "datamgr_sessions", dict(item))
                seeded += 1

        logger.info(
            "%s: Seeded %d default trading sessions",
            CATALOG_CRUD_FR,
            seeded,
            extra={"fr_id": CATALOG_CRUD_FR, "seeded": seeded},
        )
        return seeded

    def list_sessions(
        self,
        broker_id: int | None = None,
        search: str | None = None,
    ) -> list[TradingSession]:
        """List sessions matching optional broker ID and search query."""
        where: dict[str, Any] = {}
        if broker_id is not None and broker_id >= 0:
            where["broker_id"] = broker_id

        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_sessions",
                where=where or None,
                order_by="name ASC",
            )

        results: list[TradingSession] = []
        q = search.strip().lower() if search else None
        for r in rows:
            session = TradingSession.from_dict(r)
            if (
                q
                and q not in session.name.lower()
                and q not in session.description.lower()
            ):
                continue
            results.append(session)
        return results

    def get_session(self, name: str) -> TradingSession | None:
        """Retrieve a trading session by its unique name."""
        clean = name.strip()
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_sessions",
                where={"name": clean},
                limit=1,
            )
        if not rows:
            return None
        return TradingSession.from_dict(rows[0])

    def save_session(self, payload: Mapping[str, Any]) -> TradingSession:
        """Create or update a trading session calendar."""
        clean_name = str(payload.get("name", "")).strip()
        if not clean_name:
            raise ValueError("Session name is required.")

        windows_json = payload.get("windows_json")
        if windows_json is None:
            raw_w = payload.get("windows", [])
            windows_json = json.dumps(
                [w.to_dict() if hasattr(w, "to_dict") else w for w in raw_w]
            )

        holidays_json = payload.get("holidays_json")
        if holidays_json is None:
            raw_h = payload.get("holidays", [])
            holidays_json = json.dumps(
                [h.to_dict() if hasattr(h, "to_dict") else h for h in raw_h]
            )

        row_data: dict[str, Any] = {
            "name": clean_name,
            "description": str(payload.get("description", "")),
            "timezone": str(payload.get("timezone", "UTC")),
            "windows_json": windows_json,
            "holidays_json": holidays_json,
            "is_default": 1 if payload.get("is_default") else 0,
            "broker_id": int(payload.get("broker_id", -1)),
        }

        existing = self.get_session(clean_name)
        with resolve_connection(self.db_path) as conn:
            if existing is not None and existing.id is not None:
                row_data["id"] = existing.id
                update_row_by_pk(
                    conn, "datamgr_sessions", {"id": existing.id}, row_data
                )
            else:
                row_data.pop("id", None)
                inserted = insert_row(conn, "datamgr_sessions", row_data)
                row_data["id"] = int(inserted)

        result = TradingSession.from_dict(row_data)
        logger.info(
            "%s: Saved session calendar name=%s id=%s",
            CATALOG_CRUD_FR,
            result.name,
            result.id,
            extra={
                "fr_id": CATALOG_CRUD_FR,
                "session_name": result.name,
                "id": result.id,
            },
        )
        return result

    def delete_session(self, name: str) -> bool:
        """Delete a trading session by name."""
        session = self.get_session(name)
        if session is None or session.id is None:
            return False

        with resolve_connection(self.db_path) as conn:
            deleted = delete_row_by_pk(conn, "datamgr_sessions", {"id": session.id}) > 0

        logger.info(
            "%s: Deleted session name=%s deleted=%s",
            CATALOG_CRUD_FR,
            name,
            deleted,
            extra={
                "fr_id": CATALOG_CRUD_FR,
                "session_name": name,
                "deleted": deleted,
            },
        )
        return deleted

    def clone_session(
        self,
        source_name: str,
        new_name: str,
        broker_id: int = -1,
        broker_postfix: str = "",
    ) -> TradingSession:
        """Clone an existing session schedule with a new name."""
        source = self.get_session(source_name)
        if source is None:
            raise KeyError(f"Source session '{source_name}' not found.")

        target_name = (
            new_name.strip() if new_name else f"{source.name}{broker_postfix}".strip()
        )
        data = source.to_dict()
        data["id"] = None
        data["name"] = target_name
        data["broker_id"] = broker_id
        return self.save_session(data)

    def mass_delete_sessions(self, names: Sequence[str]) -> int:
        """Delete multiple sessions by name."""
        count = 0
        for name in names:
            if self.delete_session(name):
                count += 1
        logger.info(
            "%s: Mass-deleted %d sessions",
            CATALOG_CRUD_FR,
            count,
            extra={"fr_id": CATALOG_CRUD_FR, "count": count},
        )
        return count

    def list_nt_templates(self, folder_path: str | None = None) -> dict[str, Any]:
        """Discover NinjaTrader 8 TradingHours template files in folder."""
        target_dir = (
            Path(folder_path)
            if folder_path
            else self.data_dir / "templates" / "ninjatrader"
        )
        exists = target_dir.is_dir()
        templates: list[str] = []
        if exists:
            templates.extend(p.stem for p in target_dir.glob("*.xml"))

        logger.info(
            "%s: Discovered %d NT8 templates in %s",
            NT8_IMPORT_FR,
            len(templates),
            target_dir,
            extra={
                "fr_id": NT8_IMPORT_FR,
                "count": len(templates),
                "folder": str(target_dir),
            },
        )
        return {
            "folder": str(target_dir),
            "exists": exists,
            "templates": templates,
            "count": len(templates),
        }

    def import_nt_sessions(
        self,
        xml_content: str | None = None,
        folder_path: str | None = None,
        conflict_policy: str = "overwrite",
    ) -> dict[str, Any]:
        """Import NinjaTrader 8 TradingHours XML definitions."""
        imported: list[str] = []
        skipped: list[str] = []
        failed: list[str] = []
        total_holidays_parsed = 0

        xml_snippets: list[str] = []
        if xml_content:
            xml_snippets.append(xml_content)
        elif folder_path and Path(folder_path).is_dir():
            for p in Path(folder_path).glob("*.xml"):
                try:
                    xml_snippets.append(p.read_text(encoding="utf-8"))
                except OSError:
                    failed.append(p.name)

        for content in xml_snippets:
            try:
                root = DefusedET.fromstring(content)
                name = (
                    root.findtext(".//Name")
                    or root.findtext("Name")
                    or root.get("name", "NT8_Session")
                )
                clean_name = name.strip()
                existing = self.get_session(clean_name)
                if existing and conflict_policy == "skip":
                    skipped.append(clean_name)
                    continue

                windows = [
                    {
                        "day_from": s.findtext("Day") or "Mon",
                        "day_to": s.findtext("Day") or "Mon",
                        "start_time": s.findtext("StartTime") or "00:00",
                        "end_time": s.findtext("EndTime") or "23:59",
                        "session_type": "Regular",
                    }
                    for s in root.findall(".//Session")
                ]

                holidays: list[dict[str, str]] = []
                for he in root.findall(".//Holiday"):
                    h_date = (
                        he.findtext("Date")
                        or he.findtext("date")
                        or he.get("date")
                        or he.get("Date")
                        or ""
                    ).strip()
                    if h_date:
                        h_date = h_date.split("T")[0].split(" ")[0]
                        h_desc = (
                            he.findtext("Description")
                            or he.findtext("description")
                            or he.get("description")
                            or he.get("Description")
                            or ""
                        ).strip()
                        holidays.append({"date_str": h_date, "description": h_desc})
                total_holidays_parsed += len(holidays)

                self.save_session(
                    {
                        "name": clean_name,
                        "description": f"Imported NT8 template ({clean_name})",
                        "timezone": (
                            root.findtext(".//TimeZone")
                            or root.findtext("TimeZone")
                            or "UTC"
                        ),
                        "windows_json": json.dumps(windows),
                        "holidays_json": json.dumps(holidays),
                    }
                )
                imported.append(clean_name)
            except (
                DefusedXmlException,
                ET.ParseError,
                ValueError,
                TypeError,
            ):
                failed.append("XML_PARSE_ERROR")

        logger.info(
            "%s: NT8 import completed: %d imported, %d skipped, %d failed",
            NT8_IMPORT_FR,
            len(imported),
            len(skipped),
            len(failed),
            extra={
                "fr_id": NT8_IMPORT_FR,
                "imported": len(imported),
                "skipped": len(skipped),
            },
        )
        return {
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
            "dropped_holidays": 0,
            "dropped_partial_holidays": 0,
            "holidays_imported": total_holidays_parsed,
            "success": len(failed) == 0,
        }

    def export_sqx_xml(self, names: Sequence[str] | None = None) -> str:
        """Export trading sessions to native StrategyQuant X XML format."""
        sessions = self.list_sessions()
        target_names = {n.strip() for n in names} if names else None

        root = ET.Element("Sessions")
        for s in sessions:
            if target_names and s.name not in target_names:
                continue
            item = ET.SubElement(root, "Session")
            item.set("name", s.name)
            item.set("brokerId", str(s.broker_id))
            item.set("broker_id", str(s.broker_id))
            item.set("description", s.description)
            item.set("timezone", s.timezone)
            item.set("isDefault", "true" if s.is_default else "false")

            windows_elem = ET.SubElement(item, "Windows")
            for w in s.windows:
                we = ET.SubElement(windows_elem, "Window")
                we.set("dayFrom", w.day_from)
                we.set("dayTo", w.day_to)
                we.set("startTime", w.start_time)
                we.set("endTime", w.end_time)
                we.set("sessionType", w.session_type)
                we.set("eod", "true" if w.eod else "false")

            holidays_elem = ET.SubElement(item, "Holidays")
            for h in s.holidays:
                he = ET.SubElement(holidays_elem, "Holiday")
                he.set("date", h.date_str)
                he.set("description", h.description)

        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
        logger.info(
            "%s: Exported %d sessions to SQX XML",
            SQX_XML_FR,
            len(root),
            extra={"fr_id": SQX_XML_FR, "count": len(root)},
        )
        return str(xml_str)

    def import_sqx_xml(
        self, xml_content: str, policy: str = "overwrite"
    ) -> dict[str, Any]:
        """Safely import native SQX Sessions XML."""
        root = DefusedET.fromstring(xml_content)
        imported: list[TradingSession] = []
        skipped: list[str] = []

        session_nodes = root.findall("Session")
        if not session_nodes and root.tag == "Session":
            session_nodes = [root]

        for item in session_nodes:
            name = item.get("name", "").strip()
            if not name:
                continue

            existing = self.get_session(name)
            if existing and policy == "skip":
                skipped.append(name)
                continue

            broker_id_raw = item.get("brokerId") or item.get("broker_id") or "-1"
            try:
                broker_id = int(broker_id_raw)
            except ValueError:
                broker_id = -1

            window_nodes = item.findall(".//Window")
            if not window_nodes:
                window_nodes = item.findall(".//SessionElement")

            windows: list[dict[str, Any]] = []
            for we in window_nodes:
                day_from = (
                    we.get("dayFrom")
                    or we.get("day_from")
                    or we.get("startDay")
                    or we.get("Day")
                    or "Mon"
                )
                day_to = (
                    we.get("dayTo")
                    or we.get("day_to")
                    or we.get("endDay")
                    or we.get("Day")
                    or day_from
                )
                start_time = (
                    we.get("startTime")
                    or we.get("start_time")
                    or we.get("StartTime")
                    or "00:00"
                )
                end_time = (
                    we.get("endTime")
                    or we.get("end_time")
                    or we.get("EndTime")
                    or "23:59"
                )
                session_type = (
                    we.get("sessionType")
                    or we.get("session_type")
                    or we.get("SessionType")
                    or "Regular"
                )
                eod_str = (
                    we.get("eod") or we.get("Eod") or we.get("seoc") or "false"
                ).lower()
                eod = eod_str in ("true", "1", "yes")

                windows.append(
                    {
                        "day_from": day_from,
                        "day_to": day_to,
                        "start_time": start_time,
                        "end_time": end_time,
                        "session_type": session_type,
                        "eod": eod,
                    }
                )

            holidays = [
                {
                    "date_str": (
                        he.get("date") or he.get("Date") or he.findtext("Date") or ""
                    ),
                    "description": (
                        he.get("description")
                        or he.get("Description")
                        or he.findtext("Description")
                        or ""
                    ),
                }
                for he in item.findall(".//Holiday")
            ]

            saved = self.save_session(
                {
                    "name": name,
                    "broker_id": broker_id,
                    "description": item.get("description", ""),
                    "timezone": item.get("timezone", "UTC"),
                    "windows_json": json.dumps(windows),
                    "holidays_json": json.dumps(holidays),
                    "is_default": item.get("isDefault", "false").lower() == "true",
                }
            )
            imported.append(saved)

        logger.info(
            "%s: Imported %d SQX sessions (%d skipped)",
            SQX_XML_FR,
            len(imported),
            len(skipped),
            extra={
                "fr_id": SQX_XML_FR,
                "imported": len(imported),
                "skipped": len(skipped),
            },
        )
        return {
            "imported": [s.to_dict() for s in imported],
            "skipped": skipped,
        }


def main() -> None:
    """Execute real-usage demonstration of SessionsCatalogService."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_sessions.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        service = SessionsCatalogService(db_path=db_file, data_dir=temp_path / "data")
        seeded = service.ensure_default_sessions()
        print(f"Seeded {seeded} default sessions")

        forex = service.get_session("Forex 24/5")
        if forex:
            test_dt_open = datetime(2026, 10, 14, 15, 30, tzinfo=UTC)
            test_dt_closed = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)
            print(
                f"Forex 24/5 open on Wednesday: {forex.is_within_session(test_dt_open)}"
            )
            print(
                "Forex 24/5 open on Saturday: "
                f"{forex.is_within_session(test_dt_closed)}"
            )

        cloned = service.clone_session("24/7", "Crypto Weekend Only")
        print(f"Cloned session: {cloned.name}")

        xml_out = service.export_sqx_xml(["Forex 24/5"])
        print(f"Exported SQX XML:\n{xml_out[:180]}...")


if __name__ == "__main__":
    main()
