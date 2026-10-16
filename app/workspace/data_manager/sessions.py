"""Trading session calendar engine and market schedule catalog management.

Description:
    Provides domain logic for trading session calendars, schedule viewing,
    editing, cloning, deletion, and canonical JSON specification import and
    export. Operates strictly via host persistence layer functions
    (`list_datamgr_sessions`, `get_datamgr_session`, `create_datamgr_session`,
    `update_datamgr_session`, `delete_datamgr_session`) with zero direct database
    queries and non-silent requirement logging.

Purpose:
    FEAT-DATAMGR-SESSIONS: Trading session calendar and schedule catalog governance.

Key Capabilities:
    - FR-DATAMGR-SESSIONS-VIEW: Retrieve and filter session records from the catalog.
      Associated: `Sessions.view()`
      Logging: Emits INFO on listed count and query parameters.
    - FR-DATAMGR-SESSIONS-ADD: Add a trading session specification to the catalog.
      Associated: `Sessions.add()`
      Logging: Emits INFO on added session name and id.
    - FR-DATAMGR-SESSIONS-EDIT: Edit one or multiple existing session records.
      Associated: `Sessions.edit()`
      Logging: Emits INFO on edited session(s) and updated count.
    - FR-DATAMGR-SESSIONS-CLONE: Duplicate a session schedule under a new name.
      Associated: `Sessions.clone()`
      Logging: Emits INFO on source and cloned target session names.
    - FR-DATAMGR-SESSIONS-DELETE: Delete one or multiple sessions from the catalog.
      Associated: `Sessions.delete()`
      Logging: Emits INFO on deleted session name(s) and count.
    - FR-DATAMGR-SESSIONS-IMPORT: Load session specifications from a selected JSON file.
      Associated: `Sessions.import_()`
      Logging: Emits INFO on imported, overwritten, and skipped session counts.
    - FR-DATAMGR-SESSIONS-EXPORT: Save session specifications to a JSON file.
      Associated: `Sessions.export()`
      Logging: Emits INFO on exported session count and target path.
    - FR-DATAMGR-SESSIONS-CLI: Headless CLI interface for session catalog management.
      Associated: `SessionsCLI.dispatch()`
      Logging: Emits INFO on headless command dispatch and parameter evaluation.

Python API Usage:
    ```python
    from app.workspace.data_manager.sessions import Sessions, SessionsCLI

    service = Sessions()
    sessions = service.view()
    print(SessionsCLI.format_sessions_table(sessions))
    ```

CLI Usage:
    ```bash
    uv run python -m app.cli sessions action=list
    uv run python -m app.cli sessions action=add session="24/7" timezone=UTC
    uv run python -m app.cli sessions action=list csv=true
    ```
"""

from __future__ import annotations

import csv
import io
import json
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.create import create_datamgr_session, create_schema
from app.host.persistence.delete import delete_datamgr_session
from app.host.persistence.read import (
    get_datamgr_session,
    list_datamgr_sessions,
    resolve_connection,
)
from app.host.persistence.update import update_datamgr_session

__all__ = [
    "Sessions",
    "SessionsCLI",
    "SessionsCatalogService",
]

logger = get_logger(__name__)

VIEW_FR = "FR-DATAMGR-SESSIONS-VIEW"
ADD_FR = "FR-DATAMGR-SESSIONS-ADD"
EDIT_FR = "FR-DATAMGR-SESSIONS-EDIT"
CLONE_FR = "FR-DATAMGR-SESSIONS-CLONE"
DELETE_FR = "FR-DATAMGR-SESSIONS-DELETE"
IMPORT_FR = "FR-DATAMGR-SESSIONS-IMPORT"
EXPORT_FR = "FR-DATAMGR-SESSIONS-EXPORT"
CLI_FR = "FR-DATAMGR-SESSIONS-CLI"


@dataclass(frozen=True)
class _Config:
    """Internal module configuration and execution parameters."""

    db_path: Path | None = None
    default_timezone: str = "UTC"

    def to_dict(self) -> dict[str, Any]:
        """Convert internal config to standard dictionary."""
        return {
            "db_path": str(self.db_path) if self.db_path else None,
            "default_timezone": self.default_timezone,
        }


_VALID_SESSION_COLS: frozenset[str] = frozenset(
    {
        "name",
        "description",
        "timezone",
        "windows_json",
        "holidays_json",
        "is_default",
        "broker_id",
    }
)

_SESSION_FIELD_ALIASES: dict[str, str] = {
    "session": "name",
    "session_name": "name",
    "tz": "timezone",
    "time_zone": "timezone",
    "broker": "broker_id",
    "default": "is_default",
}


def _serialize_windows(raw: Any) -> str:
    """Serialize windows structure to JSON string."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        items: list[dict[str, Any]] = []
        for item in raw:
            if hasattr(item, "to_dict"):
                items.append(item.to_dict())
            elif isinstance(item, dict):
                items.append(item)
        return json.dumps(items)
    return "[]"


def _serialize_holidays(raw: Any) -> str:
    """Serialize holidays structure to JSON string."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        items: list[dict[str, Any]] = []
        for item in raw:
            if hasattr(item, "to_dict"):
                items.append(item.to_dict())
            elif isinstance(item, dict):
                items.append(item)
        return json.dumps(items)
    return "[]"


def _parse_json_payload(
    file_path_or_content: str | Path | Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Parse JSON file path, string, or mapping into a list of session dicts."""
    if isinstance(file_path_or_content, Mapping):
        raw: Any = dict(file_path_or_content)
    else:
        target = Path(file_path_or_content)
        if target.is_file():
            raw = json.loads(target.read_text(encoding="utf-8"))
        else:
            raw = json.loads(str(file_path_or_content))

    if isinstance(raw, dict):
        return list(raw.get("sessions", []))
    if isinstance(raw, list):
        return list(raw)
    return []


class Sessions:
    """Service governing trading sessions via host persistence CRUD."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        config: _Config | None = None,
        log_service: Any = None,
    ) -> None:
        """Initialize sessions service with optional DB path and configuration."""
        resolved_db = Path(db_path) if db_path is not None else None
        self._config = config or _Config(db_path=resolved_db)
        self.log_service = log_service

    @property
    def db_path(self) -> Path | None:
        """Return configured database file path."""
        return self._config.db_path

    def view(
        self,
        broker_id: int | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return sessions in datamgr_sessions matching optional filter criteria."""
        rows = list_datamgr_sessions(
            self._config.db_path,
            broker_id=broker_id if broker_id is not None and broker_id >= 0 else None,
        )
        results: list[dict[str, Any]] = []
        q = search.strip().lower() if search else None

        for r in rows:
            if q:
                name_str = str(r.get("name", "")).lower()
                desc_str = str(r.get("description", "")).lower()
                if q not in name_str and q not in desc_str:
                    continue
            results.append(r)

        logger.info(
            "%s: Listed %d sessions",
            VIEW_FR,
            len(results),
            extra={
                "fr_id": VIEW_FR,
                "count": len(results),
                "broker_id": broker_id,
                "search": search,
            },
        )
        return results

    def add(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Add a trading session specification to datamgr_sessions."""
        clean_name = str(payload.get("name", "") or payload.get("session", "")).strip()
        if not clean_name:
            raise ValueError("Session name is required.")

        windows_raw = payload.get("windows_json") or payload.get("windows", [])
        holidays_raw = payload.get("holidays_json") or payload.get("holidays", [])
        windows_json = _serialize_windows(windows_raw)
        holidays_json = _serialize_holidays(holidays_raw)

        description = str(payload.get("description", "")).strip()
        timezone = str(
            payload.get("timezone", payload.get("tz", self._config.default_timezone))
        ).strip()
        is_default = 1 if payload.get("is_default") or payload.get("default") else 0
        broker_id = int(payload.get("broker_id", payload.get("broker", -1)))

        existing = get_datamgr_session(self._config.db_path, clean_name)
        if existing is not None:
            updates: dict[str, Any] = {
                "name": clean_name,
                "description": description,
                "timezone": timezone,
                "windows_json": windows_json,
                "holidays_json": holidays_json,
                "is_default": is_default,
                "broker_id": broker_id,
            }
            update_datamgr_session(self._config.db_path, clean_name, updates)
            res = get_datamgr_session(self._config.db_path, clean_name)
            result = res if res is not None else dict(updates)
        else:
            inserted_id = create_datamgr_session(
                self._config.db_path,
                name=clean_name,
                description=description,
                timezone_name=timezone,
                windows_json=windows_json,
                holidays_json=holidays_json,
                is_default=is_default,
                broker_id=broker_id,
            )
            res = get_datamgr_session(self._config.db_path, clean_name)
            result = res if res is not None else {"id": inserted_id, "name": clean_name}

        logger.info(
            "%s: Added session name=%s id=%s",
            ADD_FR,
            clean_name,
            result.get("id"),
            extra={"fr_id": ADD_FR, "session_name": clean_name, "id": result.get("id")},
        )
        return result

    def edit(
        self,
        name_or_names: str | Sequence[str],
        updates: Mapping[str, Any],
        change_flags: Mapping[str, bool] | None = None,
    ) -> dict[str, Any] | int:
        """Edit one or multiple sessions in datamgr_sessions."""
        filtered_updates: dict[str, Any] = {}
        for k, v in updates.items():
            norm_k = _SESSION_FIELD_ALIASES.get(k.lower(), k)
            if (
                norm_k in _VALID_SESSION_COLS
                and norm_k != "id"
                and (change_flags is None or change_flags.get(k, True))
            ):
                if norm_k == "windows":
                    filtered_updates["windows_json"] = _serialize_windows(v)
                elif norm_k == "holidays":
                    filtered_updates["holidays_json"] = _serialize_holidays(v)
                else:
                    filtered_updates[norm_k] = v

        if isinstance(name_or_names, str):
            clean_name = name_or_names.strip()
            current = get_datamgr_session(self._config.db_path, clean_name)
            if current is None:
                raise KeyError(f"Session '{clean_name}' not found.")
            update_datamgr_session(self._config.db_path, clean_name, filtered_updates)
            updated = get_datamgr_session(self._config.db_path, clean_name)
            res = updated if updated is not None else dict(filtered_updates)
            logger.info(
                "%s: Edited session name=%s",
                EDIT_FR,
                clean_name,
                extra={"fr_id": EDIT_FR, "session_name": clean_name},
            )
            return res

        count = 0
        for name in name_or_names:
            clean_name = name.strip()
            if update_datamgr_session(
                self._config.db_path, clean_name, filtered_updates
            ):
                count += 1
        logger.info(
            "%s: Edited %d sessions",
            EDIT_FR,
            count,
            extra={"fr_id": EDIT_FR, "count": count},
        )
        return count

    def clone(
        self,
        name: str = "",
        clone_name: str = "",
        broker_id: int = -1,
        broker_postfix: str = "",
        source_name: str = "",
    ) -> dict[str, Any]:
        """Copy one session to create a new session in datamgr_sessions."""
        target_src = source_name or name
        clean_name = target_src.strip()
        source = get_datamgr_session(self._config.db_path, clean_name)
        if source is None:
            raise KeyError(f"Source session '{clean_name}' not found.")

        target_name = (
            clone_name.strip()
            if clone_name
            else f"{source['name']}{broker_postfix}".strip()
        )
        data = dict(source)
        data.pop("id", None)
        data["name"] = target_name
        data["broker_id"] = broker_id if broker_id >= 0 else source.get("broker_id", -1)
        cloned = self.add(data)
        logger.info(
            "%s: Cloned session %s -> %s",
            CLONE_FR,
            clean_name,
            target_name,
            extra={"fr_id": CLONE_FR, "source": clean_name, "target": target_name},
        )
        return cloned

    def delete(self, name_or_names: str | Sequence[str]) -> bool | int:
        """Remove one or more sessions from datamgr_sessions."""
        if isinstance(name_or_names, str):
            clean_name = name_or_names.strip()
            deleted = delete_datamgr_session(self._config.db_path, clean_name)
            logger.info(
                "%s: Deleted session name=%s status=%s",
                DELETE_FR,
                clean_name,
                deleted,
                extra={
                    "fr_id": DELETE_FR,
                    "session_name": clean_name,
                    "deleted": deleted,
                },
            )
            return deleted

        deleted_count = 0
        for name in name_or_names:
            clean_name = name.strip()
            if delete_datamgr_session(self._config.db_path, clean_name):
                deleted_count += 1
        logger.info(
            "%s: Deleted %d sessions",
            DELETE_FR,
            deleted_count,
            extra={"fr_id": DELETE_FR, "deleted_count": deleted_count},
        )
        return deleted_count

    def import_(
        self,
        file_path_or_content: str | Path | Mapping[str, Any],
        conflict_policy: str = "overwrite_all",
    ) -> dict[str, Any]:
        """Add new sessions from a selected JSON file or structure."""
        items = _parse_json_payload(file_path_or_content)
        imported = 0
        overwritten = 0
        skipped = 0
        sessions_list: list[str] = []

        for item in items:
            name = str(item.get("name", "") or item.get("session", "")).strip()
            if not name:
                continue
            existing = get_datamgr_session(self._config.db_path, name)
            if existing and conflict_policy == "skip":
                skipped += 1
                continue
            self.add(item)
            sessions_list.append(name)
            if existing:
                overwritten += 1
            else:
                imported += 1

        logger.info(
            "%s: Imported sessions JSON (imported=%d, overwritten=%d, skipped=%d)",
            IMPORT_FR,
            imported,
            overwritten,
            skipped,
            extra={
                "fr_id": IMPORT_FR,
                "imported": imported,
                "overwritten": overwritten,
                "skipped": skipped,
            },
        )
        return {
            "imported": imported,
            "overwritten": overwritten,
            "skipped": skipped,
            "sessions": sessions_list,
        }

    # Programmatic aliases
    import_json = import_

    def export(
        self,
        file_path: str | Path | None = None,
        names: Sequence[str] | None = None,
    ) -> str | Path:
        """Save selected sessions to a JSON file or structure."""
        all_sessions = self.view()
        target_names = {n.strip() for n in names} if names is not None else None
        exported = [
            s
            for s in all_sessions
            if target_names is None or str(s.get("name", "")).strip() in target_names
        ]

        payload = {
            "version": 1,
            "kind": "sessions",
            "sessions": exported,
        }
        json_content = json.dumps(payload, indent=2)

        if file_path is not None:
            p = Path(file_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json_content, encoding="utf-8")
            logger.info(
                "%s: Exported %d sessions to file %s",
                EXPORT_FR,
                len(exported),
                str(p),
                extra={
                    "fr_id": EXPORT_FR,
                    "count": len(exported),
                    "path": str(p),
                },
            )
            return p

        logger.info(
            "%s: Exported %d sessions as JSON string",
            EXPORT_FR,
            len(exported),
            extra={"fr_id": EXPORT_FR, "count": len(exported)},
        )
        return json_content


# Bind import attribute to import_ method for dynamic call support
setattr(Sessions, "import", Sessions.import_)


class SessionsCLI:
    """Headless CLI presentation and dispatcher for session operations."""

    MAX_DESC_LEN: int = 32
    TRUNCATE_LEN: int = 29
    _CLI_EXCLUDE_KEYS: frozenset[str] = frozenset(
        ("action", "session", "name", "sa", "se", "sl", "sd", "sc", "si", "sx")
    )

    @classmethod
    def _parse_cli_args(
        cls, args: Sequence[str] | Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Parse raw CLI arguments and return normalized (action, params)."""
        if isinstance(args, Mapping):
            params = dict(args)
        else:
            params = {}
            for item in args:
                if "=" in item:
                    k, v = item.split("=", 1)
                    params[k.lstrip("-").strip().lower()] = v.strip()
                elif item.startswith("-"):
                    params[item.lstrip("-").strip().lower()] = True
                elif "action" not in params:
                    params["action"] = item.strip().lower()

        raw_action = str(params.get("action", "")).strip().lower()
        if raw_action.startswith("action="):
            raw_action = raw_action.split("=", 1)[1].strip()

        alias_map = {
            "sl": "list",
            "sa": "add",
            "se": "edit",
            "sd": "delete",
            "sc": "clone",
            "si": "import",
            "sx": "export",
        }
        action = raw_action or next(
            (act for flag, act in alias_map.items() if flag in params), "list"
        )
        return action, params

    @classmethod
    def dispatch(
        cls,
        args: Sequence[str] | Mapping[str, Any],
        service: Sessions | None = None,
    ) -> dict[str, Any]:
        """Dispatch headless CLI session commands and flags."""
        svc = service or Sessions()
        raw_action, params = cls._parse_cli_args(args)

        logger.info(
            "%s: Executing CLI action '%s' with %d parameters",
            CLI_FR,
            raw_action,
            len(params),
            extra={"fr_id": CLI_FR, "action": raw_action, "params": params},
        )

        handlers: dict[str, Callable[[], dict[str, Any]]] = {
            "list": lambda: cls._handle_list(svc, params),
            "view": lambda: cls._handle_list(svc, params),
            "-sl": lambda: cls._handle_list(svc, params),
            "add": lambda: cls._handle_add(svc, params),
            "-sa": lambda: cls._handle_add(svc, params),
            "edit": lambda: cls._handle_edit(svc, params),
            "-se": lambda: cls._handle_edit(svc, params),
            "delete": lambda: cls._handle_delete(svc, params),
            "-sd": lambda: cls._handle_delete(svc, params),
            "clone": lambda: cls._handle_clone(svc, params),
            "-sc": lambda: cls._handle_clone(svc, params),
            "import": lambda: cls._handle_import(svc, params),
            "load": lambda: cls._handle_import(svc, params),
            "-si": lambda: cls._handle_import(svc, params),
            "export": lambda: cls._handle_export(svc, params),
            "save": lambda: cls._handle_export(svc, params),
            "-sx": lambda: cls._handle_export(svc, params),
        }

        handler = handlers.get(raw_action)
        if handler is None:
            raise ValueError(f"Unsupported session action: '{raw_action}'")
        return handler()

    @classmethod
    def _handle_list(cls, svc: Sessions, params: Mapping[str, Any]) -> dict[str, Any]:
        broker_id = int(params["broker_id"]) if "broker_id" in params else None
        sessions = svc.view(
            broker_id=broker_id,
            search=params.get("search"),
        )
        as_csv = str(params.get("csv", "false")).lower() in ("true", "1", "yes")
        rendered = (
            cls.format_sessions_csv(sessions)
            if as_csv
            else cls.format_sessions_table(sessions)
        )
        return {
            "command": "sessions",
            "action": "list",
            "count": len(sessions),
            "rendered": rendered,
            "sessions": sessions,
        }

    @classmethod
    def _handle_add(cls, svc: Sessions, params: Mapping[str, Any]) -> dict[str, Any]:
        name = params.get("session") or params.get("name")
        if not name:
            raise ValueError(
                "Parameter 'session' or 'name' is required for action=add."
            )
        payload = {k: v for k, v in params.items() if k not in cls._CLI_EXCLUDE_KEYS}
        payload["name"] = name
        added = svc.add(payload)
        return {
            "command": "sessions",
            "action": "add",
            "rendered": f"Added session '{added.get('name')}'.",
            "session": added,
        }

    @classmethod
    def _handle_edit(cls, svc: Sessions, params: Mapping[str, Any]) -> dict[str, Any]:
        name = params.get("session") or params.get("name")
        if not name:
            raise ValueError(
                "Parameter 'session' or 'name' is required for action=edit."
            )
        payload = {k: v for k, v in params.items() if k not in cls._CLI_EXCLUDE_KEYS}
        edited = svc.edit(str(name), payload)
        return {
            "command": "sessions",
            "action": "edit",
            "rendered": f"Edited session '{name}'.",
            "session": edited,
        }

    @classmethod
    def _handle_delete(cls, svc: Sessions, params: Mapping[str, Any]) -> dict[str, Any]:
        names_raw = (
            params.get("sessions") or params.get("session") or params.get("name")
        )
        if not names_raw:
            raise ValueError(
                "Parameter 'sessions' or 'name' is required for action=delete."
            )
        name_list = [s.strip() for s in str(names_raw).split(",") if s.strip()]
        if len(name_list) == 1:
            deleted = svc.delete(name_list[0])
            return {
                "command": "sessions",
                "action": "delete",
                "rendered": f"Deleted session '{name_list[0]}' (status={deleted}).",
                "deleted": deleted,
            }
        count = svc.delete(name_list)
        return {
            "command": "sessions",
            "action": "delete",
            "rendered": f"Deleted {count} sessions.",
            "deleted_count": count,
        }

    @classmethod
    def _handle_clone(cls, svc: Sessions, params: Mapping[str, Any]) -> dict[str, Any]:
        name = params.get("session") or params.get("name")
        if not name:
            raise ValueError(
                "Parameter 'session' or 'name' is required for action=clone."
            )
        clone_name = str(params.get("clone_name", params.get("new_name", "")))
        broker_id = int(params.get("broker_id", -1))
        broker_postfix = str(params.get("broker_postfix", ""))
        cloned = svc.clone(
            str(name),
            clone_name=clone_name,
            broker_id=broker_id,
            broker_postfix=broker_postfix,
        )
        return {
            "command": "sessions",
            "action": "clone",
            "rendered": f"Cloned session '{name}' -> '{cloned.get('name')}'.",
            "session": cloned,
        }

    @classmethod
    def _handle_import(cls, svc: Sessions, params: Mapping[str, Any]) -> dict[str, Any]:
        filepath = params.get("filepath") or params.get("file")
        if not filepath:
            raise ValueError("Parameter 'filepath' is required for action=import.")
        policy = str(params.get("conflict_policy", "overwrite_all"))
        report = svc.import_(filepath, conflict_policy=policy)
        return {
            "command": "sessions",
            "action": "import",
            "rendered": (
                f"Imported {report.get('imported', 0)} sessions "
                f"(overwritten={report.get('overwritten', 0)}, "
                f"skipped={report.get('skipped', 0)})."
            ),
            **report,
        }

    @classmethod
    def _handle_export(cls, svc: Sessions, params: Mapping[str, Any]) -> dict[str, Any]:
        filepath = params.get("filepath") or params.get("file")
        names_raw = params.get("sessions") or params.get("names")
        names = (
            [s.strip() for s in str(names_raw).split(",") if s.strip()]
            if names_raw
            else None
        )
        output = svc.export(filepath, names=names)
        rendered = f"Exported sessions to {output}" if filepath else str(output)
        return {
            "command": "sessions",
            "action": "export",
            "rendered": rendered,
            "output": str(output),
        }

    @classmethod
    def format_sessions_table(cls, sessions: Sequence[Mapping[str, Any]]) -> str:
        """Format sessions sequence into clean ASCII table."""
        if not sessions:
            return "No sessions found."

        col_w = {
            "Name": 20,
            "Timezone": 18,
            "Default": 8,
            "Broker": 8,
            "Windows": 8,
            "Description": cls.MAX_DESC_LEN,
        }
        for s in sessions:
            name_len = len(str(s.get("name", "")))
            if name_len > col_w["Name"]:
                col_w["Name"] = min(name_len, 28)

        hdr = (
            f"{'Name':<{col_w['Name']}}  "
            f"{'Timezone':<{col_w['Timezone']}}  "
            f"{'Default':<{col_w['Default']}}  "
            f"{'Broker':<{col_w['Broker']}}  "
            f"{'Windows':<{col_w['Windows']}}  "
            f"{'Description':<{col_w['Description']}}"
        )
        sep = (
            f"{'-' * col_w['Name']}  "
            f"{'-' * col_w['Timezone']}  "
            f"{'-' * col_w['Default']}  "
            f"{'-' * col_w['Broker']}  "
            f"{'-' * col_w['Windows']}  "
            f"{'-' * col_w['Description']}"
        )
        lines = [hdr, sep]

        for s in sessions:
            name = str(s.get("name", ""))
            tz = str(s.get("timezone", "UTC"))
            is_def = "Yes" if s.get("is_default") else "No"
            b_id = str(s.get("broker_id", -1))
            raw_w = s.get("windows_json", "[]")
            w_count = 0
            if isinstance(raw_w, str):
                try:
                    w_count = len(json.loads(raw_w))
                except json.JSONDecodeError:
                    w_count = 0
            elif isinstance(raw_w, list):
                w_count = len(raw_w)

            desc = str(s.get("description", ""))
            if len(desc) > cls.MAX_DESC_LEN:
                desc = desc[: cls.TRUNCATE_LEN] + "..."

            lines.append(
                f"{name:<{col_w['Name']}}  "
                f"{tz:<{col_w['Timezone']}}  "
                f"{is_def:<{col_w['Default']}}  "
                f"{b_id:<{col_w['Broker']}}  "
                f"{w_count:<{col_w['Windows']}}  "
                f"{desc:<{col_w['Description']}}"
            )
        return "\n".join(lines)

    @classmethod
    def format_sessions_csv(cls, sessions: Sequence[Mapping[str, Any]]) -> str:
        """Format sessions sequence as RFC-4180 CSV string."""
        buf = io.StringIO()
        fieldnames = [
            "name",
            "timezone",
            "is_default",
            "broker_id",
            "windows_json",
            "holidays_json",
            "description",
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for s in sessions:
            writer.writerow(dict(s))
        return buf.getvalue().strip()

    @classmethod
    def format_output(cls, data: Mapping[str, Any]) -> str:
        """Format generic dictionary output for terminal display."""
        logger.debug("Formatting session output: %d keys", len(data))
        lines = [f"{k}: {v}" for k, v in data.items() if k != "rendered"]
        return "\n".join(lines)


SessionsCatalogService = Sessions

if __name__ == "__main__":
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_db = Path(temp_dir) / "demo_sessions.db"
        with resolve_connection(temp_db) as conn:
            create_schema(conn)

        service = Sessions(db_path=temp_db)
        service.add(
            {
                "name": "24/7 Crypto",
                "description": "Continuous crypto schedule",
                "timezone": "UTC",
                "is_default": 1,
            }
        )
        service.add(
            {
                "name": "US Equities RTH",
                "description": "US Stock Market Regular Trading Hours",
                "timezone": "America/New_York",
                "is_default": 0,
            }
        )
        all_sessions = service.view()
        print(SessionsCLI.format_sessions_table(all_sessions))
