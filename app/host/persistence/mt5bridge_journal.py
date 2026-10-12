"""MT5 bridge command and event persistence in the shared application database.

Description:
    Owns the bridge SQLite connection, locked CRUD and commits in the shared
    application database by default. Broker owns lifecycle and trade interpretation.
    Explicit paths support isolated stores. Schema
    creation and compatibility checks belong to host persistence schema helpers.

Purpose:
    FEAT-HOST-PERSISTENCE-MT5-JOURNAL: Store bridge command receipts and events
    without connecting to a terminal or creating core application tables.

Key Capabilities:
    - FR-HOST-PERSISTENCE-MT5-JOURNAL: Connection custody and command/event CRUD.
      Associated: `Journal.__init__()`, `create_command()`, `mark_sent()`,
        `resolve_command()`, `add_event()`, `get_command()`, `close()`
      Logging: DEBUG for every operation attempt with fr_id and operation only;
        no paths, command values, arguments, credentials or event payloads.

Python API Usage:
    ```python
    from app.host.persistence.mt5bridge_journal import Journal

    journal = Journal(":memory:")
    try:
        command = journal.get_command("example-command")
    finally:
        journal.close()
    ```

CLI Usage:
    uv run pytest tests/unit/services/test_mt5bridge_journal.py --no-cov
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.engine import DEFAULT_DATABASE_PATH
from app.host.persistence.schema import ensure_mt5bridge_journal_schema

logger = get_logger(__name__)


class Journal:
    """SQLite MT5 command/event journal under host persistence custody."""

    def __init__(self, path: str | Path = DEFAULT_DATABASE_PATH) -> None:
        logger.debug(
            "Opening MT5 journal",
            extra={"fr_id": "FR-HOST-PERSISTENCE-MT5-JOURNAL", "operation": "open"},
        )
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        try:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("PRAGMA synchronous=NORMAL")
            ensure_mt5bridge_journal_schema(self._db)
            self._db.commit()
        except Exception:
            self._db.close()
            raise

    @staticmethod
    def _json(value: Any) -> str:
        """Serialize stored values using the existing compact JSON contract."""
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)

    def create_command(
        self,
        *,
        command_id: str,
        session_id: str | None,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool,
    ) -> None:
        """Create a command receipt record."""
        logger.debug(
            "MT5 journal operation",
            extra={
                "fr_id": "FR-HOST-PERSISTENCE-MT5-JOURNAL",
                "operation": "create_command",
            },
        )
        now = time.time()
        with self._lock:
            self._db.execute(
                """
                INSERT INTO mt5_commands(
                    command_id,session_id,object_id,class_name,method_name,args_json,
                    requires_arm,created_at,status
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    command_id,
                    session_id,
                    object_id,
                    class_name,
                    method_name,
                    self._json(args),
                    int(requires_arm),
                    now,
                    "created",
                ),
            )
            self._db.commit()

    def mark_sent(self, command_id: str) -> None:
        """Mark the command sent and commit its timestamp."""
        logger.debug(
            "MT5 journal operation",
            extra={
                "fr_id": "FR-HOST-PERSISTENCE-MT5-JOURNAL",
                "operation": "mark_sent",
            },
        )
        with self._lock:
            self._db.execute(
                "UPDATE mt5_commands SET sent_at=?, status='sent' WHERE command_id=?",
                (time.time(), command_id),
            )
            self._db.commit()

    def resolve_command(
        self,
        command_id: str,
        *,
        status: str,
        value: Any = None,
        meta: Any = None,
        error: Any = None,
        native_request_id: int | None = None,
    ) -> None:
        """Persist the outcome and native request identifier."""
        logger.debug(
            "MT5 journal operation",
            extra={
                "fr_id": "FR-HOST-PERSISTENCE-MT5-JOURNAL",
                "operation": "resolve_command",
            },
        )
        now = time.time()
        with self._lock:
            self._db.execute(
                """
                UPDATE mt5_commands SET
                    acknowledged_at=COALESCE(acknowledged_at, ?),
                    resolved_at=?,
                    status=?,
                    native_request_id=?,
                    value_json=?,
                    meta_json=?,
                    error_json=?
                WHERE command_id=?
                """,
                (
                    now,
                    now,
                    status,
                    None if native_request_id is None else str(native_request_id),
                    self._json(value),
                    self._json(meta or {}),
                    self._json(error) if error is not None else None,
                    command_id,
                ),
            )
            self._db.commit()

    def add_event(
        self,
        *,
        session_id: str | None,
        event_type: str,
        payload: Any,
        command_id: str | None = None,
        native_request_id: int | None = None,
    ) -> None:
        """Append a transaction event to the journal."""
        logger.debug(
            "MT5 journal operation",
            extra={
                "fr_id": "FR-HOST-PERSISTENCE-MT5-JOURNAL",
                "operation": "add_event",
            },
        )
        with self._lock:
            self._db.execute(
                """
                INSERT INTO mt5_events(
                    session_id,command_id,native_request_id,event_type,payload_json,received_at
                ) VALUES(?,?,?,?,?,?)
                """,
                (
                    session_id,
                    command_id,
                    None if native_request_id is None else str(native_request_id),
                    event_type,
                    self._json(payload),
                    time.time(),
                ),
            )
            self._db.commit()

    def get_command(self, command_id: str) -> dict[str, Any] | None:
        """Read and deserialize one command, or return None."""
        logger.debug(
            "MT5 journal operation",
            extra={
                "fr_id": "FR-HOST-PERSISTENCE-MT5-JOURNAL",
                "operation": "get_command",
            },
        )
        with self._lock:
            row = self._db.execute(
                """
                SELECT command_id,object_id,class_name,method_name,status,created_at,
                       sent_at,acknowledged_at,resolved_at,native_request_id,
                       value_json,meta_json,error_json
                FROM mt5_commands WHERE command_id=?
                """,
                (command_id,),
            ).fetchone()
        if row is None:
            return None
        keys = [
            "command_id",
            "object_id",
            "class_name",
            "method_name",
            "status",
            "created_at",
            "sent_at",
            "acknowledged_at",
            "resolved_at",
            "native_request_id",
            "value_json",
            "meta_json",
            "error_json",
        ]
        data = dict(zip(keys, row, strict=True))
        for key in ("value_json", "meta_json", "error_json"):
            raw = data.pop(key)
            data[key.removesuffix("_json")] = None if raw is None else json.loads(raw)
        if data["native_request_id"] is not None:
            data["native_request_id"] = int(data["native_request_id"])
        return data

    def close(self) -> None:
        """Close the journal connection under its lock."""
        logger.debug(
            "MT5 journal operation",
            extra={"fr_id": "FR-HOST-PERSISTENCE-MT5-JOURNAL", "operation": "close"},
        )
        with self._lock:
            self._db.close()
