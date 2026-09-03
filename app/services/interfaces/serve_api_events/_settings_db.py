"""SQLite database helpers for system settings persistence in haruquantai.db."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
)

_CREDENTIAL_SLOTS: dict[str, dict[str, Any]] = {
    "mt5_live": {
        "label": "MetaTrader 5 (Live)",
        "fields": ["mt5.live.login", "mt5.live.password", "mt5.live.server"],
    },
    "mt5_demo": {
        "label": "MetaTrader 5 (Demo)",
        "fields": ["mt5.demo.login", "mt5.demo.password", "mt5.demo.server"],
    },
    "market_data_primary": {
        "label": "Primary Market Data Provider",
        "fields": ["market_data.primary.api_key", "market_data.primary.endpoint"],
    },
    "market_data_secondary": {
        "label": "Secondary Market Data Provider",
        "fields": [
            "market_data.secondary.api_key",
            "market_data.secondary.endpoint",
        ],
    },
    "google": {
        "label": "Google AI / Gemini Platform",
        "fields": ["credentials.google_api_key"],
    },
}


def _resolve_db_path(db_path: Path | str | None) -> Path:
    if db_path is None:
        return _DEFAULT_DB_PATH
    return Path(db_path)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    target = _resolve_db_path(db_path)
    if not target.exists():
        msg = f"Database not found at {target}"
        raise FileNotFoundError(msg)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def get_system_settings(
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Retrieve system settings projection from settings table.

    Returns:
        System settings projection payload matching SettingsReadResponse.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT key, value, updated_at FROM settings")
        rows = cur.fetchall()
        settings_dict: dict[str, str] = {
            str(row["key"]): str(row["value"]) for row in rows
        }
        latest_updated_at = max(
            (str(row["updated_at"]) for row in rows),
            default=_utc_now_iso(),
        )
        return {
            "scope": "system",
            "subject_id": "system",
            "user_id": None,
            "settings": settings_dict,
            "version": 1,
            "updated_at": latest_updated_at,
            "restart_required": False,
        }
    finally:
        conn.close()


def update_system_settings(
    settings_delta: dict[str, Any],
    changed_by: str = "system",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Update settings table and record settings_history audit entries.

    Returns:
        Updated system settings projection.
    """
    now = _utc_now_iso()
    conn = _get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            for key, val in settings_delta.items():
                str_val = str(val) if val is not None else ""
                cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
                existing = cur.fetchone()
                old_val = str(existing["value"]) if existing is not None else None
                if existing is not None:
                    cur.execute(
                        "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
                        (str_val, now, key),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO settings (
                            key, value, value_type, category, label,
                            description, is_secret, is_readonly, default_value,
                            updated_at, created_at
                        ) VALUES (?, ?, 'string', 'custom', ?, '', 0, 0, ?, ?, ?)
                        """,
                        (key, str_val, key, str_val, now, now),
                    )
                cur.execute(
                    """
                    INSERT INTO settings_history (
                        key, old_value, new_value, changed_by, changed_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (key, old_val, str_val, changed_by, now),
                )
        return get_system_settings(db_path=db_path)
    finally:
        conn.close()


def get_settings_manifest(
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return all setting definitions.

    Returns:
        List of setting definitions from the database.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                key, category, label, description, value_type,
                default_value, is_secret, is_readonly, updated_at
            FROM settings
            ORDER BY category, key
            """
        )
        items: list[dict[str, Any]] = []
        for row in cur.fetchall():
            items.append(
                {
                    "key": str(row["key"]),
                    "category": str(row["category"]),
                    "label": str(row["label"]),
                    "description": str(row["description"]),
                    "value_type": str(row["value_type"]),
                    "default_value": str(row["default_value"]),
                    "is_secret": bool(row["is_secret"]),
                    "is_readonly": bool(row["is_readonly"]),
                    "version": 1,
                    "updated_at": str(row["updated_at"]),
                }
            )
        return items
    finally:
        conn.close()


def get_credentials_status(
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return status of credential slots.

    Returns:
        List of credential slot statuses.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT key, value, updated_at FROM settings WHERE category = 'credentials'"
        )
        cred_rows = {
            str(row["key"]): (str(row["value"]), str(row["updated_at"]))
            for row in cur.fetchall()
        }

        statuses: list[dict[str, Any]] = []
        for slot, info in _CREDENTIAL_SLOTS.items():
            fields = info["fields"]
            configured = any(bool(cred_rows.get(f, ("", ""))[0]) for f in fields)
            updated_times = [
                cred_rows[f][1] for f in fields if f in cred_rows and cred_rows[f][0]
            ]
            latest_update = max(updated_times) if updated_times else None
            statuses.append(
                {
                    "slot": slot,
                    "label": info["label"],
                    "fields": fields,
                    "activation": "restart_required",
                    "configured": configured,
                    "version": 1,
                    "updated_at": latest_update,
                }
            )
        return statuses
    finally:
        conn.close()


def update_credential_slot(
    slot: str,
    material: dict[str, Any],
    changed_by: str = "system",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Update credentials for a specific slot.

    Returns:
        Updated slot status payload.
    """
    now = _utc_now_iso()
    conn = _get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            for key, val in material.items():
                str_val = str(val) if val is not None else ""
                cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
                existing = cur.fetchone()
                old_val = str(existing["value"]) if existing is not None else None
                if existing is not None:
                    cur.execute(
                        "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
                        (str_val, now, key),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO settings (
                            key, value, value_type, category, label,
                            description, is_secret, is_readonly, default_value,
                            updated_at, created_at
                        ) VALUES (?, ?, 'string', 'credentials', ?, '', 1, 0, '', ?, ?)
                        """,
                        (key, str_val, key, now, now),
                    )
                cur.execute(
                    """
                    INSERT INTO settings_history (
                        key, old_value, new_value, changed_by, changed_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (key, old_val, str_val, changed_by, now),
                )
        return {
            "slot": slot,
            "configured": True,
            "version": 1,
            "updated_at": now,
            "activation": "restart_required",
        }
    finally:
        conn.close()
