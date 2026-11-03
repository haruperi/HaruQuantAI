"""Host-owned atomic storage for canonical strategy records.

Description:
    Stores integrity-checked JSON records under an explicitly configured root.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Durable strategy documents and optimistic revisions.
Key Capabilities:
    - FR-hsl-storage: Log durable writes and reject corruption or revision conflicts.
Python API Usage:
    storage = HostStrategyStorage(configured_directory)
CLI Usage:
    uv run pytest tests/core/host/test_strategy_storage.py --no-cov
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, copy_json

logger = get_logger(__name__)


class HostStrategyStorage:
    """Persist complete records without SQL or automatic schema migration."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not key or not isinstance(key, str):
            raise ValueError("A strategy storage key is required")
        name = hashlib.sha256(key.encode()).hexdigest()
        return self.root / f"{name}.json"

    def load(self, key: str) -> dict[str, Any] | None:
        """Read a verified record; absent and corrupted are distinct outcomes."""
        path = self._path(key)
        if not path.exists():
            return None
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            payload = record["payload"]
            raw = json.dumps(
                {
                    "key": record["key"],
                    "revision": record["revision"],
                    "payload": payload,
                },
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            self._verify_record(record, key, raw, payload)
        except (ValueError, KeyError, TypeError, OSError) as error:
            logger.exception("FR-hsl-storage: record verification failed")
            raise DomainError(
                code="HSL_STORAGE_CORRUPT",
                message="Stored strategy failed integrity verification",
            ) from error
        return {"revision": record["revision"], "payload": payload}

    @staticmethod
    def _verify_record(record: Any, key: str, raw: str, payload: Any) -> None:
        """Validate a stored envelope without swallowing an integrity error."""
        if (
            record["key"] != key
            or hashlib.sha256(raw.encode()).hexdigest() != record["sha256"]
        ):
            raise ValueError("Strategy storage integrity mismatch")
        if (
            not isinstance(payload, dict)
            or type(record["revision"]) is not int
            or record["revision"] < 1
        ):
            raise TypeError("Malformed strategy storage record")

    def records(self, prefix: str) -> dict[str, dict[str, Any]]:
        """Enumerate verified records; never skip an unreadable store entry."""
        result: dict[str, dict[str, Any]] = {}
        for path in sorted(self.root.glob("*.json")):
            try:
                key = json.loads(path.read_text(encoding="utf-8"))["key"]
            except (ValueError, KeyError, TypeError, OSError) as error:
                raise DomainError(
                    code="HSL_STORAGE_CORRUPT",
                    message="Cannot enumerate strategy storage",
                ) from error
            if not isinstance(key, str) or self._path(key) != path:
                raise DomainError(
                    code="HSL_STORAGE_CORRUPT", message="Invalid strategy record key"
                )
            if key.startswith(prefix):
                record = self.load(key)
                if record is not None:
                    result[key] = record
        return result

    def save(
        self, key: str, payload: Mapping[str, Any], *, expected_revision: int
    ) -> int:
        """Atomically replace one record under an exclusive cross-process lock."""
        path = self._path(key)
        lock = path.with_suffix(".lock")
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise DomainError(
                code="HSL_STORAGE_BUSY", message="Strategy record is being written"
            ) from error
        temporary: str | None = None
        try:
            os.close(descriptor)
            existing = self.load(key)
            revision = existing["revision"] if existing is not None else 0
            if revision != expected_revision:
                raise DomainError(
                    code="WIZARD_REVISION_CONFLICT",
                    message="Strategy storage revision changed",
                )
            detached = copy_json(dict(payload))
            raw = json.dumps(
                {"key": key, "revision": revision + 1, "payload": detached},
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            record = {
                "key": key,
                "revision": revision + 1,
                "payload": detached,
                "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            }
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.root,
                prefix=".strategy-",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = stream.name
                json.dump(record, stream, sort_keys=True, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            Path(temporary).replace(path)
            logger.info("FR-hsl-storage: saved strategy revision=%d", revision + 1)
            return int(revision + 1)
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)
            lock.unlink(missing_ok=True)
