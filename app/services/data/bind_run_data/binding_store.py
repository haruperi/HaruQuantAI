"""Feature-owned persistence for immutable run-data bindings."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path

from app.contracts.data.models import RunDataBinding

_SCHEMA = """
CREATE TABLE IF NOT EXISTS data_run_bindings (
    binding_id TEXT PRIMARY KEY,
    run_manifest_id TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL
);
"""


class BindingStore:
    """SQLite adapter owned exclusively by FEAT-DATA-BIND_RUN_DATA."""

    def __init__(self, database_path: Path) -> None:
        """Initialize a lazy binding repository.

        Args:
            database_path: Feature-owned SQLite path.
        """
        self._database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.executescript(_SCHEMA)
        return connection

    async def put(self, binding: RunDataBinding) -> None:
        """Persist one immutable binding or verify exact idempotent replay.

        Args:
            binding: Immutable run-data binding.

        Raises:
            ValueError: If identity or run manifest is reused with different content.
        """
        payload = json.dumps(
            binding.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )

        def write() -> None:
            with self._connect() as connection:
                existing = connection.execute(
                    "SELECT binding_id, payload_json FROM data_run_bindings "
                    "WHERE binding_id = ? OR run_manifest_id = ?",
                    (binding.binding_id, binding.run_manifest_id),
                ).fetchone()
                if existing is not None:
                    if existing != (binding.binding_id, payload):
                        raise ValueError("immutable run-data binding conflict")
                    return
                connection.execute(
                    "INSERT INTO data_run_bindings "
                    "(binding_id, run_manifest_id, payload_json) VALUES (?, ?, ?)",
                    (binding.binding_id, binding.run_manifest_id, payload),
                )

        await asyncio.to_thread(write)
