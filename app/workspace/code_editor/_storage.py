"""Durable editor state and rollback-capable atomic file publication."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from app.core.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.workspace.code_editor._common import CodeEditorError

logger = get_logger(__name__)


class StateStore:
    """Store JSON documents through the host's SQLite gateway."""

    def __init__(self, gateway: HostPersistence | None = None) -> None:
        self.gateway = gateway or HostPersistence()

    @staticmethod
    def _data(response: dict[str, Any]) -> dict[str, Any]:
        if not response["success"]:
            raise CodeEditorError(
                (response.get("error") or {}).get("message", "Persistence failed")
            )
        return cast("dict[str, Any]", response["data"])

    def read(self, key: str) -> dict[str, Any] | None:
        self._data(self.gateway.ensure_code_editor_schema())
        rows = self._data(
            self.gateway.read_records("code_editor_state", filters={"id": key}, limit=1)
        )["records"]
        return json.loads(rows[0]["payload"]) if rows else None

    def write(self, key: str, payload: Mapping[str, Any]) -> None:
        self._data(self.gateway.ensure_code_editor_schema())
        with self.gateway.transaction() as transaction:
            rows = self._data(
                transaction.read_records(
                    "code_editor_state", filters={"id": key}, limit=1
                )
            )["records"]
            if rows:
                self._data(
                    transaction.update_record(
                        "code_editor_state",
                        {"payload": json.dumps(payload)},
                        filters={"id": key},
                    )
                )
            else:
                self._data(
                    transaction.create_records(
                        "code_editor_state",
                        [{"id": key, "payload": json.dumps(payload)}],
                    )
                )


def atomic_write_batch(files: Mapping[Path, bytes]) -> None:
    """Stage every file, replace atomically per file, and rollback on failure.

    The batch is exception-atomic, not a filesystem-wide transaction on power loss.
    Readers always see a complete old or new file at each destination.
    """
    staged: dict[Path, Path] = {}
    backups: dict[Path, Path | None] = {}
    published: list[Path] = []
    retained: set[Path] = set()
    try:
        for destination, content in files.items():
            if destination.exists() and not destination.is_file():
                raise CodeEditorError(f"Not a regular file: {destination}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(dir=destination.parent, prefix=".editor-")
            staged[destination] = Path(name)
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            if destination.exists():
                fd, backup = tempfile.mkstemp(
                    dir=destination.parent, prefix=".editor-backup-"
                )
                backups[destination] = Path(backup)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(destination.read_bytes())
                staged[destination].chmod(destination.stat().st_mode)
            else:
                backups[destination] = None
        for destination, temporary in staged.items():
            os.replace(temporary, destination)
            published.append(destination)
    except BaseException:
        for destination in reversed(published):
            rollback_file = backups[destination]
            try:
                if rollback_file is None:
                    destination.unlink()
                else:
                    os.replace(rollback_file, destination)
            except OSError:
                if rollback_file is not None:
                    retained.add(rollback_file)
                logger.exception(
                    "Rollback failed for %s; recovery copy: %s",
                    destination,
                    rollback_file,
                )
        raise
    finally:
        for cleanup_file in [*staged.values(), *backups.values()]:
            if cleanup_file is not None and cleanup_file not in retained:
                cleanup_file.unlink(missing_ok=True)
