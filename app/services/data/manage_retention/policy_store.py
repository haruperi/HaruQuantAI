"""Feature-owned persistence for Data retention policies."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path

from app.contracts.data.models import RetentionPolicy
from app.kernel.time import format_utc_timestamp, utc_now

_SCHEMA = """
CREATE TABLE IF NOT EXISTS data_retention_policies (
    policy_id TEXT PRIMARY KEY,
    policy_json TEXT NOT NULL,
    defined_at TEXT NOT NULL
);
"""


class RetentionPolicyStore:
    """Persist immutable policy definitions and resolve the latest one."""

    def __init__(self, database_path: Path) -> None:
        """Initialize the lazy SQLite policy store.

        Args:
            database_path: Feature-owned SQLite database path.
        """
        self._database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        """Open one bounded SQLite connection and ensure the feature schema.

        Returns:
            Configured SQLite connection.
        """
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.executescript(_SCHEMA)
        return connection

    async def define(self, policy: RetentionPolicy) -> None:
        """Persist one immutable policy definition.

        Args:
            policy: Strict public retention policy.

        Raises:
            ValueError: If a policy identity is reused for different content.
        """
        payload = json.dumps(
            policy.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )

        def write() -> None:
            with self._connect() as connection:
                existing = connection.execute(
                    "SELECT policy_json FROM data_retention_policies WHERE policy_id = ?",
                    (policy.policy_id,),
                ).fetchone()
                if existing is not None and str(existing[0]) != payload:
                    raise ValueError("immutable retention policy conflict")
                connection.execute(
                    "INSERT OR IGNORE INTO data_retention_policies "
                    "(policy_id, policy_json, defined_at) VALUES (?, ?, ?)",
                    (
                        policy.policy_id,
                        payload,
                        format_utc_timestamp(utc_now()),
                    ),
                )

        await asyncio.to_thread(write)

    async def latest(self) -> RetentionPolicy | None:
        """Return the most recently defined policy, if any.

        Returns:
            Latest immutable policy or None.
        """

        def read() -> RetentionPolicy | None:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT policy_json FROM data_retention_policies "
                    "ORDER BY defined_at DESC, policy_id DESC LIMIT 1"
                ).fetchone()
            if row is None:
                return None
            return RetentionPolicy.model_validate(json.loads(str(row[0])))

        return await asyncio.to_thread(read)
