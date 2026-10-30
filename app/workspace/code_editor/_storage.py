"""Storage editor contracts and workflows.

Description:
    Reads and writes finite JSON through HostPersistence, and stages source-file
    publication with exception rollback. Schemas and transactions remain host-owned.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-create-file: Publish a staged complete file exclusively;
      race, failure and safe logging cases are tested in test_save_as.py.
    - FR-code-editor-state-gateway: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-state-read: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-state-write: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-storage: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-storage-atomic-write-batch: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-storage-init: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-storage-read: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-storage-write: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor._storage
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from app.core.host.persistence import HostPersistence
from app.core.lib.errors import JSONValue, copy_json
from app.core.lib.responses import ErrorCode
from app.workspace.code_editor._common import CodeEditorError

logger = logging.getLogger(__name__)


class StateStore:
    """Store JSON documents through the host's SQLite gateway."""

    def __init__(self, gateway: HostPersistence | None = None) -> None:
        logger.debug("FR-code-editor-storage-init: invoked")
        self.gateway = gateway or HostPersistence()

    @staticmethod
    def _data(response: dict[str, Any]) -> dict[str, JSONValue]:
        try:
            if response["success"] is not True:
                raise ValueError("Host operation failed")
            data = copy_json(response["data"])
            if not isinstance(data, dict):
                raise ValueError("Invalid host result")
        except KeyError, TypeError, ValueError:
            logger.warning("FR-code-editor-state-gateway: unavailable")
            raise CodeEditorError(
                "Editor persistence unavailable", code=ErrorCode.UNAVAILABLE
            ) from None
        return data

    def read(self, key: str) -> dict[str, JSONValue] | None:
        logger.debug("FR-code-editor-storage-read: invoked")
        self._data(self.gateway.ensure_code_editor_schema())
        rows = self._data(
            self.gateway.read_records("code_editor_state", filters={"id": key}, limit=1)
        ).get("records")
        if not isinstance(rows, list) or len(rows) > 1:
            raise CodeEditorError(
                "Invalid editor stored state", code=ErrorCode.INTERNAL
            )
        if not rows:
            logger.debug("FR-code-editor-state-read: absent")
            return None
        row = rows[0]
        try:
            if not isinstance(row, dict) or not isinstance(row.get("payload"), str):
                raise ValueError("Invalid stored row")
            value = copy_json(json.loads(cast("str", row["payload"])))
            if not isinstance(value, dict):
                raise ValueError("Invalid stored document")
        except TypeError, ValueError:
            logger.error("FR-code-editor-state-read: rejected")
            raise CodeEditorError(
                "Invalid editor stored state", code=ErrorCode.INTERNAL
            ) from None
        logger.debug("FR-code-editor-state-read: completed")
        return value

    def write(self, key: str, payload: Mapping[str, object]) -> None:
        logger.debug("FR-code-editor-storage-write: invoked")
        try:
            value = copy_json(cast("JSONValue", dict(payload)))
            encoded = json.dumps(value, allow_nan=False)
        except ValueError:
            logger.warning("FR-code-editor-state-write: rejected")
            raise CodeEditorError("Editor state requires finite JSON values") from None
        self._data(self.gateway.ensure_code_editor_schema())
        with self.gateway.transaction() as transaction:
            rows = self._data(
                transaction.read_records(
                    "code_editor_state", filters={"id": key}, limit=1
                )
            ).get("records")
            if not isinstance(rows, list):
                raise CodeEditorError(
                    "Invalid editor stored state", code=ErrorCode.INTERNAL
                )
            if rows:
                self._data(
                    transaction.update_record(
                        "code_editor_state",
                        {"payload": encoded},
                        filters={"id": key},
                    )
                )
            else:
                self._data(
                    transaction.create_records(
                        "code_editor_state",
                        [{"id": key, "payload": encoded}],
                    )
                )
        logger.info("FR-code-editor-state-write: completed")


def atomic_create_file(destination: Path, content: bytes) -> None:
    """Publish complete bytes exclusively; never replace an existing destination.

    The caller authorizes the destination. Same-directory staging and a hard link
    provide complete-file visibility and an atomic no-replace collision check.
    Unsupported filesystems fail closed instead of falling back to replacement.
    """
    logger.debug("FR-code-editor-create-file: invoked")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=destination.parent, prefix=".editor-new-")
    staged = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(staged, destination)
    except FileExistsError:
        logger.warning("FR-code-editor-create-file: conflict")
        raise CodeEditorError(
            "Save As destination already exists", code=ErrorCode.CONFLICT
        ) from None
    except OSError:
        logger.error("FR-code-editor-create-file: publication failed")
        raise CodeEditorError(
            "Could not publish Save As file", code=ErrorCode.UNAVAILABLE
        ) from None
    finally:
        try:
            staged.unlink(missing_ok=True)
        except OSError:
            logger.warning("FR-code-editor-create-file: staging cleanup failed")
    logger.info("FR-code-editor-create-file: completed")


def atomic_write_batch(files: Mapping[Path, bytes]) -> None:
    """Stage every file, replace atomically per file, and rollback on failure.

    The batch is exception-atomic, not a filesystem-wide transaction on power loss.
    Readers always see a complete old or new file at each destination.
    """
    logger.debug("FR-code-editor-storage-atomic-write-batch: invoked")
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
                logger.warning("FR-code-editor-storage: operation")
        raise
    finally:
        for cleanup_file in [*staged.values(), *backups.values()]:
            if cleanup_file is not None and cleanup_file not in retained:
                cleanup_file.unlink(missing_ok=True)
